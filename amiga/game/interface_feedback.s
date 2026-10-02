; Read-only feedback observer. Logical score cells are fixed Blue/Pink identities.
ui_feedback:
        tst.b   ui_paused
        bne     .done
        clr.b   ui_overlay_kind
        cmpi.w  #GAME_TITLE,game_lifecycle
        beq     .reset
        cmpi.w  #GAME_SELECTION_HELD,game_lifecycle
        beq     .reset
        move.b  game_games_a,d0
        move.b  ui_last_games,d1
        move.b  d0,ui_last_games
        cmp.b   d1,d0
        bls.s   .pink
        move.b  #2,ui_winner
        move.w  #120,ui_win_ticks
.pink:  move.b  game_games_b,d0
        move.b  ui_last_games+1,d1
        move.b  d0,ui_last_games+1
        cmp.b   d1,d0
        bls.s   .demo
        move.b  #3,ui_winner
        move.w  #120,ui_win_ticks
.demo:  tst.b   ui_demo
        beq.s   .win
        move.b  #1,ui_overlay_kind
        tst.w   ui_win_ticks
        beq.s   .done
        subq.w  #1,ui_win_ticks
        move.b  ui_winner,d0
        addq.b  #6,d0
        move.b  d0,ui_overlay_kind
        bra.s   .done
.win:   tst.w   ui_win_ticks
        beq.s   .serve
        subq.w  #1,ui_win_ticks
        move.b  ui_winner,ui_overlay_kind
        bra.s   .done
.serve:
        cmpi.w  #GAME_PLAYING,game_lifecycle
        bne.s   .done
        cmpi.b  #S_ACTIVE,game_score_state+S_STAGE
        bne.s   .done
        tst.b   game_flight
        bne.s   .done
        btst    #6,game_lower_phase
        beq.s   .upper
        btst    #1,game_score_flags
        bne.s   .done
        bra.s   .human
.upper: btst    #6,game_upper_phase
        beq.s   .done
        btst    #0,game_score_flags
        bne.s   .done
.human: move.b  #4,ui_overlay_kind
.done:  rts
.reset: move.b  game_games_a,ui_last_games
        move.b  game_games_b,ui_last_games+1
        clr.w   ui_win_ticks
        rts

