; Exact endpoint readiness is independent of the continuing dense worker.
; Private immutable launch seeds are captured only after complete dispatcher tails.
game_preview_endpoint_code_begin:
game_preview_capture_launch:
        moveq   #0,d7
        move.b  game_preview_variant,d7
        lea     game_preview_launches,a0
        tst.b   (a0,d7.w)
        beq.s   .done
        lea     game_preview_launch_saved,a0
        tst.b   (a0,d7.w)
        bne.s   .done
        st      (a0,d7.w)
        move.w  d7,d0
        mulu.w  #GAME_CORE_STATE_SIZE,d0
        lea     game_preview_launch_states,a0
        adda.l  d0,a0
        move.l  a5,a1
        bsr     game_history_copy_state
.done:  rts

; D0 generation/D1 variant0..1. D0=1 eligible,0 otherwise; all others preserved.
; No writes on rejection, including shared scratch. Four actual outgoing phases
; avoid paying a query on very short flights; not a universal break-even bound.
game_preview_endpoint_pending:
        movem.l d1-d7/a0-a6,-(sp)
        cmp.l   game_preview_generation,d0
        bne     .no
        cmpi.l  #$ffffffff,d0
        beq     .no
        cmpi.w  #1,d1
        bhi     .no
        tst.b   game_preview_active
        bne     .no
        cmpi.w  #SEEK_JOB_PENDING,game_history_seek_status
        beq     .no
        cmpi.w  #SEEK_JOB_READY,game_history_seek_status
        beq     .no
        cmpi.w  #PREVIEW_PRIME,game_preview_status
        bcs     .no
        cmpi.w  #PREVIEW_RELEASED,game_preview_status
        bhi     .no
        move.w  d1,d7
        btst    d7,game_preview_primed_mask+1
        beq     .no
        move.w  d7,d4
        mulu.w  #48,d4
        lea     game_preview_query_workspaces,a0
        cmpi.w  #2,36(a0,d4.w)
        bhi     .no
        bsr     game_preview_selection_valid
        tst.l   d0
        beq     .no
        lea     game_preview_launch_saved,a0
        tst.b   (a0,d7.w)
        beq     .no
        lea     game_preview_endpoint_attempted,a0
        tst.b   (a0,d7.w)
        bne     .no
        lea     game_preview_endpoint_ready,a0
        tst.b   (a0,d7.w)
        bne     .no
        add.w   d7,d7
        lea     game_preview_outcomes,a0
        tst.w   (a0,d7.w)
        bne     .no
        lea     game_preview_flight_phases,a0
        cmpi.w  #4,(a0,d7.w)
        bcs     .no
        cmpi.w  #PREVIEW_SEGMENT_PHASES,(a0,d7.w)
        bcc     .no
        moveq   #1,d0
        bra.s   .done
.no:    moveq   #0,d0
.done:  movem.l (sp)+,d1-d7/a0-a6
        rts

; One separately admitted bounded job. No dense state/count/status changes,
; no original ball fallback and no retries. Accepted data belongs to generation.
game_preview_endpoint_try:
        bsr     game_preview_endpoint_pending
        tst.l   d0
        beq     .done
        movem.l d1-d7/a0-a6,-(sp)
        move.w  d1,d7
        lea     game_preview_endpoint_attempted,a0
        st      (a0,d7.w)
        move.w  d7,d0
        mulu.w  #GAME_CORE_STATE_SIZE,d0
        lea     game_preview_launch_states,a1
        adda.l  d0,a1
        lea     game_preview_endpoint_scratch,a0
        bsr     game_history_copy_state
        ; copy_state clobbers D7. The saved variant remains in D1.
        move.w  d1,d7
        move.w  d7,d6
        add.w   d6,d6
        lea     game_preview_endpoint_scratch,a5
        bsr     landing_try_fast
        bsr     game_preview_endpoint_store
.returned:
        movem.l (sp)+,d1-d7/a0-a6
        moveq   #1,d0
.done:  rts

; D0 generation/D1 variant. Execute one complete private query stage.
; D0=1 progress (pending or terminal),0 rejected/stale/no eligible work.
; Partial candidates never update attempted, reason, ready or compatibility scratch.
game_preview_endpoint_step:
        bsr     game_preview_endpoint_pending
        tst.l   d0
        beq     .done
        movem.l d1-d7/a0-a6,-(sp)
        move.w  d1,d7
        move.w  d7,d0
        mulu.w  #GAME_CORE_STATE_SIZE,d0
        lea     game_preview_query_states,a5
        adda.l  d0,a5
        move.w  d7,d0
        mulu.w  #48,d0
        lea     game_preview_query_workspaces,a3
        adda.w  d0,a3
        tst.w   36(a3)
        bne.s   .resume
        move.w  d7,d0
        mulu.w  #GAME_CORE_STATE_SIZE,d0
        lea     game_preview_launch_states,a1
        adda.l  d0,a1
        move.l  a5,a0
        bsr     game_history_copy_state
        bsr     landing_try_prepare
        bra.s   .returned_stage
.resume:
        bsr     landing_try_step
.returned_stage:
        cmpi.w  #4,d0
        beq.s   .pending
        ; copy_state preserves D1/D2 but clobbers D7; reload the caller variant.
        lea     game_preview_endpoint_scratch,a0
        move.l  a5,a1
        bsr     game_history_copy_state
        move.l  (sp),d7
        bsr     game_preview_endpoint_store
.pending:
        movem.l (sp)+,d1-d7/a0-a6
        moveq   #1,d0
.done:  rts

; Publish only a terminal original helper result. A5=complete private state,
; D1=terminal phase/D2=reason/D7=variant. Shared by both query entry points.
game_preview_endpoint_store:
        lea     game_preview_endpoint_attempted,a0
        st      (a0,d7.w)
        move.w  d7,d6
        add.w   d6,d6
        lea     game_preview_endpoint_reasons,a0
        move.w  d2,(a0,d6.w)
        tst.w   d2
        bne.s   .done
        ; Terminal must be beyond the unchanged dense continuation.
        lea     game_preview_flight_phases,a0
        cmp.w   (a0,d6.w),d1
        bhi.s   .consistent
        ; Defensive seed/worker inconsistency is a distinct discarded query.
        lea     game_preview_endpoint_reasons,a0
        move.w  #15,(a0,d6.w)
        bra.s   .done
.consistent:
        lea     game_preview_endpoint_phases,a0
        move.w  d1,(a0,d6.w)
        moveq   #PREVIEW_LANDING,d0
        move.b  game_contact-game_core_state(a5),d1
        andi.b  #$88,d1
        beq.s   .landing
        moveq   #PREVIEW_OUT,d0
.landing:
        lea     game_preview_endpoint_outcomes,a0
        move.w  d0,(a0,d6.w)
        move.w  d7,d0
        lsl.w   #3,d0
        lea     game_preview_endpoints,a0
        adda.w  d0,a0
        bsr     game_preview_write_point
        lea     game_preview_endpoint_ready,a0
        st      (a0,d7.w)
.done:  rts

; Sequential worker stopped: publish its actual point, including rejected domains.
; D0 outcome, D6 word index/D7 variant. Preserve finish_variant's owner registers.
game_preview_endpoint_terminal:
        cmpi.w  #PREVIEW_INTERCEPTION,d0
        bhi.s   .done
        lea     game_preview_launches,a0
        tst.b   (a0,d7.w)
        beq.s   .done
        lea     game_preview_endpoint_outcomes,a0
        move.w  d0,(a0,d6.w)
        lea     game_preview_flight_phases,a0
        move.w  (a0,d6.w),d1
        lea     game_preview_endpoint_phases,a0
        move.w  d1,(a0,d6.w)
        move.w  d7,d0
        lsl.w   #3,d0
        lea     game_preview_endpoints,a0
        adda.w  d0,a0
        bsr     game_preview_write_point
        lea     game_preview_endpoint_ready,a0
        st      (a0,d7.w)
.done:  rts

game_preview_endpoint_code_end:
