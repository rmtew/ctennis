game_advance_ball:
        movem.l d5-d6,-(sp)
        addq.b  #1,G_STEP(a4)
        move.b  #15,G_BALL_COLOUR(a4)
        move.b  #1,G_SHADOW_COLOUR(a4)
        moveq   #0,d5
        move.b  G_STEP(a4),d5
        move.b  G_VELOCITY_X(a4),d0
        move.w  d5,d1
        bsr     game_displacement
        add.b   G_BASE_X(a4),d0
        move.b  d0,G_BALL_X(a4)
        move.b  d0,G_COURT_X(a4)
        move.b  G_VELOCITY_Y(a4),d0
        move.w  d5,d1
        bsr     game_displacement
        add.b   G_BASE_Y(a4),d0
        move.b  d0,G_COURT_Y(a4)
        moveq   #0,d0
        move.b  G_VELOCITY_Y(a4),d0
        andi.w  #127,d0
        btst    #7,G_VELOCITY_Y(a4)
        beq   .game_vertical_positive
        neg.b   d0
        ori.w   #$ff00,d0       ; preserve signed-magnitude negative zero
.game_vertical_positive:
        add.w   d5,d0
        add.w   d5,d0
        moveq   #0,d1
        move.b  G_VELOCITY_Z(a4),d1
        sub.w   d1,d0
        move.w  d0,d6
        bpl   .game_height_magnitude
        neg.b   d0
.game_height_magnitude:
        move.w  d5,d1
        moveq   #32,d2
        bsr     game_ratio
        tst.w   d6
        bpl   .game_falling_height
        tst.b   d0
        beq   .game_falling_height
        move.b  G_BASE_SCREEN_Y(a4),d1
        sub.b   d0,d1
        bcs   .game_ball_above_screen
        move.b  d1,G_BALL_Y(a4)
        bra   .game_net_colours
.game_ball_above_screen:
        clr.b   G_BALL_Y(a4)
        clr.b   G_BALL_COLOUR(a4)
        bra   .game_advance_done
.game_falling_height:
        add.b   G_BASE_SCREEN_Y(a4),d0
        move.b  d0,G_BALL_Y(a4)
.game_net_colours:
        cmpi.b  #$5e,G_COURT_Y(a4)
        bcs   .game_advance_done
        cmpi.b  #$6e,G_COURT_Y(a4)
        bcc   .game_advance_done
        clr.b   G_SHADOW_COLOUR(a4)
        cmpi.b  #$5e,G_BALL_Y(a4)
        bcs   .game_advance_done
        cmpi.b  #$6e,G_BALL_Y(a4)
        bcc   .game_advance_done
        clr.b   G_BALL_COLOUR(a4)
.game_advance_done:
        movem.l (sp)+,d5-d6
        rts

game_ball_tick:
        btst    #7,G_FLIGHT(a4)
        bne     .game_ball_launch
        btst    #6,G_FLIGHT(a4)
        bne   .game_ball_active
        btst    #5,G_FLIGHT(a4)
        beq   .game_ball_done
        move.b  #$c2,G_COURT_Y(a4)
.game_ball_done:
        rts
.game_ball_launch:
        lea     G_LAUNCH_X(a4),a0
        lea     G_VELOCITY_X(a4),a1
        moveq   #5,d0
.game_copy_launch:
        move.b  (a0)+,(a1)+
        dbra    d0,.game_copy_launch
        clr.b   G_STEP(a4)
        move.b  #1,G_SOUND_EVENT(a4)
        bclr    #7,G_FLIGHT(a4)
        bset    #6,G_FLIGHT(a4)
        rts
.game_ball_active:
        bsr     game_advance_ball
        move.b  G_VELOCITY_Y(a4),d0
        andi.b  #127,d0
        cmpi.b  #4,d0
        bcs     .game_ball_outside
        move.b  G_COURT_Y(a4),d0
        cmp.b   G_BALL_Y(a4),d0
        bcs     game_bounce
        btst    #3,G_FLIGHT(a4)
        beq   .game_ball_bounds
        btst    #0,G_CONTACT(a4)
        bne   .game_ball_bounds
        moveq   #$6e,d1
        bsr     game_distance
        cmpi.w  #3,d0
        bcc   .game_ball_bounds
        bset    #0,G_CONTACT(a4)
        eori.b  #128,G_VELOCITY_Y(a4)
        move.b  G_BALL_Y(a4),G_BASE_SCREEN_Y(a4)
        move.b  G_BALL_X(a4),G_BASE_X(a4)
        move.b  G_COURT_Y(a4),G_BASE_Y(a4)
        move.w  #$40,d5
        move.w  #$c0,d6
        bra     game_reflect
.game_ball_bounds:
        cmpi.b  #$20,G_COURT_X(a4)
        bcs   .game_ball_outside
        cmpi.b  #$e8,G_COURT_X(a4)
        bcc   .game_ball_outside
        cmpi.b  #4,G_COURT_Y(a4)
        bcs   .game_ball_outside
        cmpi.b  #$cc,G_COURT_Y(a4)
        bcs   .game_ball_done
.game_ball_outside:
        bset    #7,G_CONTACT(a4)
        bclr    #6,G_FLIGHT(a4)
        bset    #5,G_FLIGHT(a4)
        rts

game_bounce:
        btst    #1,G_CONTACT(a4)
        bne   .game_second_bounce
        moveq   #0,d0
        move.b  G_COURT_Y(a4),d0
        cmpi.b  #$27,d0
        bcs   .game_court_out
        cmpi.b  #$b8,d0
        bcc   .game_court_out
        subi.w  #$27,d0
        lsr.w   #2,d0
        moveq   #$4f,d1
        sub.w   d0,d1
        cmp.b   G_COURT_X(a4),d1
        bcc   .game_court_out
        addi.w  #$af,d0
        cmp.b   G_COURT_X(a4),d0
        bcc   .game_contact_first
.game_court_out:
        bset    #3,G_CONTACT(a4)
.game_contact_first:
        bset    #1,G_CONTACT(a4)
        bra   .game_bounce_vector
.game_second_bounce:
        bset    #2,G_CONTACT(a4)
.game_bounce_vector:
        move.w  #255,d5
        move.w  #$c0,d6
        move.b  G_FLIGHT(a4),d0
        andi.b  #10,d0
        beq   .game_bounce_normal
        move.w  #$f0,d5
        move.w  #$80,d6
.game_bounce_normal:
        move.b  G_COURT_Y(a4),G_BALL_Y(a4)
        move.b  G_COURT_X(a4),G_BALL_X(a4)
        move.b  G_COURT_Y(a4),G_BASE_SCREEN_Y(a4)
        move.b  G_COURT_X(a4),G_BASE_X(a4)
        move.b  G_COURT_Y(a4),G_BASE_Y(a4)
; D5 horizontal/longitudinal damping, D6 vertical damping (fractions /256).
game_reflect:
        moveq   #0,d0
        move.b  G_STEP(a4),d0
        lsl.w   #2,d0
        moveq   #0,d1
        move.b  G_VELOCITY_Z(a4),d1
        sub.w   d1,d0
        bpl   .game_reflect_above
        moveq   #0,d0
.game_reflect_above:
        andi.w  #255,d0
        mulu.w  d6,d0
        lsr.w   #8,d0
        move.b  d0,G_VELOCITY_Z(a4)
        lea     G_VELOCITY_X(a4),a0
        moveq   #1,d3
.game_damp_axis:
        moveq   #0,d0
        move.b  (a0),d0
        move.w  d0,d1
        andi.w  #127,d0
        mulu.w  d5,d0
        lsr.w   #8,d0
        andi.b  #128,d1
        or.b    d1,d0
        move.b  d0,(a0)+
        dbra    d3,.game_damp_axis
        clr.b   G_STEP(a4)
        andi.b  #$9f,G_LOWER+P_ANIMATION(a4)
        ori.b   #$60,G_LOWER+P_ANIMATION(a4)
        andi.b  #$9f,G_UPPER+P_ANIMATION(a4)
        ori.b   #$60,G_UPPER+P_ANIMATION(a4)
        rts
