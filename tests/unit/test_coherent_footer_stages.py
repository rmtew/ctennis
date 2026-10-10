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


def final_fixture():
    state=dict(generation=111,footer_generation=111,stage_generation=111,dirty=0,ready=0,stage=0,first=100,second=200,overlay=bytes(512).hex(),scratch=bytes(512).hex())
    request=dict(cck=10)
    commit=dict(entry=dict(cck=40),exit=dict(cck=60),bytes_written=512,generation=111,footer_generation=111)
    completion=dict(entry=dict(cck=41),position=dict(cck=61),state=state)
    witness=dict(generation=111,limit_seconds=2,physical_clock_hz=3546895,start=dict(cck=30),observed=dict(cck=70),elapsed_cck=40,completion=completion,final_state=state,final_input_request=request,caption_commit_latency_cck=51)
    c=dict(final_caption=witness,endpoints=[dict(generation=111,request=request) for _ in range(9)],footer_commit_completions=[completion],footer_stage_profiles=[dict(completed=1,exit=dict(cck=39),after=state)],stack_timing=dict(calls=[dict(callee='tutorial_background',entry=dict(cck=35),exit=dict(cck=65))]))
    return c,[commit]


class FinalCaptionTests(unittest.TestCase):
    def validate(self,c,commits):
        from coherent_footer_stages import validate_final_caption
        return validate_final_caption(c,commits)

    def test_actual_stage_copy_and_clean_readback(self):
        c,commits=final_fixture();self.assertEqual(self.validate(c,commits)['bytes_committed'],512)

    def test_no_completed_stage_is_starvation(self):
        c,commits=final_fixture();c['footer_stage_profiles']=[]
        with self.assertRaisesRegex(AssertionError,'completed actual stage'):self.validate(c,commits)

    def test_partial_copy_rejected(self):
        c,commits=final_fixture();commits[0]['bytes_written']=510
        with self.assertRaisesRegex(AssertionError,'live512'):self.validate(c,commits)

    def test_stale_generation_rejected(self):
        c,commits=final_fixture();commits[0]['footer_generation']=110
        with self.assertRaisesRegex(AssertionError,'stale generation'):self.validate(c,commits)

    def test_dirty_ready_and_partial_rejected(self):
        for field in ('dirty','ready','stage'):
            c,commits=final_fixture();c['final_caption']['final_state'][field]=1
            with self.assertRaisesRegex(AssertionError,'partial or pending'):self.validate(c,commits)

    def test_live_bytes_mismatch_rejected(self):
        c,commits=final_fixture();c['final_caption']['final_state']['overlay']=(bytes([1])*512).hex()
        with self.assertRaisesRegex(AssertionError,'differs from completed'):self.validate(c,commits)

    def test_timeout_rejected(self):
        c,commits=final_fixture();w=c['final_caption'];w['observed']['cck']=w['start']['cck']+2*w['physical_clock_hz']+1;w['elapsed_cck']=w['observed']['cck']-w['start']['cck']
        with self.assertRaisesRegex(AssertionError,'settle bound'):self.validate(c,commits)

    def test_return_tail_outside_root_rejected(self):
        c,commits=final_fixture();c['stack_timing']['calls'][0]['exit']['cck']=60
        with self.assertRaisesRegex(AssertionError,'return tail'):self.validate(c,commits)

    def test_ninth_input_and_latency_identity_rejected(self):
        c,commits=final_fixture();c['final_caption']['caption_commit_latency_cck']=50
        with self.assertRaisesRegex(AssertionError,'latency'):self.validate(c,commits)
