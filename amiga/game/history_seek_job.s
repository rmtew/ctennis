; Paused navigation over complete logical boundaries. No presentation clock.
; The native caller admits zero/one body using its real remaining deadline.
SEEK_JOB_PENDING equ 1
SEEK_JOB_READY equ 2
SEEK_JOB_CANCELED equ 3

; D0 expected generation, D1/D2 target high/low. Validation failure is atomic.
game_history_seek_begin:
        cmp.l   game_history_seek_generation,d0
        bne     .invalid
        cmpi.l  #$fffffffe,d0
        bcc     .invalid
        cmpi.b  #2,game_history_mode
        bne     .invalid
        tst.b   game_history_replaying
        bne     .invalid
        tst.b   game_preview_active
        bne     .invalid
        movem.l d2-d7/a2-a6,-(sp)
        move.l  d1,d0
        move.l  d2,d1
        suba.w  #game_history_state_end-game_history_state,sp
        lea     game_history_state,a0
        move.l  sp,a1
        bsr     game_history_seek_copy_metadata
        bsr     game_history_seek_prepare
        tst.l   d0
        beq     .rollback
        ; All envelope/operation validation precedes replacement of an old job.
        move.l  game_history_target,game_history_seek_target
        move.l  game_history_target+4,game_history_seek_target+4
        move.l  game_history_origin,game_history_seek_cursor
        move.l  game_history_origin+4,game_history_seek_cursor+4
        move.w  game_history_replay_count,game_history_seek_remaining
        lea     game_history_seek_selected,a0
        lea     game_core_state,a1
        bsr     game_history_copy_state
        lea     game_history_seek_working,a0
        move.l  game_history_selected,a1
        adda.w  #12,a1
        bsr     game_history_copy_state
        move.l  sp,a0
        lea     game_history_seek_history,a1
        bsr     game_history_seek_copy_metadata
        move.l  sp,a0
        lea     game_history_state,a1
        bsr     game_history_seek_copy_metadata
        adda.w  #game_history_state_end-game_history_state,sp
        addq.l  #1,game_history_seek_generation
        move.w  #SEEK_JOB_PENDING,game_history_seek_status
        tst.w   game_history_seek_remaining
        bne.s   .pending
        move.w  #SEEK_JOB_READY,game_history_seek_status
.pending:
        clr.b   game_history_seek_active
        bsr     game_preview_invalidate
        movem.l (sp)+,d2-d7/a2-a6
        moveq   #1,d0
        rts
.rollback:
        move.l  sp,a0
        lea     game_history_state,a1
        bsr     game_history_seek_copy_metadata
        adda.w  #game_history_state_end-game_history_state,sp
        movem.l (sp)+,d2-d7/a2-a6
.invalid:
        moveq   #0,d0
        rts

; D0 generation, D1 admission0/1. Admission0 is a successful no-work yield.
; At most one actual body. READY does not publish: commit is separately bounded.
game_history_seek_step:
        cmp.l   game_history_seek_generation,d0
        bne     .invalid
        cmpi.w  #1,d1
        bhi     .invalid
        cmpi.w  #SEEK_JOB_PENDING,game_history_seek_status
        beq.s   .identity
        cmpi.w  #SEEK_JOB_READY,game_history_seek_status
        bne     .invalid
.identity:
        move.w  d1,-(sp)
        bsr     game_history_seek_identity
        move.w  (sp)+,d1
        tst.l   d0
        beq     .invalid
        tst.w   d1
        beq     .valid
        cmpi.w  #SEEK_JOB_READY,game_history_seek_status
        beq     .valid
        movem.l d2-d7/a2-a6,-(sp)
        ; Revalidate the next record before changing either working image.
        move.l  game_history_seek_cursor+4,d0
        andi.w  #HISTORY_RECORDS-1,d0
        mulu.w  #HISTORY_RECORD_BYTES,d0
        move.l  game_history_store,a5
        adda.l  d0,a5
        move.w  (a5),d0
        beq     .invalid_saved
        cmpi.w  #9,d0
        bhi     .invalid_saved
        cmpi.w  #2,d0
        bne.s   .record_valid
        cmpi.w  #1,6(a5)
        bhi     .invalid_saved
.record_valid:
        move.b  #1,game_history_seek_active
        lea     game_history_seek_working,a1
        lea     game_core_state,a0
        bsr     game_history_copy_state
        move.l  game_history_seek_cursor+4,game_history_replay_low
        st      game_history_replaying
        moveq   #0,d6
        move.w  (a5)+,d6
        subq.w  #1,d6
        lsl.w   #2,d6
        lea     game_history_operations,a1
        move.l  (a1,d6.w),a1
        move.w  (a5)+,d0
        move.w  (a5)+,d1
        move.w  (a5)+,d2
        move.w  (a5)+,d3
        move.w  (a5)+,d4
        move.w  (a5)+,d5
        jsr     (a1)
        lea     game_history_seek_working,a0
        lea     game_core_state,a1
        bsr     game_history_copy_state
        lea     game_core_state,a0
        lea     game_history_seek_selected,a1
        bsr     game_history_copy_state
        lea     game_history_seek_history,a0
        lea     game_history_state,a1
        bsr     game_history_seek_copy_metadata
        clr.b   game_history_seek_active
        addq.l  #1,game_history_seek_cursor+4
        bcc.s   .cursor_ok
        addq.l  #1,game_history_seek_cursor
.cursor_ok:
        subq.w  #1,game_history_seek_remaining
        bne.s   .yield
        move.w  #SEEK_JOB_READY,game_history_seek_status
.yield:
        movem.l (sp)+,d2-d7/a2-a6
.valid:
        moveq   #1,d0
        rts
.invalid_saved:
        movem.l (sp)+,d2-d7/a2-a6
.invalid:
        moveq   #0,d0
        rts

; Publish only a complete target after identity checks. No bodies are executed.
game_history_seek_commit:
        cmp.l   game_history_seek_generation,d0
        bne.s   .invalid
        cmpi.w  #SEEK_JOB_READY,game_history_seek_status
        bne.s   .invalid
        bsr     game_history_seek_identity
        tst.l   d0
        beq.s   .invalid
        movem.l d2-d7/a2-a6,-(sp)
        lea     game_history_seek_working,a1
        lea     game_core_state,a0
        bsr     game_history_copy_state
        move.l  game_history_seek_target,game_history_position
        move.l  game_history_seek_target+4,game_history_position+4
        bsr     game_preview_invalidate
        bsr     game_history_seek_job_invalidate
        movem.l (sp)+,d2-d7/a2-a6
        moveq   #1,d0
        rts
.invalid:
        moveq   #0,d0
        rts

; Cancellation never restores an old selection over a newer public moment.
game_history_seek_cancel:
        cmp.l   game_history_seek_generation,d0
        bne.s   .invalid
        cmpi.w  #SEEK_JOB_PENDING,game_history_seek_status
        beq.s   .cancel
        cmpi.w  #SEEK_JOB_READY,game_history_seek_status
        bne.s   .invalid
.cancel:
        bsr     game_history_seek_job_invalidate
        move.w  #SEEK_JOB_CANCELED,game_history_seek_status
        moveq   #1,d0
        rts
.invalid:
        moveq   #0,d0
        rts

game_history_seek_identity:
        cmpi.b  #2,game_history_mode
        bne.s   .invalid
        tst.b   game_history_replaying
        bne.s   .invalid
        tst.b   game_preview_active
        bne.s   .invalid
        lea     game_core_state,a0
        lea     game_history_seek_selected,a1
        move.w  #GAME_CORE_STATE_SIZE/2-1,d0
.state: cmpm.w  (a0)+,(a1)+
        bne.s   .invalid
        dbra    d0,.state
        lea     game_history_state,a0
        lea     game_history_seek_history,a1
        moveq   #(game_history_state_end-game_history_state)/4-1,d0
.meta:  cmpm.l  (a0)+,(a1)+
        bne.s   .invalid
        dbra    d0,.meta
        moveq   #1,d0
        rts
.invalid:
        moveq   #0,d0
        rts

; Copies metadata only, preserving validation target D0/D1 and scratch D6.
game_history_seek_copy_metadata:
        move.l  d6,-(sp)
        moveq   #(game_history_state_end-game_history_state)/4-1,d6
.copy:  move.l  (a0)+,(a1)+
        dbra    d6,.copy
        move.l  (sp)+,d6
        rts

game_history_seek_job_invalidate:
        cmpi.b  #3,game_preview_active
        beq.s   .done ; existing request-owned synchronous oldest seek only
        clr.w   game_history_seek_status
        clr.b   game_history_seek_active
        cmpi.l  #$ffffffff,game_history_seek_generation
        beq.s   .done
        addq.l  #1,game_history_seek_generation
.done:  rts
