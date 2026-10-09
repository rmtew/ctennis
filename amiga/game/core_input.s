; Logical inputs only. Physical aliases/filtering remain in the native adapter.
; D0.b player A held, D1.b player B held. Preserve B across the first sampler.
game_core_sample_pads_body:
        move.w  d1,-(sp)
        lea     game_input_bits-game_core_state(a5),a0
        bsr     game_store_pad
        move.w  (sp)+,d0
        lea     game_input_bits+1-game_core_state(a5),a0
        bra     game_store_pad

; D0/D1 continue held/pressed; D2 automatic continuation; D3/D4 playback
; active/mask; D5 selection held. Boolean inputs use zero/nonzero semantics.
game_core_sample_result_body:
        ; A paused demo keeps automatic continuation true. Its falling edge
        ; ends historical playback even in selection/round tails. Title exit
        ; clears the old value before this sampler. Preserve both streams.
        tst.b   game_entropy_policy-game_core_state(a5)
        beq.s   .store
        tst.b   game_auto_continue-game_core_state(a5)
        beq.s   .store
        tst.b   d2
        bne.s   .store
        clr.b   game_entropy_policy-game_core_state(a5)
.store:
        move.b  d0,game_continue_held-game_core_state(a5)
        move.b  d1,game_continue_pressed-game_core_state(a5)
        move.b  d2,game_auto_continue-game_core_state(a5)
        move.b  d3,game_playback_active-game_core_state(a5)
        move.b  d4,game_playback_mask-game_core_state(a5)
        move.b  d5,game_selection_keys-game_core_state(a5)
        rts

; D0.b mode (0 one-player, 1 two-player), D1.w seed, D2.w entropy policy (0/1).
game_core_select_body:
        cmpi.w  #GAME_ENTROPY_LEGACY_SHIFT,d2
        bhi.s   .invalid_policy
        tst.w   d1
        bne.s   .seed_ready
        move.w  #$ace1,d1
.seed_ready:
        move.w  d1,game_match_seed-game_core_state(a5)
        move.b  d2,game_entropy_policy-game_core_state(a5)
        addq.b  #1,d0
        move.b  d0,game_core_command-game_core_state(a5)
.invalid_policy:
        rts

; Takeover consumes carried logical controls while preserving action latches.
game_core_clear_inputs_body:
        bsr     game_latch_old_actions
        clr.w   game_input_bits-game_core_state(a5)
        clr.w   game_input_pressed-game_core_state(a5)
        clr.w   game_input_released-game_core_state(a5)
        rts

; Resume retires held actions without clearing the sampled logical packet.
game_core_latch_actions_body:
        bra     game_latch_old_actions
