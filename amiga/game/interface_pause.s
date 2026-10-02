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
        bsr     game_begin_title
        bsr     game_show_returned_title
        move.b  ui_player_count,game_selected_mode
        move.b  #1,display_ready
        rts

