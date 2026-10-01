; Temporary scalar game ABI (CT10). It supplies logical score/mode/status
; events; no sprite records, tile strings, VRAM addresses or VDP bytes.
scene_collect_fields:
        lea     game_display_state,a0
        move.b  $42(a5),D_FLAGS(a0)
        move.b  $71(a5),D_TIMER(a0)
        move.b  $3d(a5),D_MODE(a0)
        move.b  $3e(a5),D_POINT_A(a0)
        move.b  $3f(a5),D_POINT_B(a0)
        move.b  $40(a5),D_GAME_A(a0)
        move.b  $41(a5),D_GAME_B(a0)
        rts
scene_export_display_flags:
        lea     game_display_state,a0
        move.b  D_FLAGS(a0),$42(a5)
        move.b  D_TIMER(a0),$71(a5)
        rts
