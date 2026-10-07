; Physical/UI boundary. Core code never reads these sources itself.
game_begin_title:
        bra     ui_begin_title

; UI selection becomes an explicit mode command consumed by this callback.
game_latch_choice:
        tst.b   ui_demo
        bne.s   .mode_ready
        move.b  d0,ui_player_count
.mode_ready:
        clr.b   game_title_display
        move.w  #$ace1,d1
        ifnd DEMO_RECORDING
        tst.b   ui_demo
        bne.s   .seed_ready
        ; Sample hardware entropy once at match selection, never during play.
        move.w  last_timer_count+2,d1
        bne.s   .seed_nonzero
        move.w  #$ace1,d1
.seed_nonzero:
.seed_ready:
        endif
        bra     game_core_select

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
        move.w  d0,-(sp)
        move.b  game_input_pressed,d0
        or.b    game_input_pressed+1,d0
        andi.b  #$30,d0
        move.b  ui_edges,d1
        andi.b  #UI_ACTION,d1
        or.b    d1,d0
        move.w  d0,-(sp)
        moveq   #0,d3
        tst.b   ui_paused
        bne.s   .done
        tst.b   ui_demo
        beq.s   .done
        cmpi.w  #GAME_PLAYING,game_lifecycle
        bne.s   .done
        moveq   #-1,d3
        move.w  d3,-(sp)
        bsr     ui_playback
        move.w  (sp)+,d3
.done:
        move.w  (sp)+,d1
        move.w  (sp)+,d0
        moveq   #0,d2
        move.b  ui_demo,d2
        moveq   #0,d4
        move.b  ui_demo_mask,d4
        moveq   #0,d5
        move.b  game_native_selection_keys,d5
        bra     game_core_sample_result

; Called only after the core completed its semantic title transition.
game_core_title_requested:
        core_trace_sink $104
        clr.b   ui_edges
        clr.b   ui_demo
        bsr     ui_begin_title
        ; Core cleanup and the four-plane menu copy must not share a callback.
        ; UI state changes now; retain the complete old presentation until the
        ; next callback can construct and publish the complete title bitmap.
        move.w  simulation_started_updates,ui_title_request_epoch
        st      ui_title_deferred
        bra     game_show_returned_title

ui_title_request_epoch: dc.w 0
ui_title_deferred: dc.b 0
        even
