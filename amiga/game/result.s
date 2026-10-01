; Native nonblocking match-result and title/restart lifecycle. Called by the
; same main-path poll in the ordinary executable and maintained replay.
; The round poll has already saved D0-D7/A0-A4. Never select by source PC.
game_result_begin:
        move.w  #GAME_RESULT_SOUND,game_lifecycle
        bsr     game_result_sound
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
        bsr     game_pair_sound_complete
        tst.b   d0
        beq     game_round_done
; Clear match ownership, points, games, old actions and audio using the same
; initialization as CT02. Returned title waits through its own display epoch.
        moveq   #0,d0
        bsr     game_new_match
        clr.b   game_lower_phase
        clr.b   game_upper_phase
        clr.b   game_score_flags
        clr.b   game_mode
        clr.b   game_display
        clr.b   game_serve_clock
        bsr     game_show_returned_title
        ifd NATIVE_SCENE_OBSERVE
        move.b  #$83,$02(a5)
        endif
        st      game_restart_context
        move.w  #GAME_TITLE_TRANSITION,game_lifecycle
        bra     game_round_done
.title_wait:
        cmpi.b  #$ff,game_serve_clock
        bne     game_round_done
        bsr     game_show_returned_court
        move.b  #4,game_mode
        move.b  #$83,game_score_flags
        ifd NATIVE_SCENE_OBSERVE
        move.b  #$81,$02(a5)
        endif
        move.b  #$20,game_display
        bsr     game_render_sprites
        bsr     game_result_redraw
        bsr     game_audio_request_cue
        move.w  #GAME_TITLE_SOUND,game_lifecycle
        bra     game_round_done
.title_sound:
        bsr     game_audio_cue_complete
        tst.b   d0
        beq     game_round_done
        move.w  #GAME_TITLE,game_lifecycle
        bsr     game_menu_tick
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
