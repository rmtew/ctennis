import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from native_run_slices import drain_target,goal_reached


class NativeRunSlices(unittest.TestCase):
    def test_intermediate_target_does_not_finish_original_goal(self):
        target=drain_target(10000,200000,3546895)
        self.assertEqual(target,13547)
        self.assertFalse(goal_reached(dict(cck=target,reason='target'),target,200000))
        self.assertTrue(goal_reached(dict(cck=200000,reason='target'),200000,200000))

    def test_pc_interrupt_retains_original_goal(self):
        first=drain_target(10000,20000,3546895)
        stop=dict(cck=10017,reason='breakpoint')
        self.assertFalse(goal_reached(stop,first,20000))
        self.assertEqual(drain_target(stop['cck'],20000,3546895),13564)

    def test_pal_ntsc_long_advances_reach_exact_goal_with_bounded_drains(self):
        for clock in (3546895,3579545):
            current=0;goal=clock;count=0;maximum=(clock+999)//1000
            while True:
                target=drain_target(current,goal,clock)
                self.assertLessEqual(target-current,maximum)
                self.assertLessEqual(target,goal)
                stop=dict(cck=target,reason='target');count+=1
                if goal_reached(stop,target,goal):break
                current=stop['cck']
            self.assertEqual(target,goal)
            self.assertLessEqual(count,1000)

    def test_final_provider_rounding_keeps_existing_target_completion_contract(self):
        # Final target stop may report the preceding integer CCK because its
        # seconds conversion is fractional; it still reached the requested goal.
        self.assertTrue(goal_reached(dict(cck=19999,reason='target'),20000,20000))
        self.assertFalse(goal_reached(dict(cck=19999,reason='breakpoint'),20000,20000))


if __name__=='__main__':unittest.main()
