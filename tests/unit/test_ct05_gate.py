"""Finite CT05 gate controls: bounded round evidence never certifies a match."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
import evidence
import progress


class BoundedRoundGateTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        for module in (evidence, progress):
            context = patch.object(module, 'ROOT', self.root)
            context.start()
            self.addCleanup(context.stop)
        env = patch.dict(os.environ, RUST_LOG='info')
        env.start()
        self.addCleanup(env.stop)
        self.reference = self.root / 'tests/reference/two-player-match.json'
        self.reference.parent.mkdir(parents=True)
        self.reference.write_text(json.dumps({'initial_callback': {'ordinal': 0}, 'updates': [{}] * 10,
            'milestones': {name: {'update': value} for name, value in zip(
                ('first_game_award', 'tail_only_start', 'gameplay_resumed', 'resumed_serve_flight'), (2,3,4,5))}}))
        self.exe = self.root / 'game'
        self.exe.write_bytes(b'compiled')
        self.path = self.root / 'report.json'

    def complete(self, updates=8, subject='maintained', **changes):
        transaction = evidence.ReportRun([self.path], 'replay', subject, 'captured phase',
                                         [self.reference], {'tool': {'version': '1'}})
        report = dict(case='two-player-match', passed=True, subject=subject, entry_point='game_source_tick',
                      executable_sha256=evidence.digest(self.exe), updates=updates, updates_matched=updates,
                      reference_updates=10, full_replay_executed=updates == 10, first_difference=None,
                      reference_sha256=evidence.digest(self.reference))
        report.update(changes)
        transaction.finalize(self.path, report, [{'files': evidence.snapshot([self.exe]),
            'executable': 'game', 'executable_sha256': evidence.digest(self.exe)}])

    def test_bounded_pass_preserves_full_match_rejection(self):
        self.complete()
        result = progress.bounded_round_status(self.path)
        self.assertEqual(result['status'], 'passed')
        self.assertEqual((result['executed'], result['reference'], result['required_updates']), (8,10,5))
        self.assertFalse(result['full_match_executed'])
        self.assertEqual(evidence.status(self.path, 'maintained', full=True)['status'], 'failed')
        self.assertEqual(progress.report_path('ct05-r2-first-round'), progress.report_path('two-player-match'))

    def test_missing_stale_wrong_subject_and_short_prefix_reject(self):
        self.assertEqual(progress.bounded_round_status(self.path)['status'], 'not run')
        for updates, subject in ((4,'maintained'), (8,'translated')):
            self.complete(updates,subject)
            self.assertNotEqual(progress.bounded_round_status(self.path)['status'], 'passed')
        self.complete()
        self.reference.write_text('{}')
        self.assertEqual(progress.bounded_round_status(self.path)['status'], 'stale')

    def test_mismatch_and_subject_case_reference_mismatch_reject(self):
        for changes in ({'first_difference': {'update': 6}}, {'case': 'a-local-phase'},
                        {'reference_sha256': 'wrong'}, {'updates_matched': 7}):
            with self.subTest(changes=changes):
                self.complete(**changes)
                self.assertNotEqual(progress.bounded_round_status(self.path)['status'], 'passed')

    def test_ordinary_requires_ordered_actual_events_and_exact_executable(self):
        report = dict(case='ct05-ordinary-one-round', executable_sha256='actual', award_callback=10,
                      pause_callback=20, resume_callback=30, next_serve_callback=40, observed_callbacks=31)
        self.assertTrue(progress.ordinary_round_proof(report, 'one', 'actual'))
        for changes in ({'pause_callback': None}, {'resume_callback': 5}, {'observed_callbacks': 2},
                        {'executable_sha256': 'other'}, {'case': 'ct05-ordinary-two-round'}):
            with self.subTest(changes=changes):
                self.assertFalse(progress.ordinary_round_proof({**report, **changes}, 'one', 'actual'))

class SceneRunStartTests(unittest.TestCase):
    def test_actual_scene_runner_keeps_incomplete_until_atomic_failure(self):
        import run_round_presentation_tests as runner
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            recipe = root / 'tests/cases/p1-first-round-scenes.json'
            recipe.parent.mkdir(parents=True)
            recipe.write_text(json.dumps({'name': 'p1-first-round-scenes'}))
            report = root / 'build/tests/p1-first-round-scenes-report.json'
            report.parent.mkdir(parents=True)
            report.write_text('{"passed": true}')
            def stop_before_capture(case):
                self.assertEqual(json.loads(report.read_text())['evidence']['state'], 'incomplete')
                raise RuntimeError('bounded setup stop')
            with patch.object(runner, 'ROOT', root), patch.object(evidence, 'ROOT', root), \
                 patch.object(evidence, 'inputs_for', return_value=(set(), {'tool': {'version': '1'}})), \
                 patch.object(runner, 'reference', side_effect=stop_before_capture), \
                 patch.object(sys, 'argv', ['runner', '--case=p1-first-round-scenes']):
                with self.assertRaisesRegex(RuntimeError, 'bounded setup stop'):
                    runner.main()
            result = json.loads(report.read_text())
            self.assertFalse(result['passed'])
            self.assertEqual(result['evidence']['state'], 'failed')


if __name__ == '__main__':
    unittest.main()
