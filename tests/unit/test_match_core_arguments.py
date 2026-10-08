import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
from match_core_cpu import Core


class LogicalArgumentTests(unittest.TestCase):
    def core(self):
        core = Core.__new__(Core)
        core.cpu = Mock()
        registers = {}
        core.cpu.w_reg.side_effect = registers.__setitem__
        core.cpu.r_reg.side_effect = registers.__getitem__
        core.logical_calls = 0
        core.context_seed = 0
        core.call = Mock(return_value=123)
        return core

    def test_only_declared_arguments_are_supplied(self):
        core = self.core()
        self.assertEqual(core.call_logical('game_core_select', [1, 0]), 123)
        core.call.assert_called_once_with('game_core_select', {0: 0x965a0001, 1: 0x975b0000}, 2000000)
        self.assertEqual(core.cpu.w_reg.call_count, 15)
        core.cpu.w_sr.assert_called_once_with(0x2700)

    def test_context_changes_between_zero_argument_calls(self):
        core = self.core()
        core.call_logical('game_round_poll', [])
        first = core.cpu.w_reg.call_args_list[:]
        core.cpu.reset_mock()
        core.call_logical('game_tick_dispatch', [])
        self.assertNotEqual(first, core.cpu.w_reg.call_args_list)
        core.cpu.w_sr.assert_called_once_with(0x2701)
        self.assertEqual(core.call.call_args.args[1], {})

    def test_word_arguments_preserve_distinct_poisoned_upper_halves(self):
        core = self.core()
        core.call_logical('game_core_select', [1, 123])
        first = core.call.call_args.args[1]
        core.call_logical('game_core_select', [1, 123])
        second = core.call.call_args.args[1]
        for register, word in enumerate([1, 123]):
            self.assertEqual(first[register] & 65535, word)
            self.assertEqual(second[register] & 65535, word)
            self.assertNotEqual(first[register] >> 16, second[register] >> 16)
        other = self.core()
        other.context_seed = 0xa5a5a5a5
        other.call_logical('game_core_select', [1, 123])
        self.assertNotEqual(first, other.call.call_args.args[1])

    def test_bad_shape_or_nonword_rejected_before_execution(self):
        for name, arguments in [('game_round_poll', [1]), ('unknown', []),
                                ('game_core_select', [1, -1]),
                                ('game_core_select', [True, 1]),
                                ('game_core_select', [1, 65536])]:
            core = self.core()
            with self.assertRaises(ValueError):
                core.call_logical(name, arguments)
            core.call.assert_not_called()
            core.cpu.w_reg.assert_not_called()


if __name__ == '__main__':
    unittest.main()
