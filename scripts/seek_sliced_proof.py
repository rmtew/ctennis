"""Bounded navigation over captured inputs, using only the actual 68000 core."""
from copy import deepcopy
import hashlib
import json
from build_match_core import load_image
from history_proof import attach,attempts,cursor,field
from match_core_cpu import Core
from preview_proof import block,OPERATIONS
from preview_native_proof import native_entries,assert_native_entries
from run_shared_match_core import READONLY
from native_evidence import digest
from native_tools import ROOT

CHECKPOINT=512
TARGET=569


def public(cpu):
    return dict(state=cpu.state(),metadata=block(cpu,'game_history_state','game_history_state_end'),
        store=block(cpu,'game_history_buffer','game_history_buffer_end'),events=deepcopy(cpu.events),
        native_intents=deepcopy(getattr(cpu,'native_semantic_events',[])))


def full(cpu):
    return public(cpu),block(cpu,'game_history_seek_storage','game_history_seek_storage_end'),block(cpu,'game_preview_storage','game_preview_storage_end'),deepcopy(cpu.seek_events)


def generation(cpu):return field(cpu,'game_history_seek_generation',4)


def checked(cpu,name,args,expected=1):
    cpu.seek_fixture_api=name
    try:cycles=cpu.call(name,args)
    finally:cpu.seek_fixture_api=None
    assert cpu.cpu.r_reg(0)==expected,(name,expected,cpu.cpu.r_reg(0))
    assert_native_entries(cpu)
    assert not field(cpu,'game_history_replaying',1) and not field(cpu,'game_preview_active',1)
    assert not field(cpu,'game_history_seek_active',1)
    return cycles


def proof(executable,stream,base=0x10000,native=False,role='standalone'):
    image,symbols=load_image(executable,base)
    references={}
    with Core(image,symbols,readonly=READONLY) as baseline:
        baseline.call_logical('game_core_init',[])
        for index,(name,args) in enumerate(stream,1):
            baseline.clear_events();baseline.call_logical(name,args)
            references[index]=(baseline.state(),deepcopy(baseline.events))
        baseline.audit_reads()
    with Core(image,symbols,readonly=READONLY) as cpu:
        cpu.call_logical('game_core_init',[]);attach(cpu)
        for index,(name,args) in enumerate(stream,1):
            cpu.call_logical(name,args)
            assert cpu.state()==references[index][0],('Recorded actual full state',index)
        if native:native_entries(cpu,image)
        cpu.call('game_history_freeze');assert cpu.cpu.r_reg(0)==1
        selected=public(cpu);selected_position=cursor(cpu,'game_history_position')
        assert selected_position==835 and selected['state']!=references[TARGET][0]
        original_trace=cpu.trace
        def guard(mode,width,address,value):
            if mode=='W' and address<symbols['game_history_buffer_end'] and address+(1<<width)>symbols['game_history_buffer']:
                raise AssertionError('Scheduled navigation writes frozen recorder/live backup')
            if mode=='W' and address<symbols['game_preview_storage_end'] and address+(1<<width)>symbols['game_preview_storage']:
                api=getattr(cpu,'seek_fixture_api',None)
                if api and api.startswith('game_preview_'):
                    original_trace(mode,width,address,value);return
                permitted=[(symbols[n],length) for n,length in (('game_preview_generation',4),
                    ('game_preview_cache_valid',2),('game_preview_counts',4),('game_preview_status',2),
                    ('game_preview_launch_saved',4),('game_preview_endpoint_ready',2))]
                permitted.extend((symbols['game_preview_query_workspaces']+offset,2)
                                 for offset in (36,84))
                assert getattr(cpu,'seek_fixture_api',None) in ('game_history_seek_begin','game_history_seek_commit','game_history_seek'), 'Seek slice writes preview-owned buffers'
                assert any(low<=address and address+(1<<width)<=low+length for low,length in permitted), 'Seek writes preview data beyond explicit retirement fields'
            if (mode=='W' and str(getattr(cpu,'seek_fixture_api',None)).startswith('game_preview_')
                    and address<symbols['game_history_seek_storage_end'] and address+(1<<width)>symbols['game_history_seek_storage']):
                raise AssertionError('Preview modifies serialized seek ownership/scratch')
            original_trace(mode,width,address,value)
        cpu.mem.set_trace_func(guard)
        bodies={symbols[n+'_body'] for n in OPERATIONS}
        negatives=[]
        def rejection(name,api,args):
            saved=full(cpu);cycles=checked(cpu,api,args,0)
            assert full(cpu)==saved,('Rejected API changes selected/job/preview/outputs',name)
            negatives.append(dict(name=name,passed=True,preserved=True,cpu_cycles=cycles))
        def begin(target=TARGET):
            return checked(cpu,'game_history_seek_begin',{0:generation(cpu),1:target>>32,2:target&0xffffffff})
        def advance():
            before=sum(cpu.visits.get(pc,0) for pc in bodies)
            cycles=checked(cpu,'game_history_seek_step',{0:generation(cpu),1:1})
            actual=sum(cpu.visits.get(pc,0) for pc in bodies)-before
            assert actual==1,'Scheduled slice must execute exactly one actual body'
            return cycles
        begin_cycles=begin();job_generation=generation(cpu)
        assert public(cpu)==selected and cursor(cpu,'game_history_seek_cursor')==CHECKPOINT
        assert field(cpu,'game_history_seek_remaining')==TARGET-CHECKPOINT
        saved=full(cpu);admission_cycles=checked(cpu,'game_history_seek_step',{0:job_generation,1:0})
        assert full(cpu)==saved
        negatives.append(dict(name='admission-zero',passed=True,preserved=True,cpu_cycles=admission_cycles))
        preview_after_begin=block(cpu,'game_preview_storage','game_preview_storage_end')
        rows=[];step_costs=[];events_start=len(cpu.seek_events)
        for boundary in range(CHECKPOINT+1,TARGET+1):
            event_start=len(cpu.seek_events);cycles=advance();step_costs.append(cycles)
            actual=deepcopy(cpu.seek_events[event_start:]);working=block(cpu,'game_history_seek_working','game_history_seek_storage_end')
            assert working==references[boundary][0] and actual==references[boundary][1]
            assert cursor(cpu,'game_history_seek_cursor')==boundary and public(cpu)==selected
            assert block(cpu,'game_preview_storage','game_preview_storage_end')==preview_after_begin
            name,args=stream[boundary-1]
            rows.append(dict(boundary=boundary,working_cursor=cursor(cpu,'game_history_seek_cursor'),
                operation=name,arguments=args,actual_body_operations=1,working_state=working.hex(),
                reference_state=references[boundary][0].hex(),events=actual,reference_events=references[boundary][1],
                public_state=cpu.state().hex(),public_metadata=block(cpu,'game_history_state','game_history_state_end').hex(),public_position=cursor(cpu,'game_history_position'),
                public_canonical_preserved=True,public_metadata_preserved=True,frozen_store_preserved=True,
                live_outputs_preserved=True,replaying_zero=True,preview_owner_zero=True,cpu_cycles=cycles))
        assert field(cpu,'game_history_seek_status')==2 and field(cpu,'game_history_seek_remaining')==0
        assert cpu.seek_events[events_start:]==sum((references[i][1] for i in range(CHECKPOINT+1,TARGET+1)),[])
        rejection('stale-step','game_history_seek_step',{0:job_generation-1,1:1})
        rejection('stale-commit','game_history_seek_commit',{0:job_generation-1})
        rejection('stale-cancel','game_history_seek_cancel',{0:job_generation-1})
        rejection('preview-request-overlap','game_preview_request',{0:field(cpu,'game_preview_generation',4),1:0xffff,2:0,3:0})
        rejection('preview-result-overlap','game_preview_result',{0:field(cpu,'game_preview_generation',4)})
        rejection('failed-begin-range','game_history_seek_begin',{0:job_generation,1:0,2:836})
        checkpoints=symbols['game_history_checkpoints']
        cp=next(checkpoints+i*330 for i in range(field(cpu,'game_history_checkpoint_count'))
            if int.from_bytes(cpu.mem.r_block(checkpoints+i*330,8),'big')==CHECKPOINT)
        for name,offset in (('failed-begin-schema',8),('failed-begin-simulation',10),
                ('failed-begin-state',12+symbols['game_entropy_policy']-symbols['game_core_state'])):
            address=cp+offset;original=cpu.mem.r8(address)
            cpu.mem.w8(address,0xff)
            rejection(name,'game_history_seek_begin',{0:job_generation,1:0,2:TARGET})
            cpu.mem.w8(address,original) # Explicit negative fixture poison retirement, not product repair.
        record=symbols['game_history_buffer']+(CHECKPOINT&4095)*14
        original=cpu.mem.r16(record);cpu.mem.w16(record,10)
        rejection('failed-begin-opcode','game_history_seek_begin',{0:job_generation,1:0,2:TARGET})
        cpu.mem.w16(record,original)
        # Successful cancellation immediately before commit cannot publish READY.
        cancel_cycles=checked(cpu,'game_history_seek_cancel',{0:job_generation})
        assert public(cpu)==selected
        negatives.append(dict(name='cancel-before-commit',passed=True,preserved=True,cpu_cycles=cancel_cycles))
        rejection('canceled-commit','game_history_seek_commit',{0:job_generation})
        begin();replacement=generation(cpu)
        for _ in range(TARGET-CHECKPOINT):advance()
        assert field(cpu,'game_history_seek_status')==2
        begin(TARGET-1)
        rejection('supersede-before-commit','game_history_seek_commit',{0:replacement})
        assert public(cpu)==selected
        # Return to the same57-boundary job; no expected canonical injection.
        begin()
        for _ in range(TARGET-CHECKPOINT):advance()
        commit_cycles=checked(cpu,'game_history_seek_commit',{0:generation(cpu)})
        final=public(cpu);expected_metadata=bytearray(selected['metadata'])
        position_offset=symbols['game_history_position']-symbols['game_history_state']
        expected_metadata[position_offset:position_offset+8]=TARGET.to_bytes(8,'big')
        assert final['state']==references[TARGET][0] and final['state']!=selected['state']
        assert final['metadata']==bytes(expected_metadata) and final['store']==selected['store'] and final['events']==selected['events'] and final['native_intents']==selected['native_intents']
        # The new owner guards must still permit a real preview after commit.
        candidate=next(((ordinal,row) for ordinal,row in enumerate(attempts(cpu))
            if row[0]==TARGET and row[1] in (1,2)),None)
        assert candidate is not None,'Actual835 prefix lacks completed target569 return/miss'
        ordinal,(_,_,end)=candidate
        player=symbols['game_play_state']+10*end
        x,y=cpu.mem.r8(player+3),cpu.mem.r8(player+2)
        settled=public(cpu);job_saved=block(cpu,'game_history_seek_storage','game_history_seek_storage_end')
        preview_generation=field(cpu,'game_preview_generation',4)
        checked(cpu,'game_preview_request',{0:preview_generation,1:ordinal,2:x,3:y})
        preview_generation=field(cpu,'game_preview_generation',4)
        preview_bodies=sum(cpu.visits.get(pc,0) for pc in bodies)
        checked(cpu,'game_preview_step',{0:preview_generation,1:1})
        assert sum(cpu.visits.get(pc,0) for pc in bodies)-preview_bodies==1,'Fresh preview ownership regression did not execute one actual body'
        checked(cpu,'game_preview_cancel',{0:preview_generation})
        assert public(cpu)==settled and block(cpu,'game_history_seek_storage','game_history_seek_storage_end')==job_saved
        preview_regression=dict(accepted_after_commit=True,one_body_yield_preserved=True,
            cancellation_preserved=True,seek_storage_preserved=True,ordinal=ordinal,selection=TARGET,end=end,x=x,y=y)
        begin();old=generation(cpu)
        checked(cpu,'game_history_seek',{0:0,1:TARGET+1})
        newer=public(cpu)
        rejection('newer-selection-preserved','game_history_seek_commit',{0:old})
        assert public(cpu)==newer and cursor(cpu,'game_history_position')==TARGET+1
        begin()
        older=public(cpu);sync_negatives=[]
        def sync_failure(name,target=TARGET):
            saved=full(cpu);before=public(cpu)
            cycles=checked(cpu,'game_history_seek',{0:target>>32,1:target&0xffffffff},0)
            after=public(cpu);assert full(cpu)==saved,('Failed synchronous seek changes older selection/job',name)
            sync_negatives.append(dict(name=name,passed=True,preserved=True,cpu_cycles=cycles,
                before_state=before['state'].hex(),after_state=after['state'].hex(),
                before_metadata=before['metadata'].hex(),after_metadata=after['metadata'].hex(),
                before_store_sha256=hashlib.sha256(before['store']).hexdigest(),after_store_sha256=hashlib.sha256(after['store']).hexdigest(),
                before_job=saved[1].hex(),after_job=block(cpu,'game_history_seek_storage','game_history_seek_storage_end').hex(),
                before_live_outputs=before['events'],after_live_outputs=after['events'],
                before_native_intents=before['native_intents'],after_native_intents=after['native_intents']))
        sync_failure('range',836)
        for name,offset in (('schema',8),('simulation',10),('state',12+symbols['game_entropy_policy']-symbols['game_core_state'])):
            address=cp+offset;original=cpu.mem.r8(address);cpu.mem.w8(address,0xff)
            sync_failure(name);cpu.mem.w8(address,original)
        original=cpu.mem.r16(record);cpu.mem.w16(record,10)
        sync_failure('opcode');cpu.mem.w16(record,original)
        original_mode=cpu.mem.r16(record+6)
        cpu.mem.w16(record,2);cpu.mem.w16(record+6,2)
        sync_failure('select-mode');cpu.mem.w16(record,original);cpu.mem.w16(record+6,original_mode)
        supersession=[]
        for label,target,count in (('zero-operation',512,0),('one-operation',513,1)):
            if field(cpu,'game_history_seek_status')!=1:begin()
            old=generation(cpu);body_before=sum(cpu.visits.get(pc,0) for pc in bodies)
            cycles=checked(cpu,'game_history_seek',{0:0,1:target})
            actual=sum(cpu.visits.get(pc,0) for pc in bodies)-body_before
            assert actual==count and cpu.state()==references[target][0] and cursor(cpu,'game_history_position')==target
            assert generation(cpu)!=old and field(cpu,'game_history_seek_status')==0
            saved=full(cpu);checked(cpu,'game_history_seek_commit',{0:old},0);assert full(cpu)==saved
            supersession.append(dict(kind=label,target=target,actual_body_operations=actual,
                state=cpu.state().hex(),reference_state=references[target][0].hex(),position=cursor(cpu,'game_history_position'),
                generation_retired=True,stale_commit_preserved=True,cpu_cycles=cycles))
        sync_validation=dict(passed=True,older_position=570,older_state=older['state'].hex(),older_metadata=older['metadata'].hex(),
            negatives=sync_negatives,supersession=supersession)
        cpu.mem.w32(symbols['game_history_seek_generation'],0xffffffff) # Private-generation exhaustion control only.
        rejection('generation-exhaustion','game_history_seek_begin',{0:0xffffffff,1:0,2:TARGET})
        cpu.audit_reads()
        report=dict(passed=True,image_role=role,base=base,executable_path=str(executable.relative_to(ROOT)),image_sha256=digest(executable),
            restored_adapter_words={name:raw.hex() for name,raw in getattr(cpu,'native_entries',{}).items()},
            adapters_restored_before_freeze=native,adapter_words_preserved=native,
            full_bus_nonstate_guard=True,frozen_history_write_guard=True,semantic_observer_read_only=True,
            setup_traps_outside_evidence=True,
            checkpoint=CHECKPOINT,target=TARGET,body_operations=57,boundaries=57,
            selected_state=selected['state'].hex(),selected_metadata=selected['metadata'].hex(),selected_position=selected_position,
            rows=rows,committed_state=final['state'].hex(),committed_metadata=final['metadata'].hex(),committed_position=TARGET,
            preview_regression=preview_regression,
            sync_validation=sync_validation,
            costs=dict(begin_cpu_cycles=begin_cycles,step_cpu_cycles=step_costs,commit_cpu_cycles=commit_cycles,
                cancel_cpu_cycles=cancel_cycles,maximum_stack_bytes=cpu.stack_bytes),negatives=negatives,
            guard_scope='Actual frozen store/live output preservation; selected318/all72 restored at every public return; emitted native adapters restored beforefreeze.')
    report['carry_validation']=carry_proof(executable,base,native)
    return report


def carry_proof(executable,base,native):
    """One history-only starting origin, then actual inputs across low-long carry."""
    image,symbols=load_image(executable,base);offset=(1<<32)-64
    stream=[('game_core_select',[0,0xace1,0])]
    for tick in range(24):
        stream.extend([('game_round_poll',[]),('game_core_sample_pads',[16 if tick>=8 else 0,0]),
            ('game_core_sample_result',[0]*6),('game_tick_dispatch',[])])
    with Core(image,symbols,readonly=READONLY) as cpu:
        cpu.call_logical('game_core_init',[]);attach(cpu)
        initial=cpu.state()
        for name in ('game_history_cursor','game_history_oldest','game_history_checkpoints'):
            cpu.mem.w_block(symbols[name],offset.to_bytes(8,'big'))
        assert cpu.state()==initial
        states={offset:initial}
        for index,(name,args) in enumerate(stream,1):
            cpu.call_logical(name,args);states[offset+index]=cpu.state()
        if native:native_entries(cpu,image)
        checked(cpu,'game_history_freeze',{})
        original_trace=cpu.trace
        def guard(mode,width,address,value):
            if mode=='W' and address<symbols['game_history_buffer_end'] and address+(1<<width)>symbols['game_history_buffer']:
                raise AssertionError('Carry fixture writes frozen recorder/live backup')
            original_trace(mode,width,address,value)
        cpu.mem.set_trace_func(guard)
        assert cursor(cpu)==offset+97 and cursor(cpu)>>32==1
        bodies={symbols[n+'_body'] for n in OPERATIONS}
        rows=[]
        for target in (offset,(1<<32)-1,1<<32,(1<<32)+1,(1<<32)+17,offset+97):
            ledger=cpu.native_semantic_events if native else cpu.events
            start=len(ledger)
            sync_cycles=checked(cpu,'game_history_seek',{0:target>>32,1:target&0xffffffff})
            sync_events=deepcopy(ledger[start:]);sync_state=cpu.state()
            assert sync_state==states[target] and cursor(cpu,'game_history_position')==target
            selected=public(cpu)
            begin_cycles=checked(cpu,'game_history_seek_begin',{0:generation(cpu),1:target>>32,2:target&0xffffffff})
            origin=cursor(cpu,'game_history_seek_cursor');count=field(cpu,'game_history_seek_remaining')
            assert 0<=count<=63 and origin+count==target
            event_start=len(cpu.seek_events);working_rows=[]
            while field(cpu,'game_history_seek_status')==1:
                boundary=cursor(cpu,'game_history_seek_cursor')+1
                visits=sum(cpu.visits.get(pc,0) for pc in bodies)
                cycles=checked(cpu,'game_history_seek_step',{0:generation(cpu),1:1})
                actual=sum(cpu.visits.get(pc,0) for pc in bodies)-visits
                assert actual==1
                assert public(cpu)==selected
                working=block(cpu,'game_history_seek_working','game_history_seek_storage_end')
                assert working==states[boundary]
                working_rows.append(dict(cursor=boundary,state=working.hex(),reference_state=states[boundary].hex(),
                    actual_body_operations=actual,cpu_cycles=cycles))
            events=deepcopy(cpu.seek_events[event_start:])
            assert events==sync_events
            commit_cycles=checked(cpu,'game_history_seek_commit',{0:generation(cpu)})
            assert cpu.state()==sync_state and cursor(cpu,'game_history_position')==target
            assert public(cpu)['events']==selected['events'] and public(cpu)['native_intents']==selected['native_intents']
            rows.append(dict(target=target,origin=origin,body_operations=count,sync_state=sync_state.hex(),
                sliced_state=cpu.state().hex(),sync_events=sync_events,sliced_events=events,position=target,
                working_rows=working_rows,begin_cpu_cycles=begin_cycles,sync_cpu_cycles=sync_cycles,commit_cpu_cycles=commit_cycles))
        bounds=[]
        for target in (offset-1,offset+98):
            for api,args in (('game_history_seek',{0:target>>32,1:target&0xffffffff}),
                    ('game_history_seek_begin',{0:generation(cpu),1:target>>32,2:target&0xffffffff})):
                saved=full(cpu);cycles=checked(cpu,api,args,0);assert full(cpu)==saved
                bounds.append(dict(api=api,target=target,preserved=True,cpu_cycles=cycles))
        cpu.audit_reads()
        return dict(passed=True,initial_origin=offset,operations=97,final_cursor=cursor(cpu),low_longword_carry_observed=True,
            rows=rows,range_negatives=bounds,maximum_stack_bytes=cpu.stack_bytes,
            initialization_scope='One history-only origin before any recorded operation; no intermediate canonical state injected.')
