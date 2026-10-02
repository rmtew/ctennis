; User-selected square LED preview, authored 16x16 masks. Build all variants
; once before title setup / timer start; live score changes still switch pointers.
init_square_score_banks:
        movem.l d0-d7/a0-a6,-(sp)
        lea     -32(sp),sp
        move.l  sp,a5
        moveq   #0,d6
square_score_variant:
        move.l  a5,a0
        moveq   #7,d7
square_score_clear:
        clr.l   (a0)+
        dbra    d7,square_score_clear
        moveq   #0,d5
square_score_digit:
        move.w  d6,d0
        add.w   d0,d0
        add.w   d5,d0
        lea     square_score_states(pc),a0
        moveq   #0,d1
        move.b  0(a0,d0.w),d1
        bmi     square_score_next_digit
        lea     square_score_glyphs(pc),a0
        moveq   #0,d3
        move.b  0(a0,d1.w),d3
        move.w  d5,d4
        mulu    #9,d4
        lea     square_score_alignment(pc),a1
        moveq   #0,d0
        move.b  0(a1,d6.w),d0
        ext.w   d0
        add.w   d0,d4
        cmpi.w  #4,d6
        bne.s   square_score_positioned
        moveq   #4,d4 ; one centred A, not Ad
square_score_positioned:
        lea     square_score_rectangles(pc),a0
        moveq   #0,d7
square_score_segment:
        btst    d7,d3
        beq.s   square_score_next_segment
        ; Inclusive x1,y1,x2,y2 rectangles in a 7x15 digit, plus y margin1.
        moveq   #15,d1
        sub.b   2(a0),d1
        add.b   (a0),d1
        move.w  #$ffff,d0
        lsr.w   d1,d0
        moveq   #15,d1
        sub.b   2(a0),d1
        sub.w   d4,d1
        lsl.w   d1,d0
        moveq   #0,d1
        move.b  1(a0),d1
        addq.w  #1,d1
        add.w   d1,d1
        lea     0(a5,d1.w),a1
        moveq   #0,d1
        move.b  3(a0),d1
        sub.b   1(a0),d1
square_score_segment_row:
        or.w    d0,(a1)+
        dbra    d1,square_score_segment_row
square_score_next_segment:
        addq.l  #4,a0
        addq.w  #1,d7
        cmpi.w  #7,d7
        bne.s   square_score_segment
square_score_next_digit:
        addq.w  #1,d5
        cmpi.w  #2,d5
        bne     square_score_digit
        ; Keep the exact four streams/28 full-width banks expected by Copper.
        ; Seed from the static court, replacing only this player's two bytes.
        lea     square_score_streams(pc),a4
        moveq   #3,d5
square_score_stream:
        move.l  (a4)+,a0
        move.l  (a4)+,a1
        move.w  d6,d0
        mulu    #512,d0
        adda.w  d0,a1
        move.l  a1,a2
        moveq   #127,d7
square_score_copy:
        move.l  (a0)+,(a1)+
        dbra    d7,square_score_copy
        adda.w  (a4)+,a2
        move.l  a5,a3
        moveq   #15,d7
square_score_stamp:
        move.w  (a3)+,(a2)
        adda.w  #32,a2
        dbra    d7,square_score_stamp
        dbra    d5,square_score_stream
        addq.w  #1,d6
        cmpi.w  #7,d6
        bne     square_score_variant
        lea     32(sp),sp
        movem.l (sp)+,d0-d7/a0-a6
init_square_score_banks_end:
        rts
square_score_streams:
        dc.l plane2+48*32,score_bank_point_a_0_p2
        dc.w 2
        dc.l plane2+48*32,score_bank_point_b_0_p2
        dc.w 28
        dc.l plane0+48*32,score_bank_point_b_0_p0
        dc.w 28
        dc.l plane3+48*32,score_bank_point_b_0_p3
        dc.w 28
square_score_definitions:
square_score_rectangles:
        incbin "assets/native/court/square-led-definitions.bin"
square_score_glyphs equ square_score_definitions+28
square_score_states equ square_score_definitions+34
square_score_definitions_end:
; Layout-only centring; original square segment definitions stay byte-identical.
square_score_alignment:
        dc.b -5,-2,-1,0,0,0,0
        even
