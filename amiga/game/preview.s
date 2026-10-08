; Isolated fixed-buffer previews over the actual logical APIs. Caller freezes
; the physical dispatcher. Every worker yield restores selected state/metadata.
PREVIEW_POINTS equ 256
PREVIEW_POINT_BYTES equ 8
PREVIEW_RESOLVE equ 1
PREVIEW_PRIME equ 2
PREVIEW_HELD equ 3
PREVIEW_RELEASED equ 4
PREVIEW_READY equ 5
PREVIEW_CONTEXT_MISSING equ 6
PREVIEW_CANCELED equ 7
PREVIEW_LANDING equ 1
PREVIEW_NET equ 2
PREVIEW_OUT equ 3
PREVIEW_INTERCEPTION equ 4
PREVIEW_NO_CONTACT equ 5
PREVIEW_LIMIT equ 6
PREVIEW_LIFECYCLE equ 7

; D0 expected generation, D1 retained index ordinal ($ffff current serve),
; D2/D3 requested byte X/Y. Current history_position is the selected boundary.
; Invalid/stale requests make no changes. D0=1 accepted, D0=0 rejected.
game_preview_request:
        cmp.l   game_preview_generation,d0
        bne     .invalid
        cmpi.l  #$fffffffe,d0
        bcc     .invalid
        cmpi.b  #2,game_history_mode
        bne     .invalid
        tst.b   game_preview_active
        bne     .invalid
        cmpi.w  #255,d2
        bhi     .invalid
        cmpi.w  #255,d3
        bhi     .invalid
        btst    #7,game_mode
        bne     .invalid
        movem.l d2-d7/a2-a6,-(sp)
        move.w  d2,d4
        move.w  d3,d5
        move.w  d1,d2
        cmpi.w  #$ffff,d1
        beq.s   .fallback
        cmp.w   game_history_attempt_count,d1
        bcc     .invalid_saved
        add.w   game_history_attempt_first,d1
        andi.w  #HISTORY_ATTEMPTS-1,d1
        move.w  d1,d0
        bsr     game_history_attempt_address
        move.w  8(a0),d6
        beq     .invalid_saved
        cmpi.w  #3,d6
        bhi     .invalid_saved
        move.w  10(a0),d7
        cmpi.w  #1,d7
        bhi     .invalid_saved
        lea     game_play_state+G_LOWER_AI,a1
        tst.b   (a1,d7.w)
        bne     .invalid_saved
        move.l  a0,a5
        bra.s   .bounds
.fallback:
        moveq   #0,d7
        btst    #1,game_score_flags
        beq.s   .fallback_end
        moveq   #1,d7
.fallback_end:
        lea     game_play_state+G_LOWER_AI,a1
        tst.b   (a1,d7.w)
        bne     .invalid_saved
        bsr     game_preview_player_address
        move.b  P_PHASE(a3),d0
        andi.b  #$e0,d0
        beq     .invalid_saved
        moveq   #3,d6
        suba.l  a5,a5
.bounds:
        bsr     game_preview_player_address
        ; Read the same immutable phase-selected limits as game_move_player.
        lea     game_lower_limits,a0
        tst.w   d7
        beq.s   .phase
        lea     game_upper_limits,a0
.phase:
        moveq   #0,d0
        move.b  P_ANIMATION(a3),d0
        lsr.w   #3,d0
        andi.w  #12,d0
        adda.w  d0,a0
        cmp.b   2(a0),d4
        bcc     .invalid_saved
        cmp.b   3(a0),d4
        bcs     .invalid_saved
        cmp.b   (a0),d5
        bcc     .invalid_saved
        cmp.b   1(a0),d5
        bcs     .invalid_saved
        ; Reuse only a fully published, unchanged selection and attempt.
        cmpi.w  #PREVIEW_READY,game_preview_status
        bne.s   .cold
        tst.w   game_preview_cache_valid
        beq.s   .cold
        cmp.w   game_preview_ordinal,d2
        bne.s   .cold
        cmp.w   game_preview_kind,d6
        bne.s   .cold
        cmp.w   game_preview_end,d7
        bne.s   .cold
        bsr     game_preview_selection_unchanged
        tst.l   d0
        beq.s   .cold
        move.l  a5,d0
        beq.s   .reuse
        lea     game_preview_origin,a0
        move.l  a5,a1
        bsr     game_preview_compare_cursor
        tst.l   d0
        bne.s   .cold
.reuse: addq.l  #1,game_preview_generation
        move.w  d4,game_preview_x
        move.w  d5,game_preview_y
        bsr     game_preview_prepare
        bra     .restore
.cold:
        ; Only after all guards: replace the prior generation and its counts.
        lea     game_preview_state+4,a0
        move.w  #(game_preview_state_end-game_preview_state-4)/2-1,d0
.clear: clr.w   (a0)+
        dbra    d0,.clear
        addq.l  #1,game_preview_generation
        move.w  d7,game_preview_end
        move.w  d6,game_preview_kind
        move.w  d2,game_preview_ordinal
        move.w  d4,game_preview_x
        move.w  d5,game_preview_y
        move.l  game_history_position,game_preview_selected
        move.l  game_history_position+4,game_preview_selected+4
        lea     game_preview_selected_state,a0
        lea     game_core_state,a1
        bsr     game_history_copy_state
        lea     game_preview_history_saved,a0
        lea     game_history_state,a1
        bsr     game_preview_copy_history
        move.l  a5,d0
        beq.s   .serve_now
        move.l  (a5),game_preview_origin
        move.l  4(a5),game_preview_origin+4
        move.w  #PREVIEW_RESOLVE,game_preview_status
        ; Oldest CP restoration performs zero logical replay operations.
        move.l  game_history_oldest,d0
        move.l  game_history_oldest+4,d1
        move.b  #3,game_preview_active
        bsr     game_history_seek
        clr.b   game_preview_active
        tst.l   d0
        beq.s   .missing
        move.l  game_history_oldest,game_preview_cursor
        move.l  game_history_oldest+4,game_preview_cursor+4
        lea     game_preview_held_state,a0
        lea     game_core_state,a1
        bsr     game_history_copy_state
        bra.s   .restore
.serve_now:
        ; No historical outgoing shot is claimed for this explicit fallback.
        move.l  game_preview_selected,game_preview_action
        move.l  game_preview_selected+4,game_preview_action+4
        bsr     game_preview_prepare
        bra.s   .restore
.missing:
        move.w  #PREVIEW_CONTEXT_MISSING,game_preview_status
.restore:
        bsr     game_preview_restore_selected
        movem.l (sp)+,d2-d7/a2-a6
        moveq   #1,d0
        rts
.invalid_saved:
        movem.l (sp)+,d2-d7/a2-a6
.invalid:
        moveq   #0,d0
        rts

; D0 generation, D1 logical-operation budget1..4. No dispatch/tick hidden in
; copying, guards or context selection. D0=1 valid call, D0=0 stale/invalid.
game_preview_step:
        cmp.l   game_preview_generation,d0
        bne     .invalid
        cmpi.w  #1,d1
        bcs     .invalid
        cmpi.w  #4,d1
        bhi     .invalid
        cmpi.b  #2,game_history_mode
        bne     .invalid
        bsr     game_preview_selection_unchanged
        tst.l   d0
        beq     .invalid
        cmpi.w  #PREVIEW_READY,game_preview_status
        bhi     .invalid
        beq     .valid
        tst.w   game_preview_status
        beq     .invalid
        move.w  d1,game_preview_budget
        movem.l d2-d7/a2-a6,-(sp)
.next:
        cmpi.w  #PREVIEW_RESOLVE,game_preview_status
        bne.s   .alternative
        lea     game_preview_held_state,a1
        lea     game_core_state,a0
        bsr     game_history_copy_state
        move.b  #1,game_preview_active
        bsr     game_preview_resolve_one
        cmpi.w  #PREVIEW_RESOLVE,game_preview_status
        bne.s   .spent
        lea     game_preview_held_state,a0
        lea     game_core_state,a1
        bsr     game_history_copy_state
        bra.s   .spent
.alternative:
        moveq   #0,d7
        cmpi.w  #PREVIEW_PRIME,game_preview_status
        bne.s   .running
        move.w  game_preview_primed,d7
        bra.s   .variant_ready
.running:
        cmpi.w  #PREVIEW_RELEASED,game_preview_status
        bne.s   .variant_ready
        moveq   #1,d7
.variant_ready:
        move.b  d7,game_preview_variant
        bsr     game_preview_context_address
        move.l  a0,a1
        lea     game_core_state,a0
        bsr     game_history_copy_state
        move.b  #2,game_preview_active
        cmpi.w  #PREVIEW_PRIME,game_preview_status
        bne.s   .continue
        bsr     game_preview_prime_one
        bra.s   .save_variant
.continue:
        bsr     game_preview_continue_one
.save_variant:
        moveq   #0,d7
        move.b  game_preview_variant,d7
        bsr     game_preview_context_address
        lea     game_core_state,a1
        bsr     game_history_copy_state
.spent:
        clr.b   game_preview_active
        bsr     game_preview_restore_selected
        subq.w  #1,game_preview_budget
        beq.s   .yield
        cmpi.w  #PREVIEW_READY,game_preview_status
        bcs     .next
.yield:
        movem.l (sp)+,d2-d7/a2-a6
.valid:
        moveq   #1,d0
        rts
.invalid:
        moveq   #0,d0
        rts

; Cancel never restores a stale selected state; workers already restore at yield.
game_preview_cancel:
        cmp.l   game_preview_generation,d0
        bne.s   .invalid
        cmpi.l  #$ffffffff,d0
        beq     .invalid
        addq.l  #1,game_preview_generation
        move.w  #PREVIEW_CANCELED,game_preview_status
        clr.w   game_preview_cache_valid
        clr.l   game_preview_counts
        clr.b   game_preview_active
        moveq   #1,d0
        rts
.invalid:
        moveq   #0,d0
        rts

; Publish only a complete current generation (limits remain honest outcomes).
; A0/A1 paths, D1/D2 counts, D3/D4 outcomes, D5 geometry coincidence.
game_preview_result:
        cmp.l   game_preview_generation,d0
        bne.s   .invalid
        cmpi.w  #PREVIEW_READY,game_preview_status
        bne.s   .invalid
        bsr     game_preview_selection_unchanged
        tst.l   d0
        beq.s   .invalid
        lea     game_preview_paths,a0
        lea     game_preview_paths+PREVIEW_POINTS*PREVIEW_POINT_BYTES,a1
        moveq   #0,d1
        moveq   #0,d2
        moveq   #0,d3
        moveq   #0,d4
        moveq   #0,d5
        move.w  game_preview_counts,d1
        move.w  game_preview_counts+2,d2
        move.w  game_preview_outcomes,d3
        move.w  game_preview_outcomes+2,d4
        move.w  game_preview_coincident,d5
        moveq   #1,d0
        rts
.invalid:
        moveq   #0,d0
        rts

game_preview_player_address:
        lea     game_lower_phase,a3
        tst.w   d7
        beq.s   .done
        lea     game_upper_phase,a3
.done:  rts

; Unsigned64 comparison, A0 lhs/A1 rhs -> D0 -1/0/1.
game_preview_compare_cursor:
        move.l  (a0),d0
        cmp.l   (a1),d0
        bcs.s   .less
        bhi.s   .more
        move.l  4(a0),d0
        cmp.l   4(a1),d0
        bcs.s   .less
        bhi.s   .more
        moveq   #0,d0
        rts
.less:  moveq   #-1,d0
        rts
.more:  moveq   #1,d0
        rts

game_preview_resolve_one:
        lea     game_preview_cursor,a0
        lea     game_history_cursor,a1
        bsr     game_preview_compare_cursor
        tst.l   d0
        bpl     game_preview_missing
        move.l  game_preview_cursor+4,game_history_replay_low
        bsr     game_history_record_address
        bsr     game_preview_execute_record
        tst.l   d0
        beq     game_preview_missing
        tst.b   game_preview_action_found
        bne     game_preview_resolved
        tst.b   game_preview_probe_seen
        beq.s   .prefix
        cmpi.w  #GAME_PLAYING,game_lifecycle
        bne.s   .miss
        move.b  game_contact,d0
        andi.b  #$8d,d0
        beq.s   .prefix
.miss:
        move.b  #2,game_preview_action_kind
        bsr     game_preview_found_action
        bra     game_preview_resolved
.prefix:
        cmpi.w  #3,game_preview_kind
        beq.s   .advance
        tst.b   game_preview_incoming_valid
        beq.s   .advance
        cmpi.w  #8,game_preview_operation
        bne.s   .advance
        lea     game_preview_cursor,a0
        lea     game_preview_selected,a1
        bsr     game_preview_compare_cursor
        tst.l   d0
        bpl.s   .advance
        cmpi.w  #PREVIEW_POINTS,game_preview_prefix_count
        bcc     game_preview_missing
        lea     game_preview_paths,a0
        moveq   #0,d0
        move.w  game_preview_prefix_count,d0
        lsl.w   #3,d0
        adda.w  d0,a0
        bsr     game_preview_write_point
        addq.w  #1,game_preview_prefix_count
.advance:
        addq.l  #1,game_preview_cursor+4
        bcc.s   .done
        addq.l  #1,game_preview_cursor
.done:  rts

game_preview_missing:
        move.w  #PREVIEW_CONTEXT_MISSING,game_preview_status
        clr.l   game_preview_counts
        rts

game_preview_resolved:
        moveq   #0,d0
        move.b  game_preview_action_kind,d0
        cmp.w   game_preview_kind,d0
        bne.s   game_preview_missing
        lea     game_preview_selected,a0
        lea     game_preview_action,a1
        bsr     game_preview_compare_cursor
        tst.l   d0
        bgt.s   game_preview_missing
        cmpi.w  #3,game_preview_kind
        beq.s   .serve
        tst.b   game_preview_incoming_valid
        beq.s   game_preview_missing
        lea     game_preview_selected,a0
        lea     game_preview_incoming,a1
        bsr     game_preview_compare_cursor
        tst.l   d0
        bmi.s   game_preview_missing
        bra.s   .ready
.serve:
        ; A completed serve is selectable only at its recorded pre-launch op.
        lea     game_preview_selected,a0
        lea     game_preview_origin,a1
        bsr     game_preview_compare_cursor
        tst.l   d0
        bne.s   game_preview_missing
.ready: bra     game_preview_prepare

game_preview_prepare:
        ; Keep original incoming prefix; discard all variant bookkeeping.
        lea     game_preview_counts,a0
        moveq   #(game_preview_state_end-game_preview_counts)/2-1,d0
.clear: clr.w   (a0)+
        dbra    d0,.clear
        move.w  #1,game_preview_cache_valid
        lea     game_preview_edited_state,a0
        lea     game_preview_selected_state,a1
        bsr     game_history_copy_state
        lea     game_preview_edited_state+G_LOWER,a0
        tst.w   game_preview_end
        beq.s   .edit
        adda.w  #G_UPPER,a0
.edit:  move.w  game_preview_x,d0
        move.b  d0,P_X(a0)
        move.w  game_preview_y,d0
        move.b  d0,P_Y(a0)
        lea     game_preview_held_state,a0
        lea     game_preview_edited_state,a1
        bsr     game_history_copy_state
        lea     game_preview_released_state,a0
        lea     game_preview_edited_state,a1
        bsr     game_history_copy_state
        move.w  game_preview_prefix_count,game_preview_counts
        move.w  game_preview_prefix_count,game_preview_counts+2
        lea     game_preview_paths,a0
        lea     game_preview_paths+PREVIEW_POINTS*PREVIEW_POINT_BYTES,a1
        move.w  game_preview_prefix_count,d0
        beq.s   .cursors
        subq.w  #1,d0
.prefix:move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        dbra    d0,.prefix
.cursors:
        move.l  game_preview_selected,game_preview_stream_cursors
        move.l  game_preview_selected+4,game_preview_stream_cursors+4
        move.l  game_preview_selected,game_preview_stream_cursors+8
        move.l  game_preview_selected+4,game_preview_stream_cursors+12
        move.w  #PREVIEW_PRIME,game_preview_status
        rts

; A0 envelope. Preserve every recorded logical argument except explicit pads.
game_preview_execute_record:
        move.w  (a0)+,d6
        beq     .invalid
        cmpi.w  #9,d6
        bhi.s   .invalid
        cmpi.w  #2,d6
        bne.s   .valid
        cmpi.w  #1,4(a0)
        bhi.s   .invalid
.valid: move.w  d6,game_preview_operation
        subq.w  #1,d6
        lsl.w   #2,d6
        lea     game_history_operations,a1
        move.l  (a1,d6.w),a1
        move.w  (a0)+,d0
        move.w  (a0)+,d1
        move.w  (a0)+,d2
        move.w  (a0)+,d3
        move.w  (a0)+,d4
        move.w  (a0)+,d5
        cmpi.b  #2,game_preview_active
        bne.s   .call
        cmpi.w  #3,game_preview_operation
        bne.s   .call
        bsr     game_preview_override_pads
.call:  st      game_history_replaying
        jsr     (a1)
        clr.b   game_history_replaying
        moveq   #1,d0
        rts
.invalid:
        moveq   #0,d0
        rts

game_preview_override_pads:
        moveq   #0,d6
        move.w  game_preview_end,d6
        lea     game_lower_owner,a0
        move.b  (a0,d6.w),d6
        andi.w  #255,d6
        beq.s   .owner_a
        andi.w  #$ffc0,d1
        tst.b   game_preview_variant
        bne.s   .done
        ori.w   #$10,d1
        rts
.owner_a:
        andi.w  #$ffc0,d0
        tst.b   game_preview_variant
        bne.s   .done
        ori.w   #$10,d0
.done:  rts

game_preview_prime_one:
        moveq   #0,d0
        moveq   #0,d1
        move.b  game_input_bits,d0
        move.b  game_input_bits+1,d1
        bsr     game_preview_override_pads
        bsr     game_core_sample_pads_body
        addq.w  #1,game_preview_primed
        cmpi.w  #2,game_preview_primed
        bne.s   .done
        move.w  #PREVIEW_HELD,game_preview_status
.done:  rts

game_preview_continue_one:
        moveq   #0,d7
        move.b  game_preview_variant,d7
        move.w  d7,d6
        lsl.w   #3,d6
        lea     game_preview_stream_cursors,a0
        adda.w  d6,a0
        lea     game_history_cursor,a1
        bsr     game_preview_compare_cursor
        tst.l   d0
        bpl.s   .synthetic
        move.l  4(a0),game_history_replay_low
        bsr     game_history_record_address
        ; A preview never crosses retained initialization/selection/title reset.
        move.w  (a0),d0
        cmpi.w  #1,d0
        beq     .invalid_record
        cmpi.w  #2,d0
        beq     .invalid_record
        cmpi.w  #6,d0
        beq     .invalid_record
        bsr     game_preview_execute_record
        tst.l   d0
        beq     .invalid_record
        moveq   #0,d7
        move.b  game_preview_variant,d7
        move.w  d7,d6
        lsl.w   #3,d6
        lea     game_preview_stream_cursors,a0
        adda.w  d6,a0
        addq.l  #1,4(a0)
        bcc     .after
        addq.l  #1,(a0)
        bra.s   .after
.synthetic:
        moveq   #0,d6
        move.b  game_preview_variant,d6
        add.w   d6,d6
        lea     game_preview_synthetic_phases,a0
        adda.w  d6,a0
        move.w  (a0),d6
        addq.w  #1,(a0)
        andi.w  #3,(a0)
        cmpi.w  #1,d6
        beq.s   .pads
        cmpi.w  #2,d6
        beq.s   .result
        cmpi.w  #3,d6
        beq.s   .tick
        move.w  #7,game_preview_operation
        bsr     game_round_poll_body
        bra.s   .after
.pads:  move.w  #3,game_preview_operation
        moveq   #0,d0
        moveq   #0,d1
        move.b  game_input_bits,d0
        move.b  game_input_bits+1,d1
        bsr     game_preview_override_pads
        bsr     game_core_sample_pads_body
        bra.s   .after
.result:
        move.w  #4,game_preview_operation
        moveq   #0,d0
        moveq   #0,d1
        moveq   #0,d2
        moveq   #0,d3
        moveq   #0,d4
        moveq   #0,d5
        bsr     game_core_sample_result_body
        bra.s   .after
.tick:  move.w  #8,game_preview_operation
        bsr     game_tick_dispatch_body
.after: cmpi.w  #GAME_PLAYING,game_lifecycle
        beq.s   .sample
        cmpi.w  #GAME_PLAYING,game_preview_selected_state+(game_lifecycle-game_core_state)
        beq     .invalid_record
.sample:cmpi.w  #8,game_preview_operation
        bne.s   .done
        moveq   #0,d7
        move.b  game_preview_variant,d7
        move.w  d7,d6
        add.w   d6,d6
        lea     game_preview_dispatches,a0
        addq.w  #1,(a0,d6.w)
        bsr     game_preview_append_point
        tst.l   d0
        bne.s   .outcome
        moveq   #PREVIEW_LIMIT,d0
        bra     game_preview_finish_variant
.outcome:
        bsr     game_preview_observe_outcome
.done:  rts
.invalid_record:
        move.w  #PREVIEW_LIFECYCLE,d0
        bra     game_preview_finish_variant

game_preview_append_point:
        moveq   #0,d7
        move.b  game_preview_variant,d7
        move.w  d7,d6
        add.w   d6,d6
        lea     game_preview_counts,a1
        move.w  (a1,d6.w),d0
        cmpi.w  #PREVIEW_POINTS,d0
        bcc.s   .full
        addq.w  #1,(a1,d6.w)
        lsl.w   #3,d0
        tst.w   d7
        beq.s   .point
        addi.w  #PREVIEW_POINTS*PREVIEW_POINT_BYTES,d0
.point: lea     game_preview_paths,a0
        adda.w  d0,a0
        bsr     game_preview_write_point
        moveq   #1,d0
        rts
.full:  moveq   #0,d0
        rts

; Eight bytes from actual projection, never a second trajectory calculation.
game_preview_write_point:
        move.b  game_court_x,(a0)+
        move.b  game_court_y,(a0)+
        move.b  game_ball_x,(a0)+
        move.b  game_ball_y,(a0)+
        move.b  game_contact,(a0)+
        move.b  game_flight,(a0)+
        move.b  game_shadow_colour,d0
        lsl.b   #4,d0
        or.b    game_ball_colour,d0
        move.b  d0,(a0)+
        move.b  game_tick,(a0)+
        rts

game_preview_observe_outcome:
        moveq   #0,d7
        move.b  game_preview_variant,d7
        lea     game_preview_launches,a0
        tst.b   (a0,d7.w)
        beq.s   .incoming
        lea     game_preview_interceptions,a0
        tst.b   (a0,d7.w)
        bne.s   .interception
        btst    #0,game_contact
        bne.s   .net
        move.b  game_contact,d0
        andi.b  #$88,d0
        bne.s   .out
        btst    #1,game_contact
        bne.s   .landing
        bra.s   .limit
.incoming:
        cmpi.w  #3,game_preview_kind
        beq.s   .limit
        move.b  game_contact,d0
        andi.b  #$8d,d0
        bne.s   .no_contact
.limit: move.w  d7,d6
        add.w   d6,d6
        lea     game_preview_counts,a0
        cmpi.w  #PREVIEW_POINTS,(a0,d6.w)
        bcc.s   .limited
        lea     game_preview_dispatches,a0
        cmpi.w  #PREVIEW_POINTS,(a0,d6.w)
        bcc.s   .limited
        cmpi.w  #GAME_PLAYING,game_lifecycle
        beq.s   .done
        cmpi.w  #GAME_PLAYING,game_preview_selected_state+(game_lifecycle-game_core_state)
        beq.s   .lifecycle
.done:  rts
.interception:
        moveq   #PREVIEW_INTERCEPTION,d0
        bra.s   game_preview_finish_variant
.net:   moveq   #PREVIEW_NET,d0
        bra.s   game_preview_finish_variant
.out:   moveq   #PREVIEW_OUT,d0
        bra.s   game_preview_finish_variant
.landing:
        moveq   #PREVIEW_LANDING,d0
        bra.s   game_preview_finish_variant
.no_contact:
        moveq   #PREVIEW_NO_CONTACT,d0
        bra.s   game_preview_finish_variant
.limited:
        moveq   #PREVIEW_LIMIT,d0
        bra.s   game_preview_finish_variant
.lifecycle:
        moveq   #PREVIEW_LIFECYCLE,d0

game_preview_finish_variant:
        moveq   #0,d7
        move.b  game_preview_variant,d7
        move.w  d7,d6
        add.w   d6,d6
        lea     game_preview_outcomes,a0
        move.w  d0,(a0,d6.w)
        tst.w   d7
        bne.s   .ready
        move.w  #PREVIEW_RELEASED,game_preview_status
        rts
.ready: bsr     game_preview_compare_geometry
        move.w  #PREVIEW_READY,game_preview_status
        rts

game_preview_compare_geometry:
        clr.w   game_preview_coincident
        move.w  game_preview_counts,d7
        cmp.w   game_preview_counts+2,d7
        bne.s   .done
        tst.w   d7
        beq.s   .same
        subq.w  #1,d7
        lea     game_preview_paths,a0
        lea     game_preview_paths+PREVIEW_POINTS*PREVIEW_POINT_BYTES,a1
.point: cmpm.l  (a0)+,(a1)+
        bne.s   .done
        moveq   #0,d0
        move.b  2(a0),d0
        bsr     game_preview_visibility
        move.w  d0,d2
        moveq   #0,d0
        move.b  2(a1),d0
        bsr     game_preview_visibility
        cmp.w   d2,d0
        bne.s   .done
        move.b  3(a0),d0
        cmp.b   3(a1),d0
        bne.s   .done
        addq.w  #4,a0
        addq.w  #4,a1
        dbra    d7,.point
.same:  move.w  #1,game_preview_coincident
.done:  rts

game_preview_visibility:
        move.b  d0,d1
        andi.w  #15,d0
        sne     d0
        andi.w  #1,d0
        andi.b  #$f0,d1
        beq.s   .done
        ori.w   #2,d0
.done:  rts

; Called inside the existing preserving history hooks only while mode2. D7=end.
game_preview_contact_begin:
        cmpi.b  #1,game_preview_active
        bne.s   .done
        cmp.w   game_preview_end,d7
        bne.s   .done
        btst    #7,game_contact
        bne.s   .done
        lea     game_preview_cursor,a0
        lea     game_preview_origin,a1
        bsr     game_preview_compare_cursor
        tst.l   d0
        bne.s   .done
        st      game_preview_probe_seen
.done:  rts

; D6 actual kind1(return) or3(serve), D7 physical end, A4 actual play state.
game_preview_launch:
        tst.b   game_preview_active
        beq     .done
        cmpi.b  #1,game_preview_active
        bne.s   .alternative
        cmp.w   game_preview_end,d7
        beq.s   .human
        move.l  game_preview_cursor,game_preview_incoming
        move.l  game_preview_cursor+4,game_preview_incoming+4
        st      game_preview_incoming_valid
        clr.w   game_preview_prefix_count
        rts
.human: cmpi.w  #3,d6
        beq.s   .serve
        tst.b   game_preview_probe_seen
        beq.s   .done
        bra.s   .found
.serve: cmpi.w  #3,game_preview_kind
        bne.s   .done
        lea     game_preview_cursor,a0
        lea     game_preview_origin,a1
        bsr     game_preview_compare_cursor
        tst.l   d0
        bne.s   .done
.found: move.b  d6,game_preview_action_kind
        bra.s   game_preview_found_action
.alternative:
        moveq   #0,d0
        move.b  game_preview_variant,d0
        cmp.w   game_preview_end,d7
        bne.s   .opponent
        lea     game_preview_launches,a0
        st      (a0,d0.w)
        rts
.opponent:
        lea     game_preview_launches,a0
        tst.b   (a0,d0.w)
        beq.s   .done
        lea     game_preview_interceptions,a0
        st      (a0,d0.w)
.done:  rts

game_preview_found_action:
        st      game_preview_action_found
        move.l  game_preview_cursor,game_preview_action
        move.l  game_preview_cursor+4,game_preview_action+4
        rts

game_preview_copy_history:
        moveq   #(game_history_state_end-game_history_state)/4-1,d0
.copy:  move.l  (a1)+,(a0)+
        dbra    d0,.copy
        rts

game_preview_restore_selected:
        lea     game_core_state,a0
        lea     game_preview_selected_state,a1
        bsr     game_history_copy_state
        lea     game_history_state,a0
        lea     game_preview_history_saved,a1
        bra     game_preview_copy_history

game_preview_selection_unchanged:
        lea     game_core_state,a0
        lea     game_preview_selected_state,a1
        move.w  #GAME_CORE_STATE_SIZE/2-1,d0
.state: cmpm.w  (a0)+,(a1)+
        bne.s   .invalid
        dbra    d0,.state
        lea     game_history_state,a0
        lea     game_preview_history_saved,a1
        moveq   #(game_history_state_end-game_history_state)/4-1,d0
.meta:  cmpm.l  (a0)+,(a1)+
        bne.s   .invalid
        dbra    d0,.meta
        moveq   #1,d0
        rts
.invalid:
        moveq   #0,d0
        rts

game_preview_context_address:
        lea     game_preview_held_state,a0
        tst.w   d7
        beq.s   .done
        lea     game_preview_released_state,a0
.done:  rts

; Successful external history mutations retire publication/generation. The
; request-owned zero-op oldest checkpoint seek uses active3 and is exempt.
game_preview_invalidate:
        tst.b   game_preview_active
        bne.s   .done
        clr.w   game_preview_cache_valid
        clr.l   game_preview_counts
        move.w  #PREVIEW_CANCELED,game_preview_status
        cmpi.l  #$ffffffff,game_preview_generation
        beq.s   .done
        addq.l  #1,game_preview_generation
.done:  rts
