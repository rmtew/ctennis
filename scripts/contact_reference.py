"""Validate a bounded source action-timing set; never calculate game results."""
import hashlib
import json
from pathlib import Path

from round_reference import validate_fixture, CONTACT_CASES as CASES

ROOT = Path(__file__).resolve().parent.parent


def validate_contact(fixture, case):
    contract = case['contact_timing']
    contact, onset = contract['contact_update'], contract['action_onset_frame']
    if case['name'] not in CASES or contact != 707 or onset != 2005 + CASES.index(case['name']):
        raise ValueError('Unsupported contact timing recipe')
    parent_path = ROOT / 'tests/reference/two-player-rally.json'
    payload = parent_path.read_bytes()
    parent = json.loads(payload)
    validate_fixture(parent)
    prefix = [row for row in fixture['updates'] if row['frame'] < onset]
    if (prefix != parent['updates'][:len(prefix)]
            or len(prefix) != onset - 1300
            or fixture['initial_post_tail'] != parent['initial_post_tail']):
        raise ValueError('Action timing did not preserve its natural rally prefix')
    row = fixture['updates'][contact - 1]
    markers = [event for event in fixture['timeline'] if event['kind'] == 'M'
               and event['pc'] == 0xFD3 and event['after_callback'] == contact]
    before, after = bytes.fromhex(row['entry_ram']), bytes.fromhex(row['ram'])
    if (len(markers) != 1 or markers[0]['context'] != 'callback'
            or row['frame'] != 2006 or row['callback_kind'] != 'gameplay'
            or before[0x44] & 0xE0 != 0x60 or after[0x3B] != 8
            or not after[0x38] & 0x40):
        raise ValueError('Missing accepted upper contact/launch evidence')
    controls = [event for event in fixture['timeline'] if event['kind'] == 'control'
                and event['control'] == 'p2-button1']
    if [(event['frame'], event['value']) for event in controls] != [(onset, 1), (onset + 4, 0)]:
        raise ValueError('Contact action pulse differs from the fixed four-frame recipe')
    sampled = []
    for update in fixture['updates']:
        if 2004 <= update['frame'] <= 2012:
            inputs = [read['value'] for read in update['inputs'] if read['group'] == 1]
            if len(inputs) != 1 or bool(inputs[0] & 16) != (onset <= update['frame'] < onset + 4):
                raise ValueError('Original input sampler did not consume the action pulse')
            if inputs[0] & 16:
                sampled.append(update['ordinal'])
    if fixture['updates'][-1]['frame'] != 2021:
        raise ValueError('Capture does not retain action release and subsequent flight')
    vector, normal = after[0x60:0x67], bytes.fromhex(parent['updates'][contact - 1]['ram'])[0x60:0x67]
    if (vector == normal) != (onset > 2006):
        raise ValueError('Source action trajectory relationship is absent')
    return {'natural_prefix_callbacks': len(prefix),
            'parent_reference_sha256': hashlib.sha256(payload).hexdigest(),
            'action_onset_frame': onset, 'action_release_frame': onset + 4,
            'action_sampled_callbacks': sampled,
            'accepted_contact_update': contact, 'accepted_contact_frame': row['frame'],
            'contact_entry_player_yx': list(before[0x45:0x47]),
            'contact_entry_ball_yx': list(before[0x34:0x36]),
            'captured_active_flight_vector': vector.hex(),
            'action_changes_trajectory': vector != normal,
            'contact_psg': row['psg'], 'complete_F2': False}


def validate_contact_set():
    observations = []
    for name in CASES:
        case = json.loads((ROOT / f'tests/cases/{name}.json').read_text())
        fixture = json.loads((ROOT / case['reference']).read_text())
        validate_fixture(fixture)
        observations.append({'case': name, **validate_contact(fixture, case)})
    vectors = [row['captured_active_flight_vector'] for row in observations]
    if vectors[0] != vectors[1] or vectors[1] == vectors[2]:
        raise ValueError('Before/at/after set does not distinguish the action boundary')
    return observations


if __name__ == '__main__':
    print(json.dumps(validate_contact_set(), indent=2))
