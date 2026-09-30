"""Validate observed F1 approach/hold/reversal evidence, not generate an oracle."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIRECTIONS = {'down': (8, 0, 1), 'up': (2, 0, -1),
              'right': (1, 1, 1), 'left': (4, 1, -1)}
OPPOSITE = {'down': 'up', 'up': 'down', 'right': 'left', 'left': 'right'}


def validate_movement(fixture, case):
    if case['name'] != 'movement-serve-bounds':
        raise ValueError('Unsupported movement evidence recipe')
    # Recorded source row-zero limits: upper limits are exclusive in the Z80
    # positive-step comparison. These are captured endpoints, not a game model.
    limits = {'lower': ((152, 153), (128, 199)),
              'upper': ((7, 9), (80, 111))}
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
                if row['callback_kind'] != 'gameplay' or before[animation] != 0 or after[animation] != 0:
                    raise ValueError('Movement row changed or animation blocked')
                if before[0x39] & 4 or after[0x39] & 4 or before[0x3D] != 0x80 or after[0x3D] != 0x80:
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
                if (row['callback_kind'] != 'gameplay' or before[animation] != 0 or after[animation] != 0
                        or before[0x39] & 4 or after[0x39] & 4
                        or before[0x3D] != 0x80 or after[0x3D] != 0x80):
                    raise ValueError('Reversal is blocked or in a different bounds row')
                if ((after[0x53] >> shift) & 15) != DIRECTIONS[reverse['direction']][0]:
                    raise ValueError('Reversal input not consumed')
                reverse_values.append(after[coordinate])
            if not any((value - end) * sign < 0 for value in reverse_values):
                raise ValueError('No observed response to reversal')
            observations.append({'player': side, 'bounds_row': 0, 'direction': direction,
                                 'source_callback_interval': [rows[0]['ordinal'], rows[-1]['ordinal']],
                                 'start_coordinate': states[0][0][coordinate], 'stopped_coordinate': end,
                                 'held_callback_interval': [rows[-8]['ordinal'], rows[-1]['ordinal']],
                                 'held_tick_parities': sorted({before[0x6B] & 1 for before, _ in held}),
                                 'reversal_callback_interval': [reversals[0]['ordinal'], reversals[-1]['ordinal']],
                                 'reversal_coordinates': reverse_values})
    required = {(side, direction) for side in limits for direction in DIRECTIONS}
    if {(row['player'], row['direction']) for row in observations} != required:
        raise ValueError('Missing row-zero direction/player evidence')
    return {'observed_movement_limits': observations,
            'remaining_bounds_rows': {'lower': [1, 2, 3], 'upper': [1, 2, 3]},
            'complete_F1': False}


if __name__ == '__main__':
    from round_reference import validate_fixture
    case = json.loads((ROOT / 'tests/cases/movement-serve-bounds.json').read_text())
    fixture = json.loads((ROOT / case['reference']).read_text())
    validate_fixture(fixture)
    report = validate_movement(fixture, case)
    (ROOT / 'build/tests/movement-coverage.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
