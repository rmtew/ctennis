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
        ifd NATIVE_SCENE_OBSERVE
        bsr     capture_export_state
        endif
        bra     game_scene_service

game_new_match:
        ifd NATIVE_SCORING
        clr.b   game_score_initialized
        endif
        move.b  d0,game_new_mode
        lea     game_play_state,a0
        moveq   #G_SIZE-1,d7
.clear_play:
        clr.b   (a0)+
        dbra    d7,.clear_play
        lea     game_score_state,a0
        moveq   #S_SIZE-1,d7
.clear_score:
        clr.b   (a0)+
        dbra    d7,.clear_score
        clr.b   game_directions
        clr.b   game_actions
        clr.b   game_status_clock
        clr.b   game_aux_clock
        ifd NATIVE_SCENE_OBSERVE
        bsr     capture_reset_match
        endif
        move.b  #194,game_court_y
        move.b  #194,game_court_x
        move.b  #1,game_shadow_colour
        move.b  #15,game_ball_colour
        move.b  #8,game_upper_y
        move.b  #88,game_upper_x
        move.b  #$fd,game_upper_colour
        move.b  #152,game_lower_y
        move.b  #192,game_lower_x
        move.b  #7,game_lower_image
        move.b  #$f4,game_lower_colour
        move.b  #$80,game_lower_phase
        move.b  #$10,game_upper_phase
        move.b  #$81,game_score_flags
        tst.b   game_new_mode
        beq.s   native_mode_ready
        move.b  #$80,game_score_flags
        move.b  #$80,game_mode
native_mode_ready:
        move.b  #$20,game_display
        bsr     game_audio_reset
        bsr     game_scene_reset
        bsr     game_scene_build_players
        rts
game_new_mode: dc.b 0
        even

; Logical-player input packet. The maintained controls module owns physical state
; and player/end identity; native gameplay consumes the logical packet.
input_update:
        moveq   #0,d0
        move.b  game_mode,d0
        move.b  d0,d1
        lsr.b   #7,d0
        lsr.b   #4,d1
        ifd NATIVE_CONTROLS
        bsr     game_assign_players
        ifd ENHANCED_INTERFACE
        bsr     ui_playback
        endif
        endif
        clr.b   game_directions
        clr.b   game_actions
        btst    #2,game_mode
        bne.s   native_input_done
        bsr     sample_second_input_group
        move.b  d0,d3
        andi.b  #15,d0
        lsl.b   #4,d0
        move.b  d0,game_directions
        andi.b  #$30,d3
        bsr     read_game_input
        move.b  d0,d1
        andi.b  #15,d0
        or.b    d0,game_directions
        lsr.b   #4,d1
        or.b    d1,d3
        move.b  d3,game_actions
native_input_done:
        rts

        ifd NATIVE_GAMEPLAY
        include "amiga/game/gameplay.s"
        include "amiga/game/gameplay_adapter.s"
        include "amiga/game/scene.s"
        include "amiga/game/scene_fields.s"
        include "amiga/game/scene_adapter.s"
        endif

        ifd NATIVE_SCORING
        include "amiga/game/scoring.s"
        include "amiga/game/scoring_adapter.s"
        include "amiga/game/round.s"
        include "amiga/game/result.s"
        include "amiga/game/result_adapter.s"
        endif

        ifd NATIVE_AUDIO
        include "amiga/game/audio.s"
        endif

; Primary tick wraps modulo256; six independently reset clocks saturate255.
game_advance_clocks:
        addq.b #1,game_tick
        cmpi.b #255,game_serve_clock
        beq.s .game_serve_clock_saturated
        addq.b #1,game_serve_clock
.game_serve_clock_saturated:
        cmpi.b #255,game_lower_clock
        beq.s .game_lower_clock_saturated
        addq.b #1,game_lower_clock
.game_lower_clock_saturated:
        cmpi.b #255,game_upper_clock
        beq.s .game_upper_clock_saturated
        addq.b #1,game_upper_clock
.game_upper_clock_saturated:
        cmpi.b #255,game_action_clock
        beq.s .game_action_clock_saturated
        addq.b #1,game_action_clock
.game_action_clock_saturated:
        cmpi.b #255,game_aux_clock
        beq.s .game_aux_clock_saturated
        addq.b #1,game_aux_clock
.game_aux_clock_saturated:
        cmpi.b #255,game_status_clock
        beq.s .game_status_clock_saturated
        addq.b #1,game_status_clock
.game_status_clock_saturated:
        rts
        include "amiga/game/state.i"
