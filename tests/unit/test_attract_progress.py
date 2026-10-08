import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from progress import acceptance


class AttractCoverageTests(unittest.TestCase):
    def report(self):
        return dict(entries=[{}, {}, {}], windows=[dict(stable=True,
                    unexpected_title_writes=0, publications=1, next_entry={'idle':1800},
                    first_complete_title_capture={'reply':True},
                    title_frame_digests=['digest']*1400) for _ in range(2)],
                    captures=[f'build/tests/attract-two-cycles/cycle-{cycle}-title-{suffix}.png'
                              for cycle in (1,2)
                              for suffix in ('4','first-complete','600','1200','1790')])

    def test_current_complete_capture_extent(self):
        self.assertTrue(acceptance('attract-cycles',self.report()))

    def test_missing_or_duplicate_capture_is_rejected(self):
        for replacement in (None, 'cycle-1-title-4.png', 'unrelated.png'):
            r=self.report()
            if replacement is None:r['captures'].pop()
            else:r['captures'][-1]=replacement
            self.assertFalse(acceptance('attract-cycles',r))

    def test_each_existing_native_contract_remains_required(self):
        original=self.report()
        for field,value in [('stable',False),('unexpected_title_writes',1),
                            ('publications',0),('next_entry',None),
                            ('first_complete_title_capture',{}),
                            ('title_frame_digests',['digest']*1399)]:
            with self.subTest(field=field):
                r=copy.deepcopy(original);r['windows'][1][field]=value
                self.assertFalse(acceptance('attract-cycles',r))
