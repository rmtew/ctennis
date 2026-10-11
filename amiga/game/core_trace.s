; Public logical boundaries. History and optional trace preserve caller context.
game_core_init:
        movem.l a5,-(sp)
        move.w  sr,-(sp)
        cmpi.b  #2,game_history_mode
        bne.s   .history_allowed
        tst.b   game_history_replaying
        bne.s   .history_allowed
        move.w  (sp)+,sr
        move.l  (sp)+,a5
        rts
.history_allowed:
        lea     game_core_state,a5
        movem.l d6-d7/a0-a1,-(sp)
        moveq   #1,d6
        bsr     game_history_before
        movem.l (sp)+,d6-d7/a0-a1
        ifd CORE_TRACE
        move.w  d0,core_trace_arguments+0
        move.w  d1,core_trace_arguments+2
        move.w  d2,core_trace_arguments+4
        move.w  d3,core_trace_arguments+6
        move.w  d4,core_trace_arguments+8
        move.w  d5,core_trace_arguments+10
        move.w  #1,core_trace_marker
        endif
        move.w  (sp)+,sr
        bsr     game_core_init_body
        move.w  sr,-(sp)
        movem.l d0/d7/a0-a1,-(sp)
        bsr     game_history_after
        movem.l (sp)+,d0/d7/a0-a1
        ifd CORE_TRACE
        clr.w   core_trace_marker
        endif
        move.w  (sp)+,sr
        move.l  (sp)+,a5
        rts
game_core_select:
        movem.l a5,-(sp)
        move.w  sr,-(sp)
        cmpi.b  #2,game_history_mode
        bne.s   .history_allowed
        tst.b   game_history_replaying
        bne.s   .history_allowed
        move.w  (sp)+,sr
        move.l  (sp)+,a5
        rts
.history_allowed:
        lea     game_core_state,a5
        movem.l d6-d7/a0-a1,-(sp)
        moveq   #2,d6
        bsr     game_history_before
        movem.l (sp)+,d6-d7/a0-a1
        ifd CORE_TRACE
        move.w  d0,core_trace_arguments+0
        move.w  d1,core_trace_arguments+2
        move.w  d2,core_trace_arguments+4
        move.w  d3,core_trace_arguments+6
        move.w  d4,core_trace_arguments+8
        move.w  d5,core_trace_arguments+10
        move.w  #2,core_trace_marker
        endif
        move.w  (sp)+,sr
        bsr     game_core_select_body
        move.w  sr,-(sp)
        movem.l d0/d7/a0-a1,-(sp)
        bsr     game_history_after
        movem.l (sp)+,d0/d7/a0-a1
        ifd CORE_TRACE
        clr.w   core_trace_marker
        endif
        move.w  (sp)+,sr
        move.l  (sp)+,a5
        rts
game_core_sample_pads:
        movem.l a5,-(sp)
        move.w  sr,-(sp)
        cmpi.b  #2,game_history_mode
        bne.s   .history_allowed
        tst.b   game_history_replaying
        bne.s   .history_allowed
        move.w  (sp)+,sr
        move.l  (sp)+,a5
        rts
.history_allowed:
        lea     game_core_state,a5
        movem.l d6-d7/a0-a1,-(sp)
        moveq   #3,d6
        bsr     game_history_before
        movem.l (sp)+,d6-d7/a0-a1
        ifd CORE_TRACE
        move.w  d0,core_trace_arguments+0
        move.w  d1,core_trace_arguments+2
        move.w  d2,core_trace_arguments+4
        move.w  d3,core_trace_arguments+6
        move.w  d4,core_trace_arguments+8
        move.w  d5,core_trace_arguments+10
        move.w  #3,core_trace_marker
        endif
        move.w  (sp)+,sr
        bsr     game_core_sample_pads_body
        move.w  sr,-(sp)
        movem.l d0/d7/a0-a1,-(sp)
        bsr     game_history_after
        movem.l (sp)+,d0/d7/a0-a1
        ifd CORE_TRACE
        clr.w   core_trace_marker
        endif
        move.w  (sp)+,sr
        move.l  (sp)+,a5
        rts
game_core_sample_result:
        movem.l a5,-(sp)
        move.w  sr,-(sp)
        cmpi.b  #2,game_history_mode
        bne.s   .history_allowed
        tst.b   game_history_replaying
        bne.s   .history_allowed
        move.w  (sp)+,sr
        move.l  (sp)+,a5
        rts
.history_allowed:
        lea     game_core_state,a5
        movem.l d6-d7/a0-a1,-(sp)
        moveq   #4,d6
        bsr     game_history_before
        movem.l (sp)+,d6-d7/a0-a1
        ifd CORE_TRACE
        move.w  d0,core_trace_arguments+0
        move.w  d1,core_trace_arguments+2
        move.w  d2,core_trace_arguments+4
        move.w  d3,core_trace_arguments+6
        move.w  d4,core_trace_arguments+8
        move.w  d5,core_trace_arguments+10
        move.w  #4,core_trace_marker
        endif
        move.w  (sp)+,sr
        bsr     game_core_sample_result_body
        move.w  sr,-(sp)
        movem.l d0/d7/a0-a1,-(sp)
        bsr     game_history_after
        movem.l (sp)+,d0/d7/a0-a1
        ifd CORE_TRACE
        clr.w   core_trace_marker
        endif
        move.w  (sp)+,sr
        move.l  (sp)+,a5
        rts
game_core_clear_inputs:
        movem.l a5,-(sp)
        move.w  sr,-(sp)
        cmpi.b  #2,game_history_mode
        bne.s   .history_allowed
        tst.b   game_history_replaying
        bne.s   .history_allowed
        move.w  (sp)+,sr
        move.l  (sp)+,a5
        rts
.history_allowed:
        lea     game_core_state,a5
        movem.l d6-d7/a0-a1,-(sp)
        moveq   #5,d6
        bsr     game_history_before
        movem.l (sp)+,d6-d7/a0-a1
        ifd CORE_TRACE
        move.w  d0,core_trace_arguments+0
        move.w  d1,core_trace_arguments+2
        move.w  d2,core_trace_arguments+4
        move.w  d3,core_trace_arguments+6
        move.w  d4,core_trace_arguments+8
        move.w  d5,core_trace_arguments+10
        move.w  #5,core_trace_marker
        endif
        move.w  (sp)+,sr
        bsr     game_core_clear_inputs_body
        move.w  sr,-(sp)
        movem.l d0/d7/a0-a1,-(sp)
        bsr     game_history_after
        movem.l (sp)+,d0/d7/a0-a1
        ifd CORE_TRACE
        clr.w   core_trace_marker
        endif
        move.w  (sp)+,sr
        move.l  (sp)+,a5
        rts
game_core_return_title:
        movem.l a5,-(sp)
        move.w  sr,-(sp)
        cmpi.b  #2,game_history_mode
        bne.s   .history_allowed
        tst.b   game_history_replaying
        bne.s   .history_allowed
        move.w  (sp)+,sr
        move.l  (sp)+,a5
        rts
.history_allowed:
        lea     game_core_state,a5
        movem.l d6-d7/a0-a1,-(sp)
        moveq   #6,d6
        bsr     game_history_before
        movem.l (sp)+,d6-d7/a0-a1
        ifd CORE_TRACE
        move.w  d0,core_trace_arguments+0
        move.w  d1,core_trace_arguments+2
        move.w  d2,core_trace_arguments+4
        move.w  d3,core_trace_arguments+6
        move.w  d4,core_trace_arguments+8
        move.w  d5,core_trace_arguments+10
        move.w  #6,core_trace_marker
        endif
        move.w  (sp)+,sr
        bsr     game_core_return_title_body
        move.w  sr,-(sp)
        movem.l d0/d7/a0-a1,-(sp)
        bsr     game_history_after
        movem.l (sp)+,d0/d7/a0-a1
        ifd CORE_TRACE
        clr.w   core_trace_marker
        endif
        move.w  (sp)+,sr
        move.l  (sp)+,a5
        rts
game_round_poll:
        movem.l a5,-(sp)
        move.w  sr,-(sp)
        cmpi.b  #2,game_history_mode
        bne.s   .history_allowed
        tst.b   game_history_replaying
        bne.s   .history_allowed
        move.w  (sp)+,sr
        move.l  (sp)+,a5
        rts
.history_allowed:
        lea     game_core_state,a5
        movem.l d6-d7/a0-a1,-(sp)
        moveq   #7,d6
        bsr     game_history_before
        movem.l (sp)+,d6-d7/a0-a1
        ifd CORE_TRACE
        move.w  d0,core_trace_arguments+0
        move.w  d1,core_trace_arguments+2
        move.w  d2,core_trace_arguments+4
        move.w  d3,core_trace_arguments+6
        move.w  d4,core_trace_arguments+8
        move.w  d5,core_trace_arguments+10
        move.w  #7,core_trace_marker
        endif
        move.w  (sp)+,sr
        bsr     game_round_poll_body
        move.w  sr,-(sp)
        movem.l d0/d7/a0-a1,-(sp)
        bsr     game_history_after
        movem.l (sp)+,d0/d7/a0-a1
        ifd CORE_TRACE
        clr.w   core_trace_marker
        endif
        move.w  (sp)+,sr
        move.l  (sp)+,a5
        rts
game_tick_dispatch:
        movem.l a5,-(sp)
        move.w  sr,-(sp)
        cmpi.b  #2,game_history_mode
        bne.s   .history_allowed
        tst.b   game_history_replaying
        bne.s   .history_allowed
        move.w  (sp)+,sr
        move.l  (sp)+,a5
        rts
.history_allowed:
        lea     game_core_state,a5
        movem.l d6-d7/a0-a1,-(sp)
        moveq   #8,d6
        bsr     game_history_before
        movem.l (sp)+,d6-d7/a0-a1
        ifd CORE_TRACE
        move.w  d0,core_trace_arguments+0
        move.w  d1,core_trace_arguments+2
        move.w  d2,core_trace_arguments+4
        move.w  d3,core_trace_arguments+6
        move.w  d4,core_trace_arguments+8
        move.w  d5,core_trace_arguments+10
        move.w  #8,core_trace_marker
        endif
        move.w  (sp)+,sr
        bsr     game_tick_dispatch_body
        move.w  sr,-(sp)
        movem.l d0/d7/a0-a1,-(sp)
        bsr     game_history_after
        movem.l (sp)+,d0/d7/a0-a1
        ifd CORE_TRACE
        clr.w   core_trace_marker
        endif
        move.w  (sp)+,sr
        move.l  (sp)+,a5
        rts
game_core_latch_actions:
        movem.l a5,-(sp)
        move.w  sr,-(sp)
        cmpi.b  #2,game_history_mode
        bne.s   .history_allowed
        tst.b   game_history_replaying
        bne.s   .history_allowed
        move.w  (sp)+,sr
        move.l  (sp)+,a5
        rts
.history_allowed:
        lea     game_core_state,a5
        movem.l d6-d7/a0-a1,-(sp)
        moveq   #9,d6
        bsr     game_history_before
        movem.l (sp)+,d6-d7/a0-a1
        ifd CORE_TRACE
        move.w  d0,core_trace_arguments+0
        move.w  d1,core_trace_arguments+2
        move.w  d2,core_trace_arguments+4
        move.w  d3,core_trace_arguments+6
        move.w  d4,core_trace_arguments+8
        move.w  d5,core_trace_arguments+10
        move.w  #9,core_trace_marker
        endif
        move.w  (sp)+,sr
        bsr     game_core_latch_actions_body
        move.w  sr,-(sp)
        movem.l d0/d7/a0-a1,-(sp)
        bsr     game_history_after
        movem.l (sp)+,d0/d7/a0-a1
        ifd CORE_TRACE
        clr.w   core_trace_marker
        endif
        move.w  (sp)+,sr
        move.l  (sp)+,a5
        rts
        ifd CORE_TRACE
core_trace_marker: dc.w 0
core_trace_arguments: dcb.w 6,0
        endif
