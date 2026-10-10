"""Challenge new receipt boundaries without simulating gameplay."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from coherent_native_extent import validate_capture,negative_controls,validate_witnesses,validate_footer


def span(name,start,end,caller=None,depth=0):
    return dict(callee=name,entry=dict(cck=start),exit=dict(cck=end),
                elapsed_bus_cck=end-start,caller=caller,depth=depth)


def capture():
    import json
    policy=json.loads((Path(__file__).resolve().parents[2]/'docs/tutorial-coherent-cost-policy.json').read_text())
    return dict(input_probe=dict(maximum_keyboard_poll_gap_cck=1000),coherent_policy=dict(policy=policy),initial_admission_state=dict(simulation_interval=12000,simulation_phase=0),admission_writes=[],
        overlay_writes=[],footer_commit_samples=[],overlay_base=1000,stack_timing=dict(open_enclosing_calls=[],calls=[
        span('tutorial_background',20,80),
        span('game_preview_step_variant',30,70,'tutorial_background',1)]),
        timing=dict(callbacks=[dict(entry=dict(cck=0),completion=dict(cck=10),work_cck=10,entry_phase_cck=0,callback=1),
                               dict(entry=dict(cck=100),completion=dict(cck=110),work_cck=10,entry_phase_cck=0,callback=2)]),
        deadline_operations=[dict(position=dict(cck=40+i),operation=op) for i,op in enumerate((3,4,8))],
        scheduler_job_writes=[dict(position=dict(cck=25),field=name,value=v) for name,v in
                             (('tutorial_job_kind',1),('tutorial_job_budget',3),('tutorial_job_variant',0),('tutorial_job_cost',4000))],
        branch_boundaries=[dict(active=0,held_state=bytes(318).hex(),released_state=bytes(318).hex(),
                                cursors=bytes(16).hex(),history=bytes(72).hex())])


class CoherentExtentTests(unittest.TestCase):
    def test_prefix_retains_multiple_semantic_envelopes(self):
        result=validate_capture(capture())
        self.assertEqual(result['chunks'][0]['operations'],[3,4,8])
        self.assertEqual(result['chunks'][0]['telemetry']['tutorial_job_cost'],4000)
        self.assertEqual(result['observed_owner_by_class_budget']['1:3']['maximum_owner_cck'],60)
        self.assertFalse(result['normative_deadline_safety'])

    def test_no_optional_callback_work(self):
        c=capture();c['stack_timing']['calls'].append(span('game_preview_endpoint_try',1,5,'tutorial_tick',1))
        with self.assertRaisesRegex(AssertionError,'outside sole'):validate_capture(c)

    def test_owner_must_finish_before_next_sample(self):
        c=capture();c['stack_timing']['calls'][0]['exit']['cck']=101
        with self.assertRaisesRegex(AssertionError,'crosses mandatory'):validate_capture(c)

    def test_observed_owner_hypothesis_overrun_fails(self):
        c=capture();c['stack_timing']['calls'][0]['elapsed_bus_cck']=20001
        with self.assertRaisesRegex(AssertionError,'job cost hypothesis'):validate_capture(c)

    def test_cost_reservation_is_reconstructed(self):
        c=capture();c['admission_writes']=[dict(position=dict(cck=28),field='simulation_phase',value=8000)]
        with self.assertRaisesRegex(AssertionError,'service/margin'):validate_capture(c)

    def footer_capture(self):
        c=capture();owner=span('tutorial_background',10,250);commit=span('tutorial_footer_commit',20,240)
        c['stack_timing']['calls']=[owner,commit]
        c['footer_commit_samples']=[dict(position=dict(cck=21),generation=7,footer_generation=7,staged=bytes(512).hex())]
        c['overlay_writes']=[dict(position=dict(cck=30+i,vpos=235),addr=1000+4*i,size=4,value=0,tutorial_active=True) for i in range(128)]
        return c,[(0,owner)]

    def test_footer_commit_full_bytes_outside_fetch(self):
        c,owners=self.footer_capture()
        self.assertEqual(validate_footer(c,owners)[0]['bytes_written'],512)

    def test_footer_dma_write_fails(self):
        c,owners=self.footer_capture();c['overlay_writes'][31]['position']['vpos']=236
        with self.assertRaisesRegex(AssertionError,'DMA fetch'):validate_footer(c,owners)

    def test_footer_missing_byte_fails(self):
        c,owners=self.footer_capture();c['overlay_writes'].pop()
        with self.assertRaisesRegex(AssertionError,'staged512'):validate_footer(c,owners)

    def test_stale_footer_write_fails(self):
        c,owners=self.footer_capture();c['footer_commit_samples'][0]['footer_generation']=6
        with self.assertRaisesRegex(AssertionError,'Stale footer'):validate_footer(c,owners)

    def test_keyboard_poll_gap_uses_finite_policy(self):
        c=capture();c['input_probe']['maximum_keyboard_poll_gap_cck']=50001
        with self.assertRaisesRegex(AssertionError,'Keyboard poll gap'):validate_capture(c)

    def test_private_release_challenge(self):
        self.assertEqual(negative_controls(capture()),['retained-private-ownership-record-rejected'])

    def test_root_counter_coincidence_is_insufficient(self):
        c=capture();root=span('game_launch_root',40,50)
        c['stack_timing']['calls'].append(root)
        witness=dict(owner=c['stack_timing']['calls'][0],roots=[root],launches=[dict(position=dict(cck=60))])
        c['dispatch_samples']=[]
        with self.assertRaisesRegex(AssertionError,'causal accepted'):validate_witnesses(c,[witness])

    def test_indirect_root_with_complete_contact_dispatch_witness(self):
        c=capture();root=span('game_launch_root',40,50,'(a1)',3)
        c['stack_timing']['calls'].extend([root,span('game_preview_dispatch',35,65),span('game_history_contact',51,62)])
        c['dispatch_samples']=[dict(position=dict(cck=35),private_state=bytes(318).hex())]
        witness=dict(owner=c['stack_timing']['calls'][0],roots=[root],launches=[dict(position=dict(cck=60))])
        validate_witnesses(c,[witness])


if __name__=='__main__':unittest.main()
