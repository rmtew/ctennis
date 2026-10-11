"""Manifest-bound CPU-only coherent scheduler proof; never builds or boots."""
import argparse
import json
import os

from coherent_scheduler_proof import run
from match_core_cpu import cpu_tool_inputs
from native_evidence import (ReportRun,atomic_json,compile_manifest,digest,
                             inputs_for,snapshot,status)
from native_tools import ROOT


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--executable',type=str,default=str(ROOT/'build/standalone/match-core'))
    parser.add_argument('--informal',action='store_true',help='Diagnostic execution during source development; no formal receipt')
    args=parser.parse_args()
    from pathlib import Path
    executable=Path(args.executable).resolve()
    if args.informal:
        from uuid import uuid4
        raw=ROOT/'build/tests/coherent-scheduler-cpu'/('informal-'+uuid4().hex)
        validation=run(executable,raw)
        atomic_json(raw/'summary.json',dict(validation,receipt_validated=False))
        print(json.dumps(dict(passed=True,informal=True,raw=str(raw))),flush=True)
        return
    listing=executable.parent/'match-core.lst'
    output=ROOT/'build/tests/coherent-scheduler-cpu/report.json'
    transaction=ReportRun([output],'coherent-scheduler-cpu','maintained-native','actual 68000 CPU only')
    try:
        paths,tools=inputs_for('build','scripts/run_coherent_scheduler_proof.py')
        cpu_paths,tools['machine68k']=cpu_tool_inputs()
        transaction.meta.update(files=snapshot(paths|cpu_paths),tools=tools,
            runner='scripts/run_coherent_scheduler_proof.py',actual_execution='actual-68000-cpu-only')
        transaction.meta['environment']['PYTHONPATH']=os.environ.get('PYTHONPATH')
        manifest=compile_manifest(executable,listing)
        raw=output.parent/('raw-'+transaction.meta['run_id'])
        validation=run(executable,raw)
        unvalidated=output.parent/('results-'+transaction.meta['run_id']+'-unvalidated.json')
        atomic_json(unvalidated,validation)
        transaction.finalize(output,dict(passed=True,execution='actual-68000-cpu-only',
            executable_sha256=digest(executable),validation=validation),[manifest],
            list(raw.glob('*.json.gz'))+[unvalidated])
        assert status(output)['status']=='passed',status(output)
        print(json.dumps(dict(passed=True,report=str(output),sha256=digest(output))),flush=True)
    except BaseException as error:
        transaction.abort(error)
        raise


if __name__=='__main__':
    main()
