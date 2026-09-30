; Maintained title/selection lifecycle. No source callback PC or RAM snapshot.
; Selection is latched once, then waits for physical release before live play.
game_begin_title:
        move.w  #GAME_TITLE,game_lifecycle
        clr.b   game_selection_keys
        clr.b   game_selected_mode
        clr.w   game_accept_count
        rts

game_menu_tick:
        cmpi.w  #GAME_TITLE,game_lifecycle
        bne.s   game_wait_release
        tst.b   game_selection_keys
        beq.s   game_menu_return
        moveq   #0,d0
        btst    #1,game_selection_keys
        beq.s   game_latch_choice
        moveq   #1,d0
game_latch_choice:
        move.b  d0,game_selected_mode
        bsr     legacy_new_match
        addq.w  #1,game_accept_count
        move.w  #GAME_SELECTION_HELD,game_lifecycle
        move.w  #64,game_selection_delay
        rts
game_wait_release:
        tst.w   game_selection_delay
        beq.s   game_check_release
        subq.w  #1,game_selection_delay
        rts
game_check_release:
        tst.b   game_selection_keys
        bne.s   game_menu_return
        move.w  #GAME_PLAYING,game_lifecycle
game_menu_return:
        rts
        even
game_selection_delay: dc.w 0
game_accept_count: dc.w 0
game_selection_keys: dc.b 0
game_selected_mode: dc.b 0
