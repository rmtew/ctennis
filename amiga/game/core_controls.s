; Logical controls only. Physical sampling lives in controls.s.
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
        move.b  d1,game_lower_owner-game_core_state(a5)
        eori.b  #1,d1
        move.b  d1,game_upper_owner-game_core_state(a5)
        move.b  game_input_bits-game_core_state(a5),game_player_controls-game_core_state(a5)
        clr.b   game_player_controls+1-game_core_state(a5)
        tst.b   d0
        beq.s   game_filter_old_actions
        move.b  game_input_bits+1-game_core_state(a5),game_player_controls+1-game_core_state(a5)
; A new match must not treat an action carried across its menu as a new serve.
; Suppress only those action bits held at selection, independently per player;
; each becomes eligible after its physical release. Normal rally holds survive.
game_filter_old_actions:
        lea     game_input_bits-game_core_state(a5),a0
        lea     game_old_action_latches-game_core_state(a5),a1
        lea     game_player_controls-game_core_state(a5),a2
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
        move.b  game_player_controls-game_core_state(a5),d0
        rts
sample_second_input_group:
        move.b  game_player_controls+1-game_core_state(a5),d0
        rts

        even

game_latch_old_actions:
        move.b  game_input_bits-game_core_state(a5),d0
        andi.b  #$30,d0
        move.b  d0,game_old_action_latches-game_core_state(a5)
        move.b  game_input_bits+1-game_core_state(a5),d0
        andi.b  #$30,d0
        move.b  d0,game_old_action_latches+1-game_core_state(a5)
        rts
        even
