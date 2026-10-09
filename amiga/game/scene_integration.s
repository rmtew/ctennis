; Native scalar presentation integration for logical score/mode/status events.
scene_collect_fields:
        lea     game_display_state-game_core_state(a5),a0
        move.b  game_display-game_core_state(a5),D_FLAGS(a0)
        move.b  game_status_clock-game_core_state(a5),D_TIMER(a0)
        move.b  game_mode-game_core_state(a5),D_MODE(a0)
        move.b  game_point_a-game_core_state(a5),D_POINT_A(a0)
        move.b  game_point_b-game_core_state(a5),D_POINT_B(a0)
        move.b  game_games_a-game_core_state(a5),D_GAME_A(a0)
        move.b  game_games_b-game_core_state(a5),D_GAME_B(a0)
        rts
scene_export_display_flags:
        lea     game_display_state-game_core_state(a5),a0
        move.b  D_FLAGS(a0),game_display-game_core_state(a5)
        move.b  D_TIMER(a0),game_status_clock-game_core_state(a5)
        rts
