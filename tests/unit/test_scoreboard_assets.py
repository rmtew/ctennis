"""Authored UI fit and independent retained court/point/Copper contracts."""
import hashlib
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from native_scoreboard_raster import scoreboard_pixels
from native_status_raster import PALETTE

CONTRACT = json.loads((ROOT / 'docs/sprites/native-contract.json').read_text())
COURT = ROOT / 'assets/native/court'


class ScoreboardAssets(unittest.TestCase):
    def test_all_counts_and_points_match_authored_pixels_without_changing_size(self):
        static = [(COURT / f'plane{n}.bin').read_bytes() for n in range(4)]
        for side, offset in (('a', 0), ('b', 208)):
            for variant in range(7):
                point = (COURT / f'score_bank_point_{side}_{variant}_p2.bin').read_bytes()
                self.assertEqual(len(point), 512)
                plain = b''.join(point[y*32+2+offset//8:y*32+4+offset//8] for y in range(16))
                self.assertEqual(hashlib.sha256(plain).hexdigest(), CONTRACT['plain_point_masks'][str(variant)])
                games = (COURT / f'score_bank_games_{side}_{variant}_p1.bin').read_bytes()
                self.assertEqual(len(games), 1536)
                actual = []
                for y in range(40, 124):
                    for x in range(offset, offset+48):
                        c = 0
                        for n, base in enumerate(static):
                            data, row = base, y
                            if 40 <= y < 56 and n == 2:
                                data, row = point, y-40
                            if 40 <= y < 56 and side == 'b' and n in (0, 3):
                                data, row = (COURT / f'score_bank_point_b_{variant}_p{n}.bin').read_bytes(), y-40
                            if 72 <= y < 120 and n == 1:
                                data, row = games, y-72
                            c |= bool(data[row*32+x//8] & (128 >> (x%8))) << n
                        rgb = tuple(((PALETTE[c] >> s) & 15)*17 for s in (8, 4, 0))
                        actual.extend((rgb, rgb))
                self.assertEqual(actual, scoreboard_pixels(side, variant, variant), (side, variant))

    def test_copper_fetch_slots_and_pointer_restores_are_byte_identical(self):
        for path, digest in CONTRACT['retained_score_copper'].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(), digest, path)

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
