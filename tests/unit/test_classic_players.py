"""Native replacement contracts frozen from 93bb640, independently of renderer."""
import hashlib
import json
from pathlib import Path
import re
import struct
import unittest

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = json.loads((ROOT/'docs/sprites/native-contract.json').read_text())
LAYOUT = json.loads((ROOT/'docs/sprites/score-layout-contract.json').read_text())


def poses(name):
    return list(struct.iter_unpack('>HHHbb', (ROOT/f'assets/native/scene/{name}.bin').read_bytes()))


def pixels(data, offset):
    return {(x, y) for y in range(16) for x in range(16)
            if struct.unpack_from('>H', data, offset+4*y)[0] & (1 << (15-x))}


class ClassicPlayers(unittest.TestCase):
    def test_all_poses_share_retained_racket_and_anchor_geometry(self):
        human, robot = poses('poses'), poses('robot-poses')
        self.assertEqual(len(human), 14)
        self.assertEqual(len(robot), 14)
        for h, r in zip(human, robot):
            self.assertEqual((h[0], h[3], h[4]), (r[0], r[3], r[4]))
        for name in ('poses', 'animations'):
            self.assertEqual(hashlib.sha256((ROOT/f'assets/native/scene/{name}.bin').read_bytes()).hexdigest(),
                             CONTRACT[name+'_sha256'])

    def test_exact_two_plane_monochrome_encoding_and_all_body_bounds(self):
        atlas = (ROOT/'assets/native/scene/sprite-images.bin').read_bytes()
        self.assertEqual(len(atlas), 8192+3072)
        for offset in range(0, len(atlas), 128):
            for y in range(16):
                a, b, c, d = (*struct.unpack_from('>HH', atlas, offset+4*y),
                              *struct.unpack_from('>HH', atlas, offset+64+4*y))
                self.assertEqual((b, c), (0, 0))
                self.assertEqual(a, d)
        for h, r in zip(poses('poses'), poses('robot-poses')):
            for old, new in zip(h[1:3], r[1:3]):
                left, top, right, bottom = CONTRACT['body_bounds'][str(old)]
                for off in (old, new):
                    px = pixels(atlas, off)
                    self.assertTrue(px)
                    self.assertTrue(all(left <= x < right and top <= y < bottom for x, y in px))
                    self.assertEqual((min(x for x,y in px), min(y for x,y in px),
                                      max(x for x,y in px)+1, max(y for x,y in px)+1),
                                     (left, top, right, bottom))
            self.assertNotEqual(atlas[h[1]:h[1]+128]+atlas[h[2]:h[2]+128],
                                atlas[r[1]:r[1]+128]+atlas[r[2]:r[2]+128])
        for off, digest in CONTRACT['retained_rackets'].items():
            off = int(off)
            self.assertEqual(hashlib.sha256(atlas[off:off+128]).hexdigest(), digest)

    def test_physics_and_frozen_replay_are_unchanged(self):
        for path, digest in CONTRACT['unchanged_physics'].items():
            data = (ROOT/path).read_bytes()
            if path == 'amiga/game/gameplay_contact.s':
                # Only the two observation calls may differ from the frozen
                # physics source. Native CPU proofs guard their side effects.
                for hook in (b'        bsr     game_history_contact_begin\n',
                             b'        bsr     game_history_contact\n'):
                    self.assertEqual(data.count(hook),1)
                    data = data.replace(hook,b'')
            if path == 'amiga/game/gameplay_players.s':
                hooked = b'        bsr     game_random_launch\n        bsr     game_history_serve\n        rts'
                self.assertEqual(data.count(hooked),1)
                data = data.replace(hooked,b'        bra     game_random_launch')
            self.assertEqual(hashlib.sha256(data).hexdigest(), digest, path)

    def test_a_b_labels_fit_font_and_court_bounds(self):
        source = (ROOT/'amiga/game/interface_text.s').read_text()
        font = (ROOT/'assets/native/title/font.bin').read_bytes()
        strings = re.findall(r"dc.b '([^']*)'", source)
        for value in strings:
            self.assertLessEqual(len(value), 28, value)
            for char in set(value)-{' '}:
                self.assertTrue(any(font[ord(char)*8:ord(char)*8+8]), char)
        self.assertNotRegex(source, r"'(?:DEMO - )?(?:BLUE|RED) WINS")
        self.assertIn("ui_a_compact: dc.b 'WASD / F',0", source)
        self.assertIn("ui_b_compact: dc.b 'Cursor keys / .',0", source)
        self.assertNotRegex(source, r"'[^']*P[12][^']*'")
        for name in ('ui_demo_selector', 'ui_tally_text', 'ui_ai_tally_text'):
            block=source[source.index(name+':'):].splitlines()
            joined=''
            for line in block:
                joined+=''.join(re.findall(r"dc.b '([^']*)'", line))
                if line.rstrip().endswith(',0'):break
            self.assertLessEqual(len(joined),28,(name,joined))
        planes = [(ROOT/f'assets/native/court/plane{n}.bin').read_bytes() for n in range(4)]
        for n,plane in enumerate(planes):
            for left in (16,224):
                block=b''.join(plane[y*32+left//8:y*32+left//8+2] for y in range(16,32))
                self.assertEqual(hashlib.sha256(block).hexdigest(), CONTRACT['ab_headers'][str(n)][str(left)])

    def test_residual_logo_cleared_and_unrelated_court_preserved(self):
        atlas=(ROOT/'assets/native/scene/sprite-images.bin').read_bytes()
        self.assertEqual(atlas[28*128:31*128],bytes(3*128))
        for n in range(4):
            plane=(ROOT/f'assets/native/court/plane{n}.bin').read_bytes()
            for y in range(139,144):
                for x in range(8,39):
                    self.assertFalse(plane[y*32+x//8] & (128>>(x%8)))
            # Mask the exact authorized logo/scoreboard regions when verifying
            # unrelated court pixels against the independently frozen base.
            masked=bytearray(plane)
            for left,top,right,bottom in [[0,32,48,124],[208,32,256,124],[8,139,39,144]]:
                for y in range(top,bottom):
                    for x in range(left,right):masked[y*32+x//8]&=~(128>>(x%8))
            self.assertEqual(hashlib.sha256(masked).hexdigest(), LAYOUT['court_outside_layout_sha256'][str(n)])


if __name__ == '__main__':
    unittest.main()
