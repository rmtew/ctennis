        section code,code
SCORE_COPPER_DISPLAY equ 1
LIVE_REFRESH_ADAPTER equ 1
        include "build/translation/player-frame-symbols.i"
        include "amiga/translated_z80_macros.i"

start:
        lea     virtual_memory,a6
        lea     virtual_memory+$c000,a5
        lea     initial_ram,a0
        move.l  a5,a1
        move.w  #255,d7
copy_initial_ram:
        move.b  (a0)+,(a1)+
        dbra    d7,copy_initial_ram
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
        lea     $dff000,a0
        move.w  #$7fff,$09a(a0)
        move.w  #$7fff,$096(a0)
        move.l  #copperlist,$080(a0)
        move.w  #0,$088(a0)
        move.w  #$83a0,$096(a0)
        bsr     paula_tone_init
        bsr     upload_sprite_attributes

wait_frame:
        move.w  $dff006,d0
        andi.w  #$ff00,d0
        cmpi.w  #$f000,d0
        bne.s   wait_frame
        move.l  simulation_phase,d0
        addi.l  #59922738,d0
        move.l  d0,simulation_phase
next_update:
        move.l  simulation_phase,d0
        cmpi.l  #50000000,d0
        bcs.s   updates_done
        subi.l  #50000000,d0
        move.l  d0,simulation_phase
        bsr     simulation_update
        bra.s   next_update
updates_done:
        addq.w  #1,presentation_frames
        subq.w  #1,log_timer
        bne.s   wait_blanking_end
        move.w  #50,log_timer
        bsr     log_state
wait_blanking_end:
        move.w  $dff006,d0
        andi.w  #$ff00,d0
        cmpi.w  #$f000,d0
        beq.s   wait_blanking_end
        bra     wait_frame

simulation_update:
        bsr     sample_amiga_joystick
        bsr     upload_sprite_attributes
        move.b  $42(a5),score_flags_before
        move.b  $71(a5),status_timer_before
        bsr     scoreboard_update
        bsr     update_native_scoreboard
        bsr     input_update
        bsr     score_gate
        bsr     lower_player_state
        bsr     upper_player_state
        bsr     ball_flight_update
        bsr     player_movement_and_sprites
        bsr     irq_counter_prefix
        move.l  #psg_log,psg_ptr
        clr.b   psg_count
        bsr     audio_tick_adapter
        ifd LONG_GAME_REPLAY
        bsr     log_replay_psg
        endif
        bsr     paula_apply_psg_events
        move.l  #vdp_log,vdp_ptr
        clr.b   vdp_count
        bsr     irq_vdp_tail
        move.w  $dff006,d0
        andi.w  #$ff00,d0
        cmpi.w  #$2c00,d0
        bcs.s   update_before_visible
        cmpi.w  #$ec00,d0
        bcc.s   update_before_visible
        addq.w  #1,missed_presentation_deadlines
update_before_visible:
        addq.w  #1,simulation_updates
        ifd LONG_GAME_REPLAY
        bsr     log_replay_transition
        endif
        rts

        ifd LONG_GAME_REPLAY
; Log only source score changes and actual native display-bank changes.
log_replay_psg:
        tst.b   psg_count
        beq.s   replay_psg_no_log
        movem.l d0-d2/d7/a0-a2,-(sp)
        move.w  simulation_updates,d2
        addq.w  #1,d2
        lea     psg_trace_update(pc),a0
        move.w  d2,d0
        lsr.w   #8,d0
        bsr     hex_byte
        moveq   #0,d0
        move.b  d2,d0
        bsr     hex_byte
        lea     psg_trace_count(pc),a0
        moveq   #0,d0
        move.b  psg_count,d0
        bsr     hex_byte
        lea     psg_trace_bytes(pc),a0
        lea     psg_log(pc),a2
        moveq   #0,d7
        move.b  psg_count,d7
        subq.w  #1,d7
replay_psg_next:
        moveq   #0,d0
        move.b  (a2)+,d0
        bsr     hex_byte
        dbra    d7,replay_psg_next
        clr.b   (a0)
        move.l  #psg_trace_text,-(sp)
        move.l  #86,-(sp)
        jsr     $f0ff60
        addq.l  #8,sp
        movem.l (sp)+,d0-d2/d7/a0-a2
replay_psg_no_log:
        rts

log_replay_transition:
        movem.l d0-d2/a0-a1,-(sp)
        moveq   #0,d2
        lea     $3e(a5),a0
        lea     last_replay_score(pc),a1
        moveq   #3,d1
replay_compare_score:
        move.b  (a0)+,d0
        cmp.b   (a1),d0
        beq.s   replay_score_same
        move.b  d0,(a1)
        moveq   #1,d2
replay_score_same:
        addq.l  #1,a1
        dbra    d1,replay_compare_score
        tst.b   score_dirty
        bne.s   replay_log_changed
        tst.b   d2
        beq.s   replay_no_log
replay_log_changed:
        bsr     log_state
replay_no_log:
        movem.l (sp)+,d0-d2/a0-a1
        rts
        endif

; Match the source scoreboard routine's two draw events. Point/game/mode RAM
; may change earlier in the score gate, but the source draws them only when
; status bit 5 is consumed on the following update. Status text remains shown
; until the source timer expires, even if other RAM state changes meanwhile.
update_native_scoreboard:
        movem.l d0-d2/a0,-(sp)
        clr.b   score_dirty
        move.b  score_flags_before,d0
        btst    #7,d0
        beq.s   check_score_redraw
        btst    #6,d0
        beq.s   set_status_selection
        cmpi.b  #$ff,status_timer_before
        bne.s   check_score_redraw
        clr.b   field_values+4
        move.b  #1,score_dirty
        bra.s   check_score_redraw
set_status_selection:
        move.b  $42(a5),d1
        andi.b  #7,d1
        move.b  d1,field_values+4
        move.b  #1,score_dirty
check_score_redraw:
        btst    #5,d0
        beq.s   commit_score_selection
        lea     field_values(pc),a0
        move.b  $3e(a5),(a0)+
        move.b  $3f(a5),(a0)+
        move.b  $40(a5),(a0)+
        move.b  $41(a5),(a0)+
        addq.l  #1,a0
        moveq   #0,d1
        move.b  $3d(a5),d2
        btst    #2,d2
        bne.s   store_mode_selection
        moveq   #1,d1
        btst    #7,d2
        beq.s   store_mode_selection
        moveq   #2,d1
store_mode_selection:
        move.b  d1,(a0)
        move.b  #1,score_dirty
commit_score_selection:
        tst.b   score_dirty
        beq.s   scoreboard_selection_done
        bsr     patch_score_pointers
scoreboard_selection_done:
        movem.l (sp)+,d0-d2/a0
        rts

        include "amiga/score_copper_patch.i"

; The cartridge uses bit 0 of Z80 R as one AI target-sign choice. The normal
; port samples a changing native timer bit, mixed with the existing game PRNG.
; A replay build can instead supply the source's recorded sign at each update.
read_refresh_adapter:
        ifd LONG_GAME_REPLAY
        movem.l d1/a0,-(sp)
        moveq   #0,d1
        move.w  simulation_updates,d1
        cmpi.w  #REFRESH_SIGN_COUNT,d1
        bcc.s   refresh_replay_default
        lea     refresh_signs,a0
        moveq   #0,d0
        move.b  0(a0,d1.w),d0
        bra.s   refresh_replay_done
refresh_replay_default:
        moveq   #0,d0
refresh_replay_done:
        movem.l (sp)+,d1/a0
        rts
        else
        move.l  d1,-(sp)
        moveq   #0,d0
        move.b  $bfe401,d0
        move.b  $72(a5),d1
        eor.b   d1,d0
        andi.b  #1,d0
        move.l  (sp)+,d1
        rts
        endif

sample_amiga_joystick:
        clr.b   game_input_bits
        move.w  $dff00c,d0
        btst    #9,d0
        beq.s   input_right
        ori.b   #4,game_input_bits
input_right:
        btst    #1,d0
        beq.s   input_fire
        ori.b   #1,game_input_bits
input_fire:
        move.b  $bfe001,d0
        btst    #7,d0
        bne.s   input_ready
        ori.b   #$10,game_input_bits
input_ready:
        rts
read_game_input:
        move.b  game_input_bits,d0
        rts
sample_second_input_group:
        clr.b   d0
        rts

; Compress the previous ten source records into eight Amiga channels in source
; priority order, then build each sprite from its source pattern and colour.
upload_sprite_attributes:
        movem.l d0-d7/a0-a4,-(sp)
        clr.l   pair_colours
        clr.l   pair_colours+4
        clr.b   sprite_bridge_error
        move.b  #$ff,active_ball_slot
        lea     $10(a5),a0
        lea     sprite_targets(pc),a1
        moveq   #0,d6
        moveq   #9,d7
next_source_sprite:
        moveq   #0,d3
        move.b  (a0),d3
        cmpi.b  #$c0,d3
        bcc     source_sprite_done
        moveq   #0,d4
        move.b  3(a0),d4
        andi.b  #15,d4
        beq     source_sprite_done
        cmpi.w  #8,d6
        bcs.s   source_sprite_fits
        ori.b   #1,sprite_bridge_error
        bra     source_sprite_done
source_sprite_fits:
        moveq   #9,d0
        sub.w   d7,d0
        cmpi.b  #0,d0
        beq.s   source_ball_slot
        cmpi.b  #4,d0
        beq.s   source_ball_slot
        cmpi.b  #8,d0
        bne.s   select_sprite_palette
source_ball_slot:
        move.b  d0,active_ball_slot
select_sprite_palette:
        move.w  d6,d0
        andi.w  #$fffe,d0
        lea     pair_colours,a4
        adda.w  d0,a4
        moveq   #1,d5
        tst.b   (a4)
        bne.s   compare_first_colour
        move.b  d4,(a4)
        bra.s   sprite_palette_ready
compare_first_colour:
        cmp.b   (a4),d4
        beq.s   sprite_palette_ready
        moveq   #2,d5
        tst.b   1(a4)
        bne.s   compare_second_colour
        move.b  d4,1(a4)
        bra.s   sprite_palette_ready
compare_second_colour:
        cmp.b   1(a4),d4
        beq.s   sprite_palette_ready
        ori.b   #2,sprite_bridge_error
sprite_palette_ready:
        cmpi.b  #1,d4
        beq.s   sprite_colour_known
        cmpi.b  #4,d4
        beq.s   sprite_colour_known
        cmpi.b  #13,d4
        beq.s   sprite_colour_known
        cmpi.b  #15,d4
        beq.s   sprite_colour_known
        ori.b   #4,sprite_bridge_error
sprite_colour_known:
        move.l  (a1)+,a2
        addi.w  #$2d,d3
        move.w  d3,d2
        addi.w  #16,d2
        move.b  d3,(a2)
        move.b  d2,2(a2)
        moveq   #0,d0
        move.b  1(a0),d0
        addi.w  #$6c,d0
        move.w  d0,d1
        lsr.w   #1,d1
        move.b  d1,1(a2)
        andi.b  #1,d0
        btst    #8,d3
        beq.s   sprite_vstop_high
        ori.b   #4,d0
sprite_vstop_high:
        btst    #8,d2
        beq.s   sprite_control_ready
        ori.b   #2,d0
sprite_control_ready:
        move.b  d0,3(a2)
        moveq   #0,d0
        move.b  2(a0),d0
        andi.w  #$fc,d0
        lsl.w   #3,d0
        lea     sprite_pattern_rows,a3
        adda.w  d0,a3
        lea     4(a2),a2
        moveq   #15,d2
next_sprite_pattern_row:
        move.w  (a3)+,d0
        cmpi.b  #1,d5
        bne.s   sprite_pattern_colour_two
        move.w  d0,(a2)+
        clr.w   (a2)+
        bra.s   sprite_pattern_row_done
sprite_pattern_colour_two:
        clr.w   (a2)+
        move.w  d0,(a2)+
sprite_pattern_row_done:
        dbra    d2,next_sprite_pattern_row
        clr.l   (a2)
        addq.w  #1,d6
source_sprite_done:
        addq.l  #4,a0
        dbra    d7,next_source_sprite
        moveq   #7,d7
        sub.w   d6,d7
        bmi.s   update_sprite_palettes
hide_unused_sprites:
        move.l  (a1)+,a2
        clr.l   (a2)
        dbra    d7,hide_unused_sprites
update_sprite_palettes:
        lea     pair_colours,a0
        lea     palette_targets(pc),a1
        moveq   #7,d7
next_sprite_colour:
        moveq   #0,d0
        move.b  (a0)+,d0
        add.w   d0,d0
        lea     sg_sprite_palette(pc),a2
        move.w  0(a2,d0.w),d0
        move.l  (a1)+,a3
        move.w  d0,(a3)
        dbra    d7,next_sprite_colour
        movem.l (sp)+,d0-d7/a0-a4
        rts

; Source writes are retained for verification; display selection uses game state.
copy_cpu_bytes_to_vram_b_count:
        MAKE_HL_NO_AR
        MAKE_DE_NO_AR
        tst.b   d1
        beq.s   copy_vram_done
copy_vram_byte:
        lea     virtual_memory,a0
        moveq   #0,d0
        move.w  d6,d0
        adda.l  d0,a0
        move.b  (a0),d0
        bsr     log_vram_write
        addq.w  #1,d6
        addq.w  #1,d4
        subq.b  #1,d1
        bne.s   copy_vram_byte
copy_vram_done:
        MAKE_H
        MAKE_D
        clr.b   d0
        rts
l_0008:
        movem.l d4/d6-d7,-(sp)
        MAKE_HL_NO_AR
        move.w  d6,d4
        bsr     log_vram_write
        movem.l (sp)+,d4/d6-d7
        rts
log_vram_write:
        andi.w  #$3fff,d4
        lea     shadow_vram,a1
        move.b  d0,0(a1,d4.w)
        rts
record_vdp_byte:
        move.l  vdp_ptr,a1
        move.b  d0,(a1)+
        move.l  a1,vdp_ptr
        addq.b  #1,vdp_count
        rts
log_state:
        movem.l d0-d2/a0-a1,-(sp)
        lea     log_frames(pc),a0
        moveq   #0,d0
        move.b  presentation_frames+1,d0
        bsr     hex_byte
        lea     log_updates(pc),a0
        moveq   #0,d0
        move.b  simulation_updates+1,d0
        bsr     hex_byte
        lea     log_input(pc),a0
        moveq   #0,d0
        move.b  game_input_bits,d0
        bsr     hex_byte
        lea     log_player_x(pc),a0
        moveq   #0,d0
        move.b  $4a(a5),d0
        bsr     hex_byte
        lea     log_sprite_x(pc),a0
        moveq   #0,d0
        move.b  $15(a5),d0
        bsr     hex_byte
        lea     log_bridge_error(pc),a0
        moveq   #0,d0
        move.b  sprite_bridge_error,d0
        bsr     hex_byte
        lea     log_ball_slot(pc),a0
        moveq   #0,d0
        move.b  active_ball_slot,d0
        bsr     hex_byte
        lea     log_ball_y(pc),a0
        moveq   #0,d0
        move.b  $34(a5),d0
        bsr     hex_byte
        lea     log_ball_x(pc),a0
        moveq   #0,d0
        move.b  $35(a5),d0
        bsr     hex_byte
        lea     log_lower_phase(pc),a0
        moveq   #0,d0
        move.b  $49(a5),d0
        bsr     hex_byte
        lea     log_upper_phase(pc),a0
        moveq   #0,d0
        move.b  $45(a5),d0
        bsr     hex_byte
        lea     log_score_b(pc),a0
        moveq   #0,d0
        move.b  field_values+1,d0
        bsr     hex_byte
        lea     log_status(pc),a0
        moveq   #0,d0
        move.b  field_values+4,d0
        bsr     hex_byte
        lea     log_updates_full(pc),a0
        moveq   #0,d0
        move.b  simulation_updates,d0
        bsr     hex_byte
        moveq   #0,d0
        move.b  simulation_updates+1,d0
        bsr     hex_byte
        lea     log_point_a(pc),a0
        moveq   #0,d0
        move.b  $3e(a5),d0
        bsr     hex_byte
        lea     log_point_b(pc),a0
        moveq   #0,d0
        move.b  $3f(a5),d0
        bsr     hex_byte
        lea     log_games_a(pc),a0
        moveq   #0,d0
        move.b  $40(a5),d0
        bsr     hex_byte
        lea     log_games_b(pc),a0
        moveq   #0,d0
        move.b  $41(a5),d0
        bsr     hex_byte
        lea     log_score_flags(pc),a0
        moveq   #0,d0
        move.b  $42(a5),d0
        bsr     hex_byte
        lea     log_mode(pc),a0
        moveq   #0,d0
        move.b  $3d(a5),d0
        bsr     hex_byte
        lea     log_display_game_b(pc),a0
        moveq   #0,d0
        move.b  field_values+3,d0
        bsr     hex_byte
        lea     log_deadlines(pc),a0
        moveq   #0,d0
        move.b  missed_presentation_deadlines,d0
        bsr     hex_byte
        moveq   #0,d0
        move.b  missed_presentation_deadlines+1,d0
        bsr     hex_byte
        ifd LONG_GAME_REPLAY
        lea     log_psg_hash(pc),a0
        moveq   #0,d0
        move.b  replay_psg_hash,d0
        bsr     hex_byte
        moveq   #0,d0
        move.b  replay_psg_hash+1,d0
        bsr     hex_byte
        lea     log_psg_total(pc),a0
        moveq   #0,d0
        move.b  replay_psg_total,d0
        bsr     hex_byte
        moveq   #0,d0
        move.b  replay_psg_total+1,d0
        bsr     hex_byte
        endif
        move.l  #log_text,-(sp)
        move.l  #86,-(sp)
        jsr     $f0ff60
        addq.l  #8,sp
        movem.l (sp)+,d0-d2/a0-a1
        rts
hex_byte:
        lea     hex_digits(pc),a1
        move.w  d0,d1
        lsr.w   #4,d1
        move.b  (a1,d1.w),(a0)+
        andi.w  #15,d0
        move.b  (a1,d0.w),(a0)+
        rts

        include "amiga/translated_audio_tick.s"
        include "amiga/paula_tone_output.s"
        include "build/translation/player-frame-routines.s"

        even
simulation_phase:   dc.l 0
simulation_updates: dc.w 0
presentation_frames: dc.w 0
missed_presentation_deadlines: dc.w 0
log_timer:         dc.w 50
game_input_bits:   dc.b 0
score_flags_before: dc.b 0
status_timer_before: dc.b 0
score_dirty: dc.b 0
field_values: dc.b 0,0,0,0,0,1
        ifd LONG_GAME_REPLAY
last_replay_score: dcb.b 4,0
        endif
        even
vdp_count:         dc.b 0
        even
pair_colours:      dcb.b 8,0
sprite_bridge_error: dc.b 0
active_ball_slot: dc.b $ff
        even
vdp_ptr:           dc.l 0
vdp_log:           dcb.b 4,0
sprite_targets:
        dc.l sprite0,sprite1,sprite2,sprite3,sprite4,sprite5,sprite6,sprite7
palette_targets:
        dc.l cop_spr_pair0_c1+2,cop_spr_pair0_c2+2
        dc.l cop_spr_pair1_c1+2,cop_spr_pair1_c2+2
        dc.l cop_spr_pair2_c1+2,cop_spr_pair2_c2+2
        dc.l cop_spr_pair3_c1+2,cop_spr_pair3_c2+2
sg_sprite_palette:
        dc.w $000,$000,$2c4,$6d7,$55e,$77f,$000,$000
        dc.w $000,$f77,$dc5,$000,$000,$c5b,$ccc,$fff
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
        ifd LONG_GAME_REPLAY
                  dc.b " PH="
log_psg_hash:     dc.b "0000 PT="
log_psg_total:    dc.b "0000"
        endif
                  dc.b 0
        ifd LONG_GAME_REPLAY
psg_trace_text:   dc.b "PSG U="
psg_trace_update: dc.b "0000 N="
psg_trace_count:  dc.b "00 D="
psg_trace_bytes:  dcb.b 129,0
        endif
hex_digits:        dc.b "0123456789ABCDEF"
        even
pointer_sources:
        dc.l plane0,plane1,plane2,plane3
        dc.l sprite0,sprite1,sprite2,sprite3,sprite4,sprite5,sprite6,sprite7
pointer_targets:
        dc.l cop_bpl0h+2,cop_bpl1h+2,cop_bpl2h+2,cop_bpl3h+2
        dc.l cop_spr0h+2,cop_spr1h+2,cop_spr2h+2,cop_spr3h+2
        dc.l cop_spr4h+2,cop_spr5h+2,cop_spr6h+2,cop_spr7h+2
        include "build/amiga/score-copper-probe/score-patch-tables.i"
        even
initial_ram: incbin "build/translation/live-initial-ram.bin"
        even
virtual_memory: incbin "build/translation/player-frame-memory.bin"
        even
sprite_pattern_rows: incbin "build/amiga/sprite-probe/sprite-pattern-rows.bin"
shadow_vram: dcb.b 16384,0

        include "amiga/sprite_probe_display.i"
        even
        include "build/amiga/score-copper-probe/score-bank-data.i"
        even
paula_square: dc.b $7f,$7f,$81,$81
        ifd LONG_GAME_REPLAY
        include "build/amiga/long-game/refresh-signs.i"
        endif
