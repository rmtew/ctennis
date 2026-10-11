; Native integer trajectory arithmetic. Byte-sized signed magnitudes preserve
; the original feel; intermediates are ordinary 68000 words/longs.
; D0,D1 byte factors, D2 byte divisor -> D0 byte quotient. Clobbers D1-D4.
; Keep the original eight-bit quotient overflow/zero-divisor behavior.
game_ratio:
        andi.l  #255,d0
        andi.l  #255,d1
        andi.l  #255,d2
        mulu.w  d1,d0
        moveq   #0,d3
        moveq   #7,d4
.game_ratio_bit:
        add.l   d0,d0
        or.l    d3,d0
        move.l  d0,d1
        lsr.l   #8,d1
        moveq   #0,d3
        btst    #16,d0
        bne   .game_ratio_subtract
        cmp.w   d2,d1
        bcs   .game_ratio_next
.game_ratio_subtract:
        sub.b   d2,d1
        andi.l  #255,d0
        lsl.w   #8,d1
        or.w    d1,d0
        moveq   #1,d3
.game_ratio_next:
        andi.l  #65535,d0
        dbra    d4,.game_ratio_bit
        add.b   d0,d0
        or.b    d3,d0
        andi.l  #255,d0
        rts

; Exact byte-factor specialization of game_ratio for divisor 32.
; Preserve legacy overflow rather than truncating ordinary division.
; D0,D1 byte factors -> D0 full-long byte quotient. Clobbers D1-D4.
; D2=32, D3=quotient bit0, D4=$0000ffff; final CCR matches game_ratio.
; See docs/ball-query-math-proof.md for the rolling three-bit derivation.
game_ratio32:
        andi.l  #255,d0
        andi.l  #255,d1
        moveq   #32,d2
        mulu.w  d1,d0
        lsr.w   #5,d0           ; N=product/32, at most 2047
        cmpi.w  #256,d0
        bcs   .game_ratio32_done
        move.w  d0,d1
        subi.w  #256,d1         ; seed h-1 followed by low eight bits
        move.w  d1,d3
        lsr.w   #1,d3
        and.w   d3,d1
        lsr.w   #1,d3
        and.w   d3,d1           ; ends of runs of three ones
        move.w  d1,d3
        lsr.w   #1,d3
        or.w    d3,d1
        move.w  d1,d3
        lsr.w   #2,d3
        or.w    d3,d1
        move.w  d1,d3
        lsr.w   #4,d3
        or.w    d3,d1           ; smear highest marker downwards
        not.b   d1
        or.b    d1,d0
.game_ratio32_done:
        moveq   #0,d3
        add.w   d3,d0           ; bounded N clears X regardless of caller CCR
        move.b  d0,d3
        andi.w  #1,d3
        moveq   #0,d4
        move.w  #-1,d4
        andi.l  #255,d0
        rts

; D0 unsigned word -> least k with k*(k+1) >= D0. No carry chain
; survives a register-pack macro: this is the resumed-serve CT-04 fix.
game_launch_root:
        andi.l  #65535,d0
        moveq   #0,d1
        moveq   #0,d2
.game_root_loop:
        cmp.l   d0,d2
        bcc   .game_root_done
        addq.w  #1,d1
        add.l   d1,d2
        add.l   d1,d2
        bra   .game_root_loop
.game_root_done:
        move.w  d1,d0
        rts

; D0 byte - D1 byte absolute distance -> D0 word.
game_distance:
        andi.w  #255,d0
        andi.w  #255,d1
        sub.w   d1,d0
        bpl   .game_distance_done
        neg.w   d0
.game_distance_done:
        rts

game_derive_launch:
        movem.l d5-d7/a0,-(sp)
        move.b  G_TARGET_Y(a4),d0
        move.b  G_LAUNCH_BASE_Y(a4),d1
        bsr     game_distance
        move.w  d0,d5           ; total court distance
        moveq   #$6f,d0
        move.b  G_LAUNCH_BASE_Y(a4),d1
        bsr     game_distance
        move.w  d0,d6           ; distance to net
        move.b  G_TARGET_Y(a4),d0
        moveq   #$6f,d1
        bsr     game_distance
        move.w  d0,d7           ; target distance beyond net
        move.b  G_HEIGHT(a4),d0
        move.w  d5,d1
        move.w  d7,d2
        bsr     game_ratio
        move.b  G_LAUNCH_BASE_Y(a4),d7
        sub.b   G_LAUNCH_SCREEN_Y(a4),d7
        sub.b   d7,d0
        move.b  d0,d2
        move.w  d5,d0
        move.w  d6,d1
        bsr     game_ratio
        lsl.w   #6,d0
        bsr     game_launch_root
        andi.b  #127,d0
        move.b  d0,G_LAUNCH_Y(a4)
        move.b  d0,d2
        moveq   #64,d0
        move.w  d5,d1
        bsr     game_ratio
        move.w  d0,d6
        move.b  G_LAUNCH_Y(a4),d0
        move.b  d7,d1
        move.w  d5,d2
        bsr     game_ratio
        sub.b   d0,d6
        move.b  d6,G_LAUNCH_Z(a4)
        move.b  G_TARGET_X(a4),d0
        move.b  G_LAUNCH_BASE_X(a4),d1
        bsr     game_distance
        move.b  G_LAUNCH_Y(a4),d1
        move.w  d5,d2
        bsr     game_ratio
        move.b  G_TARGET_X(a4),d1
        cmp.b   G_LAUNCH_BASE_X(a4),d1
        bcc   .game_launch_right
        ori.b   #128,d0
.game_launch_right:
        move.b  d0,G_LAUNCH_X(a4)
        move.b  G_TARGET_Y(a4),d0
        cmp.b   G_LAUNCH_BASE_Y(a4),d0
        bcc   .game_launch_down
        bset    #7,G_LAUNCH_Y(a4)
.game_launch_down:
        movem.l (sp)+,d5-d7/a0
        rts

; D0 signed magnitude, D1 elapsed ticks -> signed byte displacement.
game_displacement:
        move.w  d0,-(sp)
        andi.b  #127,d0
        bsr     game_ratio32
        move.w  (sp)+,d1
        btst    #7,d1
        beq   .game_displacement_done
        neg.b   d0
.game_displacement_done:
        rts
