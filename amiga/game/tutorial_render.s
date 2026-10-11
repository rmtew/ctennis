; Two private court surfaces. Displayed/queued surfaces are never writable.
; Completed native pixels place sprite O_X at court X, and O_Y at court Y+1.
; The authored sprite/Copper origins alone do not define the cropped pixel X.
TUTORIAL_X_ORIGIN equ 0
TUTORIAL_Y_ORIGIN equ $2d-$2c

; Prepare immutable court/banner and menu/control rasters before the timer is
; started. Neither private canvas is consumer-owned during this initialization.
tutorial_prepare_canvases:
        movem.l d0-d7/a0-a6,-(sp)
        st      tutorial_preparing
        move.l  #tutorial_surface0,tutorial_render_surface
        moveq   #0,d6
.selection:
        lea     plane0,a0
        lea     tutorial_surface0,a1
        move.w  #4*6144/4-1,d7
.court: move.l  (a0)+,(a1)+
        dbra    d7,.court
        move.b  d6,tutorial_menu_selection
        st      tutorial_menu
        clr.w   tutorial_text_row
.text:  bsr     tutorial_draw_text
        cmpi.w  #4,tutorial_text_row
        bcs.s   .text
        move.w  d6,d0
        mulu.w  #30*32*4,d0
        lea     tutorial_menu_cache,a1
        adda.l  d0,a1
        lea     tutorial_surface0+132*32,a0
        moveq   #3,d5
.roi:   move.w  #30*32/4-1,d7
.copy:  move.l  (a0)+,(a1)+
        dbra    d7,.copy
        adda.w  #6144-30*32,a0
        dbra    d5,.roi
        addq.w  #1,d6
        cmpi.w  #3,d6
        bcs.s   .selection
        clr.b   tutorial_menu
        clr.b   tutorial_menu_selection
        lea     plane0,a0
        lea     tutorial_surface0,a1
        move.w  #4*6144/4-1,d7
.baseline:
        move.l  (a0)+,(a1)+
        dbra    d7,.baseline
        clr.w   tutorial_text_row
        bsr     tutorial_draw_text
        lea     tutorial_surface0,a0
        lea     tutorial_surface1,a1
        move.l  a1,tutorial_render_surface
        move.w  #4*6144/4-1,d7
.second:move.l  (a0)+,(a1)+
        dbra    d7,.second
        moveq   #0,d4
        lea     tutorial_controls_texts,a5
        lea     tutorial_controls_cache,a6
        moveq   #4,d6
.hint:  move.l  (a5)+,a0
        move.l  a6,a2
        cmpi.w  #2,d6
        bcs.s   .plain_hint
        bsr     ui_footer_selected
        bra.s   .next_hint
.plain_hint:
        bsr     ui_footer_text
.next_hint:
        adda.w  #256,a6
        dbra    d6,.hint
        clr.w   tutorial_render_phase
        move.w  #$ffff,tutorial_canvas_menus
        move.w  #$ffff,tutorial_canvas_controls
        move.w  #$ffff,tutorial_canvas_captions
        clr.b   tutorial_preparing
        movem.l (sp)+,d0-d7/a0-a6
        rts

tutorial_redraw:
        ; A superseded completed bank must not display an older menu identity.
        bsr     discard_ready_scene
        addq.w  #1,tutorial_render_generation
        st      tutorial_placement_dirty
        clr.w   tutorial_render_phase
        clr.b   tutorial_line_active
        ; Preserve the reviewed three-choice menu and highlight. Its private
        ; canvas is exceptional UI work, never a placement/trail prerequisite.
        tst.b   tutorial_menu
        beq     .footer
        move.w  #1,tutorial_render_phase
        clr.l   tutorial_render_offset
        clr.w   tutorial_text_row
.footer:
        clr.w   tutorial_footer_ready
        st      tutorial_footer_dirty
        rts

tutorial_footer_select:
        ; Control instructions remain available during every generation.
        lea     tutorial_keyboard_controls_text,a0
        tst.b   tutorial_input_source
        bne.s   .control_source
        lea     tutorial_pad_controls_text,a0
.control_source:
        tst.b   tutorial_menu
        beq     .text
        lea     tutorial_menu_text,a0
        bra     .text
.text:  move.l  a0,d6
        lea     tutorial_close_hint_text,a0
        tst.b   tutorial_menu
        bne     .count_ready
        lea     tutorial_empty_text,a0
        cmpi.w  #TUTORIAL_UNAVAILABLE,tutorial_status
        beq     .count_ready
        lea     tutorial_wait_text,a0
        tst.b   tutorial_waiting_ready
        bne     .count_ready
        lea     tutorial_count_text,a0
        tst.b   tutorial_placement_ready
        bne.s   .selected_outcome
        lea     tutorial_computing_detail_text,a0
        bra     .count_ready
.selected_outcome:
        moveq   #0,d0
        move.b  tutorial_potential_variant,d0
        add.w   d0,d0
        lea     tutorial_outcomes,a1
        move.w  (a1,d0.w),d1
        bne.s   .caption_outcome
        tst.b   tutorial_marker_ready
        beq     .count_ready
        lea     game_preview_endpoint_outcomes,a1
        move.w  (a1,d0.w),d1
.caption_outcome:
        beq     .count_ready
        cmpi.w  #PREVIEW_LIFECYCLE,d1
        bhi     .count_ready
        bsr     tutorial_released_wait
        tst.l   d0
        beq     .outcome
        lea     tutorial_wait_text,a0
        bra     .count_ready
.outcome:
        subq.w  #1,d1
        lsl.w   #2,d1
        lea     tutorial_outcome_texts,a1
        cmpi.w  #3,game_preview_kind
        bne.s   .outcome_table
        ; Preserve the observed result while naming the prospective action.
        lea     tutorial_serve_press_outcomes,a1
        tst.b   tutorial_active_variant
        bne.s   .outcome_table
        lea     tutorial_serve_held_outcomes,a1
.outcome_table:
        move.l  (a1,d1.w),a0
        cmpi.w  #TUTORIAL_UNAVAILABLE,tutorial_status
        bne     .count_ready
        lea     tutorial_empty_text,a0
.count_ready:
        rts

; Preserve the synchronous ABI through the same cooperative renderer body.
tutorial_footer:
        movem.l d0-d7/a0-a6,-(sp)
.again: bsr     tutorial_footer_step
        tst.l   d0
        beq.s   .again
        movem.l (sp)+,d0-d7/a0-a6
        rts

; Cancel private work and completed-caption cache together. No live bitmap write.
tutorial_footer_invalidate:
        clr.w   tutorial_footer_ready
        clr.w   tutorial_footer_stage
        clr.l   tutorial_footer_first
        clr.l   tutorial_footer_second
        rts

; D0=1 complete, 0 pending; preserve all other registers. One clear/layout or
; at most two actual glyphs per call. Partial bytes never imply footer_ready.
; Re-select on every call: both generation and caption identity own the stage.
tutorial_footer_step:
        movem.l d1-d7/a0-a6,-(sp)
        bsr     tutorial_footer_select
        move.l  tutorial_generation,d0
        tst.w   tutorial_footer_stage
        beq     .idle
        cmp.l   tutorial_footer_stage_generation,d0
        bne     .start
        cmp.l   tutorial_footer_stage_first,d6
        bne     .start
        cmpa.l  tutorial_footer_stage_second,a0
        bne     .start
        bra     .glyphs
.idle:
        cmp.l   tutorial_footer_stage_generation,d0
        bne     .start
        cmp.l   tutorial_footer_first,d6
        bne     .start
        cmpa.l  tutorial_footer_second,a0
        beq     .complete
.start:
        ; Invalidate completed cache before touching its private payload.
        clr.w   tutorial_footer_ready
        clr.l   tutorial_footer_first
        clr.l   tutorial_footer_second
        move.l  d0,tutorial_footer_stage_generation
        move.l  d6,tutorial_footer_stage_first
        move.l  a0,tutorial_footer_stage_second
        lea     tutorial_footer_scratch,a1
        moveq   #0,d0
        move.w  #512/4-1,d1
.clear: move.l  d0,(a1)+
        dbra    d1,.clear
        move.w  #1,tutorial_footer_stage
        move.l  d6,a0
        lea     tutorial_footer_scratch,a2
        bsr     ui_footer_layout
        tst.l   d0
        beq     .second
        move.l  a0,tutorial_footer_cursor
        move.l  a2,tutorial_footer_destination
        bra     .pending
.glyphs:
        move.l  tutorial_footer_cursor,a0
        move.l  tutorial_footer_destination,a2
        moveq   #0,d4
        moveq   #0,d3
        cmpi.w  #1,tutorial_footer_stage
        bne.s   .plain
        moveq   #-1,d3
.plain: moveq   #1,d5
.character:
        bsr     ui_text_character
        tst.l   d0
        beq.s   .line_done
        dbra    d5,.character
        tst.b   (a0)
        beq.s   .line_done
        move.l  a0,tutorial_footer_cursor
        move.l  a2,tutorial_footer_destination
        bra.s   .pending
.line_done:
        cmpi.w  #1,tutorial_footer_stage
        bne.s   .finished
.second:
        move.w  #2,tutorial_footer_stage
        move.l  tutorial_footer_stage_second,a0
        lea     tutorial_footer_scratch+256,a2
        bsr     ui_footer_layout
        tst.l   d0
        beq.s   .finished
        move.l  a0,tutorial_footer_cursor
        move.l  a2,tutorial_footer_destination
        bra.s   .pending
.finished:
        move.l  tutorial_footer_stage_first,tutorial_footer_first
        move.l  tutorial_footer_stage_second,tutorial_footer_second
        clr.w   tutorial_footer_stage
.complete:
        moveq   #1,d0
        bra.s   .done
.pending:
        moveq   #0,d0
.done:  movem.l (sp)+,d1-d7/a0-a6
        rts

; A bounded released preview can settle in the actual human serve-wait phase.
; Describe that observed attached-ball state, never a completed outgoing shot.
tutorial_released_wait:
        moveq   #0,d0
        tst.b   tutorial_potential_variant
        beq     .done
        cmpi.w  #$ffff,game_preview_ordinal
        bne     .done
        cmpi.w  #PREVIEW_PRIME,game_preview_status
        bcs     .done
        btst    #1,game_preview_primed_mask+1
        beq     .done
        cmpi.w  #PREVIEW_READY,game_preview_status
        bhi     .done
        tst.w   game_preview_dispatches+2
        beq     .done
        tst.b   game_preview_launches+1
        bne     .done
        ; A partial dispatch cannot expose its gameplay-stage phase to UI.
        tst.w   game_preview_dispatch_stages+2
        beq.s   .complete_phase
        lea     game_preview_dispatch_origin_phases+1,a1
        bra.s   .phase
.complete_phase:
        lea     game_preview_released_state+(game_lower_phase-game_core_state),a1
        tst.b   tutorial_end
        beq     .phase
        lea     game_preview_released_state+(game_upper_phase-game_core_state),a1
.phase: cmpi.b  #$40,(a1)
        bne     .done
        moveq   #1,d0
.done:  rts

tutorial_render:
        ; Mandatory menu production is now one complete cached ROI transaction.
        bra     tutorial_progress_fast_publish
        ; Optional legacy ghost/path bodies remain disabled by the prototype.
        ; One complete unit per root grant; no recursive admission or loop.
        move.w  tutorial_render_phase,d0
        beq     tutorial_animate
        cmpi.w  #1,d0
        beq     tutorial_copy_court
        cmpi.w  #2,d0
        beq     tutorial_draw_ghost
        cmpi.w  #3,d0
        beq     tutorial_draw_paths
        cmpi.w  #4,d0
        beq     tutorial_draw_text
        cmpi.w  #5,d0
        beq     tutorial_publish
        rts

; Read the actual displayed/queued first bitplane from their copper banks.
tutorial_copper_plane:
        moveq   #0,d0
        move.w  cop_bpl0h+2-copperlist(a0),d0
        swap    d0
        move.w  cop_bpl0h+6-copperlist(a0),d0
        rts

tutorial_choose_surface:
        ; An IRQ can move ready to presentation and clear ready. Select from
        ; one coherent ownership snapshot; bulk rendering remains interruptible.
        move.w  sr,-(sp)
        ori.w   #$0700,sr
        move.l  presentation_copper,a0
        cmpa.l  #title_copper,a0
        beq     .none_displayed
        bsr     tutorial_copper_plane
        move.l  d0,d4
        bra     .ready
.none_displayed:
        moveq   #0,d4
.ready: moveq   #0,d5
        move.l  ready_copper,d0
        beq     .candidates
        move.l  d0,a0
        bsr     tutorial_copper_plane
        move.l  d0,d5
.candidates:
        lea     tutorial_surface0,a1
        move.l  a1,d0
        cmp.l   d0,d4
        beq     .second
        cmp.l   d0,d5
        bne     .found
.second:
        lea     tutorial_surface1,a1
        move.l  a1,d0
        cmp.l   d0,d4
        beq     .busy
        cmp.l   d0,d5
        beq     .busy
.found: move.l  a1,tutorial_render_surface
        move.w  tutorial_render_generation,tutorial_build_generation
        move.w  (sp)+,sr
        moveq   #1,d0
        rts
.busy:  move.w  (sp)+,sr
        moveq   #0,d0
        rts

; A placement can borrow an immutable already completed pending canvas. Only
; its new sprite bank is built: no court, cue or footer byte is changed. This
; avoids making mandatory actor input wait for a free canvas during prediction.
; Eligibility is re-read on every root attempt; no refused-time cache exists.
tutorial_pending_canvas_eligible:
        move.l  tutorial_visible_surface,a1
tutorial_neutral_canvas_eligible:
        moveq   #0,d0
        tst.b   tutorial_menu
        bne     .done
        tst.b   tutorial_ball_mode
        bne     .done
        tst.b   tutorial_marker_ready
        bne     .done
        cmpi.w  #TUTORIAL_COMPUTING,tutorial_status
        bne     .done
        moveq   #0,d1
        cmpa.l  #tutorial_surface0,a1
        beq.s   .identity
        cmpa.l  #tutorial_surface1,a1
        bne     .done
        moveq   #1,d1
.identity:
        lea     tutorial_canvas_menus,a0
        cmpi.b  #$ff,(a0,d1.w)
        bne     .done
        lea     tutorial_canvas_controls,a0
        move.b  tutorial_input_source,d2
        cmp.b   (a0,d1.w),d2
        bne     .done
        lea     tutorial_canvas_captions,a0
        tst.b   (a0,d1.w)
        bne     .done
        move.w  d1,d2
        mulu.w  #20,d2
        lea     tutorial_canvas_markers,a0
        tst.b   4(a0,d2.w)
        bne     .done
        moveq   #1,d0
.done:  rts

; Change only the menu's30 rows on a free canvas. Closed scenes restore the
; original ROI; opening/highlighting uses the startup-authored selection cache.
; Each of four960-byte planes is copied in bounded48-byte register bursts.
tutorial_prepare_menu_roi:
        movem.l d0-d7/a0-a6,-(sp)
        moveq   #-1,d4
        tst.b   tutorial_menu
        beq.s   .identity
        moveq   #0,d4
        move.b  tutorial_menu_selection,d4
.identity:
        lea     tutorial_canvas_menus,a2
        cmpi.l  #tutorial_surface0,tutorial_render_surface
        beq.s   .cached
        addq.l  #1,a2
.cached:
        cmp.b   (a2),d4
        beq.s   .done
        move.l  a2,a5
        lea     plane0+132*32,a0
        tst.b   tutorial_menu
        beq.s   .destination
        moveq   #0,d0
        move.b  tutorial_menu_selection,d0
        mulu.w  #30*32*4,d0
        lea     tutorial_menu_cache,a0
        adda.l  d0,a0
.destination:
        move.l  tutorial_render_surface,a1
        adda.w  #132*32,a1
        moveq   #3,d6
.plane: bsr     tutorial_copy_960
        adda.w  #6144-30*32,a1
        tst.b   tutorial_menu
        bne.s   .next
        adda.w  #6144-30*32,a0
.next:  dbra    d6,.plane
        move.b  d4,(a5)
.done:
        movem.l (sp)+,d0-d7/a0-a6
        rts

tutorial_copy_960:
        movem.l d0-d7/a2-a6,-(sp)
        moveq   #19,d7
.burst: movem.l (a0)+,d0-d6/a2-a6
        movem.l d0-d6/a2-a6,(a1)
        lea     48(a1),a1
        dbra    d7,.burst
        movem.l (sp)+,d0-d7/a2-a6
        rts

; A single current endpoint cue, never a path trail. Retire the previous cue
; only on the chosen free canvas and restore the exact underlying palette bits.
; This preserves banner and menu pixels even when the endpoint overlaps them.
tutorial_landing_owner:
        lea     tutorial_canvas_markers,a3
        cmpi.l  #tutorial_surface0,tutorial_render_surface
        beq.s   .done
        adda.w  #20,a3
.done:  rts

tutorial_restore_landing:
        movem.l d0-d7/a0-a6,-(sp)
        bsr     tutorial_landing_owner
        tst.b   4(a3)
        beq.s   .done
        move.w  (a3),d4
        move.w  2(a3),d5
        lea     6(a3),a4
        lea     tutorial_landing_offsets,a5
        moveq   #8,d7
.pixel: moveq   #0,d0
        moveq   #0,d1
        move.b  (a5)+,d0
        move.b  (a5)+,d1
        ext.w   d0
        ext.w   d1
        add.w   d4,d0
        add.w   d5,d1
        moveq   #0,d2
        move.b  (a4)+,d2
        bsr     tutorial_plot
        dbra    d7,.pixel
        clr.b   4(a3)
.done:  movem.l (sp)+,d0-d7/a0-a6
        rts

tutorial_draw_landing:
        movem.l d0-d7/a0-a6,-(sp)
        tst.b   tutorial_menu
        bne     .done
        tst.b   tutorial_waiting_ready
        bne     .done
        tst.b   tutorial_marker_ready
        beq     .done
        move.l  tutorial_generation,d0
        cmp.l   tutorial_marker_generation,d0
        bne     .done
        cmp.l   game_preview_generation,d0
        bne     .done
        moveq   #0,d0
        move.b  tutorial_potential_variant,d0
        lsl.w   #3,d0
        lea     game_preview_endpoints,a0
        adda.w  d0,a0
        moveq   #0,d4
        moveq   #0,d5
        move.b  (a0),d4
        move.b  1(a0),d5
        addi.w  #TUTORIAL_X_ORIGIN,d4
        addi.w  #TUTORIAL_Y_ORIGIN,d5
        bsr     tutorial_landing_owner
        move.w  d4,(a3)
        move.w  d5,2(a3)
        lea     6(a3),a4
        lea     tutorial_landing_offsets,a5
        moveq   #8,d7
.pixel: moveq   #0,d0
        moveq   #0,d1
        move.b  (a5)+,d0
        move.b  (a5)+,d1
        ext.w   d0
        ext.w   d1
        add.w   d4,d0
        add.w   d5,d1
        bsr     tutorial_read_landing_pixel
        move.b  d2,(a4)+
        ; The authored heading remains legible even for clipped/out endpoints.
        cmpi.w  #4,d1
        bcs.s   .draw
        cmpi.w  #12,d1
        bcc.s   .draw
        cmpi.w  #96,d0
        bcs.s   .draw
        cmpi.w  #160,d0
        bcs.s   .next_pixel
.draw:
        moveq   #15,d2
        bsr     tutorial_plot
.next_pixel:
        dbra    d7,.pixel
        st      4(a3)
.done:  movem.l (sp)+,d0-d7/a0-a6
        rts

; D0/D1 actual canvas coordinates; return four native plane bits in D2.
tutorial_read_landing_pixel:
        movem.l d0-d1/d3-d6/a0,-(sp)
        moveq   #0,d2
        cmpi.w  #256,d0
        bcc.s   .done
        cmpi.w  #192,d1
        bcc.s   .done
        lsl.w   #5,d1
        move.w  d0,d3
        lsr.w   #3,d3
        add.w   d3,d1
        move.l  tutorial_render_surface,a0
        adda.w  d1,a0
        andi.w  #7,d0
        moveq   #7,d3
        sub.w   d0,d3
        moveq   #0,d6
.plane: btst    d3,(a0)
        beq.s   .next
        bset    d6,d2
.next:  adda.w  #6144,a0
        addq.w  #1,d6
        cmpi.w  #4,d6
        bcs.s   .plane
.done:  movem.l (sp)+,d0-d1/d3-d6/a0
        rts

tutorial_landing_offsets:
        dc.b -2,0,-1,0,0,0,1,0,2,0,0,-2,0,-1,0,1,0,2
        even

; Mandatory controls are cached independently of prediction. Current completed
; contextual text is copied only with matching generation and caption identity.
; Every destination byte belongs to the selected free canvas, never live DMA.
tutorial_prepare_private_footer:
        movem.l d0-d7/a0-a6,-(sp)
        lea     tutorial_footer0,a1
        cmpi.l  #tutorial_surface0,tutorial_render_surface
        beq.s   .source
        lea     tutorial_footer1,a1
.source:
        lea     tutorial_controls_cache,a0
        tst.b   tutorial_input_source
        bne.s   .menu
        adda.w  #256,a0
.menu:  tst.b   tutorial_menu
        beq.s   .first
        lea     tutorial_controls_cache+512,a0
.first: moveq   #256/4-1,d7
.copy_first:
        move.l  (a0)+,(a1)+
        dbra    d7,.copy_first
        move.l  a1,a6
        bsr     tutorial_footer_select
        moveq   #1,d4
        cmpa.l  #tutorial_computing_detail_text,a0
        bne.s   .caption_identity
        moveq   #0,d4
.caption_identity:
        move.l  tutorial_generation,d0
        cmp.l   tutorial_caption_generation,d0
        bne.s   .pending
        cmp.l   tutorial_footer_first,d6
        bne.s   .pending
        cmpa.l  tutorial_footer_second,a0
        bne.s   .pending
        lea     tutorial_footer_scratch+256,a0
        bra.s   .second
.pending:
        lea     tutorial_controls_cache+768,a0
        moveq   #0,d4
        tst.b   tutorial_menu
        beq.s   .second
        moveq   #1,d4
        lea     tutorial_controls_cache+1024,a0
.second:
        move.l  a6,a1
        moveq   #256/4-1,d7
.copy_second:
        move.l  (a0)+,(a1)+
        dbra    d7,.copy_second
        moveq   #0,d0
        cmpi.l  #tutorial_surface0,tutorial_render_surface
        beq.s   .record_identity
        moveq   #1,d0
.record_identity:
        lea     tutorial_canvas_captions,a0
        move.b  d4,(a0,d0.w)
        lea     tutorial_canvas_controls,a0
        move.b  tutorial_input_source,(a0,d0.w)
        movem.l (sp)+,d0-d7/a0-a6
        rts

tutorial_copy_court:
        tst.l   tutorial_render_offset
        bne     .copy
        bsr     tutorial_choose_surface
        tst.l   d0
        beq     .done
.copy:  lea     plane0,a0
        move.l  tutorial_render_surface,a1
        move.l  tutorial_render_offset,d0
        adda.l  d0,a0
        adda.l  d0,a1
        move.w  #1024/4-1,d7
.loop:  move.l  (a0)+,(a1)+
        dbra    d7,.loop
        addi.l  #1024,tutorial_render_offset
        cmpi.l  #4*6144,tutorial_render_offset
        bne     .done
        ; Menu labels occupy the clear lower court, without path overprinting.
        tst.b   tutorial_menu
        beq     .ghost
        move.w  #4,tutorial_render_phase
        rts
.ghost:
        clr.w   tutorial_ghost_actor
        clr.w   tutorial_ghost_row
        move.w  #2,tutorial_render_phase
.done:  rts

; Four-plane point compositor. Coordinates already have native viewport offsets.
; D0=X, D1=Y, D2=palette index. Clips actual projected points at court bounds.
tutorial_plot:
        movem.l d0-d6/a0,-(sp)
        cmpi.w  #256,d0
        bcc     .done
        cmpi.w  #192,d1
        bcc     .done
        lsl.w   #5,d1
        move.w  d0,d3
        lsr.w   #3,d3
        add.w   d3,d1
        move.l  tutorial_render_surface,a0
        adda.w  d1,a0
        andi.w  #7,d0
        moveq   #7,d3
        sub.w   d0,d3
        moveq   #3,d4
.plane: btst    #0,d2
        beq     .clear
        bset     d3,(a0)
        bra     .next
.clear: bclr    d3,(a0)
.next:  lsr.w   #1,d2
        adda.w  #6144,a0
        dbra    d4,.plane
.done:  movem.l (sp)+,d0-d6/a0
        rts

; Ghost pixels come from the actual selected sprite frames, two rows/unit.
tutorial_draw_ghost:
        moveq   #0,d0
        move.b  tutorial_end,d0
        mulu.w  #3*O_SIZE,d0
        move.w  tutorial_ghost_actor,d1
        lsl.w   #3,d1
        add.w   d1,d0
        lea     game_scene_objects,a3
        adda.w  d0,a3
        lea     game_scene_images,a4
        moveq   #0,d0
        move.w  O_FRAME(a3),d0
        adda.l  d0,a4
        move.w  tutorial_ghost_row,d0
        lsl.w   #2,d0
        adda.w  d0,a4
        moveq   #1,d6
.row:   move.w  (a4)+,d5
        or.w    (a4)+,d5
        moveq   #15,d7
.pixel: btst    d7,d5
        beq     .next
        moveq   #0,d0
        move.b  O_X(a3),d0
        addi.w  #TUTORIAL_X_ORIGIN+15,d0
        sub.w   d7,d0
        moveq   #0,d1
        move.b  O_Y(a3),d1
        add.w   tutorial_ghost_row,d1
        addi.w  #TUTORIAL_Y_ORIGIN,d1
        moveq   #6,d2
        bsr     tutorial_plot
.next:  dbra    d7,.pixel
        addq.w  #1,tutorial_ghost_row
        dbra    d6,.row
        cmpi.w  #16,tutorial_ghost_row
        bne     .done
        clr.w   tutorial_ghost_row
        addq.w  #1,tutorial_ghost_actor
        cmpi.w  #3,tutorial_ghost_actor
        bne     .done
        moveq   #0,d0
        move.b  tutorial_potential_variant,d0
        eori.w  #1,d0
        move.w  d0,tutorial_render_path
        clr.w   tutorial_render_point
        move.w  #3,tutorial_render_phase
        tst.b   tutorial_trails_enabled
        bne     .done
        move.w  #4,tutorial_render_phase
.done:  rts

; One aggregate32-pixel slice, at most8 segment headers, including invisible
; points. Stationary samples must not consume a whole callback each.
tutorial_draw_paths:
        moveq   #31,d7
        moveq   #7,d6
        tst.b   tutorial_work_pending
        bne     .finished
.segment:
        tst.b   tutorial_line_active
        bne     .line
        move.w  tutorial_render_path,d0
        add.w   d0,d0
        lea     tutorial_counts,a0
        move.w  (a0,d0.w),d1
        cmp.w   tutorial_render_point,d1
        bls     .next_path
        lsl.w   #1,d0
        lea     tutorial_paths,a0
        move.l  (a0,d0.w),a0
        move.w  tutorial_render_point,d0
        lsl.w   #3,d0
        adda.w  d0,a0
        addq.w  #1,tutorial_render_point
        move.b  6(a0),d0
        andi.b  #15,d0
        beq     .header_spent
        moveq   #0,d0
        moveq   #0,d1
        move.b  2(a0),d0
        move.b  3(a0),d1
        addi.w  #TUTORIAL_X_ORIGIN,d0
        addi.w  #TUTORIAL_Y_ORIGIN,d1
        move.w  d0,tutorial_line_end_x
        move.w  d1,tutorial_line_end_y
        cmpi.w  #1,tutorial_render_point
        beq     .start
        move.b  -2(a0),d2
        andi.b  #15,d2
        beq     .start
        moveq   #0,d0
        moveq   #0,d1
        move.b  -6(a0),d0
        move.b  -5(a0),d1
        addi.w  #TUTORIAL_X_ORIGIN,d0
        addi.w  #TUTORIAL_Y_ORIGIN,d1
.start: move.w  d0,tutorial_line_x
        move.w  d1,tutorial_line_y
        move.w  tutorial_line_end_x,d2
        sub.w   d0,d2
        move.w  #1,tutorial_line_sx
        tst.w   d2
        bpl     .dx
        neg.w   d2
        move.w  #-1,tutorial_line_sx
.dx:    move.w  d2,tutorial_line_dx
        move.w  tutorial_line_end_y,d3
        sub.w   d1,d3
        move.w  #1,tutorial_line_sy
        tst.w   d3
        bpl     .dy
        neg.w   d3
        move.w  #-1,tutorial_line_sy
.dy:    neg.w   d3
        move.w  d3,tutorial_line_dy
        add.w   d3,d2
        move.w  d2,tutorial_line_error
        st      tutorial_line_active
        clr.w   tutorial_line_dash
.line:
.pixel: moveq   #6,d2
        moveq   #0,d0
        move.b  tutorial_potential_variant,d0
        cmp.w   tutorial_render_path,d0
        bne     .dash
        moveq   #15,d2
        bra     .plot
.dash:  btst    #1,tutorial_line_dash+1
        bne     .advance
.plot:  move.w  tutorial_line_x,d0
        move.w  tutorial_line_y,d1
        bsr     tutorial_plot
.advance:
        addq.w  #1,tutorial_line_dash
        move.w  tutorial_line_x,d0
        cmp.w   tutorial_line_end_x,d0
        bne     .walk
        move.w  tutorial_line_y,d0
        cmp.w   tutorial_line_end_y,d0
        beq     .segment_done
.walk:  move.w  tutorial_line_error,d4
        add.w   d4,d4
        cmp.w   tutorial_line_dy,d4
        blt     .y
        move.w  tutorial_line_dy,d0
        add.w   d0,tutorial_line_error
        move.w  tutorial_line_sx,d0
        add.w   d0,tutorial_line_x
.y:     cmp.w   tutorial_line_dx,d4
        bgt     .spent
        move.w  tutorial_line_dx,d0
        add.w   d0,tutorial_line_error
        move.w  tutorial_line_sy,d0
        add.w   d0,tutorial_line_y
.spent: dbra    d7,.pixel
        rts
.segment_done:
        clr.b   tutorial_line_active
        subq.w  #1,d7
        bmi     .done
.header_spent:
        dbra    d6,.segment
        rts
.next_path:
        moveq   #0,d0
        move.b  tutorial_potential_variant,d0
        cmp.w   tutorial_render_path,d0
        beq     .finished
        move.w  d0,tutorial_render_path
        clr.w   tutorial_render_point
        bra     .header_spent
.finished:
        move.w  #4,tutorial_render_phase
.done:  rts

tutorial_draw_text:
        ; One font row per callback, including all four explicit planes.
        moveq   #1,d4
        move.w  tutorial_text_row,d0
        bne     .menu_row
        move.l  tutorial_render_surface,a2
        adda.w  #4*32,a2
        lea     tutorial_banner_text,a0
        bsr     ui_footer_selected
        tst.b   tutorial_menu
        beq     .finished
        addq.w  #1,tutorial_text_row
        rts
.menu_row:
        move.w  d0,d1
        subq.w  #1,d1
        mulu.w  #11*32,d1
        addi.w  #132*32,d1
        move.l  tutorial_render_surface,a2
        adda.w  d1,a2
        lea     tutorial_branch_text,a0
        cmpi.w  #1,d0
        bne     .resume
        tst.b   tutorial_menu_selection
        bne     .plain
        bsr     ui_footer_selected
        bra     .next
.resume:
        lea     tutorial_resume_text,a0
        cmpi.w  #2,d0
        beq     .selection
        lea     tutorial_close_text,a0
.selection:
        subq.w  #1,d0
        cmp.b   tutorial_menu_selection,d0
        bne     .plain
        bsr     ui_footer_selected
        bra     .next
.plain: bsr     ui_footer_text
.next:  addq.w  #1,tutorial_text_row
        cmpi.w  #4,tutorial_text_row
        bcs     .done
.finished:
        move.w  #5,tutorial_render_phase
.done:  rts

; Patch only the writable building copper bank, then publish complete objects.
tutorial_patch_planes:
        movem.l d2-d3/a1-a3,-(sp)
        move.l  a0,a1
        move.l  back_copper,a2
        adda.w  #cop_bpl0h-copperlist,a2
        moveq   #3,d7
.loop:  move.l  a0,d0
        move.l  d0,d1
        swap    d1
        move.w  d1,2(a2)
        move.w  d0,6(a2)
        adda.w  #6144,a0
        adda.w  #8,a2
        dbra    d7,.loop
        ; Native HUD/status strips keep their own pointers. Every fixed court
        ; restore must resume this same surface, rather than the original court.
        lea     tutorial_court_restores,a3
        move.l  back_copper,a2
        moveq   #10,d7
.restore:
        moveq   #0,d0
        move.w  4(a3),d0
        add.l   a1,d0
        move.l  d0,d1
        swap    d1
        move.w  (a3)+,d2
        move.w  (a3)+,d3
        addq.l  #2,a3
        move.w  d1,(a2,d2.w)
        move.w  d0,(a2,d3.w)
        dbra    d7,.restore
        ; Bind the complete private footer to this same canvas identity.
        move.l  a1,d0
        lea     ui_overlay_plane,a0
        cmpi.l  #tutorial_surface0,d0
        bne.s   .footer_second
        lea     tutorial_footer0,a0
        bra.s   .footer_pointer
.footer_second:
        cmpi.l  #tutorial_surface1,d0
        bne.s   .footer_pointer
        lea     tutorial_footer1,a0
.footer_pointer:
        move.l  a0,d0
        move.l  d0,d1
        swap    d1
        move.l  back_copper,a2
        adda.w  #ui_overlay_pointer0-copperlist,a2
        moveq   #3,d7
.footer_planes:
        move.w  d1,2(a2)
        move.w  d0,6(a2)
        adda.w  #8,a2
        dbra    d7,.footer_planes
        movem.l (sp)+,d2-d3/a1-a3
        rts

; Copper high/low word offsets and the corresponding native court row/plane.
tutorial_court_restores:
        dc.w score_cop_244_hi+2-copperlist,score_cop_244_lo+2-copperlist,42*32
        dc.w score_cop_245_hi+2-copperlist,score_cop_245_lo+2-copperlist,6144+42*32
        dc.w score_cop_246_hi+2-copperlist,score_cop_246_lo+2-copperlist,12288+42*32
        dc.w score_cop_247_hi+2-copperlist,score_cop_247_lo+2-copperlist,18432+42*32
        dc.w score_cop_point_restore0_hi+2-copperlist,score_cop_point_restore0_lo+2-copperlist,64*32
        dc.w score_cop_point_restore2_hi+2-copperlist,score_cop_point_restore2_lo+2-copperlist,12288+64*32
        dc.w score_cop_point_restore3_hi+2-copperlist,score_cop_point_restore3_lo+2-copperlist,18432+64*32
        dc.w score_cop_224_hi+2-copperlist,score_cop_224_lo+2-copperlist,104*32
        dc.w score_cop_226_hi+2-copperlist,score_cop_226_lo+2-copperlist,12288+104*32
        dc.w score_cop_227_hi+2-copperlist,score_cop_227_lo+2-copperlist,18432+104*32
        dc.w score_cop_games_restore_hi+2-copperlist,score_cop_games_restore_lo+2-copperlist,6144+120*32

; Retire tutorial pointers only when a formerly private bank becomes writable.
; Displayed/queued banks remain immutable; normal banks pay only the comparison.
tutorial_restore_build_planes:
        move.l  back_copper,a0
        bsr     tutorial_copper_plane
        cmpi.l  #plane0,d0
        beq     .done
        lea     plane0,a0
        bsr     tutorial_patch_planes
.done:  rts

tutorial_publish:
        clr.l   tutorial_neutral_copper
        move.w  tutorial_render_generation,d0
        cmp.w   tutorial_build_generation,d0
        bne     tutorial_redraw
        move.l  tutorial_render_surface,a0
        bsr     tutorial_patch_planes
        bsr     tutorial_prepare_objects
        bsr     tutorial_render_objects
        jsr     complete_scene
        move.w  tutorial_render_generation,tutorial_published_generation
        clr.w   tutorial_render_phase
        tst.b   tutorial_menu
        beq     .placement
        move.l  tutorial_render_surface,tutorial_visible_surface
        clr.b   tutorial_placement_dirty
        bsr     tutorial_progress_status
        bra     .done
.placement:
        tst.b   tutorial_work_pending
        bne     .computing
        clr.b   tutorial_pending
        cmpi.w  #TUTORIAL_UNAVAILABLE,tutorial_status
        beq     .done
        move.w  #TUTORIAL_READY,tutorial_status
        bra     .done
.computing:
        move.w  #TUTORIAL_COMPUTING,tutorial_status
.done:  move.w  simulation_started_updates,tutorial_animation_callback
        rts

; Actors retain actual immutable pose/frame geometry; edit changes only XY.
tutorial_prepare_objects:
        lea     game_scene_objects,a0
        lea     tutorial_scene_objects,a1
        moveq   #64/4-1,d7
.copy:  move.l  (a0)+,(a1)+
        dbra    d7,.copy
        moveq   #0,d0
        move.b  tutorial_end,d0
        move.w  d0,d1
        mulu.w  #10,d0
        lea     game_play_state,a0
        adda.w  d0,a0
        move.b  tutorial_x,d4
        sub.b   P_X(a0),d4
        move.b  tutorial_y,d5
        sub.b   P_Y(a0),d5
        mulu.w  #3*O_SIZE,d1
        lea     tutorial_scene_objects,a1
        adda.w  d1,a1
        moveq   #2,d7
.actor: add.b   d4,O_X(a1)
        add.b   d5,O_Y(a1)
        adda.w  #O_SIZE,a1
        dbra    d7,.actor
        tst.b   tutorial_menu
        beq.s   .normal_ball
        clr.b   tutorial_scene_objects+SC_BALL+O_VISIBLE
        clr.b   tutorial_scene_objects+SC_SHADOW+O_VISIBLE
        bra     tutorial_menu_objects
.normal_ball:
        ; Until a current sample exists, retain the actual frozen ball, never
        ; an invented edited attachment or an old-generation prediction.
        tst.b   tutorial_ball_mode
        beq     .done
        clr.b   tutorial_scene_objects+SC_BALL+O_VISIBLE
        clr.b   tutorial_scene_objects+SC_SHADOW+O_VISIBLE
        move.l  tutorial_presentation_generation,d0
        cmp.l   game_preview_generation,d0
        bne     .done
        moveq   #0,d0
        move.b  tutorial_potential_variant,d0
        cmpi.b  #1,tutorial_ball_mode
        bne.s   .dense_sample
        tst.b   tutorial_marker_ready
        beq     .done
        lea     game_preview_endpoint_ready,a0
        tst.b   (a0,d0.w)
        beq     .done
        lsl.w   #3,d0
        lea     game_preview_endpoints,a0
        adda.w  d0,a0
        bra.s   .point
.dense_sample:
        add.w   d0,d0
        lea     tutorial_counts,a0
        move.w  (a0,d0.w),d1
        beq     .done
        move.w  tutorial_animation_index,d2
        cmp.w   d1,d2
        bcs     .index
        move.w  d1,d2
        subq.w  #1,d2
        move.w  d2,tutorial_animation_index
.index: lsl.w   #1,d0
        lea     tutorial_paths,a0
        move.l  (a0,d0.w),a0
        lsl.w   #3,d2
        adda.w  d2,a0
.point: move.b  2(a0),tutorial_scene_objects+SC_BALL+O_X
        move.b  3(a0),tutorial_scene_objects+SC_BALL+O_Y
        move.b  (a0),tutorial_scene_objects+SC_SHADOW+O_X
        move.b  1(a0),tutorial_scene_objects+SC_SHADOW+O_Y
        move.b  6(a0),d0
        andi.b  #15,d0
        beq     .shadow
        cmpi.b  #192,tutorial_scene_objects+SC_BALL+O_Y
        bcc     .shadow
        st      tutorial_scene_objects+SC_BALL+O_VISIBLE
        move.b  #COLOUR_WHITE,tutorial_scene_objects+SC_BALL+O_COLOUR
.shadow:
        move.b  6(a0),d0
        andi.b  #$f0,d0
        beq     .done
        cmpi.b  #192,tutorial_scene_objects+SC_SHADOW+O_Y
        bcc     .done
        st      tutorial_scene_objects+SC_SHADOW+O_VISIBLE
        move.b  #COLOUR_BLACK,tutorial_scene_objects+SC_SHADOW+O_COLOUR
.done:  rts

; Modal labels occupy viewport rows132..161. A native actor part spans
; O_Y+1..O_Y+16; hide the whole private group if a visible part intersects.
; Canonical objects and every pose/XY/frame remain unchanged.
tutorial_menu_objects:
        lea     tutorial_scene_objects,a1
        moveq   #1,d6
.group: move.l  a1,a0
        moveq   #2,d7
.part:  tst.b   O_VISIBLE(a0)
        beq.s   .next_part
        cmpi.b  #116,O_Y(a0)
        bcs.s   .next_part
        cmpi.b  #161,O_Y(a0)
        bcc.s   .next_part
        clr.b   O_VISIBLE(a1)
        clr.b   O_SIZE+O_VISIBLE(a1)
        clr.b   2*O_SIZE+O_VISIBLE(a1)
        bra.s   .next_group
.next_part:
        adda.w  #O_SIZE,a0
        dbra    d7,.part
.next_group:
        adda.w  #3*O_SIZE,a1
        dbra    d6,.group
        rts

tutorial_render_objects:
        movem.l d0-d7/a0-a4,-(sp)
        move.l  #tutorial_scene_objects,tutorial_sprite_source
        move.b  #2,tutorial_scene_layer
        jmp     game_render_prepared_scene

tutorial_animate:
        bsr     tutorial_animation_due
        tst.l   d0
        beq     .done
        moveq   #0,d0
        move.b  tutorial_potential_variant,d0
        add.w   d0,d0
        lea     tutorial_counts,a0
        move.w  (a0,d0.w),d1
        beq     .done
        subq.w  #1,d1
        cmp.w   tutorial_animation_index,d1
        bhi.s   .advance
        ; Last available sample is not terminal while the dense worker runs.
        moveq   #0,d0
        move.b  tutorial_potential_variant,d0
        add.w   d0,d0
        lea     tutorial_available_outcomes,a0
        tst.w   (a0,d0.w)
        beq     .done
        cmpi.w  #PREVIEW_NO_CONTACT,(a0,d0.w)
        bhi     .done ; incomplete limits and lifecycle waits do not loop
        ; Replay the completed immutable potential, without new simulation,
        ; input consumption or RNG. A partial prefix never wraps.
        clr.w   tutorial_animation_index
        move.w  simulation_started_updates,tutorial_animation_callback
        move.b  #2,tutorial_ball_mode
        bra     .sample
.advance:
        ; Advance the nominal cursor, rather than adopting late callback entry
        ; time. A delayed publication catches up without accumulating drift.
        move.w  simulation_started_updates,d2
        move.w  d2,d3
        sub.w   tutorial_animation_callback,d3
        move.w  d2,tutorial_animation_callback
        move.b  #2,tutorial_ball_mode
        add.w   d3,tutorial_animation_index
        cmp.w   tutorial_animation_index,d1
        bhi     .sample
        move.w  d1,tutorial_animation_index
        move.w  simulation_started_updates,tutorial_animation_callback
.sample:
        clr.l   tutorial_neutral_copper
        move.l  tutorial_visible_surface,a0
        bsr     tutorial_patch_planes
        bsr     tutorial_prepare_objects
        bsr     tutorial_render_objects
        jsr     complete_scene
.done:  rts

; Cheap query; the scheduler admits actual publication separately.
tutorial_animation_due:
        tst.b   tutorial_animation_ready
        beq     .no
        tst.b   tutorial_menu
        bne     .no
        moveq   #0,d0
        move.w  simulation_started_updates,d0
        sub.w   tutorial_animation_callback,d0
        cmpi.w  #1,d0
        bcs     .no
        moveq   #0,d0
        move.b  tutorial_potential_variant,d0
        add.w   d0,d0
        lea     tutorial_counts,a0
        move.w  (a0,d0.w),d1
        beq     .no
        subq.w  #1,d1
        cmp.w   tutorial_animation_index,d1
        bhi.s   .yes
        lea     tutorial_available_outcomes,a0
        move.w  (a0,d0.w),d1
        beq.s   .no
        cmpi.w  #PREVIEW_NO_CONTACT,d1
        bhi.s   .no
.yes:   moveq   #1,d0
        rts
.no:    moveq   #0,d0
        rts

tutorial_restore_court:
        clr.l   tutorial_neutral_copper
        lea     plane0,a0
        bsr     tutorial_patch_planes
        jsr     game_render_sprites
        jmp     complete_scene

tutorial_empty_text: dc.b 'UNAVAILABLE - RESUME FROM MENU',0
tutorial_title_text: dc.b 'Tutorial',0
tutorial_banner_text: dc.b 'TUTORIAL',0
tutorial_keyboard_controls_text: dc.b 'AUTO WASD F ACTION G MENU',0
tutorial_pad_controls_text: dc.b 'AUTO PAD B1 ACTION B2 MENU',0
tutorial_computing_detail_text: dc.b 'CALCULATING PATHS',0
tutorial_close_hint_text: dc.b 'G/B2 CLOSE  RESUME ORIGINAL',0
        even
tutorial_controls_texts:
        dc.l tutorial_keyboard_controls_text,tutorial_pad_controls_text
        dc.l tutorial_menu_text,tutorial_computing_detail_text,tutorial_close_hint_text
tutorial_computing_text: dc.b 'TUTORIAL - CALCULATING PATHS',0
tutorial_hint_text: dc.b 'TUTORIAL F RELEASED / WASD / G',0
tutorial_held_hint_text: dc.b 'TUTORIAL F HELD / WASD / G MENU',0
tutorial_joystick_hint_text: dc.b 'TUTORIAL B1 RELEASED / B2 MENU',0
tutorial_joystick_held_hint_text: dc.b 'TUTORIAL B1 HELD / MOVE / B2',0
tutorial_unavailable_text: dc.b 'NO CURRENT HUMAN SERVE CONTEXT',0
tutorial_menu_text: dc.b 'UP/DOWN SELECT - F/ENTER OK',0
tutorial_wait_hint_text: dc.b 'AUTO SERVE: NEXT F/B1 PRESS',0
tutorial_other_pending_text: dc.b 'TUTORIAL: OTHER PATH CALCULATING',0
tutorial_count_text: dc.b '1/1  CURRENT SERVE',0
tutorial_branch_text: dc.b 'PLAY FROM HERE (NOT READY)',0
tutorial_resume_text: dc.b 'RESUME LATEST',0
tutorial_close_text: dc.b 'CLOSE MENU',0
tutorial_landing_text: dc.b 'LANDING - ACTUAL GAME PATH',0
tutorial_net_text: dc.b 'NET - ACTUAL GAME PATH',0
tutorial_out_text: dc.b 'OUT - ACTUAL GAME PATH',0
tutorial_intercept_text: dc.b 'OPPONENT CONTACT',0
tutorial_miss_text: dc.b 'NO CONTACT - NO OUTGOING SHOT',0
tutorial_limit_text: dc.b 'CALCULATION LIMIT - INCOMPLETE',0
tutorial_wait_text: dc.b 'RELEASED - WAITING TO SERVE',0
tutorial_lifecycle_text: dc.b 'GAME TRANSITION - PATH STOPPED',0
        even
tutorial_outcome_texts:
        dc.l tutorial_landing_text,tutorial_net_text,tutorial_out_text
        dc.l tutorial_intercept_text,tutorial_miss_text,tutorial_limit_text
        dc.l tutorial_lifecycle_text


; Current actual result plus the future serve action represented by autoplay.
tutorial_serve_press_landing: dc.b 'NEXT F/B1 PRESS: LANDING',0
tutorial_serve_press_net: dc.b 'NEXT F/B1 PRESS: NET',0
tutorial_serve_press_out: dc.b 'NEXT F/B1 PRESS: OUT',0
tutorial_serve_press_contact: dc.b 'NEXT F/B1 PRESS: CONTACT',0
tutorial_serve_press_miss: dc.b 'NEXT F/B1 PRESS: NO CONTACT',0
tutorial_serve_press_limit: dc.b 'NEXT F/B1 PRESS: INCOMPLETE',0
tutorial_serve_press_lifecycle: dc.b 'NEXT F/B1 PRESS: TRANSITION',0
tutorial_serve_held_landing: dc.b 'F/B1 HELD SERVE: LANDING',0
tutorial_serve_held_net: dc.b 'F/B1 HELD SERVE: NET',0
tutorial_serve_held_out: dc.b 'F/B1 HELD SERVE: OUT',0
tutorial_serve_held_contact: dc.b 'F/B1 HELD SERVE: CONTACT',0
tutorial_serve_held_miss: dc.b 'F/B1 HELD SERVE: NO CONTACT',0
tutorial_serve_held_limit: dc.b 'F/B1 HELD SERVE: INCOMPLETE',0
tutorial_serve_held_lifecycle: dc.b 'F/B1 HELD SERVE: TRANSITION',0
        even
tutorial_serve_press_outcomes:
        dc.l tutorial_serve_press_landing,tutorial_serve_press_net,tutorial_serve_press_out
        dc.l tutorial_serve_press_contact,tutorial_serve_press_miss,tutorial_serve_press_limit
        dc.l tutorial_serve_press_lifecycle
tutorial_serve_held_outcomes:
        dc.l tutorial_serve_held_landing,tutorial_serve_held_net,tutorial_serve_held_out
        dc.l tutorial_serve_held_contact,tutorial_serve_held_miss,tutorial_serve_held_limit
        dc.l tutorial_serve_held_lifecycle
