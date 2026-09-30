"""Index actual source return markers and point awards in a continuous rally."""
MARKERS = {0xC9F: ('lower', 0x3A), 0xFD3: ('upper', 0x3B)}


def validate_rally(fixture, case):
    requirement = case['rally_requirement']
    if requirement['minimum_returns'] < 4 or set(requirement['players']) != {'lower', 'upper'}:
        raise ValueError('Rally requirement weakened below the reference specification')
    markers = {}
    for event in fixture['timeline']:
        if event['kind'] == 'M' and event['pc'] in MARKERS:
            if event['context'] != 'callback':
                raise ValueError('Accepted-return marker outside gameplay callback')
            markers.setdefault(event['after_callback'], []).append(event)
    previous_score = list(bytes.fromhex(fixture['initial_post_tail'])[0x3E:0x40])
    completed, returns = [], []
    for row in fixture['updates']:
        state = bytes.fromhex(row['ram'])
        score = list(state[0x3E:0x40])
        if score != previous_score:
            if returns:
                completed.append({'first_return_update': returns[0]['update'],
                                  'point_award_update': row['ordinal'], 'point_award_frame': row['frame'],
                                  'score_before': previous_score, 'score_after': score, 'returns': returns})
            returns = []
            previous_score = score
        events = markers.get(row['ordinal'], [])
        if len(events) > 1:
            raise ValueError('Multiple return markers need explicit interpretation')
        for event in events:
            player, phase = MARKERS[event['pc']]
            if row['callback_kind'] != 'gameplay' or state[phase] != 8 or not state[0x38] & 0x40:
                raise ValueError('Return marker lacks launched-flight/animation evidence')
            returns.append({'update': row['ordinal'], 'frame': row['frame'], 'player': player,
                            'court_ball_yx': list(state[0x34:0x36]),
                            'displayed_ball_yx': list(state[0x4D:0x4F]),
                            'active_flight_vector': state[0x60:0x67].hex(),
                            'lower_player_yx': list(state[0x49:0x4B]),
                            'upper_player_yx': list(state[0x45:0x47])})
    qualified = [rally for rally in completed
                 if len(rally['returns']) >= requirement['minimum_returns']
                 and {event['player'] for event in rally['returns']} == set(requirement['players'])]
    if not qualified:
        raise ValueError('No completed same-rally return sequence meeting R2 requirement')
    if not any(rally['returns'][-1]['frame'] < requirement['deliberate_miss_start_frame']
               <= rally['point_award_frame'] for rally in qualified):
        raise ValueError('Deliberate physical miss did not finish the qualifying rally')
    return {'qualifying_completed_rallies': qualified,
            'uncompleted_returns_at_capture_end': len(returns),
            'R2_same_rally_source_requirement_satisfied': True}
