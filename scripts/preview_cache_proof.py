"""Cache/seek failure proofs use actual API execution, not a rules oracle."""
from copy import deepcopy
from build_match_core import load_image
from history_proof import attempts, cursor, field, seek
from match_core_cpu import Core
from preview_proof import fixture, protected, call_checked, block, ARITY, OPERATIONS
from run_shared_match_core import READONLY


def result(cpu):
    counts=[cpu.mem.r16(cpu.symbols['game_preview_counts']+2*v) for v in (0,1)]
    prefix=field(cpu,'game_preview_prefix_count')
    return dict(paths=[bytes(cpu.mem.r_block(cpu.symbols['game_preview_paths']+v*2048,counts[v]*8)) for v in (0,1)],
        contexts=[bytes(cpu.mem.r_block(cpu.symbols[n],318)) for n in ('game_preview_held_state','game_preview_released_state')],
        outputs=[deepcopy(cpu.preview_event_groups.get((2,v),[])) for v in (0,1)],
        outcomes=[cpu.mem.r16(cpu.symbols['game_preview_outcomes']+2*v) for v in (0,1)],
        edited=block(cpu,'game_preview_edited_state','game_preview_held_state'),prefix=prefix,
        incoming=cursor(cpu,'game_preview_incoming'),action=cursor(cpu,'game_preview_action'))


def job(cpu,ordinal,x,y,expected_status=5,observer=None):
    saved=protected(cpu)
    expected=bytearray(cpu.state())
    end=(1 if field(cpu,'game_score_flags',1)&2 else 0) if ordinal==0xffff else attempts(cpu)[ordinal][2]
    player=cpu.symbols['game_play_state']-cpu.symbols['game_core_state']+end*10
    expected[player+3]=x;expected[player+2]=y
    bodies={cpu.symbols[n+'_body'] for n in OPERATIONS}
    resolver=0
    def observe(pc):
        nonlocal resolver
        cpu.instruction(pc)
        if observer is not None:observer(pc)
        if pc in bodies and field(cpu,'game_preview_active',1)==1:resolver+=1
    cpu.cpu.set_instr_hook_callback(observe)
    generation=field(cpu,'game_preview_generation',4)
    cpu.preview_events.clear();cpu.preview_event_groups.clear()
    was_cache_valid=(bool(field(cpu,'game_preview_cache_valid'))
        and field(cpu,'game_preview_status')==5 and field(cpu,'game_preview_ordinal')==ordinal)
    request_cycles=call_checked(cpu,'game_preview_request',{0:generation,1:ordinal,2:x,3:y},saved)
    assert cpu.cpu.r_reg(0)==1
    generation+=1
    cache_hit=was_cache_valid and field(cpu,'game_preview_status')==2
    cycles=[];operations=[]
    for _ in range(8192):
        if field(cpu,'game_preview_status')>=5:break
        before=sum(cpu.visits.get(pc,0) for pc in bodies)
        cycles.append(call_checked(cpu,'game_preview_step',{0:generation,1:4},saved))
        assert cpu.cpu.r_reg(0)==1
        operations.append(sum(cpu.visits.get(pc,0) for pc in bodies)-before)
        assert operations[-1]<=4
    else:raise AssertionError('Cache proof worker did not terminate')
    assert field(cpu,'game_preview_status')==expected_status
    if expected_status==5:
        assert block(cpu,'game_preview_edited_state','game_preview_held_state')==bytes(expected), 'Preview changes bytes beyond requested human X/Y (including RNG)'
    cpu.cpu.set_instr_hook_callback(cpu.instruction)
    return dict(generation=generation,edited_only_position_changed=expected_status==5,cache_hit=cache_hit,resolver_operations=resolver,
        request_cpu_cycles=request_cycles,total_worker_cpu_cycles=sum(cycles),
        maximum_worker_cpu_cycles=max(cycles),maximum_worker_operations=max(operations),
        worker_calls=len(cycles),stack_bytes=cpu.stack_bytes),result(cpu)


def ready_failure(cpu,target,label,address=None,width=2):
    """Poison a declared negative slot; product must preserve the poisoned store."""
    generation=field(cpu,'game_preview_generation',4)
    read=cpu.mem.r8 if width==1 else cpu.mem.r16
    write=cpu.mem.w8 if width==1 else cpu.mem.w16
    old=read(address) if address is not None else None
    if address is not None:write(address,0 if label=='corrupt-operation-id' else old^(2 if width==1 else 1))
    saved=protected(cpu)
    preview=block(cpu,'game_preview_storage','game_preview_storage_end')
    cycles=call_checked(cpu,'game_history_seek',{0:target>>32,1:target&0xffffffff},saved)
    assert cpu.cpu.r_reg(0)==0
    assert block(cpu,'game_preview_storage','game_preview_storage_end')==preview
    call_checked(cpu,'game_preview_result',{0:generation},saved)
    assert cpu.cpu.r_reg(0)==1
    assert block(cpu,'game_preview_storage','game_preview_storage_end')==preview
    if address is not None:write(address,old)
    return dict(name=label,passed=True,all_72_metadata_preserved=True,canonical_preserved=True,
        history_bytes_preserved=True,cache_generation_status_preserved=True,
        ready_result_preserved=True,failed_seek_cpu_cycles=cycles)


def exercise(executable):
    image,symbols=load_image(executable)
    with Core(image,symbols,readonly=READONLY) as cpu:
        _,_,_,launches=fixture(cpu)
        event=next((x for x in launches if x['human'] and x['kind']==1),None)
        assert event is not None, 'Cache fixture has no completed human return'
        index=attempts(cpu)
        ordinal=next((i for i,(n,k,e) in enumerate(index) if k==1 and e==event['end']),None)
        serve_ordinal=next((i for i,(n,k,e) in enumerate(index) if k==3),None)
        assert ordinal is not None and serve_ordinal is not None
        selection=event['origin']
        cpu.call('game_history_freeze');seek(cpu,selection)
        original,original_result=job(cpu,ordinal,event['x'],event['y'])
        assert original['resolver_operations']>0 and not original['cache_hit']
        player=symbols['game_play_state']+event['end']*10
        limits=symbols['game_lower_limits' if event['end']==0 else 'game_upper_limits']+((cpu.mem.r8(player+1)>>3)&12)
        x=event['x']+1 if event['x']+1<cpu.mem.r8(limits+2) else event['x']-1
        assert cpu.mem.r8(limits+3)<=x<cpu.mem.r8(limits+2) and x!=event['x']
        warm,warm_result=job(cpu,ordinal,x,event['y'])
        assert warm['cache_hit'] and warm['resolver_operations']==0
        prefix=original_result['prefix']*8
        assert warm_result['paths'][0][:prefix]==warm_result['paths'][1][:prefix]==original_result['paths'][0][:prefix]
        # A successful external seek back to the same exact boundary retires READY.
        retired=warm['generation']
        seek(cpu,selection+1);seek(cpu,selection)
        assert field(cpu,'game_preview_cache_valid')==0 and field(cpu,'game_preview_generation',4)>retired
        saved=protected(cpu);before=block(cpu,'game_preview_storage','game_preview_storage_end')
        call_checked(cpu,'game_preview_result',{0:retired},saved)
        assert cpu.cpu.r_reg(0)==0 and block(cpu,'game_preview_storage','game_preview_storage_end')==before
        cold,cold_result=job(cpu,ordinal,x,event['y'])
        assert not cold['cache_hit'] and cold['resolver_operations']>0
        assert cold_result==warm_result, 'Warm context differs from forced cold actual resolver'
        comparison=dict(passed=True,state_path_output_equal=True,prefix_equal=True,
            live_history_output_preserved=True,cold=cold,warm=warm,original=original,
            selected_cursor=selection,incoming_origin=warm_result['incoming'],
            original_action_boundary=warm_result['action'],prefix_samples=warm_result['prefix'])
        cp=field(cpu,'game_history_selected',4)
        cp_origin=(cpu.mem.r32(cp)<<32)|cpu.mem.r32(cp+4)
        opcode=symbols['game_history_buffer']+(cp_origin&4095)*14
        assert cp_origin<selection
        failures=[ready_failure(cpu,selection,'corrupt-checkpoint-schema',cp+8),
            ready_failure(cpu,selection,'corrupt-checkpoint-simulation',cp+10),
            ready_failure(cpu,selection,'corrupt-checkpoint-state',cp+12+symbols['game_entropy_policy']-symbols['game_core_state'],width=1),
            ready_failure(cpu,selection,'corrupt-operation-id',opcode),
            ready_failure(cpu,cursor(cpu)+1,'out-of-range-high')]
        # Cancel clears both cache and publication; old generation cannot work.
        saved=protected(cpu);retired=field(cpu,'game_preview_generation',4)
        call_checked(cpu,'game_preview_cancel',{0:retired},saved)
        assert cpu.cpu.r_reg(0)==1 and field(cpu,'game_preview_cache_valid')==0
        before=block(cpu,'game_preview_storage','game_preview_storage_end')
        for api,args in (('game_preview_step',{0:retired,1:4}),('game_preview_result',{0:retired})):
            call_checked(cpu,api,args,saved)
            assert cpu.cpu.r_reg(0)==0 and block(cpu,'game_preview_storage','game_preview_storage_end')==before
        after_cancel,_=job(cpu,ordinal,x,event['y'])
        assert not after_cancel['cache_hit'] and after_cancel['resolver_operations']>0
        different,_=job(cpu,serve_ordinal,x,event['y'],expected_status=6)
        assert not different['cache_hit'] and different['resolver_operations']>0
        # Resume and drive actual operations past eviction, then freeze again.
        cpu.call('game_history_resume_latest')
        for tick in range(1024):
            for name,args in (('game_round_poll',[]),('game_core_sample_pads',[16,0]),
                    ('game_core_sample_result',[0]*6),('game_tick_dispatch',[])):
                cpu.call_logical(name,args)
        cpu.call('game_history_freeze')
        assert cursor(cpu,'game_history_oldest')>warm_result['incoming']
        assert field(cpu,'game_preview_cache_valid')==0
        saved=protected(cpu);preview=block(cpu,'game_preview_storage','game_preview_storage_end')
        call_checked(cpu,'game_history_seek',{0:selection>>32,1:selection&0xffffffff},saved)
        assert cpu.cpu.r_reg(0)==0 and block(cpu,'game_preview_storage','game_preview_storage_end')==preview
        call_checked(cpu,'game_preview_result',{0:cold['generation']},saved)
        assert cpu.cpu.r_reg(0)==0 and block(cpu,'game_preview_storage','game_preview_storage_end')==preview
        # Deliberate lifetime boundary negative setup in preview-owned metadata.
        cpu.mem.w32(symbols['game_preview_generation'],0xffffffff)
        saved=protected(cpu)
        cpu.call('game_history_resume_latest');assert cpu.cpu.r_reg(0)==1
        cpu.call('game_history_freeze');assert cpu.cpu.r_reg(0)==1
        seek(cpu,cursor(cpu))
        assert field(cpu,'game_preview_generation',4)==0xffffffff
        saved=protected(cpu);before=block(cpu,'game_preview_storage','game_preview_storage_end')
        generation=0xffffffff
        for api,args in (('game_preview_request',{0:generation,1:0xffff,2:128,3:152}),
                ('game_preview_cancel',{0:generation}),('game_preview_step',{0:generation,1:4}),
                ('game_preview_result',{0:generation})):
            call_checked(cpu,api,args,saved)
            assert cpu.cpu.r_reg(0)==0 and block(cpu,'game_preview_storage','game_preview_storage_end')==before
        cpu.audit_reads()
        return dict(passed=True,cold_warm=comparison,failed_seek_controls=failures,
            invalidation=dict(passed=True,negative_controls=['seek-back-ready','failed-seek-preserves',
                'different-attempt','cancel','eviction','exhaustion','stale-generation'],
                after_cancel_resolver_operations=after_cancel['resolver_operations'],
                different_attempt_resolver_operations=different['resolver_operations'],
                oldest_after_eviction=cursor(cpu,'game_history_oldest'),evicted_incoming_origin=warm_result['incoming'],
                generation_exhausted=field(cpu,'game_preview_generation',4)==0xffffffff),
            maximum_stack_bytes=cpu.stack_bytes)
