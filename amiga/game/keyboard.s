; Poll the real CIA-A serial keyboard. CIA interrupts are disabled by the game.
; Keep SDR acknowledgement asserted for >=85 us without delaying the main loop.
game_poll_keyboard:
        tst.b   keyboard_ack
        beq.s   keyboard_receive
        move.w  last_timer_count+2,d0
        sub.w   keyboard_ack_timer,d0
        neg.w   d0
        cmpi.w  #70,d0
        bcs.s   keyboard_return
        bclr    #6,$bfee01
        clr.b   keyboard_ack
keyboard_receive:
        btst    #3,$bfed01
        beq.s   keyboard_return
        move.b  $bfec01,d0
        not.b   d0
        ror.b   #1,d0
        moveq   #0,d1
        move.b  d0,d1
        andi.b  #$7f,d1
        bsr     keyboard_enhanced_store
        bra     keyboard_handshake
keyboard_handshake:
        bset    #6,$bfee01
        move.w  last_timer_count+2,keyboard_ack_timer
        move.b  #1,keyboard_ack
keyboard_return:
        rts
keyboard_ack: dc.b 0
        even
keyboard_ack_timer: dc.w 0

; Raw Amiga positions (US legends), not host key symbols. One byte per key
; preserves independent aliases and simultaneous release transitions.
keyboard_enhanced_store:
        lea     game_keyboard_matrix,a0
        btst    #7,d0
        bne.s   .up
        move.b  #1,0(a0,d1.w)
        bra.s   .selection
.up:    clr.b   0(a0,d1.w)
        lea     ui_keyboard_entry_keys,a1
        clr.b   0(a1,d1.w)
.selection:
        move.b  $01(a0),d0      ; main 1
        or.b    $46(a0),d0      ; Delete
        move.b  $02(a0),d1      ; main 2
        or.b    $42(a0),d1      ; Tab
        add.b   d1,d1
        or.b    d1,d0
        move.b  d0,game_selection_keys
        rts

; D0 pad bits, D3 logical player index. Combine before game_store_pad.
game_merge_keyboard:
        move.l  a3,-(sp)
        lea     ui_keyboard_entry_keys,a3
        lea     game_keyboard_mapping,a1
        lea     game_keyboard_matrix,a2
.loop:  moveq   #0,d1
        move.b  (a1)+,d1
        bmi.s   .done
        move.b  (a1)+,d2
        cmp.b   d3,d2
        beq.s   .player
        addq.l  #1,a1
        bra.s   .loop
.player:
        move.b  (a1)+,d2
        tst.b   0(a2,d1.w)
        beq.s   .loop
        tst.b   0(a3,d1.w)
        bne.s   .loop
        or.b    d2,d0
        bra.s   .loop
.done:  move.l  (sp)+,a3
        rts
; key, player, held mask: right/up/left/down/red/blue =1/2/4/8/16/32.
game_keyboard_mapping:
        dc.b $11,0,2,$20,0,4,$21,0,8,$22,0,1,$23,0,16,$24,0,32
        dc.b $4c,1,2,$4f,1,4,$4d,1,8,$4e,1,1,$39,1,16,$3a,1,32
        dc.b $3e,1,2,$2d,1,4,$1e,1,8,$2f,1,1,$0f,1,16,$3c,1,32
        dc.b $ff
        even
game_enhanced_interface:
game_keyboard_matrix: dcb.b 128,0
