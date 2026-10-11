; A learning step is actual full-core play on the ordinary nominal callback,
; with history frozen and physical tutorial controls kept out of logical play.
; No predictor state or animation sample is promoted to a playable state.

; Z clear only for this canonical complete-callback hardware owner. Preserve
; every register; sinks save/restore CCR around this explicit ownership query.
tutorial_live_owner:
        tst.b   tutorial_running
        beq.s   .done
        cmpa.l  #game_core_state,a5
        bne.s   .no
        tst.b   game_preview_active
        bne.s   .no
        tst.b   game_history_replaying
        bne.s   .no
        tst.b   game_history_seek_active
        bne.s   .no
        tst.b   tutorial_running
.done:  rts
.no:    cmpa.l  a5,a5
        rts

; Press-time full incoming/serve origin is authored before projected work.
; Current generations/placement must match. The selected action comes from the
; physical packet now, not the prior callback's variant or a later release.
tutorial_capture_shot:
        clr.b   tutorial_gesture_ready
        move.l  tutorial_generation,d0
        cmp.l   game_preview_generation,d0
        bne     .done
        tst.w   game_preview_cache_valid
        beq.s   .done
        moveq   #0,d0
        move.b  tutorial_x,d0
        cmp.w   game_preview_x,d0
        bne.s   .done
        move.b  tutorial_y,d0
        cmp.w   game_preview_y,d0
        bne.s   .done
        cmpi.w  #PREVIEW_PRIME,game_preview_status
        bcs.s   .done
        cmpi.w  #PREVIEW_READY,game_preview_status
        bhi.s   .done
        move.b  #1,tutorial_gesture_variant
        btst    #4,tutorial_packet
        beq.s   .action
        clr.b   tutorial_gesture_variant
.action:
        cmpi.w  #3,game_preview_kind
        bne.s   .copy
        ; The initial serve is explicitly the prospective held launch on screen.
        clr.b   tutorial_gesture_variant
.copy:  lea     tutorial_gesture_state,a0
        lea     game_preview_edited_state,a1
        bsr     game_history_copy_state
        move.l  game_preview_generation,tutorial_gesture_generation
        st      tutorial_gesture_ready
.done:  rts

tutorial_start_shot:
        tst.b   tutorial_gesture_ready
        beq     .done
        clr.b   tutorial_gesture_ready
        ; The accepted full press snapshot owns its literal action independently
        ; of action-only preview refreshes while G is down. Chords/long holds
        ; consume it in tutorial_sample; a later button release cannot edit it.
        tst.b   tutorial_running
        bne     .done
        cmpi.b  #2,game_history_mode
        bne     .done
        tst.b   game_preview_active
        bne     .done
        tst.b   game_history_replaying
        bne     .done
        tst.b   game_history_seek_active
        bne     .done
        cmpi.w  #SEEK_JOB_PENDING,game_history_seek_status
        beq     .done
        cmpi.w  #SEEK_JOB_READY,game_history_seek_status
        beq     .done
        lea     game_core_state,a0
        lea     tutorial_gesture_state,a1
        bsr     game_history_copy_state
        bsr     discard_ready_scene
        clr.l   tutorial_neutral_copper
        clr.l   tutorial_visible_surface
        clr.b   tutorial_ball_mode
        clr.b   tutorial_refresh_pending
        bsr     game_preview_invalidate
        clr.b   tutorial_pending
        clr.b   tutorial_work_pending
        clr.b   tutorial_exploration_polled
        clr.b   tutorial_human_launched
        clr.b   tutorial_opponent_launched
        clr.b   tutorial_stop_reason
        clr.w   tutorial_exploration_ticks
        st      tutorial_explored
        st      tutorial_running
        addq.w  #1,tutorial_exploration_cycles
.done:  rts

; Called before physical sampling on subsequent ordinary callbacks. Initial
; entry performs this same logical poll before its first logical pad sample.
tutorial_exploration_poll:
        movem.l d0-d7/a0-a6,-(sp)
        lea     game_core_state,a5
        bsr     game_round_poll_body
        st      tutorial_exploration_polled
        movem.l (sp)+,d0-d7/a0-a6
        rts

tutorial_exploration_update:
        movem.l d0-d7/a0-a6,-(sp)
        tst.b   tutorial_exploration_polled
        bne.s   .sample
        bsr     tutorial_exploration_poll
.sample:
        clr.b   tutorial_exploration_polled
        lea     game_core_state,a5
        moveq   #0,d0
        moveq   #0,d1
        tst.b   tutorial_gesture_variant
        bne.s   .pads
        moveq   #16,d0
.pads:  bsr     game_core_sample_pads_body
        moveq   #0,d0
        moveq   #0,d1
        move.b  game_input_bits,d0
        andi.b  #16,d0
        move.b  game_input_pressed,d1
        andi.b  #16,d1
        moveq   #0,d2
        moveq   #0,d3
        moveq   #0,d4
        moveq   #0,d5
        bsr     game_core_sample_result_body
        ; Retain ordinary render-before-full-dispatch ordering. All hardware
        ; writes target an owned complete scene; preview/background is disabled.
        bsr     game_render_sprites
        bsr     game_tick_dispatch_body
        clr.l   tutorial_neutral_copper
        bsr     complete_scene
        addq.w  #1,tutorial_exploration_ticks
        tst.b   tutorial_stop_reason
        bne.s   .pause
        tst.b   tutorial_opponent_launched
        bne.s   .incoming
        cmpi.w  #GAME_PLAYING,game_lifecycle
        bne.s   .ended
        move.b  game_contact,d0
        andi.b  #$8d,d0
        bne.s   .ended
        cmpi.w  #512,tutorial_exploration_ticks
        bcs.s   .done
        move.b  #4,tutorial_stop_reason
        bra.s   .pause
.incoming:
        move.b  #2,tutorial_stop_reason
        bra.s   .pause
.ended:
        move.b  #3,tutorial_stop_reason
.pause:
        ; No hook-time state escapes: all actors, scene, clocks and audio tails
        ; have completed. Incoming preview requests start at this full boundary.
        clr.b   tutorial_running
        moveq   #0,d7
        tst.b   game_play_state+G_LOWER_AI
        beq.s   .end
        moveq   #1,d7
.end:   move.b  d7,tutorial_end
        mulu.w  #P_SIZE,d7
        lea     game_play_state,a0
        move.b  P_X(a0,d7.w),tutorial_x
        move.b  P_Y(a0,d7.w),tutorial_y
        st      tutorial_refresh_pending
        cmpi.b  #1,tutorial_stop_reason
        bne.s   .done
        st      tutorial_menu
        clr.b   tutorial_menu_selection
        move.b  tutorial_packet,tutorial_previous_menu_packet
.done:  movem.l (sp)+,d0-d7/a0-a6
        rts

; Called from the preserving actual launch hooks. Never mutate history or
; preview buffers; pause is deferred until the whole dispatcher tail returns.
tutorial_exploration_launch:
        bsr     tutorial_live_owner
        beq.s   .done
        cmp.b   tutorial_end,d7
        bne.s   .opponent
        st      tutorial_human_launched
        rts
.opponent:
        tst.b   tutorial_human_launched
        beq.s   .done
        st      tutorial_opponent_launched
.done:  rts

; Exit from the complete explored boundary, applying current position/action.
; Menu confirmation never supplies the selected shot bit. Commit owns history
; checkpoint installation before physical-input reconciliation/live recording.
tutorial_play_from_here:
        tst.b   tutorial_running
        bne     .done
        cmpi.b  #2,game_history_mode
        bne     .done
        tst.b   game_preview_active
        bne     .done
        tst.b   game_history_replaying
        bne     .done
        tst.b   game_history_seek_active
        bne     .done
        cmpi.w  #SEEK_JOB_PENDING,game_history_seek_status
        beq     .done
        cmpi.w  #SEEK_JOB_READY,game_history_seek_status
        beq     .done
        movem.l d0-d7/a0-a6,-(sp)
        moveq   #0,d7
        move.b  tutorial_end,d7
        mulu.w  #P_SIZE,d7
        lea     game_play_state,a0
        move.b  tutorial_x,P_X(a0,d7.w)
        move.b  tutorial_y,P_Y(a0,d7.w)
        lea     game_core_state,a5
        bsr     game_scene_build_players
        moveq   #0,d0
        moveq   #0,d1
        tst.b   tutorial_active_variant
        bne.s   .pads
        moveq   #16,d0
.pads:  bsr     game_core_sample_pads_body
        bsr     game_history_commit_current
        tst.l   d0
        beq     .restore
        bsr     discard_ready_scene
        bsr     tutorial_footer_invalidate
        clr.b   tutorial_active
        clr.b   tutorial_pending
        clr.b   tutorial_menu
        clr.b   tutorial_work_pending
        clr.b   tutorial_explored
        clr.b   tutorial_refresh_pending
        clr.b   tutorial_gesture_ready
        clr.b   tutorial_advance_pending
        clr.w   tutorial_render_phase
        clr.b   ui_paused
        st      tutorial_resume_defer
        bsr     tutorial_reconcile_inputs
        ; Exploration stays muted: Original hardware periods were untouched.
        ; On committing the explored branch, install its actual periods/levels.
        lea     game_audio_voices,a0
        moveq   #0,d7
.voice:
        moveq   #0,d0
        move.w  AV_PERIOD(a0),d0
        beq.s   .level
        bsr     game_audio_write_period
.level: moveq   #0,d0
        move.b  AV_LEVEL(a0),d0
        bsr     game_audio_write_level
        adda.w  #AV_SIZE,a0
        addq.w  #1,d7
        cmpi.w  #3,d7
        bne.s   .voice
        bsr     tutorial_restore_court
        move.w  #$ffff,ui_overlay_signature
.restore:
        movem.l (sp)+,d0-d7/a0-a6
.done:  rts
