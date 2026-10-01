; A3 addresses the native player record; D7=0 lower, 1 upper.
game_random:
        moveq   #0,d0
        move.b  G_RANDOM(a4),d0
        move.w  d0,d1
        lsl.w   #2,d0
        add.w   d1,d0
        addq.b  #1,d0
        move.b  d0,G_RANDOM(a4)
        andi.w  #255,d0
        rts

game_player_ai:
        move.b  G_LOWER_AI(a4,d7.w),d0
        rts

game_player_action:
        move.b  G_LOWER_ACTION(a4,d7.w),d0
        andi.b  #3,d0
        rts

game_player_tick:
        move.b  P_PHASE(a3),d0
        btst    #7,d0
        bne     game_serve_setup
        btst    #6,d0
        bne     game_serve_wait
        btst    #5,d0
        bne     game_serve_timed
        btst    #4,d0
        bne   .game_player_wait
        btst    #3,d0
        bne   .game_player_animation
        btst    #2,d0
        bne     game_ai_setup
        btst    #1,d0
        beq   .game_player_done
        bsr     game_player_contact
        tst.b   d0
        bne   .game_player_done
        bsr     game_player_ai
        tst.b   d0
        bne     game_ai_track
.game_player_done:
        rts
.game_player_wait:
        bsr     game_player_ai
        tst.b   d0
        beq     game_player_contact
        btst    #0,P_PHASE(a3)
        bne     game_ai_wait
        rts
.game_player_animation:
        cmpi.b  #8,G_ACTION_CLOCK(a4)
        bcs   .game_player_done
        bclr    #7,P_ANIMATION(a3)
        bsr     game_player_ai
        tst.b   d0
        bne     game_ai_wait
        move.b  #$10,P_PHASE(a3)
        rts

game_serve_setup:
        clr.b   G_VELOCITY_X(a4)
        clr.b   G_VELOCITY_Y(a4)
        move.b  #64,G_VELOCITY_Z(a4)
        clr.b   G_STEP(a4)
        clr.b   G_SERVE_CLOCK(a4)
        clr.b   G_CONTACT(a4)
        move.b  #$a0,G_BASE_SCREEN_Y(a4)
        move.b  #$b4,G_BASE_Y(a4)
        moveq   #20,d0
        tst.w   d7
        beq   .game_serve_position
        move.b  #$18,G_BASE_SCREEN_Y(a4)
        move.b  #$28,G_BASE_Y(a4)
        move.b  #$40,G_CONTACT(a4)
        moveq   #-4,d0
.game_serve_position:
        add.b   P_X(a3),d0
        move.b  d0,G_BASE_X(a4)
        move.b  #$40,P_PHASE(a3)
        rts

game_serve_wait:
        bsr     game_advance_ball
        moveq   #20,d0
        move.w  #$a0,d1
        tst.w   d7
        beq   .game_serve_attach
        moveq   #-4,d0
        moveq   #$18,d1
.game_serve_attach:
        cmp.b   G_BALL_Y(a4),d1
        bhi   .game_serve_keep_step
        clr.b   G_STEP(a4)
.game_serve_keep_step:
        add.b   P_X(a3),d0
        move.b  d0,G_BALL_X(a4)
        move.b  d0,G_COURT_X(a4)
        bsr     game_player_ai
        tst.b   d0
        beq   .game_serve_human
        cmpi.b  #$50,G_SERVE_CLOCK(a4)
        bcs   .game_serve_not_ready
        bra   .game_serve_trigger
.game_serve_human:
        bsr     game_player_action
        tst.b   d0
        beq   .game_serve_not_ready
.game_serve_trigger:
        clr.b   G_SERVE_CLOCK(a4)
        move.b  #$f0,P_ANIMATION(a3)
        tst.w   d7
        beq   .game_serve_lower_animation
        move.b  #$f3,P_ANIMATION(a3)
.game_serve_lower_animation:
        move.b  #$20,P_PHASE(a3)
.game_serve_not_ready:
        rts

game_serve_timed:
        cmpi.b  #$10,G_SERVE_CLOCK(a4)
        beq   .game_serve_launch
        cmpi.b  #$20,G_SERVE_CLOCK(a4)
        beq   .game_serve_handoff
        cmpi.b  #$31,G_SERVE_CLOCK(a4)
        bcs   .game_timed_wait
        bclr    #7,P_ANIMATION(a3)
        move.b  #$11,P_PHASE(a3)
        rts
.game_timed_wait:
        rts
.game_serve_launch:
        bset    #7,P_ANIMATION(a3)
        bra     game_random_launch
.game_serve_handoff:
        lea     G_UPPER(a4),a0
        tst.w   d7
        beq   .game_handoff_ready
        lea     G_LOWER(a4),a0
.game_handoff_ready:
        andi.b  #$1f,P_ANIMATION(a0)
        ori.b   #$40,P_ANIMATION(a0)
        bset    #0,P_PHASE(a0)
        rts

; These distributions are gameplay rules: 4 cumulative thresholds, 5 values.
game_height_choices: dc.b $40,$80,$c0,$ff,$20,$24,$24,$24,$24
game_lower_depth:    dc.b $40,$80,$c0,$ff,$40,$40,$40,$40,$40
game_lower_width:    dc.b $40,$80,$f0,$ff,$6d,$68,$58,$6d,$68
game_upper_depth:    dc.b $40,$80,$c0,$ff,$90,$90,$90,$90,$90
game_upper_width:    dc.b $40,$80,$f0,$ff,$88,$98,$a0,$a0,$a0
        even
game_sample_choice:
        bsr     game_random
        moveq   #0,d2
.game_choice_loop:
        cmpi.w  #4,d2
        beq   .game_choice_found
        cmp.b   (a0,d2.w),d0
        bcs   .game_choice_found
        addq.w  #1,d2
        bra   .game_choice_loop
.game_choice_found:
        bsr     game_random
        andi.b  #12,d0
        add.b   4(a0,d2.w),d0
        rts

game_random_launch:
        move.b  G_BALL_X(a4),G_LAUNCH_BASE_X(a4)
        move.b  #$98,G_LAUNCH_SCREEN_Y(a4)
        move.b  #$a8,G_LAUNCH_BASE_Y(a4)
        tst.w   d7
        beq   .game_launch_setup
        move.b  #12,G_LAUNCH_SCREEN_Y(a4)
        move.b  #$28,G_LAUNCH_BASE_Y(a4)
.game_launch_setup:
        lea     game_height_choices,a0
        bsr     game_sample_choice
        move.b  d0,G_HEIGHT(a4)
        lea     game_lower_depth,a0
        tst.w   d7
        beq   .game_launch_depth
        lea     game_upper_depth,a0
.game_launch_depth:
        bsr     game_sample_choice
        move.b  d0,G_TARGET_Y(a4)
        lea     game_lower_width,a0
        tst.w   d7
        beq   .game_launch_width
        lea     game_upper_width,a0
.game_launch_width:
        bsr     game_sample_choice
        move.b  d0,G_TARGET_X(a4)
        move.b  #$80,G_FLIGHT(a4)
        bsr     game_random
        cmpi.b  #$e0,d0
        bcs   .game_serve_flip
        move.b  #12,G_HEIGHT(a4)
        move.b  #$68,G_TARGET_Y(a4)
        tst.w   d7
        beq   .game_short_serve
        move.b  #$78,G_TARGET_Y(a4)
.game_short_serve:
        bset    #3,G_FLIGHT(a4)
.game_serve_flip:
        tst.b   G_FLIP_SERVE(a4)
        beq   .game_derive_serve
        neg.b   G_TARGET_X(a4)
.game_derive_serve:
        bra     game_derive_launch

; Movement uses prior tick parity; directions are already assigned to ends.
game_move_player:
        btst    #2,G_CONTACT(a4)
        bne   .game_move_done
        btst    #7,P_ANIMATION(a3)
        bne   .game_move_done
        lea     game_lower_limits,a0
        tst.w   d7
        beq   .game_move_limits
        lea     game_upper_limits,a0
.game_move_limits:
        moveq   #0,d0
        move.b  P_ANIMATION(a3),d0
        lsr.w   #3,d0
        andi.w  #12,d0
        adda.w  d0,a0
        moveq   #0,d1
        move.b  G_TICK(a4),d1
        andi.w  #1,d1
        addq.w  #1,d1
        move.b  G_LOWER_DIRECTION(a4,d7.w),d2
        btst    #3,d2
        beq   .game_move_up
        move.b  P_Y(a3),d0
        add.b   d1,d0
        cmp.b   (a0),d0
        bcc   .game_move_up
        move.b  d0,P_Y(a3)
.game_move_up:
        btst    #1,d2
        beq   .game_move_right
        move.b  P_Y(a3),d0
        sub.b   d1,d0
        cmp.b   1(a0),d0
        bcs   .game_move_right
        move.b  d0,P_Y(a3)
.game_move_right:
        btst    #0,d2
        beq   .game_move_left
        move.b  P_X(a3),d0
        add.b   d1,d0
        cmp.b   2(a0),d0
        bcc   .game_move_left
        move.b  d0,P_X(a3)
.game_move_left:
        btst    #2,d2
        beq   .game_move_done
        move.b  P_X(a3),d0
        sub.b   d1,d0
        cmp.b   3(a0),d0
        bcs   .game_move_done
        move.b  d0,P_X(a3)
.game_move_done:
        rts
; Per phase: exclusive bottom, inclusive top, exclusive right, inclusive left.
game_lower_limits: dc.b 154,152,200,128,154,152,112,40,154,128,200,40,154,98,200,40
game_upper_limits: dc.b 10,7,112,80,10,7,160,128,32,7,176,64,63,7,176,64
        even
