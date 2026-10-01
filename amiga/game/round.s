; Shared main-path round lifecycle. Poll between callbacks, never from a
; captured callback kind. Scoring owns the service mode; tail clocks/audio
; continue while gameplay is paused. Presentation/audio remain temporary ABI.
game_round_poll:
        movem.l d0-d7/a0-a4,-(sp)
        tst.b   game_score_initialized
        beq     .done
        lea     game_score_state,a4
        cmpi.w  #GAME_ROUND_PAUSE,game_lifecycle
        beq     .pause
        cmpi.w  #GAME_ROUND_SOUND,game_lifecycle
        beq     .sound
        cmpi.w  #GAME_PLAYING,game_lifecycle
        bne     .done
        btst    #5,S_MODE(a4)
        beq     .done
; Match-result handling belongs to CT-06.
        btst    #6,S_MODE(a4)
        bne     .done
        move.w  #GAME_ROUND_PAUSE,game_lifecycle
        move.b  #$81,$02(a5)
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
        move.b  d0,$3d(a5)
        move.b  #$f4,$4c(a5)
        move.b  #$fd,$48(a5)
        btst    #4,d0
        beq.s   .players
        move.b  #$fd,$4c(a5)
        move.b  #$f4,$48(a5)
.players:
        move.b  #152,$49(a5)
        move.b  #192,$4a(a5)
        move.b  #8,$45(a5)
        move.b  #88,$46(a5)
        move.b  #7,$4b(a5)
        clr.b   $47(a5)
        bsr     build_player_sprites
        bsr     upload_sprite_attributes
        clr.b   $6c(a5)
        bra     .done
.pause:
        cmpi.b  #$80,$6c(a5)
        bcs     .done
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
        move.b  d1,$3c(a5)
        move.b  #S_WAIT_SOUND,S_STAGE(a4)
        move.b  #$20,$42(a5)
        bsr     draw_pending_scoreboard_mode_and_scores
        bsr     assign_sound_stream_4
        move.w  #GAME_ROUND_SOUND,game_lifecycle
        bra.s   .done
.sound:
        move.b  $a4(a5),d0
        cmp.b   $a5(a5),d0
        bne.s   .done
        move.w  #GAME_PLAYING,game_lifecycle
.done:
        movem.l (sp)+,d0-d7/a0-a4
        rts
