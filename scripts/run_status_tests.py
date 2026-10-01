"""Compare live native status requests, expiry timing and completed Copper pixels."""
import argparse
import json
from pathlib import Path
from PIL import Image
from status_reference import CASES, reference
from capture_native_presentation import capture
from associate_presentation_generations import source_generation
from presentation_reference import ROOT, FIELDS
from run_presentation_tests import digest, map_source_palette, native_picture, compare
from widget_reference import catalog


def earliest(first, difference):
    if difference and (first is None or difference['update'] < first['update']):
        return difference
    return first


def mutation(kind):
    def alter(text):
        # Fault the maintained status selector, not the unrelated returned-title
        # clear in the application wrapper. Keep all product sources untouched.
        fields = (ROOT / 'amiga/game/scene_fields.s').read_text()
        old = ('        clr.b   field_values+4' if kind == 'retain'
               else '        cmpi.b  #255,D_TIMER(a0)')
        new = ('        nop' if kind == 'retain'
               else '        cmpi.b  #254,D_TIMER(a0)')
        if fields.count(old) != 1:
            raise ValueError('Status expiry instruction changed')
        integration = (ROOT / 'amiga/game/integration.s').read_text()
        field_include = '        include "amiga/game/scene_fields.s"'
        integration_include = '        include "amiga/game/integration.s"'
        if integration.count(field_include) != 1 or text.count(integration_include) != 1:
            raise ValueError('Maintained status selector include changed')
        return text.replace(integration_include, integration.replace(field_include, fields.replace(old, new)))
    return alter


def check(case, expected, contract, captured, glyphs):
    timing, pixels, states, first = [], [], [], None
    if case.get('observe_state'):
        events = [row for row in captured['state_events'] if row['update'] in expected]
        if [row['update'] for row in events] != list(expected):
            raise ValueError('Native consecutive state observations missing or duplicated')
        for row in events:
            wanted = bytes.fromhex(expected[row['update']]['post_tail_ram'])
            actual = bytes.fromhex(row['post_tail_ram'])
            differences = [{'update': row['update'], 'boundary': 'status-lifecycle-state',
                'field': 'source state byte', 'ram_offset': offset,
                'expected': wanted[offset], 'actual': actual[offset]}
                for offset in range(2, 256) if wanted[offset] != actual[offset]]
            first = earliest(first, differences[0] if differences else None)
            states.append({'update': row['update'], 'stop': row['stop'], 'differences': differences})
    events = [row for row in captured['field_events'] if row['update'] in expected]
    if [row['update'] for row in events] != list(expected):
        raise ValueError('Native status callback observations missing or duplicated')
    for row in events:
        update, wanted = row['update'], expected[row['update']]
        actual = bytes.fromhex(row['field_values'])[4]
        difference = None
        for name in ('score_flags_before', 'status_timer_before'):
            if row[name] != wanted[name]:
                difference = difference or {'update': update, 'boundary': 'native-status-input-state',
                    'field': name, 'expected': wanted[name], 'actual': row[name]}
        if actual != wanted['selector']:
            difference = difference or {'update': update, 'boundary': 'native-status-selection',
                'field': 'status selector', 'expected': wanted['selector'], 'actual': actual}
        first = earliest(first, difference)
        timing.append({'update': update, 'expected': wanted, 'actual_selector': actual,
                       'stop': row['stop'], 'first_difference': difference})
    for observed in captured['observations']:
        if observed['state_differences']:
            state = observed['state_differences'][0]
            first = earliest(first, {'update': observed['completed_callbacks'],
                'boundary': 'status-lifecycle-state', 'field': 'source state byte',
                'ram_offset': state['offset'], 'expected': state['expected'], 'actual': state['actual']})
        raster = observed['completed_raster']
        if not raster['generation']:
            raise ValueError('Requested status raster precedes the first completed native generation')
        generation = raster['generation']['prepared_after_callback']
        if generation not in expected or raster['rendered_frame'] < raster['generation']['visible_frame']:
            raise ValueError('Native status generation is not a completed visible lifecycle frame')
        source, association = source_generation(generation, case['source_case'])
        box = FIELDS['status']
        # Only stable raster checkpoints make a callback-to-pixels claim. At the
        # exact original draw callback, scanout may still contain the prior text.
        value = expected[generation]['selector']
        with Image.open(glyphs[value]['image']) as picture:
            from presentation_reference import ACTIVE_AREA
            glyph = picture.convert('RGB').crop(ACTIVE_AREA).crop(box)
        if source.crop(box).tobytes() != glyph.tobytes():
            raise ValueError('Stable original status raster disagrees with its drawn latch')
        wanted = map_source_palette(source, contract).crop(box)
        with Image.open(raster['capture']['path']) as picture:
            actual = native_picture(picture, contract).crop(box)
        difference = compare(wanted, actual, 'completed-status-raster')
        if difference:
            difference.update(update=generation, x=difference['x'] + box[0], y=difference['y'] + box[1])
        first = earliest(first, difference)
        pixels.append({'requested_callback': observed['completed_callbacks'], 'source': association,
            'expected_selector': value, 'raster': raster, 'native_png_sha256': digest(Path(raster['capture']['path'])),
            'state_differences': observed['state_differences'],
            'first_difference': difference})
    return {'timing': timing, 'pixels': pixels, 'states': states, 'first_difference': first}


def run(case, contract, glyphs, self_test):
    path = ROOT / f'build/tests/{case["name"]}-report.json'
    path.unlink(missing_ok=True)
    expected, proof = reference(case)
    def obtain(kind=None):
        return capture(tuple(case['completed_callbacks']), recorded_entropy=True,
            track_commits=True, completed_rasters=True, observe_fields=True,
            initial_source_update=case['initial_source_update'],
            initial_phase_reference=case['initial_phase_reference'],
            capture_label=case['name'] + (f'-{kind}' if kind else ''),
            source_mutator=mutation(kind) if kind else None,
            source_case=case['source_case'], native_inputs=case['inputs'],
            observe_state=case.get('observe_state', False))
    captured = obtain()
    checked = check(case, expected, contract, captured, glyphs)
    mutations = []
    if self_test:
        for kind in ('retain', 'early'):
            changed = obtain(kind)
            comparison = check(case, expected, contract, changed, glyphs)
            changed_timing = [row for normal, row in zip(checked['timing'], comparison['timing'])
                              if normal['actual_selector'] != row['actual_selector']]
            difference = changed_timing[0]['first_difference'] if changed_timing else None
            wanted_update = case['expiry_callback'] - (kind == 'early')
            if not difference or difference['boundary'] != 'native-status-selection' or difference['update'] != wanted_update:
                raise AssertionError(f'Compiled {kind} status mutation escaped exact expiry check')
            classification = None
            known = json.loads((ROOT / 'tests/known-failures.json').read_text())['cases'].get(case['name'])
            if known:
                from run_test_suite import classify
                classification = classify({'passed': comparison['first_difference'] is None,
                    'first_difference': comparison['first_difference'], 'checks': comparison}, known)
                if classification != 'unexpected-red':
                    raise AssertionError('Known input failure hid an actual compiled output mutation')
            mutations.append({'kind': kind, 'detected': True, 'mutation_first_difference': difference, 'checks': comparison,
                'mutation_classification': classification,
                'executable_sha256': changed['executable_sha256'],
                'capture_report_path': changed['capture_report_path'],
                'capture_report_sha256': digest(Path(changed['capture_report_path']))})
    report = {'case': case['name'], 'subject': 'maintained-native', 'passed': checked['first_difference'] is None,
        'first_difference': checked['first_difference'], 'checks': checked,
        'reference_proof': proof, 'case_sha256': digest(ROOT / f'tests/cases/{case["name"]}.json'),
        'capture_report_path': captured['capture_report_path'],
        'capture_report_sha256': digest(Path(captured['capture_report_path'])),
        'executable_sha256': captured['executable_sha256'], 'self_test': self_test,
        'hardware_mutations': mutations, 'scope': case['contract']}
    path.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'case': case['name'], 'passed': report['passed'], 'first_difference': report['first_difference'],
        'callback_checks': len(checked['timing']), 'raster_checks': len(checked['pixels']),
        'compiled_mutations': len(mutations)}), flush=True)
    return report['passed']


def run_cli():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=CASES)
    parser.add_argument('--all', action='store_true')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.all == bool(args.case):
        parser.error('Select --all or one --case')
    contract = json.loads((ROOT / 'tests/cases/presentation.json').read_text())
    _, glyphs = catalog()
    passed = []
    for name in CASES if args.all else (args.case,):
        case = json.loads((ROOT / f'tests/cases/{name}.json').read_text())
        passed.append(run(case, contract, glyphs['status'], args.self_test))
    return 0 if all(passed) else 1


def main():
    from evidence import tracked_call
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--case')
    parser.add_argument('--all', action='store_true')
    args, _ = parser.parse_known_args()
    if args.all == bool(args.case) or args.case and args.case not in CASES:
        return run_cli()
    names = (args.case,) if args.case else CASES
    paths = [ROOT / f'build/tests/{name}-report.json' for name in names]
    return tracked_call(paths, 'presentation', 'maintained-native', 'captured status lifecycle phase',
                        'scripts/run_status_tests.py', args.case or list(names), run_cli,
                        lambda path, report: [Path(report['capture_report_path']).parent / 'native-application'])


if __name__ == '__main__':
    raise SystemExit(main())
