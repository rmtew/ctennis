"""Native report timing retains every real callback and deadline failure."""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from run_preview_native import measurement,json_value,qualify_resolver


class NativePreviewTiming(unittest.TestCase):
    def test_transition_callback_miss_and_fresh_input_are_not_excluded(self):
        rows=[dict(callback=1,entry={'cck':0},completion={'cck':40},fresh_input=False),
              dict(callback=2,entry={'cck':50},completion={'cck':111},fresh_input=True)]
        observer=SimpleNamespace(timer_start=0,timer_origin=65535,callback_rows=rows,
            api_rows=[dict(name='game_preview_step',elapsed_cck=30)],stack_min=100)
        native=SimpleNamespace(observer=observer,symbols={'game_stack_top':200})
        result=measurement(native,dict(simulation_interval_whole=10,simulation_interval_fraction=0))
        self.assertEqual(result['callback_distribution']['samples'],2)
        self.assertEqual(result['fresh_input_callback_distribution']['max_cck'],61)
        self.assertEqual(result['minimum_callback_headroom_cck'],-11)
        self.assertEqual(result['worker_distribution']['max_cck'],30)
        self.assertEqual(result['stack_bytes'],100)

    def test_replacement_resolver_budget_cannot_execute_primers(self):
        class Resolver:
            def __init__(self):self.status=1;self.calls=[]
            def number(self,name):return self.status
            def step(self,generation,budget):
                self.calls.append((generation,budget))
                if len(self.calls)==3:self.status=2 if budget==1 else 3
        native=Resolver();qualify_resolver(native,9)
        self.assertEqual(native.status,2)
        self.assertEqual(native.calls,[(9,1)]*3)
        native.status=3
        with self.assertRaisesRegex(AssertionError,'crossed PRIME'):
            qualify_resolver(native,9)

    def test_private_readback_serialization_does_not_mutate_observation(self):
        source={'selected':bytes([1,2]),'rows':[(3,bytes([4]))]}
        self.assertEqual(json_value(source),{'selected':'0102','rows':[[3,'04']]})
        self.assertEqual(source['selected'],bytes([1,2]))


if __name__=='__main__':unittest.main()
