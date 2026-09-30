"""Identify original captured pixels by callback and uploaded sprite generation.

The expected image is a verified original-emulator capture. Static hardware
decoding is used only by the existing independent source validation, not here
to manufacture an expected image or select visually similar native output.
"""
import hashlib
import json

from PIL import Image

from presentation_reference import ROOT, ACTIVE_AREA
from run_presentation_tests import digest, map_source_palette, native_picture, compare


def source_generation(generation, source_case='one-player-match',
                      reference_directory='tests/reference/presentation', region=None,
                      callback_kind='gameplay'):
    root = ROOT / reference_directory
    frozen = json.loads((root / 'manifest.json').read_text())
    if not frozen['source_media_checks_passed']:
        raise ValueError('Source media not accepted')
    if digest(ROOT / 'tests/cases/presentation.json') != frozen['recipe_sha256']:
        raise ValueError('Presentation contract changed')
    if frozen.get('supplemental_recipe') and digest(ROOT / frozen['supplemental_recipe']) != frozen['supplemental_recipe_sha256']:
        raise ValueError('Supplemental presentation recipe changed')
    entry = frozen['references'][source_case]
    manifest_path, validation_path = root / entry['manifest'], root / entry['validation']
    if digest(manifest_path) != entry['manifest_sha256'] or digest(validation_path) != entry['validation_sha256']:
        raise ValueError('Frozen source manifest/association changed')
    manifest, validation = json.loads(manifest_path.read_text()), json.loads(validation_path.read_text())
    parent_path = ROOT / f'tests/reference/{source_case}.json'
    if digest(parent_path) != manifest['parent_reference_sha256']:
        raise ValueError('Source simulation fixture changed')
    parent = json.loads(parent_path.read_text())
    if generation < 1 or generation > len(parent['updates']):
        raise ValueError('Source generation outside captured gameplay')
    row = parent['updates'][generation - 1]
    if callback_kind not in ('gameplay', 'tail-only') or row['callback_kind'] != callback_kind:
        raise ValueError('Source callback kind differs from the explicit presentation contract')
    ram = bytes.fromhex(row['entry_ram'])
    candidates = []
    for sample in manifest['samples']:
        # active_updates uses begin_frame < frame <= end_frame. Short tail
        # callbacks can begin and end in one frame and have no indexed sample.
        # Their explicit contract admits contemporaneous endpoint observations,
        # still requiring the captured hardware SAT to match the source entry.
        eligible = (row['begin_frame'] <= sample['frame'] <= row['end_frame']
                    if callback_kind == 'tail-only' else generation in sample['active_updates'])
        if not eligible:
            continue
        stem = manifest_path.parent / f'f{sample["frame"]:05d}'
        for suffix in ('vram', 'regs'):
            if digest(stem.with_suffix('.' + suffix)) != sample['hardware_sha256'][suffix]:
                raise ValueError('Source hardware observation changed')
        regs, vram = stem.with_suffix('.regs').read_bytes(), stem.with_suffix('.vram').read_bytes()
        address = regs[5] * 128
        if vram[address:address + 40] == ram[0x10:0x38]:
            candidates.append(sample['frame'])
    if not candidates:
        raise ValueError(f'No source hardware observation for generation {generation}')
    frames = [row['frame'] for row in validation['raster_vdp_associations']
              if any(frame in candidates for frame in row['matching_captured_vdp_frames'])]
    samples = {row['frame']: row for row in manifest['samples']}
    images = []
    for frame in frames:
        with Image.open(manifest_path.parent / f'f{frame:05d}.png') as picture:
            rgb = picture.convert('RGB')
            if hashlib.sha256(rgb.tobytes()).hexdigest() != samples[frame]['rgb_sha256']:
                raise ValueError('Original captured pixels changed')
            images.append(rgb.crop(ACTIVE_AREA))
    if not images or len({(picture.crop(region) if region else picture).tobytes() for picture in images}) != 1:
        raise ValueError(f'No unique source displayed image for generation {generation}')
    return images[0], {'generation': generation, 'source_case': source_case, 'hardware_frames': candidates, 'pixel_frames': frames,
                       'reference_sha256': digest(root / 'manifest.json'),
                       'callback_kind': callback_kind,
                       'comparison_region': region}


def main():
    path = ROOT / 'build/tests/native-presentation-recorded/report.json'
    captured = json.loads(path.read_text())
    if not captured['recorded_entropy'] or not captured['commit_tracking'] or not captured['completed_rasters']:
        raise ValueError('Recorded entropy, commits and completed raster observations required')
    contract = json.loads((ROOT / 'tests/cases/presentation.json').read_text())
    rows = []
    for observation in captured['observations']:
        raster = observation['completed_raster']
        if not raster['generation']:
            continue  # Initial bitmap precedes any simulated display preparation.
        generation = raster['generation']['prepared_after_callback']
        source, association = source_generation(generation)
        expected = map_source_palette(source, contract)
        with Image.open(raster['capture']['path']) as picture:
            actual = native_picture(picture, contract)
        difference = compare(expected, actual, 'completed-native-raster')
        if difference:
            difference['update'] = generation
        rows.append({'requested_callback': observation['completed_callbacks'], 'source': association,
                     'rendered_frame': raster['rendered_frame'], 'first_difference': difference})
        print(json.dumps(rows[-1]), flush=True)
    (path.parent / 'generation-associations.json').write_text(json.dumps({'observations': rows}, indent=2) + '\n')


if __name__ == '__main__':
    main()
