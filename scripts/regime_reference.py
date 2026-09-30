"""Validate complete source regimes and prefix-preserving restart extensions."""
import hashlib
import json
from pathlib import Path

from round_reference import validate_fixture

ROOT = Path(__file__).resolve().parent.parent


def load_reference(name):
    payload = (ROOT / f'tests/reference/{name}.json').read_bytes()
    fixture = json.loads(payload)
    validate_fixture(fixture)
    return fixture, hashlib.sha256(payload).hexdigest()


def serve_interval(fixture, start, flight):
    rows = fixture['updates']
    launched = bytes.fromhex(rows[flight - 1]['ram'])
    servers = [side for side, phase in (('lower', 0x3A), ('upper', 0x3B)) if launched[phase] == 0x20]
    if len(servers) != 1:
        raise ValueError('Serve flight does not identify a single timed server')
    side = servers[0]
    phase, animation, receiver = (0x3A, 0x43, 0x3B) if side == 'lower' else (0x3B, 0x44, 0x3A)
    receiver_animation = 0x44 if side == 'lower' else 0x43
    receiver_is_ai = bool(launched[0x3C] & (1 if side == 'lower' else 2))
    receiver_phase = 4 if receiver_is_ai else 0x11
    windup = next((row for row in rows[start - 1:flight]
                   if bytes.fromhex(row['ram'])[phase] == 0x20), None)
    complete = next((row for row in rows[flight:]
                     if bytes.fromhex(row['ram'])[phase] == 0x11
                     and not bytes.fromhex(row['ram'])[animation] & 0x80), None)
    if windup is None or complete is None:
        raise ValueError('Complete serve windup/release is not retained')
    handoff = next((row for row in rows[flight - 1:complete['ordinal']]
                    if bytes.fromhex(row['ram'])[receiver] == receiver_phase
                    and bytes.fromhex(row['ram'])[receiver_animation] & 0x60 == 0x40), None)
    if handoff is None or bytes.fromhex(complete['ram'])[0x6C] < 49:
        raise ValueError('Serve handoff/timed release evidence absent')
    return {'serving_player': side, 'receiver_is_ai': receiver_is_ai,
            'receiver_handoff_phase': receiver_phase, 'windup_update': windup['ordinal'],
            'flight_update': flight, 'handoff_update': handoff['ordinal'],
            'completion_update': complete['ordinal'], 'completion_frame': complete['frame']}


def validate_extension(fixture, case):
    parent, digest = load_reference(case['continuous_parent'])
    count = len(parent['updates'])
    if (fixture['initial_post_tail'] != parent['initial_post_tail']
            or fixture['updates'][:count] != parent['updates'] or len(fixture['updates']) <= count):
        raise ValueError('Restart extension changed or truncated the original full replay')
    milestones = parent['milestones']
    proof = serve_interval(fixture, milestones['restart_gameplay']['update'],
                           milestones['restart_serve_flight']['update'])
    return {'continuous_parent': case['continuous_parent'], 'parent_sha256': digest,
            'identical_prefix_callbacks': count, 'extended_callbacks': len(fixture['updates']) - count,
            'restart_serve': proof}


def regime_layout(parent, case):
    base, digest = load_reference(case['continuous_parent'])
    milestones = base['milestones']
    if case['regime'] in ('round', 'round-tail', 'resumed-serve', 'launched-serve'):
        expected_parent = f"tests/reference/{case['continuous_parent']}.json"
        award, start, flight = 'first_game_award', 'gameplay_resumed', 'resumed_serve_flight'
        required = ('first_game_award', 'tail_only_start', 'gameplay_resumed', 'resumed_serve_flight')
        previous = list(bytes.fromhex(base['initial_post_tail'])[0x40:0x42])
        found = None
        for row in base['updates']:
            state = bytes.fromhex(row['ram'])
            games = list(state[0x40:0x42])
            is_award = sum(games) == sum(previous) + 1 and not state[0x3D] & 0x40
            previous = games
            if not is_award:
                continue
            later = base['updates'][row['ordinal']:]
            tail = next(update for update in later if update['callback_kind'] == 'tail-only')
            resumed = next(update for update in later if update['ordinal'] > tail['ordinal']
                           and update['callback_kind'] == 'gameplay')
            launched = next(update for update in later if update['ordinal'] > resumed['ordinal']
                            and bytes.fromhex(update['ram'])[0x38] & 0x40
                            and bytes.fromhex(update['ram'])[0x66] > 0)
            serve = serve_interval(base, resumed['ordinal'], launched['ordinal'])
            if serve['serving_player'] == case['service_end']:
                found = (row, tail, resumed, launched)
                break
        if found is None:
            raise ValueError('Requested complete serving-end round is absent')
        milestones = {name: {'update': row['ordinal'], 'frame': row['frame']}
                      for name, row in zip(required, found)}
    elif case['regime'] in ('match', 'restarted-serve'):
        name = case['continuous_parent'].replace('-match', '-restart-complete')
        extension_case = json.loads((ROOT / f'tests/cases/{name}.json').read_text())
        validate_extension(parent, extension_case)
        expected_parent = extension_case['reference']
        award, start, flight = 'match_award', 'restart_gameplay', 'restart_serve_flight'
        required = ('match_award', 'restart_selection', 'restart_gameplay', 'restart_serve_flight')
    elif case['regime'] == 'result-tail':
        if case['parent_reference'] != f"tests/reference/{case['continuous_parent']}.json":
            raise ValueError('Result tail uses the wrong source parent')
        tail = next(row for row in base['updates']
                    if row['ordinal'] > milestones['match_award']['update']
                    and row['callback_kind'] == 'tail-only')
        end = milestones['restart_selection']['update']
        return {'initial_source_update': tail['ordinal'], 'updates': end - tail['ordinal'],
                'continuous_parent_sha256': digest,
                'milestones': {'result_tail_start': {'update': tail['ordinal'], 'frame': tail['frame']},
                               'restart_selection': milestones['restart_selection']}}
    else:
        raise ValueError('Unknown complete regime')
    if case['parent_reference'] != expected_parent:
        raise ValueError('Regime uses the wrong source parent')
    serve = serve_interval(parent, milestones[start]['update'], milestones[flight]['update'])
    initial = milestones[award]['update'] - 1
    end = serve['completion_update']
    if case['regime'] == 'round-tail':
        initial, end = milestones['tail_only_start']['update'], milestones[start]['update']
    elif case['regime'] in ('resumed-serve', 'restarted-serve'):
        initial = milestones[start]['update']
    elif case['regime'] == 'launched-serve':
        initial = milestones[flight]['update']
    return {'initial_source_update': initial, 'updates': end - initial,
            'continuous_parent_sha256': digest, 'serve': serve,
            'milestones': {name: milestones[name] for name in required}}


def validate_regime_span(parent, case):
    layout = regime_layout(parent, case)
    if (case['initial_source_update'] != layout['initial_source_update']
            or (case['updates'] < layout['updates'] if case['regime'] == 'resumed-serve'
                else case['updates'] != layout['updates'])):
        raise ValueError('Regime does not cover award through complete subsequent serve')
    return layout
