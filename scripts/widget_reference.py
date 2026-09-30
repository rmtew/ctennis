"""Find verified original, unobscured widget rasters in the frozen P1 media."""
import configparser
import hashlib
import json
from pathlib import Path
from PIL import Image
from presentation_reference import ROOT, ACTIVE_AREA, PALETTE, RECORDS
from run_amiga_score_copper_probe import FIELDS, source_pixel
from run_presentation_tests import digest

CASES = tuple('p1-widget-' + field.name.replace('_', '-') for field in FIELDS)


def catalog():
    policy = json.loads((ROOT / 'tests/cases/widgets.json').read_text())
    root = ROOT / 'tests/reference/presentation'
    frozen = json.loads((root / 'manifest.json').read_text())
    if not frozen['source_media_checks_passed'] or frozen['recipe_sha256'] != digest(ROOT / 'tests/cases/presentation.json'):
        raise ValueError('Frozen source media contract changed')
    config = configparser.ConfigParser(interpolation=None)
    config.read(ROOT / 'config.local.ini', encoding='utf-8')
    rom = Path(config['inputs']['cartridge']).read_bytes()
    result = {field.name: {} for field in FIELDS}
    for case, entry in frozen['references'].items():
        mp, vp = root / entry['manifest'], root / entry['validation']
        if digest(mp) != entry['manifest_sha256'] or digest(vp) != entry['validation_sha256']:
            raise ValueError('Source raster associations changed')
        manifest, validation = json.loads(mp.read_text()), json.loads(vp.read_text())
        parent = json.loads((ROOT / f'tests/reference/{case}.json').read_text())
        if hashlib.sha256(rom).hexdigest() != parent['rom_sha256'] or digest(ROOT / f'tests/reference/{case}.json') != manifest['parent_reference_sha256']:
            raise ValueError('Source cartridge/parent changed')
        samples = {s['frame']: s for s in manifest['samples']}
        for assoc in validation['raster_vdp_associations']:
            pf = assoc['frame']
            for vf in assoc['matching_captured_vdp_frames']:
                stem = mp.parent / f'f{vf:05d}'
                for suffix in ('vram', 'regs'):
                    if digest(stem.with_suffix('.' + suffix)) != samples[vf]['hardware_sha256'][suffix]:
                        raise ValueError('Captured source hardware changed')
                vram, regs = stem.with_suffix('.vram').read_bytes(), stem.with_suffix('.regs').read_bytes()
                if not regs[1] & 64:
                    continue
                for field in FIELDS:
                    address, length = RECORDS[field.name]
                    if field.tiles != rom[address:address + field.count * length]:
                        raise ValueError('Native field definitions differ from original tile records')
                    tiles = bytes(vram[regs[2] * 1024 + (y // 8) * 32 + x // 8]
                                  for y in range(field.y, field.y + field.height, 8)
                                  for x in range(field.x, field.x + field.width, 8))
                    for value in policy['required_variants'][field.name]:
                        if value in result[field.name] or tiles != rom[address + value * length:address + (value + 1) * length]:
                            continue
                        path = mp.parent / f'f{pf:05d}.png'
                        with Image.open(path) as picture:
                            rgb = picture.convert('RGB')
                        if hashlib.sha256(rgb.tobytes()).hexdigest() != samples[pf]['rgb_sha256']:
                            raise ValueError('Original pixels changed')
                        box = (field.x, field.y, field.x + field.width, field.y + field.height)
                        crop = rgb.crop(ACTIVE_AREA).crop(box)
                        # Eligibility check only: exclude sprite obscuration/partial writes.
                        # The original cropped raster remains the expected image.
                        background = bytes(c for y in range(field.height) for x in range(field.width)
                                           for c in PALETTE[source_pixel(vram, field, value, x, y)])
                        if crop.tobytes() != background:
                            continue
                        result[field.name][value] = {'source_case': case, 'pixel_frame': pf,
                            'hardware_frame': vf, 'image': str(path), 'rectangle': list(box),
                            'source_crop_sha256': hashlib.sha256(crop.tobytes()).hexdigest()}
    for field in FIELDS:
        for value in policy['required_direct_variants'][field.name]:
            if value not in result[field.name]:
                raise ValueError('A directly observed source widget variant is missing')
        for value in policy['required_variants'][field.name]:
            if value in result[field.name]:
                continue
            opposite = field.name[:-1] + ('b' if field.name.endswith('a') else 'a')
            donor = next((f for f in FIELDS if f.name == opposite), None)
            if (donor is None or value not in result[opposite] or donor.tiles != field.tiles
                    or donor.y != field.y or donor.columns != field.columns or donor.rows != field.rows
                    or donor.planes != field.planes or donor.fixed_planes != field.fixed_planes):
                raise ValueError('Missing original glyph or shared-font equivalence')
            result[field.name][value] = {**result[opposite][value], 'shared_font_from': opposite,
                'equivalence': 'Identical ROM tile record and Graphics II pattern/color bank; opposite field position only.'}
        if sorted(result[field.name]) != policy['required_variants'][field.name]:
            raise ValueError(f'Missing unobscured original widget values: {field.name}')
    return policy, result
