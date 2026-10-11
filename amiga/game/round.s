; Shared main-path round lifecycle. Poll between callbacks, never from a
; captured callback kind. Scoring owns the service mode; tail clocks/audio
; continue while gameplay is paused. Presentation/audio remain native integration fields.
game_round_poll_body:
        movem.l d0-d7/a0-a4,-(sp)
        tst.b   game_restart_context-game_core_state(a5)
        beq.s   .non_menu
        cmpi.w  #GAME_TITLE,game_lifecycle-game_core_state(a5)
        beq.s   .menu
        cmpi.w  #GAME_SELECTION_HELD,game_lifecycle-game_core_state(a5)
        bne.s   .non_menu
.menu:
        bsr     game_menu_tick
        bra     game_round_done
.non_menu:
        cmpi.w  #GAME_RESULT_SOUND,game_lifecycle-game_core_state(a5)
        bcc     game_result_poll
        tst.b   game_score_initialized-game_core_state(a5)
        beq     game_round_done
        lea     game_score_state-game_core_state(a5),a4
        cmpi.w  #GAME_ROUND_PAUSE,game_lifecycle-game_core_state(a5)
        beq     .pause
        cmpi.w  #GAME_ROUND_SOUND,game_lifecycle-game_core_state(a5)
        beq     .sound
        cmpi.w  #GAME_PLAYING,game_lifecycle-game_core_state(a5)
        bne     game_round_done
        btst    #5,S_MODE(a4)
        beq     game_round_done
; Match award enters the native result/title lifecycle.
        btst    #6,S_MODE(a4)
        bne     game_result_begin
        move.w  #GAME_ROUND_PAUSE,game_lifecycle-game_core_state(a5)
        move.b  S_MODE(a4),d0
        andi.b  #$d7,d0
        move.b  d0,d1
        andi.b  #$ec,d1
        addq.b  #1,d0
        andi.b  #3,d0
        beq.s   .mode
        cmpi.b  #3,d0
        beq.s   .mode
        bset    #4,d0
.mode:
        or.b    d1,d0
        move.b  d0,S_MODE(a4)
        move.b  d0,game_mode-game_core_state(a5)
        move.b  #$f4,game_lower_colour-game_core_state(a5)
        move.b  #$fd,game_upper_colour-game_core_state(a5)
        btst    #4,d0
        beq.s   .players
        move.b  #$fd,game_lower_colour-game_core_state(a5)
        move.b  #$f4,game_upper_colour-game_core_state(a5)
.players:
        move.b  #152,game_lower_y-game_core_state(a5)
        move.b  #192,game_lower_x-game_core_state(a5)
        move.b  #8,game_upper_y-game_core_state(a5)
        move.b  #88,game_upper_x-game_core_state(a5)
        move.b  #7,game_lower_image-game_core_state(a5)
        clr.b   game_upper_image-game_core_state(a5)
        bsr     game_scene_build_players
        bsr     game_render_sprites
        clr.b   game_serve_clock-game_core_state(a5)
        bra     game_round_done
.pause:
        cmpi.b  #$80,game_serve_clock-game_core_state(a5)
        bcs     game_round_done
        moveq   #0,d0
        move.b  S_MODE(a4),d0
        moveq   #0,d1
        btst    #7,d0
        bne.s   .controls
        moveq   #1,d1
        btst    #4,d0
        beq.s   .controls
        moveq   #2,d1
.controls:
        move.b  d1,S_AI(a4)
        ori.b   #$80,d1
        move.b  d1,game_score_flags-game_core_state(a5)
        move.b  #S_WAIT_SOUND,S_STAGE(a4)
        move.b  #$20,game_display-game_core_state(a5)
        bsr     game_scene_redraw_fields
        bsr     game_audio_request_cue
        move.w  #GAME_ROUND_SOUND,game_lifecycle-game_core_state(a5)
        bra.s   game_round_done
.sound:
        bsr     game_audio_cue_complete
        tst.b   d0
        beq.s   game_round_done
        move.w  #GAME_PLAYING,game_lifecycle-game_core_state(a5)
game_round_done:
        movem.l (sp)+,d0-d7/a0-a4
        rts
