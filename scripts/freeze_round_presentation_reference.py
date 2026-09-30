"""Validate only the missing upper-round source windows; retain primary media."""
import argparse
import json
import shutil
from presentation_reference import ROOT, verify_capture
from run_presentation_tests import digest
from associate_presentation_generations import source_generation


def freeze(case):
    recipe_path = ROOT / f'tests/cases/round-scenes-{case}.json'
    recipe = json.loads(recipe_path.read_text())
    directory = ROOT / f'build/tests/{case}-presentation-{recipe["capture_label"]}'
    manifest = json.loads((directory / 'manifest.json').read_text())
    if manifest['supplemental_recipe_sha256'] != digest(recipe_path):
        raise ValueError('Round source recipe changed')
    validation = verify_capture(case, directory)
    if validation['unmatched_named_checkpoints'] or any(
            field['first_captured_visible_frame'] is None
            for checkpoint in validation['field_checkpoints'].values() for field in checkpoint['fields'].values()):
        raise ValueError('Missing verified round source pixels or fields')
    target = ROOT / recipe['reference_directory']
    destination = target / case
    destination.mkdir(parents=True, exist_ok=True)
    descriptor_path = target / 'manifest.json'
    descriptor_path.unlink(missing_ok=True)
    for sample in manifest['samples']:
        stem = f'f{sample["frame"]:05d}'
        for suffix in ('png', 'active.png', 'pixels', 'raster', 'ram', 'vram', 'regs', 'pc'):
            shutil.copyfile(directory / 'a' / f'{stem}.{suffix}', destination / f'{stem}.{suffix}')
    for name in ('manifest.json', 'raster-validation.json'):
        shutil.copyfile(directory / name, destination / name)
    descriptor = {'source_media_checks_passed': True,
        'recipe_sha256': digest(ROOT / 'tests/cases/presentation.json'),
        'supplemental_recipe': str(recipe_path.relative_to(ROOT)), 'supplemental_recipe_sha256': digest(recipe_path),
        'references': {case: {'manifest': f'{case}/manifest.json', 'manifest_sha256': digest(destination / 'manifest.json'),
            'validation': f'{case}/raster-validation.json', 'validation_sha256': digest(destination / 'raster-validation.json')}},
        'primary_media_unchanged': True, 'scope': recipe['contract']}
    descriptor_path.write_text(json.dumps(descriptor, indent=2) + '\n')
    try:
        parent = json.loads((ROOT / f'tests/reference/{case}.json').read_text())
        associations = [source_generation(update, case, recipe['reference_directory'],
            callback_kind=parent['updates'][update - 1]['callback_kind'])[1]
            for update in recipe['association_updates']]
    except Exception:
        descriptor_path.unlink(missing_ok=True)
        raise
    (target / 'generation-associations.json').write_text(json.dumps(associations, indent=2) + '\n')
    print(json.dumps({'case': case, 'samples': len(manifest['samples']),
        'repeat_identical': manifest['repeat_identical'], 'preserved_callbacks': manifest['observer_preserved_callback_capture'],
        'verified_generations': recipe['association_updates']}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=('one-player-match', 'two-player-match'), required=True)
    freeze(parser.parse_args().case)
