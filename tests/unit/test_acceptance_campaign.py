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

def preview_a1_report():
    costs=dict(generation=1,edited_only_position_changed=True,cache_hit=False,resolver_operations=1,
               request_cpu_cycles=1,total_worker_cpu_cycles=1,maximum_worker_cpu_cycles=1,
               maximum_worker_operations=4,worker_calls=1,stack_bytes=204)
    def accepted():
        return dict(passed=True,continuous_state_path_output_equal=True,independent_continuation_policy_equal=True,
                    edited_only_position_changed=True,live_history_output_preserved=True,costs=dict(costs),end=0,
                    classes=['landing','landing'],path_counts=[1,1],actual_accepted_launches={'0':[],'1':[]},
                    actual_final_boundaries=[dict(contact=0,flight=0,lifecycle=1)]*2)
    fallback=accepted();fallback.update(human=True,legal_position_verified=True,released_no_launch=True,
        lifecycle=1,phase=64,released_outgoing_path_claimed=False,classes=['landing','limit'],path_counts=[1,256],
        timed_prelaunch=dict(passed=True,phase=32,complete_boundary_clocks=[15,16],launch_entry_clock=16,
            actual_launch_absent_before_requests=True,held_actual_launch_after_requests=True,
            cases=[accepted(),accepted()]),
        postlaunch_rejection=dict(passed=True,lifecycle=1,phase=32,serve_clock=17,operations=1,
            actual_human_launch_observed=True,legal_position_verified=True,request_rejected=True,
            full_live_history_output_preview_preserved=True,launch_entry_clock=16,first_postlaunch_boundary_clock=17))
    miss=accepted();miss.update(classes=['no-contact','no-contact'],no_contact_outgoing_path_claimed=False)
    def replacement(phase):
        return dict(passed=True,phase=phase,retired_generation=1,new_generation=2,cold_restart=True,
            old_and_partial_results_unavailable=True,full_live_history_output_preserved=True,partial_prefix_samples=0,
            request_cpu_cycles=1,replacement_cpu_cycles=1,maximum_worker_cpu_cycles=1,worker_calls=1,maximum_stack_bytes=204)
    lifecycle=[]
    for _ in range(3):
        row=accepted();row.update(classes=['lifecycle','lifecycle'],path_counts=[0,0],actual_final_boundaries=[None,None]);lifecycle.append(row)
    rows={'human-serve-fallback':fallback,'no-contact':miss,
          'title-dual-rejection':dict(passed=True,lifecycle=2,stale_phase=64,fallback_rejected=True,
              historical_rejected=True,full_live_history_output_preview_preserved=True),
          'limit-256':dict(passed=True,samples=256,total_sample_limit=256,no_actual_human_launch=True,
              outgoing_path_claimed=False,incomplete=True,full_live_history_output_preserved=True,
              continuous_state_path_output_equal=True,independent_continuation_policy_equal=True),
          'replacement-resolve':replacement(1),'replacement-held':replacement(3),
          'non-dispatch-lifecycle':dict(passed=True,clear_latch_result_order_preserved=True,reset_not_executed=True,
              reset_operations=['game_core_init','game_core_select','game_core_return_title'],cases=lifecycle),
          'truncated-completed-context':dict(passed=True,request_accepted=True,context_missing=True,result_rejected=True,
              unavailable_scratch_preserved=True,full_live_history_output_preserved=True,cache_valid=False,
              completed_kind=2,incoming_origin=1,oldest=64,probe_origin=65,dispatches=1,operations=129,
              non_tick_calls_between_launch_and_probe=128,costs=dict(costs,edited_only_position_changed=False))}
    return dict(passed=True,canonical_bytes=318,history_metadata_bytes=72,total_samples_per_path=256,
                maximum_worker_operations=4,other_stages_pending=['A2-endpoint-discovery','A3-relocation-native-history'],cases=rows)

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
        self.assertEqual(len(cases()),45)
        self.assertIn('takeover-tail',{c.id for c in cases()})
        self.assertIn('takeover-sound',{c.id for c in cases()})
    def test_preview_extent_requires_isolation_budget_and_continuous_replay(self):
        case=next(c for c in cases() if c.id=='preview-cpu')
        names=('completed-serve','return-after-pads','return-before-dispatch')
        row=dict(passed=True,continuous_state_path_output_equal=True,live_history_output_preserved=True,
                 independent_continuation_policy_equal=True,first_dispatch_controls={'0':16,'1':0},
                 worker_calls=4,maximum_worker_operations=4,preservation_checks=4,worker_restorations=4,
                 path_counts=[2,256],negative_controls=['stale-step','stale-cancel','stale-request',
                     'zero-budget','excess-budget','unpublished-result','changed-selection-result','ai-serve-fallback'],
                 request_cpu_cycles=1,total_worker_cpu_cycles=4,maximum_worker_cpu_cycles=1,
                 repeat_request_cpu_cycles=1,resolver_operations=1,resolver_worker_calls=1,
                 resolver_inclusive_cpu_cycles=1,repeat_resolver_operations=1,
                 repeat_resolver_worker_calls=1,repeat_resolver_cpu_cycles=1)
        report=dict(passed=True,execution='actual-68000-cpu-only',
                    evidence=dict(target_role='legacy-validator-reference',actual_execution='actual-68000-cpu-only'),
                    preview_validation=dict(passed=True,preview_storage_bytes=5550,metadata_bytes=110,
                        ai_serve_setup_fixture=dict(passed=True,ai=True,frozen=True,legal_position_verified=True,
                            rejection_scope='ai-serving-context',ai_guard_isolated=False,human_phase=0,
                            operations=4,end=1,phase=128,legal_x=8,legal_y=8),
                        fixture_operations=2049,cases=[dict(row,name=name) for name in names]))
        job=dict(generation=1,resolver_operations=1,request_cpu_cycles=1,total_worker_cpu_cycles=1,
                 maximum_worker_cpu_cycles=1,maximum_worker_operations=4,worker_calls=1,stack_bytes=256)
        failed=dict(passed=True,all_72_metadata_preserved=True,canonical_preserved=True,
                    history_bytes_preserved=True,cache_generation_status_preserved=True,
                    ready_result_preserved=True,failed_seek_cpu_cycles=1)
        cache=dict(passed=True,maximum_stack_bytes=256,
                   cold_warm=dict(passed=True,state_path_output_equal=True,prefix_equal=True,
                       live_history_output_preserved=True,original=dict(job,cache_hit=False),
                       cold=dict(job,cache_hit=False),warm=dict(job,cache_hit=True,resolver_operations=0)),
                   failed_seek_controls=[dict(failed,name=name) for name in
                       ('corrupt-checkpoint-schema','corrupt-checkpoint-simulation','corrupt-checkpoint-state',
                        'corrupt-operation-id','out-of-range-high')],
                   invalidation=dict(passed=True,generation_exhausted=True,
                       negative_controls=['seek-back-ready','failed-seek-preserves','different-attempt',
                           'cancel','eviction','exhaustion','stale-generation'],
                       after_cancel_resolver_operations=1,different_attempt_resolver_operations=1,
                       oldest_after_eviction=64,evicted_incoming_origin=1))
        report['preview_validation']['cache_validation']=cache
        report['preview_validation']['stage_a1_validation']=preview_a1_report()
        self.assertTrue(campaign.required_extent(case,report))
        for area,key,value in (('cold_warm','state_path_output_equal',False),
                               ('invalidation','generation_exhausted',False),
                               ('invalidation','oldest_after_eviction',1)):
            partial=json.loads(json.dumps(report));partial['preview_validation']['cache_validation'][area][key]=value
            with self.subTest(cache=(area,key)):self.assertFalse(campaign.required_extent(case,partial))
        partial=json.loads(json.dumps(report));partial['preview_validation']['cache_validation']['cold_warm']['warm']['resolver_operations']=1
        self.assertFalse(campaign.required_extent(case,partial))
        partial=json.loads(json.dumps(report));partial['preview_validation']['cache_validation']['failed_seek_controls'][0]['all_72_metadata_preserved']=False
        self.assertFalse(campaign.required_extent(case,partial))
        for key,value in (('passed',False),('ai',False),('frozen',False),('legal_position_verified',False),
                          ('operations',0),('end',2),('phase',31),('legal_x',256),('human_phase',128),
                          ('ai_guard_isolated',True),('rejection_scope','ai-flag-alone')):
            partial=json.loads(json.dumps(report));partial['preview_validation']['ai_serve_setup_fixture'][key]=value
            with self.subTest(fallback=key):self.assertFalse(campaign.required_extent(case,partial))
        for key,value in (('continuous_state_path_output_equal',False),('live_history_output_preserved',False),
                          ('independent_continuation_policy_equal',False),
                          ('maximum_worker_operations',5),('worker_restorations',3),('preservation_checks',3),
                          ('path_counts',[0,256]),('negative_controls',[]),('repeat_resolver_cpu_cycles',None)):
            partial=json.loads(json.dumps(report));partial['preview_validation']['cases'][0][key]=value
            with self.subTest(key=key):self.assertFalse(campaign.required_extent(case,partial))
        for controls in ({},{'0':0,'1':0},{'0':16,'1':16},{'0':17,'1':0},{'0':True,'1':0}):
            partial=json.loads(json.dumps(report));partial['preview_validation']['cases'][1]['first_dispatch_controls']=controls
            with self.subTest(controls=controls):self.assertFalse(campaign.required_extent(case,partial))
        for key,value in (('cases',[]),('preview_storage_bytes',6000),('metadata_bytes',100),('fixture_operations',2048)):
            partial=json.loads(json.dumps(report));partial['preview_validation'][key]=value
            with self.subTest(key=key):self.assertFalse(campaign.required_extent(case,partial))
    def test_preview_a1_extent_requires_boundaries_and_honest_unavailability(self):
        report=preview_a1_report();self.assertTrue(campaign.preview_a1_extent(report))
        changes=[('title-dual-rejection','lifecycle',1),('limit-256','samples',255),
                 ('limit-256','outgoing_path_claimed',True),('replacement-held','phase',1),
                 ('replacement-resolve','new_generation',1),('truncated-completed-context','completed_kind',0),
                 ('truncated-completed-context','incoming_origin',64),('truncated-completed-context','cache_valid',True),
                 ('non-dispatch-lifecycle','reset_not_executed',False)]
        for name,key,value in changes:
            partial=json.loads(json.dumps(report));partial['cases'][name][key]=value
            with self.subTest(case=name,key=key):self.assertFalse(campaign.preview_a1_extent(partial))
        partial=json.loads(json.dumps(report));partial['cases']['human-serve-fallback']['postlaunch_rejection']['serve_clock']=16
        self.assertFalse(campaign.preview_a1_extent(partial))
        partial=json.loads(json.dumps(report));partial['cases']['human-serve-fallback']['timed_prelaunch']['complete_boundary_clocks']=[15,17]
        self.assertFalse(campaign.preview_a1_extent(partial))
    def test_history_extent_requires_native_recorder_and_every_boundary(self):
        case=next(c for c in cases() if c.id=='history-pal')
        report={'passed':True,'history':True,'seconds':24,
                'target':dict(video='PAL',cpu='68000',chipset='OCS',chip_kib=512,slow_kib=0,fast_kib=0),
                'evidence':{'target_role':'legacy-validator-reference',
                            'actual_target':dict(video='PAL',cpu='68000',chipset='OCS',chip_kib=512,slow_kib=0,fast_kib=0)},
                'rows':[{}],'summary':{'operations':1},
                'native_video':dict(presentation_last_line=311,simulation_interval_whole=11838,
                                   simulation_interval_fraction=14906),
                'history_validation':{'passed':True,'native_buffer_equal':True,'retained_operations':4040,
                                      'native_attempts':[[65,2,0]],
                                      'seek':{'operations':5000,'oldest':960,'buffer_bytes':80318,'frozen_operations_checked':9,'terminal_outcome_operations':1,
                                              'register_sr_equivalence_operations':5000,'failure_preserves_older_position':True,
                                              'retained_operations':4040,'boundaries_checked':4041,
                                              'seeks':8082,'negative_controls':['checkpoint-byte-8','checkpoint-byte-10',
                                                  'checkpoint-byte-326','checkpoint-byte-104','out-of-range-1','out-of-range-65']}}}
        self.assertTrue(campaign.required_extent(case,report))
        for path,value in ((('history',),False),(('seconds',),23),(('target','video'),'NTSC'),
                           (('history_validation','native_buffer_equal'),False),
                           (('history_validation','seek','boundaries_checked'),4040),
                           (('history_validation','seek','seeks'),8081),
                           (('history_validation','seek','negative_controls'),[]),
                           (('history_validation','seek','terminal_outcome_operations'),0),
                           (('history_validation','seek','operations'),4096),
                           (('history_validation','seek','oldest'),0),
                           (('history_validation','seek','buffer_bytes'),21470),
                           (('history_validation','native_attempts'),[[65,0,0]]),
                           (('evidence','target_role'),'execution-target'),(('evidence','actual_target'),{}),
                           (('native_video','presentation_last_line'),261),
                           (('native_video','simulation_interval_whole'),11947),
                           (('native_video','simulation_interval_fraction'),13180)):
            partial=json.loads(json.dumps(report));node=partial
            for key in path[:-1]:node=node[key]
            node[path[-1]]=value
            with self.subTest(path=path):self.assertFalse(campaign.required_extent(case,partial))
    def test_history_cpu_extent_requires_wrap_hits_misses_and_native_sinks(self):
        case=next(c for c in cases() if c.id=='history-cpu')
        proof={'passed':True,'operations':1089,'frozen_operations_checked':9,
               'register_sr_equivalence_operations':1089,'failure_preserves_older_position':True,
               'record_arguments_sha256':'a'*64,'retained_operations':64,'boundaries_checked':65,'seeks':130,
               'negative_controls':['native-presentation-and-hardware-sinks-suppressed','invalid-operation-id',
                                    'checkpoint-byte-8','checkpoint-byte-10','checkpoint-byte-326',
                                    'checkpoint-byte-104','out-of-range-1','out-of-range-65']}
        proofs={name:dict(proof) for name in ('long','cursor-wrap','relocated','native-sinks','logical-api','pending-eviction')}
        proofs['empty']={'passed':True,'operations':0,'boundaries_checked':1}
        proofs['long'].update(operations=12289,register_sr_equivalence_operations=12289,tick_wraps=1,
                              completed_episode_kinds={'1':1,'2':1},terminal_outcome_operations=1,
                              buffer_bytes=80318,retained_operations=4032,boundaries_checked=4033,seeks=8066)
        proofs['cursor-wrap'].update(low_longword_wrap=True,latest=(1<<32)+1089)
        proofs['logical-api']['operation_counts']={name:1 for name in (
            'game_core_init','game_core_select','game_core_sample_pads','game_core_sample_result',
            'game_core_clear_inputs','game_core_return_title','game_round_poll','game_tick_dispatch','game_core_latch_actions')}
        proofs['pending-eviction'].update(pending_canceled=True,evicted_pending_origin=1,eviction_oldest=64,
                                          completed_new_origin=65,completed_new_episode_kind=2)
        report={'passed':True,'execution':'actual-68000-cpu-only',
                'evidence':{'target_role':'legacy-validator-reference','actual_execution':'actual-68000-cpu-only'},
                'history_validation':{'passed':True,'proofs':proofs}}
        self.assertTrue(campaign.required_extent(case,report))
        for name,key,value in (('long','operations',12288),('long','completed_episode_kinds',{'1':1}),
                               ('long','terminal_outcome_operations',0),
                               ('long','buffer_bytes',21470),('long','retained_operations',1023),
                               ('cursor-wrap','latest',1089),('native-sinks','negative_controls',[]),
                               ('relocated','boundaries_checked',64),('logical-api','frozen_operations_checked',8),
                               ('logical-api','operation_counts',{}),('pending-eviction','pending_canceled',False),
                               ('cursor-wrap','record_arguments_sha256','b'*64),('long','failure_preserves_older_position',False)):
            partial=json.loads(json.dumps(report));partial['history_validation']['proofs'][name][key]=value
            with self.subTest(name=name,key=key):self.assertFalse(campaign.required_extent(case,partial))
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
    def test_new_campaign_rejects_old_native_pass_after_child_exit7(self):
        self.child('raise SystemExit(7)\n')
        self.case=Case('fake',('child.py',),'tests/old-native/report.json')
        old=self.root/'build'/self.case.report;atomic_json(old,{'passed':True})
        prior=self.directory/'attempts/fake/000001';prior.mkdir(parents=True)
        atomic_json(prior/'started.json',dict(action='run',dependency_key=campaign.canonical(self.deps),started_utc='2026-01-01T00:00:00+00:00'))
        with patch.object(campaign,'compatible_receipt',return_value=({'path':str(old),'sha256':digest(old)},'old pass')):
            self.assertEqual(self.run_worker(),7)
            new=self.root/'new-campaign';new.mkdir()
            decision=campaign.plan([self.case],new,self.root)[0]
            self.assertEqual(decision['action'],'run');self.assertIn('shared-workspace',decision['reason'])
        self.assertEqual(json.loads(old.read_text()),{'passed':True})
    def test_new_campaign_rejects_unfinished_execution(self):
        history=self.root/'build/.acceptance-case-history/fake'/campaign.canonical(self.deps)/'interrupted'
        atomic_json(history/'started.json',dict(action='run',dependency_key=campaign.canonical(self.deps),started_utc='2026-01-01T00:00:00+00:00'))
        with patch.object(campaign,'compatible_receipt',return_value=({'sha256':'oldpass'},'old pass')):
            self.assertEqual(campaign.plan([self.case],self.root/'new',self.root)[0]['action'],'run')
    def test_later_reused_pass_does_not_clear_failed_actual_execution(self):
        base=self.root/'build/.acceptance-case-history/fake'/campaign.canonical(self.deps)
        for name,action,code in [('01','run',7),('02','reuse',0)]:
            atomic_json(base/name/'started.json',dict(action=action,dependency_key=campaign.canonical(self.deps),started_utc='2026-01-01T00:00:0'+name[-1]+'+00:00'))
            atomic_json(base/name/'completion.json',dict(state='failed' if code else 'complete',exit_code=code))
        self.assertIsNotNone(campaign.execution_blocker(self.case,self.deps,self.root))
        atomic_json(base/'03/started.json',dict(action='run',dependency_key=campaign.canonical(self.deps),started_utc='2026-01-01T00:00:03+00:00'))
        atomic_json(base/'03/completion.json',dict(state='complete',exit_code=0))
        self.assertIsNone(campaign.execution_blocker(self.case,self.deps,self.root))
    def test_known_index_key_missing_or_corrupt_record_fails_closed(self):
        base=self.root/'build/.acceptance-case-history/fake'/campaign.canonical(self.deps)/'known'
        base.mkdir(parents=True)
        self.assertIsNotNone(campaign.execution_blocker(self.case,self.deps,self.root))
        (base/'started.json').write_text('corrupt')
        self.assertIsNotNone(campaign.execution_blocker(self.case,self.deps,self.root))
        atomic_json(base/'started.json',dict(action='run',dependency_key='different',started_utc='2026-01-01T00:00:00+00:00'))
        self.assertIsNotNone(campaign.execution_blocker(self.case,self.deps,self.root))
        atomic_json(base/'started.json',dict(action='run',dependency_key=campaign.canonical(self.deps),started_utc='2026-01-01T00:00:00+00:00'))
        (base/'completion.json').write_text('corrupt')
        self.assertIsNotNone(campaign.execution_blocker(self.case,self.deps,self.root))
    def test_legacy_campaign_failure_is_scanned_without_index(self):
        old=self.root/'build/acceptance/campaigns/legacy/attempts/fake/000001'
        atomic_json(old/'started.json',dict(action='run',dependency_key=campaign.canonical(self.deps),started_utc='2026-01-01T00:00:00+00:00'))
        atomic_json(old/'completion.json',dict(state='failed',exit_code=7))
        self.assertIsNotNone(campaign.execution_blocker(self.case,self.deps,self.root))
        self.assertIsNone(campaign.execution_blocker(self.case,{'different':'key'},self.root))
    def test_imported_native_pythonpath_missing_and_different_rejected(self):
        case=Case('fake',('child.py',),'tests/native/report.json')
        path=self.root/'build'/case.report
        report=dict(passed=True,evidence={'command':['child.py'],'files':{},'environment':{'RUST_LOG':'info'}})
        with patch.object(campaign,'status',return_value={'status':'passed'}),patch.dict(os.environ,{'PYTHONPATH':'current'}):
            atomic_json(path,report);self.assertIsNone(campaign.compatible_receipt(case,self.root)[0])
            report['evidence']['environment']['PYTHONPATH']='other';atomic_json(path,report)
            self.assertIsNone(campaign.compatible_receipt(case,self.root)[0])
            report['evidence']['environment']['PYTHONPATH']='current';atomic_json(path,report)
            self.assertIsNotNone(campaign.compatible_receipt(case,self.root)[0])
    def test_fresh_environment_binding_reuses_in_new_campaign(self):
        case=Case('fake',('child.py',),'tests/native/report.json')
        self.deps['environment']={'RUST_LOG':'info','PYTHONPATH':None}
        path=self.root/'build'/case.report
        atomic_json(path,dict(passed=True,evidence={'command':['child.py'],'files':{},'environment':{'RUST_LOG':'info'}}))
        with patch.object(campaign,'status',return_value={'status':'passed'}),patch.dict(os.environ,{},clear=True):
            saved=campaign.fresh_receipt(case,self.root,campaign.canonical(self.deps));self.assertIsNotNone(saved)
            history=self.root/'build/.acceptance-case-history/fake'/campaign.canonical(self.deps)/'actual'
            atomic_json(history/'started.json',dict(action='run',dependency_key=campaign.canonical(self.deps),started_utc='2026-01-01T00:00:00+00:00'))
            atomic_json(history/'completion.json',dict(state='complete',exit_code=0,dependency_key=campaign.canonical(self.deps),receipt=saved,artifacts={}))
            self.assertEqual(campaign.plan([case],self.root/'new',self.root)[0]['action'],'reuse')
            with patch.dict(os.environ,{'PYTHONPATH':'different'}):
                self.assertIsNone(campaign.compatible_receipt(case,self.root)[0])
    def test_exit0_cannot_bind_untouched_old_receipt(self):
        case=Case('fake',('child.py',),'tests/native/report.json');path=self.root/'build'/case.report
        atomic_json(path,dict(passed=True,evidence={'started_utc':'2026-01-01T00:00:00+00:00'}))
        self.assertFalse(campaign.produced_receipt(case,self.root,'2026-01-02T00:00:00+00:00',campaign.receipt_token(case,self.root)))
    def test_fresh_environment_binding_cannot_override_contradictory_header(self):
        case=Case('fake',('child.py',),'tests/native/report.json');path=self.root/'build'/case.report
        atomic_json(path,dict(passed=True,evidence={'command':['child.py'],'files':{},'environment':{'RUST_LOG':'info','PYTHONPATH':'old'}}))
        with patch.object(campaign,'status',return_value={'status':'passed'}),patch.dict(os.environ,{'PYTHONPATH':'new'}):
            self.assertIsNone(campaign.fresh_receipt(case,self.root,campaign.canonical(self.deps)))
    def test_metrics_optional_absence_is_not_required_missing_file(self):
        self.stub.stop()
        try:
            from native_metrics import CASES
            path=self.root/next(iter(CASES.values()))
            optional='build/tests/optional-never-run.json'
            atomic_json(path,{'passed':True,'evidence':{'optional_inputs_absent':[optional]}})
            case=Case('metrics',('scripts/native_metrics.py',),category='host')
            deps=campaign.dependencies(case,self.root)
            self.assertNotIn(str(self.root/optional),deps['files'])
            self.assertTrue(deps['optional_absence'][str(self.root/optional)])
        finally:self.stub.start()
    def test_metrics_runtime_failure_and_composite_invalidate_identity(self):
        self.stub.stop()
        try:
            from native_metrics import CASES
            relative=next(iter(CASES.values()));path=self.root/relative;atomic_json(path,{'passed':True})
            case=Case('metrics',('scripts/native_metrics.py',),category='host')
            initial=campaign.canonical(campaign.dependencies(case,self.root))
            atomic_json(path,{'passed':False})
            self.assertNotEqual(initial,campaign.canonical(campaign.dependencies(case,self.root)))
            plan=self.root/'composite.json';atomic_json(plan,{'passed':True})
            with patch.dict(os.environ,{'CTENNIS_ACCEPTANCE_COMPOSITE':str(plan)}):
                old=campaign.canonical(campaign.dependencies(case,self.root));atomic_json(plan,{'passed':False})
                self.assertNotEqual(old,campaign.canonical(campaign.dependencies(case,self.root)))
        finally:self.stub.start()
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
             patch.object(campaign,'caller_ancestors',return_value=set()),\
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
             patch.object(campaign,'caller_ancestors',return_value=set()),\
             patch.object(campaign,'process_identity',side_effect=[owner,identity,identity]):
            with self.assertRaisesRegex(RuntimeError,'Cannot verify'):
                campaign.tagged_processes('old',owner)
    def test_reconnect_launcher_identity_is_not_descendant(self):
        from unittest.mock import Mock
        owner=dict(campaign.process_identity(),start='1',group=-1)
        item=Mock();item.name='999999';item.__truediv__=Mock()
        identity=dict(owner,pid=999999,start='2',group=-2)
        with patch.object(campaign.Path,'iterdir',return_value=[item]),\
             patch.object(campaign,'caller_ancestors',return_value={(999999,'2')}),\
             patch.object(campaign,'process_identity',side_effect=[owner,identity]):
            self.assertEqual(campaign.tagged_processes('old',owner),[])
        item.__truediv__.assert_not_called()
        owned=dict(identity,group=owner['group'])
        with patch.object(campaign.Path,'iterdir',return_value=[item]),\
             patch.object(campaign,'caller_ancestors',return_value={(999999,'2')}),\
             patch.object(campaign,'process_identity',side_effect=[owner,owned]):
            self.assertEqual(campaign.tagged_processes('old',owner),[owned])

if __name__=='__main__':unittest.main()
