        section display_data,data,chip
copperlist:
        dc.w $008e,$2c81,$0090,$ecc1
        ifd ENHANCED_INTERFACE
        dc.w $0092,$0048,$0094,$00c0
        else
        dc.w $0092,$0038,$0094,$00b0
        endif
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
cop_spr_pair0_c1: dc.w $01a2,$fff
cop_spr_pair0_c2: dc.w $01a4,$55e
        dc.w $01a6,$000
cop_spr_pair1_c1: dc.w $01aa,$55e
cop_spr_pair1_c2: dc.w $01ac,$fff
        dc.w $01ae,$000
cop_spr_pair2_c1: dc.w $01b2,$fff
cop_spr_pair2_c2: dc.w $01b4,$c5b
        dc.w $01b6,$000
cop_spr_pair3_c1: dc.w $01ba,$c5b
cop_spr_pair3_c2: dc.w $01bc,$000
        dc.w $01be,$000
        ifd SCORE_COPPER_DISPLAY
score_cop_commands:
        include "build/amiga/score-copper-probe/score-cop-commands.i"
        endif
        dc.w $ffff,$fffe
copperlist_end:

        ifd SCORE_COPPER_DISPLAY
plane0: incbin "build/amiga/score-copper-probe/plane0.bin"
        else
plane0: incbin "build/amiga/sprite-probe/plane0.bin"
        endif
        ifd SCORE_COPPER_DISPLAY
plane1: incbin "build/amiga/score-copper-probe/plane1.bin"
plane2: incbin "build/amiga/score-copper-probe/plane2.bin"
plane3: incbin "build/amiga/score-copper-probe/plane3.bin"
        else
plane1: incbin "build/amiga/sprite-probe/plane1.bin"
plane2: incbin "build/amiga/sprite-probe/plane2.bin"
plane3: incbin "build/amiga/sprite-probe/plane3.bin"
        endif
sprite0: incbin "build/amiga/sprite-probe/sprite0.bin"
sprite1: incbin "build/amiga/sprite-probe/sprite1.bin"
sprite2: incbin "build/amiga/sprite-probe/sprite2.bin"
sprite3: incbin "build/amiga/sprite-probe/sprite3.bin"
sprite4: incbin "build/amiga/sprite-probe/sprite4.bin"
sprite5: incbin "build/amiga/sprite-probe/sprite5.bin"
sprite6: incbin "build/amiga/sprite-probe/sprite6.bin"
sprite7: incbin "build/amiga/sprite-probe/sprite7.bin"
