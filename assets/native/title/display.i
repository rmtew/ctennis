title_copper:
        dc.w $008e,$2c81,$0090,$ecc1,$0092,$0048,$0094,$00c0
        dc.w $0100,$4200,$0102,0,$0104,0,$0108,0,$010a,0
title_pointer0: dc.w $00e0,0,$00e2,0
title_pointer1: dc.w $00e4,0,$00e6,0
title_pointer2: dc.w $00e8,0,$00ea,0
title_pointer3: dc.w $00ec,0,$00ee,0
        dc.w $0180,$000
        dc.w $0182,$000
        dc.w $0184,$2c4
        dc.w $0186,$6d7
        dc.w $0188,$55e
        dc.w $018a,$77f
        dc.w $018c,$555 ; subdued title build hash, previously unused slot6
        dc.w $018e,$000
        dc.w $0190,$000
        dc.w $0192,$f77
        dc.w $0194,$dc5
        dc.w $0196,$000
        dc.w $0198,$000
        dc.w $019a,$e33
        dc.w $019c,$ccc
        dc.w $019e,$fff
        dc.w $fd01,$fffe ; retired bottom interval
        dc.w $009c,$8010 ; Copper interrupt for latest completed scene
        dc.w $ffff,$fffe
title_plane0: incbin "assets/native/title/plane0.bin"
title_plane1: incbin "assets/native/title/plane1.bin"
title_plane2: incbin "assets/native/title/plane2.bin"
title_plane3: incbin "assets/native/title/plane3.bin"
