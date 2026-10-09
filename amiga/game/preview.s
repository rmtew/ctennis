; Isolated fixed-buffer previews over the actual logical APIs. Caller freezes
; the physical dispatcher. Bodies run in supplied private state; each worker
; yield restores history metadata without writing the frozen canonical state.
PREVIEW_POINTS equ 513
PREVIEW_SEGMENT_PHASES equ 256
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

; D0 expected generation, D1 retained index ordinal ($ffff current serve,
; $fffe current incoming episode),
; D2/D3 requested byte X/Y. Current history_position is the selected boundary.
; Invalid/stale requests make no changes. D0=1 accepted, D0=0 rejected.
game_preview_request:
        cmpi.w  #SEEK_JOB_PENDING,game_history_seek_status
        beq     .invalid
        cmpi.w  #SEEK_JOB_READY,game_history_seek_status
        beq     .invalid
        cmp.l   game_preview_generation,d0
        bne     .invalid
        cmpi.l  #$fffffffe,d0
        bcc     .invalid
        bsr     game_preview_selection_valid
        tst.l   d0
        beq     .invalid
        cmpi.w  #GAME_PLAYING,game_lifecycle
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
        cmpi.w  #$fffe,d1
        beq.s   .current_incoming
        cmpi.w  #$ffff,d1
        beq.s   .fallback
        cmp.w   game_history_attempt_count,d1
        bcc     .invalid_saved
        add.w   game_history_attempt_first,d1
        andi.w  #HISTORY_ATTEMPTS-1,d1
        move.w  d1,d0
        bsr     game_history_attempt_address
        move.w  8(a0),d6
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
.current_incoming:
        moveq   #0,d7
        tst.b   game_play_state+G_LOWER_AI
        beq.s   .current_end
        moveq   #1,d7
.current_end:
        lea     game_play_state+G_LOWER_AI,a1
        tst.b   (a1,d7.w)
        bne     .invalid_saved
        moveq   #0,d6
        suba.l  a5,a5
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
        ; Match player-tick priority: setup/wait precede timed serve.
        ; The complete timed boundary at $10 is still before launch; the
        ; service tail advances it to $11 after the actual launch hook.
        cmpi.b  #$20,d0
        bne.s   .fallback_ready
        cmpi.b  #$10,game_serve_clock
        bhi     .invalid_saved
.fallback_ready:
        moveq   #3,d6
        suba.l  a5,a5
.bounds:
        bsr     game_preview_player_address
        cmpi.w  #3,d6
        bne.s   .incoming_bounds
        ; Current serves have a known canonical phase. Incoming limits are
        ; checked in prepare against the resolved matching launch context.
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
.incoming_bounds:
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
        tst.w   game_preview_kind
        beq.s   .resolve_current
        move.l  a5,d0
        beq.s   .serve_now
        move.l  (a5),game_preview_origin
        move.l  4(a5),game_preview_origin+4
.resolve_current:
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
        cmpi.w  #SEEK_JOB_PENDING,game_history_seek_status
        beq     .invalid
        cmpi.w  #SEEK_JOB_READY,game_history_seek_status
        beq     .invalid
        cmp.l   game_preview_generation,d0
        bne     .invalid
        cmpi.l  #$ffffffff,d0
        beq     .invalid
        cmpi.w  #1,d1
        bcs     .invalid
        cmpi.w  #4,d1
        bhi     .invalid
        bsr     game_preview_selection_valid
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
        cmpi.b  #1,game_preview_active
        beq.s   .resolve
        lea     game_preview_held_state,a5
        move.b  #1,game_preview_active
.resolve:
        bsr     game_preview_resolve_one
        bra.s   .spent
.alternative:
        bsr     game_preview_desired_variant
        cmpi.b  #2,game_preview_active
        bne.s   .load_variant
        cmp.b   game_preview_variant,d7
        beq.s   .variant_loaded
.load_variant:
        move.b  d7,game_preview_variant
        bsr     game_preview_context_address
        move.l  a0,a5
        move.b  #2,game_preview_active
.variant_loaded:
        cmpi.w  #PREVIEW_PRIME,game_preview_status
        bne.s   .continue
        bsr     game_preview_prime_one
        bra.s   .spent
.continue:
        bsr     game_preview_continue_one
.spent:
        subq.w  #1,game_preview_budget
        beq.s   .yield
        cmpi.w  #PREVIEW_READY,game_preview_status
        bcc.s   .yield
        cmpi.b  #2,game_preview_active
        bne     .next
        ; Actual bodies clobber D7. Derive the next owner from persisted phase.
        bsr     game_preview_desired_variant
        cmp.b   game_preview_variant,d7
        beq     .next
        bsr     game_preview_release_current
        bra     .next
.yield:
        bsr     game_preview_release_current
        movem.l (sp)+,d2-d7/a2-a6
.valid:
        moveq   #1,d0
        rts
.invalid:
        moveq   #0,d0
        rts

; Private bodies persist directly in their owner; only metadata needs retirement.
game_preview_release_current:
        tst.b   game_preview_active
        beq.s   .done
        bsr     game_preview_restore_owner
.done:  rts

game_preview_restore_owner:
        lea     game_history_state,a0
        lea     game_preview_history_saved,a1
        bsr     game_preview_copy_history
        clr.b   game_preview_active
game_preview_context_released:
        rts

; No register owner survives a body call: status/primed are authoritative.
game_preview_desired_variant:
        moveq   #0,d7
        cmpi.w  #PREVIEW_PRIME,game_preview_status
        bne.s   .running
        move.w  game_preview_primed,d7
        rts
.running:
        cmpi.w  #PREVIEW_RELEASED,game_preview_status
        bne.s   .done
        moveq   #1,d7
.done:  rts

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
        cmpi.w  #SEEK_JOB_PENDING,game_history_seek_status
        beq     .invalid
        cmpi.w  #SEEK_JOB_READY,game_history_seek_status
        beq     .invalid
        cmp.l   game_preview_generation,d0
        bne.s   .invalid
        cmpi.l  #$ffffffff,d0
        beq.s   .invalid
        cmpi.w  #PREVIEW_READY,game_preview_status
        bne.s   .invalid
        bsr     game_preview_selection_valid
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
        ; A current receiving episode ends at the frozen pre-operation boundary.
        tst.w   game_preview_kind
        bne.s   .record
        lea     game_preview_cursor,a0
        lea     game_preview_selected,a1
        bsr     game_preview_compare_cursor
        tst.l   d0
        bmi.s   .record
        tst.b   game_preview_incoming_valid
        beq     game_preview_missing
        bsr     game_preview_restore_owner
        bra     game_preview_prepare
.record:
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
        ; The hook only marked a launch. Copy after the complete body/tail.
        tst.b   game_preview_incoming_pending
        beq.s   .captured
        clr.b   game_preview_incoming_pending
        lea     game_preview_incoming_state,a0
        move.l  a5,a1
        bsr     game_history_copy_state
.captured:
        tst.w   game_preview_kind
        bne.s   .historical_action
        move.b  game_contact-game_core_state(a5),d0
        andi.b  #$8d,d0
        beq     .advance
        clr.b   game_preview_incoming_valid
        bra     .advance
.historical_action:
        tst.b   game_preview_action_found
        bne     game_preview_resolved
        tst.b   game_preview_probe_seen
        beq.s   .prefix
        cmpi.w  #GAME_PLAYING,game_lifecycle-game_core_state(a5)
        bne.s   .miss
        move.b  game_contact-game_core_state(a5),d0
        andi.b  #$8d,d0
        beq.s   .prefix
.miss:
        move.b  #2,game_preview_action_kind
        bsr     game_preview_found_action
        bra     game_preview_resolved
.prefix:
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
.ready: bsr     game_preview_restore_owner
        bra     game_preview_prepare

game_preview_prepare:
        ; Check the actual incoming phase limits before publishing an edit.
        cmpi.w  #3,game_preview_kind
        beq.s   .valid_placement
        lea     game_preview_incoming_state+G_LOWER,a3
        lea     game_lower_limits,a0
        tst.w   game_preview_end
        beq.s   .placement_phase
        adda.w  #G_UPPER,a3
        lea     game_upper_limits,a0
.placement_phase:
        moveq   #0,d0
        move.b  P_ANIMATION(a3),d0
        lsr.w   #3,d0
        andi.w  #12,d0
        adda.w  d0,a0
        move.w  game_preview_x,d0
        cmp.b   2(a0),d0
        bcc     game_preview_missing
        cmp.b   3(a0),d0
        bcs     game_preview_missing
        move.w  game_preview_y,d0
        cmp.b   (a0),d0
        bcc     game_preview_missing
        cmp.b   1(a0),d0
        bcs     game_preview_missing
.valid_placement:
        ; Discard all variant bookkeeping; incoming cache remains immutable.
        lea     game_preview_counts,a0
        moveq   #(game_preview_state_end-game_preview_counts)/2-1,d0
.clear: clr.w   (a0)+
        dbra    d0,.clear
        move.w  #1,game_preview_cache_valid
        lea     game_preview_edited_state,a0
        lea     game_preview_selected_state,a1
        cmpi.w  #3,game_preview_kind
        beq.s   .source
        lea     game_preview_incoming_state,a1
.source:bsr     game_history_copy_state
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
        ; The common initial sample is the actual complete launch projection.
        lea     game_preview_edited_state,a5
        bsr     game_preview_append_point
        move.b  #1,game_preview_variant
        bsr     game_preview_append_point
        clr.b   game_preview_variant
        lea     game_preview_selected,a0
        cmpi.w  #3,game_preview_kind
        beq.s   .cursors
        lea     game_preview_incoming,a0
.cursors:
        move.l  (a0),game_preview_stream_cursors
        move.l  4(a0),game_preview_stream_cursors+4
        cmpi.w  #3,game_preview_kind
        beq.s   .second
        addq.l  #1,game_preview_stream_cursors+4
        bcc.s   .second
        addq.l  #1,game_preview_stream_cursors
.second:
        move.l  game_preview_stream_cursors,game_preview_stream_cursors+8
        move.l  game_preview_stream_cursors+4,game_preview_stream_cursors+12
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
        lea     game_preview_operations,a1
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

; Private retained envelopes call the same actual bodies. Public wrappers bind
; canonical live state and therefore are deliberately absent from this table.
game_preview_operations:
        dc.l game_core_init_body,game_core_select_body
        dc.l game_core_sample_pads_body,game_core_sample_result_body
        dc.l game_core_clear_inputs_body,game_core_return_title_body
        dc.l game_round_poll_body,game_tick_dispatch_body
        dc.l game_core_latch_actions_body

game_preview_override_pads:
        moveq   #0,d6
        move.w  game_preview_end,d6
        lea     game_lower_owner-game_core_state(a5),a0
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
        move.b  game_input_bits-game_core_state(a5),d0
        move.b  game_input_bits+1-game_core_state(a5),d1
        bsr     game_preview_override_pads
        bsr     game_core_sample_pads_body
        addq.w  #1,game_preview_primed
        cmpi.w  #2,game_preview_primed
        bne.s   .done
        move.w  #PREVIEW_HELD,game_preview_status
.done:  rts

game_preview_continue_one:
        ; After human launch, only the exact original geometric ball phase runs.
        moveq   #0,d7
        move.b  game_preview_variant,d7
        lea     game_preview_launches,a0
        tst.b   (a0,d7.w)
        bne     game_preview_flight_one
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
        move.b  game_input_bits-game_core_state(a5),d0
        move.b  game_input_bits+1-game_core_state(a5),d1
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
.after: cmpi.w  #GAME_PLAYING,game_lifecycle-game_core_state(a5)
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

game_preview_flight_one:
        move.w  d7,d6
        add.w   d6,d6
        lea     game_preview_flight_phases,a0
        cmpi.w  #PREVIEW_SEGMENT_PHASES,(a0,d6.w)
        bcc.s   .limited
        addq.w  #1,(a0,d6.w)
        lea     game_play_state-game_core_state(a5),a4
        bsr     game_ball_tick
        bsr     game_preview_append_point
        tst.l   d0
        beq.s   .limited
        bsr     game_preview_observe_outcome
        rts
.limited:
        moveq   #PREVIEW_LIMIT,d0
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
        move.b  game_court_x-game_core_state(a5),(a0)+
        move.b  game_court_y-game_core_state(a5),(a0)+
        move.b  game_ball_x-game_core_state(a5),(a0)+
        move.b  game_ball_y-game_core_state(a5),(a0)+
        move.b  game_contact-game_core_state(a5),(a0)+
        move.b  game_flight-game_core_state(a5),(a0)+
        move.b  game_shadow_colour-game_core_state(a5),d0
        lsl.b   #4,d0
        or.b    game_ball_colour-game_core_state(a5),d0
        move.b  d0,(a0)+
        move.b  game_tick-game_core_state(a5),(a0)+
        rts

game_preview_observe_outcome:
        moveq   #0,d7
        move.b  game_preview_variant,d7
        lea     game_preview_launches,a0
        tst.b   (a0,d7.w)
        beq.s   .incoming
        btst    #0,game_contact-game_core_state(a5)
        bne.s   .net
        move.b  game_contact-game_core_state(a5),d0
        andi.b  #$88,d0
        bne.s   .out
        btst    #1,game_contact-game_core_state(a5)
        bne.s   .landing
        bra.s   .limit
.incoming:
        cmpi.w  #3,game_preview_kind
        beq.s   .limit
        move.b  game_contact-game_core_state(a5),d0
        andi.b  #$8d,d0
        bne.s   .no_contact
.limit: move.w  d7,d6
        add.w   d6,d6
        lea     game_preview_counts,a0
        cmpi.w  #PREVIEW_POINTS,(a0,d6.w)
        bcc.s   .limited
        lea     game_preview_launches,a0
        tst.b   (a0,d7.w)
        bne.s   .lifecycle_check
        lea     game_preview_dispatches,a0
        cmpi.w  #PREVIEW_SEGMENT_PHASES,(a0,d6.w)
        bcc.s   .limited
.lifecycle_check:
        cmpi.w  #GAME_PLAYING,game_lifecycle-game_core_state(a5)
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
        btst    #7,game_contact-game_core_state(a5)
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
        st      game_preview_incoming_pending
        clr.w   game_preview_prefix_count
        rts
.human: tst.w   game_preview_kind
        bne.s   .human_action
        clr.b   game_preview_incoming_valid
        rts
.human_action:
        cmpi.w  #3,d6
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

; Callers already checked generation. Main-loop APIs own all validity changes;
; IRQ/presentation never mutate selected simulation/history or generation.
game_preview_selection_valid:
        cmpi.b  #2,game_history_mode
        bne.s   .invalid
        tst.b   game_preview_active
        bne.s   .invalid
        tst.b   game_history_replaying
        bne.s   .invalid
        tst.b   game_history_seek_active
        bne.s   .invalid
        moveq   #1,d0
        rts
.invalid:
        moveq   #0,d0
        rts

; Explicit test diagnostic catches unversioned corruption. No runtime caller.
        ifd PREVIEW_DEBUG
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

        endif

game_preview_context_address:
        lea     game_preview_held_state,a0
        tst.w   d7
        beq.s   .done
        lea     game_preview_released_state,a0
.done:  rts

; Successful external history mutations retire publication/generation. The
; request-owned zero-op oldest checkpoint seek uses active3 and is exempt.
game_preview_invalidate:
        cmpi.b  #3,game_preview_active
        beq.s   .done
        clr.w   game_preview_cache_valid
        clr.l   game_preview_counts
        move.w  #PREVIEW_CANCELED,game_preview_status
        cmpi.l  #$ffffffff,game_preview_generation
        beq.s   .done
        addq.l  #1,game_preview_generation
.done:  rts
