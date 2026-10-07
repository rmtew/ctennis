UI_DEMO_SEED equ $ace1 ; native-rules-v1 / galois16-b400-v1, checked against recording metadata

; Deterministic recorded physical packets, consumed by the normal input dispatcher.
ui_playback:
        tst.b   ui_demo
        beq.s   .done
        tst.w   ui_demo_remaining
        bne.s   .packet
        move.l  ui_demo_cursor,a0
        move.w  (a0)+,d0
        bne.s   .load
        ; End of a complete match recording: neutral input, never loop it.
        clr.b   ui_demo_mask
        clr.b   game_playback_mask
        rts
.load:  move.w  d0,ui_demo_remaining
        move.w  (a0)+,d0
        move.b  d0,ui_demo_mask
        move.l  a0,ui_demo_cursor
.packet:
        subq.w  #1,ui_demo_remaining
        move.b  ui_demo_mask,game_playback_mask
        ; B exclusion and native AI continue through the existing one-player path.
.done:  rts
        include "build/native/demo-inputs.i"


