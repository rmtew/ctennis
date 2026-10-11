; Presentation consumes only completed public preview yields. No core bodies,
; canonical edits, timer writes or physics calculations belong in these hooks.

; Call after accepting a new request, before any renderer can inspect old paths.
; Publication itself is deferred to an admitted presentation slice.
tutorial_progress_reset:
        bsr     tutorial_footer_invalidate
        addq.w  #1,tutorial_render_generation
        move.l  tutorial_generation,tutorial_presentation_generation
        clr.l   tutorial_marker_generation
        clr.l   tutorial_animation_generation
        clr.l   tutorial_available_counts
        clr.l   tutorial_available_outcomes
        clr.l   tutorial_counts
        clr.l   tutorial_outcomes
        clr.w   tutorial_animation_index
        clr.w   tutorial_render_phase
        clr.b   tutorial_line_active
        clr.b   tutorial_ball_mode
        clr.b   tutorial_waiting_ready
        clr.b   tutorial_placement_ready
        clr.b   tutorial_marker_ready
        clr.b   tutorial_animation_ready
        st      tutorial_placement_dirty
        rts

; Call after a successful public step or READY result has returned. Public
; steps have restored selected318/all72; READY results contain complete counts.
; PRIME-or-later has a resolved immutable prefix; RESOLVE can reset its prefix
; and is intentionally not exposed. Thereafter this generation only appends.
; Preserve scheduler D5/D6 and every other caller register.
tutorial_progress_returned:
        movem.l d0-d4/a0-a1,-(sp)
        move.l  tutorial_presentation_generation,d0
        cmp.l   tutorial_generation,d0
        bne     .done
        cmp.l   game_preview_generation,d0
        bne     .done
        cmpi.w  #PREVIEW_PRIME,game_preview_status
        bcs     .done
        cmpi.w  #PREVIEW_READY,game_preview_status
        bhi     .done
        cmpi.w  #PREVIEW_POINTS,game_preview_counts
        bhi     .done
        cmpi.w  #PREVIEW_POINTS,game_preview_counts+2
        bhi     .done
        move.l  game_preview_counts,d0
        cmp.l   tutorial_available_counts,d0
        beq     .outcomes
        ; Playback pauses at an exhausted immutable prefix. Newly appended
        ; samples start from this return, without accumulating unseen wait time.
        moveq   #0,d2
        move.b  tutorial_potential_variant,d2
        add.w   d2,d2
        lea     tutorial_available_counts,a0
        move.w  (a0,d2.w),d3
        lea     game_preview_counts,a0
        cmp.w   (a0,d2.w),d3
        bcc.s   .counts
        tst.w   d3
        beq.s   .rebase
        subq.w  #1,d3
        cmp.w   tutorial_animation_index,d3
        bne.s   .counts
.rebase:
        move.w  simulation_started_updates,tutorial_animation_callback
.counts:
        move.l  d0,tutorial_available_counts
        move.l  d0,tutorial_counts
.outcomes:
        move.l  game_preview_outcomes,d0
        move.l  d0,tutorial_available_outcomes
        move.l  d0,tutorial_outcomes
        move.l  #game_preview_paths,tutorial_paths
        move.l  #game_preview_paths+PREVIEW_POINTS*PREVIEW_POINT_BYTES,tutorial_paths+4
.placement:
        bsr     tutorial_progress_qualify
.done:  movem.l (sp)+,d0-d4/a0-a1
        rts

; Re-evaluate current observed variant; F choice is presentation, not new rules.
tutorial_progress_variant_changed:
        movem.l d0-d4/a0-a1,-(sp)
        addq.w  #1,tutorial_render_generation
        clr.w   tutorial_animation_index
        clr.w   tutorial_render_phase
        clr.b   tutorial_line_active
        st      tutorial_placement_dirty
        clr.b   tutorial_waiting_ready
        clr.b   tutorial_placement_ready
        clr.b   tutorial_marker_ready
        clr.b   tutorial_ball_mode
        bsr     tutorial_progress_qualify
        movem.l (sp)+,d0-d4/a0-a1
        rts

tutorial_progress_qualify:
        move.b  tutorial_waiting_ready,d3
        moveq   #0,d0
        move.b  tutorial_potential_variant,d0
        add.w   d0,d0
        lea     tutorial_available_outcomes,a0
        move.w  (a0,d0.w),d1
        bne.s   .qualified_outcome
        moveq   #0,d2
        move.b  tutorial_potential_variant,d2
        lea     game_preview_endpoint_ready,a0
        tst.b   (a0,d2.w)
        beq.s   .qualified_outcome
        lea     game_preview_endpoint_outcomes,a0
        move.w  (a0,d0.w),d1
.qualified_outcome:
        tst.b   tutorial_placement_ready
        bne     .observed
        tst.w   d1
        beq     .observed
        st      tutorial_placement_dirty
.observed:
        clr.b   tutorial_waiting_ready
        clr.b   tutorial_placement_ready
        clr.b   tutorial_marker_ready
        clr.b   tutorial_animation_ready
        clr.l   tutorial_marker_generation
        clr.l   tutorial_animation_generation
        ; Actual available samples qualify playback independently of a terminal
        ; outcome. Waiting/computing still cannot qualify a landing marker.
        lea     tutorial_available_counts,a0
        cmpi.w  #2,(a0,d0.w)
        bcs.s   .no_samples
        st      tutorial_animation_ready
        move.l  tutorial_presentation_generation,tutorial_animation_generation
.no_samples:
        tst.w   d1
        beq     .hide
        ; A queried endpoint can be ready while dense work continues. LIMIT
        ; remains incomplete; NO_CONTACT has no outgoing landing marker.
        st      tutorial_placement_ready
        lea     tutorial_available_counts,a0
        cmpi.w  #2,(a0,d0.w)
        bcs     .marker
        st      tutorial_animation_ready
        move.l  tutorial_presentation_generation,tutorial_animation_generation
.marker:
        cmpi.w  #PREVIEW_INTERCEPTION,d1
        bhi     .hide
        moveq   #0,d2
        move.b  tutorial_potential_variant,d2
        lea     game_preview_launches,a0
        tst.b   (a0,d2.w)
        beq     .hide
        lea     game_preview_endpoint_ready,a0
        tst.b   (a0,d2.w)
        beq     .hide
        st      tutorial_marker_ready
        move.l  tutorial_presentation_generation,tutorial_marker_generation
        cmpi.b  #2,tutorial_ball_mode
        beq     .status
        move.b  #1,tutorial_ball_mode
        bra     .status
.hide:
        tst.b   tutorial_animation_ready
        bne     .status ; an actual wait/no-contact loop is not an endpoint
        clr.b   tutorial_ball_mode
.status:
        bsr     tutorial_released_wait
        tst.l   d0
        beq     .not_waiting
        st      tutorial_waiting_ready
        tst.b   d3
        bne     .not_waiting
        st      tutorial_placement_dirty
.not_waiting:
        bra     tutorial_progress_status

; Legacy status/pending describe latest placement, never idle trail completion.
tutorial_progress_status:
        cmpi.w  #TUTORIAL_UNAVAILABLE,tutorial_status
        beq     .done
        tst.b   tutorial_placement_dirty
        bne     .pending
        tst.b   tutorial_waiting_ready
        beq     .endpoint
        move.w  #TUTORIAL_WAITING,tutorial_status
        clr.b   tutorial_pending
        rts
.endpoint:
        tst.b   tutorial_placement_ready
        beq     .pending
        tst.b   tutorial_placement_dirty
        bne     .pending
        move.w  #TUTORIAL_READY,tutorial_status
        clr.b   tutorial_pending
        rts
.pending:
        move.w  #TUTORIAL_COMPUTING,tutorial_status
        st      tutorial_pending
.done:  rts

; Root scheduler calls one admitted presentation slice, independently of physics.
; Fast placement has priority; no trail passes are scheduled.
tutorial_progress_slice:
        tst.b   tutorial_active
        beq     .done
        tst.b   tutorial_menu
        beq     .placement
        tst.w   tutorial_render_phase
        bne     tutorial_render
.placement:
        tst.b   tutorial_placement_dirty
        bne     tutorial_progress_fast_publish
        bra     tutorial_animate
.done:  rts

; Original court is immutable. This clears old-generation chords immediately
; without a canvas copy and prepares the latest test actor from selected poses.
; No old count/path is consulted while reset has ball_mode0.
tutorial_progress_fast_publish:
        move.l  tutorial_presentation_generation,d0
        cmp.l   game_preview_generation,d0
        beq     .publish
        ; Even rejected/canceled work must remove old markers for the new XY.
        ; In this path no sample payload is read at all.
        clr.b   tutorial_ball_mode
        clr.b   tutorial_marker_ready
        clr.b   tutorial_animation_ready
        clr.l   tutorial_marker_generation
        clr.l   tutorial_animation_generation
        clr.l   tutorial_counts
.publish:
        bsr     tutorial_pending_canvas_eligible
        tst.l   d0
        beq.s   .private_canvas
        move.l  a1,tutorial_render_surface
        move.w  tutorial_render_generation,tutorial_build_generation
        bra.s   .complete_objects
.private_canvas:
        bsr     tutorial_choose_surface
        tst.l   d0
        beq     .done
        bsr     tutorial_closed_canvas_rank
        cmpi.l  #2,d0
        beq.s   .prepared_landing
        bsr     tutorial_restore_landing
        bsr     tutorial_prepare_menu_roi
        bsr     tutorial_draw_landing
.prepared_landing:
        bsr     tutorial_prepare_private_footer
.complete_objects:
        move.l  tutorial_render_surface,a0
        bsr     tutorial_patch_planes
        bsr     tutorial_prepare_objects
        bsr     tutorial_render_objects
        ; Bind neutrality to this actual completed sprite/Copper bank, rather
        ; than inferring queued content from later mutable presentation state.
        ; An IRQ before complete_scene can only make the pointer comparison
        ; conservative; no consumer uses this descriptor to mutate the bank.
        clr.l   tutorial_neutral_copper
        move.l  tutorial_render_surface,a1
        bsr     tutorial_neutral_canvas_eligible
        tst.l   d0
        beq.s   .classified_bank
        move.l  back_copper,tutorial_neutral_copper
.classified_bank:
        jsr     complete_scene
        move.l  tutorial_render_surface,tutorial_visible_surface
        move.w  simulation_started_updates,tutorial_animation_callback
        move.w  tutorial_render_generation,tutorial_published_generation
        clr.b   tutorial_placement_dirty
        clr.w   tutorial_render_phase
        bsr     tutorial_progress_status
        bsr     tutorial_footer_select
        move.l  tutorial_generation,d0
        cmp.l   tutorial_footer_stage_generation,d0
        bne.s   .footer_changed
        cmp.l   tutorial_footer_first,d6
        bne.s   .footer_changed
        cmpa.l  tutorial_footer_second,a0
        bne.s   .footer_changed
        clr.b   tutorial_footer_dirty
        bra.s   .done
.footer_changed:
        st      tutorial_footer_dirty
.done:  rts

