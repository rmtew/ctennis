"""Test-only causal-slice experiment; never builds or changes production.

Both executions start independently from one immutable origin. Original emitted
bodies are the oracle; candidates call actual emitted helpers, not a physics
model. Raw state/evidence and immutable attempts remain outside Git.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'scripts'))
from build_match_core import load_image
from match_core_cpu import Core, STACK_BASE, STACK_TOP, cpu_tool_inputs
from preview_proof import fixture, point
from run_shared_match_core import READONLY


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def offset(symbols, name):
    return symbols[name]-symbols['game_core_state']


def edited_inputs(state, symbols, end, held, values):
    result=list(values)
    owner=state[offset(symbols,'game_lower_owner')+end]
    result[owner]=(result[owner]&0xffc0)|(16 if held else 0)
    return result


def outside(cpu, scratch):
    pieces=[]
    for lo,hi in cpu.regions:
        for a,b in ((lo,min(hi,scratch)),(max(lo,scratch+318),hi)):
            if a<b:pieces.append(bytes(cpu.mem.r_block(a,b-a)))
    return pieces


def execute(image, symbols, origin, paused, stream, end, held, profile, poison):
    retained=set(range(318)) if profile=='original' else (
        set(range(60))|{offset(symbols,'game_mode')}|set(range(offset(symbols,'game_audio_voices'),offset(symbols,'game_display_state')))|
        set(range(offset(symbols,'game_input_bits'),offset(symbols,'game_scene_objects')))|
        set(range(offset(symbols,'game_score_flags'),318)))
    initial=bytes(value if i in retained else poison for i,value in enumerate(origin))
    samples=[point(origin,symbols)] # Immutable input projection, not an oracle intermediate.
    attempts=[];launches=[];cycles=0;phase=0;launched=False;initial_reads=set();written=set()
    random_calls=0;wide_contacts=[];handoffs=[];clamps=[];phases=[];termination='stream-exhausted'
    with Core(image,symbols,initial=paused,poison=poison,readonly=READONLY) as cpu:
        scratch=symbols['game_preview_held_state']
        cpu.mem.w_block(scratch,initial)
        cpu.mem.w8(symbols['game_preview_active'],2) # Observation sinks are private, not live output.
        cpu.mem.w8(symbols['game_history_mode'],0) # No recorder/preview hook mutations.
        saved=outside(cpu,scratch)
        old_trace=cpu.trace
        def trace(mode,width,address,value):
            size=1<<width
            if mode=='R' and address<cpu.stop and address+size>cpu.start:
                raise AssertionError(('Private execution read paused canonical state',hex(address),size))
            if scratch<=address and address+size<=scratch+318:
                indices=set(range(address-scratch,address-scratch+size))
                if mode=='R':initial_reads.update(indices-written)
                else:written.update(indices)
            elif mode=='W' and not STACK_BASE<=address<=STACK_TOP:
                raise AssertionError(('Non-private CPU store',hex(address),size))
            old_trace(mode,width,address,value)
        cpu.mem.set_trace_func(trace)
        def state():return bytes(cpu.mem.r_block(scratch,318))
        def value(name):return cpu.mem.r8(scratch+offset(symbols,name))
        def observe(pc):
            nonlocal launched,random_calls
            cpu.instruction(pc)
            if pc==symbols['game_random']:random_calls+=1
            if pc==symbols['game_player_tick'] and cpu.cpu.r_reg(7)&0xffff==end:
                p=value('game_lower_phase' if end==0 else 'game_upper_phase')
                if not phases or phases[-1]['value']!=p:phases.append(dict(phase=phase,value=p))
            if pc==symbols['game_serve_timed'] and value('game_serve_clock')==32:
                handoffs.append(dict(phase=phase,end=cpu.cpu.r_reg(7)&0xffff))
            if pc==symbols['game_scene_finish_tick'] and value('game_ball_y')>=192 and value('game_court_y')!=194:
                clamps.append(dict(phase=phase,ball_y=value('game_ball_y'),court_y=value('game_court_y')))
            if pc==symbols['game_return_vector'] and cpu.cpu.r_reg(7)&0xffff==end:
                distance=abs(value('game_ball_x')-(cpu.cpu.r_reg(6)&0xffff))
                if distance>=13:wide_contacts.append(dict(phase=phase,distance=distance,random_calls=random_calls))
            if pc in (symbols['game_history_contact_begin'],symbols['game_history_contact'],symbols['game_history_serve']):
                actual_end=cpu.cpu.r_reg(7)&0xffff
                if actual_end!=end:return
                if pc==symbols['game_history_contact_begin']:
                    # Actual receiving-side/phase-gated attempt, before geometry tests.
                    attempts.append(dict(phase=phase,projection=point(state(),symbols).hex(),
                                         player_xy=list(state()[end*10+2:end*10+4]),
                                         player_phase=state()[end*10]))
                else:
                    launched=True
                    launches.append(dict(phase=phase,kind='serve' if pc==symbols['game_history_serve'] else 'contact',
                        launch=list(state()[offset(symbols,'game_launch_x'):offset(symbols,'game_launch_x')+6]),
                        target=list(state()[offset(symbols,'game_target_y'):offset(symbols,'game_height')+1]),
                        flags=[value('game_contact'),value('game_flight')]))
        cpu.cpu.set_instr_hook_callback(observe)
        def call(name,args=()):
            nonlocal cycles
            regs={i:v for i,v in enumerate(args)};regs[13]=scratch
            cycles+=cpu.call(name,regs)
            assert outside(cpu,scratch)==saved,'Paused image/history mutated'
        def helper(name,regs=None):
            nonlocal cycles
            cycles+=cpu.call(name,{13:scratch,**(regs or {})})
            assert outside(cpu,scratch)==saved,'Paused image/history mutated'
        call('game_core_sample_pads_body',edited_inputs(origin,symbols,end,held,
             origin[offset(symbols,'game_input_bits'):offset(symbols,'game_input_bits')+2]))
        for name,args in stream:
            if name=='game_core_sample_pads':args=edited_inputs(state(),symbols,end,held,args)
            if name!='game_tick_dispatch':
                if profile=='original' or name!='game_round_poll':call(name+'_body',args)
                continue
            phase+=1
            if profile=='original':call('game_tick_dispatch_body')
            else:
                helper('input_update')
                if profile=='play-rng-negative' and phase==1:
                    helper('game_random',{12:scratch}) # Actual extra RNG draw: detector control.
                if profile=='human-only':
                    helper('game_prepare_controls',{12:scratch})
                    helper('game_player_tick',{12:scratch,11:scratch+end*10,7:end})
                    helper('game_ball_tick',{12:scratch})
                else:helper('game_play_tick')
                if profile!='no-scene':helper('game_scene_finish_tick')
                helper('game_advance_clocks')
            samples.append(point(state(),symbols))
            if launched:termination='launch';break
            if value('game_contact')&0x8d:termination='incoming-no-contact';break
            if phase==256:termination='incoming-limit';break
        if launched:
            for _ in range(256):
                helper('game_ball_tick',{12:scratch})
                samples.append(point(state(),symbols))
                flags=value('game_contact')
                # Test observation projection of preview.s's ordered flag policy;
                # all geometry and flags above come from actual emitted routines.
                if flags&0x8b:
                    termination='net' if flags&1 else 'out' if flags&0x88 else 'landing'
                    break
            else:termination='outgoing-limit'
        final=state();cpu.audit_reads()
        assert not cpu.events,'Private experiment emitted live outputs'
        fields=[n for n,a in symbols.items() if cpu.start<=a<cpu.stop and a-cpu.start in initial_reads]
        return dict(samples=[p.hex() for p in samples],attempts=attempts,launches=launches,
                    final_contact=final[offset(symbols,'game_contact')],
                    final_flight=final[offset(symbols,'game_flight')],termination=termination,cycles=cycles,
                    instructions=sum(cpu.visits.values()),stack_bytes=cpu.stack_bytes,
                    retained_initial_bytes=len(retained),seed_read_offsets=sorted(initial_reads),
                    omitted_seed_reads=sorted(initial_reads-retained),seed_read_symbols=sorted(fields),
                    private_final_sha256=hashlib.sha256(final).hexdigest(),paused_preserved=True,
                    random_calls=random_calls,wide_contacts=wide_contacts,handoffs=handoffs,clamps=clamps,phases=phases,
                    private_output_count=len(cpu.preview_events),live_output_count=len(cpu.events))


def comparison(expected, actual):
    for key in ('attempts','launches','samples','final_contact','final_flight','termination'):
        if expected[key]!=actual[key]:
            a,b=expected[key],actual[key]
            index=next((i for i,(x,y) in enumerate(zip(a,b)) if x!=y),min(len(a),len(b))) if isinstance(a,list) else None
            return dict(equal=False,first_field=key,index=index,
                        expected=a[index] if index is not None and index<len(a) else a,
                        actual=b[index] if index is not None and index<len(b) else b)
    return dict(equal=True)


def validate_case(record):
    """Coverage requirements and actual causal negatives, not case-name claims."""
    label=record['case']
    assert len(record['rows'])==16
    for row in record['rows']:
        ref,actual=row['reference'],row['candidate']
        assert actual['live_output_count']==0 and actual['paused_preserved']
        assert not actual['omitted_seed_reads'],'Retained input dependency missing'
        assert ref['termination'] not in ('stream-exhausted','incoming-limit','outgoing-limit')
        if row['profile']=='play':assert row['comparison']['equal'],row['comparison']
        if 'wide' in label:
            assert ref['launches'] and ref['wide_contacts']
            assert all(13<=r['distance']<=16 for r in ref['wide_contacts'])
            if row['profile']=='play-rng-negative':assert not row['comparison']['equal']
        if 'central' in label:assert ref['launches'] and not ref['wide_contacts']
        if label.endswith('miss'):assert not ref['launches'] and ref['termination']=='incoming-no-contact'
        if label.startswith('upper-'):
            assert ref['handoffs'] and any(p['value']&1 for p in ref['phases'])
            if row['profile']=='human-only':assert not row['comparison']['equal']
        if label=='declared-clamp':
            assert ref['clamps'] and ref['clamps'][0]['ball_y']==193
            if row['profile']=='no-scene':assert not row['comparison']['equal']
        if label.startswith('lower-wide') and row['profile']=='human-only':
            assert not row['comparison']['equal']
    for held in (True,False):
        for profile in ('human-only','play','no-scene','play-rng-negative'):
            pair=[r['candidate'] for r in record['rows'] if r['held']==held and r['profile']==profile]
            assert len(pair)==2 and comparison(*pair)['equal'],'Omitted initial bytes changed observations'


def discover(image,symbols):
    with Core(image,symbols,readonly=READONLY) as cpu:
        stream,states,_,launches=fixture(cpu,dispatches=512)
        contact=next(r for r in launches if r['human'] and r['kind']==1)
        incoming=max(r['origin'] for r in launches if r['end']!=contact['end'] and r['origin']<contact['origin'])
        source=states[incoming+1]
        serve=next(r['origin'] for r in launches if r['human'] and r['kind']==3)
        upper=bytearray(states[serve+1])
        # Declared initial-role fixture, not a naturally observed end exchange.
        # Same immutable origin is supplied independently to both executions.
        upper[offset(symbols,'game_mode')]|=16
        upper[offset(symbols,'game_score_flags')]=(upper[offset(symbols,'game_score_flags')]&~3)|2
        upper[offset(symbols,'game_score_state')+1]=2 # S_AI: lower AI, upper human.
        upper[offset(symbols,'game_score_state')+3]|=16 # S_MODE: human plays far end.
        upper[offset(symbols,'game_lower_owner')]=1
        upper[offset(symbols,'game_upper_owner')]=0
        boundary=bytearray(source)
        # Declared initial boundary fixture; never used as ordinary-match evidence.
        for name,value in dict(game_ball_y=193,game_court_y=193,game_ball_x=100,game_court_x=100,
            game_base_screen_y=193,game_base_y=193,game_base_x=100,game_velocity_x=0,
            game_velocity_y=4,game_velocity_z=0,game_step=0,game_flight=64,game_contact=64).items():
            boundary[offset(symbols,name)]=value
        return stream,states[max(states)],source,incoming,bytes(upper),serve,bytes(boundary)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--executable',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--case',action='append')
    parser.add_argument('--resume',action='store_true')
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    tool_paths,tool=cpu_tool_inputs()
    bindings={str(p):sha(p) for p in [Path(__file__),args.executable,*tool_paths,
        *sorted((ROOT/'scripts').glob('*.py')),*sorted((ROOT/'amiga/game').glob('*.s')),*sorted((ROOT/'amiga/game').glob('*.i'))]}
    identity=hashlib.sha256(json.dumps(bindings,sort_keys=True).encode()).hexdigest()
    manifest=args.output/'manifest.json'
    if manifest.exists():assert json.loads(manifest.read_text())['identity']==identity,'Different experiment inputs; choose fresh output directory'
    else:manifest.write_text(json.dumps(dict(identity=identity,files=bindings,tool=tool),indent=2)+'\n')
    image,symbols=load_image(args.executable)
    stream,paused,lower,incoming,upper,serve,boundary=discover(image,symbols)
    cases=[('lower-central',lower,incoming,0,100,153),('lower-wide13',lower,incoming,0,111,153),
           ('lower-wide16',lower,incoming,0,114,153),('lower-earlier',lower,incoming,0,111,128),
           ('lower-miss',lower,incoming,0,40,153),('upper-handoff',upper,serve,1,88,20),
           ('upper-wide',upper,serve,1,99,20),('upper-central',upper,serve,1,64,7),
           ('upper-miss',upper,serve,1,144,32),('declared-clamp',boundary,incoming,0,40,153)]
    selected=set(args.case or [r[0] for r in cases]);assert selected<={r[0] for r in cases}
    for label,source,cursor,end,x,y in cases:
        if label not in selected:continue
        path=args.output/(label+'.json')
        if args.resume and path.exists():
            old=json.loads(path.read_text());assert old['identity']==identity and old['complete'];print(json.dumps(dict(case=label,reused=True)),flush=True);continue
        assert not path.exists(),'Existing attempt is immutable; resume complete case or choose fresh output directory'
        record=dict(identity=identity,case=label,complete=False,origin_cursor=cursor,end=end,x=x,y=y,
                    declared_initial_role_exchange=end==1,declared_boundary_fixture=label=='declared-clamp',
                    origin_lifecycle=int.from_bytes(source[offset(symbols,'game_lifecycle'):offset(symbols,'game_lifecycle')+2],'big'),
                    origin_score_stage=source[offset(symbols,'game_score_state')],
                    origin_sha256=hashlib.sha256(source).hexdigest(),rows=[])
        path.write_text(json.dumps(record,indent=2)+'\n')
        for held in (True,False):
            origin=bytearray(source);origin[end*10+3]=x;origin[end*10+2]=y;origin=bytes(origin)
            expected=execute(image,symbols,origin,paused,stream[cursor+1:],end,held,'original',0xa5)
            for profile in ('human-only','play','no-scene','play-rng-negative'):
                for poison in (0xa5,0x96):
                    actual=execute(image,symbols,origin,paused,stream[cursor+1:],end,held,profile,poison)
                    row=dict(held=held,profile=profile,poison=poison,comparison=comparison(expected,actual),
                             reference=expected,candidate=actual)
                    record['rows'].append(row);path.write_text(json.dumps(record,indent=2)+'\n')
                    print(json.dumps(dict(case=label,held=held,profile=profile,poison=poison,
                         equal=row['comparison']['equal'],field=row['comparison'].get('first_field'),
                         reference_cycles=expected['cycles'],candidate_cycles=actual['cycles'],
                         omitted_seed_reads=actual['omitted_seed_reads'])),flush=True)
        validate_case(record)
        record['coverage_validated']=True
        record['complete']=True;path.write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(dict(output=str(args.output),identity=identity,selected=sorted(selected))),flush=True)

if __name__=='__main__':main()
