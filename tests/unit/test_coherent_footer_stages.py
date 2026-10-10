import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from coherent_footer_stages import validate_stages


def fixture(completed=0):
    owner=dict(entry=dict(cck=0),exit=dict(cck=100))
    call=dict(entry=dict(cck=10),exit=dict(cck=90),elapsed_bus_cck=80,callee='tutorial_footer_step')
    before=dict(overlay='00',stage=1,generation=3,stage_generation=3,ready=0,first=0,second=0)
    after=dict(before,stage=0 if completed else 2,first=100 if completed else 0,second=200 if completed else 0)
    c=dict(stack_timing=dict(calls=[call]),footer_stage_profiles=[dict(entry=dict(cck=11),exit=dict(cck=91),before=before,after=after,completed=completed)])
    return c,[(0,owner)]


class FooterStagesTests(unittest.TestCase):
    def test_partial_and_complete(self):
        for completed in (0,1):
            c,owners=fixture(completed);self.assertEqual(validate_stages(c,owners)[0]['completed'],bool(completed))

    def test_live_write_rejected(self):
        c,owners=fixture();c['footer_stage_profiles'][0]['after']['overlay']='01'
        with self.assertRaisesRegex(AssertionError,'live overlay'):validate_stages(c,owners)

    def test_early_ready_rejected(self):
        c,owners=fixture();c['footer_stage_profiles'][0]['after']['ready']=1
        with self.assertRaisesRegex(AssertionError,'prematurely'):validate_stages(c,owners)

    def test_partial_cache_rejected(self):
        c,owners=fixture();c['footer_stage_profiles'][0]['after']['first']=100
        with self.assertRaisesRegex(AssertionError,'completed cache'):validate_stages(c,owners)

    def test_stale_partial_generation_rejected(self):
        c,owners=fixture();c['footer_stage_profiles'][0]['after']['stage_generation']=2
        with self.assertRaisesRegex(AssertionError,'stale generation'):validate_stages(c,owners)

    def test_missing_and_duplicate_profiles_rejected(self):
        c,owners=fixture();c['footer_stage_profiles']=[]
        with self.assertRaisesRegex(AssertionError,'every emitted'):validate_stages(c,owners)
        c,owners=fixture();c['footer_stage_profiles'].append(copy.deepcopy(c['footer_stage_profiles'][0]))
        with self.assertRaisesRegex(AssertionError,'unique call'):validate_stages(c,owners)

    def test_return_tail_must_remain_in_owner(self):
        c,owners=fixture();c['footer_stage_profiles'][0]['exit']['cck']=101
        with self.assertRaisesRegex(AssertionError,'root owner'):validate_stages(c,owners)

    def test_excess_actual_glyph_calls_rejected(self):
        c,owners=fixture();c['stack_timing']['calls'] += [dict(callee='ui_text_character',entry=dict(cck=20+i),exit=dict(cck=21+i)) for i in range(3)]
        with self.assertRaisesRegex(AssertionError,'two actual'):validate_stages(c,owners)

    def test_missing_schema_rejected(self):
        c,owners=fixture();del c['footer_stage_profiles']
        with self.assertRaises(KeyError):validate_stages(c,owners)
