"""A1 bounded actual-core API/context proofs and independent continuations."""
from build_match_core import load_image
from history_proof import attach, attempts, cursor, field, seek
from match_core_cpu import Core
from preview_cache_proof import job
from preview_proof import fixture, protected, call_checked, block, OPERATIONS, ARITY, point, geometry
from run_shared_match_core import READONLY
from native_tools import ROOT

# API lifecycle values read from the product declaration, not gameplay rules.
def lifecycle(name):
    import re
    source=(ROOT/'amiga/game/tick.s').read_text()
    return int(re.search(r'^'+name+r' equ (\d+)$',source,re.M).group(1))

PLAYING=lifecycle('GAME_PLAYING')
TITLE=lifecycle('GAME_TITLE')



def value(state,symbols,name,width=1):
    offset=symbols[name]-symbols['game_core_state']
    return int.from_bytes(state[offset:offset+width],'big')


def table(cpu,end):
    player=cpu.symbols['game_play_state']+end*10
    phase=(cpu.mem.r8(player+1)>>3)&12
    address=cpu.symbols['game_lower_limits' if end==0 else 'game_upper_limits']+phase
    bottom,top,right,left=bytes(cpu.mem.r_block(address,4))
    assert top<bottom and left<right
    return dict(left=left,right=right,top=top,bottom=bottom,phase_offset=phase)


def candidates(index,launches):
    completed={(n,e) for n,k,e in index if k==1}
    result=[]
    for launch in launches:
        if not launch['human'] or launch['kind']!=1:continue
        probe=launch['episode_origin']
        if (probe,launch['end']) not in completed:continue
        incoming=next((other for other in reversed(launches)
            if other['end']!=launch['end'] and other['origin']<probe),None)
        if incoming is None:continue
        ordinal=next(i for i,(n,k,e) in enumerate(index) if (n,k,e)==(probe,1,launch['end']))
        result.append(dict(launch,ordinal=ordinal,incoming_origin=incoming['origin'],probe_origin=probe))
        if len(result)==2:break
    return result


def execute(cpu,ordinal,selection,x,y,stream,seed,name,budget=4,extra_observer=None):
    """Observe actual accepted-launch hooks and complete dispatch boundaries."""
    if cursor(cpu,'game_history_position')!=selection:
        if hasattr(cpu,'native_entries'):
            from preview_native_proof import seek_preserving_ledger
            seek_preserving_ledger(cpu,selection)
        else:seek(cpu,selection)
    selected=cpu.state()
    end=(1 if field(cpu,'game_score_flags',1)&2 else 0) if ordinal==0xffff else attempts(cpu)[ordinal][2]
    bodies={cpu.symbols[n+'_body']:(n,a) for n,a in zip(OPERATIONS,ARITY)}
    traces={0:[],1:[]};launches={0:[],1:[]};boundaries={0:[],1:[]}
    def observe(pc):
        if extra_observer is not None:extra_observer(pc)
        if field(cpu,'game_preview_active',1)!=2:return
        variant=field(cpu,'game_preview_variant',1)
        if pc in bodies:
            op,arity=bodies[pc]
            traces[variant].append((op,[cpu.cpu.r_reg(r)&0xffff for r in range(arity)],cpu.working_state()))
        if pc in (cpu.symbols['game_history_contact'],cpu.symbols['game_history_serve']):
            launches[variant].append(dict(end=cpu.cpu.r_reg(7)&0xffff,
                kind=1 if pc==cpu.symbols['game_history_contact'] else 3,
                dispatch=len(boundaries[variant]),serve_clock=value(cpu.working_state(),cpu.symbols,'game_serve_clock')))
        if pc==cpu.symbols['game_preview_write_point']:
            state=cpu.working_state()
            boundaries[variant].append(dict(contact=value(state,cpu.symbols,'game_contact'),
                flight=value(state,cpu.symbols,'game_flight'),lifecycle=value(state,cpu.symbols,'game_lifecycle',2)))
    costs,result=job(cpu,ordinal,x,y,observer=observe,budget=budget)
    classes=[]
    for variant in (0,1):
        accepted=launches[variant]
        human=next((i for i,event in enumerate(accepted) if event['end']==end),None)
        final=result['contexts'][variant]
        contact=value(final,cpu.symbols,'game_contact')
        outcome=result['outcomes'][variant]
        if human is not None:
            intercepted=any(event['end']!=end and event['kind']==1 for event in accepted[human+1:])
            if intercepted:classification='interception';assert outcome==4
            elif contact&1:classification='net';assert outcome==2
            elif contact&0x88:classification='out';assert outcome==3
            elif contact&2:classification='landing';assert outcome==1
            else:classification='incomplete'
        elif ordinal!=0xffff and contact&0x8d:
            classification='no-contact';assert outcome==5
        else:classification='incomplete'
        if outcome==6:
            count=len(result['paths'][variant])//8
            dispatches=cpu.mem.r16(cpu.symbols['game_preview_dispatches']+2*variant)
            assert count==256 or dispatches==256
            classification='limit'
        if outcome==7:
            # Lifecycle stops may be before execution of a recorded reset API.
            stream_cursor=cursor(cpu,'game_preview_stream_cursors') if variant==0 else int.from_bytes(cpu.mem.r_block(cpu.symbols['game_preview_stream_cursors']+8,8),'big')
            pending=stream[stream_cursor][0] if stream_cursor<len(stream) else None
            assert value(final,cpu.symbols,'game_lifecycle',2)!=value(selected,cpu.symbols,'game_lifecycle',2) or pending in ('game_core_init','game_core_select','game_core_return_title')
            classification='lifecycle'
        assert boundaries[variant] or classification=='lifecycle', 'No full actual dispatch boundary observed'
        classes.append(classification)
    prefix=result['prefix']
    assert result['paths'][0][:prefix*8]==result['paths'][1][:prefix*8]
    assert bool(field(cpu,'game_preview_coincident'))==(geometry([result['paths'][0][i:i+8] for i in range(0,len(result['paths'][0]),8)])==geometry([result['paths'][1][i:i+8] for i in range(0,len(result['paths'][1]),8)]))
    observation=dict(name=name,seed=seed,ordinal=ordinal,selection=selection,end=end,x=x,y=y,
        selected=selected,stream=stream,traces=traces,result=result,classes=classes,launches=launches,boundaries=boundaries,
        costs=costs,bounds=table(cpu,end),coincident=bool(field(cpu,'game_preview_coincident')))
    return observation


def continuous(image,symbols,observation,native_sinks=False):
    """One actual edited initialization, then uninterrupted original API policy."""
    result=observation['result'];selection=observation['selection'];stream=observation['stream']
    for variant in (0,1):
        with Core(image,symbols,initial=None if native_sinks else result['edited'],readonly=READONLY) as cpu:
            if native_sinks:
                from preview_native_proof import native_entries,assert_native_entries,outside_canonical
                # Real setup with observation traps is outside the reference.
                # Establish frozen metadata before the one edited initial state.
                cpu.call_logical('game_core_init',[]);attach(cpu)
                native_entries(cpu,image)
                cpu.call('game_history_freeze')
                cpu.mem.w8(symbols['game_history_replaying'],1)
                cpu.mem.w_block(cpu.start,result['edited'])
                cpu.clear_events()
                cpu.native_semantic_events.clear()
                saved_nonstate=outside_canonical(cpu)
            generated=[result['paths'][variant][i:i+8] for i in range(0,result['prefix']*8,8)]
            for ordinal,(name,args,before) in enumerate(observation['traces'][variant]):
                if ordinal==0:
                    expected_name='game_core_sample_pads'
                    offset=symbols['game_input_bits']-symbols['game_core_state']
                    expected_args=list(result['edited'][offset:offset+2])
                else:
                    position=selection+ordinal-1
                    if position<len(stream):expected_name,expected_args=stream[position];expected_args=list(expected_args)
                    else:
                        phase=(position-len(stream))%4
                        expected_name=('game_round_poll','game_core_sample_pads','game_core_sample_result','game_tick_dispatch')[phase]
                        offset=symbols['game_input_bits']-symbols['game_core_state']
                        expected_args=list(before[offset:offset+2]) if phase==1 else [0]*6 if phase==2 else []
                if expected_name=='game_core_sample_pads':
                    owner=value(before,symbols,'game_lower_owner') if observation['end']==0 else value(before,symbols,'game_upper_owner')
                    expected_args[owner]=(expected_args[owner]&0xffc0)|(16 if variant==0 else 0)
                assert (name,args)==(expected_name,expected_args), 'Preview changes known API order or opponent/result input'
                assert cpu.state()==before, 'Chunked state differs from uninterrupted actual core'
                cpu.call_logical(name,args)
                if native_sinks:
                    assert_native_entries(cpu)
                    assert outside_canonical(cpu)==saved_nonstate, 'Native continuous reference changes history/presentation/input/preview globals'
                if name=='game_tick_dispatch' and len(generated)<256:generated.append(point(cpu.state(),symbols))
            assert cpu.state()==result['contexts'][variant]
            assert b''.join(generated)==result['paths'][variant]
            assert (cpu.native_semantic_events if native_sinks else cpu.events)==result['outputs'][variant]
            cpu.audit_reads()
    return dict(passed=True,continuous_state_path_output_equal=True,independent_continuation_policy_equal=True,
        name=observation['name'],seed=observation['seed'],ordinal=observation['ordinal'],selection=selection,
        end=observation['end'],x=observation['x'],y=observation['y'],bounds=observation['bounds'],
        classes=observation['classes'],actual_accepted_launches=observation['launches'],
        actual_final_boundaries=[events[-1] if events else None for events in observation['boundaries'].values()],
        path_counts=[len(path)//8 for path in result['paths']],prefix_samples=result['prefix'],
        incoming_origin=result['incoming'],action_boundary=result['action'],coincident=observation['coincident'],
        costs=observation['costs'],live_history_output_preserved=True,edited_only_position_changed=True,
        selected_state=observation['selected'].hex(),edited_state=result['edited'].hex(),
        final_states=[state.hex() for state in result['contexts']],
        paths=[path.hex() for path in result['paths']],ordered_outputs=result['outputs'])


def human_serve_wait(cpu,cap=512,phase_wanted=0x40):
    """Actual controlled fixture, including a completed first serve."""
    launches=[]
    def observe(pc):
        cpu.instruction(pc)
        if pc==cpu.symbols['game_history_serve']:
            end=cpu.cpu.r_reg(7)&0xffff
            if cpu.mem.r8(cpu.symbols['game_play_state']+54+end)==0:
                launches.append(dict(origin=cursor(cpu),end=end,entry_clock=field(cpu,'game_serve_clock',1)))
    cpu.cpu.set_instr_hook_callback(observe)
    cpu.call_logical('game_core_init',[]);attach(cpu)
    stream=[('game_core_select',[0,0xace1,0])]
    cpu.call_logical(*stream[0])
    for tick in range(cap):
        packet=[0 if tick<8 or launches else 16,0]
        for name,args in (('game_round_poll',[]),('game_core_sample_pads',packet),
                ('game_core_sample_result',[0]*6),('game_tick_dispatch',[])):
            stream.append((name,args));cpu.call_logical(name,args)
        end=1 if field(cpu,'game_score_flags',1)&2 else 0
        player=cpu.symbols['game_play_state']+end*10
        if (launches and field(cpu,'game_lifecycle')==PLAYING and cpu.mem.r8(player)==phase_wanted
                and not cpu.mem.r8(cpu.symbols['game_play_state']+54+end)):
            cpu.cpu.set_instr_hook_callback(cpu.instruction)
            cpu.actual_serve_launch_observations=launches
            return stream,end,cursor(cpu),cpu.mem.r8(player)
    raise AssertionError(f'Controlled fixture does not reach human serve phase {phase_wanted:#04x} after a real launch within512dispatches')


def stale_title(executable):
    image,symbols=load_image(executable)
    with Core(image,symbols,readonly=READONLY) as cpu:
        stream,end,serve_cursor,phase=human_serve_wait(cpu)
        index=attempts(cpu)
        ordinal=next((i for i,(_,kind,owner) in enumerate(index) if kind==3 and owner==end),None)
        assert ordinal is not None, 'Stale-title fixture lacks genuine completed serve index'
        bounds=table(cpu,end)
        x,y=bounds['left'],bounds['top']
        cpu.call_logical('game_core_return_title',[])
        assert field(cpu,'game_lifecycle')==TITLE
        assert cpu.mem.r8(symbols['game_play_state']+end*10)==phase and phase&0xe0
        cpu.call('game_history_freeze')
        saved=protected(cpu);preview=block(cpu,'game_preview_storage','game_preview_storage_end')
        for candidate in (0xffff,ordinal):
            call_checked(cpu,'game_preview_request',{0:field(cpu,'game_preview_generation',4),1:candidate,2:x,3:y},saved)
            assert cpu.cpu.r_reg(0)==0 and block(cpu,'game_preview_storage','game_preview_storage_end')==preview
        cpu.audit_reads()
        return dict(passed=True,operations=len(stream)+1,serve_cursor=serve_cursor,
            retained_serve_ordinal=ordinal,end=end,stale_phase=phase,lifecycle=TITLE,
            fallback_rejected=True,historical_rejected=True,full_live_history_output_preview_preserved=True)



def postlaunch_rejection(executable):
    image,symbols=load_image(executable)
    with Core(image,symbols,readonly=READONLY) as cpu:
        stream,end,selection,phase=human_serve_wait(cpu,phase_wanted=0x20)
        clock=field(cpu,'game_serve_clock',1)
        assert clock==0x11 and field(cpu,'game_lifecycle')==PLAYING
        assert cpu.actual_serve_launch_observations and all(event['entry_clock']==0x10 for event in cpu.actual_serve_launch_observations)
        bounds=table(cpu,end);player=symbols['game_play_state']+end*10
        x,y=cpu.mem.r8(player+3),cpu.mem.r8(player+2)
        assert bounds['left']<=x<bounds['right'] and bounds['top']<=y<bounds['bottom']
        cpu.call('game_history_freeze')
        saved=protected(cpu);preview=block(cpu,'game_preview_storage','game_preview_storage_end')
        call_checked(cpu,'game_preview_request',{0:field(cpu,'game_preview_generation',4),1:0xffff,2:x,3:y},saved)
        assert cpu.cpu.r_reg(0)==0 and block(cpu,'game_preview_storage','game_preview_storage_end')==preview
        cpu.audit_reads()
        return dict(passed=True,lifecycle=PLAYING,phase=phase,serve_clock=clock,operations=len(stream),
            actual_human_launch_observed=True,actual_launch_observations=cpu.actual_serve_launch_observations,
            launch_entry_clock=cpu.actual_serve_launch_observations[0]['entry_clock'],first_postlaunch_boundary_clock=clock,
            legal_position_verified=True,request_rejected=True,
            full_live_history_output_preview_preserved=True)


def timed_prelaunch(executable):
    image,symbols=load_image(executable);observations=[];clocks=[]
    for wanted in (0x0f,0x10):
        with Core(image,symbols,readonly=READONLY) as cpu:
            launches=[]
            def observe(pc):
                cpu.instruction(pc)
                if pc==symbols['game_history_serve']:launches.append(cursor(cpu))
            cpu.cpu.set_instr_hook_callback(observe)
            cpu.call_logical('game_core_init',[]);attach(cpu)
            stream=[('game_core_select',[0,0xace1,0])];cpu.call_logical(*stream[0])
            for tick in range(512):
                for name,args in (('game_round_poll',[]),('game_core_sample_pads',[0 if tick<8 else 16,0]),
                        ('game_core_sample_result',[0]*6),('game_tick_dispatch',[])):
                    stream.append((name,args));cpu.call_logical(name,args)
                end=1 if field(cpu,'game_score_flags',1)&2 else 0
                player=symbols['game_play_state']+end*10
                if cpu.mem.r8(player)==0x20 and field(cpu,'game_serve_clock',1)==wanted:break
            else:raise AssertionError(f'No actual timed prelaunch boundary clock{wanted} within512dispatches')
            assert not launches, 'Declared timed prelaunch boundary already executed a serve hook'
            assert field(cpu,'game_lifecycle')==PLAYING
            cpu.cpu.set_instr_hook_callback(cpu.instruction)
            selection=cursor(cpu);x,y=cpu.mem.r8(player+3),cpu.mem.r8(player+2)
            cpu.call('game_history_freeze')
            observation=execute(cpu,0xffff,selection,x,y,stream,0xace1,f'timed-prelaunch-{wanted}')
            assert any(event['end']==end and event['kind']==3 for event in observation['launches'][0])
            assert all(event['serve_clock']==0x10 for event in observation['launches'][0] if event['kind']==3)
            observations.append(observation);clocks.append(wanted);cpu.audit_reads()
    return dict(passed=True,phase=0x20,complete_boundary_clocks=clocks,launch_entry_clock=0x10,
        actual_launch_absent_before_requests=True,held_actual_launch_after_requests=True,
        cases=[continuous(image,symbols,o) for o in observations])

def current_fallback(executable):
    image,symbols=load_image(executable)
    with Core(image,symbols,readonly=READONLY) as cpu:
        stream,end,selection,phase=human_serve_wait(cpu)
        bounds=table(cpu,end)
        player=symbols['game_play_state']+end*10
        x,y=cpu.mem.r8(player+3),cpu.mem.r8(player+2)
        assert bounds['left']<=x<bounds['right'] and bounds['top']<=y<bounds['bottom']
        assert field(cpu,'game_lifecycle')==PLAYING
        cpu.call('game_history_freeze')
        observation=execute(cpu,0xffff,selection,x,y,stream,0xace1,'current-human-serve-fallback')
        assert observation['classes'][1]=='limit'
        assert len(observation['result']['paths'][1])//8==256
        assert not any(event['end']==end for event in observation['launches'][1])
        cpu.audit_reads()
    report=continuous(image,symbols,observation)
    return dict(report,lifecycle=PLAYING,phase=phase,human=True,legal_position_verified=True,
        released_no_launch=True,released_outgoing_path_claimed=False,total_sample_limit=256)


def lifecycle_stops(executable):
    image,symbols=load_image(executable)
    observations=[]
    resets=(('game_core_init',[]),('game_core_select',[0,0x1234,0]),('game_core_return_title',[]))
    for reset,args in resets:
        with Core(image,symbols,readonly=READONLY) as cpu:
            stream,end,selection,_=human_serve_wait(cpu)
            player=symbols['game_play_state']+end*10
            x,y=cpu.mem.r8(player+3),cpu.mem.r8(player+2)
            continuation=[('game_core_clear_inputs',[]),('game_core_latch_actions',[]),
                ('game_core_sample_result',[0]*6),(reset,args)]
            for name,packet in continuation:
                stream.append((name,packet));cpu.call_logical(name,packet)
            cpu.call('game_history_freeze');seek(cpu,selection)
            observation=execute(cpu,0xffff,selection,x,y,stream,0xace1,'non-dispatch-'+reset)
            assert observation['classes']==['lifecycle','lifecycle']
            assert not observation['boundaries'][0] and not observation['boundaries'][1]
            assert observation['result']['outcomes']==[7,7]
            assert all(trace[-1][0]=='game_core_sample_result' for trace in observation['traces'].values())
            observations.append(observation);cpu.audit_reads()
    return dict(passed=True,reset_operations=[name for name,_ in resets],
        clear_latch_result_order_preserved=True,reset_not_executed=True,
        cases=[continuous(image,symbols,o) for o in observations])


def partial_replacement(executable):
    image,symbols=load_image(executable)
    with Core(image,symbols,readonly=READONLY) as cpu:
        stream,_,_,launches=fixture(cpu)
        eligible=candidates(attempts(cpu),launches)
        assert eligible, 'Partial replacement fixture lacks completed return'
        candidate=eligible[0];ordinal=candidate['ordinal'];selection=candidate['origin']
        cpu.call('game_history_freeze');seek(cpu,selection)
        saved=protected(cpu);x,y=candidate['x'],candidate['y']
        bounds=table(cpu,candidate['end'])
        changed_x=x+1 if x+1<bounds['right'] else x-1
        assert bounds['left']<=changed_x<bounds['right'] and changed_x!=x
        records=[]
        for wanted in (1,3):
            old=field(cpu,'game_preview_generation',4)
            request_cycles=call_checked(cpu,'game_preview_request',{0:old,1:ordinal,2:x,3:y},saved)
            assert cpu.cpu.r_reg(0)==1 and field(cpu,'game_preview_status')==1
            generation=old+1;cycles=[];operations=[]
            bodies={symbols[name+'_body'] for name in OPERATIONS}
            def step():
                before=sum(cpu.visits.get(pc,0) for pc in bodies)
                cycles.append(call_checked(cpu,'game_preview_step',{0:generation,1:1},saved))
                operations.append(sum(cpu.visits.get(pc,0) for pc in bodies)-before)
                assert operations[-1]<=1
            for _ in range(8192):
                step()
                assert cpu.cpu.r_reg(0)==1
                if field(cpu,'game_preview_status')==wanted:break
                assert field(cpu,'game_preview_status')<5
            else:raise AssertionError('Partial replacement did not reach declared RESOLVE/HELD phase')
            if wanted==3:
                step()
                assert cpu.cpu.r_reg(0)==1 and field(cpu,'game_preview_status')==3
            before_count=field(cpu,'game_preview_counts')
            replace_cycles=call_checked(cpu,'game_preview_request',{0:generation,1:ordinal,2:changed_x,3:y},saved)
            assert cpu.cpu.r_reg(0)==1 and field(cpu,'game_preview_generation',4)==generation+1
            assert field(cpu,'game_preview_status')==1 and field(cpu,'game_preview_cache_valid')==0
            assert field(cpu,'game_preview_x')==changed_x and field(cpu,'game_preview_y')==y
            preview=block(cpu,'game_preview_storage','game_preview_storage_end')
            for api,args in (('game_preview_step',{0:generation,1:4}),
                    ('game_preview_cancel',{0:generation}),('game_preview_result',{0:generation}),
                    ('game_preview_result',{0:generation+1})):
                call_checked(cpu,api,args,saved)
                assert cpu.cpu.r_reg(0)==0 and block(cpu,'game_preview_storage','game_preview_storage_end')==preview
            expected=bytearray(cpu.state())
            player=symbols['game_play_state']-symbols['game_core_state']+candidate['end']*10
            expected[player+3]=changed_x;expected[player+2]=y
            replacement_cycles=[];replacement_operations=[]
            for _ in range(8192):
                before=sum(cpu.visits.get(pc,0) for pc in bodies)
                replacement_cycles.append(call_checked(cpu,'game_preview_step',{0:generation+1,1:1},saved))
                replacement_operations.append(sum(cpu.visits.get(pc,0) for pc in bodies)-before)
                assert replacement_operations[-1]<=1
                assert cpu.cpu.r_reg(0)==1
                if field(cpu,'game_preview_status')==2:break
                assert field(cpu,'game_preview_status')==1
            else:raise AssertionError('Replacement cold resolver did not reach edited PRIME within8192calls')
            assert block(cpu,'game_preview_edited_state','game_preview_held_state')==bytes(expected)
            records.append(dict(phase=wanted,retired_generation=generation,new_generation=generation+1,
                cold_restart=True,old_and_partial_results_unavailable=True,
                full_live_history_output_preserved=True,partial_prefix_samples=before_count,
                old_x=x,old_y=y,new_x=changed_x,new_y=y,edited_only_position_changed=True,
                replacement_resolver_worker_calls=len(replacement_cycles),
                replacement_resolver_cpu_cycles=sum(replacement_cycles),
                request_cpu_cycles=request_cycles,replacement_cpu_cycles=replace_cycles,
                maximum_worker_cpu_cycles=max(cycles+replacement_cycles),
                maximum_worker_operations=max(operations+replacement_operations),
                old_phase_worker_calls=len(cycles),
                maximum_replacement_resolver_cpu_cycles=max(replacement_cycles),
                worker_calls=len(cycles)+len(replacement_cycles)))
            call_checked(cpu,'game_preview_cancel',{0:generation+1},saved);assert cpu.cpu.r_reg(0)==1
        cpu.audit_reads()
        return dict(passed=True,cases=records,maximum_stack_bytes=cpu.stack_bytes)


def no_contact(executable):
    image,symbols=load_image(executable)
    observation=None;tested=[]
    with Core(image,symbols,readonly=READONLY) as cpu:
        # A released start edge, then held serve; no human movement is fabricated.
        stream,states,_,launches=fixture(cpu,controls=lambda tick:[0 if tick<8 else 16,0])
        index=attempts(cpu)
        candidate=next(((i,n,end) for i,(n,k,end) in enumerate(index) if k==2),None)
        assert candidate is not None, 'Bounded neutral-control fixture lacks a completed actual miss'
        ordinal,selection,end=candidate
        incoming=next((event for event in reversed(launches)
            if event['end']!=end and event['origin']<selection),None)
        assert incoming is not None, 'Completed miss lacks retained actual incoming launch'
        cpu.call('game_history_freeze');seek(cpu,selection);bounds=table(cpu,end)
        xs=sorted({bounds['left'],(bounds['left']+bounds['right']-1)//2,bounds['right']-1})
        ys=sorted({bounds['top'],(bounds['top']+bounds['bottom']-1)//2,bounds['bottom']-1})
        for x in xs:
            for y in ys:
                candidate_observation=execute(cpu,ordinal,selection,x,y,stream,0xace1,'completed-miss-no-contact')
                tested.append(dict(x=x,y=y,classes=candidate_observation['classes']))
                if 'no-contact' in candidate_observation['classes']:
                    observation=candidate_observation;break
            if observation is not None:break
        assert observation is not None, 'Nine legal table positions did not produce actual NO_CONTACT; no bound expansion'
        cpu.audit_reads()
    report=continuous(image,symbols,observation)
    for variant,classification in enumerate(observation['classes']):
        if classification=='no-contact':assert not any(event['end']==end for event in observation['launches'][variant])
    return dict(report,completed_index_kind=2,incoming_origin_observed=incoming['origin'],
        tested_positions=tested,no_contact_outgoing_path_claimed=False,position_cap=9)


def truncated_completed(executable):
    """Keep a real completed probe, but evict the real incoming launch.

    Padding consists only of actual non-tick round-poll calls. No canonical
    value or expected intermediate state is injected. The 64-boundary gap is
    created before the probe so sparse checkpoint alignment cannot hide it.
    """
    image,symbols=load_image(executable)
    with Core(image,symbols,readonly=READONLY) as cpu:
        cpu.call_logical('game_core_init',[]);attach(cpu)
        stream=[];accepted=[]
        def observe(pc):
            cpu.instruction(pc)
            if pc==symbols['game_history_contact']:
                accepted.append((cursor(cpu),cpu.cpu.r_reg(7)&0xffff))
        cpu.cpu.set_instr_hook_callback(observe)
        def call(name,args):
            assert len(stream)<8192, 'Truncated-context fixture exceeds declared8192logicaloperation cap'
            stream.append((name,args));cpu.call_logical(name,args)
        call('game_core_select',[0,0xace1,0])
        incoming=None;completed=None;between=0
        for tick in range(512):
            before=len(accepted)
            for name,args in (('game_round_poll',[]),
                    ('game_core_sample_pads',[(16 if tick%64>=8 else 0)|(8 if tick%96<48 else 4),0]),
                    ('game_core_sample_result',[0]*6),('game_tick_dispatch',[])):
                call(name,args)
            if incoming is None:
                first=next(((n,end) for n,end in accepted[before:]
                    if cpu.mem.r8(symbols['game_play_state']+54+end)),None)
                if first is not None:
                    incoming,end=first
                    assert not field(cpu,'game_history_probe_active',1), 'Probe starts in incoming-launch dispatch; fixture cannot insert approved gap'
                    for _ in range(128):call('game_round_poll',[])
                    between=128
            if incoming is not None:
                completed=next(((i,n,kind,end) for i,(n,kind,end) in enumerate(attempts(cpu))
                    if kind in (1,2) and n>incoming+between),None)
                if completed is not None:break
        assert incoming is not None and completed is not None, 'No completed incoming episode within512dispatches'
        _,probe,kind,end=completed
        assert (incoming//64+1)*64<=probe, 'Sparse checkpoint gap does not separate incoming and probe'
        while cursor(cpu,'game_history_oldest')<=incoming:call('game_round_poll',[])
        oldest=cursor(cpu,'game_history_oldest')
        assert incoming<oldest<=probe
        ordinal=next((i for i,(n,k,e) in enumerate(attempts(cpu)) if (n,k,e)==(probe,kind,end)),None)
        assert ordinal is not None, 'Completed probe was evicted with incoming launch'
        cpu.cpu.set_instr_hook_callback(cpu.instruction)
        cpu.call('game_history_freeze');seek(cpu,probe)
        player=symbols['game_play_state']+end*10
        x,y=cpu.mem.r8(player+3),cpu.mem.r8(player+2)
        bounds=table(cpu,end)
        assert bounds['left']<=x<bounds['right'] and bounds['top']<=y<bounds['bottom']
        costs,_=job(cpu,ordinal,x,y,expected_status=6)
        assert field(cpu,'game_preview_cache_valid')==0 and field(cpu,'game_preview_counts',4)==0
        saved=protected(cpu);preview=block(cpu,'game_preview_storage','game_preview_storage_end')
        call_checked(cpu,'game_preview_result',{0:costs['generation']},saved)
        assert cpu.cpu.r_reg(0)==0 and block(cpu,'game_preview_storage','game_preview_storage_end')==preview
        cpu.audit_reads()
        return dict(passed=True,seed=0xace1,dispatches=tick+1,dispatch_cap=512,
            operations=len(stream),operation_cap=8192,non_tick_calls_between_launch_and_probe=between,
            incoming_origin=incoming,oldest=oldest,probe_origin=probe,completed_kind=kind,
            request_accepted=True,context_missing=True,result_rejected=True,cache_valid=False,
            unavailable_scratch_preserved=True,full_live_history_output_preserved=True,costs=costs)


def stage_a1(executable,progress):
    """A1 finite API/lifecycle/context coverage; A2/A3 remain separate."""
    cases={}
    def saved(name,report):
        cases[name]=report;progress(dict(stage='stage-a1',case=name,result=report))
    fallback=current_fallback(executable)
    progress(dict(stage='stage-a1',case='human-serve-fallback-core',result=fallback))
    fallback['postlaunch_rejection']=postlaunch_rejection(executable)
    progress(dict(stage='stage-a1',case='postlaunch-rejection',result=fallback['postlaunch_rejection']))
    fallback['timed_prelaunch']=timed_prelaunch(executable)
    saved('human-serve-fallback',fallback)
    saved('limit-256',dict(passed=True,case='human-serve-fallback',variant=1,
        samples=fallback['path_counts'][1],total_sample_limit=256,no_actual_human_launch=True,
        outgoing_path_claimed=False,incomplete=True,full_live_history_output_preserved=True,
        continuous_state_path_output_equal=True,independent_continuation_policy_equal=True))
    saved('title-dual-rejection',stale_title(executable))
    saved('no-contact',no_contact(executable))
    replacements=partial_replacement(executable)
    for report,name in zip(replacements['cases'],('replacement-resolve','replacement-held')):
        saved(name,dict(report,passed=True,maximum_stack_bytes=replacements['maximum_stack_bytes']))
    saved('non-dispatch-lifecycle',lifecycle_stops(executable))
    saved('truncated-completed-context',truncated_completed(executable))
    return dict(passed=True,scope='A1 only: API/context/lifecycle bounds; endpoint discovery, relocation, emitted native sinks and current native costs remain pending.',
        cases=cases,other_stages_pending=['A2-endpoint-discovery','A3-relocation-native-history'],
        canonical_bytes=318,history_metadata_bytes=72,total_samples_per_path=256,maximum_worker_operations=4)
