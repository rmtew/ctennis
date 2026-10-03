"""Verify this native gate's preserved receipts; never edit the originals.

Two narrowly reviewed observer/reporting equivalences are supported. All other
file/tool/config/fixture/raw-artifact changes retain native_evidence's strict
invalidation. This is a composite evidence verifier, not a general cache.
"""
import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from native_tools import ROOT
from native_evidence import digest,status

BASE='2219fd63509dd2e9c2851a08a3a169d25cb0bb42'
PLAN_ENV='CTENNIS_ACCEPTANCE_COMPOSITE'


def source_without_function(source,name):
    tree=ast.parse(source)
    removed=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name]
    if len(removed)!=1:raise ValueError(f'Expected exactly one {name} function')
    tree.body=[n for n in tree.body if n not in removed]
    return ast.dump(tree,include_attributes=False)


def equivalence(path,expected,meta):
    if path not in ('scripts/run_ordinary_round_tests.py','scripts/native_metrics.py'):
        raise ValueError(f'No reviewed equivalence for {path}')
    old=subprocess.check_output(['git','show',f"{meta['commit']}:{path}"],cwd=ROOT)
    if hashlib.sha256(old).hexdigest()!=expected:raise ValueError('Recorded source differs from its immutable Git blob')
    current=(ROOT/path).read_bytes()
    name='run_match' if path.endswith('run_ordinary_round_tests.py') else 'measurement_status'
    if path.endswith('run_ordinary_round_tests.py'):
        command=meta['command']
        if Path(command[0]).name=='run_ordinary_round_tests.py' and not any(a in command for a in ('--cadence','--bank-control')):
            raise ValueError('Active restart observer changed: it must rerun')
    old_ast=source_without_function(old.decode(),name)
    new_ast=source_without_function(current.decode(),name)
    if old_ast!=new_ast:raise ValueError(f'Changes outside the reviewed inactive/reporting function: {path}')
    return {'path':path,'recorded_sha256':expected,'current_sha256':hashlib.sha256(current).hexdigest(),
            'unchanged_ast_sha256':hashlib.sha256(old_ast.encode()).hexdigest(),'excluded_function':name,
            'reason':'Restart-only function is inactive for this preserved stage' if name=='run_match' else 'Measurement classification only; product construction and observation unchanged'}


def verified_status(path,*,subject='maintained-native',interface_flavor='enhanced',plan=None):
    path=Path(path)
    initial=status(path,subject=subject,interface_flavor=interface_flavor)
    if initial['status']=='passed':return initial
    differences=initial.get('changed_dependencies',[])
    if initial['status']!='stale' or not differences:return initial
    if plan is None:
        value=os.environ.get(PLAN_ENV)
        if not value:return initial
        plan=json.loads(Path(value).read_text())
    key=str(path.relative_to(ROOT))
    if plan.get('base_commit')!=BASE or plan.get('policy_sha256')!=digest(Path(__file__)):
        return dict(initial,reason='Composite base or verifier identity changed')
    if any(digest(ROOT/name)!=sha for name,sha in plan.get('product',{}).items()) or not plan.get('product'):
        return dict(initial,reason='Composite product binding changed or absent')
    binding=plan.get('receipts',{}).get(key)
    if not binding or binding['sha256']!=digest(path):
        return dict(initial,reason='Receipt absent from composite plan or changed since binding')
    report=json.loads(path.read_text());meta=report['evidence']
    if meta.get('changed_during_run'):
        return dict(initial,reason='Inputs changed during the historical invocation')
    if meta.get('commit')!=binding['commit'] or meta.get('command')!=binding['command']:
        return dict(initial,reason='Composite command/head binding differs')
    proofs=[]
    adjusted=copy.deepcopy(report)
    try:
        for name in sorted(set(differences)):
            if name not in meta['files']:raise ValueError('Changed compiled artifact or unrecorded dependency')
            proof=equivalence(name,meta['files'][name],meta)
            proofs.append(proof)
            adjusted['evidence']['files'][name]=proof['current_sha256']
        # Re-run the original strict validator on an ephemeral copy only after
        # proving each allowed source difference. No historical receipt changes.
        with tempfile.TemporaryDirectory(prefix='ctennis-composite-') as temporary:
            check=Path(temporary)/'receipt.json';check.write_text(json.dumps(adjusted))
            result=status(check,subject=subject,interface_flavor=interface_flavor)
        if result['status']!='passed':return dict(result,dependency_equivalences=proofs)
        return dict(result,freshness='reused_verified',original_receipt_sha256=binding['sha256'],dependency_equivalences=proofs)
    except (KeyError,ValueError,subprocess.CalledProcessError) as error:
        return dict(initial,reason=str(error))
