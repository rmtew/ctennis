; Deterministic recorded physical packets, consumed by the normal input dispatcher.
ui_playback:
        tst.b   ui_demo
        beq.s   .done
        tst.w   ui_demo_remaining
        bne.s   .packet
        move.l  ui_demo_cursor,a0
        move.w  (a0)+,d0
        bne.s   .load
        lea     ui_demo_packets,a0
        move.w  (a0)+,d0
.load:  move.w  d0,ui_demo_remaining
        move.w  (a0)+,d0
        move.b  d0,ui_demo_mask
        move.l  a0,ui_demo_cursor
.packet:
        subq.w  #1,ui_demo_remaining
        move.b  ui_demo_mask,game_player_controls
        ; P2 exclusion and native AI continue through the existing one-player path.
.done:  rts
        include "build/amiga/title/enhanced/demo-inputs.i"

