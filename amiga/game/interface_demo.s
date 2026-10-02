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
        clr.b   game_player_controls
        rts
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


; Version1 native entropy source: 16-bit maximal-period Galois LFSR.
; Same adapter consumers as live CIA entropy. Only demo/recording uses it.
ui_seed_entropy:
        move.w  #UI_DEMO_SEED,ui_entropy_state
        rts
ui_demo_entropy:
        move.w  ui_entropy_state,d1
        lsr.w   #1,d1
        moveq   #0,d0
        bcc.s   .store
        eori.w  #$b400,d1
        moveq   #1,d0
.store: move.w  d1,ui_entropy_state
        rts
