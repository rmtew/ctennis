"""CPU-only cooperative helper proof; consumes existing builds, never builds."""
import argparse
import json
import os
from pathlib import Path
from uuid import uuid4

from cooperative_endpoint_proof import run, OLD_SHA
from match_core_cpu import cpu_tool_inputs
from native_evidence import (ReportRun,atomic_json,compile_manifest,digest,
    inputs_for,snapshot,status)
from native_tools import ROOT


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--informal',action='store_true')
    parser.add_argument('--executable',type=Path,default=ROOT/'build/standalone/match-core')
    parser.add_argument('--reference',type=Path,default=ROOT/'build/tests/coherent-frozen-helper-b08b/match-core')
    args=parser.parse_args();new=args.executable.resolve();old=args.reference.resolve()
    output=ROOT/'build/tests/cooperative-endpoint-cpu/report.json'
    if args.informal:
        raw=output.parent/('informal-'+uuid4().hex)
        try:
            validation=run(new,old,raw)
            atomic_json(raw/'results-unvalidated.json',dict(validation,receipt_validated=False,
                candidate_sha256=digest(new),reference_sha256=digest(old)))
        except BaseException as error:
            atomic_json(raw/'failure-unvalidated.json',dict(passed=False,error=repr(error),
                candidate_sha256=digest(new),reference_sha256=digest(old)))
            raise
        print(json.dumps(dict(passed=True,informal=True,raw=str(raw))),flush=True)
        return
    transaction=ReportRun([output],'cooperative-endpoint-cpu','maintained-native','actual 68000 CPU only')
    try:
        assert digest(old)==OLD_SHA
        paths,tools=inputs_for('build','scripts/run_cooperative_endpoint_proof.py')
        cpu_paths,tools['machine68k']=cpu_tool_inputs()
        transaction.meta.update(files=snapshot(paths|cpu_paths|{old,old.parent/'match-core.lst'}),tools=tools,
            reference_executable_sha256=OLD_SHA,
            reference_binding='Frozen old executable and listing, not current helper source or new synchronous entry')
        transaction.meta['environment']['PYTHONPATH']=os.environ.get('PYTHONPATH')
        manifest=compile_manifest(new,new.parent/'match-core.lst')
        raw=output.parent/('raw-'+transaction.meta['run_id'])
        validation=run(new,old,raw)
        unvalidated=raw/'results-unvalidated.json';atomic_json(unvalidated,validation)
        transaction.finalize(output,dict(passed=True,execution='actual-68000-cpu-only',
            executable_sha256=digest(new),reference_executable_sha256=OLD_SHA,
            validation=validation),[manifest],list(raw.glob('*')))
        assert status(output)['status']=='passed',status(output)
        print(json.dumps(dict(passed=True,report=str(output),sha256=digest(output))),flush=True)
    except BaseException as error:
        transaction.abort(error)
        archive=output.parent/('failed-'+transaction.meta['run_id']+'.json')
        archive.write_bytes(output.read_bytes())
        raise


if __name__=='__main__':main()
