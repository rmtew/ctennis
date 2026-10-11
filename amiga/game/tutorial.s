; Native tutorial controller. Every worker return retains selected318/all72.
TUTORIAL_ENTERING equ 1
TUTORIAL_COMPUTING equ 2
TUTORIAL_RENDERING equ 3
TUTORIAL_READY equ 4
TUTORIAL_UNAVAILABLE equ 5
TUTORIAL_WAITING equ 6

; Gesture thresholds are video-standard dependent and ready before sampling.
tutorial_init:
        move.l  simulation_interval_whole,d0
        mulu.w  #15,d0
        move.l  d0,tutorial_double_ticks
        move.l  simulation_interval_whole,d0
        move.l  d0,tutorial_repeat_ticks
        rts

; D0/D1 physical A/B packets. B2 belongs to the one-player UI before sampling.
tutorial_sample:
        movem.l d2-d7/a0-a2,-(sp)
        clr.b   tutorial_resume_defer
        clr.b   tutorial_enter_pressed
        ; No tutorial hint is displayed on an idle non-playing screen. Fresh
        ; pad/Return intent still selects its source before a title entry.
        tst.b   tutorial_active
        bne     .source_intent
        cmpi.w  #GAME_PLAYING,game_lifecycle
        beq     .source_intent
        tst.b   d0
        bne     .source_intent
        tst.b   d1
        bne     .source_intent
        tst.b   game_keyboard_matrix+$44
        beq     .source_done
.source_intent:
        ; Only deliberate physical edges select hints, never held repeats.
        move.b  ui_joystick_bits,d2
        move.b  ui_joystick_previous,d3
        eor.b   d3,d2
        andi.b  #$3f,d2
        beq     .keyboard_source
        clr.b   tutorial_input_source
.keyboard_source:
        lea     game_keyboard_mapping,a0
.source_key:
        moveq   #0,d2
        move.b  (a0)+,d2
        bmi     .source_done
        move.b  (a0)+,d3
        addq.l  #1,a0
        tst.b   d3
        bne     .source_key
        lea     game_keyboard_matrix,a1
        move.b  (a1,d2.w),d3
        lea     ui_previous_keys,a1
        move.b  (a1,d2.w),d4
        eor.b   d4,d3
        beq     .source_key
        move.b  #1,tutorial_input_source
        bra     .source_key
.source_done:
        tst.b   game_keyboard_matrix+$44
        beq     .enter_done
        tst.b   ui_previous_keys+$44
        bne     .enter_done
        move.b  #16,tutorial_enter_pressed
.enter_done:
        btst     #7,game_mode
        bne     .done
        move.b  d0,tutorial_packet
        move.b  d0,d2
        move.b  tutorial_previous_packet,d3
        eor.b   d3,d2
        move.b  d0,tutorial_previous_packet
        andi.b  #$df,d0
        tst.b   tutorial_active
        bne     .active
        tst.b   ui_demo
        bne     .done
        cmpi.w  #GAME_PLAYING,game_lifecycle
        bne     .done
        btst     #5,d2
        beq     .done
        btst     #5,tutorial_packet
        bne     .done
        tst.b   tutorial_tap_pending
        beq     .first_tap
        move.l  tutorial_tap_time,d3
        sub.l   last_timer_count,d3
        cmp.l   tutorial_double_ticks,d3
        bhi     .first_tap
        st      tutorial_enter_pending
        clr.b   tutorial_tap_pending
        bra     .done
.first_tap:
        st      tutorial_tap_pending
        move.l  last_timer_count,tutorial_tap_time
        bra     .done
.active:
        btst     #5,tutorial_packet
        beq     .released
        move.b  tutorial_packet,d3
        andi.b  #15,d3
        beq     .done
        st      tutorial_modifier_used
        bra     .done
.released:
        btst     #5,d2
        beq     .done
        tst.b   tutorial_modifier_used
        bne     .consume_modifier
        eori.b  #1,tutorial_menu
        move.b  #0,tutorial_menu_selection
        move.b  tutorial_packet,tutorial_previous_menu_packet
        movem.l d0-d1,-(sp)
        bsr     tutorial_redraw
        movem.l (sp)+,d0-d1
.consume_modifier:
        clr.b   tutorial_modifier_used
.done:
        movem.l (sp)+,d2-d7/a0-a2
        rts

; Called after physical sampling/commands, before any native dispatcher body.
tutorial_tick:
        tst.b   tutorial_active
        bne     .work
        tst.b   tutorial_enter_pending
        bne     .work
        tst.b   tutorial_title_pending
        bne     .work
        rts
.work:  movem.l d0-d7/a0-a6,-(sp)
        tst.b   tutorial_title_pending
        beq     .entry
        cmpi.w  #GAME_PLAYING,game_lifecycle
        bne     .done
        st      tutorial_enter_pending
        clr.b   tutorial_title_pending
.entry:
        tst.b   tutorial_enter_pending
        beq     .running
        clr.b   tutorial_enter_pending
        bsr     tutorial_enter
.running:
        tst.b   tutorial_active
        beq     .done
        bsr     tutorial_controls
        tst.b   tutorial_active
        beq     .done
        ; Optional prediction and production belong to the root deadline owner.
.done:
        movem.l (sp)+,d0-d7/a0-a6
        rts

tutorial_enter:
        btst     #7,game_mode
        bne     .done
        tst.b   ui_demo
        bne     .done
        cmpi.w  #GAME_PLAYING,game_lifecycle
        bne     .done
        jsr     game_history_freeze
        tst.l   d0
        beq     .done
        st      tutorial_active
        st      ui_paused
        bsr     tutorial_footer_invalidate
        clr.b   tutorial_menu
        clr.b   tutorial_modifier_used
        clr.b   tutorial_tap_pending
        move.l  game_history_position,tutorial_selected_cursor
        move.l  game_history_position+4,tutorial_selected_cursor+4
        moveq   #0,d7
        tst.b    game_play_state+G_LOWER_AI
        beq     .end_ready
        moveq   #1,d7
.end_ready:
        move.b  d7,tutorial_end
        mulu.w  #10,d7
        lea     game_play_state,a0
        adda.w  d7,a0
        move.b  P_X(a0),tutorial_x
        move.b  P_Y(a0),tutorial_y
        moveq   #0,d0
        move.b  game_audio_voices+AV_LEVEL,d0
        move.w  d0,ui_saved_volumes
        move.b  game_audio_voices+AV_SIZE+AV_LEVEL,d0
        move.w  d0,ui_saved_volumes+2
        move.b  game_audio_voices+2*AV_SIZE+AV_LEVEL,d0
        move.w  d0,ui_saved_volumes+4
        clr.w   $dff0a8
        clr.w   $dff0b8
        clr.w   $dff0d8
        bsr     tutorial_request
.done:  rts

tutorial_request:
        move.w  #$fffe,d1
        moveq   #0,d7
        move.b  tutorial_end,d7
        mulu.w  #P_SIZE,d7
        lea     game_play_state,a0
        move.b  P_PHASE(a0,d7.w),d2
        andi.b  #$e0,d2
        bne.s   .serve_context
        ; Current incoming before contact; latest retained return/miss after it.
        move.b  game_contact,d2
        andi.b  #$8d,d2
        bne.s   .completed_context
        moveq   #0,d2
        btst    #6,game_contact
        sne     d2
        andi.w  #1,d2
        moveq   #0,d3
        move.b  tutorial_end,d3
        eori.w  #1,d3
        cmp.w   d3,d2
        beq.s   .context
.completed_context:
        move.w  game_history_attempt_count,d4
.find_completed:
        subq.w  #1,d4
        bmi.s   .context
        move.w  d4,d0
        add.w   game_history_attempt_first,d0
        andi.w  #HISTORY_ATTEMPTS-1,d0
        bsr     game_history_attempt_address
        move.w  10(a0),d2
        moveq   #0,d3
        move.b  tutorial_end,d3
        cmp.w   d3,d2
        bne.s   .find_completed
        move.w  8(a0),d2
        cmpi.w  #1,d2
        beq.s   .completed_found
        cmpi.w  #2,d2
        bne.s   .find_completed
.completed_found:
        move.w  d4,d1
        bra.s   .context
.serve_context:
        move.w  #$ffff,d1
.context:
        move.l  game_preview_generation,d0
        moveq   #0,d2
        moveq   #0,d3
        move.b  tutorial_x,d2
        move.b  tutorial_y,d3
        jsr     game_preview_request_projected
        tst.l   d0
        beq     .missing
        ; A completed waiting bank belongs to the old accepted placement.
        ; Retire it before the new generation becomes visible to publication.
        bsr     discard_ready_scene
        move.l  game_preview_generation,tutorial_generation
        st      tutorial_pending
        st      tutorial_work_pending
        move.w  #TUTORIAL_COMPUTING,tutorial_status
        clr.w   tutorial_animation_index
        clr.w   tutorial_progress_operations
        clr.l   tutorial_counts
        bsr     tutorial_progress_reset
        clr.w   tutorial_footer_ready
        st      tutorial_footer_dirty
        rts
.missing:
        clr.b   tutorial_work_pending
        move.w  #TUTORIAL_UNAVAILABLE,tutorial_status
        clr.b   tutorial_pending
        clr.l   tutorial_counts
        bsr     tutorial_progress_reset
        clr.w   tutorial_footer_ready
        st      tutorial_footer_dirty
        rts

; Native key/direction intent only. Legal positions are read from actual tables.
tutorial_controls:
        ; Menu confirmation owns F/B1; preserve the chosen shot alternative
        ; while the menu is open instead of turning its confirm into an edit.
        tst.b   tutorial_menu
        bne     .menu
        move.b  tutorial_packet,d0
        moveq   #1,d1
        btst     #4,d0
        beq     .variant
        moveq   #0,d1
.variant:
        cmp.b   tutorial_active_variant,d1
        beq     .menu
        ; Variant changes also retire an obsolete completed waiting bank.
        bsr     discard_ready_scene
        move.b  d1,tutorial_active_variant
        clr.w   tutorial_animation_index
        bsr     tutorial_progress_variant_changed
.menu:
        tst.b   tutorial_menu
        beq     .movement
        move.b  ui_edges,d0
        btst     #0,d0
        beq     .down
        tst.b   tutorial_menu_selection
        beq     .down
        subq.b  #1,tutorial_menu_selection
        bsr     tutorial_redraw
.down:
        move.b  ui_edges,d0
        btst     #1,d0
        beq     .confirm
        cmpi.b  #2,tutorial_menu_selection
        beq     .confirm
        addq.b  #1,tutorial_menu_selection
        bsr     tutorial_redraw
.confirm:
        tst.b   tutorial_enter_pressed
        bne     .activate
        move.b  tutorial_packet,d0
        move.b  tutorial_previous_menu_packet,d1
        eor.b   d1,d0
        and.b   tutorial_packet,d0
        btst     #4,d0
        beq     .save_menu
.activate:
        cmpi.b  #1,tutorial_menu_selection
        beq     tutorial_resume_latest
        cmpi.b  #2,tutorial_menu_selection
        bne     .save_menu
        clr.b   tutorial_menu
        bsr     tutorial_redraw
.save_menu:
        move.b  tutorial_packet,tutorial_previous_menu_packet
        rts
.movement:
        btst     #5,tutorial_packet
        bne     .done
        move.b  tutorial_packet,d6
        andi.b  #15,d6
        beq     .done
        move.l  tutorial_repeat_time,d0
        sub.l   last_timer_count,d0
        cmp.l   tutorial_repeat_ticks,d0
        bcs     .done
        move.l  last_timer_count,tutorial_repeat_time
        moveq   #0,d7
        move.b  tutorial_end,d7
        mulu.w  #10,d7
        lea     game_play_state,a3
        ; UI edits use the selected frozen phase, including completed handoff.
        adda.w  d7,a3
        lea     game_lower_limits,a0
        tst.b   tutorial_end
        beq     .limits
        lea     game_upper_limits,a0
.limits:
        moveq   #0,d0
        move.b  P_ANIMATION(a3),d0
        lsr.w   #3,d0
        andi.w  #12,d0
        adda.w  d0,a0
        move.b  tutorial_x,d4
        move.b  tutorial_y,d5
        btst     #0,d6
        beq     .left
        addq.b  #1,d4
.left:  btst    #2,d6
        beq     .up
        subq.b  #1,d4
.up:    btst    #1,d6
        beq     .down_move
        subq.b  #1,d5
.down_move:
        btst     #3,d6
        beq     .clamp
        addq.b  #1,d5
.clamp:
        cmp.b   3(a0),d4
        bcc     .right
        move.b  3(a0),d4
.right: cmp.b   2(a0),d4
        bcs     .top
        move.b  2(a0),d4
        subq.b  #1,d4
.top:   cmp.b   1(a0),d5
        bcc     .bottom
        move.b  1(a0),d5
.bottom:
        cmp.b   (a0),d5
        bcs     .changed
        move.b  (a0),d5
        subq.b  #1,d5
.changed:
        cmp.b   tutorial_x,d4
        bne     .request
        cmp.b   tutorial_y,d5
        beq     .done
.request:
        move.b  d4,tutorial_x
        move.b  d5,tutorial_y
        bra     tutorial_request
.done:  rts

tutorial_resume_latest:
        jsr     game_history_resume_latest
        tst.l   d0
        beq     tutorial_resume_done
tutorial_resume_restored:
        ; Exact interrupted canonical boundary, before physical reconciliation.
        bsr     tutorial_footer_invalidate
        clr.b   tutorial_active
        clr.b   tutorial_pending
        clr.b   tutorial_menu
        clr.b   tutorial_work_pending
        clr.w   tutorial_render_phase
        clr.b   ui_paused
        st      tutorial_resume_defer
        addq.w  #1,tutorial_resume_count
        bsr     tutorial_reconcile_inputs
        move.w  ui_saved_volumes,$dff0a8
        move.w  ui_saved_volumes+2,$dff0b8
        move.w  ui_saved_volumes+4,$dff0d8
        bsr     tutorial_restore_court
        move.w  #$ffff,ui_overlay_signature
tutorial_resume_done:
        rts

; Consume only newly carried physical bits; retain already-held logical bits.
tutorial_reconcile_inputs:
        lea     ui_joystick_bits,a0
        lea     ui_joystick_entry,a1
        lea     game_input_bits,a2
        moveq   #1,d7
.pads:  move.b  (a2)+,d0
        not.b   d0
        and.b   (a0)+,d0
        move.b  d0,(a1)+
        dbra    d7,.pads
        lea     game_keyboard_mapping,a0
        lea     ui_keyboard_entry_keys,a1
.keys:  moveq   #0,d0
        move.b  (a0)+,d0
        bmi     .enter
        moveq   #0,d1
        move.b  (a0)+,d1
        move.b  (a0)+,d2
        lea     game_input_bits,a2
        and.b   (a2,d1.w),d2
        bne     .retained
        lea     game_keyboard_matrix,a2
        move.b  (a2,d0.w),(a1,d0.w)
        bra     .keys
.retained:
        clr.b   (a1,d0.w)
        bra     .keys
.enter: clr.b   ui_keyboard_entry_keys+$44
        tst.b   game_continue_held
        bne     .done
        move.b  game_keyboard_matrix+$44,ui_keyboard_entry_keys+$44
.done:  rts

        include "amiga/game/tutorial_deadline.s"
