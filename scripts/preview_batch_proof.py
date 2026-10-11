"""Budget changes alter chunk boundaries, never actual simulation semantics."""
import hashlib
import json
from build_match_core import load_image
from history_proof import attempts,seek,field
from match_core_cpu import Core
from preview_proof import fixture,protected,assert_preserved,call_checked,OPERATIONS
from preview_extended_proof import candidates,execute,continuous
from run_shared_match_core import READONLY

TRANSITIONS=('resolve->prime-held','prime-held->prime-released','prime-released->held',
             'held->released','released->ready')


def batching(executable,progress):
    image,symbols=load_image(executable);observations=[];baseline=None;cases=[]
    with Core(image,symbols,readonly=READONLY) as cpu:
        stream,states,_,launches=fixture(cpu,seed=0xace1,dispatches=512)
        candidate=next(iter(candidates(attempts(cpu),launches)),None)
        assert candidate is not None, 'Batching fixture has no actual completed return'
        original_trace=cpu.trace
        def guard(mode,width,address,value):
            if (mode=='W' and field(cpu,'game_preview_active',1) in (1,2)
                    and address<cpu.stop and address+(1<<width)>cpu.start):
                raise AssertionError('Private preview worker writes canonical state')
            if (mode=='W' and field(cpu,'game_history_mode',1)==2
                    and address<symbols['game_history_buffer_end']
                    and address+(1<<width)>symbols['game_history_buffer']):
                raise AssertionError('Batched preview writes frozen history/live backup')
            original_trace(mode,width,address,value)
        cpu.mem.set_trace_func(guard)
        cpu.call('game_history_freeze')
        for budget in (1,2,3,4):
            selection=candidate['origin'];seek(cpu,selection)
            assert cpu.state()==states[selection]
            saved=protected(cpu);roles=[];body_trace=[];restores=0;last_body_restore_count=0
            bodies={symbols[name+'_body']:name for name in OPERATIONS}
            def observe(pc):
                nonlocal restores,last_body_restore_count
                if pc==symbols['game_preview_context_released']:
                    assert_preserved(cpu,saved);restores+=1
                if pc not in bodies:return
                active=field(cpu,'game_preview_active',1)
                if active not in (1,2):return
                status=field(cpu,'game_preview_status')
                variant=field(cpu,'game_preview_variant',1)
                role='resolve' if active==1 else ('prime-held' if variant==0 else 'prime-released') if status==2 else 'held' if variant==0 else 'released'
                if roles and roles[-1]!=role:
                    assert restores>last_body_restore_count, 'Owner transition enters a body before restoring selected/history/output'
                if not roles or roles[-1]!=role:roles.append(role)
                last_body_restore_count=restores
                body_trace.append((role,bodies[pc]))
            observation=execute(cpu,candidate['ordinal'],selection,candidate['x'],candidate['y'],
                stream,0xace1,f'batch-budget-{budget}',budget=budget,extra_observer=observe)
            result=observation['result'];costs=observation['costs']
            assert restores>last_body_restore_count, 'READY publication lacks a restore after the final actual body'
            call_checked(cpu,'game_preview_result',{0:costs['generation']},saved)
            assert cpu.cpu.r_reg(0)==1
            assert [cpu.cpu.r_reg(r) for r in (1,2)]==[len(path)//8 for path in result['paths']]
            call_checked(cpu,'game_preview_cancel',{0:costs['generation']},saved)
            assert cpu.cpu.r_reg(0)==1
            transitions=[a+'->'+b for a,b in zip(roles,roles[1:])]+[roles[-1]+'->ready']
            assert transitions==list(TRANSITIONS), 'Budget skips or reorders actual context ownership'
            fingerprint=hashlib.sha256(json.dumps(body_trace,separators=(',',':')).encode()).hexdigest()
            semantic=(observation['selected'],result['edited'],result['contexts'],result['paths'],
                result['outcomes'],result['outputs'],fingerprint)
            if baseline is None:baseline=semantic
            else:assert semantic==baseline, 'Batch budget changes full actual state/path/outcome/output or API role trace'
            assert len(body_trace)==sum(costs['worker_body_counts'])>0 and 0<costs['maximum_worker_operations']<=budget
            facts=dict(budget=budget,passed=True,actual_body_operations=len(body_trace),
                maximum_actual_body_operations_per_call=costs['maximum_worker_operations'],
                costs=costs,worker_body_counts=costs['worker_body_counts'],
                worker_calls=costs['worker_calls'],public_restore_checks=costs['worker_calls']+3,
                ownership_restore_checks=restores,owner_transitions=transitions,
                owner_transition_preservation=True,selected_history_output_preserved=True,
                semantic_trace_sha256=fingerprint,semantic_trace_equal_across_budgets=True)
            observations.append((observation,facts))
            progress(dict(stage='batch-budget-recorded',result=facts))
        cpu.audit_reads()
    for observation,facts in observations:
        facts['continuous']=continuous(image,symbols,observation)
        cases.append(facts);progress(dict(stage='batch-budget-continuous',result=facts))
    return dict(passed=True,canonical_bytes=318,history_metadata_bytes=72,
        preview_storage_bytes=symbols['game_preview_storage_end']-symbols['game_preview_storage'],
        preview_metadata_bytes=symbols['game_preview_state_end']-symbols['game_preview_state'],
        budgets=[1,2,3,4],cases=cases,state_path_outcome_output_equal_across_budgets=True,
        independent_continuation_policy_equal=True,required_owner_transitions=list(TRANSITIONS),
        scope='Four actual return continuations vary only public operation budget; real native interrupt/latency/resources remain pending.')
