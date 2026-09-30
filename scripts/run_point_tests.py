"""Compare actual native point producer timing and completed Copper field pixels."""
import argparse
import json
from pathlib import Path
from PIL import Image
from point_reference import CASES, FIELDS, SLOTS, reference
from presentation_reference import ROOT, FIELDS as BOXES
from capture_native_presentation import capture
from associate_presentation_generations import source_generation
from run_presentation_tests import digest, map_source_palette, native_picture, compare
from run_status_tests import earliest


def mutation(kind):
    def alter(text):
        if kind == 'freeze':
            old = '        move.b  $3f(a5),(a0)+'
            if text.count(old) != 1:
                raise ValueError('Point field instruction changed')
            return text.replace(old, '        addq.l  #1,a0')
        old = '        bsr     update_native_scoreboard'
        gate = '        bsr     score_gate'
        if text.count(old) != 1 or text.count(gate) != 1:
            raise ValueError('Point dispatch instructions changed')
        return text.replace(old, '        nop').replace(gate, gate +
            '\n        move.b  $42(a5),score_flags_before\n        bsr     update_native_scoreboard')
    return alter


def check(case, expected, contract, captured, proof):
    first, states, timing, pixels = None, [], [], []
    if len(captured['initial_fields']) != 1:
        raise ValueError('Missing actual pre-callback native field observation')
    initial = bytes.fromhex(captured['initial_fields'][0]['field_values'])
    initial = [initial[slot] for slot in SLOTS]
    state_events = [row for row in captured['state_events'] if row['update'] in expected]
    events = [row for row in captured['field_events'] if row['update'] in expected]
    if [row['update'] for row in state_events] != list(expected) or [row['update'] for row in events] != list(expected):
        raise ValueError('Point callback observations missing or duplicated')
    for row in state_events:
        wanted = bytes.fromhex(expected[row['update']]['post_tail_ram'])
        actual = bytes.fromhex(row['post_tail_ram'])
        differences = [{'update': row['update'], 'boundary': 'point-transition-state',
            'field': 'source state byte', 'ram_offset': offset,
            'expected': wanted[offset], 'actual': actual[offset]}
            for offset in range(2, 256) if wanted[offset] != actual[offset]]
        first = earliest(first, differences[0] if differences else None)
        states.append({'update': row['update'], 'differences': differences})
    for row in events:
        wanted = expected[row['update']]['selection']
        wanted = initial if wanted is None else wanted
        actual = bytes.fromhex(row['field_values'])
        actual = [actual[slot] for slot in SLOTS]
        difference = next(({'update': row['update'], 'boundary': 'native-point-selection',
            'field': name, 'expected': a, 'actual': b}
            for name, a, b in zip(FIELDS, wanted, actual) if a != b), None)
        first = earliest(first, difference)
        timing.append({'update': row['update'], 'expected': wanted, 'actual': actual,
                       'first_difference': difference})
    for observation in captured['observations']:
        raster = observation['completed_raster']
        if not raster['generation']:
            raise ValueError('Point raster precedes the first native generation')
        generation = raster['generation']['prepared_after_callback']
        if generation not in expected or expected[generation]['selection'] is None or raster['rendered_frame'] < raster['generation']['visible_frame']:
            raise ValueError('Point raster is not a stable completed score generation')
        with Image.open(raster['capture']['path']) as picture:
            native = native_picture(picture, contract)
        for field in FIELDS:
            box = BOXES[field]
            source, association = source_generation(generation, case['source_case'], proof['reference_directory'], box)
            wanted = map_source_palette(source, contract).crop(box)
            difference = compare(wanted, native.crop(box), 'completed-point-raster')
            if difference:
                difference.update(update=generation, field=field,
                    x=difference['x'] + box[0], y=difference['y'] + box[1])
            first = earliest(first, difference)
            pixels.append({'update': generation, 'field': field, 'source': association,
                'raster': raster, 'first_difference': difference})
    return {'states': states, 'timing': timing, 'pixels': pixels, 'first_difference': first}


def run(case, self_test):
    path = ROOT / f'build/tests/{case["name"]}-report.json'
    path.unlink(missing_ok=True)
    expected, proof = reference(case)
    contract = json.loads((ROOT / 'tests/cases/presentation.json').read_text())
    def obtain(kind=None):
        return capture(tuple(case['completed_callbacks']), recorded_entropy=True,
            track_commits=True, completed_rasters=True, observe_fields=True,
            observe_state=True, observe_initial_fields=True,
            initial_source_update=case['initial_source_update'],
            initial_phase_reference=case['initial_phase_reference'],
            capture_label=case['name'] + (f'-{kind}' if kind else ''),
            source_mutator=mutation(kind) if kind else None,
            source_case=case['source_case'], native_inputs=case['inputs'])
    captured = obtain()
    checked = check(case, expected, contract, captured, proof)
    mutations = []
    if self_test:
        for kind in ('early', 'freeze'):
            changed = obtain(kind)
            comparison = check(case, expected, contract, changed, proof)
            different = [row for normal, row in zip(checked['timing'], comparison['timing']) if normal['actual'] != row['actual']]
            difference = different[0]['first_difference'] if different else None
            target = proof['award_callback'] if kind == 'early' else proof['draw_callback']
            if not difference or difference['boundary'] != 'native-point-selection' or difference['update'] != target:
                raise AssertionError(f'Compiled {kind} point mutation escaped its exact draw boundary')
            if comparison['states'] != checked['states']:
                raise AssertionError('Output-only point mutation changed game RAM')
            classification = None
            known = json.loads((ROOT / 'tests/known-failures.json').read_text())['cases'].get(case['name'])
            if known:
                from run_test_suite import classify
                classification = classify({'passed': comparison['first_difference'] is None,
                    'first_difference': comparison['first_difference'], 'checks': comparison}, known)
                if classification != 'unexpected-red':
                    raise AssertionError('Known input failure hid an actual compiled point mutation')
            mutations.append({'kind': kind, 'detected': True, 'mutation_first_difference': difference,
                'mutation_classification': classification, 'checks': comparison,
                'executable_sha256': changed['executable_sha256'],
                'capture_report_path': changed['capture_report_path'],
                'capture_report_sha256': digest(Path(changed['capture_report_path']))})
    report = {'case': case['name'], 'passed': checked['first_difference'] is None,
        'first_difference': checked['first_difference'], 'checks': checked, 'reference_proof': proof,
        'case_sha256': digest(ROOT / f'tests/cases/{case["name"]}.json'),
        'capture_report_path': captured['capture_report_path'],
        'capture_report_sha256': digest(Path(captured['capture_report_path'])),
        'executable_sha256': captured['executable_sha256'], 'self_test': self_test,
        'hardware_mutations': mutations, 'scope': case['contract']}
    path.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'case': case['name'], 'passed': report['passed'],
        'first_difference': report['first_difference'], 'callback_checks': len(checked['timing']),
        'raster_checks': len(checked['pixels']), 'compiled_mutations': len(mutations)}), flush=True)
    return report['passed']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=CASES)
    parser.add_argument('--all', action='store_true')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.all == bool(args.case):
        parser.error('Select --all or one --case')
    results = [run(json.loads((ROOT / f'tests/cases/{name}.json').read_text()), args.self_test)
               for name in CASES if args.all or name == args.case]
    return 0 if all(results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
