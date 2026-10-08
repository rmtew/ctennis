"""Preview proofs execute the actual 68000; host code only supplies inputs/reads."""
from copy import deepcopy
from build_match_core import load_image
from history_proof import attach, attempts, cursor, field, seek
from match_core_cpu import Core
from run_shared_match_core import READONLY

OPERATIONS = ('game_core_init','game_core_select','game_core_sample_pads',
              'game_core_sample_result','game_core_clear_inputs','game_core_return_title',
              'game_round_poll','game_tick_dispatch','game_core_latch_actions')
ARITY = (0,3,2,6,0,0,0,0,0)


def block(cpu,first,last):
    return bytes(cpu.mem.r_block(cpu.symbols[first],cpu.symbols[last]-cpu.symbols[first]))


def point(state,symbols):
    start = symbols['game_core_state']
    def value(name): return state[symbols[name]-start]
    ball,shadow = value('game_ball_colour'),value('game_shadow_colour')
    assert 0<=ball<16 and 0<=shadow<16
    return bytes([value(n) for n in ('game_court_x','game_court_y','game_ball_x',
                 'game_ball_y','game_contact','game_flight')]+[ball|(shadow<<4),value('game_tick')])


def protected(cpu):
    """Full image outside preview scratch, plus existing live observation queue."""
    preview=(cpu.symbols['game_preview_storage'],cpu.symbols['game_preview_storage_end'])
    pieces=[]
    for first,last in cpu.regions:
        if first<preview[0]: pieces.append(bytes(cpu.mem.r_block(first,max(0,min(last,preview[0])-first))))
        if last>preview[1]: pieces.append(bytes(cpu.mem.r_block(max(first,preview[1]),last-max(first,preview[1]))))
    return pieces,deepcopy(cpu.events)


def assert_preserved(cpu,saved):
    assert protected(cpu)==saved, 'Preview changes selected/history/live output or immutable image'
    assert field(cpu,'game_history_mode',1)==2
    assert field(cpu,'game_preview_active',1)==0


def call_checked(cpu,name,args,saved):
    cycles=cpu.call(name,args)
    assert_preserved(cpu,saved)
    return cycles


def fixture(cpu):
    stream=[('game_core_select',[0,0xace1,0])]
    for tick in range(512):
        stream.extend([('game_round_poll',[]),
            ('game_core_sample_pads',[(0x10 if tick%64>=8 else 0)|(8 if tick%96<48 else 4),0]),
            ('game_core_sample_result',[0]*6),('game_tick_dispatch',[])])
    states,ticks,launches={},[],[]
    original=cpu.instruction
    def observe(pc):
        original(pc)
        if pc in (cpu.symbols['game_history_serve'],cpu.symbols['game_history_contact']):
            end=cpu.cpu.r_reg(7)&0xffff
            assert end in (0,1)
            player=cpu.symbols['game_play_state']+end*10
            launches.append(dict(kind=3 if pc==cpu.symbols['game_history_serve'] else 1,
                end=end,origin=cursor(cpu),human=cpu.mem.r8(cpu.symbols['game_play_state']+54+end)==0,
                x=cpu.mem.r8(player+3),y=cpu.mem.r8(player+2)))
    cpu.cpu.set_instr_hook_callback(observe)
    cpu.call_logical('game_core_init',[])
    attach(cpu)
    states[0]=cpu.state()
    for name,args in stream:
        cpu.clear_events();cpu.call_logical(name,args)
        states[cursor(cpu)]=cpu.state()
        if name=='game_tick_dispatch':ticks.append(cursor(cpu))
    cpu.cpu.set_instr_hook_callback(cpu.instruction)
    return stream,states,ticks,launches


def geometry(path):
    return [(p[:4],bool(p[6]&15),bool(p[6]&240),p[7]) for p in path]


def small(executable):
    image,symbols=load_image(executable)
    observations=[]
    with Core(image,symbols,readonly=READONLY) as cpu:
        stream,states,ticks,launches=fixture(cpu)
        index=attempts(cpu)
        serve=next(x for x in launches if x['human'] and x['kind']==3)
        contact=next(x for x in launches if x['human'] and x['kind']==1)
        return_entry=next((i,n) for i,(n,k,e) in enumerate(index) if k==1 and e==contact['end'])
        serve_entry=next((i,n) for i,(n,k,e) in enumerate(index) if k==3 and n==serve['origin'])
        cpu.call('game_history_freeze')
        # Every write while frozen must be canonical, recorder metadata, preview
        # scratch or stack. The history store (including live backup) is read-only.
        original_trace=cpu.trace
        def guard(mode,width,address,value):
            if mode=='W' and symbols['game_history_buffer']<=address<symbols['game_history_buffer_end']:
                raise AssertionError('Frozen preview writes history/live backup')
            original_trace(mode,width,address,value)
        cpu.mem.set_trace_func(guard)
        bodies={symbols[n+'_body']:(n,a) for n,a in zip(OPERATIONS,ARITY)}
        for name,(ordinal,origin),selection,event in (
                ('completed-serve',serve_entry,serve['origin'],serve),
                ('return-after-pads',return_entry,contact['origin']-1,contact),
                ('return-before-dispatch',return_entry,contact['origin'],contact)):
            seek(cpu,selection)
            saved=protected(cpu)
            generation=field(cpu,'game_preview_generation',4)
            traces={0:[],1:[]}
            resolver_operations=0
            def observe(pc):
                nonlocal resolver_operations
                cpu.instruction(pc)
                if pc in bodies and field(cpu,'game_preview_active',1)==1:
                    resolver_operations+=1
                if pc in bodies and field(cpu,'game_preview_active',1)==2:
                    op,arity=bodies[pc]
                    variant=field(cpu,'game_preview_variant',1)
                    traces[variant].append((op,[cpu.cpu.r_reg(r)&0xffff for r in range(arity)],cpu.state()))
            cpu.cpu.set_instr_hook_callback(observe)
            cpu.preview_events.clear();cpu.preview_event_groups.clear()
            request_cycles=call_checked(cpu,'game_preview_request',{0:generation,1:ordinal,2:event['x'],3:event['y']},saved)
            assert cpu.cpu.r_reg(0)==1
            generation+=1
            negatives=[]
            for op,args,label in (
                ('game_preview_step',{0:generation-1,1:4},'stale-step'),
                ('game_preview_cancel',{0:generation-1},'stale-cancel'),
                ('game_preview_request',{0:generation-1,1:ordinal,2:event['x'],3:event['y']},'stale-request'),
                ('game_preview_step',{0:generation,1:0},'zero-budget'),
                ('game_preview_step',{0:generation,1:5},'excess-budget'),
                ('game_preview_result',{0:generation},'unpublished-result')):
                before=block(cpu,'game_preview_storage','game_preview_storage_end')
                call_checked(cpu,op,args,saved)
                assert cpu.cpu.r_reg(0)==0 and block(cpu,'game_preview_storage','game_preview_storage_end')==before
                negatives.append(label)
            budgets,cycles,operations=[],[],[]
            resolver_calls=resolver_cycles=0
            for worker in range(8192):
                budget=1 if worker%3==0 else 4
                before=sum(cpu.visits.get(pc,0) for pc in bodies)
                resolving=field(cpu,'game_preview_status')==1
                cycles.append(call_checked(cpu,'game_preview_step',{0:generation,1:budget},saved))
                assert cpu.cpu.r_reg(0)==1
                if resolving:
                    resolver_calls+=1;resolver_cycles+=cycles[-1]
                actual=sum(cpu.visits.get(pc,0) for pc in bodies)-before
                assert actual<=budget<=4,(actual,budget)
                budgets.append(budget);operations.append(actual)
                status=field(cpu,'game_preview_status')
                if status>=5:break
            else:raise AssertionError('Bounded worker fails to terminate')
            assert status==5,(name,status)
            paths=[];contexts=[]
            for variant in (0,1):
                count=field(cpu,'game_preview_counts' ,2) if variant==0 else cpu.mem.r16(symbols['game_preview_counts']+2)
                assert 0<count<=256
                raw=bytes(cpu.mem.r_block(symbols['game_preview_paths']+variant*2048,count*8))
                paths.append([raw[i:i+8] for i in range(0,len(raw),8)])
                address=symbols['game_preview_held_state'] if variant==0 else symbols['game_preview_released_state']
                contexts.append(bytes(cpu.mem.r_block(address,318)))
            call_checked(cpu,'game_preview_result',{0:generation},saved)
            assert cpu.cpu.r_reg(0)==1
            coincident=field(cpu,'game_preview_coincident')
            assert bool(coincident)==(geometry(paths[0])==geometry(paths[1]))
            prefix=field(cpu,'game_preview_prefix_count')
            incoming=cursor(cpu,'game_preview_incoming') if prefix else None
            original_prefix=[point(states[t],symbols) for t in ticks if incoming is not None and incoming<t<=selection]
            assert paths[0][:prefix]==paths[1][:prefix]==original_prefix
            outcomes=[cpu.mem.r16(symbols['game_preview_outcomes']+2*v) for v in (0,1)]
            observations.append(dict(name=name,selection=selection,original_action_boundary=contact['origin'] if name.startswith('return') else serve['origin'],
                edited=block(cpu,'game_preview_edited_state','game_preview_held_state'),
                traces=traces,paths=paths,contexts=contexts,prefix=prefix,outcomes=outcomes,
                outputs={v:deepcopy(cpu.preview_event_groups.get((2,v),[])) for v in (0,1)},
                incoming_origin=incoming,end=event['end'],coincident=bool(coincident),negative_controls=negatives,
                worker_calls=len(cycles),request_cpu_cycles=request_cycles,total_worker_cpu_cycles=sum(cycles),
                resolver_worker_calls=resolver_calls,resolver_operations=resolver_operations,
                resolver_inclusive_cpu_cycles=resolver_cycles,
                maximum_worker_cpu_cycles=max(cycles),maximum_worker_operations=max(operations),
                actual_operations=sum(operations),preservation_checks=len(cycles)+10,worker_restorations=len(cycles),stack_bytes=cpu.stack_bytes))
            call_checked(cpu,'game_preview_cancel',{0:generation},saved)
            assert cpu.cpu.r_reg(0)==1
            before=block(cpu,'game_preview_storage','game_preview_storage_end')
            call_checked(cpu,'game_preview_result',{0:generation},saved)
            assert cpu.cpu.r_reg(0)==0 and block(cpu,'game_preview_storage','game_preview_storage_end')==before
            # Measure a fresh legal position edit at the unchanged selected cursor.
            # Bounds come from the actual movement table and selected animation.
            player=symbols['game_play_state']+event['end']*10
            phase=(cpu.mem.r8(player+1)>>3)&12
            limits=symbols['game_lower_limits' if event['end']==0 else 'game_upper_limits']+phase
            left,right=cpu.mem.r8(limits+3),cpu.mem.r8(limits+2)
            edit_x=event['x']+1 if event['x']+1<right else event['x']-1
            assert left<=edit_x<right and edit_x!=event['x']
            generation=field(cpu,'game_preview_generation',4)
            repeat_request_cycles=call_checked(cpu,'game_preview_request',
                {0:generation,1:ordinal,2:edit_x,3:event['y']},saved)
            assert cpu.cpu.r_reg(0)==1
            generation+=1
            repeat_cycles=[];before_resolver=resolver_operations
            while field(cpu,'game_preview_status')==1:
                assert len(repeat_cycles)<8192
                repeat_cycles.append(call_checked(cpu,'game_preview_step',{0:generation,1:1},saved))
                assert cpu.cpu.r_reg(0)==1
            assert field(cpu,'game_preview_status')==2
            observations[-1].update(repeat_position_edit_x=edit_x,
                repeat_request_cpu_cycles=repeat_request_cycles,
                repeat_resolver_operations=resolver_operations-before_resolver,
                repeat_resolver_worker_calls=len(repeat_cycles),
                repeat_resolver_cpu_cycles=sum(repeat_cycles))
            call_checked(cpu,'game_preview_cancel',{0:generation},saved)
            assert cpu.cpu.r_reg(0)==1
        cpu.audit_reads()
    # Independent uninterrupted executions, each initialized ONCE from the
    # intended edited snapshot. No subsequent canonical injection is used.
    reports=[]
    for observation in observations:
        for variant in (0,1):
            with Core(image,symbols,initial=observation['edited'],readonly=READONLY) as cpu:
                generated=observation['paths'][variant][:observation['prefix']]
                for name,args,before in observation['traces'][variant]:
                    assert cpu.state()==before, 'Chunked preview differs from uninterrupted actual core'
                    if name=='game_core_sample_pads':
                        owner=cpu.mem.r8(symbols['game_lower_owner']+observation['end'])
                        assert args[owner]&0x3f==(0x10 if variant==0 else 0)
                    cpu.call_logical(name,args)
                    if name=='game_tick_dispatch': generated.append(point(cpu.state(),symbols))
                assert cpu.state()==observation['contexts'][variant]
                assert generated==observation['paths'][variant]
                assert cpu.events==observation['outputs'][variant], 'Ordered preview outputs differ'
                cpu.audit_reads()
        report={k:v for k,v in observation.items() if k not in ('edited','traces','paths','contexts','outputs')}
        report.update(passed=True,continuous_state_path_output_equal=True,
                      live_history_output_preserved=True,path_counts=[len(p) for p in observation['paths']])
        reports.append(report)
    return dict(passed=True,cases=reports,preview_storage_bytes=symbols['game_preview_storage_end']-symbols['game_preview_storage'],
                metadata_bytes=symbols['game_preview_state_end']-symbols['game_preview_state'],fixture_operations=len(stream),
                scope='Small actual CPU proof only; native sinks/cadence, eviction/fallback and broad outcome coverage pending.')
