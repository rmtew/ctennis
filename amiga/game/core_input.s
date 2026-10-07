; Logical inputs only. Physical aliases/filtering remain in the native adapter.
; D0.b player A held, D1.b player B held. Preserve B across the first sampler.
        ifd CORE_TRACE
game_core_sample_pads_body:
        else
game_core_sample_pads:
        endif
        move.w  d1,-(sp)
        lea     game_input_bits,a0
        bsr     game_store_pad
        move.w  (sp)+,d0
        lea     game_input_bits+1,a0
        bra     game_store_pad

; D0/D1 continue held/pressed; D2 automatic continuation; D3/D4 playback
; active/mask; D5 selection held. Boolean inputs use zero/nonzero semantics.
        ifd CORE_TRACE
game_core_sample_result_body:
        else
game_core_sample_result:
        endif
        move.b  d0,game_continue_held
        move.b  d1,game_continue_pressed
        move.b  d2,game_auto_continue
        move.b  d3,game_playback_active
        move.b  d4,game_playback_mask
        move.b  d5,game_selection_keys
        rts

; D0.b mode (0 one-player, 1 two-player), D1.w match seed.
        ifd CORE_TRACE
game_core_select_body:
        else
game_core_select:
        endif
        tst.w   d1
        bne.s   .seed_ready
        move.w  #$ace1,d1
.seed_ready:
        move.w  d1,game_match_seed
        addq.b  #1,d0
        move.b  d0,game_core_command
        rts

; Takeover consumes carried logical controls while preserving action latches.
        ifd CORE_TRACE
game_core_clear_inputs_body:
        else
game_core_clear_inputs:
        endif
        bsr     game_latch_old_actions
        clr.w   game_input_bits
        clr.w   game_input_pressed
        clr.w   game_input_released
        rts

; Resume retires held actions without clearing the sampled logical packet.
        ifd CORE_TRACE
game_core_latch_actions_body:
        else
game_core_latch_actions:
        endif
        bra     game_latch_old_actions
