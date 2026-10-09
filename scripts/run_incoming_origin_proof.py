"""Manifest-bound selective incoming-origin CPU proof; raw evidence remains ignored."""
import json
import os

from build_match_core import build
from build_native_game import build as build_native
from check_shared_core_bytes import run as original_bytes
from incoming_origin_proof import run
from match_core_cpu import cpu_tool_inputs
from native_evidence import ReportRun,atomic_json,compile_manifest,digest,inputs_for,snapshot,status
from native_tools import ROOT


def main():
    output=ROOT/'build/tests/incoming-origin-cpu/report.json'
    transaction=ReportRun([output],'incoming-origin-cpu','maintained-native','actual68000CPU')
    try:
        paths,tools=inputs_for('build','scripts/run_incoming_origin_proof.py')
        cpu_paths,tools['machine68k']=cpu_tool_inputs()
        transaction.meta.update(files=snapshot(paths|cpu_paths),tools=tools,
            runner='scripts/run_incoming_origin_proof.py')
        transaction.meta['environment']['PYTHONPATH']=os.environ.get('PYTHONPATH')
        executable,listing=build();build_native()
        native=ROOT/'build/amiga/interfaces/enhanced/baseline-rally'
        validation=run(executable,output.parent/'raw')
        validation['original_core_bytes']=original_bytes()
        atomic_json(output.parent/'results-unvalidated.json',validation)
        transaction.finalize(output,dict(passed=True,execution='actual-68000-cpu-only',
            executable_sha256=digest(executable),validation=validation),
            [compile_manifest(executable,listing),compile_manifest(native,native.parent/'native.lst')],
            list((output.parent/'raw').glob('*.json'))+[output.parent/'results-unvalidated.json'])
        verdict=status(output)
        assert verdict['status']=='passed',verdict
        print(json.dumps(dict(passed=True,report=str(output),sha256=digest(output))),flush=True)
    except BaseException as error:
        transaction.abort(error);raise


if __name__=='__main__':main()
