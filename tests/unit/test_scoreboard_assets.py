"""Authored UI fit and independent retained court/point/Copper contracts."""
import hashlib
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from native_scoreboard_raster import scoreboard_pixels, WHITE
from native_status_raster import PALETTE
from native_square_scores import MASKS, ORIGINAL_MASKS, expected_point_bank, expected_hud_bank, CONTRACT as LED_CONTRACT

CONTRACT = json.loads((ROOT / 'docs/sprites/native-contract.json').read_text())
COURT = ROOT / 'assets/native/court'


class ScoreboardAssets(unittest.TestCase):
    def test_all_counts_and_points_match_authored_pixels_without_changing_size(self):
        static = [(COURT / f'plane{n}.bin').read_bytes() for n in range(4)]
        for side, offset in (('a', 0), ('b', 208)):
            for variant in range(7):
                point = expected_point_bank(side, variant, 2)
                self.assertEqual(len(point), 512)
                plain = b''.join(point[y*32+2+offset//8:y*32+4+offset//8] for y in range(16))
                self.assertEqual(plain, MASKS[variant])
                games = expected_hud_bank([variant,variant,variant,variant,0,1])[1536:]
                self.assertEqual(len(games), 1536)
                actual = []
                for y in range(42, 124):
                    for x in range(offset, offset+48):
                        c = 0
                        for n, base in enumerate(static):
                            data, row = base, y
                            if 48 <= y < 64 and n == 2:
                                data, row = point, y-48
                            if 48 <= y < 64 and side == 'b' and n in (0, 3):
                                data, row = expected_point_bank('b', variant, n), y-48
                            if 72 <= y < 120 and n == 1:
                                data, row = games, y-72
                            c |= bool(data[row*32+x//8] & (128 >> (x%8))) << n
                        rgb = tuple(((PALETTE[c] >> s) & 15)*17 for s in (8, 4, 0))
                        actual.extend((rgb, rgb))
                self.assertEqual(actual, scoreboard_pixels(side, variant, variant), (side, variant))

    def test_static_zero_cells_match_selected_preview(self):
        for side, left, colour in (('a', 16, 4), ('b', 224, 13)):
            for n in range(4):
                data = (COURT/f'plane{n}.bin').read_bytes()
                actual = b''.join(data[y*32+left//8:y*32+left//8+2] for y in range(48, 64))
                self.assertEqual(actual, MASKS[0] if colour & (1 << n) else bytes(32))
        self.assertEqual(MASKS[3], MASKS[5])
        self.assertEqual(MASKS[6], bytes(32))
        self.assertEqual((COURT/'square-led-definitions.bin').stat().st_size, 48)
        self.assertFalse(list(COURT.glob('score_bank_point_*.bin')))

    def test_fixed_region_transitions_replace_horizontal_pointer_switches(self):
        source=(COURT/'score-cop-commands.i').read_text()
        waits=re.findall(r'dc.w \$([0-9a-f]{4}),\$fffe',source)
        self.assertEqual(waits,['4e01','5601','5c01','6c01','7401','8c01','9401','a401'])
        # Each boundary completes all pointer writes before DDF start $48;
        # the target DMA observer verifies actual contended fetch timing.
        groups=re.split(r'dc.w \$[0-9a-f]{4},\$fffe[^\n]*',source)[1:]
        self.assertEqual([len(re.findall(r'_hi:',g)) for g in groups],[4,4,3,3,1,3,3,1])
        self.assertFalse(list(COURT.glob('score_bank_games_*.bin')))
        self.assertEqual(len(re.findall(r'dc.w \$[0-9a-f]{4}',(COURT/'score-patch-tables.i').read_text())),22)

    def test_score_cell_has_equal_native_padding_and_closed_stacked_frames(self):
        layout=json.loads((ROOT/'docs/sprites/score-layout-contract.json').read_text())
        self.assertEqual([16-layout['frame_left']-1,layout['frame_right']-32,
                          layout['point_y']-layout['frame_top']-1,
                          layout['shared_divider_y']-(layout['point_y']+16)], [4]*4)
        self.assertEqual(layout['role_y'],34)
        self.assertEqual(MASKS,ORIGINAL_MASKS)
        for y in range(16):
            zero=int.from_bytes(MASKS[0][y*2:y*2+2],'big')
            self.assertEqual(zero & ~0x7f,0)  # blank tens, units at x9..15
            for variant in (2,3,5):  # 30,40,deuce40
                self.assertEqual(int.from_bytes(MASKS[variant][y*2:y*2+2],'big') & 0x7f,zero)
        for side in ('a','b'):
            for point in range(7):
                pixels=scoreboard_pixels(side,point,0)
                at=lambda x,y: pixels[((y-42)*48+x)*2]
                for y in (43,68,123):
                    for x in range(11,37):self.assertEqual(at(x,y),WHITE)
                for y in range(43,124):
                    for x in (11,36):self.assertEqual(at(x,y),WHITE)

    def test_palette_changes_are_score_only_and_match_native_copper(self):
        source = (ROOT / 'amiga/display.i').read_text()
        colours = {int(a, 16): int(b, 16) for a, b in re.findall(r'\$([0-9a-f]{4}),\$([0-9a-f]{3})\b', source)}
        self.assertEqual(tuple(colours[0x180+2*n] for n in range(16)), PALETTE)
        self.assertEqual((PALETTE[1], PALETTE[3], PALETTE[4], PALETTE[5], PALETTE[6], PALETTE[13], PALETTE[14], PALETTE[15]),
                         (0xe33, 0x333, 0x55e, 0x77f, 0x333, 0xe33, 0xccc, 0xfff))
        planes = [(COURT / f'plane{n}.bin').read_bytes() for n in range(4)]
        for y in range(192):
            for x in range(256):
                c = sum(bool(p[y*32+x//8] & (128 >> (x%8))) << n for n, p in enumerate(planes))
                if c in (1, 3, 6):
                    self.assertTrue(any(left <= x < right and top <= y < bottom
                        for left, top, right, bottom in CONTRACT['scoreboard_rectangles']), (x, y, c))


if __name__ == '__main__':
    unittest.main()
