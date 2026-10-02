        section code,code
; Accepted PAL E-clock cadence:11838+14906/65536 ticks at709379Hz.
; Retain fractional phase instead of rounding every update down.
SIM_INTERVAL_WHOLE equ 11838
SIM_INTERVAL_FRACTION equ 14906

start:
        ; DOS enters on its task stack. Finish all OS scheduling calls there,
        ; then own the machine and use a bounded application stack forever.
        move.l  sp,dos_entry_sp
        move.l  4.w,a6
        jsr     -132(a6) ; Exec Forbid
        jsr     -120(a6) ; Exec Disable
        lea     game_stack_top,sp
        bsr     game_begin_title
        lea     pointer_sources(pc),a0
        lea     pointer_targets(pc),a1
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
        move.l  #copperlist,front_copper
        move.l  #copperlist_back,back_copper
        move.l  #copperlist_back,d0
        sub.l   #copperlist,d0
        move.l  d0,copper_write_delta
        move.l  #sprite_back,d0
        sub.l   #sprite0,d0
        move.l  d0,sprite_write_delta
        bsr     patch_back_sprite_pointers
        lea     $dff000,a0
        move.w  #$7fff,$09a(a0)
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
main_loop:
        tst.b   ui_paused
        bne.s   ui_skip_round_poll
        bsr     game_round_poll
ui_skip_round_poll:
        bsr     game_poll_keyboard
        bsr     poll_presentation
        bsr     account_sim_timer
        move.l  simulation_phase,d0
        cmp.l   simulation_interval,d0
        bcs.s   main_loop
        sub.l   simulation_interval,d0
        move.l  d0,simulation_phase
        move.l  #SIM_INTERVAL_WHOLE,simulation_interval
        addi.w  #SIM_INTERVAL_FRACTION,simulation_fraction
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

; Simulation prepares an inactive Copper list and sprite bank. The display
; commit changes only COP1LC; preparation of the next back list can run later.
poll_presentation:
        move.w  $dff006,d0
        andi.w  #$ff00,d0
        ; The UI footer is visible through251; late blank starts at252.
        cmpi.w  #$fc00,d0
        bcc.s   presentation_blank
        ; Sprite POS/CTL DMA starts before the visible bitplane window.
        ; Publish with one line of margin before its line25 header fetch;
        ; changing banks later can mix old controls with new sprite pixels.
        cmpi.w  #$1800,d0
        bcs.s   presentation_blank
        bra     presentation_not_blank
presentation_blank:
        tst.b   blank_seen
        bne     presentation_poll_done
        move.b  #1,blank_seen
        addq.w  #1,presentation_frames
        tst.b   display_ready
        beq     presentation_log
        move.l  back_copper,d0
        move.l  front_copper,back_copper
        move.l  d0,front_copper
        tst.b   game_title_display
        beq.s   presentation_court
        move.l  #title_copper,d0
        move.w  #$0020,$dff096
        bra.s   presentation_selected
presentation_court:
        move.w  #$8020,$dff096
presentation_selected:
        move.l  d0,presentation_copper
        move.l  d0,$dff080
        ; COP1LC alone takes effect at the next automatic Copper restart.
        ; Reload in blank so an early-blank publication drives this frame too.
        move.w  #0,$dff088
        move.w  game_accept_count,game_presented_generation
        move.w  $dff006,d0
        andi.w  #$ff00,d0
        cmpi.w  #$2c00,d0
        bcs.s   presentation_commit_in_blank
        ; The UI footer is visible through251; late blank starts at252.
        cmpi.w  #$fc00,d0
        bcc.s   presentation_commit_in_blank
        addq.w  #1,missed_presentation_deadlines
presentation_commit_in_blank:
        clr.b   display_ready
        move.l  back_copper,d0
        sub.l   #copperlist,d0
        move.l  d0,copper_write_delta
        tst.l   d0
        beq.s   write_original_sprites
        move.l  #sprite_back,d0
        sub.l   #sprite0,d0
        move.l  d0,sprite_write_delta
        bra.s   back_list_prepared
write_original_sprites:
        clr.l   sprite_write_delta
back_list_prepared:
        bsr     patch_back_sprite_pointers
        bsr     patch_score_pointers
presentation_log:
        subq.w  #1,log_timer
        bne.s   presentation_poll_done
        move.w  #50,log_timer
presentation_poll_done:
        rts
presentation_not_blank:
        cmpi.w  #$6000,d0
        bcs.s   presentation_poll_done
        clr.b   blank_seen
        rts

patch_back_sprite_pointers:
        movem.l d0-d2/d7/a0-a2,-(sp)
        lea     sprite_targets(pc),a0
        lea     pointer_targets+16(pc),a1
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
        bsr     sample_amiga_joystick
        bsr     ui_sample
        tst.b   ui_paused
        bne     ui_frozen_update
        cmpi.w  #GAME_PLAYING,game_lifecycle
        bne.s   simulation_menu
        bsr     game_render_sprites
        bsr     game_tick_dispatch
        move.b  #1,display_ready
        addq.w  #1,simulation_updates
        rts

ui_frozen_update:
        addq.w  #1,simulation_updates
        rts
simulation_menu:
        cmpi.w  #GAME_ROUND_PAUSE,game_lifecycle
        bcs.s   simulation_service_tick
        bsr     game_render_sprites
simulation_service_tick:
        bsr     game_tick_dispatch
        cmpi.w  #GAME_ROUND_PAUSE,game_lifecycle
        bcs.s   simulation_service_observed
        move.b  #1,display_ready
simulation_service_observed:
        addq.w  #1,simulation_updates
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
        tst.b   score_dirty
        beq.s   scoreboard_selection_done
        bsr     patch_score_pointers
scoreboard_selection_done:
        rts
game_show_returned_title:
        bsr     prepare_title_display
        st      game_title_display
        rts
game_show_returned_court:
        clr.b   game_title_display
        rts
game_clear_returned_status:
        clr.b   field_values+4
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

; Native AI target-sign entropy: timer bit mixed with the game PRNG.
; Attract playback uses the independently recorded native seeded stream.
native_entropy_bit:
        ifd DEMO_RECORDING
        move.l  d1,-(sp)
        bsr     ui_demo_entropy
        move.l  (sp)+,d1
        rts
        else
        tst.b   ui_demo
        beq.s   refresh_live_entropy
        move.l  d1,-(sp)
        bsr     ui_demo_entropy
        move.l  (sp)+,d1
        rts
refresh_live_entropy:
        endif
        move.l  d1,-(sp)
        moveq   #0,d0
        move.b  $bfe401,d0
        move.b  game_random_seed,d1
        eor.b   d1,d0
        andi.b  #1,d0
        move.l  (sp)+,d1
        rts

        include "amiga/game/controls.s"

; Eight native primitives drive hardware channels directly. Images are already
; Native two-plane sprite data.
game_render_sprites:
        movem.l d0-d7/a0-a4,-(sp)
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
        clr.l   pair_colours
        clr.l   pair_colours+4
        clr.b   sprite_bridge_error
        move.b  #$ff,active_ball_slot
        tst.b   game_scene_objects+SC_BALL+O_VISIBLE
        beq.s   .order
        move.b  game_scene_ball_layer,d0
        lsl.b   #2,d0
        move.b  d0,active_ball_slot ; diagnostic depth label only
.order:
        moveq   #0,d0
        move.b  game_scene_ball_layer,d0
        lsl.w   #3,d0
        lea     game_scene_order,a3
        adda.w  d0,a3
        lea     sprite_targets(pc),a1
        moveq   #0,d6
        moveq   #7,d7
.next:
        moveq   #0,d0
        move.b  (a3)+,d0
        lsl.w   #3,d0
        lea     game_scene_objects,a0
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

        include "amiga/game/paula_output.s"
        include "amiga/game/keyboard.s"
        include "amiga/game/tick.s"
        include "amiga/game/integration.s"
        include "amiga/game/interface.s"

        even
dos_entry_sp: dc.l 0
game_stack_bottom: dcb.b 4096,0
game_stack_top:
simulation_phase:   dc.l SIM_INTERVAL_WHOLE
simulation_interval: dc.l SIM_INTERVAL_WHOLE
simulation_fraction: dc.w 0
simulation_timer_origin: dc.w 0
last_timer_count:  dc.l 0
simulation_timer_running: dc.b 0
        even
blank_seen:        dc.b 0
display_ready:     dc.b 0
        even
front_copper:      dc.l 0
back_copper:       dc.l 0
copper_write_delta: dc.l 0
sprite_write_delta: dc.l 0
simulation_updates: dc.w 0
simulation_started_updates: dc.w 0
presentation_frames: dc.w 0
missed_presentation_deadlines: dc.w 0
log_timer:         dc.w 50
score_dirty: dc.b 0
field_values: dc.b 0,0,0,0,0,1
prepared_field_values: dc.b 0,0,0,0,0,1
        even
pair_colours:      dcb.b 8,0
sprite_bridge_error: dc.b 0
active_ball_slot: dc.b $ff
        even
sprite_targets:
        dc.l sprite0,sprite1,sprite2,sprite3,sprite4,sprite5,sprite6,sprite7
palette_targets:
        dc.l cop_spr_pair0_c1+2,cop_spr_pair0_c2+2
        dc.l cop_spr_pair1_c1+2,cop_spr_pair1_c2+2
        dc.l cop_spr_pair2_c1+2,cop_spr_pair2_c2+2
        dc.l cop_spr_pair3_c1+2,cop_spr_pair3_c2+2
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
hex_digits:        dc.b "0123456789ABCDEF"
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

        even
        include "assets/native/title/display.i"
