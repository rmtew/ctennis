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
        bsr     legacy_new_match
        clr.b   $3a(a5)
        clr.b   $3b(a5)
        clr.b   $3c(a5)
        clr.b   $3d(a5)
        clr.b   $42(a5)
        clr.b   $6c(a5)
        bsr     game_show_returned_title
        move.b  #$83,$02(a5)
        st      game_restart_context
        move.w  #GAME_TITLE_TRANSITION,game_lifecycle
        bra     game_round_done
.title_wait:
        cmpi.b  #$ff,$6c(a5)
        bne     game_round_done
        bsr     game_show_returned_court
        move.b  #4,$3d(a5)
        move.b  #$83,$3c(a5)
        move.b  #$81,$02(a5)
        move.b  #$20,$42(a5)
        bsr     upload_sprite_attributes
        bsr     game_result_redraw
        bsr     assign_sound_stream_4
        move.w  #GAME_TITLE_SOUND,game_lifecycle
        bra     game_round_done
.title_sound:
        move.b  $a4(a5),d0
        cmp.b   $a5(a5),d0
        bne     game_round_done
        move.w  #GAME_TITLE,game_lifecycle
        bsr     game_menu_tick
        bra     game_round_done
.restart_sound:
        bsr     game_pair_sound_complete
        tst.b   d0
        beq     game_round_done
        move.b  #$80,$3c(a5)
        tst.b   game_selected_mode
        bne.s   .mode
        move.b  #$81,$3c(a5)
.mode:
        move.b  #$20,$42(a5)
        bsr     game_result_redraw
        bsr     assign_sound_stream_4
        move.w  #GAME_RESTART_SERVE_SOUND,game_lifecycle
        bra     game_round_done
.serve_sound:
        move.b  $a4(a5),d0
        cmp.b   $a5(a5),d0
        bne     game_round_done
        clr.b   game_restart_context
        clr.b   game_score_initialized
        move.w  #GAME_PLAYING,game_lifecycle
        bra     game_round_done

game_restart_begin:
        bsr     game_clear_returned_status
        bsr     game_start_sound
        move.w  #GAME_RESTART_SOUND,game_lifecycle
        rts
