import hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
import native_composite as c

class CompositeBindingTests(unittest.TestCase):
 def test_only_inactive_function_may_differ(self):
  old='def run_match():\n return 1\ndef main():\n return 2\n'
  new=old.replace('return 1','return 3')
  self.assertEqual(c.source_without_function(old,'run_match'),c.source_without_function(new,'run_match'))
  self.assertNotEqual(c.source_without_function(old,'run_match'),c.source_without_function(new.replace('return 2','return 4'),'run_match'))
 def test_active_restart_observer_must_rerun(self):
  old=b'def run_match():\n return 1\ndef main():\n return 2\n'
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);p=root/'scripts/run_ordinary_round_tests.py';p.parent.mkdir();p.write_bytes(old.replace(b'return 1',b'return 3'))
   with patch.object(c,'ROOT',root),patch.object(c.subprocess,'check_output',return_value=old):
    with self.assertRaisesRegex(ValueError,'must rerun'):c.equivalence(str(p.relative_to(root)),hashlib.sha256(old).hexdigest(),{'commit':c.BASE,'command':['scripts/run_ordinary_round_tests.py','--match','--early-release']})
    proof=c.equivalence(str(p.relative_to(root)),hashlib.sha256(old).hexdigest(),{'commit':c.BASE,'command':['scripts/run_ordinary_round_tests.py','--cadence','--adf']})
    self.assertEqual(proof['excluded_function'],'run_match')
    with self.assertRaisesRegex(ValueError,'immutable Git blob'):c.equivalence(str(p.relative_to(root)),'bad',{'commit':c.BASE,'command':['scripts/run_ordinary_round_tests.py','--cadence']})
 def test_reporter_construction_change_is_rejected(self):
  old=b'def measurement_status():\n return 1\ndef read_case():\n return 1\ndef generate():\n return 1\ndef static_metrics():\n return 2\n'
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);p=root/'scripts/native_metrics.py';p.parent.mkdir();p.write_bytes(old.replace(b'return 2',b'return 3'))
   with patch.object(c,'ROOT',root),patch.object(c.subprocess,'check_output',return_value=old):
    with self.assertRaisesRegex(ValueError,'outside'):c.equivalence(str(p.relative_to(root)),hashlib.sha256(old).hexdigest(),{'commit':c.BASE,'command':['scripts/native_metrics.py']})
 def test_failed_receipt_is_never_reused(self):
  with patch.object(c,'status',return_value={'status':'failed'}):
   self.assertEqual(c.verified_status(Path('/no/receipt'),plan={})['status'],'failed')
 def test_binding_product_policy_receipt_and_unknown_dependencies(self):
  for broken in ('product','policy','receipt','unknown','fixture','changed-during-run'):
   with self.subTest(broken=broken),tempfile.TemporaryDirectory() as d:
    root=Path(d);p=root/'receipt.json';meta={'commit':c.BASE,'command':['scripts/run_native_inputs.py'],'files':{'scripts/unknown.py':'x'},'changed_during_run':['scripts/unknown.py'] if broken=='changed-during-run' else []};p.write_text(json.dumps({'passed':True,'evidence':meta}))
    plan={'base_commit':c.BASE,'policy_sha256':'policy','product':{'exe':'exe'},'receipts':{'receipt.json':{'sha256':'receipt','commit':c.BASE,'command':meta['command']}}}
    hashes={str(p):'receipt',str(root/'exe'):'exe',str(Path(c.__file__)):'policy'}
    if broken in ('product','policy','receipt'):hashes[{'product':str(root/'exe'),'policy':str(Path(c.__file__)),'receipt':str(p)}[broken]]='changed'
    changed=['build/native-fixture'] if broken=='fixture' else ['scripts/unknown.py']
    with patch.object(c,'ROOT',root),patch.object(c,'digest',side_effect=lambda x:hashes.get(str(x))),patch.object(c,'status',return_value={'status':'stale','changed_dependencies':changed}):
     self.assertNotEqual(c.verified_status(p,plan=plan)['status'],'passed')

class CompositeMetricTests(unittest.TestCase):
 def test_composite_rejection_cannot_use_legacy_reporter_fallback(self):
  import native_metrics as m
  with patch.object(m,'status',return_value={'status':'stale','changed_dependencies':['scripts/native_metrics.py']}),patch.object(c,'verified_status',return_value={'status':'stale','reason':'Product or policy mismatch'}),patch.dict(c.os.environ,{c.PLAN_ENV:'bound-plan'}):
   self.assertEqual(m.measurement_status(Path('/unused'))['status'],'stale')
 def test_mixed_old_new_metrics_preserve_raw_and_compare_verified_identity(self):
  import copy,types,native_metrics as m
  old={'scripts/run_ordinary_round_tests.py':b'def run_match():\n return 1\ndef main():\n return 2\n','scripts/run_native_setup_tests.py':b'def run():\n return 1\ndef main():\n return 2\n'}
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);new={p:data.replace(b'return 1',b'return 3') for p,data in old.items()}
   for p,data in new.items():q=root/p;q.parent.mkdir(exist_ok=True);q.write_bytes(data)
   raw_old={p:hashlib.sha256(data).hexdigest() for p,data in old.items()};raw_new={p:hashlib.sha256(data).hexdigest() for p,data in new.items()}
   before={'commit':c.BASE,'command':['scripts/run_ordinary_round_tests.py','--cadence'],'files':raw_old};after={'commit':'new','command':['scripts/run_native_setup_tests.py','--self-test'],'files':raw_new}
   with patch.object(c,'ROOT',root),patch.object(c.subprocess,'check_output',side_effect=lambda args,**kw:old[args[-1].split(':',1)[1]]):
    a=c.normalized_metric_dependencies(before,'cold-one');b=c.normalized_metric_dependencies(after,'setup')
   self.assertNotEqual(a[0],b[0]);self.assertEqual(a[1],b[1]);self.assertEqual(a[2],b[2])
   cases={}
   for name in m.CASES:
    raw,norm,current,proof=a if name!='setup' else b
    cases[name]={'classification':{'status':'passed'},'metrics':{'profiles':{p:{'callbacks':1} for p in m.PROFILES}},'provenance':{'dependencies':raw,'verified_dependencies':norm,'verified_input_fingerprints':current,'dependency_equivalences':proof}}
   static={'release':{'executable_sha256':'release'},'executable_sha256':'exe','features':{'celebration':False},'product_inputs':{}}
   with patch.object(m,'read_case',side_effect=lambda name,*args:copy.deepcopy(cases[name])),patch.object(m,'static_metrics',return_value=static),patch.object(m,'cold_loading_issues',return_value=[]),patch.object(m,'report_identity',return_value='identity'),patch.object(m.subprocess,'run',return_value=types.SimpleNamespace(returncode=0,stdout='{"schema":0}')):
    result=m.generate()
   self.assertEqual(result['state'],'complete');self.assertEqual(result['measurement_inputs'],raw_new)
   self.assertEqual(result['runtime']['cold-one']['provenance']['recorded_dependencies'],raw_old)
   self.assertEqual(result['runtime']['setup']['provenance']['recorded_dependencies'],raw_new)
   self.assertEqual(result['runtime']['cold-one']['provenance']['verified_dependency_identity'],result['runtime']['setup']['provenance']['verified_dependency_identity'])

if __name__=='__main__':unittest.main()
