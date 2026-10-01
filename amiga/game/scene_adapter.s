; Temporary scalar game ABI (CT10). It supplies logical score/mode/status
; events; no sprite records, tile strings, VRAM addresses or VDP bytes.
scene_collect_fields:
        lea     game_display_state,a0
        move.b  game_display,D_FLAGS(a0)
        move.b  game_status_clock,D_TIMER(a0)
        move.b  game_mode,D_MODE(a0)
        move.b  game_point_a,D_POINT_A(a0)
        move.b  game_point_b,D_POINT_B(a0)
        move.b  game_games_a,D_GAME_A(a0)
        move.b  game_games_b,D_GAME_B(a0)
        rts
scene_export_display_flags:
        lea     game_display_state,a0
        move.b  D_FLAGS(a0),game_display
        move.b  D_TIMER(a0),game_status_clock
        rts
