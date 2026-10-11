; One root deadline owner. Complete elapsed allowances remain hypotheses.
; Record envelopes are semantic boundaries, not compulsory scheduling yields.
TUTORIAL_BG_CHUNK_E equ 1000
TUTORIAL_BG_PHYSICS_E equ 4000
TUTORIAL_BG_FULL_E equ 10000
; Separate complete-owner hypothesis for one exact returned serve stage.
; Qualification is finite; this does not reduce the original full reservation.
TUTORIAL_BG_SERVE_STAGE_E equ 4000
TUTORIAL_BG_SERVICE_E equ 500
TUTORIAL_BG_MARGIN_E equ 500
TUTORIAL_BG_CALLBACK_E equ 11150
TUTORIAL_BG_ENTRY_E equ 400
TUTORIAL_BG_COMPLETION_MARGIN_E equ 250
TUTORIAL_BG_READY_LINE equ 253
TUTORIAL_BG_LINE_CCK equ 226
TUTORIAL_LOOKAHEAD equ 8
TUTORIAL_JOB_PREVIEW equ 1
TUTORIAL_JOB_ENDPOINT equ 2
TUTORIAL_JOB_GEOMETRY equ 3
TUTORIAL_JOB_PRODUCER equ 4
TUTORIAL_JOB_FOOTER equ 5
TUTORIAL_JOB_RESULT equ 6
TUTORIAL_JOB_FOOTER_COMMIT equ 7

tutorial_background:
        tst.b   tutorial_active
        beq     .return
        tst.b   ui_paused
        beq     .return
        tst.b   tutorial_enter_pending
        bne     .return
        tst.b   tutorial_title_pending
        bne     .return
        tst.b   tutorial_resume_defer
        bne     .return
        tst.b   game_preview_active
        bne     .return
        tst.b   game_history_replaying
        bne     .return
        tst.b   game_history_seek_active
        bne     .return
        cmpi.w  #SEEK_JOB_PENDING,game_history_seek_status
        beq     .return
        cmpi.w  #SEEK_JOB_READY,game_history_seek_status
        beq     .return
        movem.l d0-d7/a0-a6,-(sp)
        clr.w   tutorial_job_kind
        clr.w   tutorial_job_budget
        cmpi.b  #1,tutorial_active_variant
        bhi     .done
        move.l  simulation_interval,d0
        sub.l   simulation_phase,d0
        bcs     .done
        cmpi.l  #TUTORIAL_BG_CHUNK_E+TUTORIAL_BG_SERVICE_E+TUTORIAL_BG_MARGIN_E,d0
        bcs     .done
        tst.b   tutorial_menu
        bne     .menu
        move.l  tutorial_generation,d0
        cmp.l   game_preview_generation,d0
        bne     .presentation_only
        cmp.l   tutorial_presentation_generation,d0
        bne     .done
.presentation_only:
        tst.b   tutorial_placement_dirty
        bne     .producer
        bsr     tutorial_animation_due
        tst.l   d0
        bne     .producer
        tst.b   tutorial_work_pending
        beq     .residual_footer
        cmpi.w  #PREVIEW_READY,game_preview_status
        bhi     .unavailable
        tst.w   game_preview_status
        beq     .unavailable
        moveq   #0,d2
        move.b  tutorial_active_variant,d2
        move.w  d2,tutorial_job_variant
        ; Terminal/ready branches cannot have a pending endpoint. Test those
        ; cheap immutable fields before entering the full eligibility wrapper.
        move.w  tutorial_job_variant,d2
        add.w   d2,d2
        lea     game_preview_outcomes,a0
        tst.w   (a0,d2.w)
        bne.s   .residual
        moveq   #0,d1
        move.w  tutorial_job_variant,d1
        lea     game_preview_endpoint_ready,a0
        tst.b   (a0,d1.w)
        bne.s   .waterline
        ; The branch already retains its next-query prerequisites at actual
        ; launch/flight/query transitions. Impossible queries need no repeated
        ; public eligibility frame. A possible query still validates all live
        ; API conditions and receives fresh deadline admission below.
        lea     game_preview_launch_saved,a0
        tst.b   (a0,d1.w)
        beq     .preview
        lea     game_preview_flight_phases,a0
        cmpi.w  #4,(a0,d2.w)
        bcs     .preview
        lea     game_preview_endpoint_attempted,a0
        tst.b   (a0,d1.w)
        bne     .preview
        move.l  tutorial_generation,d0
        jsr     game_preview_endpoint_pending
        tst.l   d0
        bne     .endpoint
        bra     .preview
.waterline:
        lea     game_preview_counts,a0
        move.w  (a0,d2.w),d0
        sub.w   tutorial_animation_index,d0
        bcs     .preview
        cmpi.w  #TUTORIAL_LOOKAHEAD,d0
        bcs     .preview
.residual:
        tst.w   game_preview_outcomes
        beq.s   .other
        tst.w   game_preview_outcomes+2
        beq.s   .other
        cmpi.w  #PREVIEW_READY,game_preview_status
        beq     .result
        move.w  #TUTORIAL_JOB_GEOMETRY,tutorial_job_kind
        move.l  #TUTORIAL_BG_CHUNK_E,tutorial_job_cost
        bra     .admit
.other:
        ; Alternate the nonurgent footer and other branch on residual yields.
        tst.w   tutorial_residual_turn
        beq.s   .other_branch
        tst.w   tutorial_footer_ready
        bne     .footer_commit
        tst.b   tutorial_footer_dirty
        bne     .footer
.other_branch:
        ; Rotate on the residual attempt even when this branch cannot fit.
        ; A declined full operation must not starve the smaller footer job.
        move.w  #1,tutorial_residual_turn
        moveq   #1,d0
        eor.w   d0,tutorial_job_variant
        move.w  tutorial_job_variant,d2
        add.w   d2,d2
        lea     game_preview_outcomes,a0
        tst.w   (a0,d2.w)
        beq     .preview
.residual_footer:
        tst.w   tutorial_footer_ready
        bne     .footer_commit
        tst.b   tutorial_footer_dirty
        bne     .footer
        bra     .done
.menu:  tst.b   tutorial_placement_dirty
        bne.s   .producer
        tst.w   tutorial_render_phase
        beq     .residual_footer
        bra.s   .producer
.producer:
        move.w  #TUTORIAL_JOB_PRODUCER,tutorial_job_kind
        move.l  #6000-TUTORIAL_BG_SERVICE_E-TUTORIAL_BG_MARGIN_E,tutorial_job_cost
        bsr     tutorial_pending_canvas_eligible
        tst.l   d0
        beq.s   .canvas_cost
        move.l  #3500-TUTORIAL_BG_SERVICE_E-TUTORIAL_BG_MARGIN_E,tutorial_job_cost
        bra.s   .producer_admit
.canvas_cost:
        ; The measured pose-only owner needs no menu ROI or landing retirement.
        ; Both canvas identities must agree, since either can become free.
        ; Any uncertain/new ROI or cross retains the larger reservation.
        tst.b   tutorial_marker_ready
        bne.s   .producer_admit
        tst.b   tutorial_canvas_markers+4
        bne.s   .producer_admit
        tst.b   tutorial_canvas_markers+24
        bne.s   .producer_admit
        moveq   #-1,d0
        tst.b   tutorial_menu
        beq.s   .producer_identity
        moveq   #0,d0
        move.b  tutorial_menu_selection,d0
.producer_identity:
        cmp.b   tutorial_canvas_menus,d0
        bne.s   .producer_admit
        cmp.b   tutorial_canvas_menus+1,d0
        bne.s   .producer_admit
        move.l  #4000-TUTORIAL_BG_SERVICE_E-TUTORIAL_BG_MARGIN_E,tutorial_job_cost
.producer_admit:
        bra     .admit
.footer_commit:
        move.w  #TUTORIAL_JOB_FOOTER_COMMIT,tutorial_job_kind
        move.l  #TUTORIAL_BG_CHUNK_E,tutorial_job_cost
        bra     .admit
.footer:
        move.w  #TUTORIAL_JOB_FOOTER,tutorial_job_kind
        move.l  #TUTORIAL_BG_CHUNK_E,tutorial_job_cost
        bra     .admit
.endpoint:
        move.w  #TUTORIAL_JOB_ENDPOINT,tutorial_job_kind
        move.l  #TUTORIAL_BG_PHYSICS_E,tutorial_job_cost
        bra     .admit
.result:
        move.w  #TUTORIAL_JOB_RESULT,tutorial_job_kind
        move.l  #TUTORIAL_BG_CHUNK_E,tutorial_job_cost
        bra     .admit
.preview:
        bsr     tutorial_background_class
        tst.w   tutorial_job_budget
        beq     .done
        move.w  #TUTORIAL_JOB_PREVIEW,tutorial_job_kind
.admit:
        bsr     tutorial_job_admitted
        tst.l   d0
        bne.s   .run_job
        cmpi.w  #TUTORIAL_JOB_ENDPOINT,tutorial_job_kind
        ; Preserve the selected query's eligible seed/phase when it does not
        ; fit this gap. Advancing its dense flight here can reach terminal
        ; before any query runs, defeating selected-endpoint priority.
        beq     .done
        cmpi.w  #TUTORIAL_JOB_FOOTER,tutorial_job_kind
        bne     .done
        tst.b   tutorial_work_pending
        beq     .done
        moveq   #1,d0
        eor.w   d0,tutorial_job_variant
.smaller_prefix:
        bsr     tutorial_background_class
        tst.w   tutorial_job_budget
        beq     .done
        move.w  #TUTORIAL_JOB_PREVIEW,tutorial_job_kind
        bsr     tutorial_job_admitted
        tst.l   d0
        beq     .done
.run_job:
        move.w  tutorial_job_kind,d0
        cmpi.w  #TUTORIAL_JOB_PREVIEW,d0
        beq.s   .run_preview
        cmpi.w  #TUTORIAL_JOB_ENDPOINT,d0
        beq     .run_endpoint
        cmpi.w  #TUTORIAL_JOB_GEOMETRY,d0
        beq     .run_geometry
        cmpi.w  #TUTORIAL_JOB_PRODUCER,d0
        beq     .run_producer
        cmpi.w  #TUTORIAL_JOB_FOOTER,d0
        beq     .run_footer
        cmpi.w  #TUTORIAL_JOB_FOOTER_COMMIT,d0
        beq     .run_footer_commit
        bra     .run_result
.run_preview:
        move.l  tutorial_generation,d0
        tst.w   tutorial_job_stage
        bne.s   .run_serve_stage
        moveq   #0,d1
        move.w  tutorial_job_budget,d1
        moveq   #0,d2
        move.w  tutorial_job_variant,d2
        jsr     game_preview_step_variant
        tst.l   d0
        beq     .done
        move.w  tutorial_job_budget,d0
        sub.w   game_preview_budget,d0
        add.w   d0,tutorial_progress_operations
        bsr     tutorial_progress_returned
        move.w  #1,tutorial_residual_turn
        bra     .completed
.run_serve_stage:
        moveq   #0,d1
        move.w  tutorial_job_variant,d1
        jsr     game_preview_dispatch_stage
        tst.l   d0
        beq     .done
        tst.w   d1
        beq.s   .serve_stage_returned
        add.w   d1,tutorial_progress_operations
        bsr     tutorial_progress_returned
.serve_stage_returned:
        move.w  #1,tutorial_residual_turn
        bra     .completed
.run_endpoint:
        move.l  tutorial_generation,d0
        moveq   #0,d1
        move.w  tutorial_job_variant,d1
        jsr     game_preview_endpoint_step
        bsr     tutorial_progress_returned
        bra     .completed
.run_geometry:
        move.l  tutorial_generation,d0
        jsr     game_preview_complete
        bra     .completed
.run_producer:
        bsr     tutorial_progress_slice
        bra     .completed
.run_footer:
        bsr     tutorial_footer_step
        tst.l   d0
        beq.s   .footer_pending
        move.l  tutorial_generation,tutorial_footer_generation
        move.w  #1,tutorial_footer_ready
        clr.b   tutorial_footer_dirty
        clr.w   tutorial_residual_turn
        bra     .completed
.footer_pending:
        clr.w   tutorial_residual_turn
        bra     .completed
.run_footer_commit:
        bsr     tutorial_footer_commit
        bra     .completed
.run_result:
        move.l  tutorial_generation,d0
        jsr     game_preview_result
        tst.l   d0
        beq     .done
        move.w  d5,tutorial_coincident
        bsr     tutorial_progress_returned
        clr.b   tutorial_work_pending
        bsr     tutorial_progress_status
        clr.w   tutorial_footer_ready
        st      tutorial_footer_dirty
        bra     .completed
.unavailable:
        clr.b   tutorial_work_pending
        move.w  #TUTORIAL_UNAVAILABLE,tutorial_status
        clr.b   tutorial_pending
        bsr     tutorial_progress_reset
        bra     .done
.completed:
        addq.l  #1,tutorial_jobs_completed
.done:  movem.l (sp)+,d0-d7/a0-a6
.return:rts

; Read-only bounded-prefix plan. Retained records may have irregular prefixes;
; peek each actual opcode. Never skip a body or its intermediate checks.
tutorial_background_class:
        clr.w   tutorial_job_budget
        clr.w   tutorial_job_stage
        clr.l   tutorial_job_cost
        cmpi.w  #PREVIEW_READY,game_preview_status
        bcc     .done
        move.l  tutorial_generation,d0
        cmp.l   game_preview_generation,d0
        bne     .done
        move.l  simulation_interval,d5
        sub.l   simulation_phase,d5
        bcs     .done
        subi.l  #TUTORIAL_BG_SERVICE_E+TUTORIAL_BG_MARGIN_E,d5
        bcs     .done
        cmpi.w  #PREVIEW_RESOLVE,game_preview_status
        beq     .cold
        move.w  tutorial_job_variant,d7
        btst    d7,game_preview_primed_mask+1
        beq     .prime
        bsr     game_preview_context_address
        move.l  a0,a3
        lea     game_preview_launches,a0
        tst.b   (a0,d7.w)
        bne     .flight
        move.w  d7,d4
        lsl.w   #3,d4
        lea     game_preview_stream_cursors,a0
        adda.w  d4,a0
        lea     game_history_cursor,a1
        bsr     game_preview_compare_cursor
        tst.l   d0
        bgt     .done
        beq.s   .synthetic
        lea     game_history_oldest,a1
        bsr     game_preview_compare_cursor
        tst.l   d0
        bmi     .done
        move.l  4(a0),d6
        andi.w  #HISTORY_RECORDS-1,d6
        moveq   #0,d4
        bra.s   .next
.synthetic:
        moveq   #1,d4
        move.w  d7,d0
        add.w   d0,d0
        lea     game_preview_synthetic_phases,a0
        move.w  (a0,d0.w),d6
.next:  tst.w   d4
        bne.s   .synthetic_op
        move.w  d6,d0
        mulu.w  #HISTORY_RECORD_BYTES,d0
        move.l  game_history_store,a0
        adda.l  d0,a0
        moveq   #0,d0
        move.w  (a0),d0
        bra.s   .cost
.synthetic_op:
        moveq   #7,d0
        tst.w   d6
        beq.s   .cost
        moveq   #3,d0
        cmpi.w  #1,d6
        beq.s   .cost
        moveq   #4,d0
        cmpi.w  #2,d6
        beq.s   .cost
        moveq   #8,d0
.cost:  move.l  #TUTORIAL_BG_CHUNK_E,d1
        cmpi.w  #8,d0
        beq.s   .dispatch
        cmpi.w  #7,d0
        beq.s   .poll
        cmpi.w  #3,d0
        beq     .fit
        cmpi.w  #4,d0
        beq     .fit
        cmpi.w  #5,d0
        beq     .fit
        cmpi.w  #9,d0
        bne.s   .rejection
        bra.s   .fit
.rejection:
        ; Reset/invalid envelopes terminate honestly without executing them.
        moveq   #8,d0
        bra.s   .fit
.poll:  cmpi.w  #GAME_PLAYING,game_lifecycle-game_core_state(a3)
        bne.s   .full
        tst.b   game_score_initialized-game_core_state(a3)
        beq.s   .full
        tst.b   game_core_command-game_core_state(a3)
        bne.s   .full
        tst.b   game_restart_context-game_core_state(a3)
        bne.s   .full
        tst.b   game_entropy_policy-game_core_state(a3)
        bne.s   .full
        btst    #5,game_score_state+S_MODE-game_core_state(a3)
        beq     .fit
.full:  move.l  #TUTORIAL_BG_FULL_E,d1
        bra.s   .fit
.dispatch:
        move.l  tutorial_generation,d0
        move.w  d7,d1
        bsr     game_preview_dispatch_stage_eligible
        tst.l   d0
        beq.s   .ordinary_dispatch
        move.l  #TUTORIAL_BG_SERVE_STAGE_E,d1
        cmp.l   d5,d1
        bhi     .done
        move.l  d1,tutorial_job_cost
        move.w  #1,tutorial_job_budget
        move.w  #1,tutorial_job_stage
        moveq   #8,d0
        bra     .done
.ordinary_dispatch:
        moveq   #8,d0
        lea     game_preview_predictor_routes,a0
        tst.b   (a0,d7.w)
        beq.s   .full
        bsr     tutorial_dispatch_allowance
.fit:   add.l   tutorial_job_cost,d1
        cmp.l   d5,d1
        bhi     .done
        move.l  d1,tutorial_job_cost
        addq.w  #1,tutorial_job_budget
        cmpi.w  #8,d0
        beq     .done
        cmpi.w  #4,tutorial_job_budget
        beq     .done
        ; Every next operation costs at least one chunk. Stop before peeking
        ; or classifying an operation which cannot possibly join this prefix.
        move.l  tutorial_job_cost,d1
        addi.l  #TUTORIAL_BG_CHUNK_E,d1
        cmp.l   d5,d1
        bhi     .done
        addq.w  #1,d6
        tst.w   d4
        bne.s   .next_phase
        andi.w  #HISTORY_RECORDS-1,d6
        ; End the retained prefix before its immutable tail; next call begins
        ; synthetic work instead of interpreting an unwritten retained slot.
        move.w  d7,d0
        lsl.w   #3,d0
        lea     game_preview_stream_cursors,a0
        adda.w  d0,a0
        move.l  (a0),d1
        move.l  4(a0),d0
        moveq   #0,d2
        move.w  tutorial_job_budget,d2
        add.l   d2,d0
        bcc.s   .tail_high
        addq.l  #1,d1
.tail_high:
        cmp.l   game_history_cursor,d1
        bne     .next
        cmp.l   game_history_cursor+4,d0
        beq     .done
        bra     .next
.next_phase:
        andi.w  #3,d6
        bra     .next
.prime: move.l  #TUTORIAL_BG_CHUNK_E,d1
        bra.s   .single
.flight:move.l  #TUTORIAL_BG_PHYSICS_E,d1
        bra.s   .single
.cold:  move.l  #TUTORIAL_BG_FULL_E,d1
.single:cmp.l   d5,d1
        bhi     .done
        move.l  d1,tutorial_job_cost
        move.w  #1,tutorial_job_budget
.done:  rts

; Admission includes complete return/progress and the next root mandatory path.
; A producer targets the current unconsumed opportunity or the next field.
; Pure simulation has no producer cutoff; it still cannot hide a whole visible
; interval from latch rearming, nor delay nominal input/transport service.
tutorial_job_admitted:
        move.l  tutorial_job_cost,d5
        addi.l  #TUTORIAL_BG_SERVICE_E+TUTORIAL_BG_MARGIN_E,d5
        move.l  simulation_interval,d0
        sub.l   simulation_phase,d0
        bcs     .no
        cmp.l   d5,d0
        bcs     .no
        cmpi.w  #TUTORIAL_JOB_PRODUCER,tutorial_job_kind
        beq.s   .producer
        cmpi.w  #TUTORIAL_JOB_FOOTER_COMMIT,tutorial_job_kind
        beq     .footer_window
        tst.b   blank_seen
        beq.s   .timer
        bsr     read_presentation_line
        cmpi.w  #253,d0
        bcs     .no ; next root pump must observe the visible rearm first
        bra.s   .next_field
.footer_window:
        ; Overlay DMA reads lines236..251. Build in private scratch; copy
        ; only when the complete live512-byte transaction precedes consumption.
        bsr     read_presentation_line
        cmpi.w  #236,d0
        bcs.s   .footer_current
        cmpi.w  #251,d0
        bls     .no
        move.w  presentation_last_line,d1
        sub.w   d0,d1
        addi.w  #235,d1
        bra.s   .beam_fit
.footer_current:
        move.w  #235,d1
        sub.w   d0,d1
        bra.s   .beam_fit
.producer:
        bsr     read_presentation_line
        cmpi.w  #253,d0
        bcs.s   .current_field
        tst.b   blank_seen
        beq     .no ; allow IRQ/root first-window ownership before producing
.next_field:
        move.w  presentation_last_line,d1
        sub.w   d0,d1
        addi.w  #252,d1
        bra.s   .beam_fit
.current_field:
        move.w  #252,d1
        sub.w   d0,d1
.beam_fit:
        mulu.w  #TUTORIAL_BG_LINE_CCK,d1
        move.l  d5,d2
        mulu.w  #5,d2
        cmp.l   d2,d1
        bcs.s   .no
.timer: bsr     account_sim_timer
        move.l  simulation_interval,d0
        sub.l   simulation_phase,d0
        bcs.s   .no
        cmp.l   d5,d0
        bcs.s   .no
        move.l  simulation_interval_whole,d0
        cmpi.l  #TUTORIAL_BG_CALLBACK_E+TUTORIAL_BG_ENTRY_E+TUTORIAL_BG_COMPLETION_MARGIN_E,d0
        bcs.s   .no
        moveq   #1,d0
        rts
.no:    moveq   #0,d0
        rts

; Retained observer identity; coherent admission no longer uses this old switch.
        even
tutorial_background_physics_enabled: dc.w 1

; The narrower elapsed hypothesis belongs to the audited one-root domain,
; not to every projected dispatch. Other paths retain a full-body hypothesis.
; All inputs are read from the branch's current state; allowed preparation
; bodies do not mutate these phase/geometry/lifecycle fields.
tutorial_dispatch_allowance:
        movem.l d0/d2-d7/a0-a4,-(sp)
        cmpi.w  #GAME_PLAYING,game_lifecycle-game_core_state(a3)
        bne     .no
        tst.b   game_core_command-game_core_state(a3)
        bne     .no
        tst.b   game_restart_context-game_core_state(a3)
        bne     .no
        tst.b   game_entropy_policy-game_core_state(a3)
        bne     .no
        ; Only projected incoming motion/contact. Neither arbitrary original
        ; dispatch, outgoing ball nor endpoint query is admitted here.
        lea     game_play_state-game_core_state(a3),a4
        move.b  game_mode-game_core_state(a3),d1
        andi.b  #$e4,d1
        bne     .no
        tst.b   game_score_initialized-game_core_state(a3)
        beq     .no
        cmpi.b  #S_ACTIVE,game_score_state+S_STAGE-game_core_state(a3)
        bne     .no
        moveq   #0,d2
        move.w  game_preview_end,d2
        cmpi.w  #1,d2
        bhi     .no
        moveq   #1,d1
        lsl.b   d2,d1
        cmp.b   game_score_state+S_AI-game_core_state(a3),d1
        bne     .no
        ori.b   #$40,d1
        cmp.b   game_score_flags-game_core_state(a3),d1
        bne     .no
        move.b  game_mode-game_core_state(a3),d1
        lsr.b   #4,d1
        andi.w  #1,d1
        cmp.w   d2,d1
        bne     .no
        cmp.b   game_lower_owner-game_core_state(a3),d2
        bne     .no
        move.w  d2,d1
        eori.w  #1,d1
        cmp.b   game_upper_owner-game_core_state(a3),d1
        bne     .no
        lsl.b   #6,d1
        move.b  G_CONTACT(a4),d3
        andi.b  #$40,d3
        cmp.b   d1,d3
        bne     .no
        move.b  G_CONTACT(a4),d1
        andi.b  #$8d,d1
        bne     .no
        move.b  G_FLIGHT(a4),d1
        andi.b  #$c0,d1
        cmpi.b  #$40,d1
        bne     .no
        ; Nonoverlapping receiving court intervals prove at most one contact
        ; derive/root call before movement/ball advancement in this dispatch.
        cmpi.b  #98,G_LOWER+P_Y(a4)
        bcs     .no
        cmpi.b  #154,G_LOWER+P_Y(a4)
        bcc     .no
        cmpi.b  #7,G_UPPER+P_Y(a4)
        bcs     .no
        cmpi.b  #63,G_UPPER+P_Y(a4)
        bcc     .no
        move.b  G_LOWER+P_PHASE(a4),d1
        or.b    G_UPPER+P_PHASE(a4),d1
        move.b  d1,d2
        andi.b  #$c0,d1
        bne     .no
        andi.b  #$20,d2
        beq.s   .counts
        cmpi.b  #$10,G_SERVE_CLOCK(a4)
        bls     .no
.counts:
        move.l  #TUTORIAL_BG_PHYSICS_E,d1
        bra.s   .returned
.no:    move.l  #TUTORIAL_BG_FULL_E,d1
.returned:
        movem.l (sp)+,d0/d2-d7/a0-a4
        rts

; Only root admission calls this live overlay transaction. The staged caption
; has the same bytes/font/layout as before; DMA never observes its construction.
tutorial_footer_commit:
        move.l  tutorial_footer_generation,d0
        cmp.l   tutorial_generation,d0
        bne.s   .discard
        ; Raster bytes remain private. The next complete scene copies them only
        ; into its free canvas's footer and atomically binds that pointer.
        cmp.l   tutorial_caption_generation,d0
        bne.s   .changed
        move.l  tutorial_footer_first,d1
        cmp.l   tutorial_caption_first,d1
        bne.s   .changed
        move.l  tutorial_footer_second,d1
        cmp.l   tutorial_caption_second,d1
        beq.s   .discard
.changed:
        move.l  d0,tutorial_caption_generation
        move.l  tutorial_footer_first,tutorial_caption_first
        move.l  tutorial_footer_second,tutorial_caption_second
        st      tutorial_placement_dirty
.discard:
        clr.w   tutorial_footer_ready
        rts
