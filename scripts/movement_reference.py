"""Validate observed F1 approach/hold/reversal evidence, not generate an oracle."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIRECTIONS = {'down': (8, 0, 1), 'up': (2, 0, -1),
              'right': (1, 1, 1), 'left': (4, 1, -1)}
OPPOSITE = {'down': 'up', 'up': 'down', 'right': 'left', 'left': 'right'}
RECEIVER_BOUNDS = {
    'movement-receiver-right-bound': {'direction': 'right', 'coordinate': 0x46, 'start': 160, 'limit': 175,
        'prefix_frame': 2619, 'prefix_callbacks': 1320, 'press': 2620, 'reverse': 2642, 'release': 2646, 'mode': 0x88},
    'movement-receiver-left-bound': {'direction': 'left', 'coordinate': 0x46, 'start': 88, 'limit': 64,
        'prefix_frame': 1511, 'prefix_callbacks': 212, 'press': 1512, 'reverse': 1536, 'release': 1540, 'mode': 0x80},
    'movement-receiver-up-bound': {'direction': 'up', 'coordinate': 0x45, 'start': 8, 'limit': 7,
        'prefix_frame': 1511, 'prefix_callbacks': 212, 'press': 1512, 'reverse': 1536, 'release': 1540, 'mode': 0x80},
    'movement-receiver-down-bound': {'direction': 'down', 'coordinate': 0x45, 'start': 8, 'limit': 31,
        'prefix_frame': 1511, 'prefix_callbacks': 212, 'press': 1512, 'reverse': 1536, 'release': 1540, 'mode': 0x80},
    'movement-lower-receiver-right-bound': {'player': 'lower', 'direction': 'right', 'coordinate': 0x4A,
        'start': 192, 'limit': 199, 'prefix_frame': 5868, 'prefix_callbacks': 4569,
        'press': 5869, 'reverse': 5887, 'release': 5891, 'mode': 0x92},
}
RECEIVER_PHASES = {'movement-lower-receiver-right-phase': 'movement-lower-receiver-right-bound'}


def validate_movement(fixture, case):
    if case['name'] in RECEIVER_PHASES:
        from phase_reference import validate_phase
        validate_phase(fixture, case)
        source_name = RECEIVER_PHASES[case['name']]
        source_case = json.loads((ROOT / f'tests/cases/{source_name}.json').read_text())
        source_fixture = json.loads((ROOT / source_case['reference']).read_text())
        proof = validate_movement(source_fixture, source_case)
        for observation in proof['observed_movement_limits']:
            for interval in ('source_callback_interval', 'held_callback_interval', 'reversal_callback_interval'):
                if not all(case['initial_source_update'] < ordinal <= case['initial_source_update'] + case['updates']
                           for ordinal in observation[interval]):
                    raise ValueError('Native phase does not include all required movement observations')
        return {**proof, 'source_capture_case': source_name, 'phase_initial_source_update': case['initial_source_update']}
    if case['name'] in RECEIVER_BOUNDS:
        return validate_receiver_bound(fixture, case)
    if case['name'] not in ('movement-serve-bounds', 'movement-alternate-serve-bounds'):
        raise ValueError('Unsupported movement evidence recipe')
    # Recorded service-row limits: upper limits are exclusive in the Z80
    # positive-step comparison. These are captured endpoints, not a game model.
    row_number = 0 if case['name'] == 'movement-serve-bounds' else 1
    limits = ({'lower': ((152, 153), (128, 199)), 'upper': ((7, 9), (80, 111))}
              if row_number == 0 else
              {'lower': ((152, 153), (40, 111)), 'upper': ((7, 9), (128, 159))})
    expected_animation = row_number << 5
    expected_mode = 0x80 | (8 if row_number else 0)
    prefix_evidence = None
    if row_number == 1:
        from round_reference import validate_fixture
        parent_path = ROOT / 'tests/reference/two-player-match.json'
        parent_payload = parent_path.read_bytes()
        parent = json.loads(parent_payload)
        validate_fixture(parent)
        prefix = [row for row in fixture['updates'] if row['frame'] <= 1784]
        if (len(prefix) != 485 or prefix != parent['updates'][:485]
                or fixture['initial_post_tail'] != parent['initial_post_tail']):
            raise ValueError('Alternate serve did not preserve the natural R2 point/reset prefix')
        prefix_evidence = {'parent_reference': 'tests/reference/two-player-match.json',
                           'parent_sha256': hashlib.sha256(parent_payload).hexdigest(),
                           'identical_source_callbacks': 485, 'through_source_frame': 1784}
    intervals = case['movement_intervals']
    observations = []
    for index, interval in enumerate(intervals[:-1]):
        direction = interval['direction']
        reverse = intervals[index + 1]
        if reverse['direction'] != OPPOSITE[direction]:
            continue
        bit, axis, sign = DIRECTIONS[direction]
        rows = [row for row in fixture['updates']
                if interval['press_frame'] <= row['frame'] < interval['release_frame']]
        reversals = [row for row in fixture['updates']
                     if reverse['press_frame'] <= row['frame'] < reverse['release_frame']][:4]
        if len(rows) < 9 or len(reversals) != 4:
            raise ValueError('Insufficient held/reversed callbacks')
        for side, coordinate, animation, shift in (
                ('lower', 0x49 + axis, 0x43, 0),
                ('upper', 0x45 + axis, 0x44, 4)):
            states = [(bytes.fromhex(row['entry_ram']), bytes.fromhex(row['ram']))
                      for row in rows]
            end = states[-1][1][coordinate]
            expected_limit = limits[side][axis][int(sign > 0)]
            if end != expected_limit:
                raise ValueError(f'{side} {direction}: source did not reach its limit')
            if not any(before[coordinate] != after[coordinate] for before, after in states):
                raise ValueError('No observed approach to limit')
            for row, (before, after) in zip(rows, states):
                if (row['callback_kind'] != 'gameplay' or before[animation] != expected_animation
                        or after[animation] != expected_animation):
                    raise ValueError('Movement row changed or animation blocked')
                if (before[0x39] & 4 or after[0x39] & 4
                        or before[0x3D] != expected_mode or after[0x3D] != expected_mode):
                    raise ValueError('Point block or side/mode change obscures movement')
                if ((after[0x53] >> shift) & 15) != bit:
                    raise ValueError('Held direction was not consumed')
            held = states[-8:]
            if any(before[coordinate] != end or after[coordinate] != end for before, after in held):
                raise ValueError('Eight accepted attempts did not remain at the limit')
            if {before[0x6B] & 1 for before, _ in held} != {0, 1}:
                raise ValueError('Held attempts did not cover both step sizes')
            reverse_values = []
            for row in reversals:
                before, after = bytes.fromhex(row['entry_ram']), bytes.fromhex(row['ram'])
                if (row['callback_kind'] != 'gameplay' or before[animation] != expected_animation
                        or after[animation] != expected_animation
                        or before[0x39] & 4 or after[0x39] & 4
                        or before[0x3D] != expected_mode or after[0x3D] != expected_mode):
                    raise ValueError('Reversal is blocked or in a different bounds row')
                if ((after[0x53] >> shift) & 15) != DIRECTIONS[reverse['direction']][0]:
                    raise ValueError('Reversal input not consumed')
                reverse_values.append(after[coordinate])
            if not any((value - end) * sign < 0 for value in reverse_values):
                raise ValueError('No observed response to reversal')
            observations.append({'player': side, 'bounds_row': row_number, 'direction': direction,
                                 'source_callback_interval': [rows[0]['ordinal'], rows[-1]['ordinal']],
                                 'start_coordinate': states[0][0][coordinate], 'stopped_coordinate': end,
                                 'held_callback_interval': [rows[-8]['ordinal'], rows[-1]['ordinal']],
                                 'held_tick_parities': sorted({before[0x6B] & 1 for before, _ in held}),
                                 'reversal_callback_interval': [reversals[0]['ordinal'], reversals[-1]['ordinal']],
                                 'reversal_coordinates': reverse_values})
    required = {(side, direction) for side in limits for direction in DIRECTIONS}
    if {(row['player'], row['direction']) for row in observations} != required:
        raise ValueError('Missing direction/player evidence for selected row')
    return {'observed_movement_limits': observations,
            'natural_prefix_evidence': prefix_evidence,
            'remaining_bounds_rows': {side: [row for row in range(4) if row != row_number] for side in limits},
            'complete_F1': False}


def validate_receiver_bound(fixture, case):
    contract = RECEIVER_BOUNDS[case['name']]
    player = contract.get('player', 'upper')
    animation = 0x43 if player == 'lower' else 0x44
    coordinate, direction = contract['coordinate'], contract['direction']
    limit, start = contract['limit'], contract['start']
    sign = DIRECTIONS[direction][2]
    if not fixture.get('movement_observations') or not fixture.get('ordinary_raw_stream_unchanged'):
        raise ValueError('Receiver bound lacks non-invasive source observation proof')
    from round_reference import validate_fixture
    parent_path = ROOT / 'tests/reference/two-player-match.json'
    parent_payload = parent_path.read_bytes()
    parent = json.loads(parent_payload)
    validate_fixture(parent)
    prefix = [{key: value for key, value in row.items() if not key.startswith('movement_')}
              for row in fixture['updates'] if row['frame'] <= contract['prefix_frame']]
    # Extra observer records change debugger-log sequence numbers, not the
    # ordered source main-thread writes/events. Preserve every other field.
    def normalized(rows):
        return [{**row, 'before_events': [{key: value for key, value in event.items() if key != 'sequence'}
                                         for event in row['before_events']]} for row in rows]
    if (len(prefix) != contract['prefix_callbacks']
            or normalized(prefix) != normalized(parent['updates'][:contract['prefix_callbacks']])
            or fixture['initial_post_tail'] != parent['initial_post_tail']):
        raise ValueError('Receiver bound did not preserve natural R2 service setup')
    held = [row for row in fixture['updates'] if contract['press'] <= row['frame'] < contract['reverse']]
    reversed_rows = [row for row in fixture['updates'] if contract['reverse'] <= row['frame'] < contract['release']]
    if len(held) != contract['reverse'] - contract['press'] or len(reversed_rows) != 4:
        raise ValueError('Missing receiver approach/hold/reversal interval')
    states = []
    for row in held + reversed_rows:
        before = bytes.fromhex(row['movement_entry_ram'])
        after = bytes.fromhex(row['movement_return_ram'])
        if row['callback_kind'] != 'gameplay' or (before[animation] & 0xE0) != 0x40 or before[0x39] & 4:
            raise ValueError('Receiver movement not enabled in row two')
        if before[0x3D] != contract['mode']:
            raise ValueError('Unexpected physical controller ownership')
        if before[animation] != after[animation] or before[0x6B] != after[0x6B]:
            raise ValueError('Movement observations straddle a phase or tick change')
        expected_direction = DIRECTIONS[direction if row['frame'] < contract['reverse'] else OPPOSITE[direction]][0]
        shift = 4 if (before[0x3D] ^ (16 if player == 'upper' else 0)) & 16 else 0
        if (before[0x53] >> shift) & 15 != expected_direction:
            raise ValueError('Receiver did not consume held/reversed direction')
        if bytes.fromhex(row['ram'])[coordinate] != after[coordinate]:
            raise ValueError('Later callback work changed observed receiver coordinate')
        states.append((before, after))
    if states[0][0][coordinate] != start or states[len(held) - 1][1][coordinate] != limit:
        raise ValueError('Receiver did not approach the specified row-two limit')
    for before, after in states[len(held) - 8:len(held)]:
        if before[coordinate] != limit or after[coordinate] != limit:
            raise ValueError('Eight enabled attempts did not hold the receiver limit')
    if {before[0x6B] & 1 for before, _ in states[len(held) - 8:len(held)]} != {0, 1}:
        raise ValueError('Receiver hold lacks both step parities')
    if not all((after[coordinate] - limit) * sign < 0 for _, after in states[len(held):]):
        raise ValueError('Receiver did not respond to reversal')
    return {'observed_movement_limits': [{'player': player, 'bounds_row': 2, 'direction': direction,
             'source_callback_interval': [held[0]['ordinal'], held[-1]['ordinal']],
             'start_coordinate': start, 'stopped_coordinate': limit,
             'held_callback_interval': [held[-8]['ordinal'], held[-1]['ordinal']],
             'reversal_callback_interval': [reversed_rows[0]['ordinal'], reversed_rows[-1]['ordinal']],
             'reversal_coordinates': [after[coordinate] for _, after in states[len(held):]]}],
            'source_movement_entry_observed': True,
            'natural_prefix_evidence': {'parent_reference': 'tests/reference/two-player-match.json',
                'parent_sha256': hashlib.sha256(parent_payload).hexdigest(),
                'identical_source_callbacks': contract['prefix_callbacks']},
            'complete_F1': False}


if __name__ == '__main__':
    import argparse
    from round_reference import validate_fixture
    parser = argparse.ArgumentParser(description=__doc__)
    from round_reference import MOVEMENT_CASES
    parser.add_argument('--case', choices=MOVEMENT_CASES, default='movement-serve-bounds')
    args = parser.parse_args()
    case = json.loads((ROOT / f'tests/cases/{args.case}.json').read_text())
    fixture = json.loads((ROOT / case['reference']).read_text())
    validate_fixture(fixture)
    report = validate_movement(fixture, case)
    (ROOT / f'build/tests/{args.case}-coverage.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
