; Native scoring packet. Shared score cells alias scorer-owned state; gameplay
; outcomes/poses are sampled and resolved before the native player update.
game_score_tick:
        movem.l d0-d7/a0-a4,-(sp)
        lea     game_score_state-game_core_state(a5),a4
        tst.b   game_score_initialized-game_core_state(a5)
        bne.s   .sample
        move.b  game_score_flags-game_core_state(a5),d0
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
        st      game_score_initialized-game_core_state(a5)
.sample:
        lea     score_sample_fields,a0
        bsr     score_import_fields
        bsr     game_audio_cue_complete
        move.b  d0,S_AUDIO_COMPLETE(a4)
        bsr     game_score_resolve
        lea     score_sample_fields,a0
        bsr     score_export_fields
        moveq   #0,d0
        move.b  S_STAGE(a4),d0
        lea     score_stage_flags,a0
        move.b  (a0,d0.w),d0
        or.b    S_AI(a4),d0
        move.b  d0,game_score_flags-game_core_state(a5)
        btst    #S_EVENT_POSITIONS,S_EVENT(a4)
        beq.s   .sound
        bsr     game_scene_build_players
        bsr     game_render_sprites
.sound:
        lea     game_score_state-game_core_state(a5),a4
        btst    #S_EVENT_SOUND,S_EVENT(a4)
        beq.s   .done
        bsr     game_audio_request_cue
.done:
        movem.l (sp)+,d0-d7/a0-a4
        rts
score_import_fields:
        moveq   #0,d0
        moveq   #0,d1
.next:
        move.l  (a0)+,d0
        tst.l   d0
        bmi.s   .done
        move.w  (a0)+,d1
        lea     (a5,d0.w),a1
        move.b  (a1),(a4,d1.w)
        bra.s   .next
.done:
        rts
score_export_fields:
        moveq   #0,d0
        moveq   #0,d1
.next:
        move.l  (a0)+,d0
        tst.l   d0
        bmi.s   .done
        move.w  (a0)+,d1
        lea     (a5,d0.w),a1
        move.b  (a4,d1.w),(a1)
        bra.s   .next
.done:
        rts
score_stage_flags: dc.b 0,$40,$20,$10,$80
        even
score_sample_fields:
        dc.l game_contact-game_core_state
        dc.w S_OUTCOME
        dc.l game_display-game_core_state
        dc.w S_DISPLAY
        dc.l game_serve_clock-game_core_state
        dc.w S_TIMER
        dc.l game_lower_animation-game_core_state
        dc.w S_LOWER_ANIMATION
        dc.l game_upper_animation-game_core_state
        dc.w S_UPPER_ANIMATION
        dc.l game_flight-game_core_state
        dc.w S_FLIGHT
        dc.l game_lower_phase-game_core_state
        dc.w S_LOWER_PHASE
        dc.l game_upper_phase-game_core_state
        dc.w S_UPPER_PHASE
        dc.l game_lower_y-game_core_state
        dc.w S_LOWER_Y
        dc.l game_lower_x-game_core_state
        dc.w S_LOWER_X
        dc.l game_upper_y-game_core_state
        dc.w S_UPPER_Y
        dc.l game_upper_x-game_core_state
        dc.w S_UPPER_X
        dc.l game_lower_image-game_core_state
        dc.w S_LOWER_IMAGE
        dc.l game_upper_image-game_core_state
        dc.w S_UPPER_IMAGE
        dc.l -1
        even
