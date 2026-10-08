; Shared simulation state ABI. Logical held/edge inputs, lifecycle commands,
; match seed and evolving entropy belong to this block, not physical adapters.
; Existing packet widths and labels remain stable; all word/long accesses are
; even-aligned. Reserved packet bytes are owned state and must be initialized.
        even
game_core_state:
game_play_state: dcb.b G_SIZE,0
game_score_state: dcb.b S_SIZE,0
game_audio_voices: dcb.b 3*AV_SIZE,0
game_audio_rate: dc.b 2
game_audio_wait: dc.b 2
game_audio_transpose: dc.b 0
game_audio_due: dc.b 0
game_display_state: dcb.b D_SIZE,0
game_celebration_loops: dc.w 0
game_celebration_first_play: dc.b 0
game_celebration_armed: dc.b 0
game_celebration_pose: dc.b 0
game_celebration_winner: dc.b 0
game_celebration_upper: dc.b 0
game_celebration_audio_fraction: dc.b 0
game_input_bits: dc.b 0,0
game_input_pressed: dc.b 0,0
game_input_released: dc.b 0,0
game_player_controls: dc.b 0,0
game_lower_owner: dc.b 0
game_upper_owner: dc.b 1
game_old_action_latches: dc.b 0,0
game_lifecycle: dc.w GAME_SERVICE
game_legacy_entropy_state: dc.w 0
game_match_seed: dc.w $ace1
game_selection_delay: dc.w 0
game_accept_count: dc.w 0
game_selection_keys: dc.b 0
game_selected_mode: dc.b 0
game_restart_context: dc.b 0
game_score_initialized: dc.b 0
game_scene_objects: dcb.b 8*O_SIZE,0
game_scene_ball_layer: dc.b 2
game_score_flags: dc.b 0
game_directions: dc.b 0
game_actions: dc.b 0
game_aux_clock: dc.b 0
game_status_clock: dc.b 0
game_new_mode: dc.b 0
score_dirty: dc.b 0
field_values: dc.b 0,0,0,0,0,1
game_continue_held: dc.b 0
game_continue_pressed: dc.b 0
game_auto_continue: dc.b 0
game_playback_active: dc.b 0
game_playback_mask: dc.b 0
game_core_command: dc.b 0
game_entropy_policy: dc.b GAME_ENTROPY_MODERN
game_entropy_alignment:
        even
game_entropy_state:
game_modern_entropy_state: dc.w 0
game_core_state_end:
GAME_CORE_STATE_SIZE equ game_core_state_end-game_core_state
