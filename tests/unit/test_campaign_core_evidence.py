"""Compatibility rejection must precede expensive CPU replay or capture reuse."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'scripts'))
import campaign_core_evidence as evidence


class CoreEvidenceTests(unittest.TestCase):
    def capture(self, root):
        path = root/'build/tests/shared-match-core-pal-demo/report.json'
        path.parent.mkdir(parents=True)
        value = {'passed': True, 'files': {'amiga/main.s': 'source'},
                 'sha256': {'build/standalone/match-core': 'product'},
                 'summary': {'operations': 1, 'written_bytes': 318},
                 'rows': [{'index': 0, 'state': bytes(318).hex()}],
                 'target': dict(video='PAL', cpu='68000', chipset='OCS',
                                chip_kib=512, slow_kib=0, fast_kib=0),
                 'demo': True, 'seconds': 300}
        path.write_text(json.dumps(value))
        return path, value

    def test_changed_native_source_rejected_before_cpu(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.capture(root)
            with patch.object(evidence, 'ROOT', root), patch.object(evidence, 'changed', return_value=['amiga/main.s']):
                with self.assertRaisesRegex(ValueError, 'inputs changed'):
                    evidence.capture_inputs('pal-demo')

    def test_full_state_stream_target_and_extent_required(self):
        for key, bad in [('rows', [{'index': 0, 'state': bytes(314).hex()}]),
                         ('rows', [{'index': 1, 'state': bytes(318).hex()}]),
                         ('seconds', 8), ('demo', False),
                         ('target', dict(video='NTSC', cpu='68000'))]:
            with self.subTest(key=key, bad=bad), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                path, value = self.capture(root)
                value[key] = bad
                path.write_text(json.dumps(value))
                with patch.object(evidence, 'ROOT', root), patch.object(evidence, 'changed', return_value=[]):
                    with self.assertRaises(ValueError):
                        evidence.capture_inputs('pal-demo')

    def test_latest_failed_cpu_proof_never_reuses_pass_flag(self):
        case = evidence.core_cases()[0]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'build'/case.report
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps({'passed': True, 'proof': 'pal-demo'}))
            with patch.object(evidence, 'status', return_value={'status': 'failed'}):
                receipt, reason = evidence.validate(case, directory)
            self.assertIsNone(receipt)
            self.assertIn('failed', reason)


if __name__ == '__main__':
    unittest.main()
