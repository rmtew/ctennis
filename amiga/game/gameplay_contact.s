; Accept contact only on the receiving end, within the existing court/height
; bounds. A3=player, D7=end. D0 returns whether a return was accepted.
game_player_contact:
        move.b  G_CONTACT(a4),d0
        andi.b  #$0d,d0
        bne     game_no_contact
        btst    #6,G_CONTACT(a4)
        beq   .game_contact_upper_side
        tst.w   d7
        bne     game_no_contact
        bra   .game_contact_geometry
.game_contact_upper_side:
        tst.w   d7
        beq     game_no_contact
.game_contact_geometry:
        bsr     game_history_contact_begin
        moveq   #0,d5
        move.b  P_X(a3),d5
        lsl.w   #8,d5
        move.b  P_Y(a3),d5
        addi.w  #$081b,d5
        tst.w   d7
        beq   .game_contact_point
        addq.w  #8,d5
.game_contact_point:
        move.w  d5,d6
        lsr.w   #8,d6
        andi.w  #255,d5
        move.b  G_COURT_Y(a4),d0
        move.w  d5,d1
        bsr     game_distance
        cmpi.w  #4,d0
        bcc     game_no_contact
        move.b  G_COURT_X(a4),d0
        move.w  d6,d1
        bsr     game_distance
        cmpi.w  #17,d0
        bcc     game_no_contact
        moveq   #0,d2
        move.b  G_COURT_Y(a4),d2
        moveq   #0,d1
        move.b  G_BALL_Y(a4),d1
        sub.w   d1,d2
        bmi     game_no_contact
        cmpi.w  #29,d2
        bcc     game_no_contact
        clr.b   G_FLIGHT(a4)
        cmpi.w  #8,d2
        bcc   .game_contact_regular
        bsr     game_player_ai
        tst.b   d0
        beq   .game_contact_special
        bsr     game_random
        cmpi.b  #$e0,d0
        bcs   .game_contact_regular
.game_contact_special:
        bset    #3,G_FLIGHT(a4)
        move.b  #12,G_HEIGHT(a4)
        move.b  #$68,G_TARGET_Y(a4)
        tst.w   d7
        beq     game_return_vector
        move.b  #$78,G_TARGET_Y(a4)
        bra     game_return_vector
.game_contact_regular:
        addi.b  #24,d2
        move.b  d2,G_HEIGHT(a4)
        move.w  #$e0,d0
        sub.b   d5,d0
        tst.w   d7
        bne   .game_contact_upper_depth
        cmpi.b  #$40,d0
        bcc   .game_contact_depth_ready
        moveq   #$40,d0
        bra   .game_contact_depth_ready
.game_contact_upper_depth:
        cmpi.b  #$a0,d0
        bcs   .game_contact_depth_ready
        move.w  #$a0,d0
.game_contact_depth_ready:
        move.b  d0,G_TARGET_Y(a4)
        bsr     game_player_ai
        tst.b   d0
        beq   .game_contact_human_action
        bsr     game_random
        andi.b  #15,d0
        bne     game_return_vector
        bra   .game_contact_action
.game_contact_human_action:
        bsr     game_player_action
        tst.b   d0
        beq     game_return_vector
.game_contact_action:
        tst.w   d7
        bne   .game_upper_action
        move.w  d5,d0
        subi.b  #$60,d0
        move.b  d0,G_HEIGHT(a4)
        addi.b  #16,d0
        move.b  d0,G_TARGET_Y(a4)
        bra   .game_contact_action_ready
.game_upper_action:
        move.w  #$80,d0
        sub.b   d5,d0
        move.b  d0,G_HEIGHT(a4)
        move.w  #$d0,d1
        sub.b   d0,d1
        move.b  d1,G_TARGET_Y(a4)
.game_contact_action_ready:
        bset    #1,G_FLIGHT(a4)

game_return_vector:
        bclr    #0,P_PHASE(a3)
        moveq   #0,d0
        move.b  G_BALL_X(a4),d0
        sub.w   d6,d0
        bpl   .game_return_distance
        neg.w   d0
        bset    #0,P_PHASE(a3)
.game_return_distance:
        move.w  d0,d2
        cmpi.w  #13,d2
        bcs   .game_return_width
        bsr     game_random
        andi.w  #7,d0
        add.b   d0,d2
.game_return_width:
        add.b   d2,d2
        move.b  d2,G_TARGET_X(a4)
        move.w  d6,d0
        move.w  #128,d1
        bsr     game_distance
        move.w  #$e0,d1
        sub.b   d5,d1
        andi.w  #255,d1
        lsr.w   #2,d1
        addi.w  #36,d1
        move.w  d5,d2
        lsr.w   #2,d2
        addi.w  #36,d2
        bsr     game_ratio
        cmpi.w  #128,d6
        bcc   .game_target_right
        neg.b   d0
.game_target_right:
        addi.b  #128,d0
        andi.w  #255,d0
        moveq   #0,d1
        move.b  G_TARGET_X(a4),d1
        btst    #0,P_PHASE(a3)
        beq   .game_target_add
        neg.b   d1
        add.w   d1,d0
        cmpi.w  #255,d0
        bhi   .game_target_store
        moveq   #0,d0
        bra   .game_target_store
.game_target_add:
        add.b   d1,d0
.game_target_store:
        move.b  d0,G_TARGET_X(a4)
        btst    #3,G_FLIGHT(a4)
        bne   .game_return_derive
        btst    #1,G_CONTACT(a4)
        bne   .game_return_derive
        bset    #1,G_FLIGHT(a4)
.game_return_derive:
        move.b  G_BALL_Y(a4),G_LAUNCH_SCREEN_Y(a4)
        move.b  G_BALL_X(a4),G_LAUNCH_BASE_X(a4)
        move.b  G_COURT_Y(a4),G_LAUNCH_BASE_Y(a4)
        bsr     game_derive_launch
        bclr    #4,G_DISPLAY(a4)
        bset    #7,G_FLIGHT(a4)
        move.b  #$f1,P_ANIMATION(a3)
        btst    #0,P_PHASE(a3)
        beq   .game_return_animation
        move.b  #$f2,P_ANIMATION(a3)
.game_return_animation:
        clr.b   G_ACTION_CLOCK(a4)
        clr.b   G_CONTACT(a4)
        tst.w   d7
        beq   .game_return_end
        move.b  #$40,G_CONTACT(a4)
.game_return_end:
        move.b  #8,P_PHASE(a3)
        moveq   #1,d0
        bsr     game_history_contact
        rts

game_no_contact:
        moveq   #0,d0
        rts
