; Bounded intrinsic endpoint attempt on a complete private post-launch state.
; A5=318-byte input; D0=3 accepted original bounce,0 rejected; D1=phases (0
; rejected), D2=guard reason (0 accepted), D3=point checks (at most 6).
; D4-D7/A0-A6 preserved; D0-D3/CCR scratch. Rejection preserves all 318 bytes.
; No fallback, player/AI, scene, audio, clock, input, history or RNG work.
; Caller derives NET/OUT/LANDING from final contact flags, not D0 alone.
landing_try_begin:
landing_try_fast:
        movem.l d4-d7/a0-a6,-(sp)
        lea     -48(sp),sp
        move.l  sp,a3
        lea     game_play_state-game_core_state(a5),a4
        clr.w   12(a3)
        clr.w   14(a3)
        move.w  #14,10(a3)
        move.b  G_CONTACT(a4),d0
        andi.b  #$8b,d0
        bne     .fallback
        moveq   #0,d0
        move.b  G_BASE_Y(a4),d0
        move.w  d0,20(a3)
        moveq   #0,d1
        move.b  G_BASE_SCREEN_Y(a4),d1
        move.w  d1,22(a3)
        sub.w   d1,d0
        move.w  #1,10(a3)
        tst.w   d0
        bmi     .fallback
        move.w  d0,0(a3)
        move.w  #2,10(a3)
        btst    #6,G_FLIGHT(a4)
        beq     .fallback
        btst    #7,G_FLIGHT(a4)
        bne     .fallback
        move.w  #11,10(a3)
        tst.b   G_STEP(a4)
        bne     .fallback
        moveq   #0,d0
        move.b  G_VELOCITY_Y(a4),d0
        andi.w  #127,d0
        move.w  #3,10(a3)
        cmpi.w  #4,d0
        bcs     .fallback
        btst    #7,G_VELOCITY_Y(a4)
        beq     .positive_y
        neg.w   d0
.positive_y:
        move.w  d0,2(a3)
        move.w  #4,10(a3)
        btst    #3,G_FLIGHT(a4)
        beq     .net_safe
        btst    #0,G_CONTACT(a4)
        beq     .fallback
.net_safe:
        moveq   #0,d1
        move.b  G_VELOCITY_Z(a4),d1
        move.w  d1,4(a3)
        move.w  0(a3),d0
        lsl.w   #5,d0
        addq.w  #1,d0
        bsr     landing_root
        move.w  d0,8(a3)
        move.w  0(a3),d0
        lsl.w   #5,d0
        addi.w  #63,d0
        move.w  4(a3),d1
        bsr     landing_root
        move.w  d0,6(a3)
        move.w  #5,10(a3)
        cmpi.w  #255,d0
        bhi     .fallback
        moveq   #0,d1
        move.b  G_VELOCITY_X(a4),d1
        andi.w  #127,d1
        move.w  d1,16(a3)
        mulu.w  d0,d1
        move.w  #6,10(a3)
        cmpi.l  #8192,d1
        bcc     .fallback
        move.w  2(a3),d1
        bpl     .y_magnitude
        neg.w   d1
.y_magnitude:
        mulu.w  d0,d1
        cmpi.l  #8192,d1
        bcc     .fallback
        move.w  2(a3),d1
        sub.w   4(a3),d1
        move.w  d1,32(a3)
        move.w  #7,10(a3)
        move.w  32(a3),d0
        bsr     landing_factor_guard
        tst.w   d1
        bne     .fallback
        move.w  32(a3),d0
        add.w   6(a3),d0
        add.w   6(a3),d0
        bsr     landing_factor_guard
        tst.w   d1
        bne     .fallback
        clr.l   24(a3)
        clr.l   28(a3)
        move.w  6(a3),d0
        bsr     landing_extreme
        move.w  32(a3),d0
        neg.w   d0
        asr.w   #2,d0           ; Python floor division for vertex neighbour
        bpl     .vertex_nonnegative
        moveq   #0,d0
.vertex_nonnegative:
        cmp.w   6(a3),d0
        bls     .vertex_bounded
        move.w  6(a3),d0
.vertex_bounded:
        move.w  d0,34(a3)
        bsr     landing_extreme
        move.w  34(a3),d0
        cmp.w   6(a3),d0
        bcc     .extremes_done
        addq.w  #1,d0
        bsr     landing_extreme
.extremes_done:
        move.w  #8,10(a3)
        cmpi.l  #-8192,24(a3)
        ble     .fallback
        cmpi.l  #8192,28(a3)
        bge     .fallback
        move.w  #9,10(a3)
        move.l  24(a3),d0
        bsr     landing_trunc32
        add.w   22(a3),d0
        bmi     .fallback
        move.l  28(a3),d0
        bsr     landing_trunc32
        add.w   22(a3),d0
        cmpi.w  #255,d0
        bgt     .fallback
        moveq   #0,d1
        move.b  G_BASE_X(a4),d1
        move.w  d1,18(a3)
        move.w  #10,10(a3)
        cmpi.w  #32,d1
        bcs     .fallback
        cmpi.w  #232,d1
        bcc     .fallback
        move.w  16(a3),d0
        mulu.w  6(a3),d0
        lsr.l   #5,d0
        btst    #7,G_VELOCITY_X(a4)
        beq     .x_positive
        neg.w   d0
.x_positive:
        add.w   d1,d0
        cmpi.w  #32,d0
        blt     .fallback
        cmpi.w  #232,d0
        bge     .fallback
        move.w  #13,10(a3)
        move.w  20(a3),d1
        cmpi.w  #4,d1
        bcs     .fallback
        cmpi.w  #204,d1
        bcc     .fallback
        move.w  2(a3),d0
        muls.w  6(a3),d0
        bsr     landing_trunc32
        add.w   d1,d0
        cmpi.w  #4,d0
        blt     .fallback
        cmpi.w  #204,d0
        bge     .fallback
        clr.w   10(a3)
        move.b  G_STEP(a4),40(a3)
        move.b  G_BALL_COLOUR(a4),41(a3)
        move.b  G_SHADOW_COLOUR(a4),42(a3)
        move.b  G_BALL_X(a4),43(a3)
        move.b  G_COURT_X(a4),44(a3)
        move.b  G_COURT_Y(a4),45(a3)
        move.b  G_BALL_Y(a4),46(a3)
        move.w  8(a3),d7
.candidate:
        move.w  d7,d0
        subq.w  #1,d0
        move.b  d0,G_STEP(a4)
        jsr     game_advance_ball
        addq.w  #1,12(a3)
        move.b  G_COURT_Y(a4),d0
        cmp.b   G_BALL_Y(a4),d0
        bcs     .fast_bounce
        addq.w  #1,d7
        cmp.w   6(a3),d7
        bls     .candidate
        ; Defensive rollback of every byte advance can write; never continue
        ; a fallback from a partially evaluated candidate state.
        move.b  40(a3),G_STEP(a4)
        move.b  41(a3),G_BALL_COLOUR(a4)
        move.b  42(a3),G_SHADOW_COLOUR(a4)
        move.b  43(a3),G_BALL_X(a4)
        move.b  44(a3),G_COURT_X(a4)
        move.b  45(a3),G_COURT_Y(a4)
        move.b  46(a3),G_BALL_Y(a4)
        move.w  #12,10(a3)
        bra     .fallback
.fast_bounce:
        move.w  d7,14(a3)
        jsr     game_bounce
        moveq   #3,d0
        bra     .done
.fallback:
        moveq   #0,d0
.done:
        moveq   #0,d1
        move.w  14(a3),d1
        moveq   #0,d2
        move.w  10(a3),d2
        moveq   #0,d3
        move.w  12(a3),d3
        lea     48(sp),sp
        movem.l (sp)+,d4-d7/a0-a6
        rts

; Exact first ascending crossing of 2*n*n-z*n >= positive K.
; Eight bounded decisions find the largest failing n in 0..255; +1 is the root.
; Predicate is monotone because K>0 excludes the descending nonpositive arm.
; D0=K, D1=z -> D0=root; D1-D5 scratch.
landing_root:
        move.w  d0,d4
        moveq   #0,d2
        move.w  #128,d3
.root_bit:
        move.w  d2,d0
        add.w   d3,d0
        move.w  d0,d5
        mulu.w  d0,d0
        add.l   d0,d0
        mulu.w  d1,d5
        sub.l   d5,d0
        ext.l   d4
        cmp.l   d4,d0
        bge     .root_keep
        add.w   d3,d2
.root_keep:
        lsr.w   #1,d3
        bne     .root_bit
        moveq   #0,d0
        move.w  d2,d0
        addq.w  #1,d0
        rts

; D0 signed factor -> D1=0 iff absolute value <=255. D0 preserved.
landing_factor_guard:
        moveq   #1,d1
        cmpi.w  #-255,d0
        blt     .factor_done
        cmpi.w  #255,d0
        bgt     .factor_done
        moveq   #0,d1
.factor_done:
        rts

; Incorporate exact quadratic numerator at n=D0 into frame min/max.
landing_extreme:
        move.w  d0,d1
        add.w   d0,d1
        add.w   32(a3),d1
        muls.w  d0,d1
        cmp.l   24(a3),d1
        bge     .not_min
        move.l  d1,24(a3)
.not_min:
        cmp.l   28(a3),d1
        ble     .not_max
        move.l  d1,28(a3)
.not_max:
        rts

; D0 signed long -> signed word truncation toward zero /32. D1 preserved.
landing_trunc32:
        tst.l   d0
        bpl     .trunc_positive
        neg.l   d0
        lsr.l   #5,d0
        neg.w   d0
        rts
.trunc_positive:
        lsr.l   #5,d0
        rts
landing_try_end:
