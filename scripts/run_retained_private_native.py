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
CORE_SHA='951935ce4ec1538f5ff2fa83898c36af7a75de60f4c0fe025e74181543f1544c'


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
    native.call('game_preview_cancel',[native.number('game_preview_generation',4)])
    native.resume()
    native.session.inspect('break_remove',{'id':native.breakpoint});native.breakpoint=native.arm('main_loop')
    native.stop=native.session.inspect('run_until',{'seconds':native.stop['seconds']+.2})
    assert native.stop['pc']==native.symbols['main_loop']
    native.observer.finish();assert native.observer.current_callback is None
    return candidate,observations


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
        assert (len(expected[0]),expected[1],expected[2],hashlib.sha256(expected[0]).hexdigest())==(17524,7,14,CORE_SHA)
        manifests=[compile_manifest(product,product.parent/'native.lst'),compile_manifest(standalone,core_listing),fixture_manifest]
        image,symbols=load_image(standalone)
        with Core(image,symbols,readonly=READONLY) as cpu:
            with ObservedSession(directory) as session:
                native=Native(session,executable,listing,standard,cpu)
                candidate,observations=schedule(native,directory)
                video={n:native.number(n,size) for n,size in [('presentation_last_line',2),('simulation_interval_whole',4),('simulation_interval_fraction',2)]}
                assert list(video.values())==([311,11838,14906] if standard=='PAL' else [261,11947,13180])
                costs=measurement(native,video);assert costs['minimum_callback_headroom_cck']>=0
                observer=native.observer;frames=observer.body_frames
                assert frames.entries==len(frames.records) and not frames.stack
                assert observer.irq_inside>0 and any(r['irq'] for r in observer.api_rows if r['name']=='game_preview_step')
                assert not observer.drops and not observer.problems
                irq_owner_roles=sorted({frame['ownership']['active'] for frame in frames.records
                    if frame['ownership']['active'] in (1,2) and any(
                        row['pc']==observer.irq_entry_pc and frame['start']['cck']<=row['position']['cck']<=frame['end']['cck']
                        for row in observer.irq_writes)})
                assert irq_owner_roles==[1,2],'Both resolver and variant bodies need actual interrupt coverage'
                validation=dict(passed=True,candidate=candidate,video=video,costs=costs,
                    memory=memory_summary(chip_memory(native.read)),cpu_receipts=CPU_RECEIPTS,
                    body_frames=frames.records,body_sink_events=observer.body_sink_events,
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
                callback_rows=native.observer.callback_rows,problems=native.observer.problems,body_frames=native.observer.body_frames.records)))
            native.observer.close()
        transaction.abort(error);raise


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--ntsc',action='store_true')
    args=parser.parse_args();run('NTSC' if args.ntsc else 'PAL')
