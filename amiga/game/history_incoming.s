; Latest incoming origin is live recording metadata, never a replay output.
game_history_incoming_reset:
        clr.b   game_history_incoming_valid
        clr.b   game_history_incoming_pending
        addq.l  #1,game_history_live_epoch
        rts

; Called from actual preserving launch hooks. D7 launching physical end.
game_history_incoming_launch:
        cmpi.b  #1,game_history_mode
        bne.s   .done
        tst.b   game_history_replaying
        bne.s   .done
        tst.b   game_preview_active
        bne.s   .done
        cmpi.w  #8,game_history_operation
        bne.s   .done
        cmpa.l  #game_core_state,a5
        bne.s   .done
        tst.b   G_LOWER_AI(a4,d7.w)
        beq.s   .human
        move.w  d7,d0
        eori.w  #1,d0
        tst.b   G_LOWER_AI(a4,d0.w)
        bne.s   .human
        move.w  d0,game_history_incoming_pending_end
        st      game_history_incoming_pending
        clr.b   game_history_incoming_valid
        rts
.human:
        ; A later human launch inside this same dispatcher cancels capture.
        clr.b   game_history_incoming_valid
        clr.b   game_history_incoming_pending
.done:  rts

; After full body/service, cursor advancement and checkpoint eviction. Uses
; only D0/D7/A0/A1; the public wrapper preserves these and the incoming CCR.
game_history_incoming_after:
        cmpi.b  #1,game_history_mode
        bne     .done
        tst.b   game_history_replaying
        bne     .done
        tst.b   game_preview_active
        bne     .done
        cmpi.w  #GAME_PLAYING,game_lifecycle
        bne     .retire
        move.b  game_contact,d0
        andi.b  #$8d,d0
        bne     .retire
        tst.b   game_history_incoming_pending
        beq.s   .existing
        clr.b   game_history_incoming_pending
        cmpi.w  #8,game_history_operation
        bne     .retire
        move.w  game_history_incoming_pending_end,d0
        move.w  d0,game_history_incoming_end
        eori.w  #1,d0
        lsl.b   #6,d0
        cmp.b   game_contact,d0
        bne     .retire
        btst    #6,game_flight
        beq     .retire
        btst    #7,game_flight
        bne     .retire
        lea     game_history_incoming_state,a0
        lea     game_core_state,a1
        bsr     game_history_copy_state
        move.l  game_history_cursor,game_history_incoming_cursor
        move.l  game_history_cursor+4,game_history_incoming_cursor+4
        move.w  #GAME_CORE_SCHEMA_VERSION,game_history_incoming_schema
        move.w  #GAME_CORE_SIMULATION_VERSION,game_history_incoming_simulation
        move.l  game_history_live_epoch,game_history_incoming_epoch
        st      game_history_incoming_valid
game_history_incoming_capture_complete equ *
.existing:
        tst.b   game_history_incoming_valid
        beq.s   .done
        move.w  game_history_incoming_end,d0
        lea     game_play_state+G_LOWER_AI,a0
        tst.b   (a0,d0.w)
        bne.s   .retire
        lea     game_history_incoming_cursor,a0
        lea     game_history_oldest,a1
        bsr     game_preview_compare_cursor
        tst.l   d0
        bmi.s   .retire
.done:  rts
.retire:
        clr.b   game_history_incoming_valid
        clr.b   game_history_incoming_pending
        rts

; Read-only current/latest shortcut. D0 accepted. Historical
; selection, expired identities and unsupported state retain original resolver.
game_history_incoming_match:
        moveq   #0,d0
        tst.b   game_history_incoming_valid
        beq     .done
        move.w  game_preview_end,d0
        cmp.w   game_history_incoming_end,d0
        bne     .invalid
        cmpi.w  #GAME_CORE_SCHEMA_VERSION,game_history_incoming_schema
        bne     .invalid
        cmpi.w  #GAME_CORE_SIMULATION_VERSION,game_history_incoming_simulation
        bne     .invalid
        move.l  game_history_live_epoch,d0
        cmp.l   game_history_incoming_epoch,d0
        bne.s   .invalid
        ; No launch has completed at match cursor zero. Reject before converting
        ; the post-operation identity into the preview's pre-operation cursor.
        move.l  game_history_incoming_cursor,d0
        or.l    game_history_incoming_cursor+4,d0
        beq.s   .invalid
        lea     game_preview_selected,a0
        lea     game_history_cursor,a1
        bsr     game_preview_compare_cursor
        tst.l   d0
        bne.s   .invalid
        lea     game_history_incoming_cursor,a0
        lea     game_history_oldest,a1
        bsr     game_preview_compare_cursor
        tst.l   d0
        bmi.s   .invalid
        lea     game_history_incoming_cursor,a0
        lea     game_preview_selected,a1
        bsr     game_preview_compare_cursor
        tst.l   d0
        bgt.s   .invalid
        moveq   #1,d0
.done:  rts
.invalid:
        moveq   #0,d0
        rts
