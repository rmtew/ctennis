"""Synthetic policy/source checks; no CPU execution or gameplay model."""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from preview_extended_proof import HumanLaunchTransition, validate_edited_source


class ContinuationOracle(unittest.TestCase):
    def transition(self, physical_end=0):
        seen=[]
        cpu=SimpleNamespace(instruction=seen.append,cpu=SimpleNamespace(r_reg=lambda register:physical_end))
        return HumanLaunchTransition(cpu,{'game_history_contact':100,'game_history_serve':200},0),seen

    def test_original_hook_switches_only_after_complete_dispatch(self):
        transition,seen=self.transition()
        transition.before('game_tick_dispatch')
        transition.observe(100)
        self.assertFalse(transition.launched)
        self.assertEqual(seen,[100])
        transition.after('game_tick_dispatch')
        transition.before('game_ball_tick')
        self.assertTrue(transition.launched)

    def test_premature_ball_and_delayed_dispatch_are_rejected(self):
        transition,_=self.transition()
        with self.assertRaisesRegex(AssertionError,'before actual human launch'):
            transition.before('game_ball_tick')
        transition.observe(200);transition.after('game_tick_dispatch')
        for name in ('game_tick_dispatch','game_round_poll','game_core_sample_pads'):
            with self.subTest(name=name),self.assertRaisesRegex(AssertionError,'after actual human launch'):
                transition.before(name)

    def test_opponent_hook_does_not_authorize_human_outgoing(self):
        transition,seen=self.transition(1)
        transition.observe(100);transition.after('game_tick_dispatch')
        self.assertEqual(seen,[100])
        self.assertFalse(transition.launched)
        with self.assertRaises(AssertionError):transition.before('game_ball_tick')

    def test_launch_must_return_from_its_actual_dispatcher(self):
        transition,_=self.transition()
        transition.observe(100)
        with self.assertRaisesRegex(AssertionError,'outside its complete dispatcher'):
            transition.after('game_core_sample_pads')

    def test_complete_recorded_source_allows_only_requested_xy(self):
        source=bytes(range(159))*2
        edited=bytearray(source);edited[3]=120;edited[2]=31
        observation=dict(end=0,x=120,y=31,result=dict(kind=1,incoming_state=source,edited=bytes(edited)))
        symbols={'game_core_state':0,'game_play_state':0}
        self.assertEqual(validate_edited_source(observation,symbols,source),bytes(edited))
        for change in ('cache','edited','both'):
            changed=bytearray(source);changed[200]^=1
            altered=bytearray(edited);altered[200]^=1
            observation['result'].update(incoming_state=bytes(changed) if change in ('cache','both') else source,
                edited=bytes(altered) if change in ('edited','both') else bytes(edited))
            with self.subTest(change=change),self.assertRaises(AssertionError):
                validate_edited_source(observation,symbols,source)
