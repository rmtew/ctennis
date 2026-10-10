import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from coherent_write_observer import CoherentWriteObserver


class CoherentTelemetryWrites(unittest.TestCase):
    def setUp(self):
        self.symbols={name:1000+8*i for i,name in enumerate(CoherentWriteObserver.WIDTHS)}
        self.observer=CoherentWriteObserver(self.symbols)

    def row(self,name,offset,value,size=2,pc=200,cck=20):
        return dict(access='write',addr=self.symbols[name]+offset,size=size,value=value,pc=pc,position=dict(cck=cck))

    def test_low_first_timer_borrow_publishes_only_complete_value(self):
        self.assertIsNone(self.observer.observe(self.row('simulation_phase',2,0xfad8)))
        value=self.observer.observe(self.row('simulation_phase',0,3,cck=25))
        self.assertEqual(value['value'],0x3fad8)
        self.assertEqual(value['position']['cck'],25)
        self.observer.require_complete()

    def test_high_first_job_cost_and_aggregate_counter(self):
        self.assertIsNone(self.observer.observe(self.row('tutorial_job_cost',0,0)))
        self.assertEqual(self.observer.observe(self.row('tutorial_job_cost',2,9000))['value'],9000)
        self.assertEqual(self.observer.observe(self.row('tutorial_jobs_completed',0,8,size=4))['value'],8)

    def test_word_job_kind_keeps_value(self):
        self.assertEqual(self.observer.observe(self.row('tutorial_job_kind',0,7))['value'],7)

    def test_mixed_guest_instructions_cannot_form_value(self):
        self.observer.observe(self.row('simulation_phase',2,7))
        with self.assertRaisesRegex(ValueError,'Incomplete long store'):
            self.observer.observe(self.row('simulation_phase',0,1,pc=202))

    def test_final_partial_store_fails(self):
        self.observer.observe(self.row('tutorial_job_cost',0,0))
        with self.assertRaisesRegex(AssertionError,'Incomplete scheduler long'):
            self.observer.require_complete()


if __name__=='__main__':unittest.main()
