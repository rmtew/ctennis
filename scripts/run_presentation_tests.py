"""Compare actual native Amiga hardware output with retained original-game pixels."""
import argparse
import configparser
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image

from copperline_test_session import CopperlineSession
from presentation_reference import ROOT, PALETTE, ACTIVE_AREA
from run_translated_player_frame_probe import prepare_gameplay
from run_translated_prng_probe import ASSEMBLER, OUT, run
from run_amiga_score_copper_probe import make_banks, make_copper_and_patch_tables
from maintained_state_contract import MAINTAINED_STATE_CONTRACT, MAINTAINED_SCRATCH_OFFSETS


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_picture(case):
    root = ROOT / case['reference']
    manifest = json.loads(root.read_text())
    if not manifest['source_media_checks_passed']:
        raise ValueError('Source graphics not verified')
    if digest(ROOT / 'tests/cases/presentation.json') != manifest['recipe_sha256']:
        raise ValueError('Presentation contract changed; revalidate/freeze the source media')
    reference = manifest['references'][case['source_case']]
    path = root.parent / reference['manifest']
    if digest(path) != reference['manifest_sha256']:
        raise ValueError('Source media manifest changed')
    capture = json.loads(path.read_text())
    frame = capture['named_frames'][case['checkpoint']]
    sample = next(row for row in capture['samples'] if row['frame'] == frame)
    with Image.open(path.parent / f'f{frame:05d}.png') as picture:
        rgb = picture.convert('RGB')
        if hashlib.sha256(rgb.tobytes()).hexdigest() != sample['rgb_sha256']:
            raise ValueError('Source pixels changed')
        return rgb.crop(ACTIVE_AREA), frame, digest(root)


def map_source_palette(picture, contract):
    mapping = {}
    for index, value in contract['amiga_palette_12bit'].items():
        colour = int(value, 16)
        mapping[PALETTE[int(index)]] = tuple(((colour >> shift) & 15) * 17 for shift in (8, 4, 0))
    try:
        return Image.frombytes('RGB', picture.size,
                               bytes(component for pixel in picture.get_flattened_data() for component in mapping[pixel]))
    except KeyError as error:
        raise ValueError(f'Undeclared source colour: {error}') from error


def native_picture(picture, contract):
    if list(picture.size) != contract['amiga_capture_size']:
        raise ValueError('Native capture dimensions changed; review the viewport mapping')
    active = picture.crop(contract['amiga_active_rectangle']).convert('RGB')
    if active.size != (512, 192) or contract['amiga_pixels_per_source_pixel'] != [2, 1]:
        raise ValueError('Unsupported native viewport mapping')
    rows = []
    for y in range(192):
        row = active.crop((0, y, 512, y + 1)).tobytes()
        if any(row[offset:offset + 3] != row[offset + 3:offset + 6] for offset in range(0, len(row), 6)):
            raise ValueError('Native horizontal pixel duplication failed; no interpolated comparison allowed')
        rows.append(bytes(component for offset in range(0, len(row), 6) for component in row[offset:offset + 3]))
    return Image.frombytes('RGB', (256, 192), b''.join(rows))


def compare(expected, actual, boundary="stable-title"):
    if expected.size != actual.size:
        raise ValueError('Logical display dimensions differ')
    for index, (wanted, observed) in enumerate(zip(expected.get_flattened_data(), actual.get_flattened_data())):
        if wanted != observed:
            return {'update': 0, 'boundary': boundary, 'field': 'logical display pixel',
                    'x': index % expected.width, 'y': index // expected.width,
                    'expected': bytes(wanted).hex(), 'actual': bytes(observed).hex()}
    return None


def build_native(case, directory, recorded_refresh=False, initial_source_update=0, source_mutator=None):
    if source_mutator and not recorded_refresh:
        raise ValueError('Source mutations require a private replay wrapper')
    run([sys.executable, 'scripts/roundtrip_rom.py'])
    prepare_gameplay()
    from generate_native_title import generate
    generate()
    run([sys.executable, 'scripts/generate_amiga_sprite_probe.py'])
    make_banks((ROOT / 'build/reference/source-timing/sprite-f1310.vram').read_bytes())
    make_copper_and_patch_tables()
    # Explicit captured-phase diagnostic, independent of ordinary title startup.
    # No intermediate expected states or title-specific code are injected.
    source_case = case.get('source_case', 'one-player-match')
    if source_case not in ('one-player-match', 'two-player-match', 'one-player-restart-complete', 'two-player-restart-complete'):
        raise ValueError('Unsupported native presentation source parent')
    parent_path = ROOT / f'tests/reference/{source_case}.json'
    parent = json.loads(parent_path.read_text())
    if initial_source_update:
        phase_path = ROOT / case['initial_phase_reference']
        from phase_reference import validate_phase
        phase = json.loads(phase_path.read_text())
        validate_phase(phase, json.loads((ROOT / f'tests/cases/{phase_path.stem}.json').read_text()))
        if (phase['initial_source_update'] != initial_source_update
                or phase['parent_sha256'] != digest(parent_path)):
            raise ValueError('Native presentation start/parent differs from verified phase')
        initial = phase['initial_post_tail']
    else:
        initial = parent['initial_post_tail']
    (OUT / 'live-initial-ram.bin').write_bytes(bytes.fromhex(initial))
    executable = directory / 'native-application'
    source = case['native_source']
    defines = ['-DLIVE_PHASE_START=1']
    if recorded_refresh:
        signs = bytearray(len(parent['updates']))
        for index, row in enumerate(parent['updates']):
            bits = {event['bit'] for event in row['refresh_reads']}
            if len(bits) > 1:
                raise ValueError('Native replay adapter cannot supply distinct refresh bits within one callback')
            if bits:
                signs[index] = bits.pop()
        (directory / 'refresh-signs.bin').write_bytes(signs)
        include = directory / 'refresh-signs.i'
        include.write_text(f'REFRESH_SIGN_COUNT equ {len(signs)}\nrefresh_signs: incbin "{(directory / "refresh-signs.bin").as_posix()}"\n', encoding='ascii')
        original = (ROOT / source).read_text(encoding='utf-8')
        if initial_source_update:
            marker = 'simulation_updates: dc.w 0'
            if original.count(marker) != 1:
                raise ValueError('Native callback count initializer changed')
            original = original.replace(marker, f'simulation_updates: dc.w {initial_source_update}')
        old = 'include "build/amiga/long-game/refresh-signs.i"'
        if original.count(old) != 1:
            raise ValueError('Live replay entropy include changed')
        wrapper = directory / 'native-recorded-refresh.s'
        original = original.replace(old, f'include "{include.as_posix()}"')
        initial_path = directory / 'live-initial-ram.bin'
        initial_path.write_bytes(bytes.fromhex(initial))
        marker = 'incbin "build/translation/live-initial-ram.bin"'
        if original.count(marker) != 1:
            raise ValueError('Live phase initializer include changed')
        original = original.replace(marker, f'incbin "{initial_path.as_posix()}"')
        if source_mutator:
            original = source_mutator(original)
        wrapper.write_text(original, encoding='utf-8')
        source = str(wrapper)
        defines = ['-DLONG_GAME_REPLAY=1', '-DLIVE_PHASE_START=1']
    if not recorded_refresh:
        # A capture owns its initial state; later phase builds must not replace
        # a live dependency of its retained executable/evidence.
        initial_path = directory / 'live-initial-ram.bin'
        initial_path.write_bytes(bytes.fromhex(initial))
        original = (ROOT / source).read_text(encoding='utf-8')
        marker = 'incbin "build/translation/live-initial-ram.bin"'
        if original.count(marker) != 1:
            raise ValueError('Live phase initializer include changed')
        wrapper = directory / 'native-captured-phase.s'
        wrapper.write_text(original.replace(marker, f'incbin "{initial_path.as_posix()}"'))
        source = str(wrapper)
    run([str(ASSEMBLER), '-Fhunkexe', '-kick1hunks', '-m68000', *defines,
         '-L', str(directory / 'native.lst'), '-o', str(executable), source])
    from evidence import compile_manifest
    compile_manifest(executable, directory / "native.lst")
    return executable


def player_placement(case, contract, self_test):
    # Imported lazily: the capture adapter uses this module's shared builder.
    from capture_native_presentation import capture
    if case['inputs'] != [{'port': 2, 'red': True}] or case['native_source'] != 'amiga/gameplay_integration_probe.s':
        raise ValueError('Placement adapter supports only the declared live application/fire input')
    source, source_frame, reference_sha = source_picture(case)
    expected = map_source_palette(source, contract)
    region = case['region']
    capture_manifest = ROOT / 'tests/reference/presentation' / case['source_case'] / 'manifest.json'
    manifest = json.loads(capture_manifest.read_text())
    samples = {row['frame']: row for row in manifest['samples']}
    for frame in case['source_frames']:
        with Image.open(capture_manifest.parent / f'f{frame:05d}.png') as picture:
            rgb = picture.convert('RGB')
            if hashlib.sha256(rgb.tobytes()).hexdigest() != samples[frame]['rgb_sha256']:
                raise ValueError('Source window pixels changed')
            mapped = map_source_palette(rgb.crop(ACTIVE_AREA), contract)
            if mapped.crop(region).tobytes() != expected.crop(region).tobytes():
                raise ValueError('Placement region is not invariant across the declared source window')
    captured = capture((case['completed_callbacks'],),track_commits=True,completed_rasters=True)
    observed = captured['observations'][0]
    if any(row['offset'] not in MAINTAINED_SCRATCH_OFFSETS for row in observed['state_differences']):
        raise ValueError('Placement precondition failed: native simulation differs from source')
    raster=observed['completed_raster']
    if not raster['generation'] or raster['rendered_frame'] < raster['generation']['visible_frame']:
        raise ValueError('Placement raster has not completed its published generation')
    from associate_presentation_generations import source_generation
    published,association=source_generation(raster['generation']['prepared_after_callback'])
    if map_source_palette(published,contract).crop(region).tobytes()!=expected.crop(region).tobytes():
        raise ValueError('Completed placement generation is outside the invariant source region')
    with Image.open(raster['capture']['path']) as picture:
        actual = native_picture(picture, contract)
    difference = compare(expected.crop(region), actual.crop(region), case['boundary'])
    if difference:
        difference['x'] += region[0]
        difference['y'] += region[1]
        difference['update'] = case['completed_callbacks']
    if self_test:
        altered = actual.crop(region)
        wanted = expected.crop(region)
        altered.putpixel((0, 0), (255, 255, 255) if wanted.getpixel((0, 0)) != (255, 255, 255) else (0, 0, 0))
        if compare(wanted, altered, case['boundary']) == compare(wanted, actual.crop(region), case['boundary']):
            raise AssertionError('Placement mutation was not detected')
    report = {'case': case['name'], 'subject':'maintained-native', 'state_contract':MAINTAINED_STATE_CONTRACT,
              'omitted_legacy_scratch_offsets':list(MAINTAINED_SCRATCH_OFFSETS),
              'raw_state_differences':observed['state_differences'],
              'completed_raster':raster, 'source_generation':association, 'passed': difference is None,
              'first_difference': difference, 'source_frame': source_frame,
              'reference_sha256': reference_sha, 'executable_sha256': captured['executable_sha256'],
              'native_provenance': {key: captured[key] for key in ('native_source', 'native_source_sha256',
                  'emulator_sha256', 'bridge_sha256', 'kickstart_sha256', 'reference_sha256')},
              'case_sha256': digest(ROOT / f'tests/cases/{case["name"]}.json'),
              'scope': case['contract'], 'source_window': case['source_frames'],
              'region': region, 'self_test': self_test, 'native_observation': observed, 'capture_report_path':captured['capture_report_path']}
    (ROOT / f'build/tests/{case["name"]}-report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


def generation_sequence(case, contract, self_test):
    from capture_native_presentation import capture
    from associate_presentation_generations import source_generation
    from presentation_reference import FIELDS
    def original_generation(generation):
        # Keep primary frozen media intact. Only this previously missing exact
        # upper-serve checkpoint uses the separately repeated/validated capture.
        if case['name'] == 'p1-upper-serve' and generation == 4131:
            recipe = json.loads((ROOT / 'tests/cases/presentation-upper-serve-generation-4131.json').read_text())
            if recipe['source_case'] != case['source_case'] or recipe['association_updates'] != [4131]:
                raise ValueError('Upper-serve supplement changed its declared checkpoint')
            return source_generation(generation, case['source_case'], recipe['reference_directory'])
        return source_generation(generation)
    if case['source_case'] != 'one-player-match' or case['inputs'] != [{'port': 2, 'red': True}]:
        raise ValueError('Generation adapter supports the frozen R1 held-fire prefix')
    captured = capture(tuple(case['completed_callbacks']), recorded_entropy=True,
                       track_commits=True, completed_rasters=True, initial_source_update=case.get('initial_source_update', 0),
                       initial_phase_reference=case.get('initial_phase_reference'), capture_label=case['name'])
    checks, first = [], None
    for observed in captured['observations']:
        if any(row['offset'] not in MAINTAINED_SCRATCH_OFFSETS for row in observed['state_differences']):
            raise ValueError('Graphics precondition failed: source/native simulation differs')
        raster = observed['completed_raster']
        if not raster['generation']:
            raise ValueError('No simulated presentation generation for requested checkpoint')
        generation = raster['generation']['prepared_after_callback']
        source, association = original_generation(generation)
        expected = map_source_palette(source, contract)
        with Image.open(raster['capture']['path']) as picture:
            actual = native_picture(picture, contract)
        for field in case['fields']:
            region = tuple(case['regions'][field]) if field in case.get('regions', {}) else FIELDS[field] if field != 'whole_display' else (0, 0, 256, 192)
            wanted, seen = expected.crop(region), actual.crop(region)
            difference = compare(wanted, seen, f'presentation-generation-{field}')
            if difference:
                difference['update'] = generation
                difference['x'] += region[0]
                difference['y'] += region[1]
                first = first or difference
            if self_test:
                if compare(wanted, wanted) is not None:
                    raise AssertionError('Equal graphics rejected')
                changed = seen.copy()
                changed.putpixel((0, 0), (255, 255, 255) if wanted.getpixel((0, 0)) != (255, 255, 255) else (0, 0, 0))
                if compare(wanted, changed) == compare(wanted, seen):
                    raise AssertionError('Generation comparison failed to detect changed pixel')
            checks.append({'requested_callback': observed['completed_callbacks'], 'field': field,
                           'region': region, 'source': association, 'raster': raster,
                           'first_difference': difference})
    hardware_mutation = None
    if self_test and case.get('initial_source_update'):
        def move_sprite_one_pixel(executable):
            code = executable.read_bytes()
            old, new = bytes.fromhex('06400080'), bytes.fromhex('06400081')
            if code.count(old) != 1:
                raise ValueError('Native sprite origin instruction changed')
            executable.write_bytes(code.replace(old, new))
        changed_capture = capture(tuple(case['completed_callbacks']), recorded_entropy=True,
            track_commits=True, completed_rasters=True,
            initial_source_update=case['initial_source_update'],
            initial_phase_reference=case['initial_phase_reference'],
            executable_mutator=move_sprite_one_pixel, capture_label=case['name'] + '-mutation')
        changed_checks = []
        for observed in changed_capture['observations']:
            if any(row['offset'] not in MAINTAINED_SCRATCH_OFFSETS for row in observed['state_differences']):
                raise AssertionError('Renderer mutation changed simulation state')
            raster = observed['completed_raster']
            generation = raster['generation']['prepared_after_callback']
            source, association = original_generation(generation)
            wanted = map_source_palette(source, contract)
            with Image.open(raster['capture']['path']) as picture:
                seen = native_picture(picture, contract)
            for field in case['fields']:
                region = tuple(case['regions'][field])
                difference = compare(wanted.crop(region), seen.crop(region), f'presentation-generation-{field}')
                if difference:
                    difference.update(update=generation, x=difference['x'] + region[0], y=difference['y'] + region[1])
                normal = next(row for row in checks if row['requested_callback'] == observed['completed_callbacks'] and row['field'] == field)
                if difference == normal['first_difference']:
                    raise AssertionError('Actual sprite-position mutation was not detected')
                changed_checks.append({'requested_callback': observed['completed_callbacks'],
                    'first_difference': difference, 'source': association, 'raster': raster})
        hardware_mutation = {'instruction': 'ADDI.W #$80,D0 changed to #$81 in test executable',
            'executable_sha256': changed_capture['executable_sha256'], 'checks': changed_checks,
            'simulation_unchanged': True, 'detected_at_all_checkpoints': True}
    report = {'case': case['name'], 'subject':'maintained-native', 'state_contract':MAINTAINED_STATE_CONTRACT,
              'omitted_legacy_scratch_offsets':list(MAINTAINED_SCRATCH_OFFSETS),
              'raw_state_differences':[{'update':row['completed_callbacks'],'differences':row['state_differences']} for row in captured['observations']],
              'passed': first is None, 'first_difference': first,
              'checks': checks, 'self_test': self_test, 'scope': case['contract'],
              'hardware_mutation': hardware_mutation,
              'initial_source_update': captured['initial_source_update'],
              'initial_phase_reference': captured['initial_phase_reference'],
              'initial_phase_sha256': captured['initial_phase_sha256'],
              'executable_sha256': captured['executable_sha256'],
              'case_sha256': digest(ROOT / f'tests/cases/{case["name"]}.json'),
              'capture_report_path': captured['capture_report_path'],
              'capture_report_sha256': digest(Path(captured['capture_report_path'])),
              'native_provenance': {key: captured[key] for key in ('native_source', 'native_source_sha256',
                  'emulator_sha256', 'bridge_sha256', 'kickstart_sha256', 'reference_sha256', 'refresh_fixture_sha256')},
              'entropy_reads': captured['entropy_reads']}
    (ROOT / f'build/tests/{case["name"]}-report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'case': case['name'], 'passed': first is None, 'first_difference': first, 'checks': len(checks)}, indent=2))
    return 0 if first is None else 1


def run_cli():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=('p1-title', 'p1-upper-player-placement',
                        'p1-moving-prefix', 'p1-score-status-prefix', 'p1-upper-serve'), default='p1-title')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.case == 'p1-title':
        from run_mode_selection_tests import run as run_mode
        return 0 if run_mode(args.case, args.self_test) else 1
    case = json.loads((ROOT / f'tests/cases/{args.case}.json').read_text())
    contract = json.loads((ROOT / 'tests/cases/presentation.json').read_text())
    report_path = ROOT / f'build/tests/{args.case}-report.json'
    report_path.unlink(missing_ok=True)
    if args.case == 'p1-upper-player-placement':
        return player_placement(case, contract, args.self_test)
    if args.case in ('p1-moving-prefix', 'p1-score-status-prefix', 'p1-upper-serve'):
        return generation_sequence(case, contract, args.self_test)


def main():
    from evidence import tracked_call
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--case', default='p1-title')
    args, _ = parser.parse_known_args()
    if args.case == 'p1-title':
        return run_cli()
    if args.case not in ('p1-upper-player-placement', 'p1-moving-prefix', 'p1-score-status-prefix', 'p1-upper-serve'):
        return run_cli()
    path = ROOT / f'build/tests/{args.case}-report.json'
    return tracked_call([path], 'presentation', 'maintained-native', 'captured presentation phase',
                        'scripts/run_presentation_tests.py', args.case, run_cli,
                        lambda path, report: [Path(report['capture_report_path']).parent / 'native-application'])


if __name__ == '__main__':
    raise SystemExit(main())
