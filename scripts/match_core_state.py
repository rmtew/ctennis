"""Versioned ownership contract for the production contiguous match state.

Packet interiors use the existing G_/S_/AV_/D_/O_ assembly field definitions.
Every byte, including packet reserves and trailing alignment, is checkpointed.
No hardware/UI buffer or relocated address belongs to this inventory.
"""
SCHEMA_VERSION = 1
SIMULATION_VERSION = 2
STATE_BYTES = 314
FIELDS = (
    ('game_play_state',60), ('game_score_state',28), ('game_audio_voices',96),
    ('game_audio_rate',1), ('game_audio_wait',1), ('game_audio_transpose',1),
    ('game_audio_due',1), ('game_display_state',8), ('game_celebration_loops',2),
    ('game_celebration_first_play',1), ('game_celebration_armed',1),
    ('game_celebration_pose',1), ('game_celebration_winner',1),
    ('game_celebration_upper',1), ('game_celebration_audio_fraction',1),
    ('game_input_bits',2), ('game_input_pressed',2), ('game_input_released',2),
    ('game_player_controls',2), ('game_lower_owner',1), ('game_upper_owner',1),
    ('game_old_action_latches',2), ('game_lifecycle',2), ('game_entropy_state',2),
    ('game_match_seed',2), ('game_selection_delay',2), ('game_accept_count',2),
    ('game_selection_keys',1), ('game_selected_mode',1), ('game_restart_context',1),
    ('game_score_initialized',1), ('game_scene_objects',64),
    ('game_scene_ball_layer',1), ('game_score_flags',1), ('game_directions',1),
    ('game_actions',1), ('game_aux_clock',1), ('game_status_clock',1),
    ('game_new_mode',1), ('score_dirty',1), ('field_values',6),
    ('game_continue_held',1), ('game_continue_pressed',1), ('game_auto_continue',1),
    ('game_playback_active',1), ('game_playback_mask',1), ('game_core_command',1),
)


def inventory(symbols):
    """Reject layout drift instead of silently interpreting a different ABI."""
    start = symbols['game_core_state']
    if symbols['game_core_state_end']-start != STATE_BYTES:
        raise ValueError('Incompatible canonical state size')
    offset = 0
    result = []
    for name,size in FIELDS:
        if symbols[name]-start != offset:
            raise ValueError('Incompatible canonical state field: '+name)
        result.append({'name':name,'offset':offset,'bytes':size})
        offset += size
    if offset % 2:
        result.append({'name':'alignment_reserved','offset':offset,'bytes':1})
        offset += 1
    if offset != STATE_BYTES:
        raise ValueError('Ownership does not cover complete state')
    return {'schema_version':SCHEMA_VERSION,'simulation_version':SIMULATION_VERSION,
            'bytes':STATE_BYTES,'fields':result}


def validate_record(record, symbols, rules_sha256):
    """Validate an internal checkpoint envelope before restoring its raw bytes."""
    expected = inventory(symbols)
    if record.get('schema_version') != expected['schema_version']:
        raise ValueError('Incompatible state schema')
    if record.get('simulation_version') != expected['simulation_version']:
        raise ValueError('Incompatible simulation version')
    if record.get('rules_sha256') != rules_sha256:
        raise ValueError('Incompatible simulation build')
    try:
        data = bytes.fromhex(record['state'])
    except (KeyError,TypeError,ValueError) as error:
        raise ValueError('Invalid canonical state encoding') from error
    if len(data) != STATE_BYTES:
        raise ValueError('Incomplete canonical state')
    clips = (('native_audio_score_0','native_audio_score_1'),
             ('native_audio_score_1','native_audio_score_4'),
             ('native_victory_melody','native_victory_bass'),
             ('native_victory_bass','native_victory_arpeggio'),
             ('native_audio_score_4','native_audio_score_5'),
             ('native_audio_score_5','native_audio_periods'),
             ('native_victory_arpeggio','native_victory_periods'))
    for voice in range(3):
        packet = data[88+voice*32:120+voice*32]
        offset, clip = int.from_bytes(packet[:4],'big'), packet[4]
        if offset == 0 and (clip == 255 or packet == bytes(32)):
            continue
        if clip >= len(clips):
            raise ValueError('Invalid audio clip ID')
        first,last = clips[clip]
        low,high = symbols[first]-symbols['native_audio_scores'],symbols[last]-symbols['native_audio_scores']
        if (not low <= offset <= high or (offset-low) % 16
                or offset == high and not packet[6]):
            raise ValueError('Invalid audio table offset')
    return data
