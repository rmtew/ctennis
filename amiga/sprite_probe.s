        section code,code
start:
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

        lea     $dff000,a6
        move.w  #$7fff,$09a(a6)     ; stop OS interrupts for this bounded demo
        move.w  #$7fff,$096(a6)     ; clear DMA before installing our display
        move.l  #copperlist,$080(a6)
        move.w  #0,$088(a6)
        move.w  #$83a0,$096(a6)     ; master, bitplane, copper, sprite DMA
wait_frame:
        move.w  $006(a6),d0
        andi.w  #$ff00,d0
        cmpi.w  #$f000,d0          ; update only in PAL vertical blank
        bne.s   wait_frame
        tst.b   state_armed
        bne.s   advance_clock
        move.w  $00c(a6),d0        ; JOY1DAT bit 9 is joystick left
        btst    #9,d0
        beq.s   wait_blanking_end
        move.b  #1,state_armed     ; resume from source frame-1299 state
advance_clock:
        move.l  state_phase,d4
        addi.l  #59922738,d4      ; 59.922738 source updates per second
next_update:
        cmpi.l  #50000000,d4      ; PAL presentation is 50 frames per second
        bcs.s   updates_done
        subi.l  #50000000,d4
        bsr     simulation_update
        bra.s   next_update
updates_done:
        move.l  d4,state_phase
        bsr     render_lower_x
        bsr     render_ball
        addq.w  #1,state_frames
        cmpi.w  #50,state_frames
        beq.s   clock_checkpoint
        cmpi.w  #100,state_frames
        bne.s   wait_blanking_end
clock_checkpoint:
        bsr     log_clock
wait_blanking_end:
        move.w  $006(a6),d0
        andi.w  #$ff00,d0
        cmpi.w  #$f000,d0
        beq.s   wait_blanking_end
        bra.s   wait_frame

simulation_update:
        move.b  state_tick,state_last_tick
        clr.b   state_input
        move.w  $00c(a6),d0
        btst    #9,d0
        beq.s   test_right
        move.b  #4,state_input
        bra.s   begin_update
test_right:
        btst    #1,d0
        beq.s   begin_update
        move.b  #1,state_input
begin_update:
        bsr     serve_wait_update
        tst.b   state_input
        beq.s   finish_update
move_lower:
        moveq   #1,d1
        btst    #0,state_tick
        beq.s   step_ready
        addq.w  #1,d1
step_ready:
        moveq   #0,d2
        move.b  state_x,d2
        cmpi.b  #4,state_input
        bne.s   move_lower_right
        sub.w   d1,d2
        cmpi.w  #$80,d2           ; source lower X minimum, row zero
        bcs.s   finish_update
        move.b  d2,state_x
        addq.b  #1,state_held
        bra.s   finish_update
move_lower_right:
        add.w   d1,d2
        cmpi.w  #$c8,d2           ; source upper bound is exclusive
        bcc.s   finish_update
        move.b  d2,state_x
finish_update:
        addq.b  #1,state_tick
        addq.w  #1,state_updates
        cmpi.w  #40,state_updates
        bhi.s   update_done
        bsr     log_state
update_done:
        move.b  state_input,state_prev_input
        rts

serve_wait_update:
        ; Source $0B7A: update the attached ball before player movement.
        move.b  state_x,state_visible_x
        move.b  state_ball_x,state_visible_ball_x
        move.b  state_ball_y,state_visible_ball_y
        addq.b  #1,state_ball_step
        moveq   #0,d0
        move.b  state_ball_step,d0
        move.w  d0,d1
        add.w   d1,d1
        subi.w  #$40,d1
        bpl.s   positive_height
        neg.w   d1
        moveq   #1,d2
        bra.s   height_magnitude
positive_height:
        moveq   #0,d2
height_magnitude:
        mulu.w  d0,d1
        lsr.l   #5,d1
        moveq   #$a0,d0
        tst.b   d2
        beq.s   add_height
        sub.w   d1,d0
        bra.s   height_ready
add_height:
        add.w   d1,d0
height_ready:
        move.b  d0,state_ball_y
        cmpi.b  #$a0,d0
        bcs.s   attach_ball
        clr.b   state_ball_step
attach_ball:
        move.b  state_x,d0
        addi.b  #$14,d0
        move.b  d0,state_ball_x
        rts

render_lower_x:
        moveq   #0,d0
        move.b  state_visible_x,d0
        addi.w  #$006c,d0         ; source X to Amiga sprite HSTART
        move.w  d0,d1
        lsr.w   #1,d1
        move.b  d1,sprite0+1
        move.b  d1,sprite1+1
        move.b  d1,sprite2+1
        andi.b  #1,d0
        move.b  d0,sprite0+3
        move.b  d0,sprite1+3
        move.b  d0,sprite2+3
        rts

render_ball:
        moveq   #0,d0
        move.b  state_visible_ball_x,d0
        addi.w  #$006c,d0
        move.w  d0,d1
        lsr.w   #1,d1
        move.b  d1,sprite3+1
        move.b  d1,sprite7+1
        andi.b  #1,d0
        move.b  d0,sprite3+3
        move.b  d0,sprite7+3
        moveq   #0,d0
        move.b  state_visible_ball_y,d0
        addi.w  #$2d,d0
        move.b  d0,sprite3
        addi.w  #16,d0
        move.b  d0,sprite3+2
        rts

log_state:
        movem.l d0-d2/a0-a1,-(sp)
        lea     log_input(pc),a0
        moveq   #0,d0
        move.b  state_input,d0
        bsr     hex_byte
        lea     log_x(pc),a0
        moveq   #0,d0
        move.b  state_x,d0
        bsr     hex_byte
        lea     log_tick(pc),a0
        moveq   #0,d0
        move.b  state_last_tick,d0
        bsr     hex_byte
        lea     log_held(pc),a0
        moveq   #0,d0
        move.b  state_held,d0
        bsr     hex_byte
        lea     log_update_count(pc),a0
        moveq   #0,d0
        move.b  state_updates+1,d0
        bsr     hex_byte
        lea     log_ball_y(pc),a0
        moveq   #0,d0
        move.b  state_ball_y,d0
        bsr     hex_byte
        lea     log_ball_x(pc),a0
        moveq   #0,d0
        move.b  state_ball_x,d0
        bsr     hex_byte
        lea     log_ball_step(pc),a0
        moveq   #0,d0
        move.b  state_ball_step,d0
        bsr     hex_byte
        move.l  #log_text,-(sp)
        move.l  #86,-(sp)         ; Copperline/WinUAE uaelib debug string
        jsr     $f0ff60
        addq.l  #8,sp
        movem.l (sp)+,d0-d2/a0-a1
        rts
log_clock:
        movem.l d0-d2/a0-a1,-(sp)
        lea     clock_frames(pc),a0
        moveq   #0,d0
        move.b  state_frames+1,d0
        bsr     hex_byte
        lea     clock_updates(pc),a0
        moveq   #0,d0
        move.b  state_updates+1,d0
        bsr     hex_byte
        move.l  #clock_text,-(sp)
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
        andi.w  #$000f,d0
        move.b  (a1,d0.w),(a0)+
        rts

pointer_sources:
        dc.l plane0,plane1,plane2,plane3
        dc.l sprite0,sprite1,sprite2,sprite3,sprite4,sprite5,sprite6,sprite7
pointer_targets:
        dc.l cop_bpl0h+2,cop_bpl1h+2,cop_bpl2h+2,cop_bpl3h+2
        dc.l cop_spr0h+2,cop_spr1h+2,cop_spr2h+2,cop_spr3h+2
        dc.l cop_spr4h+2,cop_spr5h+2,cop_spr6h+2,cop_spr7h+2
state_x:          dc.b $c0
state_visible_x:  dc.b $c0
state_tick:       dc.b $a9
state_last_tick:  dc.b $a8
state_input:      dc.b 0
state_prev_input: dc.b 0
state_held:       dc.b 0
state_armed:      dc.b 0
        even
state_updates:    dc.w 0
state_frames:     dc.w 0
state_phase:      dc.l 0
state_ball_y:     dc.b $9b
state_ball_x:     dc.b $d4
state_ball_step:  dc.b $1d
state_visible_ball_y: dc.b $9b
state_visible_ball_x: dc.b $d4
log_text:         dc.b "MOVE I="
log_input:        dc.b "00 X="
log_x:            dc.b "00 T="
log_tick:         dc.b "00 H="
log_held:         dc.b "00 U="
log_update_count: dc.b "00 BY="
log_ball_y:       dc.b "00 BX="
log_ball_x:       dc.b "00 BS="
log_ball_step:    dc.b "00",0
clock_text:       dc.b "CLOCK F="
clock_frames:     dc.b "00 U="
clock_updates:    dc.b "00",0
hex_digits:       dc.b "0123456789ABCDEF"
        even

        section display_data,data,chip
copperlist:
        dc.w $008e,$2c81,$0090,$ecc1
        dc.w $0092,$0038,$0094,$00b0
        dc.w $0100,$4200,$0102,$0000,$0104,$0024
        dc.w $0108,$0000,$010a,$0000
cop_bpl0h: dc.w $00e0,0
           dc.w $00e2,0
cop_bpl1h: dc.w $00e4,0
           dc.w $00e6,0
cop_bpl2h: dc.w $00e8,0
           dc.w $00ea,0
cop_bpl3h: dc.w $00ec,0
           dc.w $00ee,0
cop_spr0h: dc.w $0120,0
           dc.w $0122,0
cop_spr1h: dc.w $0124,0
           dc.w $0126,0
cop_spr2h: dc.w $0128,0
           dc.w $012a,0
cop_spr3h: dc.w $012c,0
           dc.w $012e,0
cop_spr4h: dc.w $0130,0
           dc.w $0132,0
cop_spr5h: dc.w $0134,0
           dc.w $0136,0
cop_spr6h: dc.w $0138,0
           dc.w $013a,0
cop_spr7h: dc.w $013c,0
           dc.w $013e,0

        ; Background colours, sampled from the MAME VDP capture and rounded
        ; to the Amiga's four-bit RGB components.
        dc.w $0180,$000,$0182,$000,$0184,$2c4,$0186,$6d7
        dc.w $0188,$55e,$018a,$77f,$018c,$000,$018e,$000
        dc.w $0190,$000,$0192,$f77,$0194,$dc5,$0196,$000
        dc.w $0198,$000,$019a,$c5b,$019c,$ccc,$019e,$fff
        ; Sprite pairs 0/1, 2/3, 4/5, 6/7. Colour zero is transparent.
        dc.w $01a2,$fff,$01a4,$55e,$01a6,$000
        dc.w $01aa,$55e,$01ac,$fff,$01ae,$000
        dc.w $01b2,$fff,$01b4,$c5b,$01b6,$000
        dc.w $01ba,$c5b,$01bc,$000,$01be,$000
        dc.w $ffff,$fffe

plane0: incbin "build/amiga/sprite-probe/plane0.bin"
plane1: incbin "build/amiga/sprite-probe/plane1.bin"
plane2: incbin "build/amiga/sprite-probe/plane2.bin"
plane3: incbin "build/amiga/sprite-probe/plane3.bin"
sprite0: incbin "build/amiga/sprite-probe/sprite0.bin"
sprite1: incbin "build/amiga/sprite-probe/sprite1.bin"
sprite2: incbin "build/amiga/sprite-probe/sprite2.bin"
sprite3: incbin "build/amiga/sprite-probe/sprite3.bin"
sprite4: incbin "build/amiga/sprite-probe/sprite4.bin"
sprite5: incbin "build/amiga/sprite-probe/sprite5.bin"
sprite6: incbin "build/amiga/sprite-probe/sprite6.bin"
sprite7: incbin "build/amiga/sprite-probe/sprite7.bin"
