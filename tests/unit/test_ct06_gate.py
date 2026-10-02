"""Focused result acceptance: local extent and ordinary restart stay separate."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
import evidence
import progress
import run_result_presentation_tests as runner

class ResultGateTests(unittest.TestCase):
    def test_early_release_requires_sampled_release_fresh_press_and_held_p2(self):
        names=('match_award','returned_title_display','title_ready','restart_selected','early_release',
               'sampled_release','early_repress','sampled_repress','restart_playing','fresh_action_eligible','restarted_flight')
        points=dict(zip(names,range(100,111)))
        report={'case':'ct06-ordinary-one-early-release','subject':'maintained-native',
                'executable_sha256':'ordinary','start_mode':'one','restart_mode':'two',
                'consecutive_callbacks':True,'early_release_verified':True,
                'observed_callbacks':200,'checkpoints':points,'action_samples':{
                    'before_release':{'lifecycle':9,'raw':[16,16],'latches':[16,16]},
                    'sampled_release':{'callback':points['sampled_release'],'lifecycle':9,
                        'raw':[0,16],'latches':[0,16],'released':[16,0]},
                    'sampled_repress':{'callback':points['sampled_repress'],'lifecycle':9,
                        'raw':[16,16],'latches':[0,16],'pressed':[16,0]},
                    'playable':{'callback':points['fresh_action_eligible'],'lifecycle':1,
                        'raw':[16,16],'latches':[0,16],'controls':[16,0]}}}
        self.assertTrue(progress.early_release_proof(report,'ordinary'))
        self.assertFalse(progress.early_release_proof(report,'wrong-executable'))
        for sample,key,value in (('sampled_release','latches',[16,16]),
                                 ('sampled_repress','pressed',[0,0]),
                                 ('playable','controls',[16,16]),
                                 ('playable','callback',points['restarted_flight'])):
            altered=copy.deepcopy(report);altered['action_samples'][sample][key]=value
            self.assertFalse(progress.early_release_proof(altered,'ordinary'))

    def test_result_media_dependencies_follow_declared_directories(self):
        # The graph contract must also run in a source-only checkout. This is
        # in-memory dependency metadata, not fabricated source pixels/audio.
        primary=evidence.ROOT/'tests/reference/presentation/manifest.json'
        declared=json.dumps({'references': {
            'one-player-match': {'manifest':'one-player-match/manifest.json'},
            'two-player-match': {'manifest':'two-player-match/manifest.json'}}})
        original_read=Path.read_text
        original_is_file=Path.is_file
        def read_manifest(path,*args,**kwargs):
            return declared if path==primary else original_read(path,*args,**kwargs)
        def manifest_exists(path):
            return path==primary or original_is_file(path)
        with patch.object(evidence,'tool_info',return_value=({},set())), \
             patch.object(Path,'read_text',read_manifest), \
             patch.object(Path,'is_file',manifest_exists):
            paths,_=evidence.inputs_for('result-scenes','scripts/run_result_presentation_tests.py',runner.CASES[1])
        names={evidence.key(path) for path in paths}
        self.assertNotIn('tests/reference/presentation/two-player-restart-complete/manifest.json',names)
        self.assertIn('tests/reference/presentation/two-player-match/manifest.json',names)
        self.assertIn('tests/reference/presentation-result-scenes-two-player/two-player-restart-complete/manifest.json',names)

    def test_scene_shortened_output_wrong_subject_and_expanded_scratch_reject(self):
        recipe={'name':'scene','initial_source_update':10,'completed_callbacks':[11,12]}
        report={'case':'scene','subject':'maintained-native','state_contract':progress.MAINTAINED_STATE_CONTRACT,
            'omitted_legacy_scratch_offsets':list(progress.MAINTAINED_SCRATCH_OFFSETS),
            'state_bytes_compared_per_callback':250,'raw_state_subject':'maintained-native',
            'raw_state_contract':'original-byte-page-diagnostic-v1','raw_state_bytes_compared_per_callback':254,
            'raw_state_passed':False,'hardware_mutations':[{'kind':k,'detected':True} for k in ('sprite','field','entropy')],
            'checks':{'states':[{'update':n,'differences':[]} for n in (11,12)],'source_events':[],
                'pixels':[{'checkpoint':n,'region':r,'expected_sha256':'abc','actual_sha256':'abc','first_difference':None}
                          for n in (11,12) for r in ('viewport','point_a','point_b','games_a','games_b','status','mode')]}}
        self.assertTrue(progress.result_scene_proof(report,recipe))
        for key,value in [('subject','translated'),('omitted_legacy_scratch_offsets',[103,104,105,106,107]),
                          ('hardware_mutations',[])]:
            altered=copy.deepcopy(report);altered[key]=value
            self.assertFalse(progress.result_scene_proof(altered,recipe))
        for key in ('states','pixels'):
            altered=copy.deepcopy(report);altered['checks'][key].pop()
            self.assertFalse(progress.result_scene_proof(altered,recipe))

    def test_local_start_wrong_executable_and_unordered_ordinary_restart_reject(self):
        names=('match_award','returned_title_display','title_ready','restart_selected','restart_playing','old_action_blocked','restart_action','restarted_flight')
        report={'case':'ct06-ordinary-one-restart','subject':'maintained-native','start_mode':'one','restart_mode':'two',
                'executable_sha256':'ordinary','consecutive_callbacks':True,'held_old_actions_verified':True,'observed_callbacks':200,
                'checkpoints':dict(zip(names,range(100,108)))}
        self.assertTrue(progress.ordinary_restart_proof(report,'one','ordinary'))
        self.assertFalse(progress.ordinary_restart_proof(report,'one','captured-phase'))
        for changes in ({'case':'one-player-match-complete-phase'},{'consecutive_callbacks':False},{'held_old_actions_verified':False},
                        {'restart_mode':'one'},{'observed_callbacks':2},
                        {'checkpoints':dict(report['checkpoints'],restarted_flight=100)}):
            self.assertFalse(progress.ordinary_restart_proof(dict(report,**changes),'one','ordinary'))

    def test_actual_result_runner_replaces_old_pass_on_failed_and_interrupted_setup(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);name=runner.CASES[0]
            recipe=root/f'tests/cases/{name}.json';recipe.parent.mkdir(parents=True)
            recipe.write_text(json.dumps({'name':name}))
            report=root/f'build/tests/{name}-report.json';report.parent.mkdir(parents=True)
            for error,state in ((RuntimeError('setup stop'),'failed'),(KeyboardInterrupt(),'interrupted')):
                report.write_text('{"passed":true}')
                def stop(case):
                    self.assertEqual(json.loads(report.read_text())['evidence']['state'],'incomplete')
                    raise error
                with patch.object(runner,'ROOT',root),patch.object(evidence,'ROOT',root), \
                     patch.object(evidence,'inputs_for',return_value=(set(),{})), \
                     patch.object(runner,'reference',side_effect=stop),patch.object(sys,'argv',['runner',f'--case={name}']):
                    with self.assertRaises(type(error)):runner.main()
                current=json.loads(report.read_text());self.assertFalse(current['passed'])
                self.assertEqual(current['evidence']['state'],state)

if __name__=='__main__':unittest.main()
