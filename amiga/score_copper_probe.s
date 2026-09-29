        section code,code
SCORE_COPPER_PROBE equ 1

start:
        lea     pointer_sources(pc),a0
        lea     pointer_targets(pc),a1
        moveq   #11,d7
patch_display_pointers:
        move.l  (a0)+,d0
        move.l  (a1)+,a2
        move.l  d0,d1
        swap    d1
        move.w  d1,(a2)
        move.w  d0,4(a2)
        dbra    d7,patch_display_pointers

        lea     score_cop_commands,a0
        lea     plane2+41*32,a1
        lea     score_overlay_zero+2,a2
        moveq   #15,d7
patch_score_rows:
        move.l  a2,d0
        bsr     patch_base_pointer
        move.l  a1,d0
        bsr     patch_overlay_pointer
        adda.w  #24,a0
        adda.w  #32,a1
        adda.w  #32,a2
        dbra    d7,patch_score_rows
        lea     $dff000,a6
        move.w  #$7fff,$09a(a6)
        move.w  #$7fff,$096(a6)
        move.l  #copperlist,$080(a6)
        move.w  #0,$088(a6)
        move.w  #$83a0,$096(a6)
wait_forever:
        move.w  $006(a6),d0
        andi.w  #$ff00,d0
        cmpi.w  #$f000,d0
        bne.s   wait_forever
        move.b  $bfe001,d0
        btst    #7,d0
        bne.s   select_zero
        lea     score_overlay_one+2,a2
        bra.s   patch_selected_score
select_zero:
        lea     score_overlay_zero+2,a2
patch_selected_score:
        lea     score_cop_commands,a0
        moveq   #15,d7
patch_selected_rows:
        move.l  a2,d0
        bsr     patch_base_pointer
        adda.w  #24,a0
        adda.w  #32,a2
        dbra    d7,patch_selected_rows
wait_frame_end:
        move.w  $006(a6),d0
        andi.w  #$ff00,d0
        cmpi.w  #$f000,d0
        beq.s   wait_frame_end
        bra.s   wait_forever

patch_base_pointer:
        move.l  d0,d1
        swap    d1
        move.w  d1,6(a0)
        move.w  d0,10(a0)
        rts
patch_overlay_pointer:
        move.l  d0,d1
        swap    d1
        move.w  d1,18(a0)
        move.w  d0,22(a0)
        rts

        even
pointer_sources:
        dc.l plane0,plane1,plane2,plane3
        dc.l sprite0,sprite1,sprite2,sprite3,sprite4,sprite5,sprite6,sprite7
pointer_targets:
        dc.l cop_bpl0h+2,cop_bpl1h+2,cop_bpl2h+2,cop_bpl3h+2
        dc.l cop_spr0h+2,cop_spr1h+2,cop_spr2h+2,cop_spr3h+2
        dc.l cop_spr4h+2,cop_spr5h+2,cop_spr6h+2,cop_spr7h+2

        include "amiga/sprite_probe_display.i"
        even
score_overlay_zero: incbin "build/amiga/score-copper-probe/overlay-point-0.bin"
score_overlay_one: incbin "build/amiga/score-copper-probe/overlay-point-1.bin"
