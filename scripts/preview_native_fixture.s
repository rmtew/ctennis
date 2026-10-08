; Test-only callback mailbox. No gameplay state or expected output is supplied.
        section code,code
preview_native_hook:
        move.w  sr,-(sp)
        movem.l d0-d7/a0-a6,-(sp)
preview_native_before:
        moveq   #0,d7
        move.w  preview_native_command,d7
        beq     preview_native_after
        cmpi.w  #10,d7
        bhi     preview_native_after
        cmpi.w  #8,d7
        bne     .dispatch
        bsr     preview_native_admit_seek
.dispatch:
        subq.w  #1,d7
        lsl.w   #2,d7
        lea     preview_native_targets,a0
        move.l  (a0,d7.w),a0
        movem.l preview_native_arguments,d0-d5
        cmpi.w  #28,d7
        bne     preview_native_call
        move.l  preview_native_timer_admitted,d1
preview_native_call:
        jsr     (a0)
preview_native_after:
        movem.l d0-d5,preview_native_results
        clr.w   preview_native_command
preview_native_return:
        movem.l (sp)+,d0-d7/a0-a6
        move.w  (sp)+,sr
        rts
preview_native_targets:
        dc.l game_history_freeze,game_history_seek_begin,game_preview_request
        dc.l game_preview_step,game_preview_result,game_preview_cancel
        dc.l game_history_resume_latest
        dc.l game_history_seek_step,game_history_seek_commit,game_history_seek_cancel
; Read-only guest clock admission. 10,000 Eclock ticks is an initial CPU-derived
; reserve estimate; actual callback deadlines (including this read) still gate.
preview_native_admit_seek:
        jsr     read_sim_timer
        move.l  d0,preview_native_timer_current
        move.l  last_timer_count,d1
        move.l  d1,preview_native_timer_last
        sub.l   d0,d1
        move.l  simulation_phase,d2
        move.l  d2,preview_native_timer_phase
        move.l  simulation_interval,d3
        move.l  d3,preview_native_timer_interval
        move.l  preview_native_arguments+4,d4
        move.l  d4,preview_native_timer_requested_work
        clr.l   preview_native_timer_admitted
        clr.l   preview_native_timer_remaining
        move.l  #10000,preview_native_timer_reserve
        sub.l   d2,d3
        bcs     .done
        sub.l   d1,d3
        bcs     .done
        move.l  d3,preview_native_timer_remaining
        cmpi.l  #10000,d3
        bcs     .done
        cmpi.l  #1,d4
        bne     .done
        move.l  #1,preview_native_timer_admitted
.done:
        rts
        section preview_fixture,bss
preview_native_mailbox:
preview_native_command: ds.w 1
preview_native_arguments: ds.l 6
preview_native_results: ds.l 6
preview_native_timer_current: ds.l 1
preview_native_timer_last: ds.l 1
preview_native_timer_phase: ds.l 1
preview_native_timer_interval: ds.l 1
preview_native_timer_remaining: ds.l 1
preview_native_timer_reserve: ds.l 1
preview_native_timer_admitted: ds.l 1
preview_native_timer_requested_work: ds.l 1
preview_native_mailbox_end:
