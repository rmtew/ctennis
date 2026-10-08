; Test-only callback mailbox. No gameplay state or expected output is supplied.
        section code,code
preview_native_hook:
        move.w  sr,-(sp)
        movem.l d0-d7/a0-a6,-(sp)
preview_native_before:
        moveq   #0,d7
        move.w  preview_native_command,d7
        beq     preview_native_after
        cmpi.w  #7,d7
        bhi     preview_native_after
        subq.w  #1,d7
        lsl.w   #2,d7
        lea     preview_native_targets,a0
        move.l  (a0,d7.w),a0
        movem.l preview_native_arguments,d0-d5
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
        dc.l game_history_freeze,game_history_seek,game_preview_request
        dc.l game_preview_step,game_preview_result,game_preview_cancel
        dc.l game_history_resume_latest
        section preview_fixture,bss
preview_native_mailbox:
preview_native_command: ds.w 1
preview_native_arguments: ds.l 6
preview_native_results: ds.l 6
preview_native_mailbox_end:
