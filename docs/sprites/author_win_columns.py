"""Offline authored UI fitting; never called by build or asset validation.

Run only on the pre-scoreboard Classic checkpoint112285c. This edits approved
native Amiga inputs, not original-platform assets or generated concept pixels.
The existing number/advantage masks are retained without their decorative hearts.
"""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
COURT = ROOT / 'assets/native/court'


def put(planes, x, y, colour):
    for n, p in enumerate(planes):
        bit = 128 >> (x % 8)
        offset = y * 32 + x // 8
        p[offset] = (p[offset] & ~bit) | (bit if colour & (1 << n) else 0)


def main():
    contract = json.loads((ROOT / 'docs/sprites/native-contract.json').read_text())
    planes = [bytearray((COURT / f'plane{n}.bin').read_bytes()) for n in range(4)]
    glyphs = []
    for variant in range(7):
        old = (COURT / f'score_bank_point_a_{variant}_p2.bin').read_bytes()
        mask = b''.join(old[y*32+2:y*32+4] for y in range(16))
        assert hashlib.sha256(mask).hexdigest() == contract['plain_point_masks'][str(variant)]
        glyphs.append(mask)
    for left, top, right, bottom in contract['scoreboard_rectangles']:
        for y in range(top, bottom):
            for x in range(left, right):
                put(planes, x, y, 0)
    font = (ROOT / 'assets/native/title/font.bin').read_bytes()
    win = set()
    cursor = 0
    for char in 'WIN':
        pixels = {(x, y) for y in range(8) for x in range(8)
                  if font[ord(char)*8+y] & (128 >> x)}
        left = min(x for x, y in pixels)
        right = max(x for x, y in pixels)
        win.update((cursor + x-left, y) for x, y in pixels)
        cursor += right-left+2
    assert cursor-1 == 15
    for offset, ghost in ((0, 6), (208, 3)):
        for x in range(12+offset, 37+offset):
            put(planes, x, 68, 15)
        for y in range(69, 124):
            for x in (12+offset, 36+offset):
                put(planes, x, y, 15)
        for row in range(6):
            for x, y in win:
                put(planes, 17+offset+x, 72+8*row+y, ghost)
    for offset, colour in ((0, 4), (208, 13)):
        mask = glyphs[0]
        for y in range(16):
            for x in range(16):
                if mask[y*2+x//8] & (128 >> (x%8)):
                    put(planes, 16+offset+x, 40+y, colour)
    for n, plane in enumerate(planes):
        (COURT / f'plane{n}.bin').write_bytes(plane)
    for side, offset in (('a', 0), ('b', 208)):
        for variant, mask in enumerate(glyphs):
            point = [bytearray(p[40*32:56*32]) for p in planes]
            for y in range(16):
                for x in range(16):
                    on = bool(mask[y*2+x//8] & (128 >> (x%8)))
                    put(point, 16+offset+x, y, (4 if side == 'a' else 13) if on else 0)
            for n in (2,) if side == 'a' else (0, 2, 3):
                (COURT / f'score_bank_point_{side}_{variant}_p{n}.bin').write_bytes(point[n])
        for count in range(7):
            games = bytearray(planes[1][72*32:120*32])
            for row in range(count):
                for x, y in win:
                    xx, yy = 17+offset+x, 8*row+y
                    games[yy*32+xx//8] &= ~(128 >> (xx%8))
            (COURT / f'score_bank_games_{side}_{count}_p1.bin').write_bytes(games)
    manifest_path = ROOT / 'assets/native/manifest.json'
    manifest = json.loads(manifest_path.read_text())
    provenance = (' Plain retained point/advantage glyphs and six compact WIN rows '
        'with an open white frame are authored native UI edits; font columns are packed without '
        'resampling. No conceptual ImageGen pixels are imported into the scoreboard.')
    manifest['provenance'] = manifest['provenance'].replace(provenance, '') + provenance
    for item in manifest['files']:
        p = ROOT / item['path']
        if p.parent == COURT:
            item.update(size_bytes=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    manifest_path.write_text(json.dumps(manifest, indent=2)+'\n')


if __name__ == '__main__':
    main()
