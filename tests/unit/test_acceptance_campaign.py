import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
import acceptance_campaign as campaign
from acceptance_cases import Case,cases
from native_evidence import atomic_json,digest

class CampaignTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.directory=self.root/'campaign';self.directory.mkdir()
        self.case=Case('fake',('child.py',),category='host')
        atomic_json(self.directory/'campaign.json',{'id':'fake-'+self.root.name})
        self.deps={'command':['child.py'],'files':{}}
        self.stub=patch.object(campaign,'dependencies',return_value=self.deps);self.stub.start()
    def tearDown(self):
        self.stub.stop();self.temp.cleanup()
        os.environ.pop('CTENNIS_CAMPAIGN_ID',None)
    def child(self,text):
        (self.root/'child.py').write_text(text)
    def run_worker(self):
        with patch.object(campaign,'tagged_processes',return_value=[]):
            return campaign.worker(self.directory,[self.case],self.root)
    def test_catalog_stable_complete(self):
        self.assertEqual(len(cases()),41)
        self.assertIn('takeover-tail',{c.id for c in cases()})
        self.assertIn('takeover-sound',{c.id for c in cases()})
    def test_identity_start_not_pid_only(self):
        identity=campaign.process_identity();self.assertTrue(campaign.alive(identity))
        identity=dict(identity,start='wrong');self.assertFalse(campaign.alive(identity))
    def test_exclusive_shared_symlink_lock(self):
        target=self.root/'outputs';alias=self.root/'alias';target.mkdir();alias.symlink_to(target)
        lock=campaign.WorkspaceLock(target)
        try:
            with self.assertRaises(RuntimeError):campaign.WorkspaceLock(alias)
        finally:lock.close()
        campaign.WorkspaceLock(alias).close()
    def test_success_resume_does_not_repeat_child(self):
        self.child("from pathlib import Path\np=Path('count');p.write_text(str(int(p.read_text())+1) if p.exists() else '1')\n")
        self.assertEqual(self.run_worker(),0)
        # A finished controller's identity remains durable; simulate reconnect
        # after it actually ended, rather than claiming the current test died.
        atomic_json(self.directory/'owner.json',{'controller':dict(campaign.process_identity(),start='old')})
        self.assertEqual(self.run_worker(),0)
        self.assertEqual((self.root/'count').read_text(),'1')
        attempts=sorted((self.directory/'attempts/fake').iterdir());self.assertEqual(len(attempts),2)
        self.assertEqual(json.loads((attempts[1]/'completion.json').read_text())['action'],'reuse')
    def test_latest_failure_hides_old_success(self):
        base=self.directory/'attempts/fake';(base/'000001').mkdir(parents=True)
        atomic_json(base/'000001/completion.json',{'state':'complete','exit_code':0,'dependency_key':campaign.canonical(self.deps),'artifacts':{}})
        (base/'000002').mkdir();atomic_json(base/'000002/completion.json',{'state':'failed','exit_code':1})
        self.assertEqual(campaign.plan([self.case],self.directory,self.root)[0]['action'],'run')
    def test_interrupted_attempt_hides_old_success(self):
        base=self.directory/'attempts/fake';(base/'000001').mkdir(parents=True)
        atomic_json(base/'000001/completion.json',{'state':'complete','exit_code':0,'dependency_key':campaign.canonical(self.deps),'artifacts':{}})
        (base/'000002').mkdir();atomic_json(base/'000002/started.json',{'state':'incomplete'})
        self.assertEqual(campaign.plan([self.case],self.directory,self.root)[0]['action'],'run')
    def test_dependency_invalidation(self):
        self.child('pass\n');self.assertEqual(self.run_worker(),0)
        self.deps['command'].append('--new')
        self.assertEqual(campaign.plan([self.case],self.directory,self.root)[0]['action'],'run')
    def test_artifact_corruption(self):
        self.child("print('original')\n");self.run_worker()
        (self.directory/'attempts/fake/000001/child.log').write_text('tampered')
        self.assertEqual(campaign.plan([self.case],self.directory,self.root)[0]['action'],'run')
    def test_failure_atomic_completion(self):
        self.child('raise SystemExit(7)\n');self.assertEqual(self.run_worker(),7)
        receipt=json.loads((self.directory/'attempts/fake/000001/completion.json').read_text())
        self.assertEqual(receipt['state'],'failed');self.assertEqual(receipt['exit_code'],7)
        self.assertIn(str(self.directory/'attempts/fake/000001/child.log'),receipt['artifacts'])
    def test_live_controller_not_reclaimed(self):
        atomic_json(self.directory/'owner.json',{'controller':campaign.process_identity()})
        with self.assertRaisesRegex(RuntimeError,'already running'):self.run_worker()
    def test_live_descendant_not_reclaimed(self):
        with patch.object(campaign,'tagged_processes',return_value=[{'pid':123}]):
            with self.assertRaisesRegex(RuntimeError,'descendants'):campaign.worker(self.directory,[self.case],self.root)
    def test_other_host_not_reclaimed(self):
        atomic_json(self.directory/'owner.json',{'controller':{'host':'other','pid':999999,'start':'1'}})
        with self.assertRaisesRegex(RuntimeError,'another host'):self.run_worker()
    def test_latest_native_failure_rejects_saved_pass(self):
        native=Case('native',('check.py',),'tests/receipt.json')
        attempt={'state':'complete','exit_code':0,'dependency_key':campaign.canonical(self.deps),'artifacts':{},'receipt':{'sha256':'old'}}
        with patch.object(campaign,'compatible_receipt',return_value=(None,'latest failed')):
            self.assertFalse(campaign.attempt_valid(attempt,native,self.deps,self.root))
    def test_detached_child_keeps_exclusive_lock_after_controller_dies(self):
        self.child("from pathlib import Path\nimport time\nPath('child-started').write_text('yes')\nwhile not Path('release').exists():time.sleep(.02)\nPath('child-finished').write_text('yes')\n")
        scripts=Path(campaign.__file__).parent
        code=(f"import sys;sys.path.insert(0,{str(scripts)!r});import acceptance_campaign as c;"
              f"from acceptance_cases import Case;c.dependencies=lambda *a: {self.deps!r};"
              f"c.worker({str(self.directory)!r},[Case('fake',('child.py',),category='host')],{str(self.root)!r})")
        with (self.root/'controller.log').open('wb') as log:
            controller=subprocess.Popen([sys.executable,'-c',code],stdout=log,stderr=log,start_new_session=True)
            try:
                deadline=time.monotonic()+5
                while not (self.root/'child-started').exists() and time.monotonic()<deadline:time.sleep(.02)
                self.assertTrue((self.root/'child-started').exists())
                controller.terminate();controller.wait(timeout=3)
                with self.assertRaises(RuntimeError):campaign.WorkspaceLock(self.root/'build')
                self.assertFalse((self.directory/'attempts/fake/000001/completion.json').exists())
                (self.root/'release').touch()
                deadline=time.monotonic()+5
                while not (self.root/'child-finished').exists() and time.monotonic()<deadline:time.sleep(.02)
                self.assertTrue((self.root/'child-finished').exists())
                self.assertEqual(campaign.plan([self.case],self.directory,self.root)[0]['action'],'run')
            finally:
                (self.root/'release').touch()
                if controller.poll() is None:controller.terminate();controller.wait(timeout=3)
    def test_known_startup_extent_rejects_partial(self):
        self.assertFalse(campaign.required_extent(Case('startup',()),{'passed':True,'cases':[]}))
    def test_tail_extent_requires_actual_confirmation(self):
        case=Case('takeover-sound',())
        report=dict(passed=True,takeover=True,takeover_tail=True,takeover_round_sound=True,
                    takeover_confirmation_lifecycle=5,verified_input_ticks=1608,missed_publications=0,entropy_request_observed=False)
        self.assertTrue(campaign.required_extent(case,report))
        report['takeover_confirmation_lifecycle']=4;self.assertFalse(campaign.required_extent(case,report))
    def test_selected_resume_forwards_saved_selection_to_worker(self):
        atomic_json(self.directory/'campaign.json',{'id':self.directory.name,'case_ids':['fake'],
                    'resolved_build':str((self.root/'build').resolve())})
        target=self.root/'build/acceptance/campaigns'/self.directory.name
        target.parent.mkdir(parents=True);self.directory.rename(target)
        with patch.object(campaign,'ROOT',self.root),patch.object(campaign,'cases',return_value=[self.case,Case('other',('other.py',))]),\
             patch('campaign_core_evidence.core_cases',return_value=[]),patch.object(sys,'argv',['campaign','--resume','--campaign',target.name]),\
             patch.object(campaign.subprocess,'Popen') as launch:
            launch.return_value.pid=os.getpid()
            self.assertEqual(campaign.main(),0)
            command=launch.call_args.args[0]
            self.assertEqual(command[command.index('--case')+1],'fake')
            self.assertNotIn('other',command)
    def test_immutable_artifact_survives_canonical_overwrite(self):
        artifact=self.root/'build/tests/old.log';artifact.parent.mkdir(parents=True);artifact.write_text('original')
        with patch.object(campaign,'ROOT',self.root):
            preserved=campaign.preserve_artifacts({str(artifact):digest(artifact)},self.directory)
        artifact.write_text('overwritten')
        self.assertEqual(len(preserved),1)
        for path,sha in preserved.items():self.assertEqual(digest(path),sha)
    def test_environment_is_dependency(self):
        base={'files':{},'environment':{'PYTHONPATH':'old'}}
        changed={'files':{},'environment':{'PYTHONPATH':'new'}}
        self.assertNotEqual(campaign.canonical(base),campaign.canonical(changed))
    def test_monitor_never_accepts_old_green_when_new_controller_failed(self):
        atomic_json(self.directory/'report.json',{'state':'complete','passed':True})
        from unittest.mock import Mock
        child=Mock();child.poll.return_value=1;child.returncode=1
        self.assertEqual(campaign.monitor(self.directory,child),1)
    def test_different_campaign_cannot_bypass_orphan_emulator(self):
        owner=dict(campaign.process_identity(),start='old')
        atomic_json(self.root/'build/acceptance-active.json',{'campaign':'different-old-campaign','controller':owner})
        with patch.object(campaign,'tagged_processes',return_value=[{'pid':123}]) as scan:
            with self.assertRaisesRegex(RuntimeError,'live descendants'):campaign.require_idle_workspace(self.root)
            self.assertEqual(scan.call_args.args[0],'different-old-campaign')
    def test_different_host_workspace_owner_is_ambiguous(self):
        atomic_json(self.root/'build/acceptance-active.json',{'campaign':'old','controller':{'host':'other'}})
        with self.assertRaisesRegex(RuntimeError,'another host'):campaign.require_idle_workspace(self.root)
    def test_exiting_process_permission_race_is_not_live_owner(self):
        from unittest.mock import Mock
        owner=dict(campaign.process_identity(),start='1',group=-1)
        item=Mock();item.name='999999'
        item.__truediv__=Mock(return_value=Mock())
        (item/'environ').read_bytes.side_effect=PermissionError('exiting')
        identity=dict(owner,pid=999999,start='2',group=-2)
        with patch.object(campaign.Path,'iterdir',return_value=[item]),\
             patch.object(campaign,'process_identity',side_effect=[owner,identity,None]):
            self.assertEqual(campaign.tagged_processes('old',owner),[])
    def test_live_same_user_permission_denial_still_blocks(self):
        from unittest.mock import Mock
        owner=dict(campaign.process_identity(),start='1',group=-1)
        item=Mock();item.name='999999'
        item.__truediv__=Mock(return_value=Mock())
        (item/'environ').read_bytes.side_effect=PermissionError('live')
        item.stat.return_value.st_uid=os.getuid()
        identity=dict(owner,pid=999999,start='2',group=-2)
        with patch.object(campaign.Path,'iterdir',return_value=[item]),\
             patch.object(campaign,'process_identity',side_effect=[owner,identity,identity]):
            with self.assertRaisesRegex(RuntimeError,'Cannot verify'):
                campaign.tagged_processes('old',owner)

if __name__=='__main__':unittest.main()
