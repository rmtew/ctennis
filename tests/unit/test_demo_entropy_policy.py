import hashlib
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from native_assets import demo_entropy_policy


class DemoEntropyPolicyTests(unittest.TestCase):
    def test_modern_recording_explicitly_uses_correct_generator(self):
        self.assertEqual(demo_entropy_policy(b'{"entropy_version":"galois16-b400-v2"}',{}),0)

    def test_legacy_requires_exact_recording_identity_and_truthful_policy(self):
        recording = b'{"entropy_version":"galois16-b400-v1"}'
        compatibility = {'schema':1,'policy':1,'effective_entropy_policy':'legacy-shift16-v1',
            'original_entropy_label':'galois16-b400-v1',
            'recording_sha256':hashlib.sha256(recording).hexdigest()}
        self.assertEqual(demo_entropy_policy(recording,compatibility),1)
        for changed in (dict(compatibility,recording_sha256='different'),
                        dict(compatibility,effective_entropy_policy='galois16-b400-v1'),
                        dict(compatibility,original_entropy_label='different'),
                        dict(compatibility,policy=0),dict(compatibility,schema=2)):
            with self.assertRaises(ValueError):
                demo_entropy_policy(recording,changed)
        with self.assertRaises(ValueError):
            demo_entropy_policy(recording+b' ',compatibility)

    def test_unknown_algorithm_is_rejected(self):
        with self.assertRaises(ValueError):
            demo_entropy_policy(b'{"entropy_version":"unknown"}',{})


if __name__ == '__main__':
    unittest.main()
