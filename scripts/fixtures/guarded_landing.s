; Diagnostic wrapper only. Calls the shared bounded helper; shipping has no caller yet.
; Rejected domains continue through original ball ticks, up to 256 phases.
landing_query_begin:
landing_query:
        movem.l d4-d7/a0-a6,-(sp)
        lea     -48(sp),sp
        move.l  sp,a3
        lea     game_play_state-game_core_state(a5),a4
        clr.w   14(a3)
        jsr     landing_try_fast
        tst.w   d2
        beq     .return
        move.w  d2,10(a3)
        move.w  d3,12(a3)
.fallback:
        btst    #7,G_FLIGHT(a4)
        bne     .launch
        btst    #6,G_FLIGHT(a4)
        beq     .inactive
.scan:
        moveq   #0,d0
        move.b  G_VELOCITY_Y(a4),d0
        andi.w  #128,d0
        move.w  d0,36(a3)
        moveq   #0,d0
        move.b  G_STEP(a4),d0
        addq.b  #1,d0
        move.w  d0,38(a3)
        bne     .ordinary_scan
        ; Phase zero has exact base geometry even in overflow/clamp domains.
        ; Preclassify it because a reset to zero is otherwise indistinguishable
        ; from natural byte wrap. Apply the event through the actual routine.
        moveq   #0,d0
        move.b  G_VELOCITY_Y(a4),d0
        andi.w  #127,d0
        cmpi.w  #4,d0
        bcs     .wrap_outside
        move.b  G_BASE_Y(a4),d0
        cmp.b   G_BASE_SCREEN_Y(a4),d0
        bcs     .wrap_bounce
        btst    #3,G_FLIGHT(a4)
        beq     .wrap_bounds
        btst    #0,G_CONTACT(a4)
        bne     .wrap_bounds
        moveq   #0,d0
        move.b  G_BASE_Y(a4),d0
        subi.w  #110,d0
        cmpi.w  #-2,d0
        blt     .wrap_bounds
        cmpi.w  #2,d0
        ble     .wrap_net
.wrap_bounds:
        cmpi.b  #32,G_BASE_X(a4)
        bcs     .wrap_outside
        cmpi.b  #232,G_BASE_X(a4)
        bcc     .wrap_outside
        cmpi.b  #4,G_BASE_Y(a4)
        bcs     .wrap_outside
        cmpi.b  #204,G_BASE_Y(a4)
        bcc     .wrap_outside
        moveq   #0,d7
        bra     .wrap_apply
.wrap_outside:
        moveq   #5,d7
        bra     .wrap_apply
.wrap_bounce:
        moveq   #3,d7
        bra     .wrap_apply
.wrap_net:
        moveq   #4,d7
.wrap_apply:
        jsr     game_ball_tick
        addq.w  #1,14(a3)
        move.w  d7,d0
        bne     .done
        bra     .scan_cap
.ordinary_scan:
        jsr     game_ball_tick
        addq.w  #1,14(a3)
        btst    #6,G_FLIGHT(a4)
        beq     .outside
        tst.b   G_STEP(a4)
        bne     .scan_cap
        moveq   #0,d0
        move.b  G_VELOCITY_Y(a4),d0
        andi.w  #128,d0
        cmp.w   36(a3),d0
        bne     .net
        moveq   #3,d0
        bra     .done
.scan_cap:
        cmpi.w  #256,14(a3)
        bcs     .scan
        moveq   #0,d0
        bra     .done
.launch:
        jsr     game_ball_tick
        move.w  #1,14(a3)
        moveq   #1,d0
        bra     .done
.inactive:
        jsr     game_ball_tick
        move.w  #1,14(a3)
        moveq   #2,d0
        bra     .done
.outside:
        moveq   #5,d0
        bra     .done
.net:
        moveq   #4,d0
.done:
        moveq   #0,d1
        move.w  14(a3),d1
        moveq   #0,d2
        move.w  10(a3),d2
        moveq   #0,d3
        move.w  12(a3),d3
.return:
        lea     48(sp),sp
        movem.l (sp)+,d4-d7/a0-a6
        rts

landing_query_end:
