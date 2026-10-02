ui_resume:
        clr.b   ui_paused
        clr.b   ui_confirmation
        bsr     game_latch_old_actions
        move.w  ui_saved_volumes,$dff0a8
        move.w  ui_saved_volumes+2,$dff0b8
        move.w  ui_saved_volumes+4,$dff0d8
        bra     ui_input_draw

ui_return_title:
        clr.b   ui_edges
        clr.b   ui_demo
        bsr     game_audio_reset
        cmpi.w  #GAME_RESULT_SOUND,game_lifecycle
        bne.s   .ordinary_return
        moveq   #0,d0
        bsr     game_new_match
.ordinary_return:
        bsr     game_celebration_reset
        bsr     game_begin_title
        bsr     game_show_returned_title
        move.b  ui_player_count,game_selected_mode
        ; ui_render publishes only after all title planes/selection are copied.
        rts
