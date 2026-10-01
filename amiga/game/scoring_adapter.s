; Temporary ABI for gameplay/presentation/audio that have not yet retired the
; byte page. Points, games, mode and scoring stage persist in native state.
game_score_tick:
        movem.l d0-d7/a0-a4,-(sp)
        lea     game_score_state,a4
        tst.b   game_score_initialized
        bne.s   .sample
        lea     score_initial_fields,a0
        bsr     score_import_fields
        move.b  $3c(a5),d0
        move.b  d0,d1
        andi.b  #7,d0
        move.b  d0,S_AI(a4)
        moveq   #S_IDLE,d0
        btst    #7,d1
        bne.s   .sound_wait
        moveq   #S_ACTIVE,d0
        btst    #6,d1
        bne.s   .stage
        moveq   #S_POINT_PAUSE,d0
        btst    #5,d1
        bne.s   .stage
        moveq   #S_GAME_PAUSE,d0
        btst    #4,d1
        bne.s   .stage
        moveq   #S_IDLE,d0
        bra.s   .stage
.sound_wait:
        moveq   #S_WAIT_SOUND,d0
.stage:
        move.b  d0,S_STAGE(a4)
        st      game_score_initialized
.sample:
        lea     score_sample_fields,a0
        bsr     score_import_fields
        bsr     game_score_resolve
        lea     score_initial_fields,a0
        bsr     score_export_fields
        lea     score_sample_fields,a0
        bsr     score_export_fields
        moveq   #0,d0
        move.b  S_STAGE(a4),d0
        lea     score_stage_flags,a0
        move.b  (a0,d0.w),d0
        or.b    S_AI(a4),d0
        move.b  d0,$3c(a5)
        btst    #S_EVENT_POSITIONS,S_EVENT(a4)
        beq.s   .sound
        bsr     build_player_sprites
        bsr     upload_sprite_attributes
.sound:
        lea     game_score_state,a4
        btst    #S_EVENT_SOUND,S_EVENT(a4)
        beq.s   .done
        bsr     assign_sound_stream_4
.done:
        movem.l (sp)+,d0-d7/a0-a4
        rts
score_import_fields:
        moveq   #0,d0
        moveq   #0,d1
.next:
        move.b  (a0)+,d0
        cmpi.b  #255,d0
        beq.s   .done
        move.b  (a0)+,d1
        move.b  (a5,d0.w),(a4,d1.w)
        bra.s   .next
.done:
        rts
score_export_fields:
        moveq   #0,d0
        moveq   #0,d1
.next:
        move.b  (a0)+,d0
        cmpi.b  #255,d0
        beq.s   .done
        move.b  (a0)+,d1
        move.b  (a4,d1.w),(a5,d0.w)
        bra.s   .next
.done:
        rts
score_stage_flags: dc.b 0,$40,$20,$10,$80
score_initial_fields:
        dc.b $3d,S_MODE,$3e,S_POINTS,$3f,S_POINTS+1
        dc.b $40,S_GAMES,$41,S_GAMES+1
        dc.b $77,S_ROUND_GAME_A,$78,S_ROUND_GAME_B,255
score_sample_fields:
        dc.b $39,S_OUTCOME,$42,S_DISPLAY,$6c,S_TIMER
        dc.b $a4,S_AUDIO_POSITION,$a5,S_AUDIO_LIMIT
        dc.b $43,S_LOWER_ANIMATION,$44,S_UPPER_ANIMATION,$38,S_FLIGHT
        dc.b $3a,S_LOWER_PHASE,$3b,S_UPPER_PHASE
        dc.b $49,S_LOWER_Y,$4a,S_LOWER_X,$45,S_UPPER_Y,$46,S_UPPER_X
        dc.b $4b,S_LOWER_IMAGE,$47,S_UPPER_IMAGE,255
        even
