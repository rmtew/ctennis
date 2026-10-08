; Two private court surfaces. Displayed/queued surfaces are never writable.
; XY offsets are the existing sprite origins minus the native display origins.
TUTORIAL_X_ORIGIN equ $a0-$81
TUTORIAL_Y_ORIGIN equ $2d-$2c

tutorial_redraw:
        addq.w  #1,tutorial_render_generation
        st      tutorial_pending
        move.w  #1,tutorial_render_phase
        clr.l   tutorial_render_offset
        clr.b   tutorial_line_active
        clr.w   tutorial_text_row
        bsr     tutorial_footer
        rts

tutorial_footer:
        lea     ui_overlay_plane,a1
        moveq   #0,d0
        move.w  #512/4-1,d1
.clear: move.l  d0,(a1)+
        dbra    d1,.clear
        lea     tutorial_computing_text,a0
        tst.b   tutorial_work_pending
        bne     .text
        lea     tutorial_hint_text,a0
        tst.b   tutorial_active_variant
        bne     .keyboard_hint
        lea     tutorial_held_hint_text,a0
.keyboard_hint:
        tst.b   tutorial_input_source
        bne     .hint_ready
        lea     tutorial_joystick_hint_text,a0
        tst.b   tutorial_active_variant
        bne     .hint_ready
        lea     tutorial_joystick_held_hint_text,a0
.hint_ready:
        cmpi.w  #TUTORIAL_UNAVAILABLE,tutorial_status
        bne     .menu
        lea     tutorial_unavailable_text,a0
.menu:  tst.b   tutorial_menu
        beq     .text
        lea     tutorial_menu_text,a0
.text:  lea     ui_overlay_plane,a2
        moveq   #0,d4
        bsr     ui_footer_selected
        lea     tutorial_count_text,a0
        tst.b   tutorial_work_pending
        bne     .count_ready
        moveq   #0,d0
        move.b  tutorial_active_variant,d0
        add.w   d0,d0
        lea     tutorial_outcomes,a1
        move.w  (a1,d0.w),d1
        beq     .count_ready
        cmpi.w  #PREVIEW_LIFECYCLE,d1
        bhi     .count_ready
        subq.w  #1,d1
        lsl.w   #2,d1
        lea     tutorial_outcome_texts,a1
        move.l  (a1,d1.w),a0
        cmpi.w  #TUTORIAL_UNAVAILABLE,tutorial_status
        bne     .count_ready
        lea     tutorial_empty_text,a0
.count_ready:
        lea     ui_overlay_plane+256,a2
        bsr     ui_footer_text
        rts

tutorial_render:
        bsr     tutorial_work_admitted
        tst.l   d0
        beq     .done
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
.done:  rts

; Read the actual displayed/queued first bitplane from their copper banks.
tutorial_copper_plane:
        moveq   #0,d0
        move.w  cop_bpl0h+2-copperlist(a0),d0
        swap    d0
        move.w  cop_bpl0h+6-copperlist(a0),d0
        rts

tutorial_choose_surface:
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
        moveq   #1,d0
        rts
.busy:  moveq   #0,d0
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

; Ghost pixels come from the actual selected sprite frames, two rows/callback.
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
        move.b  tutorial_active_variant,d0
        eori.w  #1,d0
        move.w  d0,tutorial_render_path
        clr.w   tutorial_render_point
        move.w  #3,tutorial_render_phase
.done:  rts

; One segment per callback, at most32 raster pixels; continuation is explicit.
tutorial_draw_paths:
        tst.b   tutorial_work_pending
        bne     .finished
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
        beq     .done
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
        bpl     .dx
        neg.w   d2
        move.w  #-1,tutorial_line_sx
.dx:    move.w  d2,tutorial_line_dx
        move.w  tutorial_line_end_y,d3
        sub.w   d1,d3
        move.w  #1,tutorial_line_sy
        bpl     .dy
        neg.w   d3
        move.w  #-1,tutorial_line_sy
.dy:    neg.w   d3
        move.w  d3,tutorial_line_dy
        add.w   d3,d2
        move.w  d2,tutorial_line_error
        st      tutorial_line_active
        clr.w   tutorial_line_dash
.line:  moveq   #31,d7
.pixel: moveq   #6,d2
        moveq   #0,d0
        move.b  tutorial_active_variant,d0
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
        rts
.next_path:
        moveq   #0,d0
        move.b  tutorial_active_variant,d0
        cmp.w   tutorial_render_path,d0
        beq     .finished
        move.w  d0,tutorial_render_path
        clr.w   tutorial_render_point
        rts
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
        addi.w  #90*32,d1
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
        rts

tutorial_publish:
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
        tst.b   tutorial_work_pending
        bne     .computing
        clr.b   tutorial_pending
        cmpi.w  #TUTORIAL_UNAVAILABLE,tutorial_status
        beq     .done
        move.w  #TUTORIAL_READY,tutorial_status
        bra     .done
.computing:
        move.w  #TUTORIAL_COMPUTING,tutorial_status
.done:  move.l  last_timer_count,tutorial_animation_time
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
        clr.b   tutorial_scene_objects+SC_BALL+O_VISIBLE
        clr.b   tutorial_scene_objects+SC_SHADOW+O_VISIBLE
        moveq   #0,d0
        move.b  tutorial_active_variant,d0
        add.w   d0,d0
        lea     tutorial_counts,a0
        move.w  (a0,d0.w),d1
        beq     .done
        move.w  tutorial_animation_index,d2
        cmp.w   d1,d2
        bcs     .index
        clr.w   d2
        clr.w   tutorial_animation_index
.index: lsl.w   #1,d0
        lea     tutorial_paths,a0
        move.l  (a0,d0.w),a0
        lsl.w   #3,d2
        adda.w  d2,a0
        move.b  2(a0),tutorial_scene_objects+SC_BALL+O_X
        move.b  3(a0),tutorial_scene_objects+SC_BALL+O_Y
        move.b  (a0),tutorial_scene_objects+SC_SHADOW+O_X
        move.b  1(a0),tutorial_scene_objects+SC_SHADOW+O_Y
        move.b  6(a0),d0
        andi.b  #15,d0
        beq     .shadow
        st      tutorial_scene_objects+SC_BALL+O_VISIBLE
        move.b  #COLOUR_WHITE,tutorial_scene_objects+SC_BALL+O_COLOUR
.shadow:
        move.b  6(a0),d0
        andi.b  #$f0,d0
        beq     .done
        st      tutorial_scene_objects+SC_SHADOW+O_VISIBLE
        move.b  #COLOUR_BLACK,tutorial_scene_objects+SC_SHADOW+O_COLOUR
.done:  rts

tutorial_render_objects:
        movem.l d0-d7/a0-a4,-(sp)
        move.l  #tutorial_scene_objects,tutorial_sprite_source
        move.b  #2,tutorial_scene_layer
        jmp     game_render_prepared_scene

tutorial_animate:
        cmpi.w  #TUTORIAL_READY,tutorial_status
        bne     .done
        tst.b   tutorial_menu
        bne     .done
        move.l  tutorial_animation_time,d0
        sub.l   last_timer_count,d0
        move.l  simulation_interval_whole,d1
        add.l   d1,d1
        cmp.l   d1,d0
        bcs     .done
        move.l  last_timer_count,tutorial_animation_time
        addq.w  #2,tutorial_animation_index
        move.l  tutorial_render_surface,a0
        bsr     tutorial_patch_planes
        bsr     tutorial_prepare_objects
        bsr     tutorial_render_objects
        jsr     complete_scene
.done:  rts

tutorial_restore_court:
        lea     plane0,a0
        bsr     tutorial_patch_planes
        jsr     game_render_sprites
        jmp     complete_scene

tutorial_empty_text: dc.b 'UNAVAILABLE - RESUME FROM MENU',0
tutorial_title_text: dc.b 'Tutorial',0
tutorial_banner_text: dc.b 'TUTORIAL',0
tutorial_computing_text: dc.b 'COMPUTING - PLEASE WAIT',0
tutorial_hint_text: dc.b 'WASD MOVE  F RELEASED  G MENU',0
tutorial_held_hint_text: dc.b 'WASD MOVE  F HELD  G MENU',0
tutorial_joystick_hint_text: dc.b 'MOVE TEST  B1 RELEASED  B2 MENU',0
tutorial_joystick_held_hint_text: dc.b 'MOVE TEST  B1 HELD  B2 MENU',0
tutorial_unavailable_text: dc.b 'NO CURRENT HUMAN SERVE CONTEXT',0
tutorial_menu_text: dc.b 'UP/DOWN SELECT - F/ENTER OK',0
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
tutorial_lifecycle_text: dc.b 'GAME TRANSITION - PATH STOPPED',0
        even
tutorial_outcome_texts:
        dc.l tutorial_landing_text,tutorial_net_text,tutorial_out_text
        dc.l tutorial_intercept_text,tutorial_miss_text,tutorial_limit_text
        dc.l tutorial_lifecycle_text

