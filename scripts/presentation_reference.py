"""Verify captured source pixels against captured VDP state, never generate an oracle.

Test-side hardware decoding follows MAME mame0289 tms9928a.cpp. This is not a
gameplay analogue or a production SG-to-Amiga rendering layer.
Primary source: https://github.com/mamedev/mame/blob/mame0289/src/devices/video/tms9928a.cpp
MAME TMS implementation is BSD-3-Clause, credited to Sean Young, Nathan Woods,
Aaron Giles, Wilbert Pol and hap. The captured emulator pixels remain the oracle.
"""
import hashlib
import configparser
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ACTIVE_AREA = (12, 12, 268, 204)
FIELDS = {
    'point_a': (16, 40, 32, 56), 'point_b': (224, 40, 240, 56),
    'games_a': (16, 72, 32, 120), 'games_b': (224, 72, 240, 120),
    'status': (112, 96, 136, 104), 'mode': (208, 144, 248, 152),
}
RECORDS = {'point_a': (0x0816, 4), 'point_b': (0x0816, 4),
           'games_a': (0x07B1, 12), 'games_b': (0x07B1, 12),
           'status': (0x0725, 3), 'mode': (0x07A2, 5)}
# Pinned MAME palette, independent of the chosen Amiga 12-bit palette.
PALETTE = ((0, 0, 0), (0, 0, 0), (33, 200, 66), (94, 220, 120),
           (84, 85, 237), (125, 118, 252), (212, 82, 77), (66, 235, 245),
           (252, 85, 84), (255, 121, 120), (212, 193, 84), (230, 206, 128),
           (33, 176, 59), (201, 91, 186), (204, 204, 204), (255, 255, 255))


def decode_vdp(vram, regs):
    """Decode a captured, static Graphics II state for an independent cross-check."""
    if len(vram) != 16384 or len(regs) != 8:
        raise ValueError('Incomplete VDP state')
    backdrop = regs[7] & 15
    colours = bytearray([backdrop]) * (256 * 192)
    if not regs[1] & 0x40:
        return rgb_image(colours)
    mode = (regs[0] & 2) | ((regs[1] & 0x10) >> 4) | ((regs[1] & 8) >> 1)
    if mode != 2:
        raise ValueError(f'Unobserved graphics mode: {mode}')
    names, patterns, table = regs[2] * 1024, (regs[4] & 4) * 2048, (regs[3] & 128) * 64
    colour_mask = ((regs[3] & 127) << 3) | 7
    pattern_mask = ((regs[4] & 3) << 8) | (colour_mask & 255)
    for y in range(192):
        for column in range(32):
            code = vram[names + (y >> 3) * 32 + column] + ((y >> 6) << 8)
            bits = vram[patterns + ((code & pattern_mask) << 3) + (y & 7)]
            colour = vram[table + ((code & colour_mask) << 3) + (y & 7)]
            foreground, background = colour >> 4 or backdrop, colour & 15 or backdrop
            for bit in range(8):
                colours[y * 256 + column * 8 + bit] = foreground if bits & (128 >> bit) else background
    attributes, sprites = regs[5] * 128, regs[6] * 2048
    size, magnification = (16 if regs[1] & 2 else 8), (2 if regs[1] & 1 else 1)
    for y in range(192):
        drawn, count = set(), 0
        for slot in range(32):
            sy, sx, pattern, flags = vram[attributes + slot * 4:attributes + slot * 4 + 4]
            if sy == 208:
                break
            sy = (sy - 256 if sy > 224 else sy) + 1
            if not sy <= y < sy + size * magnification:
                continue
            count += 1
            if count > 4:
                break
            if flags & 128:
                sx -= 32
            row = (y - sy) // magnification
            address = sprites + (pattern & ~3 if size == 16 else pattern) * 8 + row
            for x in range(size):
                bits = vram[address + (16 if x >= 8 else 0)]
                if not bits & (128 >> (x & 7)) or not flags & 15:
                    continue
                for duplicate in range(magnification):
                    px = sx + x * magnification + duplicate
                    if 0 <= px < 256 and px not in drawn:
                        colours[y * 256 + px] = flags & 15
                        drawn.add(px)
    return rgb_image(colours)


def rgb_image(indices):
    return Image.frombytes('RGB', (256, 192), bytes(channel for index in indices for channel in PALETTE[index]))


def verify_capture(case, directory=None):
    directory = directory or ROOT / f'build/tests/{case}-presentation'
    manifest = json.loads((directory / 'manifest.json').read_text())
    parent_path = ROOT / f'tests/reference/{case}.json'
    if hashlib.sha256(parent_path.read_bytes()).hexdigest() != manifest['parent_reference_sha256']:
        raise ValueError('Presentation parent reference changed')
    if not manifest['repeat_identical'] or not manifest['observer_preserved_callback_capture']:
        raise ValueError('Unverified presentation capture')
    samples = manifest['samples']
    parent = json.loads(parent_path.read_text())
    decoded = {}
    for sample in samples:
        for run in ('a', 'b'):
            stem = directory / run / f"f{sample['frame']:05d}"
            for suffix, expected in sample['hardware_sha256'].items():
                if hashlib.sha256(stem.with_suffix('.' + suffix).read_bytes()).hexdigest() != expected:
                    raise ValueError(f'Captured source media changed: {stem}.{suffix}')
            with Image.open(stem.with_suffix('.png')) as image:
                if list(image.size) != sample['size'] or hashlib.sha256(image.convert('RGB').tobytes()).hexdigest() != sample['rgb_sha256']:
                    raise ValueError(f'Captured source image changed: {stem}')
        stem = directory / 'a' / f"f{sample['frame']:05d}"
        decoded[sample['frame']] = decode_vdp(stem.with_suffix('.vram').read_bytes(), stem.with_suffix('.regs').read_bytes()).tobytes()
    rows = []
    for sample in samples:
        frame = sample['frame']
        stem = directory / 'a' / f'f{frame:05d}'
        with Image.open(stem.with_suffix('.png')) as image:
            observed = image.convert('RGB').crop(ACTIVE_AREA).tobytes()
        matches = [candidate for candidate in range(frame - 4, frame + 5)
                   if decoded.get(candidate) == observed]
        rows.append({'frame': frame, 'matching_captured_vdp_frames': matches,
                     'same_frame_vdp_match': frame in matches})
    report = {'case': case, 'manifest_sha256': hashlib.sha256((directory / 'manifest.json').read_bytes()).hexdigest(),
              'samples': len(rows), 'same_frame_matches': sum(row['same_frame_vdp_match'] for row in rows),
              'unmatched_frames': [row['frame'] for row in rows if not row['matching_captured_vdp_frames']],
              'raster_vdp_associations': rows,
              'unmatched_named_checkpoints': {name: frame for name, frame in manifest['named_frames'].items()
                                             if frame in {row['frame'] for row in rows if not row['matching_captured_vdp_frames']}},
              'scope': 'independent captured-pixel/static-hardware-state cross-check; transition scanout may straddle writes'}
    report['field_checkpoints'] = field_checkpoints(directory, manifest, parent)
    (directory / 'raster-validation.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def field_checkpoints(directory, manifest, parent):
    """Find the first captured display of ROM glyphs selected by observed source state."""
    config = configparser.ConfigParser(interpolation=None)
    config.read(ROOT / 'config.local.ini', encoding='utf-8')
    cartridge = Path(config['inputs']['cartridge']).read_bytes()
    if hashlib.sha256(cartridge).hexdigest() != parent['rom_sha256']:
        raise ValueError('Unexpected reference cartridge')
    observed, hardware = {}, {}
    for sample in manifest['samples']:
        frame = sample['frame']
        stem = directory / 'a' / f'f{frame:05d}'
        with Image.open(stem.with_suffix('.png')) as image:
            observed[frame] = image.convert('RGB').crop(ACTIVE_AREA)
        vram, regs = stem.with_suffix('.vram').read_bytes(), stem.with_suffix('.regs').read_bytes()
        hardware[frame] = (vram, regs, decode_vdp(vram, regs))
    results = {}
    for name, frame in manifest['named_frames'].items():
        selected = manifest.get('field_requests', {}).get(name, {})
        if selected:
            pass
        elif name.startswith('point-codes-'):
            a, b = map(int, name.removeprefix('point-codes-').split('-'))
            selected = {'point_a': a, 'point_b': b}
        elif name.startswith('status-'):
            selected = {'status': 0 if name.endswith('-disappears') else int(name.split('-')[1])}
        elif name in ('accepted-mode', 'first_game_award', 'match_award', 'restart_gameplay', 'restart_serve_flight'):
            ordinal = manifest.get('trigger_updates', {}).get(name)
            if ordinal is None:
                ordinal = parent['milestones'].get(name, {}).get('update', 0)
            ram = bytes.fromhex(parent['updates'][ordinal - 1]['ram'] if ordinal else parent['initial_post_tail'])
            selected = dict(point_a=ram[0x3E], point_b=ram[0x3F], games_a=ram[0x40], games_b=ram[0x41],
                            mode=0 if ram[0x3D] & 4 else 2 if ram[0x3D] & 128 else 1)
        if not selected:
            continue
        window = [candidate for candidate in range(frame - 2, frame + 5) if candidate in observed]
        fields = {}
        for field, variant in selected.items():
            address, length = RECORDS[field]
            expected_tiles = cartridge[address + variant * length:address + (variant + 1) * length]
            box = FIELDS[field]
            hashes, vdp_frames = set(), []
            for candidate in window:
                vram, regs, picture = hardware[candidate]
                tiles = bytes(vram[regs[2] * 1024 + (y // 8) * 32 + x // 8]
                              for y in range(box[1], box[3], 8) for x in range(box[0], box[2], 8))
                if tiles == expected_tiles:
                    hashes.add(hashlib.sha256(picture.crop(box).tobytes()).hexdigest())
                    vdp_frames.append(candidate)
            visible = [candidate for candidate in window
                       if hashlib.sha256(observed[candidate].crop(box).tobytes()).hexdigest() in hashes]
            first = visible[0] if visible else None
            if first is not None:
                observed[first].crop(box).save(directory / f'{name}-{field}.png')
            fields[field] = {'source_variant': variant, 'expected_rom_tile_record': expected_tiles.hex(),
                             'rom_address': address + variant * length, 'source_rectangle': list(box),
                             'matching_vdp_frames': vdp_frames, 'matching_display_frames': visible,
                             'first_captured_visible_frame': first,
                             'already_visible_before_trigger': first is not None and first < frame}
        results[name] = {'trigger_frame': frame, 'fields': fields}
    return results


if __name__ == '__main__':
    for case in ('one-player-match', 'two-player-match'):
        report = verify_capture(case)
        print(case, 'samples', report['samples'], 'same-frame matches', report['same_frame_matches'],
              'unmatched', report['unmatched_frames'])
