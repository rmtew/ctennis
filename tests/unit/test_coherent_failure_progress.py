import gzip
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from coherent_failure_progress import write_progress


class CoherentFailureProgress(unittest.TestCase):
    def test_partial_scenes_and_stage_profiles_retained_without_pass_claim(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'unvalidated-progress.json.gz'
            payload=dict(passed=False,endpoints=[dict(first_actual_publication=dict(mode=1))],endpoint_profiles=[dict(completed=False)])
            write_progress(p,payload)
            with gzip.open(p,'rt') as f:self.assertEqual(json.load(f),payload)

    def test_cap_failure_preserves_prior_progress_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'unvalidated-progress.json.gz';write_progress(p,dict(passed=False))
            previous=p.read_bytes()
            with patch('coherent_failure_progress.MAX_UNCOMPRESSED',1):
                with self.assertRaisesRegex(ValueError,'uncompressed storage cap'):write_progress(p,dict(new='oversized'))
            self.assertEqual(p.read_bytes(),previous)
            self.assertFalse(p.with_name(p.name+'.tmp').exists())


if __name__=='__main__':unittest.main()
