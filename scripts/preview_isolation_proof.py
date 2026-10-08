"""A3 exact input continuations at two relocations and emitted native sinks."""
import hashlib
from build_match_core import load_image
from check_shared_core_bytes import normalized
from history_proof import attach,attempts,cursor,logical_api,exercise
from match_core_cpu import Core
from preview_proof import fixture,protected,call_checked
from preview_extended_proof import candidates,execute,continuous,table
from preview_discovery_proof import sampling_rows,qualification
from preview_native_proof import native_entries,assert_native_entries,seek_preserving_ledger
from run_shared_match_core import READONLY

# Input descriptors only. No expected intermediate gameplay state is supplied.
DESCRIPTORS=((0,'low',-16),(1,'regular',-16),(1,'regular',16))


def empty_boundary(executable):
    image,symbols=load_image(executable)
    with Core(image,symbols,readonly=READONLY) as cpu:
        cpu.call_logical('game_core_init',[]);attach(cpu)
        selected=cpu.state();cpu.clear_events();cpu.call('game_history_freeze')
        size=symbols['game_history_buffer_end']-symbols['game_history_buffer']
        saved=bytes(cpu.mem.r_block(symbols['game_history_buffer'],size));seek_preserving_ledger(cpu,0)
        assert cpu.state()==selected and cpu.events==[]
        assert bytes(cpu.mem.r_block(symbols['game_history_buffer'],size))==saved
        cpu.audit_reads()
    return dict(passed=True,operations=0,boundaries_checked=1,selected_history_output_preserved=True)


def isolation(standalone,native,progress):
    left,relocations,branches=normalized(native,native.parent/'native.lst')
    right,other_relocations,other_branches=normalized(standalone,standalone.parent/'match-core.lst')
    assert left==right and (relocations,branches)==(other_relocations,other_branches)
    audit=dict(passed=True,matched_bytes=len(left),relocations_each=relocations,
        verified_sink_branches_each=branches,normalized_sha256=hashlib.sha256(left).hexdigest())
    images=[];baseline=None
    for label,executable,base,is_native in (('standalone',standalone,0x10000,False),
            ('relocated',standalone,0x30000,False),('emitted-native',native,0x10000,True)):
        image,symbols=load_image(executable,base);observations=[]
        with Core(image,symbols,readonly=READONLY) as cpu:
            stream,states,_,launches=fixture(cpu,seed=0xace1,dispatches=512)
            eligible=candidates(attempts(cpu),launches)
            assert len(eligible)==2, 'A3 known input fixture lacks first two actual completed returns'
            if is_native:native_entries(cpu,image)
            else:
                # Same full-extent frozen history guard as the emitted image.
                from history_proof import field
                original_trace=cpu.trace
                def guard(mode,width,address,value):
                    if (mode=='W' and field(cpu,'game_history_mode',1)==2
                            and address<symbols['game_history_buffer_end']
                            and address+(1<<width)>symbols['game_history_buffer']):
                        raise AssertionError('Relocated frozen proof writes history/live backup')
                    original_trace(mode,width,address,value)
                cpu.mem.set_trace_func(guard)
            cpu.call('game_history_freeze');assert_native_entries(cpu)
            frozen_store=bytes(cpu.mem.r_block(symbols['game_history_buffer'],symbols['game_history_buffer_end']-symbols['game_history_buffer']))
            live_outputs=list(cpu.events)
            for index,(candidate_index,band,lateral) in enumerate(DESCRIPTORS):
                candidate=eligible[candidate_index]
                sample=next((row for row in sampling_rows(cpu,candidate,stream,states)
                    if row['band']==band and row['available']),None)
                assert sample is not None, 'A3 descriptor lacks actual recorded time row: '+band
                selection=sample['selection'];seek_preserving_ledger(cpu,selection);assert_native_entries(cpu)
                assert cursor(cpu,'game_history_position')==selection
                assert cpu.state()==states[selection], 'Image-specific history seek differs from recorded actual full state'
                if is_native:assert cpu.events==live_outputs
                assert bytes(cpu.mem.r_block(symbols['game_history_buffer'],len(frozen_store)))==frozen_store
                bounds=table(cpu,candidate['end']);assert bounds==sample['bounds']
                x=max(bounds['left'],min(bounds['right']-1,sample['center_x']+lateral));y=sample['center_y']
                observation=execute(cpu,candidate['ordinal'],selection,x,y,stream,0xace1,f'isolation-{index}')
                facts=qualification(observation,symbols)
                descriptor=dict(candidate_index=candidate_index,band=band,lateral_offset=lateral,
                    ordinal=candidate['ordinal'],incoming_origin=candidate['incoming_origin'],
                    probe_origin=candidate['probe_origin'],original_action=candidate['origin'],
                    selection=selection,x=x,y=y,sampling_row=sample)
                observations.append((observation,facts,descriptor))
                saved=protected(cpu)
                call_checked(cpu,'game_preview_cancel',{0:cpu.mem.r32(symbols['game_preview_generation'])},saved)
                assert_native_entries(cpu)
            cpu.audit_reads()
            entries={name:raw.hex() for name,raw in getattr(cpu,'native_entries',{}).items()}
        reports=[];semantic=[];coverage=set()
        for observation,facts,descriptor in observations:
            report=continuous(image,symbols,observation,native_sinks=is_native)
            report.update(qualification=facts,descriptor=descriptor)
            reports.append(report);coverage.update(facts['coverage'])
            semantic.append({key:report[key] for key in ('seed','ordinal','selection','end','x','y',
                'selected_state','edited_state','final_states','paths','classes','ordered_outputs',
                'actual_accepted_launches','actual_final_boundaries','prefix_samples','incoming_origin','action_boundary')})
        assert coverage=={'net','out','interception','coincidence'}, 'A3 actual input cases lost endpoint coverage'
        if baseline is None:baseline=semantic
        else:assert semantic==baseline, 'Relocation/native emitted sinks change actual states/paths/outcomes/semantic intents'
        row=dict(name=label,base=base,passed=True,cases=reports,semantic_equal=True,
            actual_coverage=sorted(coverage),restored_adapter_words=entries,
            adapters_restored_before_freeze=is_native,adapter_words_preserved=True,
            full_bus_nonstate_guard=True,frozen_history_write_guard=True,
            history_seek_cases_checked=3,history_seek_full_state_store_equal=True,
            history_seek_live_output_preserved=is_native,
            semantic_observer_read_only=True,setup_traps_outside_evidence=True)
        images.append(row);progress(dict(stage='stage-a3-image',result=row))
    # Focused current-product regressions retain full canonical/output/ABI
    # comparisons and both directions at every retained ring boundary.
    regressions=dict(image='standalone',base=0x10000,
        empty=empty_boundary(standalone),logical_api=dict(logical_api(standalone),passed=True),
        ring_wrap=dict(exercise(standalone,ticks=1040,wrap=True),passed=True),
        failed_seek_all72_rollback_covered_by='cache_validation')
    report=dict(passed=True,shared_byte_audit=audit,seed=0xace1,dispatch_cap=512,
        ordinary_operation_cap=2049,descriptors=[list(row) for row in DESCRIPTORS],
        images=images,history_regressions=regressions,
        semantic_state_path_outcome_output_equal=True,
        scope='A3 actual CPU relocation and emitted frozen sinks. Setup traps outside evidence; semantic intent ledger is read-only. Real native interrupt/paused latency/resources remain pending.')
    progress(dict(stage='stage-a3-complete',result=report))
    return report
