"""Manifest-bound focused CPU evidence for the incoming flight integration."""
import json
import os
from build_match_core import build
from incoming_flight_proof import run
from match_core_cpu import cpu_tool_inputs
from native_evidence import ReportRun, compile_manifest, digest, inputs_for, snapshot, status
from native_tools import ROOT


def main():
    output = ROOT/'build/tests/incoming-flight-cpu/report.json'
    transaction = ReportRun([output], 'incoming-flight-cpu', 'maintained-native', 'actual 68000 CPU')
    try:
        paths, tools = inputs_for('build','scripts/run_incoming_proof.py')
        cpu_paths, tools['machine68k'] = cpu_tool_inputs()
        transaction.meta.update(files=snapshot(paths|cpu_paths), tools=tools,
                                runner='scripts/run_incoming_proof.py')
        transaction.meta['environment']['PYTHONPATH']=os.environ.get('PYTHONPATH')
        executable, listing = build()
        result = run(executable)
        report = dict(passed=True, execution='actual-68000-cpu-only',
                      executable_sha256=digest(executable), validation=result)
        transaction.finalize(output,report,compiled=[compile_manifest(executable,listing)])
        assert status(output)['status']=='passed'
        print(json.dumps({'passed':True,'report':str(output),'sha256':digest(output)}),flush=True)
    except BaseException as error:
        transaction.abort(error)
        raise


if __name__=='__main__':main()
