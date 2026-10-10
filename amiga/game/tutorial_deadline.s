; Experimental G2 owner. Numerical allowances are calibration hypotheses.
; Only the root loop dispatches this owner, after mandatory service/accounting.
TUTORIAL_BG_CHUNK_E equ 1000
TUTORIAL_BG_PHYSICS_E equ 4000
        ifnd TUTORIAL_BG_PHYSICS_ENABLE
TUTORIAL_BG_PHYSICS_ENABLE equ 1
        endif
TUTORIAL_BG_SERVICE_E equ 500
TUTORIAL_BG_MARGIN_E equ 500
TUTORIAL_BG_CALLBACK_E equ 11150
TUTORIAL_BG_ENTRY_E equ 400
TUTORIAL_BG_COMPLETION_MARGIN_E equ 250
TUTORIAL_BG_READY_LINE equ 253
TUTORIAL_BG_LINE_CCK equ 226

tutorial_background:
        ; Main-loop accounting is fresh. Decline cheaply near the nominal
        ; boundary before classification/beam work can delay mandatory input.
        move.l  simulation_interval,d0
        sub.l   simulation_phase,d0
        bcs     .done
        cmpi.l  #TUTORIAL_BG_CHUNK_E+TUTORIAL_BG_SERVICE_E+TUTORIAL_BG_MARGIN_E,d0
        bcs     .done
        bsr     tutorial_background_class
        tst.l   d0
        beq     .done
        move.l  #TUTORIAL_BG_CHUNK_E+TUTORIAL_BG_SERVICE_E+TUTORIAL_BG_MARGIN_E,d5
        cmpi.w  #8,d0
        bne.s   .cost_ready
        move.l  #TUTORIAL_BG_PHYSICS_E+TUTORIAL_BG_SERVICE_E+TUTORIAL_BG_MARGIN_E,d5
.cost_ready:
        ; A whole current line is excluded. No background work is admitted
        ; during the guarded publication interval or its reserved approach.
        bsr     read_presentation_line
        cmpi.w  #TUTORIAL_BG_READY_LINE-1,d0
        bcc     .done
        move.w  #TUTORIAL_BG_READY_LINE-1,d1
        sub.w   d0,d1
        mulu.w  #TUTORIAL_BG_LINE_CCK,d1
        move.l  d5,d2
        mulu.w  #5,d2
        cmp.l   d2,d1
        bcs     .done
        bsr     account_sim_timer
        move.l  simulation_interval,d0
        sub.l   simulation_phase,d0
        bcs     .done
        ; Preserve the nominal sample boundary and reserve the next root
        ; transport/presenter service. Full callback completion has its own
        ; inequality, even though the earlier entry inequality usually wins.
        cmp.l   d5,d0
        bcs     .done
        ; A callback waits until its nominal start. Earlier idle slack cannot
        ; be lent to completion; reserve full callback + entry lateness +
        ; residual completion uncertainty against the next whole interval.
        move.l  simulation_interval_whole,d0
        cmpi.l  #TUTORIAL_BG_CALLBACK_E+TUTORIAL_BG_ENTRY_E+TUTORIAL_BG_COMPLETION_MARGIN_E,d0
        bcs     .done
        move.l  tutorial_generation,d0
        moveq   #1,d1
        jsr     game_preview_step
        tst.l   d0
        beq.s   .done
        addq.w  #1,tutorial_progress_operations
        bsr     tutorial_progress_returned
.done:  rts

; Read-only class peek. It never restores a context, changes history metadata,
; enters hardware sampling or grants ownership. D0 operation3/4/5/7/8/9 or0.
tutorial_background_class:
        tst.b   tutorial_active
        beq     .no
        tst.b   ui_paused
        beq     .no
        tst.b   tutorial_menu
        bne     .no
        tst.b   tutorial_enter_pending
        bne     .no
        tst.b   tutorial_title_pending
        bne     .no
        tst.b   tutorial_resume_defer
        bne     .no
        tst.b   tutorial_placement_dirty
        bne     .no
        tst.b   tutorial_footer_dirty
        bne     .no
        tst.b   tutorial_work_pending
        beq     .no
        tst.b   game_preview_active
        bne     .no
        tst.b   game_history_replaying
        bne     .no
        tst.b   game_history_seek_active
        bne     .no
        cmpi.b  #2,game_history_mode
        bne     .no
        cmpi.w  #SEEK_JOB_PENDING,game_history_seek_status
        beq     .no
        cmpi.w  #SEEK_JOB_READY,game_history_seek_status
        beq     .no
        move.l  tutorial_generation,d0
        cmp.l   game_preview_generation,d0
        bne     .no
        cmp.l   tutorial_presentation_generation,d0
        bne     .no
        cmpi.w  #PREVIEW_HELD,game_preview_status
        bcs     .no
        cmpi.w  #PREVIEW_RELEASED,game_preview_status
        bhi     .no
        bsr     tutorial_animation_due
        tst.l   d0
        bne     .no
        bsr     game_preview_desired_variant
        lea     game_preview_predictor_routes,a0
        cmpi.b  #1,(a0,d7.w)
        bne     .no
        lea     game_preview_launches,a0
        tst.b   (a0,d7.w)
        bne     .no
        bsr     game_preview_context_address
        move.l  a0,a3
        cmpi.w  #GAME_PLAYING,game_lifecycle-game_core_state(a3)
        bne     .no
        tst.b   game_core_command-game_core_state(a3)
        bne     .no
        tst.b   game_restart_context-game_core_state(a3)
        bne     .no
        tst.b   game_entropy_policy-game_core_state(a3)
        bne     .no
        move.w  d7,d4
        lsl.w   #3,d4
        lea     game_preview_stream_cursors,a0
        adda.w  d4,a0
        lea     game_history_oldest,a1
        bsr     game_preview_compare_cursor
        tst.l   d0
        bmi     .no
        lea     game_history_cursor,a1
        bsr     game_preview_compare_cursor
        tst.l   d0
        bgt     .no
        beq.s   .synthetic
        move.l  4(a0),d0
        andi.w  #HISTORY_RECORDS-1,d0
        mulu.w  #HISTORY_RECORD_BYTES,d0
        move.l  game_history_store,a0
        adda.l  d0,a0
        moveq   #0,d0
        move.w  (a0),d0
        cmpi.w  #4,d0
        bne.s   .supported
        move.l  2(a0),d1
        or.l    6(a0),d1
        or.l    10(a0),d1
        bne     .no
        bra.s   .supported
.synthetic:
        move.w  d7,d4
        add.w   d4,d4
        lea     game_preview_synthetic_phases,a0
        move.w  (a0,d4.w),d0
        beq.s   .poll
        cmpi.w  #1,d0
        beq.s   .pads
        cmpi.w  #3,d0
        beq.s   .tick
        cmpi.w  #2,d0
        bne     .no
        moveq   #4,d0
        rts
.pads:  moveq   #3,d0
        rts
.tick:  moveq   #8,d0
        bra.s   .supported
.poll:  moveq   #7,d0
.supported:
        cmpi.w  #8,d0
        beq     .physics
        cmpi.w  #3,d0
        beq.s   .yes
        cmpi.w  #4,d0
        beq.s   .yes
        cmpi.w  #5,d0
        beq.s   .yes
        cmpi.w  #9,d0
        beq.s   .yes
        cmpi.w  #7,d0
        bne     .no
        ; Exact round-poll no-op partition: initialized PLAYING, no restart
        ; and no round/match award. Audio/lifecycle transitions are excluded.
        tst.b   game_score_initialized-game_core_state(a3)
        beq     .no
        btst    #5,game_score_state+S_MODE-game_core_state(a3)
        bne     .no
.yes:   rts
.physics:
        tst.w   tutorial_background_physics_enabled
        beq     .no
        ; Only projected incoming motion/contact. Neither arbitrary original
        ; dispatch, outgoing ball nor endpoint query is admitted here.
        lea     game_play_state-game_core_state(a3),a4
        move.b  game_mode-game_core_state(a3),d1
        andi.b  #$e4,d1
        bne     .no
        tst.b   game_score_initialized-game_core_state(a3)
        beq     .no
        cmpi.b  #S_ACTIVE,game_score_state+S_STAGE-game_core_state(a3)
        bne     .no
        moveq   #0,d2
        move.w  game_preview_end,d2
        cmpi.w  #1,d2
        bhi     .no
        moveq   #1,d1
        lsl.b   d2,d1
        cmp.b   game_score_state+S_AI-game_core_state(a3),d1
        bne     .no
        ori.b   #$40,d1
        cmp.b   game_score_flags-game_core_state(a3),d1
        bne     .no
        move.b  game_mode-game_core_state(a3),d1
        lsr.b   #4,d1
        andi.w  #1,d1
        cmp.w   d2,d1
        bne     .no
        cmp.b   game_lower_owner-game_core_state(a3),d2
        bne     .no
        move.w  d2,d1
        eori.w  #1,d1
        cmp.b   game_upper_owner-game_core_state(a3),d1
        bne     .no
        lsl.b   #6,d1
        move.b  G_CONTACT(a4),d3
        andi.b  #$40,d3
        cmp.b   d1,d3
        bne     .no
        move.b  G_CONTACT(a4),d1
        andi.b  #$8d,d1
        bne     .no
        move.b  G_FLIGHT(a4),d1
        andi.b  #$c0,d1
        cmpi.b  #$40,d1
        bne     .no
        ; Nonoverlapping receiving court intervals prove at most one contact
        ; derive/root call before movement/ball advancement in this dispatch.
        cmpi.b  #98,G_LOWER+P_Y(a4)
        bcs     .no
        cmpi.b  #154,G_LOWER+P_Y(a4)
        bcc     .no
        cmpi.b  #7,G_UPPER+P_Y(a4)
        bcs     .no
        cmpi.b  #63,G_UPPER+P_Y(a4)
        bcc     .no
        move.b  G_LOWER+P_PHASE(a4),d1
        or.b    G_UPPER+P_PHASE(a4),d1
        move.b  d1,d2
        andi.b  #$c0,d1
        bne     .no
        andi.b  #$20,d2
        beq.s   .counts
        cmpi.b  #$10,G_SERVE_CLOCK(a4)
        bls     .no
.counts:
        lea     game_preview_counts,a0
        cmpi.w  #PREVIEW_POINTS,(a0)
        bhi     .no
        cmpi.w  #PREVIEW_POINTS,2(a0)
        bhi     .no
        move.w  d7,d4
        add.w   d4,d4
        cmpi.w  #PREVIEW_POINTS-2,(a0,d4.w)
        bhi     .no
        tst.w   d7
        beq.s   .phases
        move.w  2(a0),d1
        addq.w  #1,d1
        cmp.w   (a0),d1
        beq     .no
.phases:
        lea     game_preview_dispatches,a0
        cmpi.w  #PREVIEW_SEGMENT_PHASES-2,(a0,d4.w)
        bhi     .no
        moveq   #8,d0
        rts
.no:    moveq   #0,d0
        rts

; Read-only same-layout scheduling switch for controlled before/after builds.
        even
tutorial_background_physics_enabled: dc.w TUTORIAL_BG_PHYSICS_ENABLE
