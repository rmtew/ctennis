; Test-only original-byte serialization. Never linked into ordinary product.
capture_import_state:
        movem.l d0-d1/a0-a1,-(sp)
        lea capture_state_fields,a0
.next:
        move.w (a0)+,d0
        bmi.s .done
        move.l (a0)+,a1
        move.b (a5,d0.w),(a1)
        bra.s .next
.done:
        movem.l (sp)+,d0-d1/a0-a1
        rts
capture_export_state:
        movem.l d0-d1/a0-a1,-(sp)
        lea capture_state_fields,a0
.next:
        move.w (a0)+,d0
        bmi.s .done
        move.l (a0)+,a1
        move.b (a1),(a5,d0.w)
        bra.s .next
.done:
        movem.l (sp)+,d0-d1/a0-a1
        rts
capture_reset_match:
        movem.l d7/a0,-(sp)
        lea $10(a5),a0
        move.w #239,d7
.clear:
        clr.b (a0)+
        dbra d7,.clear
        lea $10(a5),a0
        moveq #39,d7
.hide:
        move.b #194,(a0)+
        dbra d7,.hide
        clr.b $36(a5) ; shadow image is native constant frame0
        move.b #1,$7c(a5)
        movem.l (sp)+,d7/a0
        rts
capture_state_fields:
        dc.w $3a
        dc.l game_lower_phase
        dc.w $43
        dc.l game_lower_animation
        dc.w $49
        dc.l game_lower_y
        dc.w $4a
        dc.l game_lower_x
        dc.w $4b
        dc.l game_lower_image
        dc.w $4c
        dc.l game_lower_colour
        dc.w $73
        dc.l game_lower_target_y
        dc.w $74
        dc.l game_lower_target_x
        dc.w $6d
        dc.l game_lower_clock
        dc.w $3b
        dc.l game_upper_phase
        dc.w $44
        dc.l game_upper_animation
        dc.w $45
        dc.l game_upper_y
        dc.w $46
        dc.l game_upper_x
        dc.w $47
        dc.l game_upper_image
        dc.w $48
        dc.l game_upper_colour
        dc.w $75
        dc.l game_upper_target_y
        dc.w $76
        dc.l game_upper_target_x
        dc.w $6e
        dc.l game_upper_clock
        dc.w $34
        dc.l game_court_y
        dc.w $35
        dc.l game_court_x
        dc.w $37
        dc.l game_shadow_colour
        dc.w $38
        dc.l game_flight
        dc.w $39
        dc.l game_contact
        dc.w $4d
        dc.l game_ball_y
        dc.w $4e
        dc.l game_ball_x
        dc.w $4f
        dc.l game_ball_image
        dc.w $50
        dc.l game_ball_colour
        dc.w $57
        dc.l game_launch_x
        dc.w $58
        dc.l game_launch_y
        dc.w $59
        dc.l game_launch_z
        dc.w $5a
        dc.l game_launch_screen_y
        dc.w $5b
        dc.l game_launch_base_x
        dc.w $5c
        dc.l game_launch_base_y
        dc.w $5d
        dc.l game_target_y
        dc.w $5e
        dc.l game_target_x
        dc.w $5f
        dc.l game_height
        dc.w $60
        dc.l game_velocity_x
        dc.w $61
        dc.l game_velocity_y
        dc.w $62
        dc.l game_velocity_z
        dc.w $63
        dc.l game_base_screen_y
        dc.w $64
        dc.l game_base_x
        dc.w $65
        dc.l game_base_y
        dc.w $66
        dc.l game_step
        dc.w $72
        dc.l game_random_seed
        dc.w $6b
        dc.l game_tick
        dc.w $6c
        dc.l game_serve_clock
        dc.w $6f
        dc.l game_action_clock
        dc.w $42
        dc.l game_display
        dc.w $3c
        dc.l game_score_flags
        dc.w $3d
        dc.l game_mode
        dc.w $3e
        dc.l game_point_a
        dc.w $3f
        dc.l game_point_b
        dc.w $40
        dc.l game_games_a
        dc.w $41
        dc.l game_games_b
        dc.w $53
        dc.l game_directions
        dc.w $56
        dc.l game_actions
        dc.w $70
        dc.l game_aux_clock
        dc.w $71
        dc.l game_status_clock
        dc.w $77
        dc.l game_round_game_a
        dc.w $78
        dc.l game_round_game_b
        dc.w -1
        even
