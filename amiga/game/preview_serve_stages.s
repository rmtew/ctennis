; Root-only continuation of synthetic original operation8. No suspended stack.
; The entry-selected playing lane survives lifecycle changes inside scoring.
; Public logical APIs remain synchronous; they finish any pending continuation.
game_preview_serve_code_begin:

; D0 generation, D1 variant. Read-only eligibility; preserve all other registers.
; Existing branch ownership is generation-bound and is not reclassified mid-op.
game_preview_dispatch_stage_eligible:
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
        bsr     game_preview_selection_valid
        tst.l   d0
        beq     .no
        cmpi.w  #3,game_preview_kind
        bne     .no
        move.w  d1,d7
        move.w  d7,d6
        add.w   d6,d6
        lea     game_preview_dispatch_stages,a0
        tst.w   (a0,d6.w)
        beq.s   .initial
        cmpi.w  #10,(a0,d6.w)
        bcc     .no
        add.w   d6,d6
        lea     game_preview_dispatch_generations,a0
        move.l  game_preview_generation,d0
        cmp.l   (a0,d6.w),d0
        bne     .no
        bra.s   .yes
.initial:
        cmpi.w  #PREVIEW_PRIME,game_preview_status
        bcs     .no
        cmpi.w  #PREVIEW_RELEASED,game_preview_status
        bhi     .no
        btst    d7,game_preview_primed_mask+1
        beq     .no
        lea     game_preview_launches,a0
        tst.b   (a0,d7.w)
        bne     .no
        lea     game_preview_outcomes,a0
        tst.w   (a0,d6.w)
        bne     .no
        lea     game_preview_synthetic_phases,a0
        cmpi.w  #3,(a0,d6.w)
        bne     .no
        lsl.w   #2,d6
        lea     game_preview_stream_cursors,a0
        adda.w  d6,a0
        lea     game_history_cursor,a1
        bsr     game_preview_compare_cursor
        tst.l   d0
        bne     .no
        bsr     game_preview_context_address
        cmpi.w  #GAME_PLAYING,game_lifecycle-game_core_state(a0)
        bne     .no
        tst.b   game_core_command-game_core_state(a0)
        bne     .no
.yes:   moveq   #1,d0
        bra.s   .done
.no:    moveq   #0,d0
.done:  movem.l (sp)+,d1-d7/a0-a6
        rts

; D0 generation, D1 variant. One complete physical stage. D0=progress/rejected,
; D1=completed logical envelopes (0 or1). No partial path/launch/outcome is public.
game_preview_dispatch_stage:
        bsr     game_preview_dispatch_stage_eligible
        tst.l   d0
        beq.s   .rejected
        movem.l d2-d7/a2-a6,-(sp)
        move.b  d1,game_preview_variant
        move.w  #1,game_preview_explicit
        move.w  d1,game_preview_requested_variant
        clr.w   game_preview_dispatch_finished
        move.w  d1,d7
        bsr     game_preview_context_address
        move.l  a0,a5
        move.b  #2,game_preview_active
        bsr     game_preview_dispatch_stage_one
        tst.l   d0
        beq.s   .release
        move.w  #1,game_preview_dispatch_finished
        st      game_preview_dispatch_commit
        bsr     game_preview_continue_one
.release:
        bsr     game_preview_release_current
        clr.w   game_preview_explicit
        movem.l (sp)+,d2-d7/a2-a6
        moveq   #0,d1
        move.w  game_preview_dispatch_finished,d1
        moveq   #1,d0
        rts
.rejected:
        moveq   #0,d1
        rts

; A5 private branch, active2. Resume full register/CCR and metadata ownership.
; D0=1 only after final scene service. Caller commits the logical envelope.
game_preview_dispatch_stage_one:
        move.w  sr,-(sp)
        movem.l d0-d7/a0-a6,-(sp)
        moveq   #0,d7
        move.b  game_preview_variant,d7
        move.w  d7,d6
        add.w   d6,d6
        lea     game_preview_dispatch_stages,a0
        move.w  (a0,d6.w),d5
        move.w  d7,d0
        lsl.w   #6,d0
        lea     game_preview_dispatch_registers,a6
        adda.w  d0,a6
        tst.w   d5
        bne.s   .restore_history
        move.l  sp,a0
        move.l  a6,a1
        moveq   #14,d0
.initial_registers:
        move.l  (a0)+,(a1)+
        dbra    d0,.initial_registers
        move.w  (a0),(a1)
        lea     game_play_state-game_core_state(a5),a0
        move.w  game_preview_end,d0
        mulu.w  #10,d0
        lea     game_preview_dispatch_origin_phases,a1
        move.b  (a0,d0.w),(a1,d7.w)
        lsl.w   #2,d7
        lea     game_preview_dispatch_generations,a0
        move.l  game_preview_generation,(a0,d7.w)
        bra.s   .enter
.restore_history:
        move.w  d7,d0
        mulu.w  #game_history_state_end-game_history_state,d0
        lea     game_preview_dispatch_history,a1
        adda.w  d0,a1
        lea     game_history_state,a0
        bsr     game_preview_copy_history
.enter:
        lea     62(sp),sp
        add.w   d5,d5
        add.w   d5,d5
        lea     game_preview_dispatch_stage_bodies,a0
        move.l  (a0,d5.w),a0
        jmp     (a0)
game_preview_dispatch_call_0:
        move.w  60(a6),ccr
        movem.l (a6),d0-d7/a0-a6
        bsr     game_scene_update_fields
        bra     game_preview_dispatch_stage_returned
game_preview_dispatch_call_1:
        move.w  60(a6),ccr
        movem.l (a6),d0-d7/a0-a6
        bsr     input_update
        bra     game_preview_dispatch_stage_returned
game_preview_dispatch_call_2:
        move.w  60(a6),ccr
        movem.l (a6),d0-d7/a0-a6
        bsr     game_score_tick
        bra     game_preview_dispatch_stage_returned
game_preview_dispatch_call_3:
        move.w  60(a6),ccr
        movem.l (a6),d0-d7/a0-a6
        bsr     game_play_tick
        bra     game_preview_dispatch_stage_returned
game_preview_dispatch_call_4:
        move.w  60(a6),ccr
        movem.l (a6),d0-d7/a0-a6
        bsr     game_scene_finish_tick
        bra     game_preview_dispatch_stage_returned
game_preview_dispatch_call_5:
        move.w  60(a6),ccr
        movem.l (a6),d0-d7/a0-a6
        bsr     game_observe_pre_tail
        bra     game_preview_dispatch_stage_returned
game_preview_dispatch_call_6:
        move.w  60(a6),ccr
        movem.l (a6),d0-d7/a0-a6
        bsr     game_advance_clocks
        bra     game_preview_dispatch_stage_returned
game_preview_dispatch_call_7:
        move.w  60(a6),ccr
        movem.l (a6),d0-d7/a0-a6
        bsr     game_audio_tick
        bra     game_preview_dispatch_stage_returned
game_preview_dispatch_call_8:
        move.w  60(a6),ccr
        movem.l (a6),d0-d7/a0-a6
        bsr     game_apply_sound
        bra     game_preview_dispatch_stage_returned
game_preview_dispatch_call_9:
        move.w  60(a6),ccr
        movem.l (a6),d0-d7/a0-a6
        bsr     game_scene_service
        bra     game_preview_dispatch_stage_returned
game_preview_dispatch_stage_returned:
        move.w  sr,-(sp)
        movem.l d0-d7/a0-a6,-(sp)
        moveq   #0,d7
        move.b  game_preview_variant,d7
        move.w  d7,d0
        lsl.w   #6,d0
        lea     game_preview_dispatch_registers,a1
        adda.w  d0,a1
        move.l  sp,a0
        moveq   #14,d0
.save_registers:
        move.l  (a0)+,(a1)+
        dbra    d0,.save_registers
        move.w  (a0),(a1)
        move.w  d7,d0
        mulu.w  #game_history_state_end-game_history_state,d0
        lea     game_preview_dispatch_history,a0
        adda.w  d0,a0
        lea     game_history_state,a1
        bsr     game_preview_copy_history
        lea     62(sp),sp
        add.w   d7,d7
        lea     game_preview_dispatch_stages,a0
        addq.w  #1,(a0,d7.w)
        cmpi.w  #10,(a0,d7.w)
        beq.s   .complete
        moveq   #0,d0
        rts
.complete:
        clr.w   (a0,d7.w)
        lsr.w   #1,d7
        lea     game_preview_dispatch_launches,a0
        lea     game_preview_launches,a1
        move.b  (a0,d7.w),(a1,d7.w)
        lea     game_preview_dispatch_interceptions,a0
        lea     game_preview_interceptions,a1
        move.b  (a0,d7.w),(a1,d7.w)
        moveq   #1,d0
        rts

game_preview_dispatch_stage_bodies:
        dc.l game_preview_dispatch_call_0
        dc.l game_preview_dispatch_call_1
        dc.l game_preview_dispatch_call_2
        dc.l game_preview_dispatch_call_3
        dc.l game_preview_dispatch_call_4
        dc.l game_preview_dispatch_call_5
        dc.l game_preview_dispatch_call_6
        dc.l game_preview_dispatch_call_7
        dc.l game_preview_dispatch_call_8
        dc.l game_preview_dispatch_call_9
game_preview_serve_code_end:
