"""Retain the bounded original point-field supplement without changing primary media."""
import json
import hashlib
import shutil
from pathlib import Path
from presentation_reference import ROOT, verify_capture
from run_presentation_tests import digest
from presentation_reference import FIELDS
from associate_presentation_generations import source_generation


def main():
    recipe_path = ROOT / 'tests/cases/point-fields.json'
    recipe = json.loads(recipe_path.read_text())
    case = recipe['source_case']
    directory = ROOT / f'build/tests/{case}-presentation-{recipe["capture_label"]}'
    manifest = json.loads((directory / 'manifest.json').read_text())
    if manifest['supplemental_recipe_sha256'] != digest(recipe_path):
        raise ValueError('Supplemental source recipe changed')
    validation = verify_capture(case, directory)
    if validation['unmatched_named_checkpoints'] or any(
            value['first_captured_visible_frame'] is None
            for checkpoint in validation['field_checkpoints'].values() for value in checkpoint['fields'].values()):
        raise ValueError('Supplemental source rasters or requested fields are unverified')
    target = ROOT / recipe['reference_directory']
    target.mkdir(parents=True, exist_ok=True)
    (target / 'manifest.json').unlink(missing_ok=True)
    destination = target / case
    destination.mkdir(exist_ok=True)
    for sample in manifest['samples']:
        stem = f'f{sample["frame"]:05d}'
        for suffix in ('png', 'active.png', 'pixels', 'raster', 'ram', 'vram', 'regs', 'pc'):
            shutil.copyfile(directory / 'a' / f'{stem}.{suffix}', destination / f'{stem}.{suffix}')
    for name in ('manifest.json', 'raster-validation.json'):
        shutil.copyfile(directory / name, destination / name)
    descriptor = {'schema_version': 1, 'source_media_checks_passed': True,
        'recipe_sha256': digest(ROOT / 'tests/cases/presentation.json'),
        'supplemental_recipe': str(recipe_path.relative_to(ROOT)),
        'supplemental_recipe_sha256': digest(recipe_path),
        'references': {case: {'manifest': f'{case}/manifest.json', 'manifest_sha256': digest(destination / 'manifest.json'),
            'validation': f'{case}/raster-validation.json', 'validation_sha256': digest(destination / 'raster-validation.json'),
            'samples': len(manifest['samples'])}},
        'scope': recipe['contract'], 'primary_media_unchanged': True}
    (target / 'manifest.json').write_text(json.dumps(descriptor, indent=2) + '\n')
    # Check only the five fields needed by the pending native regression. The
    # original pixels remain the oracle; actor movement elsewhere is irrelevant.
    associations = []
    for name, checkpoint in recipe['checkpoints'].items():
        for offset in (2, 5):
            for field in ('point_a', 'point_b', 'games_a', 'games_b', 'mode'):
                update = checkpoint['update'] + offset
                image, proof = source_generation(update, case, recipe['reference_directory'], FIELDS[field])
                associations.append({'checkpoint': name, 'callback': update, 'field': field,
                    'pixel_sha256': hashlib.sha256(image.crop(FIELDS[field]).tobytes()).hexdigest(),
                    'association': proof})
    (target / 'field-associations.json').write_text(json.dumps(associations, indent=2) + '\n')
    print(json.dumps({'samples': len(manifest['samples']), 'field_checkpoints': len(validation['field_checkpoints']),
                      'verified_field_observations': len(associations),
                      'repeat_identical': manifest['repeat_identical'], 'preserved_callbacks': manifest['observer_preserved_callback_capture']}))


if __name__ == '__main__':
    main()
