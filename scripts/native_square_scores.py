"""Frozen selected-preview pixels; never generated from the native renderer.

These masks were sampled from the accepted square LED comparison before the
68000 implementation. They are test evidence, not product build inputs.
"""
import hashlib
import json
from native_tools import ROOT

CONTRACT = json.loads((ROOT/'docs/sprites/square-led-contract.json').read_text())
ORIGINAL_MASKS = tuple(bytes.fromhex(value) for value in CONTRACT['masks_hex'])
LAYOUT = json.loads((ROOT/'docs/sprites/score-layout-contract.json').read_text())
# The follow-up layout centres the unchanged selected segment shapes. These
# authored translations are independent of the assembly's alignment table.
MASKS = tuple(b''.join((int.from_bytes(mask[y*2:y*2+2], 'big') << -shift).to_bytes(2, 'big')
                      for y in range(16))
              for mask,shift in zip(ORIGINAL_MASKS, LAYOUT['point_mask_x_shifts']))


def expected_point_bank(side, variant, plane):
    if (side, plane) not in (('a', 2), ('b', 2), ('b', 0), ('b', 3)) or not 0 <= variant < 7:
        raise ValueError('Unsupported native point stream')
    data = bytearray((ROOT/f'assets/native/court/plane{plane}.bin').read_bytes()[48*32:64*32])
    left = 2 if side == 'a' else 28
    for row in range(16):
        data[row*32+left:row*32+left+2] = MASKS[variant][row*2:row*2+2]
    return bytes(data)


def assert_generated_point_banks(raw, located):
    checks = []
    for side, plane in (('a', 2), ('b', 2), ('b', 0), ('b', 3)):
        for variant in range(7):
            name = f'score_bank_point_{side}_{variant}_p{plane}'
            actual = raw(located(name), 512)
            expected = expected_point_bank(side, variant, plane)
            if actual != expected:
                raise AssertionError({'label': 'startup banks match selected square preview',
                    'bank': name, 'different_bytes': sum(a != b for a, b in zip(actual, expected))})
            checks.append({'bank': name, 'bytes': len(actual),
                           'sha256': hashlib.sha256(actual).hexdigest(), 'matched': True})
    return checks
