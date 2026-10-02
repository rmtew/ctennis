import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
from native_evidence import ReportRun, digest, snapshot, status

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
        return ReportRun([self.report], 'replay', 'maintained', 'ordinary native title', [self.source], {'test-tool': {'version': '1'}})

    def complete(self, run=None, **changes):
        run = run or self.start()
        result = dict(passed=True, subject='maintained', entry_point='game_tick_dispatch', executable_sha256=digest(self.exe), updates=200, reference_updates=200, updates_matched=200, full_replay_executed=True, first_difference=None)
        result.update(changes)
        run.finalize(self.report, result, [{'files': snapshot([self.exe]), 'symbols': [], 'executable': str(self.exe), 'executable_sha256': digest(self.exe)}])
        return run

    def test_interface_flavors_cannot_cross_credit(self):
        run = self.start()
        result = dict(passed=True, subject='maintained', entry_point='game_tick_dispatch', executable_sha256=digest(self.exe), updates=200, reference_updates=200, updates_matched=200, full_replay_executed=True, first_difference=None)
        compiled = dict(files=snapshot([self.exe]), symbols=['game_enhanced_interface'], executable=str(self.exe), executable_sha256=digest(self.exe), interface_flavor='enhanced')
        run.finalize(self.report, result, [compiled])
        self.assertEqual(status(self.report, interface_flavor='enhanced')['status'], 'passed')
        self.assertEqual(status(self.report, interface_flavor='original')['status'], 'stale')
        run = self.start()
        run.finalize(self.report, dict(result, interface_flavor='original'), [compiled])
        self.assertEqual(status(self.report)['status'], 'failed')
        self.complete()
        self.assertEqual(status(self.report, interface_flavor='enhanced')['status'], 'stale')

    def test_unchanged_reused_and_fresh_execution(self):
        run = self.complete()
        self.assertEqual(status(self.report, 'maintained', full=True)['freshness'], 'reused')
        self.assertEqual(status(self.report, 'maintained', full=True, fresh_since=run.meta['started_utc'])['freshness'], 'fresh')
        unrelated = self.root / 'unrelated.txt'
        unrelated.write_text('changed')
        self.assertEqual(status(self.report)['status'], 'passed')

    def test_missing_and_legacy_report(self):
        self.assertEqual(status(self.report)['status'], 'not run')
        self.report.write_text('{"passed": true}')
        self.assertEqual(status(self.report)['status'], 'stale')

    def test_interrupted_and_failed_latest_replace_pass(self):
        self.complete()
        run = self.start()
        self.assertFalse(json.loads(self.report.read_text())['passed'])
        self.assertEqual(status(self.report)['status'], 'interrupted')
        run.abort(RuntimeError('failed rerun'))
        self.assertEqual(status(self.report)['status'], 'failed')
        self.assertFalse(json.loads(self.report.read_text())['passed'])

    def test_subject_and_extent_cannot_pass(self):
        self.complete()
        self.assertEqual(status(self.report, 'other-native')['status'], 'stale')
        self.complete(full_replay_executed=False, updates=96, updates_matched=96)
        self.assertEqual(status(self.report, 'maintained', full=True)['status'], 'failed')

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

    def test_during_run_change_and_changed_executable(self):
        run = self.start()
        self.source.write_text('changed during run')
        self.complete(run)
        self.assertEqual(status(self.report)['status'], 'stale')
        self.complete()
        self.exe.write_bytes(b'different executable')
        self.assertEqual(status(self.report)['status'], 'stale')

class ListingAssetTests(unittest.TestCase):

    def test_truncated_shared_directory_uses_actual_listing_source_context(self):
        from native_evidence import compile_manifest
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first, second = (root / 'initial.bin', root / 'refresh.bin')
            first.write_bytes(b'initial')
            second.write_bytes(b'refresh')
            source, include = (root / 'game.s', root / 'refresh.i')
            source.write_text(f'initial: incbin "{first}"\n')
            include.write_text(f'refresh: incbin "{second}"\n')
            exe, listing = (root / 'game', root / 'native.lst')
            exe.write_bytes(b'game')
            listing.write_text(f'Source: "{source}"\n00:00000000 initial: incbin "{root}/\nSource: "{include}"\n00:00000008 refresh: incbin "{root}/\n')
            compiled = compile_manifest(exe, listing)
            self.assertIn(str(first), compiled['files'])
            self.assertIn(str(second), compiled['files'])

    def test_truncated_incbin_line_uses_compiled_source_and_invalidates_asset_change(self):
        from native_evidence import compile_manifest
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, asset = (root / 'source.s', root / 'long-private-asset.bin')
            source.write_text(f'blob: incbin "{asset}"\n')
            asset.write_bytes(b'asset')
            exe, listing = (root / 'game', root / 'native.lst')
            exe.write_bytes(b'game')
            listing.write_text(f'Source: "{source}"\n00:00000000 blob: incbin "{str(asset)[:-4]}\n00:00000008 00000000\nSource: "{source}"\n')
            compiled = compile_manifest(exe, listing)
            self.assertIn(str(asset), compiled['files'])
            from native_evidence import changed
            self.assertFalse(changed(compiled['files']))
            asset.write_bytes(b'changed')
            self.assertIn(str(asset), changed(compiled['files']))
