"""Execute the focused actual CPU preview proof through native_acceptance.py."""
import json
import os
from build_match_core import build
from match_core_cpu import cpu_tool_inputs
from native_evidence import ReportRun,atomic_json,compile_manifest,digest,inputs_for,snapshot,status
from native_tools import ROOT
from preview_proof import small
from preview_cache_proof import exercise as cache_proof
from preview_extended_proof import stage_a1
from preview_discovery_proof import discovery
from preview_isolation_proof import isolation
from preview_batch_proof import batching
from build_native_game import build as build_native


def run():
    path=ROOT/'build/tests/preview-cpu/report.json'
    transaction=ReportRun([path],'preview-cpu','maintained-native','actual CPU, no emulator')
    try:
        paths,tools=inputs_for('build','scripts/run_preview_proof.py')
        cpu_paths,tools['machine68k']=cpu_tool_inputs()
        transaction.meta.update(files=snapshot(paths|cpu_paths),tools=tools,
            target_role='legacy-validator-reference',actual_execution='actual-68000-cpu-only',
            target_scope='evidence.target is a legacy validation reference, not an actual display target.')
        transaction.meta['environment']['PYTHONPATH']=os.environ.get('PYTHONPATH')
        executable,listing=build()
        validation=small(executable)
        atomic_json(path.parent/('small-results-'+transaction.meta['run_id']+'-unvalidated.json'),
            dict(preview_validation=validation,receipt_validated=False,receipt_run_id=transaction.meta['run_id']))
        validation['cache_validation']=cache_proof(executable)
        atomic_json(path.parent/('cache-results-'+transaction.meta['run_id']+'-unvalidated.json'),
            dict(preview_validation=validation,receipt_validated=False,receipt_run_id=transaction.meta['run_id']))
        stage_a1_rows=[]
        def progress(row):
            stage_a1_rows.append(row)
            atomic_json(path.parent/('stage-a1-progress-'+transaction.meta['run_id']+'-unvalidated.json'),
                dict(rows=stage_a1_rows,receipt_validated=False,receipt_run_id=transaction.meta['run_id']))
            print(json.dumps(row),flush=True)
        validation['stage_a1_validation']=stage_a1(executable,progress)
        atomic_json(path.parent/('a1-results-'+transaction.meta['run_id']+'-unvalidated.json'),
            dict(preview_validation=validation,receipt_validated=False,receipt_run_id=transaction.meta['run_id']))
        stage_a2_rows=[]
        def discovery_progress(row):
            stage_a2_rows.append(row)
            atomic_json(path.parent/('stage-a2-progress-'+transaction.meta['run_id']+'-unvalidated.json'),
                dict(rows=stage_a2_rows,receipt_validated=False,receipt_run_id=transaction.meta['run_id']))
            print(json.dumps(row),flush=True)
        validation['stage_a2_validation']=discovery(executable,discovery_progress)
        isolation_rows=[]
        def isolation_progress(row):
            isolation_rows.append(row)
            atomic_json(path.parent/('stage-a3-progress-'+transaction.meta['run_id']+'-unvalidated.json'),
                dict(rows=isolation_rows,receipt_validated=False,receipt_run_id=transaction.meta['run_id']))
            print(json.dumps(row),flush=True)
        _,native=build_native()
        validation['stage_a3_validation']=isolation(executable,native,isolation_progress)
        batch_rows=[]
        def batch_progress(row):
            batch_rows.append(row)
            atomic_json(path.parent/('batch-progress-'+transaction.meta['run_id']+'-unvalidated.json'),
                dict(rows=batch_rows,receipt_validated=False,receipt_run_id=transaction.meta['run_id']))
            print(json.dumps(row),flush=True)
        validation['batch_validation']=batching(executable,batch_progress)
        validation['scope']='Fresh actual 68000 CPU first-small, cache, A1 API/context/lifecycle, A2 bounded endpoints and A3 relocation/emitted frozen sinks/history regression and operation-budget batching only. Current real native interrupt/paused latency/resources/performance and UI remain pending.'
        report=dict(passed=True,execution='actual-68000-cpu-only',executable_sha256=digest(executable),
            preview_validation=validation,scope=validation['scope'])
        atomic_json(path.parent/('proof-results-'+transaction.meta['run_id']+'-unvalidated.json'),dict(report,
            receipt_validated=False,receipt_run_id=transaction.meta['run_id']))
        transaction.finalize(path,report,compiled=[compile_manifest(executable,listing),
            compile_manifest(native,native.parent/'native.lst')])
        assert status(path)['status']=='passed',status(path)
        print(json.dumps(report),flush=True)
    except BaseException as error:
        transaction.abort(error)
        raise


if __name__=='__main__':run()
