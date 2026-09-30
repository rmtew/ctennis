; Poll the real CIA-A serial keyboard. CIA interrupts are disabled by the game.
; Keep SDR acknowledgement asserted for >=85 us without delaying the main loop.
game_poll_keyboard:
        tst.b   keyboard_ack
        beq.s   keyboard_receive
        move.w  last_timer_count,d0
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
        move.b  d0,d1
        andi.b  #$7f,d1
        cmpi.b  #$46,d1
        beq.s   keyboard_one
        cmpi.b  #$42,d1
        bne.s   keyboard_handshake
        moveq   #2,d1
        bra.s   keyboard_store
keyboard_one:
        moveq   #1,d1
keyboard_store:
        btst    #7,d0
        beq.s   keyboard_down
        not.b   d1
        and.b   d1,game_selection_keys
        bra.s   keyboard_handshake
keyboard_down:
        or.b    d1,game_selection_keys
keyboard_handshake:
        bset    #6,$bfee01
        move.w  last_timer_count,keyboard_ack_timer
        move.b  #1,keyboard_ack
keyboard_return:
        rts
keyboard_ack: dc.b 0
        even
keyboard_ack_timer: dc.w 0
