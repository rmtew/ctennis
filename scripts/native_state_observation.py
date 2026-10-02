"""Read-only named native state observation; no imported memory image or writes."""

FIELDS = (
    'game_action_clock',
    'game_actions',
    'game_aux_clock',
    'game_ball_colour',
    'game_ball_image',
    'game_ball_x',
    'game_ball_y',
    'game_base_screen_y',
    'game_base_x',
    'game_base_y',
    'game_contact',
    'game_court_x',
    'game_court_y',
    'game_directions',
    'game_display',
    'game_flight',
    'game_games_a',
    'game_games_b',
    'game_height',
    'game_launch_base_x',
    'game_launch_base_y',
    'game_launch_screen_y',
    'game_launch_x',
    'game_launch_y',
    'game_launch_z',
    'game_lower_animation',
    'game_lower_clock',
    'game_lower_colour',
    'game_lower_image',
    'game_lower_phase',
    'game_lower_target_x',
    'game_lower_target_y',
    'game_lower_x',
    'game_lower_y',
    'game_mode',
    'game_point_a',
    'game_point_b',
    'game_random_seed',
    'game_round_game_a',
    'game_round_game_b',
    'game_score_flags',
    'game_serve_clock',
    'game_shadow_colour',
    'game_status_clock',
    'game_step',
    'game_target_x',
    'game_target_y',
    'game_tick',
    'game_upper_animation',
    'game_upper_clock',
    'game_upper_colour',
    'game_upper_image',
    'game_upper_phase',
    'game_upper_target_x',
    'game_upper_target_y',
    'game_upper_x',
    'game_upper_y',
    'game_velocity_x',
    'game_velocity_y',
    'game_velocity_z',
)


def field_addresses(base, symbols):
    return {name: base + symbols[name] for name in FIELDS}


def read_native_state(session, base, symbols):
    addresses = field_addresses(base, symbols)
    groups = []
    for address in sorted(set(addresses.values())):
        if groups and address <= groups[-1][1] + 4:
            groups[-1][1] = address + 1
        else:
            groups.append([address, address + 1])
    values = {}
    for start, end in groups:
        data = bytes.fromhex(session.inspect('mem_read', {'addr': start, 'len': end-start})['data'])
        values.update((start+i, v) for i, v in enumerate(data))
    return {name: values[address] for name, address in addresses.items()}
