; Presentation consumes only completed public preview yields. No core bodies,
; canonical edits, timer writes or physics calculations belong in these hooks.

; Call after accepting a new request, before any renderer can inspect old paths.
; Publication itself is deferred to an admitted presentation slice.
tutorial_progress_reset:
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

; Call ONLY after game_preview_step has returned and restored selected318/all72.
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
        move.b  tutorial_active_variant,d0
        add.w   d0,d0
        lea     tutorial_available_outcomes,a0
        move.w  (a0,d0.w),d1
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
        tst.w   d1
        beq     .hide
        ; Nonzero outcome means this alternative stopped. LIMIT remains
        ; incomplete, NO_CONTACT has no fabricated outgoing landing marker.
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
        move.b  tutorial_active_variant,d2
        lea     game_preview_launches,a0
        tst.b   (a0,d2.w)
        beq     .hide
        lea     tutorial_available_counts,a0
        tst.w   (a0,d0.w)
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
        clr.b   tutorial_ball_mode
        clr.b   tutorial_animation_ready
        clr.l   tutorial_animation_generation
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
        lea     plane0,a0
        bsr     tutorial_patch_planes
        bsr     tutorial_prepare_objects
        bsr     tutorial_render_objects
        jsr     complete_scene
        move.l  #plane0,tutorial_visible_surface
        move.l  last_timer_count,tutorial_animation_time
        move.w  tutorial_render_generation,tutorial_published_generation
        clr.b   tutorial_placement_dirty
        bsr     tutorial_progress_status
        bsr     tutorial_footer
.done:  rts

