"""Helper observation lifecycles; gameplay remains actual-core proof scope."""
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from preview_native_proof import seek_preserving_ledger


class NativeSeekLedgerTests(unittest.TestCase):
    def test_seek_keeps_existing_ledger_and_passes_full_cursor(self):
        interrupted=['existing-output'];events=[interrupted];calls=[]
        def call(name,args):
            calls.append((name,args));events.append(['observed-seek-intent']);return 123
        def forbidden_clear():raise AssertionError('Interrupted ledger was cleared')
        cpu=SimpleNamespace(call=call,cpu=SimpleNamespace(r_reg=lambda register:1),
            events=events,clear_events=forbidden_clear)
        self.assertEqual(seek_preserving_ledger(cpu,0x123456789abcdef0),123)
        self.assertIs(cpu.events,events)
        self.assertIs(cpu.events[0],interrupted)
        self.assertEqual(cpu.events,[interrupted,['observed-seek-intent']])
        self.assertEqual(calls,[('game_history_seek',{0:0x12345678,1:0x9abcdef0})])

    def test_rejected_seek_keeps_interrupted_ledger(self):
        events=[['existing-output']]
        cpu=SimpleNamespace(call=lambda name,args:123,cpu=SimpleNamespace(r_reg=lambda register:0),events=events)
        with self.assertRaisesRegex(AssertionError,'seek rejected'):seek_preserving_ledger(cpu,64)
        self.assertIs(cpu.events,events)
        self.assertEqual(events,[['existing-output']])
