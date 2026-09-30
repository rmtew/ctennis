"""Parse exact source callback records and validate the round-transition oracle."""
from collections import Counter

MOVEMENT_CASES = ('movement-serve-bounds', 'movement-alternate-serve-bounds')
FOCUSED_CASES = MOVEMENT_CASES + ('two-player-rally',)


def parse_capture(payload):
    callbacks, timeline = [], []
    current = None
    pending = None
    active = False
    for sequence, line in enumerate(payload.decode('ascii').splitlines(), 1):
        written_sequence, text = line.split('\t', 1)
        if int(written_sequence) != sequence:
            raise ValueError('Capture sequence is not contiguous')
        tokens = text.split()
        if tokens[0] != 'REF':
            raise ValueError('Unknown record prefix')
        kind = tokens[1]
        if kind == 'D':
            if pending is None:
                raise ValueError('State chunk without a boundary')
            offset, words = int(tokens[2]), tokens[3]
            if offset != len(pending['bytes']) or len(words) != 128:
                raise ValueError('Incomplete or reordered state chunks')
            for start in range(0, 128, 16):
                pending['bytes'].extend(int(words[start:start + 16], 16).to_bytes(8, 'little'))
            if len(pending['bytes']) == 256:
                current[pending['field']] = pending['bytes'].hex().upper()
                pending = None
            continue
        if pending is not None:
            raise ValueError('Interrupted state snapshot')
        if kind == 'CONTROL':
            timeline.append({'sequence': sequence, 'kind': 'control', 'frame': int(tokens[2]),
                             'control': tokens[3], 'value': int(tokens[4])})
            continue
        ordinal, frame, pc = int(tokens[2]), int(tokens[3]), int(tokens[4], 16)
        if kind in ('B', 'T', 'E') and pc != {'B': 0x49, 'T': 0x6B1, 'E': 0x45}[kind]:
            raise ValueError('Wrong source instruction boundary')
        if kind == 'B':
            if active or ordinal != len(callbacks):
                raise ValueError('Overlapping or missing callback')
            target = int(tokens[5], 16)
            if target not in (0x699, 0x6B1):
                raise ValueError(f'Unexpected callback {target:04X}')
            current = {'ordinal': ordinal, 'begin_frame': frame, 'callback_address': target,
                       'callback_kind': 'gameplay' if target == 0x699 else 'tail-only',
                       'psg': [], 'inputs': [], 'refresh_reads': [], 'before_events': []}
            callbacks.append(current)
            active = True
        if ordinal < 0:
            # The capture starts during an earlier callback. Its partial prefix
            # is retained in raw evidence, not treated as an initial full state.
            continue
        if current is None or ordinal != current['ordinal']:
            raise ValueError('Event has wrong callback ordinal')
        event = {'sequence': sequence, 'kind': kind, 'after_callback': ordinal,
                 'frame': frame, 'pc': pc, 'context': 'callback' if active else 'between-callbacks'}
        if kind in ('B', 'T', 'E'):
            field = {'B': 'entry_ram', 'T': 'ram', 'E': 'post_tail_ram'}[kind]
            if field in current:
                raise ValueError('Duplicate callback boundary')
            pending = {'field': field, 'bytes': bytearray()}
            if kind == 'T':
                current['frame'] = frame
            elif kind == 'E':
                current['end_frame'] = frame
                active = False
            event['boundary'] = field
        elif kind in ('I0', 'I1', 'R', 'P'):
            value = int(tokens[5], 16)
            event['value'] = value
            if kind in ('I0', 'I1'):
                if not active:
                    raise ValueError('Input outside captured callback')
                current['inputs'].append({'group': int(kind[1]), 'value': value, 'pc': pc, 'frame': frame})
            elif kind == 'R':
                if not active:
                    raise ValueError('Refresh read outside callback')
                current['refresh_reads'].append({'pc': pc, 'value': value, 'bit': value & 1})
            elif active:
                current['psg'].append(value)
        elif kind == 'W':
            if active:
                raise ValueError('Between-callback write marked inside callback')
            event.update(address=int(tokens[5], 16), before=int(tokens[6], 16), after=int(tokens[7], 16))
            event['actor'] = 'irq-protocol' if 0x669 <= pc < 0x699 or 0x38 <= pc < 0x4B else 'main-thread'
        elif kind != 'M':
            raise ValueError(f'Unknown event {kind}')
        timeline.append(event)
    if pending is not None or active:
        raise ValueError('Capture ends within a callback')
    for callback in callbacks:
        for field in ('entry_ram', 'ram', 'post_tail_ram'):
            if len(bytes.fromhex(callback[field])) != 256:
                raise ValueError('Invalid RAM extent')
    return callbacks, timeline


def build_fixture(payload, metadata, *, complete_match=False):
    callbacks, timeline = parse_capture(payload)
    if callbacks[0]['frame'] != 1299:
        raise ValueError('Wrong initial callback')
    initial = callbacks[0]
    game_award = next((row for row in callbacks if sum(bytes.fromhex(row['ram'])[0x40:0x42]) == 1), None)
    if game_award is None:
        raise ValueError('First game award missing')
    tail = next((row for row in callbacks if row['ordinal'] > game_award['ordinal'] and row['callback_kind'] == 'tail-only'), None)
    if tail is None:
        raise ValueError('Tail-only pause missing')
    resumed = next((row for row in callbacks if row['ordinal'] > tail['ordinal'] and row['callback_kind'] == 'gameplay'), None)
    if resumed is None:
        raise ValueError('Gameplay restoration missing')
    served = next((row for row in callbacks if row['ordinal'] > resumed['ordinal']
                   and bytes.fromhex(row['ram'])[0x38] & 0x40 and bytes.fromhex(row['ram'])[0x66] > 0), None)
    if served is None:
        raise ValueError('First resumed serve flight missing')
    milestone_rows = [('first_game_award', game_award), ('tail_only_start', tail),
                      ('gameplay_resumed', resumed), ('resumed_serve_flight', served)]
    if complete_match:
        match = next(row for row in callbacks if bytes.fromhex(row['ram'])[0x3D] & 0x40)
        selection = next(row for row in callbacks if row['ordinal'] > match['ordinal']
                         and bytes.fromhex(row['ram'])[0x3D] & 4)
        restarted = next(row for row in callbacks if row['ordinal'] > selection['ordinal']
                         and row['callback_kind'] == 'gameplay'
                         and not bytes.fromhex(row['ram'])[0x3D] & 4)
        flight = next(row for row in callbacks if row['ordinal'] > restarted['ordinal']
                      and bytes.fromhex(row['ram'])[0x38] & 0x40
                      and bytes.fromhex(row['ram'])[0x66] > 0)
        milestone_rows += [('match_award', match), ('restart_selection', selection),
                           ('restart_gameplay', restarted), ('restart_serve_flight', flight)]
    return assemble_fixture(callbacks, timeline, metadata, milestone_rows)


def build_focused_fixture(payload, metadata):
    callbacks, timeline = parse_capture(payload)
    if callbacks[0]['frame'] != 1299 or len(callbacks) < 2:
        raise ValueError('Wrong focused initial callback')
    return assemble_fixture(callbacks, timeline,
                            {**metadata, 'reference_kind': 'source-focused'},
                            [('focused_stop', callbacks[-1])])


def assemble_fixture(callbacks, timeline, metadata, milestone_rows):
    initial = callbacks[0]
    last = milestone_rows[-1][1]['ordinal']
    updates = callbacks[1:last + 1]
    timeline = [event for event in timeline if event.get('after_callback', 0) <= last]
    # Exclude events after the final callback's return. Preserve all events
    # between earlier callbacks; these include the source main-thread actions.
    final_return = next(event['sequence'] for event in timeline if event['kind'] == 'E' and event['after_callback'] == last)
    timeline = [event for event in timeline if event['sequence'] <= final_return]
    between = []
    for event in timeline:
        if event['kind'] in ('B', 'T', 'E'):
            if event['kind'] == 'B' and event['after_callback'] > 0:
                updates[event['after_callback'] - 1]['before_events'] = between
                between = []
        elif event.get('context') == 'between-callbacks' and event['kind'] in ('M', 'W', 'P'):
            between.append(event)
    fixture = {**metadata, 'schema_version': 2, 'initial_pre_tail': initial['ram'],
               'initial_post_tail': initial['post_tail_ram'], 'initial_psg': initial['psg'],
               'initial_callback': initial,
               'updates': updates, 'timeline': timeline,
               'milestones': {name: {'update': row['ordinal'], 'frame': row['frame']}
                              for name, row in milestone_rows}}
    validate_fixture(fixture)
    return fixture


def validate_fixture(fixture):
    """Validate replay continuity and independently observed transition effects."""
    if fixture.get('schema_version') != 2:
        raise ValueError('Unsupported callback reference schema')
    updates = fixture['updates']
    if not fixture['repeat_identical'] or [row['ordinal'] for row in updates] != list(range(1, len(updates) + 1)):
        raise ValueError('Non-deterministic or incomplete callback sequence')
    state = bytearray.fromhex(fixture['initial_post_tail'])
    if len(state) != 256:
        raise ValueError('Invalid initial state extent')
    for row in updates:
        if any(len(bytes.fromhex(row[field])) != 256 for field in ('entry_ram', 'ram', 'post_tail_ram')):
            raise ValueError('Invalid callback state extent')
        if not row['begin_frame'] <= row['frame'] <= row['end_frame']:
            raise ValueError('Source boundary times are not ordered')
        for event in row['before_events']:
            if event['kind'] == 'W':
                offset = event['address'] - 0xC000
                if offset == 0x6B and not (event['pc'] == 0x1E9 and event['after'] == 0
                                         and event.get('actor') == 'main-thread'):
                    raise ValueError('Uncaptured callback counter write between callbacks')
                if state[offset] != event['before']:
                    raise ValueError(f'Unaccounted state before callback {row["ordinal"]} at {offset:02X}')
                state[offset] = event['after']
        if state != bytearray.fromhex(row['entry_ram']):
            raise ValueError(f'Missing between-callback state effects at {row["ordinal"]}')
        kind = row['callback_kind']
        target = state[0] | state[1] << 8
        if target != row['callback_address'] or kind != ('gameplay' if target == 0x699 else 'tail-only'):
            raise ValueError('Callback kind does not match source dispatch state')
        if kind == 'tail-only':
            if row['inputs'] or row['refresh_reads'] or row['entry_ram'] != row['ram']:
                raise ValueError('Tail-only callback contains gameplay work')
        elif kind != 'gameplay':
            raise ValueError('Unknown callback kind')
        before, after = bytes.fromhex(row['ram']), bytes.fromhex(row['post_tail_ram'])
        if after[0x6B] != (before[0x6B] + 1) & 255:
            raise ValueError('Callback tail tick did not advance once')
        for offset in range(0x6C, 0x72):
            if after[offset] != min(before[offset] + 1, 255):
                raise ValueError('Incorrect source saturating timer observation')
        state = bytearray(after)
    milestones = fixture['milestones']
    between = [event for row in updates for event in row['before_events']]
    if fixture.get('reference_kind') == 'source-focused':
        if list(milestones) != ['focused_stop'] or milestones['focused_stop'] != {
                'update': len(updates), 'frame': updates[-1]['frame']}:
            raise ValueError('Focused stop does not match final complete callback')
        bounds = fixture['capture_bounds']
        if not updates[-1]['end_frame'] <= bounds['last_begin_frame']:
            raise ValueError('Focused recording exceeded its finite stop')
        return replay_summary(updates, between, milestones)
    names = ['first_game_award', 'tail_only_start', 'gameplay_resumed', 'resumed_serve_flight']
    if 'match_award' in milestones:
        names += ['match_award', 'restart_selection', 'restart_gameplay', 'restart_serve_flight']
    if list(milestones) != names:
        raise ValueError('Missing transition milestones')
    ordinals = [value['update'] for value in milestones.values()]
    if ordinals != sorted(set(ordinals)) or ordinals[-1] != len(updates):
        raise ValueError('Milestones do not form the requested replay')
    rows = {name: updates[value['update'] - 1] for name, value in milestones.items()}
    if any(value['frame'] != rows[name]['frame'] for name, value in milestones.items()):
        raise ValueError('Milestone frame does not match callback')
    if sum(bytes.fromhex(rows['first_game_award']['ram'])[0x40:0x42]) != 1:
        raise ValueError('First game award state missing')
    if rows['tail_only_start']['callback_kind'] != 'tail-only':
        raise ValueError('Pause milestone is not tail-only')
    for name in ('gameplay_resumed', 'restart_gameplay'):
        if name in rows and rows[name]['callback_kind'] != 'gameplay':
            raise ValueError('Restoration milestone is not gameplay')
    for name in ('resumed_serve_flight', 'restart_serve_flight'):
        if name in rows:
            ram = bytes.fromhex(rows[name]['ram'])
            if not ram[0x38] & 0x40 or ram[0x66] == 0:
                raise ValueError('Advancing serve milestone missing')
    if 'match_award' in rows:
        if not bytes.fromhex(rows['match_award']['ram'])[0x3D] & 0x40:
            raise ValueError('Match award state missing')
        if not bytes.fromhex(rows['restart_selection']['ram'])[0x3D] & 4:
            raise ValueError('Restart selection state missing')
        if bytes.fromhex(rows['restart_gameplay']['ram'])[0x3D] & 4:
            raise ValueError('Restart still in selection mode')
    between = [event for row in updates for event in row['before_events']]
    installs = [event for event in between if event['kind'] == 'W' and event['address'] in (0xC000, 0xC001)]
    if len(installs) < 4 or not any(event.get('pc') == 0x144 for event in between):
        raise ValueError('Main-thread callback transition evidence missing')
    return replay_summary(updates, between, milestones)


def replay_summary(updates, between, milestones):
    counts = Counter(row['frame'] for row in updates)
    return {'updates': len(updates), 'callback_kinds': dict(Counter(row['callback_kind'] for row in updates)),
            'psg_bytes': sum(len(row['psg']) for row in updates),
            'refresh_decisions': sum(len(row['refresh_reads']) for row in updates),
            'between_callback_writes': sum(event['kind'] == 'W' for event in between),
            'multiple_callback_frames': {str(frame): count for frame, count in counts.items() if count > 1},
            'milestones': milestones}
