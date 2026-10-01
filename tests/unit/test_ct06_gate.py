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
    def test_result_media_dependencies_follow_declared_directories(self):
        with patch.object(evidence,'tool_info',return_value=({},set())):
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
