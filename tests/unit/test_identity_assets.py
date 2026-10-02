"""Intentional CT12 pixel expectations authored from text/font, not runtime goldens."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]


def indices(paths,height):
    ps=[p.read_bytes() for p in paths]
    return [[sum(((p[y*32+x//8]>>(7-x%8))&1)<<n for n,p in enumerate(ps))
             for x in range(256)] for y in range(height)]


class IdentityAssets(unittest.TestCase):
    def test_complete_fields_spell_out_labels_and_restore_blank(self):
        font=(ROOT/'assets/native/title/font.bin').read_bytes()
        for variant,label in enumerate(('', 'IN', 'OUT', 'NET', 'ACE', 'FAULT', 'DOUBLE FAULT')):
            actual=indices([ROOT/f'assets/native/court/score_bank_status_{variant}_p{p}.bin' for p in range(4)],8)
            expected=[[0]*256 for _ in range(8)]
            left=(256-len(label)*8)//2
            for column,char in enumerate(label):
                for row in range(8):
                    for bit in range(8):
                        if font[ord(char)*8+row]&(128>>bit):expected[row][left+column*8+bit]=15
            self.assertEqual(actual,expected,('status',label))
        for variant in range(3):
            actual=indices([ROOT/f'assets/native/court/score_bank_mode_{variant}_p{p}.bin' for p in range(4)],8)
            expected=[[0]*256 for _ in range(8)]
            for label,left in (('HUMAN',6),('HUMAN',214) if variant==2 else ('AI',226)):
                for column,char in enumerate(label):
                    for row in range(8):
                        for bit in range(8):
                            if font[ord(char)*8+row]&(128>>bit):expected[row][left+column*8+bit]=15
            self.assertEqual(actual,expected,('centred controller roles',variant))

    def test_red_point_glyphs_keep_exact_existing_advantage_shapes(self):
        for v in range(7):
            actual=indices([ROOT/f'assets/native/court/score_bank_point_b_{v}_p{p}.bin' if p in (0,2,3)
                            else ROOT/'assets/native/court/plane1.bin' for p in range(4)],16)
            # plane1 above is court row0, which is blank, as is this score region.
            glyph=(ROOT/f'assets/native/court/score_bank_point_b_{v}_p2.bin').read_bytes()
            for y in range(16):
                for x in range(224,240):
                    if glyph[y*32+x//8]&(128>> (x%8)):
                        self.assertEqual(actual[y][x],13,(v,x,y))

    def test_native_font_needs_no_new_glyphs(self):
        font=(ROOT/'assets/native/title/font.bin').read_bytes()
        for c in set('BASELINE RALLYFAULTDOUBLE1 PLAYER2 PLAYERS')-{' '}:
            self.assertTrue(any(font[ord(c)*8:ord(c)*8+8]),c)
