; Native logical player assignment and physical action packet.
game_prepare_controls:
        bsr     game_assign_styles
        clr.b   G_SOUND_EVENT(a4)
        move.b  game_score_flags,d0
        move.b  d0,d1
        andi.b  #1,d0
        move.b  d0,G_UPPER_AI(a4)
        move.b  d1,d0
        andi.b  #2,d0
        move.b  d0,G_LOWER_AI(a4)
        andi.b  #$40,d1
        move.b  d1,G_TRACK_AI(a4)
        move.b  game_mode,d0
        andi.b  #8,d0
        move.b  d0,G_FLIP_SERVE(a4)
        move.b  game_directions,d0
        move.b  game_actions,d1
        btst    #4,game_mode
        beq   .native_controls_ordered
        rol.b   #4,d0
        rol.b   #4,d1
.native_controls_ordered:
        move.b  d0,d2
        andi.b  #15,d0
        move.b  d0,G_LOWER_DIRECTION(a4)
        lsr.b   #4,d2
        move.b  d2,G_UPPER_DIRECTION(a4)
        move.b  d1,d2
        andi.b  #3,d1
        move.b  d1,G_LOWER_ACTION(a4)
        lsr.b   #4,d2
        andi.b  #3,d2
        move.b  d2,G_UPPER_ACTION(a4)
        rts

game_finish_controls:
        move.b  G_UPPER_DIRECTION(a4),d0
        lsl.b   #4,d0
        or.b    G_LOWER_DIRECTION(a4),d0
        btst    #4,game_mode
        beq   .native_export_directions
        rol.b   #4,d0
.native_export_directions:
        move.b  d0,game_directions
        tst.b   G_SOUND_EVENT(a4)
        beq   .native_export_done
        bsr     game_audio_request_hit
.native_export_done:
        rts

game_entropy:
        movem.l d1-d7/a0-a6,-(sp)
        ifd LIVE_REFRESH_ADAPTER
        bsr     read_refresh_adapter
        else
        ifd PRODUCT_REPLAY
        moveq   #0,d0
        else
        move.b  $bfe401,d0
        endif
        endif
        andi.l  #1,d0
        movem.l (sp)+,d1-d7/a0-a6
        rts


game_assign_styles:
        move.b  #2,G_LOWER+P_STYLE(a4)
        move.b  #3,G_UPPER+P_STYLE(a4)
        btst    #4,game_mode
        beq.s   .styles_ready
        move.b  #3,G_LOWER+P_STYLE(a4)
        move.b  #2,G_UPPER+P_STYLE(a4)
.styles_ready:
        rts
