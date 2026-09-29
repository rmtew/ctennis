        section code,code
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
        lea     $dff000,a0
        move.w  #$7fff,$09a(a0)
        move.w  #$7fff,$096(a0)
        move.l  #copperlist,$080(a0)
        move.w  #0,$088(a0)
        move.w  #$83a0,$096(a0)
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
        bra.s   wait_frame

simulation_update:
        bsr     sample_amiga_joystick
        bsr     upload_sprite_attributes
        bsr     scoreboard_update
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
        move.l  #vdp_log,vdp_ptr
        clr.b   vdp_count
        bsr     irq_vdp_tail
        addq.w  #1,simulation_updates
        rts

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

; Show the previous C010-C037 attribute buffer before the game builds its next one.
; Shape and colours still come from the controlled frame-1310 sprite assets.
upload_sprite_attributes:
        movem.l d0-d7/a0-a3,-(sp)
        lea     sprite_source_offsets(pc),a0
        lea     sprite_targets(pc),a3
        moveq   #7,d7
next_sprite:
        moveq   #0,d0
        move.b  (a0)+,d0
        lea     $10(a5),a1
        adda.w  d0,a1
        move.l  (a3)+,a2
        moveq   #0,d0
        move.b  (a1),d0
        cmpi.b  #$c0,d0
        bcc.s   hide_sprite
        tst.b   3(a1)
        beq.s   hide_sprite
        addi.w  #$2d,d0
        move.w  d0,d2
        addi.w  #16,d2
        move.b  d0,(a2)
        move.b  d2,2(a2)
        moveq   #0,d3
        move.b  1(a1),d3
        addi.w  #$6c,d3
        move.w  d3,d4
        lsr.w   #1,d4
        move.b  d4,1(a2)
        andi.b  #1,d3
        btst    #8,d0
        beq.s   sprite_vstop_high
        ori.b   #4,d3
sprite_vstop_high:
        btst    #8,d2
        beq.s   sprite_control_ready
        ori.b   #2,d3
sprite_control_ready:
        move.b  d3,3(a2)
        bra.s   sprite_done
hide_sprite:
        clr.l   (a2)
sprite_done:
        dbra    d7,next_sprite
        movem.l (sp)+,d0-d7/a0-a3
        rts

; Deferred SG scoreboard/VDP writes are collected for later bitmap rendering.
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
        include "build/translation/player-frame-routines.s"

        even
simulation_phase:   dc.l 0
simulation_updates: dc.w 0
presentation_frames: dc.w 0
log_timer:         dc.w 50
game_input_bits:   dc.b 0
        even
vdp_count:         dc.b 0
        even
vdp_ptr:           dc.l 0
vdp_log:           dcb.b 4,0
sprite_source_offsets: dc.b 4,8,12,16,20,24,28,36
        even
sprite_targets:
        dc.l sprite0,sprite1,sprite2,sprite3,sprite4,sprite5,sprite6,sprite7
log_text:          dc.b "LIVE F="
log_frames:        dc.b "00 U="
log_updates:       dc.b "00 I="
log_input:         dc.b "00 X="
log_player_x:      dc.b "00 SX="
log_sprite_x:      dc.b "00",0
hex_digits:        dc.b "0123456789ABCDEF"
        even
pointer_sources:
        dc.l plane0,plane1,plane2,plane3
        dc.l sprite0,sprite1,sprite2,sprite3,sprite4,sprite5,sprite6,sprite7
pointer_targets:
        dc.l cop_bpl0h+2,cop_bpl1h+2,cop_bpl2h+2,cop_bpl3h+2
        dc.l cop_spr0h+2,cop_spr1h+2,cop_spr2h+2,cop_spr3h+2
        dc.l cop_spr4h+2,cop_spr5h+2,cop_spr6h+2,cop_spr7h+2
        even
initial_ram: incbin "build/translation/live-initial-ram.bin"
        even
virtual_memory: incbin "build/translation/player-frame-memory.bin"
shadow_vram: dcb.b 16384,0

        include "amiga/sprite_probe_display.i"
