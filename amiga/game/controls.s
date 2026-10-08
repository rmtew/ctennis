; Physical pads belong to players, never to screen positions.
; A = connector 2, B = connector 1; two-button sticks (red/blue).
; Held bits: right/up/left/down/action1/action2 = 1/2/4/8/16/32.
game_init_controls:
        andi.b  #$3f,$bfe201     ; CIA fire pins are inputs
        move.w  #$ff00,$dff034   ; charge button lines high; switches pull low
        rts

sample_amiga_joystick:
        move.w  $dff00c,d0
        bsr.s   game_decode_directions
        btst    #7,$bfe001
        bne.s   game_p1_blue
        ori.b   #16,d0
game_p1_blue:
        move.w  $dff016,d1
        btst    #14,d1
        bne.s   game_p1_store
        ori.b   #32,d0
game_p1_store:
        moveq   #0,d3
        bsr     ui_filter_joystick
        bsr     game_merge_keyboard
        move.b  d0,game_native_pad_bits
        move.w  $dff00a,d0
        bsr.s   game_decode_directions
        btst    #6,$bfe001
        bne.s   game_p2_blue
        ori.b   #16,d0
game_p2_blue:
        move.w  $dff016,d1
        btst    #10,d1
        bne.s   game_p2_store
        ori.b   #32,d0
game_p2_store:
        moveq   #1,d3
        bsr     ui_filter_joystick
        bsr     game_merge_keyboard
        move.b  d0,game_native_pad_bits+1
        move.b  d0,d1
        move.b  game_native_pad_bits,d0
        bsr     game_core_sample_pads
input_ready:
        rts

game_native_pad_bits: dc.b 0,0
        even

game_decode_directions:
        move.w  d0,d1
        moveq   #0,d0
        btst    #9,d1
        beq.s   game_decode_right
        ori.b   #4,d0
game_decode_right:
        btst    #1,d1
        beq.s   game_decode_vertical
        ori.b   #1,d0
game_decode_vertical:
        move.w  d1,d2
        lsr.w   #1,d2
        eor.w   d2,d1           ; up = bit8 XOR bit9; down = bit0 XOR bit1
        btst    #8,d1
        beq.s   game_decode_down
        ori.b   #2,d0
game_decode_down:
        btst    #0,d1
        beq.s   game_decode_done
        ori.b   #8,d0
game_decode_done:
        rts
