game_ai_wait:
        move.w  #$a0,d5
        tst.w   d7
        beq   .game_ai_wait_lower
        moveq   #$40,d5
.game_ai_wait_lower:
        move.w  #$80,d6
        bsr     game_adjust_intercept
        move.b  d5,P_TARGET_Y(a3)
        move.b  d6,P_TARGET_X(a3)
        move.b  #4,P_PHASE(a3)
        rts

; D5,D6 court target -> sprite-space target.
game_adjust_intercept:
        cmp.b   P_X(a3),d6
        bls   .game_adjust_y
        subi.b  #16,d6
.game_adjust_y:
        subi.b  #32,d5
        rts

game_ai_setup:
        btst    #6,G_CONTACT(a4)
        beq   .game_ai_setup_upper
        tst.w   d7
        bne     game_ai_track
        bra   .game_ai_intercept
.game_ai_setup_upper:
        tst.w   d7
        beq     game_ai_track
.game_ai_intercept:
        move.b  G_TARGET_Y(a4),d0
        move.b  G_LAUNCH_BASE_Y(a4),d1
        bsr     game_distance
        move.w  d0,d5
        move.b  G_TARGET_X(a4),d0
        move.b  G_LAUNCH_BASE_X(a4),d1
        bsr     game_distance
        moveq   #16,d1
        move.w  d5,d2
        bsr     game_ratio
        move.w  d0,d2
        moveq   #0,d5
        move.b  G_TARGET_Y(a4),d5
        moveq   #0,d6
        move.b  G_TARGET_X(a4),d6
        cmp.b   G_LAUNCH_BASE_Y(a4),d5
        bcc   .game_ai_forward_y
        subi.b  #16,d5
        bra   .game_ai_intercept_x
.game_ai_forward_y:
        addi.b  #16,d5
.game_ai_intercept_x:
        cmp.b   G_LAUNCH_BASE_X(a4),d6
        bcc   .game_ai_forward_x
        sub.b   d2,d6
        bra   .game_ai_choose
.game_ai_forward_x:
        add.b   d2,d6
.game_ai_choose:
        bsr     game_random
        cmpi.b  #$f0,d0
        bcs   .game_ai_target_chosen
        move.b  G_TARGET_Y(a4),d0
        cmpi.b  #$50,d0
        bcs   .game_ai_second
        cmpi.b  #$90,d0
        bcs   .game_ai_target_chosen
.game_ai_second:
        cmp.b   G_LAUNCH_BASE_Y(a4),d0
        bcc   .game_ai_second_forward
        addi.b  #32,d5
        bra   .game_ai_second_x
.game_ai_second_forward:
        subi.b  #32,d5
.game_ai_second_x:
        add.b   d2,d6
        add.b   d2,d6
.game_ai_target_chosen:
        bsr     game_adjust_intercept
        bsr     game_random
        move.b  d0,d1
        andi.b  #7,d1
        btst    #4,d0
        beq   .game_ai_jitter
        neg.b   d1
.game_ai_jitter:
        add.b   d1,d6
        move.b  d5,P_TARGET_Y(a3)
        move.b  d6,P_TARGET_X(a3)
        move.b  #2,P_PHASE(a3)
        rts

game_ai_track:
        tst.b   G_TRACK_AI(a4)
        beq     .game_ai_track_done
        moveq   #0,d2
        move.b  P_Y(a3),d0
        cmp.b   P_TARGET_Y(a3),d0
        beq   .game_ai_direction_x
        bcc   .game_ai_direction_up
        ori.b   #8,d2
        bra   .game_ai_direction_x
.game_ai_direction_up:
        ori.b   #2,d2
.game_ai_direction_x:
        move.b  P_X(a3),d0
        cmp.b   P_TARGET_X(a3),d0
        beq   .game_ai_direction_ready
        bcc   .game_ai_direction_left
        ori.b   #1,d2
        bra   .game_ai_direction_ready
.game_ai_direction_left:
        ori.b   #4,d2
.game_ai_direction_ready:
        move.b  d2,G_LOWER_DIRECTION(a4,d7.w)
        tst.b   d2
        bne   .game_ai_track_done
        btst    #1,P_PHASE(a3)
        bne   .game_ai_track_done
        bsr     game_entropy
        andi.w  #1,d0
        move.w  d0,d5
        bsr     game_random
        andi.w  #15,d0
        ori.w   #16,d0
        tst.w   d5
        beq   .game_ai_retarget
        neg.b   d0
.game_ai_retarget:
        move.b  G_UPPER+P_X(a4),d1
        tst.w   d7
        beq   .game_ai_opponent
        move.b  G_LOWER+P_X(a4),d1
.game_ai_opponent:
        add.b   d1,d0
        move.b  d0,P_TARGET_X(a3)
        move.b  P_Y(a3),P_TARGET_Y(a3)
.game_ai_track_done:
        rts
