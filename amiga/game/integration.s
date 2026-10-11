; Shared native frame order, also used by maintained replay.
game_active_tick:
        bsr     game_scene_update_fields
        bsr     input_update
        bsr     game_score_tick

        bsr     game_play_tick
        bra     game_scene_finish_tick


game_service_tail:
        bsr     game_advance_clocks
        bsr     game_audio_tick
        bsr     game_apply_sound
        bra     game_scene_service

game_new_match:
        clr.b   game_score_initialized-game_core_state(a5)
        move.b  d0,game_new_mode-game_core_state(a5)
        lea     game_play_state-game_core_state(a5),a0
        ; Even-aligned canonical blocks have whole-longword sizes. Preserve
        ; the byte loop's final pointer, counter and zero-clear condition codes.
        moveq   #G_SIZE/4-1,d7
.clear_play:
        clr.l   (a0)+
        dbra    d7,.clear_play
        lea     game_score_state-game_core_state(a5),a0
        moveq   #S_SIZE/4-1,d7
.clear_score:
        clr.l   (a0)+
        dbra    d7,.clear_score
        bsr     ui_seed_entropy
        clr.b   game_directions-game_core_state(a5)
        clr.b   game_actions-game_core_state(a5)
        clr.b   game_status_clock-game_core_state(a5)
        clr.b   game_aux_clock-game_core_state(a5)
        move.b  #194,game_court_y-game_core_state(a5)
        move.b  #194,game_court_x-game_core_state(a5)
        move.b  #1,game_shadow_colour-game_core_state(a5)
        move.b  #15,game_ball_colour-game_core_state(a5)
        move.b  #8,game_upper_y-game_core_state(a5)
        move.b  #88,game_upper_x-game_core_state(a5)
        move.b  #$fd,game_upper_colour-game_core_state(a5)
        move.b  #152,game_lower_y-game_core_state(a5)
        move.b  #192,game_lower_x-game_core_state(a5)
        move.b  #7,game_lower_image-game_core_state(a5)
        move.b  #$f4,game_lower_colour-game_core_state(a5)
        move.b  #$80,game_lower_phase-game_core_state(a5)
        move.b  #$10,game_upper_phase-game_core_state(a5)
        move.b  #$81,game_score_flags-game_core_state(a5)
        tst.b   game_new_mode-game_core_state(a5)
        beq.s   native_mode_ready
        move.b  #$80,game_score_flags-game_core_state(a5)
        move.b  #$80,game_mode-game_core_state(a5)
native_mode_ready:
        move.b  #$20,game_display-game_core_state(a5)
        bsr     game_audio_reset
        bsr     game_scene_reset
        bsr     game_scene_build_players
        rts
        even

; Logical-player input packet. The maintained controls module owns physical state
; and player/end identity; native gameplay consumes the logical packet.
input_update:
        moveq   #0,d0
        move.b  game_mode-game_core_state(a5),d0
        move.b  d0,d1
        lsr.b   #7,d0
        lsr.b   #4,d1
        bsr     game_assign_players
        tst.b   game_playback_active-game_core_state(a5)
        beq.s   .live_controls
        move.b  game_playback_mask-game_core_state(a5),game_player_controls-game_core_state(a5)
.live_controls:
        clr.b   game_directions-game_core_state(a5)
        clr.b   game_actions-game_core_state(a5)
        btst    #2,game_mode-game_core_state(a5)
        bne.s   native_input_done
        bsr     sample_second_input_group
        move.b  d0,d3
        andi.b  #15,d0
        lsl.b   #4,d0
        move.b  d0,game_directions-game_core_state(a5)
        andi.b  #$30,d3
        bsr     read_game_input
        move.b  d0,d1
        andi.b  #15,d0
        or.b    d0,game_directions-game_core_state(a5)
        lsr.b   #4,d1
        or.b    d1,d3
        move.b  d3,game_actions-game_core_state(a5)
native_input_done:
        rts

        include "amiga/game/gameplay.s"
        include "amiga/game/gameplay_controls.s"
        include "amiga/game/scene.s"
        include "amiga/game/scene_fields.s"
        include "amiga/game/scene_integration.s"

        include "amiga/game/scoring.s"
        include "amiga/game/scoring_integration.s"
        include "amiga/game/round.s"
        include "amiga/game/result.s"
        include "amiga/game/result_audio.s"

        include "amiga/game/audio.s"

; Primary tick wraps modulo256; six independently reset clocks saturate255.
game_advance_clocks:
        addq.b #1,game_tick-game_core_state(a5)
        cmpi.b #255,game_serve_clock-game_core_state(a5)
        beq.s .game_serve_clock_saturated
        addq.b #1,game_serve_clock-game_core_state(a5)
.game_serve_clock_saturated:
        cmpi.b #255,game_lower_clock-game_core_state(a5)
        beq.s .game_lower_clock_saturated
        addq.b #1,game_lower_clock-game_core_state(a5)
.game_lower_clock_saturated:
        cmpi.b #255,game_upper_clock-game_core_state(a5)
        beq.s .game_upper_clock_saturated
        addq.b #1,game_upper_clock-game_core_state(a5)
.game_upper_clock_saturated:
        cmpi.b #255,game_action_clock-game_core_state(a5)
        beq.s .game_action_clock_saturated
        addq.b #1,game_action_clock-game_core_state(a5)
.game_action_clock_saturated:
        cmpi.b #255,game_aux_clock-game_core_state(a5)
        beq.s .game_aux_clock_saturated
        addq.b #1,game_aux_clock-game_core_state(a5)
.game_aux_clock_saturated:
        cmpi.b #255,game_status_clock-game_core_state(a5)
        beq.s .game_status_clock_saturated
        addq.b #1,game_status_clock-game_core_state(a5)
.game_status_clock_saturated:
        rts
        include "amiga/game/state.i"
