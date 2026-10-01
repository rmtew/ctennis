; Diagnostic projection only. The product renderer never reads these records.
; A captured phase may initialize its previously prepared scene exactly once.
scene_import_capture:
        movem.l d0-d7/a0-a4,-(sp)
        lea     $14(a5),a0
        lea     game_scene_objects,a2
        moveq   #5,d7
.players:
        bsr     .record
        addq.w  #4,a0
        cmpi.w  #3,d7
        bne.s   .next
        addq.w  #4,a0
.next:
        adda.w  #O_SIZE,a2
        dbra    d7,.players
        lea     $30(a5),a0
        move.b  #2,game_scene_ball_layer
        cmpi.b  #192,(a0)
        bcs.s   .ball
        lea     $20(a5),a0
        move.b  #1,game_scene_ball_layer
        cmpi.b  #192,(a0)
        bcs.s   .ball
        lea     $10(a5),a0
        clr.b   game_scene_ball_layer
.ball:
        bsr     .record
        lea     $34(a5),a0
        adda.w  #O_SIZE,a2
        bsr     .record
        movem.l (sp)+,d0-d7/a0-a4
        rts
.record:
        move.b  (a0),O_Y(a2)
        move.b  1(a0),O_X(a2)
        moveq   #0,d0
        move.b  2(a0),d0
        andi.w  #$fc,d0
        lsl.w   #5,d0
        move.w  d0,O_FRAME(a2)
        move.b  3(a0),d0
        andi.b  #15,d0
        bsr     scene_import_colour
        move.b  d0,O_COLOUR(a2)
        bra     game_scene_visibility

scene_observe_players:
        lea     game_scene_objects,a2
        lea     $14(a5),a0
        moveq   #5,d7
.players:
        bsr     scene_observe_record
        addq.w  #4,a0
        cmpi.w  #3,d7
        bne.s   .next
        addq.w  #4,a0
.next:
        adda.w  #O_SIZE,a2
        dbra    d7,.players
        rts
scene_observe_ball:
        move.b  #194,$10(a5)
        move.b  #194,$20(a5)
        move.b  #194,$30(a5)
        lea     game_scene_objects+SC_BALL,a2
        moveq   #0,d0
        move.b  game_scene_ball_layer,d0
        lsl.w   #4,d0
        lea     $10(a5),a0
        adda.w  d0,a0
        bsr     scene_observe_record
        move.b  G_BALL_IMAGE(a4),2(a0)
        cmpi.b  #192,O_Y(a2)
        bcs.s   .shadow
        move.b  #194,(a0)
.shadow:
        lea     game_scene_objects+SC_SHADOW,a2
        lea     $34(a5),a0
        bra     scene_observe_record
scene_observe_record:
        move.b  O_Y(a2),(a0)
        move.b  O_X(a2),1(a0)
        move.w  O_FRAME(a2),d0
        lsr.w   #5,d0
        move.b  d0,2(a0)
        moveq   #0,d0
        move.b  O_COLOUR(a2),d0
        lea     .colours,a1
        move.b  (a1,d0.w),3(a0)
        rts
.colours: dc.b 0,15,4,13,1
        even

; Palette identity enters only at the remaining gameplay scalar ABI. Native
; primitives carry explicit colour roles, never VDP colour/early-clock records.
scene_import_colour:
        cmpi.b  #15,d0
        beq.s   .white
        cmpi.b  #4,d0
        beq.s   .blue
        cmpi.b  #13,d0
        beq.s   .purple
        cmpi.b  #1,d0
        beq.s   .black
        moveq   #0,d0
        rts
.white: moveq #COLOUR_WHITE,d0
        rts
.blue:  moveq #COLOUR_BLUE,d0
        rts
.purple: moveq #COLOUR_PURPLE,d0
        rts
.black: moveq #COLOUR_BLACK,d0
        rts
