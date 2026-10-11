        section code,code
        include "amiga/game/core_trace_macros.i"
; Accepted PAL E-clock cadence:11838+14906/65536 ticks at709379Hz.
; Retain fractional phase instead of rounding every update down.
SIM_INTERVAL_WHOLE equ 11838
SIM_INTERVAL_FRACTION equ 14906
; NTSC interval rounded to16 fractional bits:PAL interval*715909/709379.
NTSC_INTERVAL_WHOLE equ 11947
NTSC_INTERVAL_FRACTION equ 13180
; exec/execbase.i: readable UBYTE, available before the V36 additions.
EXEC_VBLANK_FREQUENCY equ $212
; Shortest supported OCS fields, zero-based last line.
PAL_LAST_LINE equ 311
NTSC_LAST_LINE equ 261
PRESENTATION_GUARD_LINES equ 4

start:
        ; DOS enters on its task stack. Finish all OS scheduling calls there,
        ; then own the machine and use a bounded application stack forever.
        move.l  a6,-(sp)
        move.l  4.w,a6
        bsr     select_video_standard
        tst.l   d0
        beq.s   .video_selected
        move.l  (sp)+,a6
        rts                     ; RETURN_FAIL, before any machine takeover
.video_selected:
        addq.l  #4,sp
        move.l  sp,dos_entry_sp
        jsr     -132(a6) ; Exec Forbid
        jsr     -120(a6) ; Exec Disable
        jsr     -150(a6) ; Exec SuperState before owning the interrupt vector
        lea     game_stack_top,sp
        bsr     init_square_score_banks
        bsr     game_core_init
        lea     game_history_buffer,a0
        move.l  #HISTORY_BUFFER_BYTES,d0
        bsr     game_history_attach
        bsr     game_begin_title
        ifd CORE_TRACE
        lea     pointer_sources,a0
        lea     pointer_targets,a1
        else
        lea     pointer_sources,a0
        lea     pointer_targets,a1
        endif
        moveq   #11,d7
patch_pointers:
        move.l  (a0)+,d0
        move.l  (a1)+,a2
        move.l  d0,d1
        swap    d1
        move.w  d1,(a2)
        move.w  d0,4(a2)
        dbra    d7,patch_pointers
        bsr     patch_score_pointers
        lea     ui_overlay_pointer0+2,a2
        move.l  #ui_overlay_plane,d0
        moveq   #3,d7
ui_init_overlay:
        move.l  d0,d1
        swap    d1
        move.w  d1,(a2)
        move.w  d0,4(a2)
        addq.l  #8,a2
        dbra    d7,ui_init_overlay
        lea     copperlist,a0
        lea     copperlist_back,a1
        move.w  #(copperlist_end-copperlist)/2-1,d7
copy_back_copper:
        move.w  (a0)+,(a1)+
        dbra    d7,copy_back_copper
        lea     copperlist,a0
        lea     copperlist_third,a1
        move.w  #(copperlist_end-copperlist)/2-1,d7
copy_third_copper:
        move.w  (a0)+,(a1)+
        dbra    d7,copy_third_copper
        move.l  #copperlist,front_copper
        move.l  #copperlist_back,back_copper
        move.l  #copperlist_third,spare_copper
        bsr     select_build_bank
        ; Initialize the spare's pointer/cache descriptors during startup too.
        ; First completed update must not pay region-pointer/bitmap initialization.
        move.l  back_copper,-(sp)
        move.l  spare_copper,back_copper
        bsr     select_build_bank
        move.l  (sp)+,back_copper
        bsr     select_build_bank
        lea     $dff000,a0
        move.w  #$7fff,$09a(a0)
        move.w  #$7fff,$09c(a0)
        move.l  #presentation_interrupt,$6c.w
        move.w  #$7fff,$096(a0)
        bsr     prepare_title_display
        move.l  #title_copper,presentation_copper
        move.l  #title_copper,$080(a0)
        move.w  #$8380,$096(a0)
        move.w  #0,$088(a0)
        move.b  #$7f,$bfed01
        bclr    #6,$bfee01
        bsr     game_init_controls
        bsr     paula_tone_init
        bsr     tutorial_init
        ; CIA-B A is the low E-clock word; B counts A underflows.
        ; Start the high word first, so the continuous epoch loses no carry.
        move.b  #0,$bfde00
        move.b  #0,$bfdf00
        move.b  #$ff,$bfd400
        move.b  #$ff,$bfd500
        move.b  #$ff,$bfd600
        move.b  #$ff,$bfd700
        move.b  #$50,$bfdf00
        move.b  #$51,$bfdf00
        move.b  #$10,$bfde00
        move.b  #$01,$bfde00
        bsr     read_sim_timer
        move.l  d0,last_timer_count
        move.w  d0,simulation_timer_origin
        st      simulation_timer_running
        ; Copper requests level3 at253, after every outgoing consumer retires.
        move.w  #$c010,$dff09a
        andi.w  #$f8ff,sr
main_loop:
        bsr     game_poll_keyboard
        bsr     poll_presentation
        bsr     account_sim_timer
        move.l  simulation_phase,d0
        cmp.l   simulation_interval,d0
        bcs.s   main_loop
        sub.l   simulation_interval,d0
        move.l  d0,simulation_phase
        move.l  simulation_interval_whole,simulation_interval
        move.w  simulation_interval_fraction,d1
        add.w   d1,simulation_fraction
        bcc.s   simulation_interval_ready
        addq.l  #1,simulation_interval
simulation_interval_ready:
        bsr     simulation_update
        bra     main_loop

; Stable high/low/high read of the cascaded down-counter. Retry if either
; byte of B or the A->B carry changes during the read.
read_sim_timer:
read_sim_timer_again:
        moveq   #0,d0
        move.b  $bfd700,d0
        lsl.w   #8,d0
        move.b  $bfd600,d0
        move.w  d0,d2
        swap    d0
        move.b  $bfd500,d0
        lsl.w   #8,d0
        move.b  $bfd400,d0
        move.w  d0,d3
        move.b  $bfd500,d1
        lsr.w   #8,d0
        cmp.b   d0,d1
        bne.s   read_sim_timer_again
        move.w  d3,d0
        moveq   #0,d1
        move.b  $bfd700,d1
        lsl.w   #8,d1
        move.b  $bfd600,d1
        cmp.w   d1,d2
        bne.s   read_sim_timer_again
        rts

account_sim_timer:
        bsr     read_sim_timer
        move.l  last_timer_count,d1
        move.l  d0,last_timer_count
        sub.l   d0,d1
        add.l   d1,simulation_phase
        rts

; Construction yields to the real clock and keyboard between bounded planes.
; Never dispatch gameplay or publish a partially completed scene here.
ui_construction_sample:
        tst.b   simulation_timer_running
        beq.s   .done
        movem.l d0-d7/a0-a6,-(sp)
        bsr     account_sim_timer
        bsr     game_poll_keyboard
        movem.l (sp)+,d0-d7/a0-a6
.done:  rts

; Read a coherent nine-bit physical beam line. A68000 longword custom read
; is two bus transfers, not an atomic beam snapshot. Retry a changed high bit.
read_presentation_line:
        move.w  $dff004,d0
        andi.w  #1,d0
        move.w  $dff006,d1
        move.w  $dff004,d2
        andi.w  #1,d2
        cmp.w   d0,d2
        bne.s   read_presentation_line
        lsl.w   #8,d0
        lsr.w   #8,d1
        or.w    d1,d0
        rts

; Read the OS standard once while Exec is available. Kickstart1.3 exposes
; VBlankFrequency; EClockFrequency is a later addition. Fixed OCS PAL/NTSC
; bounds avoid depending on transient beam readback during startup.
; A6=ExecBase; D0=0 on success, DOS RETURN_FAIL (20) if unsupported.
; Invalid values leave timing state untouched and return before takeover.
select_video_standard:
        moveq   #0,d0
        move.b  EXEC_VBLANK_FREQUENCY(a6),d0
        cmpi.b  #50,d0
        beq.s   .pal
        cmpi.b  #60,d0
        bne.s   .unsupported
        move.w  #NTSC_LAST_LINE,d1
        move.l  #NTSC_INTERVAL_WHOLE,d2
        move.w  #NTSC_INTERVAL_FRACTION,d3
        bra.s   .selected
.pal:
        move.w  #PAL_LAST_LINE,d1
        move.l  #SIM_INTERVAL_WHOLE,d2
        move.w  #SIM_INTERVAL_FRACTION,d3
.selected:
        move.w  d1,presentation_last_line
        subi.w  #PRESENTATION_GUARD_LINES,d1
        move.w  d1,presentation_last_safe_line
        move.l  d2,simulation_interval_whole
        move.w  d3,simulation_interval_fraction
        move.l  d2,simulation_interval
        move.l  d2,simulation_phase
        moveq   #0,d0
        rts
.unsupported:
        moveq   #20,d0
        rts

; Copper-driven publication can interrupt a producer that spans blank.
; Registers and its building bank remain intact; only completed ready scenes commit.
presentation_interrupt:
        movem.l d0-d7/a0-a6,-(sp)
        move.w  #$0010,$dff09c
        bsr     poll_presentation
        move.w  #$0010,$dff09c
        movem.l (sp)+,d0-d7/a0-a6
        rte

; Install at most one latest completed scene per guarded bottom interval.
; The displayed bank remains owned until COPJMP, after all old consumers retire.
poll_presentation:
        move.w  sr,-(sp)
        ori.w   #$0700,sr
        bsr     read_presentation_line
        cmpi.w  #253,d0
        bcs     presentation_not_blank
        cmp.w   presentation_last_safe_line,d0
        bhi     presentation_poll_done
presentation_blank:
        tst.b   blank_seen
        bne     presentation_poll_done
        move.b  #1,blank_seen
        addq.w  #1,presentation_frames
        tst.b   display_ready
        beq     presentation_log
        tst.b   ready_completed
        beq     presentation_log
        move.l  ready_copper,d0
        tst.b   ready_title_display
        beq.s   presentation_court
        move.l  #title_copper,d0
        move.w  #$0020,$dff096
        bra.s   presentation_selected
presentation_court:
        move.w  #$8020,$dff096
presentation_selected:
        move.l  d0,presentation_copper
        move.l  d0,$dff080
        move.w  #0,$dff088
        ; Retirement follows the strobe, never the future COP1LC write alone.
        move.l  front_copper,spare_copper
        move.l  ready_copper,front_copper
        clr.l   ready_copper
        move.w  ready_game_generation,game_presented_generation
        clr.b   display_ready
        clr.b   ready_completed
        bsr     read_presentation_line
        cmpi.w  #253,d0
        bcs.s   presentation_missed
        cmp.w   presentation_last_line,d0
        bls.s   presentation_log
presentation_missed:
        addq.w  #1,missed_presentation_deadlines
presentation_log:
        subq.w  #1,log_timer
        bne.s   presentation_poll_done
        move.w  #50,log_timer
presentation_poll_done:
        move.w  (sp)+,sr
        rts
presentation_not_blank:
        ; Any visible-line observation starts the next bottom interval; there
        ; is no requirement to poll exactly at field wrap or line0.
        clr.b   blank_seen
        bra     presentation_poll_done

; Freeze the building bank as latest complete. Its superseded ready bank (or
; the spare when no scene waits) becomes writable; the displayed bank is absent
; from this rotation. This does not wait for the PAL display or alter game ticks.
complete_scene:
        movem.l d0-d2/a0,-(sp)
        move.w  sr,-(sp)
        ori.w   #$0700,sr
        clr.b   ready_completed
        move.l  ready_copper,d0
        bne.s   .supersede
        move.l  spare_copper,d0
        clr.l   spare_copper
.supersede:
        move.l  back_copper,ready_copper
        move.w  simulation_started_updates,ready_generation
        move.w  game_accept_count,ready_game_generation
        move.b  game_title_display,ready_title_display
        move.b  #1,display_ready
        move.l  d0,back_copper
        move.w  simulation_started_updates,d1
        cmp.w   simulation_updates,d1
        bne.s   .producer_active
        st      ready_completed
.producer_active:
        move.w  (sp)+,sr
        bsr     select_build_bank
        movem.l (sp)+,d0-d2/a0
        rts

; Explicit title construction invalidates a waiting court scene, preserving
; ownership while the complete menu bitmap is built.
discard_ready_scene:
        move.w  sr,-(sp)
        ori.w   #$0700,sr
        tst.l   ready_copper
        beq.s   .none
        move.l  ready_copper,spare_copper
        clr.l   ready_copper
.none:  clr.b   display_ready
        clr.b   ready_completed
        move.w  (sp)+,sr
        rts

select_build_bank:
        move.l  back_copper,d0
        sub.l   #copperlist,d0
        move.l  d0,copper_write_delta
        clr.w   build_bank_index
        clr.l   sprite_write_delta
        tst.l   d0
        beq.s   .patch
        move.w  #1,build_bank_index
        move.l  #sprite_back-sprite0,sprite_write_delta
        cmpi.l  #copperlist_back-copperlist,d0
        beq.s   .patch
        move.w  #2,build_bank_index
        move.l  #sprite_third-sprite0,sprite_write_delta
.patch:
        bsr     patch_back_sprite_pointers
        bsr     patch_score_pointers
        rts

patch_back_sprite_pointers:
        movem.l d0-d2/d7/a0-a2,-(sp)
        lea     sprite_targets,a0
        lea     pointer_targets+16,a1
        moveq   #7,d7
next_back_sprite_pointer:
        move.l  (a0)+,d0
        add.l   sprite_write_delta,d0
        move.l  (a1)+,d1
        add.l   copper_write_delta,d1
        move.l  d1,a2
        move.l  d0,d2
        swap    d2
        move.w  d2,(a2)
        move.w  d0,4(a2)
        dbra    d7,next_back_sprite_pointer
        movem.l (sp)+,d0-d2/d7/a0-a2
        rts

simulation_update:
        ; Compact observational counter: external bus timestamps distinguish
        ; update entry/completion without stopping or tracing each instruction.
        addq.w  #1,simulation_started_updates
        tst.b   ui_paused
        bne.s   simulation_poll_done
        bsr     game_round_poll
simulation_poll_done:
        bsr     sample_amiga_joystick
        bsr     ui_sample
        bsr     game_native_commands
        jsr     tutorial_tick
        tst.b   tutorial_resume_defer
        bne     ui_frozen_update
        tst.b   ui_paused
        bne     ui_frozen_update
        cmpi.w  #GAME_PLAYING,game_lifecycle
        bne.s   simulation_menu
        bsr     game_render_sprites
        bsr     game_tick_dispatch
        bsr     complete_scene
        bsr     complete_update
        rts

ui_frozen_update:
        bsr     complete_update
        rts
simulation_menu:
        cmpi.w  #GAME_ROUND_PAUSE,game_lifecycle
        bcs.s   simulation_service_tick
        bsr     game_render_sprites
simulation_service_tick:
        bsr     game_native_menu_tick
        bsr     game_tick_dispatch
        cmpi.w  #GAME_ROUND_PAUSE,game_lifecycle
        bcs.s   simulation_service_observed
        bsr     complete_scene
simulation_service_observed:
        bsr     complete_update
        rts

 ; Completion validity belongs to a scene, not the latest global tick.
; Keep it valid across frozen ticks until consumption or supersession.
complete_update:
        move.w  sr,-(sp)
        ori.w   #$0700,sr
        addq.w  #1,simulation_updates
        tst.b   display_ready
        beq.s   .done
        move.w  ready_generation,d0
        cmp.w   simulation_updates,d0
        bne.s   .done
        st      ready_completed
.done:
        move.w  (sp)+,sr
        rts

prepare_title_display:
        movem.l d0-d1/d7/a0-a2,-(sp)
        lea     title_planes,a1
        lea     title_pointer0+2,a2
        moveq   #3,d7
title_patch_pointer:
        move.l  (a1)+,d0
        move.l  d0,d1
        swap    d1
        move.w  d1,(a2)
        move.w  d0,4(a2)
        addq.l  #8,a2
        dbra    d7,title_patch_pointer
        movem.l (sp)+,d0-d1/d7/a0-a2
        rts
title_planes: dc.l title_plane0,title_plane1,title_plane2,title_plane3
game_presented_generation: dc.w 0

; Hardware integration hooks: gameplay and service order live in game/.
game_scene_present_fields:
        core_trace_sink $102
        move.w  sr,-(sp)
        cmpi.b  #2,game_history_mode
        bne.s   .history_live
        move.w  (sp)+,sr
        rts
.history_live:
        move.w  (sp)+,sr
        tst.b   score_dirty
        beq.s   scoreboard_selection_done
        bsr     patch_score_pointers
scoreboard_selection_done:
        rts
game_show_returned_title:
        bsr     prepare_title_display
        ; ui_render selects title only after the complete menu copy.
        rts
game_core_status_present:
        core_trace_sink $103
        move.w  sr,-(sp)
        cmpi.b  #2,game_history_mode
        bne.s   .history_live
        move.w  (sp)+,sr
        rts
.history_live:
        move.w  (sp)+,sr
        bra     patch_score_pointers
game_title_display: dc.b 0
        even
presentation_copper: dc.l 0
game_observe_pre_tail:
        rts
game_apply_sound:
paula_events_done:
        rts


        include "amiga/score_copper_patch.i"
        include "amiga/square_score_banks.i"

        include "amiga/game/controls.s"

; Eight native primitives drive hardware channels directly. Images are already
; Native two-plane sprite data.
game_render_sprites:
        core_trace_sink $101
        move.w  sr,-(sp)
        cmpi.b  #2,game_history_mode
        bne.s   .history_live
        move.w  (sp)+,sr
        rts
.history_live:
        move.w  (sp)+,sr
        movem.l d0-d7/a0-a4,-(sp)
        bsr     tutorial_restore_build_planes
        move.l  #game_scene_objects,tutorial_sprite_source
        move.b  game_scene_ball_layer,tutorial_scene_layer
        ; Score/status selection belongs to this prepared scene, just like
        ; its sprites. The subsequent native tick may select fields for the
        ; following scene; it must not repatch this generation after rendering.
        lea     field_values(pc),a0
        lea     prepared_field_values(pc),a1
        moveq   #5,d7
prepare_scene_fields:
        move.b  (a0)+,(a1)+
        dbra    d7,prepare_scene_fields
        bsr     patch_score_pointers
game_render_prepared_scene:
        clr.l   pair_colours
        clr.l   pair_colours+4
        clr.b   sprite_bridge_error
        move.b  #$ff,active_ball_slot
        move.l  tutorial_sprite_source,a0
        tst.b   SC_BALL+O_VISIBLE(a0)
        beq.s   .order
        move.b  tutorial_scene_layer,d0
        lsl.b   #2,d0
        move.b  d0,active_ball_slot ; diagnostic depth label only
.order:
        moveq   #0,d0
        move.b  tutorial_scene_layer,d0
        lsl.w   #3,d0
        lea     game_scene_order,a3
        adda.w  d0,a3
        lea     sprite_targets,a1
        moveq   #0,d6
        moveq   #7,d7
.next:
        moveq   #0,d0
        move.b  (a3)+,d0
        lsl.w   #3,d0
        move.l  tutorial_sprite_source,a0
        adda.w  d0,a0
        tst.b   O_VISIBLE(a0)
        beq     .skip
        moveq   #0,d3
        move.b  O_Y(a0),d3
        moveq   #0,d4
        move.b  O_COLOUR(a0),d4
        move.w  d6,d0
        andi.w  #$fffe,d0
        lea     pair_colours,a4
        adda.w  d0,a4
        moveq   #1,d5
        tst.b   (a4)
        bne.s   .first
        move.b  d4,(a4)
        bra.s   .palette
.first:
        cmp.b   (a4),d4
        beq.s   .palette
        moveq   #2,d5
        tst.b   1(a4)
        bne.s   .second
        move.b  d4,1(a4)
        bra.s   .palette
.second:
        cmp.b   1(a4),d4
        beq.s   .palette
        ori.b   #2,sprite_bridge_error
.palette:
        cmpi.b  #COLOUR_BLACK,d4
        bls.s   .colour_valid
        ori.b   #4,sprite_bridge_error
.colour_valid:
        move.l  (a1)+,a2
        adda.l  sprite_write_delta,a2
        addi.w  #$2d,d3
        move.w  d3,d2
        addi.w  #16,d2
        move.b  d3,(a2)
        move.b  d2,2(a2)
        moveq   #0,d0
        move.b  O_X(a0),d0
        addi.w  #$a0,d0
        move.w  d0,d1
        lsr.w   #1,d1
        move.b  d1,1(a2)
        andi.b  #1,d0
        btst    #8,d3
        beq.s   .stop_high
        ori.b   #4,d0
.stop_high:
        btst    #8,d2
        beq.s   .control
        ori.b   #2,d0
.control:
        move.b  d0,3(a2)
        moveq   #0,d0
        move.w  O_FRAME(a0),d0
        cmpi.b  #2,d5
        bne.s   .image
        addi.w  #64,d0
.image:
        lea     game_scene_images,a4
        adda.w  d0,a4
        lea     4(a2),a2
        moveq   #15,d2
.copy:
        move.l  (a4)+,(a2)+
        dbra    d2,.copy
        clr.l   (a2)
        addq.w  #1,d6
.skip:
        dbra    d7,.next
        moveq   #7,d7
        sub.w   d6,d7
        bmi.s   .colours
.hide:
        move.l  (a1)+,a2
        adda.l  sprite_write_delta,a2
        clr.l   (a2)
        dbra    d7,.hide
.colours:
        lea     pair_colours,a0
        lea     palette_targets(pc),a1
        moveq   #7,d7
.palette_next:
        moveq   #0,d0
        move.b  (a0)+,d0
        add.w   d0,d0
        lea     game_scene_palette,a2
        move.w  (a2,d0.w),d0
        move.l  (a1)+,a4
        adda.l  copper_write_delta,a4
        move.w  d0,(a4)
        dbra    d7,.palette_next
game_scene_prepared:
        movem.l (sp)+,d0-d7/a0-a4
        rts

log_state:
        rts
hex_byte:
        lea     hex_digits(pc),a1
        move.w  d0,d1
        lsr.w   #4,d1
        move.b  (a1,d1.w),(a0)+
        andi.w  #15,d0
        move.b  (a1,d0.w),(a0)+
        rts

; Keep the renderer's small PC-relative working tables beside its code. The
; shared core/history/preview below can grow without widening these hot LEAs.
prepared_field_values: dc.b 0,0,0,0,0,1
palette_targets:
        dc.l cop_spr_pair0_c1+2,cop_spr_pair0_c2+2
        dc.l cop_spr_pair1_c1+2,cop_spr_pair1_c2+2
        dc.l cop_spr_pair2_c1+2,cop_spr_pair2_c2+2
        dc.l cop_spr_pair3_c1+2,cop_spr_pair3_c2+2
hex_digits:        dc.b "0123456789ABCDEF"
        even

        include "amiga/game/paula_output.s"
        include "amiga/game/keyboard.s"
        include "amiga/game/core.s"
        include "amiga/game/history.s"
        include "amiga/game/history_seek_job.s"
        include "amiga/game/preview.s"
        include "amiga/game/preview_endpoint.s"
        include "amiga/game/landing_try.s"
        include "amiga/game/core_trace.s"
        include "amiga/game/native_core_adapter.s"
        include "amiga/game/interface.s"
        include "amiga/game/tutorial.s"
        include "amiga/game/tutorial_render.s"
        include "amiga/game/tutorial_progressive.s"

        even
dos_entry_sp: dc.l 0
game_stack_bottom: dcb.b 4096,0
game_stack_top:
simulation_interval_whole: dc.l SIM_INTERVAL_WHOLE
simulation_interval_fraction: dc.w SIM_INTERVAL_FRACTION
        even
simulation_phase:   dc.l SIM_INTERVAL_WHOLE
simulation_interval: dc.l SIM_INTERVAL_WHOLE
simulation_fraction: dc.w 0
simulation_timer_origin: dc.w 0
last_timer_count:  dc.l 0
simulation_timer_running: dc.b 0
        even
blank_seen:        dc.b 0
display_ready:     dc.b 0
ready_completed:   dc.b 0
        even
front_copper:      dc.l 0
back_copper:       dc.l 0
ready_copper:      dc.l 0
spare_copper:      dc.l 0
ready_generation: dc.w 0
ready_game_generation: dc.w 0
build_bank_index:  dc.w 0
presentation_last_line: dc.w 0
presentation_last_safe_line: dc.w 0
ready_title_display: dc.b 0
ui_construction_complete: dc.b 0
copper_write_delta: dc.l 0
sprite_write_delta: dc.l 0
simulation_updates: dc.w 0
simulation_started_updates: dc.w 0
presentation_frames: dc.w 0
missed_presentation_deadlines: dc.w 0
log_timer:         dc.w 50
        even
pair_colours:      dcb.b 8,0
sprite_bridge_error: dc.b 0
active_ball_slot: dc.b $ff
        even
sprite_targets:
        dc.l sprite0,sprite1,sprite2,sprite3,sprite4,sprite5,sprite6,sprite7
log_text:          dc.b "LIVE F="
log_frames:        dc.b "00 U="
log_updates:       dc.b "00 I="
log_input:         dc.b "00 X="
log_player_x:      dc.b "00 SX="
log_sprite_x:      dc.b "00 E="
log_bridge_error:   dc.b "00 B="
log_ball_slot:      dc.b "00 BY="
log_ball_y:         dc.b "00 BX="
log_ball_x:         dc.b "00 LP="
log_lower_phase:    dc.b "00 UP="
log_upper_phase:    dc.b "00 SB="
log_score_b:      dc.b "00 ST="
log_status:       dc.b "00 UC="
log_updates_full: dc.b "0000 PA="
log_point_a:      dc.b "00 PB="
log_point_b:      dc.b "00 GA="
log_games_a:      dc.b "00 GB="
log_games_b:      dc.b "00 SF="
log_score_flags:  dc.b "00 M="
log_mode:         dc.b "00 DG="
log_display_game_b: dc.b "00 DL="
log_deadlines: dc.b "0000"
                  dc.b 0
        even
pointer_sources:
        dc.l plane0,plane1,plane2,plane3
        dc.l sprite0,sprite1,sprite2,sprite3,sprite4,sprite5,sprite6,sprite7
pointer_targets:
        dc.l cop_bpl0h+2,cop_bpl1h+2,cop_bpl2h+2,cop_bpl3h+2
        dc.l cop_spr0h+2,cop_spr1h+2,cop_spr2h+2,cop_spr3h+2
        dc.l cop_spr4h+2,cop_spr5h+2,cop_spr6h+2,cop_spr7h+2
        include "assets/native/court/score-patch-tables.i"
        even
        even
        even
game_scene_images: incbin "assets/native/scene/sprite-images.bin"


        include "amiga/display.i"
        even
        include "assets/native/court/score-bank-data.i"
        even
; Authored mathematical four-byte square; identical bytes preserve effect timbre.
paula_square: incbin "assets/native/audio/battle-hymn/square.s8"
        even
copperlist_back: dcb.b copperlist_end-copperlist,0
sprite_back: dcb.b 8*72,0
copperlist_third: dcb.b copperlist_end-copperlist,0
sprite_third: dcb.b 8*72,0

        even
        include "assets/native/title/display.i"

        include "amiga/square_score_storage.i"

        section history,bss
        include "amiga/game/history_storage.i"
; HUNK longword padding, outside the attach buffer
        ds.b 2
        include "amiga/game/preview_storage.i"
        include "amiga/game/history_seek_storage.i"
        include "amiga/game/tutorial_storage.i"
