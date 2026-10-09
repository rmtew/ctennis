"""Independent actual-68000 preview projection/reference comparisons.

No host tennis model and no intermediate oracle state feed. Initial origins are
actual postlaunch snapshots; each execution advances its own controls and RNG.
"""
import hashlib
from pathlib import Path

from build_match_core import load_image
from check_shared_core_bytes import normalized
from history_proof import field, seek
from match_core_cpu import Core, STACK_BASE, STACK_TOP
from preview_proof import fixture, point, protected, call_checked, block
from run_shared_match_core import READONLY

CAP = 256
# Includes the retained 4096-record resolver followed by both 256-dispatch
# incoming and 256-phase outgoing segments, including non-dispatch envelopes.
MAX_WORKER_CALLS = 16384
SEEDS = (0xace1, 1, 0xbeef)
EXTERNALS = ('game_preview_projection_requested','game_preview_kind',
    'game_preview_incoming_valid','game_preview_end','game_preview_active',
    'game_preview_variant','game_preview_predictor_routes','game_tick_dispatch_body',
    'input_update','game_play_tick','game_scene_finish_tick','game_advance_clocks')


def offset(symbols, name):
    return symbols[name]-symbols['game_core_state']


def override(state, symbols, end, held, arguments=None):
    start=offset(symbols,'game_input_bits')
    values=list(state[start:start+2] if arguments is None else arguments)
    owner=state[offset(symbols,'game_lower_owner')+end]
    values[owner]=(values[owner]&0xffc0)|(16 if held else 0)
    return values


def causal(state, symbols):
    # Native motion/phase/RNG and logical controls; G_DISPLAY/status/raster/audio
    # are explicitly incidental. This is an observation, never a state model.
    return (state[:49]+state[50:60]+bytes([state[offset(symbols,'game_mode')]])+
        state[offset(symbols,'game_input_bits'):offset(symbols,'game_legacy_entropy_state')+2]+
        state[offset(symbols,'game_entropy_policy'):]).hex()


def outside(cpu, scratch):
    pieces=[]
    for low,high in cpu.regions:
        for a,b in ((low,min(high,scratch)),(max(low,scratch+318),high)):
            if a<b:pieces.append(bytes(cpu.mem.r_block(a,b-a)))
    return pieces


def execute(image, symbols, origin, stream, end, held, projected, poison,
            omitted_poison=False, kind=0, policy=1):
    """Each side owns a separately initialized private state and actual calls."""
    ledger=dict(attempts=[],launches=[],wide=[],handoffs=[],clamps=[])
    phase=0;launched=False;random_calls=0;runtime_cycles=0;reads=set();written=set()
    retained=(set(range(60))|{offset(symbols,'game_mode')}|
        set(range(offset(symbols,'game_audio_voices'),offset(symbols,'game_display_state')))|
        set(range(offset(symbols,'game_input_bits'),offset(symbols,'game_scene_objects')))|
        set(range(offset(symbols,'game_score_flags'),318)))
    # The paused canonical image is deliberately different from the origin.
    with Core(image,symbols,initial=bytes([poison^0xff])*318,poison=poison,readonly=READONLY) as cpu:
        scratch=symbols['game_preview_held_state']
        cpu.mem.w_block(scratch,origin)
        for name,value,width in (('game_preview_active',2,1),('game_history_mode',0,1),
            ('game_preview_projection_requested',policy,2),('game_preview_kind',kind,2),
            ('game_preview_end',end,2),('game_preview_incoming_valid',1,1)):
            (cpu.mem.w8 if width==1 else cpu.mem.w16)(symbols[name],value)
        def state():return bytes(cpu.mem.r_block(scratch,318))
        def value(name):return cpu.mem.r8(scratch+offset(symbols,name))
        old_trace=cpu.trace
        def trace(mode,width,address,value):
            size=1<<width
            if mode=='R' and address<cpu.stop and address+size>cpu.start:
                raise AssertionError('Private CPU read paused canonical state')
            if scratch<=address and address+size<=scratch+318:
                indices=set(range(address-scratch,address-scratch+size))
                if mode=='R':reads.update(indices-written)
                else:written.update(indices)
            elif mode=='W' and not (STACK_BASE<=address and address+size<=STACK_TOP+4):
                raise AssertionError(('Non-private CPU write',hex(address),size))
            old_trace(mode,width,address,value)
        cpu.mem.set_trace_func(trace)
        guard_cycles=cpu.call('game_preview_predictor_eligible',{13:scratch})
        eligible=cpu.cpu.r_reg(0);reason=cpu.cpu.r_reg(1)
        route=int(bool(projected and eligible))
        cpu.mem.w_block(symbols['game_preview_predictor_routes'],bytes([route,route]))
        # Explicit initial-private-state poison challenge, before any logical
        # envelope. Admission inspected the intact immutable full origin.
        if route and omitted_poison:
            cpu.mem.w_block(scratch,bytes(v if i in retained else poison for i,v in enumerate(origin)))
        reads.clear();written.clear();saved=outside(cpu,scratch)
        def observe(pc):
            nonlocal launched,random_calls
            cpu.instruction(pc)
            if pc==symbols['game_random']:random_calls+=1
            if pc==symbols['game_serve_timed'] and value('game_serve_clock')==32:
                ledger['handoffs'].append(dict(phase=phase,end=cpu.cpu.r_reg(7)&0xffff))
            if pc==symbols['game_scene_finish_tick'] and value('game_ball_y')>=192 and value('game_court_y')!=194:
                ledger['clamps'].append(dict(phase=phase,ball_y=value('game_ball_y'),court_y=value('game_court_y')))
            if pc==symbols['game_return_vector'] and cpu.cpu.r_reg(7)&0xffff==end:
                distance=abs(value('game_ball_x')-(cpu.cpu.r_reg(6)&0xffff))
                if distance>=13:ledger['wide'].append(dict(phase=phase,distance=distance,random_calls=random_calls))
            if pc not in (symbols['game_history_contact_begin'],symbols['game_history_contact'],symbols['game_history_serve']):return
            if cpu.cpu.r_reg(7)&0xffff!=end:return
            st=state()
            if pc==symbols['game_history_contact_begin']:
                ledger['attempts'].append(dict(phase=phase,player=list(st[end*10:end*10+4]),projection=point(st,symbols).hex()))
            else:
                launched=True
                ledger['launches'].append(dict(phase=phase,kind=3 if pc==symbols['game_history_serve'] else 1,
                    launch=list(st[offset(symbols,'game_launch_x'):offset(symbols,'game_launch_x')+6]),
                    target=list(st[offset(symbols,'game_target_y'):offset(symbols,'game_height')+1]),
                    contact=value('game_contact'),flight=value('game_flight')))
        cpu.cpu.set_instr_hook_callback(observe)
        def call(name,args=(),ball=False):
            nonlocal runtime_cycles
            registers={r:((len(cpu.visits)*65537+r*0x1010101)^0x965aa569^poison*0x1010101)&0xffffffff for r in range(15)}
            registers.update({i:(registers[i]&0xffff0000)|v for i,v in enumerate(args)})
            registers[13]=scratch
            if ball:registers[12]=scratch
            cpu.cpu.w_sr(0x2700|(poison&31))
            runtime_cycles+=cpu.call(name,registers)
            assert outside(cpu,scratch)==saved,'Paused image/history changed'
        paths=[point(state(),symbols).hex()];boundaries=[];events=[]
        call('game_core_sample_pads_body',override(state(),symbols,end,held))
        events.extend(cpu.preview_events);cpu.preview_events.clear()
        boundaries.append(dict(operation='prime',causal=causal(state(),symbols),full=state().hex(),events=list(events)))
        record=0;synthetic=0;termination='incoming-limit'
        while phase<CAP:
            if record<len(stream):
                name,args=stream[record];record+=1
            else:
                name=('game_round_poll','game_core_sample_pads','game_core_sample_result','game_tick_dispatch')[synthetic]
                args=override(state(),symbols,end,held) if name=='game_core_sample_pads' else [0]*6 if name=='game_core_sample_result' else []
                synthetic=(synthetic+1)&3
            if name in ('game_core_init','game_core_select','game_core_return_title'):
                termination='lifecycle';break
            if name=='game_core_sample_pads':args=override(state(),symbols,end,held,args)
            if name=='game_tick_dispatch':phase+=1
            entry='game_preview_dispatch' if projected and name=='game_tick_dispatch' else name+'_body'
            call(entry,args)
            output=list(cpu.preview_events);events.extend(output);cpu.preview_events.clear()
            boundaries.append(dict(operation=name,causal=causal(state(),symbols),full=state().hex(),events=output,
                record_cursor=record,synthetic_phase=synthetic,dispatches=phase))
            if name!='game_tick_dispatch':continue
            paths.append(point(state(),symbols).hex())
            if launched:termination='launch';break
            if value('game_contact')&0x8d:termination='no-contact';break
        incoming_final=state()
        if launched:
            for _ in range(CAP):
                call('game_ball_tick',ball=True)
                paths.append(point(state(),symbols).hex())
                flags=value('game_contact')
                if flags&0x8b:
                    termination='net' if flags&1 else 'out' if flags&0x88 else 'landing'
                    break
            else:termination='outgoing-limit'
        cpu.audit_reads()
        assert not cpu.events,'Private execution emitted live output'
        if route and omitted_poison:assert not reads-retained,sorted(reads-retained)
        return dict(route=route,reason=reason,guard_cycles=guard_cycles,runtime_cycles=runtime_cycles,
            boundaries=boundaries,path=paths,ledger=ledger,termination=termination,random_calls=random_calls,
            final=state().hex(),events=events,stack=cpu.stack_bytes,initial_reads=sorted(reads),
            incoming_final=incoming_final.hex(),
            omitted_reads=sorted(reads-retained),retained_bytes=len(retained),canonical_isolated=True,
            live_outputs=0,predictor_ticks=cpu.visits.get(symbols['game_preview_predictor_tick'],0))


def compare(reference, candidate):
    for key in ('path','ledger','termination','random_calls'):
        assert reference[key]==candidate[key],key
    assert len(reference['boundaries'])==len(candidate['boundaries'])
    for left,right in zip(reference['boundaries'],candidate['boundaries']):
        for key in ('operation','record_cursor','synthetic_phase','dispatches','causal'):
            assert left.get(key)==right.get(key),(key,left,right)
        if not candidate['route']:
            assert left['full']==right['full'] and left['events']==right['events'],'Exact fallback changed'
    if not candidate['route']:assert reference['final']==candidate['final'] and reference['events']==candidate['events']


def discover(image,symbols,seed,upper=False):
    with Core(image,symbols,readonly=READONLY) as cpu:
        count=0
        def stop(c,launches):
            nonlocal count
            count+=1
            if not upper:return count>=512
            return any(r['human'] and r['kind']==1 and r['end']==1 for r in launches)
        stream,states,_,launches=fixture(cpu,seed=seed,dispatches=20000 if upper else 512,stop=stop)
        choices=[]
        for end in ((1,) if upper else (0,)):
            human=next((r for r in launches if r['human'] and r['kind']==1 and r['end']==end),None)
            opponents=[r for r in launches if not r['human'] and r['end']!=end]
            if human:opponents=[r for r in opponents if r['origin']<human['origin']]
            assert opponents,('No actual incoming origin',seed,end)
            incoming=max(opponents,key=lambda r:r['origin']) if human else opponents[0]
            selected=human['origin'] if human else min(incoming['origin']+4*16+1,max(states))
            choices.append(dict(seed=seed,end=end,incoming=incoming['origin'],selected=selected,
                source=states[incoming['origin']+1],stream=stream[incoming['origin']+1:],
                human=human,ticks=count,origin_kind=incoming['kind']))
        return choices


def api_case(image,symbols,case,x,y,budget,poison,reference):
    """Actual public projected request/worker with populated frozen history."""
    with Core(image,symbols,poison=poison,readonly=READONLY) as cpu:
        fixture(cpu,seed=case['seed'],dispatches=case['ticks'])
        cpu.call('game_history_freeze');seek(cpu,case['selected']);saved=protected(cpu)
        old_trace=cpu.trace
        def trace(mode,width,address,value):
            if (mode=='R' and cpu.mem.r8(symbols['game_preview_active'])==2
                    and address<cpu.stop and address+(1<<width)>cpu.start):
                raise AssertionError('Public private worker read paused canonical state')
            old_trace(mode,width,address,value)
        cpu.mem.set_trace_func(trace)
        generation=field(cpu,'game_preview_generation',4)
        call_checked(cpu,'game_preview_request_projected',{0:generation,1:0xfffe,2:x,3:y},saved)
        assert cpu.cpu.r_reg(0)==1,(case['seed'],case['end'],x,y)
        generation+=1;cycles=[]
        for _ in range(MAX_WORKER_CALLS):
            cycles.append(call_checked(cpu,'game_preview_step',{0:generation,1:budget},saved))
            if field(cpu,'game_preview_status')>=5:break
        assert field(cpu,'game_preview_status')==5,(case['seed'],case['end'],budget,field(cpu,'game_preview_status'))
        assert bytes(cpu.mem.r_block(symbols['game_preview_incoming_state'],318))==case['source']
        assert bytes(cpu.mem.r_block(symbols['game_preview_predictor_routes'],2))==b'\x01\x01'
        for variant,expected in enumerate(reference):
            count=cpu.mem.r16(symbols['game_preview_counts']+variant*2)
            actual=bytes(cpu.mem.r_block(symbols['game_preview_paths']+variant*513*8,count*8))
            assert actual==bytes.fromhex(''.join(expected['path'])),(case['seed'],case['end'],x,y,variant)
            last=expected['boundaries'][-1]
            stream_cursor=int.from_bytes(cpu.mem.r_block(symbols['game_preview_stream_cursors']+variant*8,8),'big')
            assert stream_cursor==case['incoming']+1+last['record_cursor']
            assert cpu.mem.r16(symbols['game_preview_synthetic_phases']+variant*2)==last['synthetic_phase']
            assert cpu.mem.r16(symbols['game_preview_dispatches']+variant*2)==last['dispatches']
            assert cpu.mem.r16(symbols['game_preview_flight_phases']+variant*2)==len(expected['path'])-1-last['dispatches']
            assert bool(cpu.mem.r8(symbols['game_preview_launches']+variant))==bool(expected['ledger']['launches'])
            expected_outcome={'landing':1,'net':2,'out':3,'no-contact':5,
                'incoming-limit':6,'outgoing-limit':6,'lifecycle':7}[expected['termination']]
            assert cpu.mem.r16(symbols['game_preview_outcomes']+variant*2)==expected_outcome
            if expected['ledger']['launches']:
                launch=bytes(cpu.mem.r_block(symbols['game_preview_launch_states']+variant*318,318))
                assert causal(launch,symbols)==causal(bytes.fromhex(expected['incoming_final']),symbols)
        # Policy replacement while PRIME/incoming/READY must never reuse a
        # reduced context as full state. Both entries restart at full origin.
        switches=[]
        for name in ('game_preview_request','game_preview_request_projected'):
            cpu.preview_event_groups.clear()
            call_checked(cpu,name,{0:generation,1:0xfffe,2:x,3:y},saved);generation+=1
            assert field(cpu,'game_preview_status')==2
            for _ in range(MAX_WORKER_CALLS):
                call_checked(cpu,'game_preview_step',{0:generation,1:budget},saved)
                if field(cpu,'game_preview_status')>=5:break
            assert field(cpu,'game_preview_status')==5
            route=field(cpu,'game_preview_predictor_routes',1)
            assert route==(name.endswith('_projected'))
            for variant,expected in enumerate(reference):
                count=cpu.mem.r16(symbols['game_preview_counts']+variant*2)
                actual=bytes(cpu.mem.r_block(symbols['game_preview_paths']+variant*513*8,count*8))
                assert actual==bytes.fromhex(''.join(expected['path']))
                if not route:
                    state_name='game_preview_held_state' if variant==0 else 'game_preview_released_state'
                    assert bytes(cpu.mem.r_block(symbols[state_name],318)).hex()==expected['final']
                    assert cpu.preview_event_groups.get((2,variant),[])==expected['events']
            switches.append(dict(api=name,route=route,completed=True,paths_equal=True,
                exact_full_state_events_equal=not route))
        # Replace a genuinely advanced projected variant, then cancel an exact
        # replacement. The full completed replacement above establishes that
        # READY reduced buffers never become an exact seed.
        call_checked(cpu,'game_preview_request_projected',{0:generation,1:0xfffe,2:x,3:y},saved);generation+=1
        for _ in range(MAX_WORKER_CALLS):
            call_checked(cpu,'game_preview_step',{0:generation,1:1},saved)
            if field(cpu,'game_preview_dispatches')>0:break
        assert field(cpu,'game_preview_dispatches')>0
        cpu.preview_event_groups.clear()
        call_checked(cpu,'game_preview_request',{0:generation,1:0xfffe,2:x,3:y},saved);generation+=1
        for _ in range(MAX_WORKER_CALLS):
            call_checked(cpu,'game_preview_step',{0:generation,1:budget},saved)
            if field(cpu,'game_preview_status')>=5:break
        assert field(cpu,'game_preview_status')==5
        assert bytes(cpu.mem.r_block(symbols['game_preview_predictor_routes'],2))==b'\x00\x00'
        for variant,expected in enumerate(reference):
            state_name='game_preview_held_state' if variant==0 else 'game_preview_released_state'
            assert bytes(cpu.mem.r_block(symbols[state_name],318)).hex()==expected['final']
            assert cpu.preview_event_groups.get((2,variant),[])==expected['events']
        switches.append(dict(api='active-projected-to-exact',route=0,completed=True,
            exact_full_state_events_equal=True))
        old=generation
        call_checked(cpu,'game_preview_cancel',{0:generation},saved)
        before=block(cpu,'game_preview_storage','game_preview_storage_end')
        for name,args in (('game_preview_step',{0:old,1:budget}),
            ('game_preview_request_projected',{0:old,1:0xfffe,2:x,3:y}),
            ('game_preview_request',{0:old,1:0xfffe,2:x,3:y})):
            call_checked(cpu,name,args,saved)
            assert cpu.cpu.r_reg(0)==0 and block(cpu,'game_preview_storage','game_preview_storage_end')==before
        cpu.audit_reads()
        return dict(passed=True,seed=case['seed'],end=case['end'],x=x,y=y,budget=budget,poison=poison,
            max_step_cycles=max(cycles),stack=cpu.stack_bytes,policy_switches=switches,
            populated_history_isolated=True,stale_cancel_neutral=True)


def byte_audit(standalone,native):
    options=dict(begin_name='game_preview_predictor_code_begin',end_name='game_preview_predictor_code_end',external_names=EXTERNALS)
    a=normalized(standalone,standalone.parent/'match-core.lst',**options)
    b=normalized(native,native.parent/'native.lst',**options)
    assert a==b,'Actual native/standalone predictor bytes differ'
    return dict(passed=True,bytes=len(a[0]),relocations=a[1],branches=a[2],sha256=hashlib.sha256(a[0]).hexdigest())


def guard_cases(image,symbols,case):
    """Admission partitions are initialized once; safe rejects also replay fully.

    Invalid owner/stage bytes are admission-only negative controls, not evidence
    of naturally reachable gameplay or permission to dispatch corrupt states.
    """
    source=case['source'];score=offset(symbols,'game_score_state')
    cases=[('exact-policy',{},dict(policy=0),1,True),
        ('serve-kind',{},dict(kind=3),1,True),
        ('invalid-kind',{},dict(kind=4),1,False),
        ('missing-incoming',{},dict(incoming_valid=0),1,False),
        ('lifecycle',{offset(symbols,'game_lifecycle')+1:0},{},2,True),
        ('uninitialized',{offset(symbols,'game_score_initialized'):0},{},3,True),
        ('idle-stage',{score:0},{},3,True),
        ('invalid-stage',{score:255},{},3,False),
        ('pending-command',{offset(symbols,'game_core_command'):1},{},4,False),
        ('restart',{offset(symbols,'game_restart_context'):1},{},4,True),
        ('suppressed-input',{offset(symbols,'game_mode'):source[offset(symbols,'game_mode')]|4},{},4,True),
        ('round-mode',{offset(symbols,'game_mode'):source[offset(symbols,'game_mode')]|32},{},4,False),
        ('result-mode',{offset(symbols,'game_mode'):source[offset(symbols,'game_mode')]|64},{},4,False),
        ('two-human-mode',{offset(symbols,'game_mode'):source[offset(symbols,'game_mode')]|128},{},4,False),
        ('invalid-end',{},dict(end=2),5,False),
        ('scorer-ai',{score+1:0},{},5,False),
        ('score-flags',{offset(symbols,'game_score_flags'):0},{},5,False),
        ('end-mode',{offset(symbols,'game_mode'):source[offset(symbols,'game_mode') ]^16},{},5,False),
        ('human-ai',{54+case['end']:1},{},5,False),
        ('opponent-human',{54+(case['end']^1):0},{},5,False),
        ('owner',{offset(symbols,'game_lower_owner'):2},{},6,False),
        ('upper-owner',{offset(symbols,'game_upper_owner'):2},{},6,False),
        ('wrong-side',{offset(symbols,'game_contact'):source[offset(symbols,'game_contact')]^64},{},7,False),
        ('terminal',{offset(symbols,'game_contact'):source[offset(symbols,'game_contact')]|1},{},7,True),
        ('launch-pending',{offset(symbols,'game_flight'):source[offset(symbols,'game_flight')]|128},{},7,False),
        ('no-flight',{offset(symbols,'game_flight'):0},{},7,True)]
    rows=[]
    for name,changes,options,reason,replay in cases:
        origin=bytearray(source)
        for position,value in changes.items():origin[position]=value
        origin=bytes(origin)
        with Core(image,symbols,initial=bytes([0x69])*318,poison=0x96,readonly=READONLY) as cpu:
            scratch=symbols['game_preview_held_state'];cpu.mem.w_block(scratch,origin)
            cpu.mem.w16(symbols['game_preview_projection_requested'],options.get('policy',1))
            cpu.mem.w16(symbols['game_preview_kind'],options.get('kind',0))
            cpu.mem.w16(symbols['game_preview_end'],options.get('end',case['end']))
            cpu.mem.w8(symbols['game_preview_incoming_valid'],options.get('incoming_valid',1))
            saved=outside(cpu,scratch)
            old_trace=cpu.trace
            def trace(mode,width,address,value):
                if mode=='W' and not STACK_BASE<=address<address+(1<<width)<=STACK_TOP+4:
                    raise AssertionError(('Admission CPU write',name,hex(address)))
                if mode=='R' and address<cpu.stop and address+(1<<width)>cpu.start:
                    raise AssertionError(('Admission canonical read',name,hex(address)))
                old_trace(mode,width,address,value)
            cpu.mem.set_trace_func(trace)
            registers={r:(0x965aa569+r*0x1010101)&0xffffffff for r in range(15)}
            registers[13]=scratch;cpu.cpu.w_sr(0x271f)
            cpu.call('game_preview_predictor_eligible',registers)
            assert cpu.cpu.r_reg(0)==0 and cpu.cpu.r_reg(1)==reason,(name,reason)
            assert all(cpu.cpu.r_reg(r)==registers[r] for r in range(2,15)),name
            assert bytes(cpu.mem.r_block(scratch,318))==origin and outside(cpu,scratch)==saved,name
            cpu.audit_reads()
        if replay:
            reference=execute(image,symbols,origin,case['stream'],case['end'],True,False,0xa5,**options)
            candidate=execute(image,symbols,origin,case['stream'],case['end'],True,True,0x96,**options)
            compare(reference,candidate)
            assert candidate['route']==0 and candidate['reason']==reason and candidate['predictor_ticks']==0,name
        rows.append(dict(name=name,reason=reason,passed=True,registers_preserved=True,
            admission_read_only=True,full_state_events_equal=replay,scope='full-fallback' if replay else 'admission-only'))
    return rows


def run(executable,raw):
    from native_evidence import atomic_json
    image,symbols=load_image(executable)
    cases=[c for seed in SEEDS for c in discover(image,symbols,seed)]
    cases.extend(discover(image,symbols,0xace1,upper=True))
    guards=guard_cases(image,symbols,cases[0])
    rows=[];apis=[];raw=Path(raw);raw.mkdir(parents=True,exist_ok=True)
    atomic_json(raw/'guard-cases.json',guards)
    irregular=[]
    case=cases[0];origin=bytearray(case['source']);origin[3]=100;origin[2]=153
    stream=[]
    for index,operation in enumerate(case['stream']):
        stream.append(operation)
        if index%11==2:stream.extend([('game_core_latch_actions',[]),('game_core_clear_inputs',[]),
            ('game_core_sample_pads',[16,0]),('game_round_poll',[])])
    for held in (True,False):
        reference=execute(image,symbols,bytes(origin),stream,0,held,False,0xa5)
        candidate=execute(image,symbols,bytes(origin),stream,0,held,True,0x96,omitted_poison=True)
        compare(reference,candidate)
        operations=sorted(set(r['operation'] for r in candidate['boundaries']))
        assert {'game_core_clear_inputs','game_core_latch_actions','game_round_poll'}<=set(operations)
        atomic_json(raw/f'irregular-{int(held)}.json',dict(reference=reference,candidate=candidate))
        irregular.append(dict(passed=True,held=held,operations=operations,required_observations_cursors_equal=True))
    for case in cases:
        end=case['end'];human=case['human']
        x,y=(human['x'],human['y']) if human else ((111,153) if end==0 else (128,31))
        positions=[(x,y),(max(64 if end else 40,x-11),y),(64 if end else 40,7 if end else 153)]
        if end==0 and case['seed']==0xace1:positions=[(100,153),(111,153),(114,153),(111,128),(40,153)]
        for x,y in dict.fromkeys(positions):
            references=[]
            for held in (True,False):
                origin=bytearray(case['source']);origin[end*10+3]=x;origin[end*10+2]=y;origin=bytes(origin)
                reference=execute(image,symbols,origin,case['stream'],end,held,False,0xa5)
                references.append(reference)
                for poison in (0xa5,0x96):
                    candidate=execute(image,symbols,origin,case['stream'],end,held,True,poison,omitted_poison=True)
                    compare(reference,candidate);assert candidate['route']==1 and candidate['predictor_ticks']>0
                    identity=f"{case['seed']:04x}-{end}-{x}-{y}-{int(held)}-{poison:02x}"
                    atomic_json(raw/(identity+'.json'),dict(reference=reference,candidate=candidate))
                    rows.append(dict(passed=True,seed=case['seed'],end=end,x=x,y=y,held=held,poison=poison,
                        reference_cycles=reference['runtime_cycles'],candidate_cycles=candidate['runtime_cycles'],
                        guard_cycles=candidate['guard_cycles'],termination=candidate['termination'],
                        low_height_contact=any(l['flight']&8 for l in candidate['ledger']['launches']),
                        wide=candidate['ledger']['wide'],handoffs=candidate['ledger']['handoffs'],
                        retained_bytes=candidate['retained_bytes'],omitted_reads=candidate['omitted_reads'],
                        stack=candidate['stack'],natural_exchange=end==1))
            # Every grouping; poison alternates without multiplying identical
            # fixture work. Natural upper and three seed contexts are retained.
            if (x,y)==positions[0]:
                for budget in (1,2,3,4):apis.append(api_case(image,symbols,case,x,y,budget,0xa5 if budget&1 else 0x96,references))
    assert any(r['wide'] for r in rows) and any(r['handoffs'] for r in rows)
    assert any(r['termination']=='no-contact' for r in rows) and any(r['natural_exchange'] for r in rows)
    assert any(r['low_height_contact'] for r in rows)
    return dict(passed=True,seeds=list(SEEDS),rows=rows,api_cases=apis,guard_cases=guards,
        irregular_cases=irregular,full_private_bytes=318,
        added_metadata_bytes=6,reference_independent=True,all_envelopes_compared=True,
        canonical_read_write_guard=True,original_exact_contract_unchanged=True,
        scope='Selective emitted-core preview observations with real natural exchange; no native timing/full release claim')
