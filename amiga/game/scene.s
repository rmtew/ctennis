; Native scene: two three-part actors, a ball and a court shadow. Eight logical
; primitives, independent of hardware channels. Geometry is prepared at tick
; end and rendered on the next update; resets can refresh actors immediately.
        rsset 0
O_Y rs.b 1
O_X rs.b 1
O_FRAME rs.w 1
O_COLOUR rs.b 1
O_VISIBLE rs.b 1
        rs.b 2 ; reserved bytes6..7
O_SIZE rs.b 0
SC_LOWER equ 0
SC_UPPER equ 3*O_SIZE
SC_BALL equ 6*O_SIZE
SC_SHADOW equ 7*O_SIZE
COLOUR_WHITE equ 1
COLOUR_BLUE equ 2
COLOUR_RED equ 3
COLOUR_BLACK equ 4

game_scene_reset:
        lea     game_scene_objects,a0
        moveq   #7,d7
.reset:
        move.b  #194,O_Y(a0)
        clr.b   O_VISIBLE(a0)
        adda.w  #O_SIZE,a0
        dbra    d7,.reset
        move.b  #2,game_scene_ball_layer
        rts

game_scene_build_players:
        movem.l d0-d7/a0-a4,-(sp)
        lea     game_play_state,a4
        bsr     game_assign_styles
        lea     G_LOWER(a4),a3
        lea     game_scene_objects+SC_LOWER,a2
        moveq   #1,d7 ; lower court record
        bsr     game_scene_actor
        lea     G_UPPER(a4),a3
        lea     game_scene_objects+SC_UPPER,a2
        moveq   #0,d7 ; upper court record
        bsr     game_scene_actor
        movem.l (sp)+,d0-d7/a0-a4
        rts

game_scene_actor:
        moveq   #0,d0
        move.b  P_IMAGE(a3),d0
        cmpi.w  #14,d0
        bcs.s   .pose
        clr.w   d0
.pose:
        lsl.w   #3,d0
        lea     game_scene_poses,a0
        ; Recorded demo input owns the same human A controller as live input.
        ; Resolve logical controller ownership from the mode/end mapping.
        ; Court-relative AI flags lag end exchange during round pause.
        ; The next completed scene publishes role and geometry together;
        ; no player state or clocks are changed.
        btst    #7,game_mode
        bne.s   .role_ready ; two human controllers
        btst    #4,game_mode
        beq.s   .original_ends
        tst.w   d7
        bne.s   .robot ; exchanged: lower is logical B
        bra.s   .role_ready
.original_ends:
        tst.w   d7
        bne.s   .role_ready ; original: lower is logical A
.robot:
        lea     game_scene_robot_poses,a0
.role_ready:
        adda.w  d0,a0
        move.b  P_Y(a3),d0
        add.b   6(a0),d0
        move.b  d0,O_Y(a2)
        move.b  P_X(a3),d0
        add.b   7(a0),d0
        move.b  d0,O_X(a2)
        move.w  (a0),O_FRAME(a2)
        moveq   #COLOUR_WHITE,d0
        move.b  d0,O_COLOUR(a2)
        bsr     game_scene_visibility
        adda.w  #O_SIZE,a2
        move.b  P_Y(a3),O_Y(a2)
        move.b  P_X(a3),O_X(a2)
        move.w  2(a0),O_FRAME(a2)
        move.b  P_STYLE(a3),d0
        move.b  d0,O_COLOUR(a2)
        bsr     game_scene_visibility
        adda.w  #O_SIZE,a2
        move.b  P_Y(a3),d1
        addi.b  #16,d1
        move.b  d1,O_Y(a2)
        move.b  P_X(a3),O_X(a2)
        move.w  4(a0),O_FRAME(a2)
        move.b  d0,O_COLOUR(a2)
        bra     game_scene_visibility

game_scene_visibility:
        clr.b   O_VISIBLE(a2)
        cmpi.b  #192,O_Y(a2)
        bcc.s   .hidden
        tst.b   O_COLOUR(a2)
        beq.s   .hidden
        st      O_VISIBLE(a2)
.hidden:
        rts

game_scene_finish_tick:
        movem.l d0-d7/a0-a4,-(sp)
        lea     game_play_state,a4
        lea     G_LOWER(a4),a3
        moveq   #7,d7
        bsr     game_scene_animate
        lea     G_UPPER(a4),a3
        moveq   #0,d7
        bsr     game_scene_animate
        bsr     game_finish_controls
        bsr     game_scene_build_players
        lea     game_play_state,a4
        moveq   #2,d0
        move.b  G_UPPER+P_Y(a4),d1
        addi.b  #32,d1
        cmp.b   G_COURT_Y(a4),d1
        bcc.s   .layer
        moveq   #1,d0
        move.b  G_LOWER+P_Y(a4),d1
        addi.b  #36,d1
        cmp.b   G_COURT_Y(a4),d1
        bcc.s   .layer
        moveq   #0,d0
.layer:
        move.b  d0,game_scene_ball_layer
        lea     game_scene_objects+SC_BALL,a2
        move.b  G_BALL_Y(a4),O_Y(a2)
        move.b  G_BALL_X(a4),O_X(a2)
        moveq   #0,d0
        move.b  G_BALL_IMAGE(a4),d0
        andi.w  #$fc,d0
        lsl.w   #5,d0
        move.w  d0,O_FRAME(a2)
        move.b  #COLOUR_WHITE,O_COLOUR(a2)
        tst.b   G_BALL_COLOUR(a4)
        bne.s   .ball_visible
        clr.b   O_COLOUR(a2)
.ball_visible:
        bsr     game_scene_visibility
        cmpi.b  #192,G_BALL_Y(a4)
        bcs.s   .shadow
        move.b  #194,G_COURT_Y(a4)
        move.b  #194,game_court_y ; remaining gameplay scalar ABI, not sprite memory
.shadow:
        lea     game_scene_objects+SC_SHADOW,a2
        move.b  G_COURT_Y(a4),O_Y(a2)
        move.b  G_COURT_X(a4),O_X(a2)
        clr.w   O_FRAME(a2)
        move.b  #COLOUR_BLACK,O_COLOUR(a2)
        tst.b   G_SHADOW_COLOUR(a4)
        bne.s   .shadow_visible
        clr.b   O_COLOUR(a2)
.shadow_visible:
        bsr     game_scene_visibility
        movem.l (sp)+,d0-d7/a0-a4
        rts

game_scene_animate:
        btst    #3,P_ANIMATION(a3)
        bne.s   .running
        btst    #4,P_ANIMATION(a3)
        beq.s   .done
        bset    #3,P_ANIMATION(a3)
        clr.b   P_CLOCK(a3)
.running:
        moveq   #0,d0
        move.b  P_ANIMATION(a3),d0
        andi.w  #7,d0
        mulu.w  #9,d0
        lea     game_scene_animations,a0
        adda.w  d0,a0
        moveq   #0,d1
.threshold:
        cmpi.w  #4,d1
        beq.s   .frame
        move.b  P_CLOCK(a3),d2
        cmp.b   (a0,d1.w),d2
        bcs.s   .frame
        addq.w  #1,d1
        bra.s   .threshold
.frame:
        move.b  4(a0,d1.w),d0
        cmpi.b  #255,d0
        bne.s   .store
        andi.b  #$e7,P_ANIMATION(a3)
        move.b  d7,d0
.store:
        move.b  d0,P_IMAGE(a3)
.done:
        rts
        even
game_scene_objects: dcb.b 8*O_SIZE,0
game_scene_ball_layer: dc.b 2
        even
game_scene_order:
        dc.b 6,0,1,2,3,4,5,7
        dc.b 0,1,2,6,3,4,5,7
        dc.b 0,1,2,3,4,5,6,7
        even
game_scene_palette: dc.w 0,$fff,$55e,$e33,$000
game_scene_poses: incbin "assets/native/scene/poses.bin"
game_scene_robot_poses: incbin "assets/native/scene/robot-poses.bin"
game_scene_animations: incbin "assets/native/scene/animations.bin"
        even
