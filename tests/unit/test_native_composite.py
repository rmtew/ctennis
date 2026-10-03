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
  old=b'def measurement_status():\n return 1\ndef static_metrics():\n return 2\n'
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

if __name__=='__main__':unittest.main()
