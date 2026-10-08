"""The saved PAL correction must fail closed for any other validator drift."""
import hashlib
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from validate_preserved_preview import gate_projection,OLD,NEW,archive_coverage,ARCHIVE_NAMES,SOURCE_COMMIT,SOURCE_SHA,SOURCE_DIR,ROOT


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

    def test_truncated_or_unbound_archive_cannot_validate(self):
        import copy
        rows=[dict(source=str(Path('build/tests/preview-native-pal')/name),
            archive=str((SOURCE_DIR/'failed-artifacts'/name).relative_to(ROOT)),
            sha256=SOURCE_SHA if name=='report.json' else '11'*32) for name in sorted(ARCHIVE_NAMES)]
        files={r['source']:r['sha256'] for r in rows}
        archive=dict(commit=SOURCE_COMMIT,files=rows);archive_coverage(archive,files)
        for invalid in (dict(commit=SOURCE_COMMIT,files=[]),dict(commit=SOURCE_COMMIT,files=rows[:-1]),
                        dict(commit='00'*20,files=rows)):
            with self.assertRaises(AssertionError):archive_coverage(invalid,files)
        invalid=copy.deepcopy(archive);invalid['files'][0]['source']='another-case/'+Path(rows[0]['source']).name
        with self.assertRaises(AssertionError):archive_coverage(invalid,files)
        invalid=copy.deepcopy(archive);invalid['files'][0]['sha256']='22'*32
        with self.assertRaises(AssertionError):archive_coverage(invalid,files)


if __name__=='__main__':unittest.main()
