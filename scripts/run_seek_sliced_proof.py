"""Focused campaign-owned actual CPU navigation proof; no native emulation."""
import hashlib
import json
import os
from build_match_core import build
from build_native_game import build as build_native
from check_shared_core_bytes import normalized
from match_core_cpu import cpu_tool_inputs
from native_evidence import ReportRun,atomic_json,compile_manifest,digest,inputs_for,snapshot,status
from native_tools import ROOT
from seek_sliced_proof import proof

INPUT=ROOT/'build/acceptance/campaigns/e61e095609b8412e95275345f78e9421/attempts/preview-native-pal/000003/actual-prefix-835.json'
INPUT_SHA='c46ef840c63608511f941fdab06b3c3a8586f0dcc79ee039e3532f1138621348'


def input_stream():
    assert digest(INPUT)==INPUT_SHA,'Pinned actual native input prefix changed or unavailable'
    document=json.loads(INPUT.read_text())
    assert document['initialization']['operation']=='game_core_init' and document['initialization']['arguments']==[]
    assert len(document['rows'])==835 and [r['cursor'] for r in document['rows']]==list(range(1,836))
    for name,sha in document['source_files'].items():assert digest(ROOT/name)==sha,('Original native input evidence changed',name)
    return document,[(r['operation'],r['arguments']) for r in document['rows']]


def proof_inputs(document):
    paths,tools=inputs_for('build','scripts/run_seek_sliced_proof.py')
    paths|={INPUT}|{ROOT/p for p in document['source_files']}
    cpu_paths,machine=cpu_tool_inputs();paths|=cpu_paths
    tools=dict(tools,machine68k=machine)
    return paths,tools


def run():
    path=ROOT/'build/tests/seek-sliced-cpu/report.json'
    transaction=ReportRun([path],'seek-sliced-cpu','maintained-native','bounded actual CPU paused navigation')
    try:
        document,stream=input_stream()
        paths,tools=proof_inputs(document)
        transaction.meta.update(files=snapshot(paths),tools=tools,
            target_role='legacy-validator-reference',actual_execution='actual-68000-cpu-only',
            target_scope='evidence.target is a compatibility reference; no actual native display execution.')
        transaction.meta['environment']['PYTHONPATH']=os.environ.get('PYTHONPATH')
        standalone,listing=build();_,native=build_native()
        left,relocations,branches=normalized(standalone,listing)
        assert normalized(native,native.parent/'native.lst')==(left,relocations,branches)
        audit=dict(matched=True,bytes=len(left),relocations=relocations,sink_branches=branches,sha256=hashlib.sha256(left).hexdigest())
        assert audit==dict(matched=True,bytes=17524,relocations=7,sink_branches=14,sha256='951935ce4ec1538f5ff2fa83898c36af7a75de60f4c0fe025e74181543f1544c')
        validation=dict(passed=False,schema=1,canonical_bytes=318,history_metadata_bytes=72,seek_storage_bytes=734,
            normalized_shared_core=audit,input_stream=dict(path=str(INPUT.relative_to(ROOT)),sha256=INPUT_SHA,
                operations=835,target_probe=569,source_files=document['source_files']),proofs={})
        for role,executable,base,is_native in (('standalone',standalone,0x10000,False),
                ('relocated',standalone,0x30000,False),('native',native,0x10000,True)):
            print('Actual sliced seek proof',role,flush=True)
            validation['proofs'][role]=proof(executable,stream,base,is_native,role)
            atomic_json(path.parent/'proof-progress-unvalidated.json',dict(seek_sliced_validation=validation,receipt_validated=False))
        semantic=lambda p:[(r['operation'],r['arguments'],r['working_state'],r['events']) for r in p['rows']]
        assert semantic(validation['proofs']['standalone'])==semantic(validation['proofs']['relocated'])==semantic(validation['proofs']['native'])
        validation['passed']=True
        report=dict(passed=True,executable_sha256=digest(standalone),execution='actual-68000-cpu-only',seek_sliced_validation=validation,
            scope='Fresh bounded seek/preview ownership and complete actual boundaries at checkpoint512 through569; no real IRQ/input native deadline or whole release gate claim.')
        unvalidated=path.parent/'report-unvalidated.json'
        atomic_json(unvalidated,dict(report,receipt_validated=False))
        transaction.finalize(path,report,compiled=[compile_manifest(standalone,listing),compile_manifest(native,native.parent/'native.lst')],
            artifacts=[path.parent/'proof-progress-unvalidated.json',unvalidated])
        assert status(path)['status']=='passed',status(path)
        print(json.dumps(dict(passed=True,report=str(path),proofs=list(validation['proofs']))),flush=True)
    except BaseException as error:
        transaction.abort(error);raise


if __name__=='__main__':run()
