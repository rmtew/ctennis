; Build six unique point masks, a WIN mask and three fixed HUD strips once.
; Only the current building bank is stamped during play.
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
        ; Logical state5 duplicates40; slot5 contains logical state6 (blank).
        move.w  d6,d0
        cmpi.w  #6,d0
        bne.s   square_score_unique
        moveq   #5,d0
square_score_unique:
        lsl.w   #5,d0
        lea     hud_point_tiles,a1
        adda.w  d0,a1
        move.l  a5,a0
        moveq   #7,d7
square_score_store_tile:
        move.l  (a0)+,(a1)+
        dbra    d7,square_score_store_tile
        addq.w  #1,d6
        cmpi.w  #5,d6
        bne.s   square_score_next_variant
        addq.w  #1,d6
square_score_next_variant:
        cmpi.w  #7,d6
        bne     square_score_variant
        lea     32(sp),sp

        ; Exact retained font columns: W at17, I at23, N at27 (word x16).
        lea     ui_font+'W'*8,a0
        lea     ui_font+'I'*8,a2
        lea     ui_font+'N'*8,a3
        lea     hud_win_tile,a1
        moveq   #0,d6
square_score_win_row:
        moveq   #0,d0
        move.b  0(a0,d6.w),d0
        andi.w  #$f8,d0
        lsl.w   #7,d0
        moveq   #0,d1
        move.b  0(a2,d6.w),d1
        andi.w  #$70,d1
        lsl.w   #2,d1
        or.w    d1,d0
        moveq   #0,d1
        move.b  0(a3,d6.w),d1
        andi.w  #$f8,d1
        lsr.w   #3,d1
        or.w    d1,d0
        move.w  d0,(a1)+
        addq.w  #1,d6
        cmpi.w  #8,d6
        bne.s   square_score_win_row

        lea     hud_bank0,a1
        moveq   #2,d6
square_score_init_bank:
        lea     plane0+48*32,a0
        bsr.s   square_score_copy_point
        lea     plane2+48*32,a0
        bsr.s   square_score_copy_point
        lea     plane3+48*32,a0
        bsr.s   square_score_copy_point
        lea     plane1+72*32,a0
        move.w  #1536/4-1,d7
square_score_copy_games:
        move.l  (a0)+,(a1)+
        dbra    d7,square_score_copy_games
        dbra    d6,square_score_init_bank
        movem.l (sp)+,d0-d7/a0-a6
init_square_score_banks_end:
        rts
square_score_copy_point:
        move.w  #512/4-1,d7
square_score_copy:
        move.l  (a0)+,(a1)+
        dbra    d7,square_score_copy
        rts
        even
square_score_definitions:
square_score_rectangles:
        incbin "assets/native/court/square-led-definitions.bin"
square_score_glyphs equ square_score_definitions+28
square_score_states equ square_score_definitions+34
square_score_definitions_end:
