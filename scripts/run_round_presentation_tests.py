"""Compare both modes/serving ends through tally, reset pause and resumed display."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image
from presentation_reference import ROOT, FIELDS
from phase_reference import build_phase, validate_phase
from capture_native_presentation import capture
from associate_presentation_generations import source_generation
from run_presentation_tests import digest, map_source_palette, native_picture, compare
from run_status_tests import earliest

CASES = ('p1-first-round-scenes', 'p1-one-player-upper-round-scenes',
         'p1-two-player-lower-round-scenes', 'p1-two-player-upper-round-scenes')


def reference(case):
    phase_path = ROOT / case['initial_phase_reference']
    phase_case = json.loads((ROOT / 'tests/cases' / phase_path.name).read_text())
    phase = build_phase(phase_case)
    proof = validate_phase(phase, phase_case)
    phase_path.write_text(json.dumps(phase, indent=2) + '\n')
    parent_path = ROOT / phase['parent_reference']
    parent = json.loads(parent_path.read_text())
    milestones = proof['complete_regime']['milestones']
    targets = [milestones['first_game_award']['update'] + 4,
               milestones['tail_only_start']['update'] + 2,
               milestones['gameplay_resumed']['update'] - 1,
               milestones['gameplay_resumed']['update'] + 2]
    inputs = {'one-player-match': [{'port': 2, 'red': True}],
              'two-player-match': [{'port': 1, 'red': True}, {'port': 2, 'red': True}]}
    if (case['source_case'] != phase_case['continuous_parent']
            or case['initial_source_update'] != phase['initial_source_update']
            or case['completed_callbacks'] != targets or case['inputs'] != inputs[case['source_case']]):
        raise ValueError('Round scene recipe differs from its verified source regime')
    proof.update(parent_sha256=digest(parent_path), phase_sha256=digest(phase_path),
                 milestones=milestones)
    return parent, proof


def mutation(kind, case):
    threshold = case['completed_callbacks'][1] - 1
    def alter(text):
        if kind == 'sprite':
            old = '        addi.w  #$6c,d0'
            new = old + '\n        cmpi.w  #1334,simulation_updates\n        bcs.s   round_mutation_sprite_done\n        addq.w  #1,d0\nround_mutation_sprite_done:'
        elif kind == 'field':
            old = 'scoreboard_selection_done:'
            new = old + '\n        cmpi.w  #1334,simulation_updates\n        bcs.s   round_mutation_field_done\n        move.b  #1,field_values+1\n        bsr     patch_score_pointers\nround_mutation_field_done:'
        else:
            old = '        bsr     upload_sprite_attributes'
            new = old + '\n        cmpi.w  #1334,simulation_updates\n        bcs.s   round_mutation_entropy_done\n        movem.l d0-d1/a0,-(sp)\n        bsr     read_refresh_adapter\n        movem.l (sp)+,d0-d1/a0\nround_mutation_entropy_done:'
        if text.count(old) != 1:
            raise ValueError('Round mutation instruction is no longer unique')
        new = new.replace('#1334,simulation_updates', f'#{threshold},simulation_updates')
        return text.replace(old, new)
    return alter


def check(case, parent, captured):
    contract = json.loads((ROOT / 'tests/cases/presentation.json').read_text())
    start, end = case['initial_source_update'], case['completed_callbacks'][-1]
    states, pixels, first = [], [], None
    events = [row for row in captured['state_events'] if start < row['update'] <= end]
    if [row['update'] for row in events] != list(range(start + 1, end + 1)):
        raise ValueError('Round state observation window is incomplete')
    for row in events:
        wanted = bytes.fromhex(parent['updates'][row['update'] - 1]['post_tail_ram'])
        actual = bytes.fromhex(row['post_tail_ram'])
        differences = [{'update': row['update'], 'boundary': case.get('state_boundary', 'round-scene-state'),
            'field': 'source state byte', 'ram_offset': offset,
            'expected': wanted[offset], 'actual': actual[offset]}
            for offset in range(2, 256) if wanted[offset] != actual[offset]]
        states.append({'update': row['update'], 'differences': differences})
        first = earliest(first, differences[0] if differences else None)
    if [row['completed_callbacks'] for row in captured['observations']] != case['completed_callbacks']:
        raise ValueError('Round raster checkpoints are incomplete')
    for observed in captured['observations']:
        raster = observed['completed_raster']
        if not raster['generation'] or raster['rendered_frame'] < raster['generation']['visible_frame']:
            raise ValueError('Round raster was not fully displayed')
        generation = raster['generation']['prepared_after_callback']
        kind = parent['updates'][generation - 1]['callback_kind']
        directory = case.get('reference_directories', {}).get(str(observed['completed_callbacks']), 'tests/reference/presentation')
        source, association = source_generation(generation, case['source_case'], directory, callback_kind=kind,
            require_uploaded_sprite_buffer=kind != 'tail-only' if case.get('tail_without_sprite_upload') else True)
        wanted = map_source_palette(source, contract)
        with Image.open(raster['capture']['path']) as picture:
            actual = native_picture(picture, contract)
        for field, box in {'viewport': (0, 0, 256, 192), **FIELDS}.items():
            expected, seen = wanted.crop(box), actual.crop(box)
            difference = compare(expected, seen, case.get('pixel_boundary', 'completed-round-') + field)
            if difference:
                difference.update(update=observed['completed_callbacks'],
                    x=difference['x'] + box[0], y=difference['y'] + box[1])
            first = earliest(first, difference)
            pixels.append({'checkpoint': observed['completed_callbacks'], 'region': field,
                'expected_sha256': hashlib.sha256(expected.tobytes()).hexdigest(),
                'actual_sha256': hashlib.sha256(seen.tobytes()).hexdigest(),
                'first_difference': difference, 'source': association, 'raster': raster})
    source_events = [row for row in captured['source_event_differences'] if start < row['update'] <= end]
    for difference in source_events:
        first = earliest(first, difference)
    baseline = {'states': states, 'pixels': [{key: row[key] for key in
        ('checkpoint', 'region', 'expected_sha256', 'actual_sha256', 'first_difference')} for row in pixels],
        'source_events': source_events}
    return {'states': states, 'pixels': pixels, 'source_events': source_events,
            'first_difference': first}, baseline


def run(case, self_test):
    path = ROOT / f'build/tests/{case["name"]}-report.json'
    path.unlink(missing_ok=True)
    parent, proof = reference(case)
    def obtain(kind=None):
        return capture(tuple(case['completed_callbacks']), recorded_entropy=True,
            track_commits=True, completed_rasters=True, observe_state=True,
            initial_source_update=case['initial_source_update'],
            initial_phase_reference=case['initial_phase_reference'],
            capture_label=case['name'] + (f'-{kind}' if kind else ''),
            source_mutator=mutation(kind, case) if kind else None,
            source_case=case['source_case'], native_inputs=case['inputs'], strict_source_events=False)
    captured = obtain()
    checks, baseline = check(case, parent, captured)
    mutations = []
    if self_test:
        for kind in ('sprite', 'field', 'entropy'):
            changed = obtain(kind)
            comparison, observed = check(case, parent, changed)
            if observed['states'] != baseline['states']:
                raise AssertionError('Presentation/event-observation mutation changed game RAM')
            if observed['pixels'][:7] != baseline['pixels'][:7] or comparison['first_difference'] != checks['first_difference']:
                raise AssertionError('Late mutation unexpectedly changed the earlier baseline failure')
            if kind == 'entropy':
                if not observed['source_events'] or observed['source_events'][0]['update'] != case['completed_callbacks'][1]:
                    raise AssertionError('Unexpected refresh consumption was not reported as a behaviour failure')
            else:
                affected = [row for normal, row in zip(baseline['pixels'], observed['pixels'])
                            if normal['actual_sha256'] != row['actual_sha256']]
                region = 'viewport' if kind == 'sprite' else 'point_b'
                if not any(row['checkpoint'] == case['completed_callbacks'][1] and row['region'] == region for row in affected):
                    raise AssertionError('Actual late output mutation escaped the reset checkpoint')
            classification = None
            known = json.loads((ROOT / 'tests/known-failures.json').read_text())['cases'].get(case['name'])
            if known:
                from run_test_suite import classify
                classification = classify({'passed': False, 'first_difference': comparison['first_difference'],
                    'baseline_observations': observed}, known)
                if classification != 'unexpected-red':
                    raise AssertionError('Known early sprite failure hid a later compiled mutation')
            mutations.append({'kind': kind, 'detected': True, 'classification': classification,
                'checks': comparison, 'baseline_observations': observed,
                'capture_report_path': changed['capture_report_path'],
                'capture_report_sha256': digest(Path(changed['capture_report_path'])),
                'executable_sha256': changed['executable_sha256']})
    report = {'case': case['name'], 'passed': checks['first_difference'] is None,
        'first_difference': checks['first_difference'], 'checks': checks,
        'baseline_observations': baseline, 'reference_proof': proof,
        'case_sha256': digest(ROOT / f'tests/cases/{case["name"]}.json'),
        'capture_report_path': captured['capture_report_path'],
        'capture_report_sha256': digest(Path(captured['capture_report_path'])),
        'executable_sha256': captured['executable_sha256'], 'self_test': self_test,
        'hardware_mutations': mutations, 'scope': case['contract']}
    path.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'case': case['name'], 'passed': report['passed'],
        'first_difference': report['first_difference'], 'state_checks': len(checks['states']),
        'field_and_viewport_crops': len(checks['pixels']), 'mutations': len(mutations)}), flush=True)
    return report['passed']


def run_cli():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=CASES, required=True)
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    case = json.loads((ROOT / f'tests/cases/{args.case}.json').read_text())
    return 0 if run(case, args.self_test) else 1


def main():
    from evidence import tracked_call
    import sys
    probe = argparse.ArgumentParser(add_help=False)
    probe.add_argument('--case')
    selected, _ = probe.parse_known_args()
    if selected.case not in CASES:
        return run_cli()
    path = ROOT / f'build/tests/{selected.case}-report.json'
    return tracked_call([path], 'round-scenes', 'maintained-native', 'captured round phase',
                        'scripts/run_round_presentation_tests.py', selected.case, run_cli,
                        lambda path, report: [Path(report['capture_report_path']).parent / 'native-application'])


if __name__ == '__main__':
    raise SystemExit(main())
