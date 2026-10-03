"""Frozen selected-preview pixels; never generated from the native renderer.

These masks were sampled from the accepted square LED comparison before the
68000 implementation. They are test evidence, not product build inputs.
"""
import hashlib
import json
from native_tools import ROOT

CONTRACT = json.loads((ROOT/'docs/sprites/square-led-contract.json').read_text())
ORIGINAL_MASKS = tuple(bytes.fromhex(value) for value in CONTRACT['masks_hex'])
# Fixed tens/units positions, exactly as selected in the original LED preview.
# In particular, the single zero has a blank tens cell and the same units pixels
# as the zero in 30/40. The single-A advantage placement also stays unchanged.
MASKS = ORIGINAL_MASKS


def expected_point_bank(side, variant, plane):
    if (side, plane) not in (('a', 2), ('b', 2), ('b', 0), ('b', 3)) or not 0 <= variant < 7:
        raise ValueError('Unsupported native point stream')
    data = bytearray((ROOT/f'assets/native/court/plane{plane}.bin').read_bytes()[48*32:64*32])
    left = 2 if side == 'a' else 28
    for row in range(16):
        data[row*32+left:row*32+left+2] = MASKS[variant][row*2:row*2+2]
    return bytes(data)


def win_mask():
    # Independent authored placement used by native_scoreboard_raster.
    font = (ROOT/'assets/native/title/font.bin').read_bytes()
    rows = bytearray(16)
    for char, first, last, left in (('W', 0, 4, 17), ('I', 1, 3, 23), ('N', 0, 4, 27)):
        for y in range(8):
            for x in range(first, last+1):
                if font[ord(char)*8+y] & (128 >> x):
                    bit = left+x-first-16
                    rows[y*2+bit//8] |= 128 >> (bit%8)
    return bytes(rows)


def expected_hud_bank(fields):
    """Independent retained assets/pixels, not product renderer output."""
    planes = [(ROOT/f'assets/native/court/plane{p}.bin').read_bytes() for p in range(4)]
    strips = bytearray(b''.join(planes[p][48*32:64*32] for p in (0,2,3)) + planes[1][72*32:120*32])
    for field, streams, x in ((0,(512,),2), (1,(0,512,1024),28)):
        for stream in streams:
            for y in range(16):
                strips[stream+y*32+x:stream+y*32+x+2] = MASKS[fields[field]][y*2:y*2+2]
    strips[1536+24*32:1536+32*32] = (ROOT/f'assets/native/court/score_bank_status_{fields[4]}_p1.bin').read_bytes()
    mask = win_mask()
    for field,x in ((2,2),(3,28)):
        for row in range(6):
            for y in range(8):
                off = 1536+(row*8+y)*32+x
                strips[off:off+2] = bytes(2) if row < fields[field] else mask[y*2:y*2+2]
    return bytes(strips)


def assert_hud_bank(raw, located, bank, fields):
    expected = expected_hud_bank(fields)
    actual = raw(located(f'hud_bank{bank}'),len(expected))
    if actual != expected:
        raise AssertionError({'label':'native HUD strips match independent pixels', 'bank':bank,
                              'fields':fields,'different_bytes':sum(a!=b for a,b in zip(actual,expected))})
    return {'bank':bank,'fields':fields,'bytes':len(expected),'matched':True}


def assert_generated_point_banks(raw, located):
    # Retain entry name for startup receipts; representation is now six tiles.
    checks = []
    for tile,variant in enumerate((0,1,2,3,4,6)):
        actual = raw(located('hud_point_tiles')+tile*32,32)
        expected = MASKS[variant]
        if actual != expected:
            raise AssertionError({'label':'startup banks match selected square preview',
                'tile':tile,'different_bytes':sum(a!=b for a,b in zip(actual,expected))})
        checks.append({'tile':tile,'logical_variant':variant,'bytes':32,'matched':True})
    if raw(located('hud_win_tile'),16) != win_mask():
        raise AssertionError('Native WIN mask differs from independently authored font placement')
    return checks
