"""Two bounded retained-return jobs using the existing physical mailbox fixture."""
import argparse
import hashlib
import json
import os
from pathlib import Path
from build_match_core import build as build_core,load_image
from build_native_game import build as build_native
from check_shared_core_bytes import normalized
from history_proof import cursor
from match_core_cpu import Core,cpu_tool_inputs
from native_evidence import ReportRun,atomic_json,compile_manifest,digest,inputs_for,snapshot,status
from native_metrics import memory_summary
from native_tools import ROOT
from ordinary_cadence import chip_memory
from preview_extended_proof import continuous,table
from run_preview_native import (Native,ObservedSession,overlay,retained_candidate,
    measurement,json_value,CAPS)
from run_shared_match_core import READONLY

from retained_private_extent import CPU_RECEIPTS
CORE_SHA='99c543c170c036137be81d07ebd30b522ef3abdff04bd7b1af38f00047bb99d5'


def seek_once(native,target):
    generation=native.number('game_history_seek_generation',4)
    native.call('game_history_seek_begin',[generation,target>>32,target&0xffffffff])
    generation=native.number('game_history_seek_generation',4)
    for _ in range(512):
        if native.number('game_history_seek_status')==2:break
        native.call('game_history_seek_step',[generation,1])
    else:raise AssertionError('One bounded seek did not become ready')
    native.call('game_history_seek_commit',[generation])
    assert native.number('game_history_position',8)==target


def private_irq_proofs(observer):
    """Only completed literal acknowledgement pairs inside an owned body count."""
    acks=[r for r in observer.irq_writes if r['pc'] in (observer.irq_entry_pc,observer.irq_exit_pc)]
    pairs=[(a,b) for a,b in zip(acks,acks[1:])
        if a['pc']==observer.irq_entry_pc and b['pc']==observer.irq_exit_pc
        and a['position']['cck']<b['position']['cck']]
    proofs=[]
    for role in (1,2):
        for frame in observer.body_frames.records:
            if frame['ownership']['active']!=role:continue
            pair=next(((a,b) for a,b in pairs if frame['start']['cck']<=a['position']['cck']
                <b['position']['cck']<=frame['end']['cck']),None)
            if pair:
                proofs.append(dict(role=role,entry_index=frame['entry_index'],
                    api_row_index=frame['api_row_index'],acknowledgements=list(pair)))
                break
    return proofs


def cover_private_irqs(native,ordinal,x,y):
    """Fixed-budget normal API work; never force an IRQ or choose a clock phase."""
    initial=private_irq_proofs(native.observer)
    ledger=dict(needed=len(initial)!=2,budget=3,maximum_worker_calls=512,
        initial_roles=[r['role'] for r in initial],worker_api_row_indices=[],worker_body_counts=[])
    if ledger['needed']:
        ledger['invalidating_cancel_api_row_index']=len(native.observer.api_rows)
        native.call('game_preview_cancel',[native.number('game_preview_generation',4)])
        ledger['request_api_row_index']=len(native.observer.api_rows)
        generation=native.request(ordinal,x,y);ledger['generation']=generation
        ledger['request_arguments']=[generation-1,ordinal,x,y]
        assert native.number('game_preview_status')==1,'IRQ coverage request must resolve a cold retained job'
        for _ in range(512):
            assert native.number('game_preview_status')<5,'Coverage job finished without required in-body IRQ'
            ledger['worker_api_row_indices'].append(len(native.observer.api_rows))
            cost=native.step(generation,3);ledger['worker_body_counts'].append(cost['bodies'])
            if len(private_irq_proofs(native.observer))==2:break
        else:raise AssertionError('Fixed-budget IRQ coverage cap exhausted')
        ledger['status_before_cancel']=native.number('game_preview_status')
        ledger['generation_before_cancel']=native.number('game_preview_generation',4)
        assert 1<=ledger['status_before_cancel']<5,'Coverage job completed before diagnostic cancellation'
        assert ledger['generation_before_cancel']==generation,'Coverage generation changed before cancellation'
        ledger['cancel_api_row_index']=len(native.observer.api_rows)
        native.call('game_preview_cancel',[generation])
        ledger['cancelled_incomplete_job']=True
    ledger['final_proofs']=private_irq_proofs(native.observer)
    assert [r['role'] for r in ledger['final_proofs']]==[1,2]
    ledger['passed']=True
    return ledger


def schedule(native,directory):
    native.key(0x01,True);native.key(0x01,False);native.fire(True)
    for _ in range(CAPS['playing_dispatches']):
        candidate=retained_candidate(native)
        if candidate is not None:break
        native.idle()
    else:raise AssertionError('Physical fixed-seed acquisition lacks retained human return/miss')
    native.fire(False);native.freeze();seek_once(native,candidate['probe'])
    end=candidate['end'];x,y=native.position(end)
    observations=[native.completed('retained-cold-budget4',candidate['ordinal'],candidate['probe'],end,x,y,4)]
    assert observations[0]['costs']['resolver_operations']>0
    bounds=table(native.cpu,end);edited_x=x+1 if x<bounds['right']-1 else x-1
    observations.append(native.completed('retained-cached-budget2',candidate['ordinal'],candidate['probe'],end,edited_x,y,2))
    assert observations[1]['costs']['cache_hit'] and observations[1]['costs']['resolver_operations']==0
    atomic_json(directory/'observations-unvalidated.json',json_value(observations))
    coverage=cover_private_irqs(native,candidate['ordinal'],edited_x,y)
    atomic_json(directory/'irq-coverage-unvalidated.json',json_value(coverage))
    native.call('game_preview_cancel',[native.number('game_preview_generation',4)])
    native.resume()
    native.session.inspect('break_remove',{'id':native.breakpoint});native.breakpoint=native.arm('main_loop')
    native.stop=native.session.inspect('run_until',{'seconds':native.stop['seconds']+.2})
    assert native.stop['pc']==native.symbols['main_loop']
    native.observer.finish();assert native.observer.current_callback is None
    return candidate,observations,coverage


def run(standard):
    directory=ROOT/'build/tests'/('private-state-retained-'+standard.lower());directory.mkdir(parents=True,exist_ok=True)
    output=directory/'report.json';transaction=ReportRun([output],'preview-native','maintained-native','bounded retained-return mailbox fixture')
    native=None
    try:
        paths,tools=inputs_for('preview-native','scripts/run_retained_private_native.py')
        cpu_paths,tools['machine68k']=cpu_tool_inputs();paths|=cpu_paths|{ROOT/'scripts/preview_native_fixture.s'}
        for name,sha in CPU_RECEIPTS.items():
            p=ROOT/name;assert digest(p)==sha and status(p)['status']=='passed',('Prior actual CPU proof changed',name)
            paths.add(p)
        transaction.meta.update(files=snapshot(paths),tools=tools,actual_execution='actual-native-paused-retained',
            actual_target=dict(transaction.meta['target'],video=standard),target_role='legacy-validator-reference',
            target_scope='Fixed-seed test-only mailbox fixture; actual PAL/NTSC backend/IRQ timing, no retained UI or full-release claim')
        transaction.meta['environment']['PYTHONPATH']=os.environ.get('PYTHONPATH')
        _,product=build_native();standalone,core_listing=build_core()
        executable,listing,fixture_manifest,overlay_identity=overlay(directory)
        expected=normalized(standalone,core_listing)
        assert normalized(product,product.parent/'native.lst')==normalized(executable,listing)==expected
        assert (len(expected[0]),expected[1],expected[2],hashlib.sha256(expected[0]).hexdigest())==(17606,7,14,CORE_SHA)
        manifests=[compile_manifest(product,product.parent/'native.lst'),compile_manifest(standalone,core_listing),fixture_manifest]
        image,symbols=load_image(standalone)
        with Core(image,symbols,readonly=READONLY) as cpu:
            with ObservedSession(directory) as session:
                native=Native(session,executable,listing,standard,cpu)
                candidate,observations,coverage=schedule(native,directory)
                video={n:native.number(n,size) for n,size in [('presentation_last_line',2),('simulation_interval_whole',4),('simulation_interval_fraction',2)]}
                assert list(video.values())==([311,11838,14906] if standard=='PAL' else [261,11947,13180])
                costs=measurement(native,video);assert costs['minimum_callback_headroom_cck']>=0
                observer=native.observer;frames=observer.body_frames
                assert frames.entries==len(frames.records) and not frames.stack
                assert observer.irq_inside>0 and any(r['irq'] for r in observer.api_rows if r['name']=='game_preview_step')
                assert not observer.drops and not observer.problems
                irq_owner_roles=[r['role'] for r in private_irq_proofs(observer)]
                assert irq_owner_roles==[1,2],'Both resolver and variant bodies need actual interrupt coverage'
                validation=dict(passed=True,candidate=candidate,video=video,costs=costs,
                    memory=memory_summary(chip_memory(native.read)),cpu_receipts=CPU_RECEIPTS,
                    body_frames=frames.records,body_sink_events=observer.body_sink_events,
                    irq_coverage_validation=coverage,api_rows=observer.api_rows,
                    irq_rules=observer.rules,irq_writes=observer.irq_writes,irq_inside=observer.irq_inside,
                    irq_owner_roles=irq_owner_roles,actual_body_entries=frames.entries,
                    callback_rows=observer.callback_rows,physical_edges=observer.physical_edges,
                    input_actions=native.input_actions,frozen_intervals=native.frozen_intervals,
                    complete318_history72_backup_preserved=True,private_a5_state_and_outputs_observed=True,
                    full_bus_write_guard=True,canonical_and_other_owner_guard=True,
                    actual_a5_preserved=True,normal_resume=True,dropped_notifications=0,
                    loaded_hunks=native.hunks,overlay=overlay_identity,
                    normalized_core=dict(bytes=len(expected[0]),relocations=expected[1],sinks=expected[2],sha256=CORE_SHA),
                    product_sha256=digest(product),fixture_sha256=digest(executable),
                    scope='Cold resolution and cached edited return, budgets4/2, real physical acquisition and IRQ. One admitted API per callback fixture; no production retained navigation/publisher or universal budget bound.')
                atomic_json(directory/'raw-results-unvalidated.json',json_value(validation))
                cpu.audit_reads();observer.close()
        # machine68k has one global instance; uninterrupted comparisons follow native acquisition.
        validation['completed_jobs']=[continuous(image,symbols,row) for row in observations]
        report=dict(passed=True,execution='actual-native-paused-retained',target=transaction.meta['actual_target'],
            executable_sha256=digest(executable),retained_private_validation=json_value(validation))
        artifacts=[p for p in directory.iterdir() if p.is_file() and p!=output]
        transaction.finalize(output,report,compiled=manifests,artifacts=artifacts)
        assert status(output)['status']=='passed',status(output)
        print(json.dumps(dict(passed=True,report=str(output),minimum_callback_headroom_cck=costs['minimum_callback_headroom_cck'])),flush=True)
    except BaseException as error:
        if native is not None:
            atomic_json(directory/'failure-progress.json',json_value(dict(error=str(error),api_rows=native.observer.api_rows,
                callback_rows=native.observer.callback_rows,problems=native.observer.problems,
                irq_writes=native.observer.irq_writes,body_frames=native.observer.body_frames.records)))
            native.observer.close()
        transaction.abort(error);raise


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--ntsc',action='store_true')
    args=parser.parse_args();run('NTSC' if args.ntsc else 'PAL')
