"""Validate and retain independently captured P1 source media; native parity is separate."""
import hashlib
import json
import shutil

from presentation_reference import ROOT, verify_capture


def main():
    recipe = json.loads((ROOT / 'tests/cases/presentation.json').read_text())
    captures = {}
    for case in recipe['source_cases']:
        directory = ROOT / f'build/tests/{case}-presentation'
        manifest = json.loads((directory / 'manifest.json').read_text())
        validation = verify_capture(case)
        if validation['unmatched_named_checkpoints']:
            raise ValueError(f'Unassociated named rasters: {case}')
        missing = [(name, field) for name, checkpoint in validation['field_checkpoints'].items()
                   for field, data in checkpoint['fields'].items()
                   if data['first_captured_visible_frame'] is None]
        if missing:
            raise ValueError(f'Missing displayed fields: {case}: {missing}')
        parent = json.loads((ROOT / f'tests/reference/{case}.json').read_text())
        pairs = {tuple(bytes.fromhex(row['ram'])[0x3E:0x40]) for row in parent['updates']}
        if any(f'point-codes-{a}-{b}' not in manifest['named_frames'] for a, b in pairs):
            raise ValueError(f'Missing observed point pair: {case}')
        for group in ('P1-title', 'P1-mode', 'P1-serve-lower', 'P1-serve-upper', 'P1-game-match-restart'):
            if any(name not in manifest['named_frames'] for name in recipe['graphics_requirements'][group]):
                raise ValueError(f'Missing {group}: {case}')
        captures[case] = (directory, manifest, validation)
    names = set().union(*(set(manifest['named_frames']) for _, manifest, _ in captures.values()))
    required = recipe['graphics_requirements']['P1-rally'] + [
        f'status-{code}-{event}' for code in recipe['graphics_requirements']['P1-status']['observed_codes']
        for event in recipe['graphics_requirements']['P1-status']['events']]
    if any(name not in names for name in required):
        raise ValueError('Missing rally or status source media')
    target = ROOT / recipe['reference_directory']
    target.mkdir(parents=True, exist_ok=True)
    # Remove a stale acceptance report before copying; incomplete copies cannot pass.
    (target / 'manifest.json').unlink(missing_ok=True)
    references = {}
    for case, (directory, manifest, validation) in captures.items():
        destination = target / case
        destination.mkdir(exist_ok=True)
        for sample in manifest['samples']:
            stem = f"f{sample['frame']:05d}"
            for suffix in ('png', 'active.png', 'pixels', 'raster', 'ram', 'vram', 'regs', 'pc'):
                shutil.copyfile(directory / 'a' / f'{stem}.{suffix}', destination / f'{stem}.{suffix}')
        for name, row in validation['field_checkpoints'].items():
            for field in row['fields']:
                shutil.copyfile(directory / f'{name}-{field}.png', destination / f'{name}-{field}.png')
        for name in ('manifest.json', 'raster-validation.json'):
            shutil.copyfile(directory / name, destination / name)
        references[case] = {'manifest': f'{case}/manifest.json',
                            'manifest_sha256': hashlib.sha256((destination / 'manifest.json').read_bytes()).hexdigest(),
                            'validation': f'{case}/raster-validation.json',
                            'validation_sha256': hashlib.sha256((destination / 'raster-validation.json').read_bytes()).hexdigest(),
                            'samples': len(manifest['samples']),
                            'field_observations': sum(len(row['fields']) for row in validation['field_checkpoints'].values())}
    result = {'schema_version': 1, 'kind': 'independent-original-game-P1-source-media',
              'source_media_checks_passed': True, 'native_comparison_complete': False,
              'references': references,
              'scope': 'Required named P1 windows and displayed fields. Frame-buffer/VDP associations retained explicitly; not whole-match presentation verification.',
              'remaining': ['native P1 adapters and comparison', 'P2 source WAVs/native comparison',
                            'P3 hardware timing/input and complete-match presentation checks'],
              'recipe_sha256': hashlib.sha256((ROOT / 'tests/cases/presentation.json').read_bytes()).hexdigest()}
    (target / 'manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
