ui_resume:
        clr.b   ui_paused
        clr.b   ui_confirmation
        bsr     game_core_latch_actions
        move.w  ui_saved_volumes,$dff0a8
        move.w  ui_saved_volumes+2,$dff0b8
        move.w  ui_saved_volumes+4,$dff0d8
        bra     ui_input_draw

ui_return_title:
        bra     game_core_return_title
