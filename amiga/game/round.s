; Shared main-path round lifecycle. Poll between callbacks, never from a
; captured callback kind. Scoring owns the service mode; tail clocks/audio
; continue while gameplay is paused. Presentation/audio remain temporary ABI.
game_round_poll:
        movem.l d0-d7/a0-a4,-(sp)
        tst.b   game_restart_context
        beq.s   .non_menu
        cmpi.w  #GAME_TITLE,game_lifecycle
        beq.s   .menu
        cmpi.w  #GAME_SELECTION_HELD,game_lifecycle
        bne.s   .non_menu
.menu:
        bsr     game_menu_tick
        bra     game_round_done
.non_menu:
        cmpi.w  #GAME_RESULT_SOUND,game_lifecycle
        bcc     game_result_poll
        tst.b   game_score_initialized
        beq     game_round_done
        lea     game_score_state,a4
        cmpi.w  #GAME_ROUND_PAUSE,game_lifecycle
        beq     .pause
        cmpi.w  #GAME_ROUND_SOUND,game_lifecycle
        beq     .sound
        cmpi.w  #GAME_PLAYING,game_lifecycle
        bne     game_round_done
        btst    #5,S_MODE(a4)
        beq     game_round_done
; Match award enters the native result/title lifecycle.
        btst    #6,S_MODE(a4)
        bne     game_result_begin
        move.w  #GAME_ROUND_PAUSE,game_lifecycle
        ifd NATIVE_SCENE_OBSERVE
        move.b  #$81,$02(a5)
        endif
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
        move.b  d0,game_mode
        move.b  #$f4,game_lower_colour
        move.b  #$fd,game_upper_colour
        btst    #4,d0
        beq.s   .players
        move.b  #$fd,game_lower_colour
        move.b  #$f4,game_upper_colour
.players:
        move.b  #152,game_lower_y
        move.b  #192,game_lower_x
        move.b  #8,game_upper_y
        move.b  #88,game_upper_x
        move.b  #7,game_lower_image
        clr.b   game_upper_image
        bsr     game_scene_build_players
        bsr     game_render_sprites
        clr.b   game_serve_clock
        bra     game_round_done
.pause:
        cmpi.b  #$80,game_serve_clock
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
        move.b  d1,game_score_flags
        move.b  #S_WAIT_SOUND,S_STAGE(a4)
        move.b  #$20,game_display
        bsr     game_scene_redraw_fields
        bsr     game_audio_request_cue
        move.w  #GAME_ROUND_SOUND,game_lifecycle
        bra.s   game_round_done
.sound:
        bsr     game_audio_cue_complete
        tst.b   d0
        beq.s   game_round_done
        move.w  #GAME_PLAYING,game_lifecycle
game_round_done:
        movem.l (sp)+,d0-d7/a0-a4
        rts
