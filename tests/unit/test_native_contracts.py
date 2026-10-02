"""Native input isolation, fixed contract and immutable-fixture guards."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
import native_assets
from native_clock import INTERVAL_16_16
from run_demo_match_tests import load_trajectory

ROOT = Path(__file__).resolve().parents[2]


class NativeContracts(unittest.TestCase):
    def test_accepted_clock_and_assembly_declarations_agree(self):
        self.assertEqual(INTERVAL_16_16, 775830074)
        source = (ROOT / 'amiga/main.s').read_text()
        self.assertIn('SIM_INTERVAL_WHOLE equ 11838', source)
        self.assertIn('SIM_INTERVAL_FRACTION equ 14906', source)

    def test_canonical_native_trajectory_is_independently_bound(self):
        expected, manifest = load_trajectory(ROOT / 'assets/interface/demo-inputs.json')
        self.assertEqual(len(expected), 10958)
        self.assertEqual(manifest['payload_sha256'], '17dd5ddba0499a70956b2d588f084786a00c294672510f69ef991858734d79e6')
        with tempfile.TemporaryDirectory() as directory:
            changed = Path(directory) / 'recording.json'
            changed.write_bytes((ROOT / 'assets/interface/demo-inputs.json').read_bytes() + b'\n')
            with self.assertRaisesRegex(AssertionError, 'Recording does not match'):
                load_trajectory(changed)

    def test_missing_corrupt_and_undeclared_assets_fail_without_recovery(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT / 'assets', root / 'assets')
            with patch.object(native_assets, 'ROOT', root):
                native_assets.prepare()  # only versioned native inputs, empty outputs/config
                asset = root / 'assets/native/scene/poses.bin'
                original = asset.read_bytes()
                asset.unlink()
                with self.assertRaisesRegex(FileNotFoundError, 'Missing versioned native input'):
                    native_assets.prepare()
                asset.write_bytes(bytes([original[0] ^ 1]) + original[1:])
                with self.assertRaisesRegex(ValueError, 'Incompatible versioned native input'):
                    native_assets.prepare()
                asset.write_bytes(original)
                (root / 'assets/native/unlisted.bin').write_bytes(b'undeclared')
                with self.assertRaisesRegex(ValueError, 'Undeclared or missing'):
                    native_assets.prepare()
