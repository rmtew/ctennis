"""Validate the retained original pad calibration; expose observations, not a game model."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ACTIONS = ('up', 'down', 'left', 'right', 'button1', 'button2')
JOY_NAMES = dict(zip(ACTIONS, ('up', 'down', 'left', 'right', 'red', 'blue')))
VALUES = dict(zip(ACTIONS, (2, 8, 4, 1, 16, 32)))
CASES = tuple(f'p3-input-p{pad}-{action}' for pad in (1, 2) for action in ACTIONS) + ('p3-input-simultaneous',)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_reference():
    policy = json.loads((ROOT / 'tests/cases/physical-input.json').read_text())
    path = ROOT / policy['reference']
    if sha(path) != policy['reference_sha256']:
        raise ValueError('Frozen original input calibration changed')
    source = json.loads(path.read_text())
    if not source['repeat_identical'] or source['capture_sha256'] != policy['capture_sha256']:
        raise ValueError('Original input calibration lacks its repeated capture proof')
    if source['rom_sha256'] != policy['rom_sha256'] or len(source['callbacks']) != 562:
        raise ValueError('Unexpected original input calibration')
    if len(source['observations']) != 14:
        raise ValueError('Original physical control observations incomplete')
    states, samples = {}, {}
    for event in source['timeline']:
        if event['kind'] == 'control':
            states[event['control']] = bool(event['value'])
        elif event['kind'] in ('I0', 'I1'):
            group = int(event['kind'][1])
            key = event['after_callback'], group
            if key in samples:
                raise ValueError('Duplicate original input reader event')
            controls = {action: bool(states.get(f'p{group + 1}-{action}')) for action in ACTIONS}
            encoded = sum(VALUES[action] for action in ACTIONS if controls[action])
            if encoded != event['value']:
                raise ValueError('Original physical events and input reader return differ')
            samples[key] = (controls, event)
    rows = []
    for ordinal, row in enumerate(source['callbacks']):
        if row['ordinal'] != ordinal or sorted(i['group'] for i in row['inputs']) != [0, 1]:
            raise ValueError('Source callback or input reader sequence incomplete')
        ports, expected = [], []
        for group in (0, 1):
            controls, event = samples[ordinal, group]
            original = next(i for i in row['inputs'] if i['group'] == group)
            if event['value'] != original['value'] or event['frame'] != original['frame']:
                raise ValueError('Original callback and input timeline disagree')
            expected.append(original['value'])
            ports.append({'port': policy['amiga_ports'][str(group + 1)],
                          **{JOY_NAMES[action]: value for action, value in controls.items()}})
        ram = bytes.fromhex(row['ram'])
        if ram[0x3d] & 0x94 != 0x80:
            raise ValueError('Calibration no longer has the declared two-player/side ownership')
        rows.append({'update': ordinal, 'source_frame': row['inputs'][-1]['frame'],
                     'ports': ports, 'readers': expected, 'normalized': [ram[0x53], ram[0x56]],
                     'mode_side': ram[0x3d] & 0x94})
    if len(samples) != len(rows) * 2:
        raise ValueError('Extra original input reader events')
    return policy, source, rows


def window(case, rows):
    start, end = case['source_updates']
    if not 1 <= start < end < len(rows):
        raise ValueError('Physical control window outside original capture')
    active = [row for row in rows if any(row['ports'][pad - 1][JOY_NAMES[action]]
              for pad, action in case['controls']) and start <= row['update'] <= end]
    if [row['update'] for row in active] != list(range(start + 1, start + 25)) or rows[start]['readers'] != [0, 0]:
        raise ValueError('Control window lacks neutral start and 24 captured held samples')
    release = active[-1]['update'] + 1
    if end != release + 15 or any(any(row['ports'][pad - 1][JOY_NAMES[action]]
           for pad, action in case['controls']) for row in rows[release:end + 1]):
        raise ValueError('Control window lacks 16 captured release samples')
    return rows[start:end + 1]


def compare_row(expected, actual):
    for group, (wanted, seen) in enumerate(zip(expected['readers'], actual['readers'])):
        if wanted != seen:
            return {'update': expected['update'], 'source_frame': expected['source_frame'],
                    'boundary': 'native-input-reader-return', 'field': f'input group {group}',
                    'expected': wanted, 'actual': seen}
    for field, wanted, seen in zip(('player directions', 'player actions'), expected['normalized'], actual['normalized']):
        if wanted != seen:
            return {'update': expected['update'], 'source_frame': expected['source_frame'],
                    'boundary': 'native-input-normalized', 'field': field, 'expected': wanted, 'actual': seen}
    if expected['mode_side'] != actual['mode_side']:
        return {'update': expected['update'], 'source_frame': expected['source_frame'],
                'boundary': 'native-input-normalized', 'field': 'control ownership',
                'expected': expected['mode_side'], 'actual': actual['mode_side']}
    return None
