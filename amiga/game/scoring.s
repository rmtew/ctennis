        include "amiga/game/scoring_state.i"
; A4 = named native scoring state. No source registers, flags or addresses.
game_score_resolve:
        clr.b   S_EVENT(a4)
        cmpi.b  #S_WAIT_SOUND,S_STAGE(a4)
        beq     game_score_wait_sound
        cmpi.b  #S_ACTIVE,S_STAGE(a4)
        beq     game_score_pending
        cmpi.b  #S_POINT_PAUSE,S_STAGE(a4)
        beq     game_score_point_pause
        cmpi.b  #S_GAME_PAUSE,S_STAGE(a4)
        beq     game_score_game_pause
        rts
game_score_wait_sound:
        btst    #6,S_DISPLAY(a4)
        bne     game_score_return
        bset    #4,S_DISPLAY(a4)
        tst.b   S_AUDIO_COMPLETE(a4)
        beq     game_score_return
        bsr     game_score_new_serve
        move.b  #S_ACTIVE,S_STAGE(a4)
        rts
game_score_pending:
        btst    #7,S_OUTCOME(a4)
        beq     game_score_return
; Outcome message is deferred to presentation; its retry latch handles faults.
        moveq   #2,d0
        btst    #1,S_OUTCOME(a4)
        beq.s   .net
        btst    #3,S_OUTCOME(a4)
        bne.s   .net
        moveq   #1,d0
.net:
        btst    #0,S_OUTCOME(a4)
        beq.s   .status
        moveq   #3,d0
.status:
        btst    #4,S_DISPLAY(a4)
        beq.s   .queue
        cmpi.b  #1,d0
        beq.s   .first_fault
        moveq   #5,d0
        bra.s   .queue
.first_fault:
        moveq   #4,d0
.queue:
        move.b  S_DISPLAY(a4),d1
        andi.b  #$18,d1
        ori.b   #$80,d1
        or.b    d0,d1
        move.b  d1,S_DISPLAY(a4)
        btst    #4,d1
        beq.s   .award
        cmpi.b  #4,d0
        beq.s   .award
        btst    #3,d1
        bne.s   .second_fault
        bset    #3,S_DISPLAY(a4)
        bra     game_score_stop_point
.second_fault:
        addq.b  #1,S_DISPLAY(a4)
.award:
        bclr    #3,S_DISPLAY(a4)
; Winner is a logical player, independent of current end and service direction.
        moveq   #0,d2
        move.b  S_DISPLAY(a4),d0
        andi.b  #7,d0
        cmpi.b  #1,d0
        beq.s   .winner
        cmpi.b  #4,d0
        beq.s   .winner
        moveq   #1,d2
.winner:
        btst    #6,S_OUTCOME(a4)
        beq.s   .end
        eori.b  #1,d2
.end:
        btst    #4,S_MODE(a4)
        beq.s   .cells
        eori.b  #1,d2
.cells:
        lea     S_POINTS(a4),a0
        adda.w  d2,a0
        move.w  d2,d3
        eori.w  #1,d3
        lea     S_POINTS(a4),a1
        adda.w  d3,a1
        move.b  (a0),d0
        andi.b  #7,d0
        cmpi.b  #2,d0
        bcs.s   .increment
        beq.s   .thirty
        cmpi.b  #4,d0
        bls     game_score_award_game
        cmpi.b  #5,d0
        beq.s   .advantage
.deuce:
        move.b  #5,(a0)
        move.b  #5,(a1)
        bra.s   .alternate
.thirty:
        cmpi.b  #3,(a1)
        beq.s   .deuce
.increment:
        addq.b  #1,(a0)
        bra.s   .alternate
.advantage:
        subq.b  #1,(a0)
        addq.b  #1,(a1)
.alternate:
        bchg    #3,S_MODE(a4)
game_score_stop_point:
        bset    #5,S_DISPLAY(a4)
        clr.b   S_FLIGHT(a4)
        clr.b   S_TIMER(a4)
        move.b  #S_POINT_PAUSE,S_STAGE(a4)
        rts
game_score_award_game:
        lea     S_GAMES(a4),a0
        adda.w  d2,a0
        addq.b  #1,(a0)
        cmpi.b  #6,(a0)
        bcs.s   .reset
        bset    #6,S_MODE(a4)
.reset:
        clr.w   S_POINTS(a4)
        bset    #5,S_DISPLAY(a4)
        clr.b   S_FLIGHT(a4)
        clr.b   S_TIMER(a4)
        bset    #7,S_LOWER_ANIMATION(a4)
        bset    #7,S_UPPER_ANIMATION(a4)
        move.b  #S_GAME_PAUSE,S_STAGE(a4)
        rts
game_score_point_pause:
        cmpi.b  #$40,S_TIMER(a4)
        bne.s   .sound
        move.b  #152,S_LOWER_Y(a4)
        move.b  #8,S_UPPER_Y(a4)
        move.b  #184,S_LOWER_X(a4)
        move.b  #80,S_UPPER_X(a4)
        btst    #3,S_MODE(a4)
        beq.s   .positions
        move.b  #56,S_LOWER_X(a4)
        move.b  #160,S_UPPER_X(a4)
.positions:
        clr.b   S_FLIGHT(a4)
        bset    #7,S_LOWER_ANIMATION(a4)
        bset    #7,S_UPPER_ANIMATION(a4)
        move.b  #7,S_LOWER_IMAGE(a4)
        clr.b   S_UPPER_IMAGE(a4)
        bset    #S_EVENT_POSITIONS,S_EVENT(a4)
.sound:
        cmpi.b  #$c0,S_TIMER(a4)
        bcs.s   game_score_return
        bset    #S_EVENT_SOUND,S_EVENT(a4)
        move.b  #S_WAIT_SOUND,S_STAGE(a4)
        rts
game_score_game_pause:
        cmpi.b  #$80,S_TIMER(a4)
        bcs.s   game_score_return
        bset    #5,S_MODE(a4)
        clr.b   S_AI(a4)
        move.b  #S_IDLE,S_STAGE(a4)
game_score_return:
        rts
game_score_new_serve:
        clr.b   S_FLIGHT(a4)
        btst    #7,S_MODE(a4)
        bne.s   .animation
        move.b  S_GAMES(a4),S_ROUND_GAME_A(a4)
        move.b  S_GAMES(a4),S_ROUND_GAME_B(a4)
        btst    #2,S_MODE(a4)
        beq.s   .animation
        btst    #4,S_MODE(a4)
        beq.s   .first_cell
        move.b  S_GAMES+1(a4),S_ROUND_GAME_B(a4)
        bra.s   .animation
.first_cell:
        move.b  S_GAMES+1(a4),S_ROUND_GAME_A(a4)
.animation:
        moveq   #0,d0
        btst    #3,S_MODE(a4)
        beq.s   .players
        moveq   #$20,d0
.players:
        move.b  d0,S_LOWER_ANIMATION(a4)
        move.b  d0,S_UPPER_ANIMATION(a4)
        move.b  #$80,S_LOWER_PHASE(a4)
        move.b  #$10,S_UPPER_PHASE(a4)
        clr.b   S_OUTCOME(a4)
        btst    #1,S_MODE(a4)
        beq.s   .return
        move.b  #$10,S_LOWER_PHASE(a4)
        move.b  #$80,S_UPPER_PHASE(a4)
        move.b  #$40,S_OUTCOME(a4)
.return:
        rts
        even
game_score_state: dcb.b S_SIZE,0
game_score_initialized: dc.b 0
        even
