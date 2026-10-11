"""Explicitly selected differential proof against the retained reviewed product."""
import json
import os
from pathlib import Path
from build_match_core import build
from build_native_game import build as build_native
from check_shared_core_bytes import run as shared_bytes
from match_core_cpu import cpu_tool_inputs
from native_evidence import ReportRun,atomic_json,compile_manifest,digest,inputs_for,snapshot,status
from native_tools import ROOT
from private_state_proof import exercise

BEFORE_SHA='c543a695d9493254eb152cf34a093676c3c0c0dcd4df203d0ad105a5b97e3cb8'


def run():
    output=ROOT/'build/tests/private-state-cpu/report.json'
    transaction=ReportRun([output],'build','maintained-native','actual CPU private-state differential')
    try:
        before=Path(os.environ['CTENNIS_PRIVATE_STATE_BEFORE']).resolve()
        assert digest(before)==BEFORE_SHA,'Explicit reviewed baseline is missing or changed'
        paths,tools=inputs_for('build','scripts/run_private_state_proof.py')
        cpu_paths,tools['machine68k']=cpu_tool_inputs()
        transaction.meta.update(files=snapshot(paths|cpu_paths|{before}),tools=tools,
            actual_execution='actual-68000-cpu-only',target_role='legacy-validator-reference',
            target_scope='CPU differential only, no native display/deadline claim')
        transaction.meta['environment'].update(PYTHONPATH=os.environ.get('PYTHONPATH'),
            CTENNIS_PRIVATE_STATE_BEFORE=str(before))
        standalone,listing=build();_,native=build_native()
        audit=shared_bytes()
        result=exercise(before,native,standalone)
        report=dict(passed=True,execution='actual-68000-cpu-only',private_state_validation=result,
                    shared_byte_audit=audit,executable_sha256=digest(native))
        raw=output.parent/'results-unvalidated.json';atomic_json(raw,dict(report,receipt_validated=False))
        transaction.finalize(output,report,compiled=[compile_manifest(standalone,listing),
            compile_manifest(native,native.parent/'native.lst')],artifacts=[raw])
        assert status(output)['status']=='passed',status(output)
        print(json.dumps(dict(passed=True,report=str(output),operations=result['operations'])),flush=True)
    except BaseException as error:
        transaction.abort(error);raise


if __name__=='__main__':run()
