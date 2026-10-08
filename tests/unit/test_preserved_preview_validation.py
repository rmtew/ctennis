"""The saved PAL correction must fail closed for any other validator drift."""
import hashlib
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from validate_preserved_preview import gate_projection,OLD,NEW


class PreservedPreviewValidation(unittest.TestCase):
    def test_only_the_single_activity_requirement_can_change(self):
        original='strict guards\n'+OLD+'\nstrict attribution\n'
        expected=hashlib.sha256(original.encode()).hexdigest()
        corrected=original.replace(OLD,NEW)
        gate_projection(corrected,expected)
        for invalid in (corrected+'extra rule\n',corrected.replace('strict attribution','relaxed attribution'),
                        corrected+NEW,original):
            with self.subTest(invalid=invalid):
                with self.assertRaises(AssertionError):gate_projection(invalid,expected)


if __name__=='__main__':unittest.main()
