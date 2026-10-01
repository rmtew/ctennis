; Temporary CT-04 boundary to score/lifecycle, presentation and audio.
; Native gameplay has its own named layout. These mappings disappear when the
; remaining native subsystems replace the legacy byte page (CT-05/07/08).
legacy_import_gameplay:
        lea     legacy_game_fields,a0
        moveq   #0,d0
        moveq   #0,d1
.legacy_import_field:
        move.b  (a0)+,d0
        cmpi.b  #255,d0
        beq   .legacy_import_controls
        move.b  (a0)+,d1
        move.b  (a5,d0.w),(a4,d1.w)
        bra   .legacy_import_field
.legacy_import_controls:
        move.b  #2,G_LOWER+P_STYLE(a4)
        move.b  #3,G_UPPER+P_STYLE(a4)
        btst    #4,$3d(a5)
        beq.s   .legacy_styles_ready
        move.b  #3,G_LOWER+P_STYLE(a4)
        move.b  #2,G_UPPER+P_STYLE(a4)
.legacy_styles_ready:
        clr.b   G_SOUND_EVENT(a4)
        move.b  $3c(a5),d0
        move.b  d0,d1
        andi.b  #1,d0
        move.b  d0,G_UPPER_AI(a4)
        move.b  d1,d0
        andi.b  #2,d0
        move.b  d0,G_LOWER_AI(a4)
        andi.b  #$40,d1
        move.b  d1,G_TRACK_AI(a4)
        move.b  $3d(a5),d0
        andi.b  #8,d0
        move.b  d0,G_FLIP_SERVE(a4)
        move.b  $53(a5),d0
        move.b  $56(a5),d1
        btst    #4,$3d(a5)
        beq   .legacy_controls_ordered
        rol.b   #4,d0
        rol.b   #4,d1
.legacy_controls_ordered:
        move.b  d0,d2
        andi.b  #15,d0
        move.b  d0,G_LOWER_DIRECTION(a4)
        lsr.b   #4,d2
        move.b  d2,G_UPPER_DIRECTION(a4)
        move.b  d1,d2
        andi.b  #3,d1
        move.b  d1,G_LOWER_ACTION(a4)
        lsr.b   #4,d2
        andi.b  #3,d2
        move.b  d2,G_UPPER_ACTION(a4)
        rts

legacy_export_gameplay:
        lea     legacy_game_fields,a0
        moveq   #0,d0
        moveq   #0,d1
.legacy_export_field:
        move.b  (a0)+,d0
        cmpi.b  #255,d0
        beq   .legacy_export_controls
        move.b  (a0)+,d1
        move.b  (a4,d1.w),(a5,d0.w)
        bra   .legacy_export_field
.legacy_export_controls:
        move.b  G_UPPER_DIRECTION(a4),d0
        lsl.b   #4,d0
        or.b    G_LOWER_DIRECTION(a4),d0
        btst    #4,$3d(a5)
        beq   .legacy_export_directions
        rol.b   #4,d0
.legacy_export_directions:
        move.b  d0,$53(a5)
        tst.b   G_SOUND_EVENT(a4)
        beq   .legacy_export_done
; Event -> existing audio stream 1FF3, retired with the native sound driver.
        move.b  #$f2,$a1(a5)
        move.b  #$1f,$a2(a5)
        move.b  #9,$a3(a5)
        clr.b   $a4(a5)
        move.b  #1,$a5(a5)
        clr.b   $ae(a5)
.legacy_export_done:
        rts

game_entropy:
        movem.l d1-d7/a0-a6,-(sp)
        ifd LIVE_REFRESH_ADAPTER
        bsr     read_refresh_adapter
        else
        ifd PRODUCT_REPLAY
        moveq   #0,d0
        else
        move.b  $bfe401,d0
        endif
        endif
        andi.l  #1,d0
        movem.l (sp)+,d1-d7/a0-a6
        rts

legacy_game_fields:
        dc.b $3a,G_LOWER+P_PHASE
        dc.b $43,G_LOWER+P_ANIMATION
        dc.b $49,G_LOWER+P_Y
        dc.b $4a,G_LOWER+P_X
        dc.b $4b,G_LOWER+P_IMAGE
        dc.b $4c,G_LOWER+P_COLOUR
        dc.b $73,G_LOWER+P_TARGET_Y
        dc.b $74,G_LOWER+P_TARGET_X
        dc.b $6d,G_LOWER+P_CLOCK
        dc.b $3b,G_UPPER+P_PHASE
        dc.b $44,G_UPPER+P_ANIMATION
        dc.b $45,G_UPPER+P_Y
        dc.b $46,G_UPPER+P_X
        dc.b $47,G_UPPER+P_IMAGE
        dc.b $48,G_UPPER+P_COLOUR
        dc.b $75,G_UPPER+P_TARGET_Y
        dc.b $76,G_UPPER+P_TARGET_X
        dc.b $6e,G_UPPER+P_CLOCK
        dc.b $34,G_COURT_Y
        dc.b $35,G_COURT_X
        dc.b $37,G_SHADOW_COLOUR
        dc.b $38,G_FLIGHT
        dc.b $39,G_CONTACT
        dc.b $4d,G_BALL_Y
        dc.b $4e,G_BALL_X
        dc.b $4f,G_BALL_IMAGE
        dc.b $50,G_BALL_COLOUR
        dc.b $57,G_LAUNCH_X
        dc.b $58,G_LAUNCH_Y
        dc.b $59,G_LAUNCH_Z
        dc.b $5a,G_LAUNCH_SCREEN_Y
        dc.b $5b,G_LAUNCH_BASE_X
        dc.b $5c,G_LAUNCH_BASE_Y
        dc.b $5d,G_TARGET_Y
        dc.b $5e,G_TARGET_X
        dc.b $5f,G_HEIGHT
        dc.b $60,G_VELOCITY_X
        dc.b $61,G_VELOCITY_Y
        dc.b $62,G_VELOCITY_Z
        dc.b $63,G_BASE_SCREEN_Y
        dc.b $64,G_BASE_X
        dc.b $65,G_BASE_Y
        dc.b $66,G_STEP
        dc.b $72,G_RANDOM
        dc.b $6b,G_TICK
        dc.b $6c,G_SERVE_CLOCK
        dc.b $6f,G_ACTION_CLOCK
        dc.b $42,G_DISPLAY
        dc.b 255
        even
