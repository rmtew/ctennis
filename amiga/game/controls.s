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
        lea     game_input_bits,a0
        bsr.s   game_store_pad
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
        lea     game_input_bits+1,a0
        bsr.s   game_store_pad
input_ready:
        rts

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

game_store_pad:
        move.b  (a0),d1
        move.b  d0,(a0)
; Retire inherited actions on every physical sample, including menu/sound
; waits. Do not assign player controls or consume gameplay while waiting.
        and.b   d0,game_old_action_latches-game_input_bits(a0)
        eor.b   d0,d1
        move.b  d1,d2
        and.b   d0,d1
        move.b  d1,2(a0)        ; newly pressed
        not.b   d0
        and.b   d2,d0
        move.b  d0,4(a0)        ; newly released
        rts

; D0: two-player boolean, D1: exchanged-ends boolean. Called each active
; update by the temporary state adapter until native rounds own these values.
game_assign_players:
        andi.b  #1,d1
        move.b  d1,game_lower_owner
        eori.b  #1,d1
        move.b  d1,game_upper_owner
        move.b  game_input_bits,game_player_controls
        clr.b   game_player_controls+1
        tst.b   d0
        beq.s   game_filter_old_actions
        move.b  game_input_bits+1,game_player_controls+1
; A new match must not treat an action carried across its menu as a new serve.
; Suppress only those action bits held at selection, independently per player;
; each becomes eligible after its physical release. Normal rally holds survive.
game_filter_old_actions:
        lea     game_input_bits,a0
        lea     game_old_action_latches,a1
        lea     game_player_controls,a2
        moveq   #1,d2
game_filter_old_action:
        move.b  (a0)+,d0
        and.b   (a1),d0
        move.b  d0,(a1)+
        not.b   d0
        and.b   d0,(a2)+
        dbra    d2,game_filter_old_action
game_assignment_done:
        rts

; Compatibility reader names also provide observation boundaries.
read_game_input:
        move.b  game_player_controls,d0
        rts
sample_second_input_group:
        move.b  game_player_controls+1,d0
        rts

game_input_bits:       dc.b 0,0
game_input_pressed:    dc.b 0,0
game_input_released:   dc.b 0,0
game_player_controls: dc.b 0,0
game_lower_owner:     dc.b 0
game_upper_owner:     dc.b 1
        even

game_latch_old_actions:
        move.b  game_input_bits,d0
        andi.b  #$30,d0
        move.b  d0,game_old_action_latches
        move.b  game_input_bits+1,d0
        andi.b  #$30,d0
        move.b  d0,game_old_action_latches+1
        rts
game_old_action_latches: dc.b 0,0
        even
