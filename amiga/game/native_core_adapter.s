; Physical/UI boundary. Core code never reads these sources itself.
game_begin_title:
        bsr     game_core_begin_title
        bra     ui_begin_title

; UI selection becomes an explicit mode command consumed by this callback.
game_latch_choice:
        tst.b   ui_demo
        bne.s   .mode_ready
        move.b  d0,ui_player_count
.mode_ready:
        clr.b   game_title_display
        addq.b  #1,d0
        move.b  d0,game_core_command
        move.w  #$ace1,game_match_seed
        ifnd DEMO_RECORDING
        tst.b   ui_demo
        bne.s   .seed_ready
        ; Sample hardware entropy once at match selection, never during play.
        move.w  last_timer_count+2,d0
        bne.s   .seed_nonzero
        move.w  #$ace1,d0
.seed_nonzero:
        move.w  d0,game_match_seed
.seed_ready:
        endif
        rts

game_native_menu_tick:
        cmpi.w  #GAME_TITLE,game_lifecycle
        bne.s   .done
        bsr     ui_menu_tick
.done:  rts

; Logical result action includes unfiltered physical fire and Enter, matching
; the old continuation gate without exposing device identities to the core.
game_native_commands:
        move.b  game_input_bits,d0
        or.b    game_input_bits+1,d0
        or.b    ui_joystick_bits,d0
        or.b    ui_joystick_bits+1,d0
        andi.b  #$30,d0
        or.b    game_keyboard_matrix+$44,d0
        move.b  d0,game_continue_held
        move.b  game_input_pressed,d0
        or.b    game_input_pressed+1,d0
        andi.b  #$30,d0
        move.b  ui_edges,d1
        andi.b  #UI_ACTION,d1
        or.b    d1,d0
        move.b  d0,game_continue_pressed
        move.b  ui_demo,game_auto_continue
        clr.b   game_playback_active
        tst.b   ui_paused
        bne.s   .done
        tst.b   ui_demo
        beq.s   .done
        cmpi.w  #GAME_PLAYING,game_lifecycle
        bne.s   .done
        st      game_playback_active
        bsr     ui_playback
.done:  rts

; Called only after the core completed its semantic title transition.
game_core_title_requested:
        clr.b   ui_edges
        clr.b   ui_demo
        bsr     ui_begin_title
        bra     game_show_returned_title
