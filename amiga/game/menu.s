; Maintained title/selection lifecycle. No source callback PC or RAM snapshot.
; Selection is latched once, then waits for physical release before live play.
game_begin_title:
        move.w  #GAME_TITLE,game_lifecycle
        clr.b   game_selection_keys
        clr.b   game_restart_context
        ifnd ENHANCED_INTERFACE
        clr.b   game_selected_mode
        endif
        ifd ENHANCED_INTERFACE
        bsr     ui_begin_title
        endif
        clr.w   game_accept_count
        rts

game_menu_tick:
        ifd ENHANCED_INTERFACE
        cmpi.w  #GAME_TITLE,game_lifecycle
        beq     ui_menu_tick
        endif
        cmpi.w  #GAME_TITLE,game_lifecycle
        ifd ENHANCED_INTERFACE
        bne     game_wait_release
        else
        bne.s   game_wait_release
        endif
        tst.b   game_selection_keys
        beq     game_menu_return
        moveq   #0,d0
        btst    #1,game_selection_keys
        beq.s   game_latch_choice
        moveq   #1,d0
game_latch_choice:
        ifd ENHANCED_INTERFACE
        tst.b   ui_demo
        bne.s   ui_keep_player_count
        move.b  d0,ui_player_count
ui_keep_player_count:
        move.w  d0,-(sp)
        bsr     game_latch_old_actions
        move.w  (sp)+,d0
        clr.b   game_title_display
        endif
        move.b  d0,game_selected_mode
        bsr     game_new_match
        tst.b   game_restart_context
        bne.s   game_restart_choice
        ; First preparation must already carry the physical mode selection.
        ; Do not consume the pending gameplay display event before its tick.
        move.b  game_selected_mode,d0
        addq.b  #1,d0
        move.b  d0,field_values+5
        bra.s   game_choice_ready
game_restart_choice:
        ifd NATIVE_CONTROLS
        bsr     game_latch_old_actions
        endif
        clr.b   game_lower_phase
        clr.b   game_upper_phase
        clr.b   game_score_flags
        clr.b   game_display
        clr.b   game_serve_clock
game_choice_ready:
        addq.w  #1,game_accept_count
        move.w  #GAME_SELECTION_HELD,game_lifecycle
        move.w  #64,game_selection_delay
        rts
game_wait_release:
        tst.b   game_restart_context
        beq.s   game_first_release
        cmpi.b  #$40,game_serve_clock
        bcs.s   game_menu_return
        bra.s   game_check_release
game_first_release:
        tst.w   game_selection_delay
        beq.s   game_check_release
        subq.w  #1,game_selection_delay
        rts
game_check_release:
        tst.b   game_selection_keys
        bne.s   game_menu_return
        tst.b   game_restart_context
        beq.s   game_first_play
        bsr     game_restart_begin
        rts
game_first_play:
        move.w  #GAME_PLAYING,game_lifecycle
game_menu_return:
        rts
        even
game_selection_delay: dc.w 0
game_accept_count: dc.w 0
game_selection_keys: dc.b 0
game_selected_mode: dc.b 0

game_restart_context: dc.b 0
        even
