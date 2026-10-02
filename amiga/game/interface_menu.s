ui_begin_title:
        move.w  #$ffff,ui_overlay_signature
        st      game_title_display
        clr.b   ui_page
        clr.b   ui_selection
        clr.b   ui_paused
        clr.b   ui_confirmation
        clr.w   ui_idle
        st      ui_dirty
        rts

ui_menu_tick:
        tst.b   game_selection_keys
        beq.s   .navigate
        moveq   #0,d0
        btst    #1,game_selection_keys
        beq     game_latch_choice
        moveq   #1,d0
        bra     game_latch_choice
.navigate:
        tst.b   ui_edges
        beq     .idle
        clr.w   ui_idle
        st      ui_dirty
        tst.b   ui_page
        bne     .pages
        btst    #0,ui_edges
        beq.s   .down
        subq.b  #1,ui_selection
        andi.b  #3,ui_selection
.down:  btst    #1,ui_edges
        beq.s   .toggle
        addq.b  #1,ui_selection
        andi.b  #3,ui_selection
.toggle:
        cmpi.b  #1,ui_selection
        bne.s   .action
        move.b  ui_edges,d0
        andi.b  #UI_LEFT+UI_RIGHT,d0
        beq.s   .action
        eori.b  #1,ui_player_count
.action:
        btst    #4,ui_edges
        beq     .done
        moveq   #0,d0
        move.b  ui_selection,d0
        beq.s   .start
        cmpi.b  #1,d0
        bne.s   .open
        eori.b  #1,ui_player_count
        bra     .done
.open:  subq.b  #1,d0
        cmpi.b  #2,d0
        bne.s   .open_page
        moveq   #3,d0
.open_page:
        move.b  d0,ui_page
        move.b  #2,ui_help_choice
        bra     .done
.start: move.b  ui_player_count,d0
        bra     game_latch_choice
.pages:
        btst    #5,ui_edges
        bne.s   .page_exit
        btst    #2,ui_edges
        beq.s   .page_right
        tst.b   ui_help_choice
        beq.s   .page_right
        subq.b  #1,ui_help_choice
.page_right:
        btst    #3,ui_edges
        beq.s   .page_action
        cmpi.b  #2,ui_help_choice
        beq.s   .page_action
        addq.b  #1,ui_help_choice
.page_action:
        btst    #4,ui_edges
        beq     .done
        cmpi.b  #1,ui_help_choice
        beq.s   .page_exit
        tst.b   ui_help_choice
        bne.s   .page_next
        subq.b  #1,ui_page
        bne     .done
        move.b  #4,ui_page
        bra     .done
.page_next:
        addq.b  #1,ui_page
        cmpi.b  #5,ui_page
        bcs     .done
        move.b  #1,ui_page
        bra     .done
.page_exit:
        clr.b   ui_page
        bra     .done
.idle:  tst.b   ui_page
        bne.s   .done
        addq.w  #1,ui_idle
        cmpi.w  #UI_IDLE_TICKS,ui_idle
        bcs.s   .done
        ; Snapshot sources separately; raw input continues to be sampled normally.
        lea     game_keyboard_matrix,a0
        lea     ui_keyboard_entry_keys,a1
        moveq   #127,d7
.entry_keys:
        move.b  (a0)+,(a1)+
        dbra    d7,.entry_keys
        move.b  ui_joystick_bits,ui_joystick_entry
        move.b  ui_joystick_bits+1,ui_joystick_entry+1
        st      ui_demo
        clr.b   ui_demo_choice
        clr.w   ui_demo_remaining
        lea     ui_demo_packets,a0
        move.l  a0,ui_demo_cursor
        moveq   #0,d0
        bra     game_latch_choice
.done:  bsr     ui_render
        rts
