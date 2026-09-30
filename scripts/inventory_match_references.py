"""Index observed match behaviours; do not promote missing observations to coverage."""
import collections
import hashlib
import json
from pathlib import Path
from round_reference import validate_fixture
from phase_reference import CASES as PHASE_CASES, validate_phase

ROOT = Path(__file__).resolve().parent.parent


def inventory(name):
    path = ROOT / f'tests/reference/{name}.json'
    fixture = json.loads(path.read_text())
    validate_fixture(fixture)
    markers = collections.defaultdict(list)
    for event in fixture['timeline']:
        if event['kind'] == 'M' and event['pc'] in (0xC9F, 0xFD3):
            markers[event['after_callback']].append('lower' if event['pc'] == 0xC9F else 'upper')
    scores, transitions, rallies = [], [], []
    returns, return_start = [], None
    previous = tuple(bytes.fromhex(fixture['initial_post_tail'])[0x3E:0x40])
    wraps, saturations = [], {}
    for row in fixture['updates']:
        before, after = bytes.fromhex(row['ram']), bytes.fromhex(row['post_tail_ram'])
        score = tuple(before[0x3E:0x40])
        if markers[row['ordinal']] and return_start is None:
            return_start = row['ordinal']
        returns.extend(markers[row['ordinal']])
        if score != previous:
            transitions.append({'update': row['ordinal'], 'before': previous, 'after': score})
            if returns:
                rallies.append({'first_return_update': return_start, 'point_end_update': row['ordinal'],
                                'returns': returns})
            returns, return_start = [], None
            previous = score
        scores.append(score)
        if before[0x6B] == 255 and after[0x6B] == 0:
            wraps.append(row['ordinal'])
        for offset in range(0x6C, 0x72):
            if before[offset] == 254 and after[offset] == 255:
                saturations.setdefault(f'C0{offset:02X}', row['ordinal'])
    same_rally = [row for row in rallies if {'lower', 'upper'} <= set(row['returns'])]
    return {'reference_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'updates': len(fixture['updates']), 'point_codes_observed': sorted(set(scores)),
            'score_transitions': transitions, 'instrumented_return_counts': dict(collections.Counter(
                player for values in markers.values() for player in values)),
            'same_rally_both_players': same_rally,
            'required_rally_candidates': [row for row in same_rally if len(row['returns']) >= 4],
            'return_marker_instrumentation': bool(markers),
            'counter_wrap_updates': wraps, 'first_timer_saturation_updates': saturations,
            'refresh_bits_observed': sorted({read['bit'] for row in fixture['updates'] for read in row['refresh_reads']}),
            'rallies_with_instrumented_returns': rallies}


def phase_inventory():
    """Index reachable starts and current reports without claiming upstream parity."""
    result = []
    for name in PHASE_CASES:
        recipe = json.loads((ROOT / f'tests/cases/{name}.json').read_text())
        fixture = json.loads((ROOT / recipe['reference']).read_text())
        validate_phase(fixture, recipe)
        report_path = ROOT / f'build/tests/{name}-report.json'
        report = json.loads(report_path.read_text()) if report_path.exists() else None
        start = recipe['initial_source_update'] + 1
        result.append({'case': name, 'parent_reference': recipe['parent_reference'],
                       'source_callback_interval': [start, start + recipe['updates'] - 1],
                       'compared_ram_offsets': recipe.get('compared_ram_offsets', 'all except declared exclusions'),
                       'report_present': report is not None,
                       'last_report_passed': report['passed'] if report else None,
                       'first_difference': report['first_difference'] if report else None,
                       'upstream_continuous_parity_claimed': False})
    return result


if __name__ == '__main__':
    report = {name: inventory(name) for name in ('one-player-match', 'two-player-match')}
    (ROOT / 'build/tests').mkdir(parents=True, exist_ok=True)
    (ROOT / 'build/tests/match-inventory.json').write_text(json.dumps(report, indent=2) + '\n')
    coverage = {'source_matches': report, 'source_derived_phases': phase_inventory(),
                'open_requirements': json.loads((ROOT / 'tests/coverage-backlog.json').read_text()),
                'warning': 'Last reports are historical observations, not a fresh native run or complete coverage.'}
    from movement_reference import validate_movement
    case = json.loads((ROOT / 'tests/cases/movement-serve-bounds.json').read_text())
    payload = (ROOT / case['reference']).read_bytes()
    fixture = json.loads(payload)
    validate_fixture(fixture)
    coverage['focused_movement'] = {'reference_sha256': hashlib.sha256(payload).hexdigest(),
                                    **validate_movement(fixture, case)}
    (ROOT / 'build/tests/coverage-inventory.json').write_text(json.dumps(coverage, indent=2) + '\n')
    for name, row in report.items():
        print(name, 'updates', row['updates'], 'returns', row['instrumented_return_counts'],
              'same-rally-both', len(row['same_rally_both_players']),
              'wraps', len(row['counter_wrap_updates']), 'refresh bits', row['refresh_bits_observed'])
