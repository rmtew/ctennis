import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from predictor_native_proof import InputTrace


class InputProbeTests(unittest.TestCase):
    def probe(self,hold=400,include_matrix=True,include_sample=True):
        p=InputTrace(dict(game_keyboard_matrix=1000,tutorial_packet=2000))
        rows=[(0xbfed01,0,'read',1),(0xbfee01,64,'write',20),(0xbfee01,0,'write',20+hold),
              (0xbfed01,0,'read',600)]
        if include_matrix:rows.append((1034,1,'write',10))
        if include_sample:rows.append((2000,1,'write',15))
        for a,v,access,cck in sorted(rows,key=lambda r:r[3]):
            p.observe(dict(method='event.mmio',params=dict(addr=a,value=v,size=1,access=access,position=dict(cck=cck))))
        return p

    def action(self):return dict(rawkey=0x22,held=True,tutorial_active=True,position=dict(cck=5))
    def test_literal_reception_and_nominal_sample_are_distinct(self):
        result=self.probe().result([self.action()])
        self.assertEqual(result['minimum_ack_hold_cck'],400)
        self.assertEqual(result['transitions'][0]['input_to_matrix_cck'],5)
        self.assertEqual(result['transitions'][0]['matrix_to_sample_cck'],5)
    def test_short_ack_cannot_count_as_pass(self):
        with self.assertRaises(AssertionError):self.probe(hold=349).result([self.action()])
    def test_absent_matrix_transition_cannot_count_as_input(self):
        with self.assertRaises(AssertionError):self.probe(include_matrix=False).result([self.action()])
    def test_matrix_only_cannot_count_as_nominal_response(self):
        with self.assertRaises(AssertionError):self.probe(include_sample=False).result([self.action()])
    def test_later_press_cannot_satisfy_an_earlier_unsampled_press(self):
        p=self.probe(include_sample=False)
        p.observe(dict(method='event.mmio',params=dict(addr=2000,value=1,size=1,access='write',position=dict(cck=50))))
        released=dict(self.action(),held=False,position=dict(cck=30))
        with self.assertRaises(AssertionError):p.result([self.action(),released])


if __name__=='__main__':unittest.main()
