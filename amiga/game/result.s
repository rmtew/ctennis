; Native nonblocking match-result and title/restart lifecycle. Called by the
; same main-path poll in the ordinary executable and maintained replay.
; The round poll has already saved D0-D7/A0-A4. Never select by source PC.
game_result_begin:
        move.w  #GAME_RESULT_SOUND,game_lifecycle
        clr.b   game_celebration_first_play
        clr.b   game_celebration_armed
        clr.b   game_celebration_pose
        clr.w   game_celebration_loops
        clr.b   game_celebration_audio_fraction
        clr.b   game_serve_clock
        clr.b   game_celebration_winner
        cmpi.b  #6,game_games_a
        beq.s   .winner
        move.b  #1,game_celebration_winner
.winner:
        bsr     game_audio_reset
        bsr     game_result_sound
        bsr     game_latch_old_actions
        bra     game_round_done
game_result_poll:
        cmpi.w  #GAME_RESULT_SOUND,game_lifecycle
        beq     .result
        cmpi.w  #GAME_TITLE_TRANSITION,game_lifecycle
        beq     .title_wait
        cmpi.w  #GAME_TITLE_SOUND,game_lifecycle
        beq     .title_sound
        cmpi.w  #GAME_RESTART_SOUND,game_lifecycle
        beq     .restart_sound
        cmpi.w  #GAME_RESTART_SERVE_SOUND,game_lifecycle
        beq     .serve_sound
        bra     game_round_done
.result:
        bsr     game_celebration_present
        tst.b   game_celebration_first_play
        beq     game_round_done
        tst.b   game_auto_continue
        beq.s   .human_continue
        ; Unattended attract playback returns only after the complete phrase.
        ; A taken-over demo clears automatic continuation and uses the human gate.
        bsr     game_core_return_title_internal
        bra     game_round_done
.human_continue:
        tst.b   game_continue_held
        bne.s   .held
        st      game_celebration_armed
        bra     game_round_done
.held:
        tst.b   game_celebration_armed
        beq     game_round_done
        tst.b   game_continue_pressed
        beq     game_round_done
        bsr     game_core_return_title_internal
        bra     game_round_done
.title_wait:
        cmpi.b  #$ff,game_serve_clock
        bne     game_round_done
        ; Legacy transition also returns directly to the title. It must
        ; never publish a court or trigger another intro after title return.
        bsr     game_core_return_title_internal
        bra     game_round_done
.title_sound:
        bsr     game_audio_cue_complete
        tst.b   d0
        beq     game_round_done
        bsr     game_core_return_title_internal
        bra     game_round_done
.restart_sound:
        bsr     game_pair_sound_complete
        tst.b   d0
        beq     game_round_done
        move.b  #$80,game_score_flags
        tst.b   game_selected_mode
        bne.s   .mode
        move.b  #$81,game_score_flags
.mode:
        move.b  #$20,game_display
        bsr     game_result_redraw
        bsr     game_audio_request_cue
        move.w  #GAME_RESTART_SERVE_SOUND,game_lifecycle
        bra     game_round_done
.serve_sound:
        bsr     game_audio_cue_complete
        tst.b   d0
        beq     game_round_done
        clr.b   game_restart_context
        clr.b   game_score_initialized
        move.w  #GAME_PLAYING,game_lifecycle
        bra     game_round_done

game_restart_begin:
        bsr     game_clear_returned_status
        bsr     game_start_sound
        move.w  #GAME_RESTART_SOUND,game_lifecycle
        rts

; Winner is logical Blue/Red; bit4 maps that identity onto the current end.
; Court halves span native Y40..96 and96..184. Composite pose centres
; are Y+16 (upper) andY+15 (lower), hence authored origins52 and125.
game_celebration_present:
        cmpi.b  #48,game_serve_clock
        bcs     .done
        st      game_celebration_pose
        move.b  game_celebration_winner,d0
        move.b  game_mode,d1
        lsr.b   #4,d1
        andi.b  #1,d1
        eor.b   d1,d0
        clr.b   game_celebration_upper
        tst.b   d0
        beq.s   .lower
        st      game_celebration_upper
        move.b  #120,game_upper_x
        move.b  #52,game_upper_y
        move.b  #11,game_upper_image
        bra.s   .bounce
.lower:
        move.b  #120,game_lower_x
        move.b  #125,game_lower_y
        move.b  #4,game_lower_image
.bounce:
        moveq   #0,d0
        move.b  game_tick,d0
        lsr.b   #3,d0
        andi.b  #3,d0
        cmpi.b  #3,d0
        bne.s   .height
        moveq   #1,d0
.height:
        tst.b   game_celebration_upper
        beq.s   .lower_height
        sub.b   d0,game_upper_y
        bra.s   .build
.lower_height:
        sub.b   d0,game_lower_y
.build:
        bsr     game_scene_build_players
        lea     game_scene_objects+SC_UPPER,a0
        tst.b   game_celebration_upper
        beq.s   .hide
        lea     game_scene_objects+SC_LOWER,a0
.hide:
        clr.b   O_VISIBLE(a0)
        clr.b   O_VISIBLE+O_SIZE(a0)
        clr.b   O_VISIBLE+2*O_SIZE(a0)
        clr.b   game_scene_objects+SC_BALL+O_VISIBLE
        clr.b   game_scene_objects+SC_SHADOW+O_VISIBLE
.done:  rts
game_celebration_reset:
        clr.b   game_celebration_first_play
        clr.b   game_celebration_armed
        clr.b   game_celebration_pose
        clr.b   game_celebration_winner
        clr.b   game_celebration_upper
        clr.w   game_celebration_loops
        clr.b   game_celebration_audio_fraction
        rts
        even
        even
