"""Finite false-pass controls for report freshness; no gameplay expectations."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
from evidence import ReportRun, digest, snapshot, status


class FreshnessTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.source = self.root / 'source.s'
        self.source.write_text('original')
        self.exe = self.root / 'game'
        self.exe.write_bytes(b'executable')
        self.report = self.root / 'report.json'
        self.env = patch.dict(os.environ, RUST_LOG='info')
        self.env.start()
        self.addCleanup(self.env.stop)

    def start(self):
        return ReportRun([self.report], 'replay', 'maintained', 'captured phase',
                         [self.source], {'test-tool': {'version': '1'}})

    def complete(self, run=None, **changes):
        run = run or self.start()
        result = dict(passed=True, subject='maintained', entry_point='game_source_tick', executable_sha256=digest(self.exe),
                      updates=200, reference_updates=200, updates_matched=200,
                      full_replay_executed=True, first_difference=None)
        result.update(changes)
        run.finalize(self.report, result, [{'files': snapshot([self.exe]), 'symbols': [],
                                           'executable': str(self.exe), 'executable_sha256': digest(self.exe)}])
        return run

    def test_unchanged_reused_and_fresh_execution(self):
        run = self.complete()
        self.assertEqual(status(self.report, 'maintained', full=True)['freshness'], 'reused')
        self.assertEqual(status(self.report, 'maintained', full=True, fresh_since=run.meta['started_utc'])['freshness'], 'fresh')
        unrelated = self.root / 'unrelated.txt'
        unrelated.write_text('changed')
        self.assertEqual(status(self.report)['status'], 'passed')

    def test_relevant_changed_and_missing_input(self):
        self.complete()
        self.source.write_text('changed')
        self.assertEqual(status(self.report)['status'], 'stale')
        self.source.unlink()
        self.assertEqual(status(self.report)['status'], 'stale')

    def test_missing_and_legacy_report(self):
        self.assertEqual(status(self.report)['status'], 'not run')
        self.report.write_text('{"passed": true}')
        self.assertEqual(status(self.report)['status'], 'stale')

    def test_interrupted_and_failed_latest_replace_pass(self):
        self.complete()
        run = self.start()  # Simulate a kill: no finalize/abort at all.
        self.assertFalse(json.loads(self.report.read_text())['passed'])
        self.assertEqual(status(self.report)['status'], 'interrupted')
        run.abort(RuntimeError('failed rerun'))
        self.assertEqual(status(self.report)['status'], 'failed')
        self.assertFalse(json.loads(self.report.read_text())['passed'])

    def test_subject_and_extent_cannot_pass(self):
        self.complete()
        self.assertEqual(status(self.report, 'translated')['status'], 'stale')
        self.complete(full_replay_executed=False, updates=96, updates_matched=96)
        self.assertEqual(status(self.report, 'maintained', full=True)['status'], 'failed')

    def test_aggregate_rejects_subject_partial_and_retained_pass(self):
        from run_test_suite import classify
        self.complete(case='serve')
        saved = json.loads(self.report.read_text())
        self.assertEqual(classify(saved, None, self.report), 'green')
        self.complete(case='serve', subject='translated')
        self.assertEqual(classify(saved, None, self.report), 'stale')
        self.complete(case='serve', full_replay_executed=False, updates=96, updates_matched=96)
        self.assertEqual(classify(saved, None, self.report), 'incomplete')
        self.start().abort(RuntimeError('latest failure'))
        self.assertNotEqual(classify(saved, None, self.report), 'green')

    def test_malformed_target_and_disagreeing_match_are_rejected(self):
        self.report.write_text('[]')
        self.assertEqual(status(self.report)['status'], 'stale')
        self.complete()
        value = json.loads(self.report.read_text())
        value['evidence']['target']['fast_bytes'] = 524288
        self.report.write_text(json.dumps(value))
        self.assertEqual(status(self.report)['status'], 'stale')
        self.complete(updates_matched=199)
        self.assertEqual(status(self.report)['status'], 'failed')

    def test_optional_reference_appearance_invalidates_selected_fallback(self):
        optional = self.root / 'optional-reference.json'
        run = self.start()
        run.meta['optional_inputs_absent'] = [str(optional)]
        self.complete(run)
        self.assertEqual(status(self.report)['status'], 'passed')
        optional.write_text('{}')
        self.assertEqual(status(self.report)['status'], 'stale')

    def test_progress_integration_and_diagnostics_cannot_promote_gates(self):
        import progress
        build = self.root / 'build/amiga/gameplay-integration/build-report.json'
        build.parent.mkdir(parents=True)
        build.write_text(json.dumps({'compiled_symbols': [
            'game_player_tick', 'game_player_contact', 'game_ball_tick',
            'game_derive_launch', 'game_launch_root', 'game_move_player',
            'game_ai_track', 'game_ai_setup']}))
        def synthetic(path, subject=None, full=False, fresh_since=None):
            # Compiled integration is available; runtime reports are not current.
            return ({'status': 'passed', 'startup': 'ordinary title'} if path == build
                    else {'status': 'stale', 'freshness': 'unverified'})
        with patch.object(progress, 'ROOT', self.root), patch.object(progress, 'status', side_effect=synthetic):
            result = progress.progress()
        self.assertNotEqual(result['runtime_dependencies']['subsystems']['AI']['integration'], 'unverified')
        self.assertTrue(all(g['acceptance'] == 'unverified'
                            for g in result['behavior']['capabilities'].values()))
        self.assertEqual(result['delivery']['peak_chip_ram'], 'unverified')
        run = self.start()
        run.meta['subject'] = 'translated'
        self.complete(run, subject='translated', entry_point='fixed translated sequence')
        self.assertEqual(status(self.report)['status'], 'passed')
        self.assertEqual(status(self.report, 'maintained', full=True)['status'], 'stale')

    def test_progress_failed_interrupted_invocation_replaces_old_summary(self):
        import progress
        output = self.root / 'build/progress-report.json'
        output.parent.mkdir(parents=True)
        for error, state in ((RuntimeError('progress failure'), 'failed'),
                             (KeyboardInterrupt(), 'interrupted')):
            output.write_text('{"state": "complete", "old_pass": true}')
            with patch.object(progress, 'ROOT', self.root), patch.object(progress, 'progress', side_effect=error), patch.object(sys, 'argv', ['progress.py']):
                with self.assertRaises(type(error)):
                    progress.main()
            current = json.loads(output.read_text())
            self.assertEqual(current['state'], state)
            self.assertNotIn('old_pass', current)

    def test_during_run_change_and_changed_executable(self):
        run = self.start()
        self.source.write_text('changed during run')
        self.complete(run)
        self.assertEqual(status(self.report)['status'], 'stale')
        self.complete()
        self.exe.write_bytes(b'different executable')
        self.assertEqual(status(self.report)['status'], 'stale')


if __name__ == '__main__':
    unittest.main()
