"""Inherited-list binding at either side of the publisher's physical strobe."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
from native_sprite_dma import SLOT, analyse


class InheritedCopperTests(unittest.TestCase):
    def capture(self, front, marker, physical, *, corrupt=False, evidence=True):
        names = ['front_copper', 'back_copper', 'ready_copper', 'spare_copper',
                 'display_ready', 'ready_completed', 'blank_seen', 'ready_generation',
                 'ready_title_display', 'simulation_updates',
                 'simulation_started_updates', 'presentation_copper', 'score_pointer_cache']
        addresses = {n: 16 + 8*i for i, n in enumerate(names)}
        banks = [1000, 2000, 3000]
        addresses.update(copperlist=1000, copperlist_back=2000, copperlist_third=3000,
                         copperlist_end=1100, sprite0=4000, sprite_back=5000,
                         sprite_third=6000, title_copper=7000)
        memory = bytearray(8000)
        for name, value in [('front_copper', banks[front]),
                            ('presentation_copper', banks[marker] if marker is not None else 7000)]:
            a = addresses[name]
            memory[a:a+4] = value.to_bytes(4, 'big')
        records = []
        for slot in range(16):
            source = banks[physical]+70+4*slot
            if corrupt and slot == 1:
                source = banks[(physical+1) % 3]+70+4*slot
            records.append(SLOT.pack(0x120+2*slot, 3 if evidence else 0,
                                     0, 2, 0, 0, source, 0, 0))
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)
            (p/'chip-ram.bin').write_bytes(memory)
            (p/'partial.bin').write_bytes(b''.join(records))
            (p/'full.bin').write_bytes(bytes(SLOT.size*16))
            (p/'profile.jsonl').write_text('\n'.join(json.dumps(dict(
                frame=i, rows=1, line_cck=16, traced=True, partial=i == 1,
                slots_file='partial.bin' if i == 1 else 'full.bin'))
                for i in (1, 2)))
            # This minimal bus fixture tests binding only; complete DMA extent
            # checks intentionally fail and are exercised by native captures.
            return analyse(p, addresses, cpu_events=[], require_three=False)

    def test_after_strobe_before_front_cleanup(self):
        result = self.capture(front=0, marker=1, physical=1)
        self.assertEqual(result['inherited_binding']['bank'], 1)
        self.assertFalse(any('installed completed list' in f['reason'] for f in result['failures']))

    def test_marker_before_strobe_keeps_actual_old_list(self):
        result = self.capture(front=1, marker=2, physical=1)
        self.assertEqual(result['inherited_binding']['bank'], 1)
        self.assertFalse(any('installed completed list' in f['reason'] for f in result['failures']))

    def test_inconsistent_physical_source_is_rejected(self):
        result = self.capture(front=0, marker=1, physical=1, corrupt=True)
        self.assertTrue(any('installed completed list' in f['reason'] for f in result['failures']))

    def test_ambiguous_snapshot_requires_physical_evidence(self):
        result = self.capture(front=0, marker=1, physical=1, evidence=False)
        self.assertTrue(any(f['reason'] == 'inherited physical list lacks Copper evidence'
                            for f in result['failures']))

    def test_title_retains_court_front_without_sprite_dma(self):
        result = self.capture(front=0, marker=None, physical=0, evidence=False)
        self.assertTrue(result['passed'], result['failures'])
