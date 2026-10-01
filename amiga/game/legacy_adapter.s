; Temporary CT-01 bridge, retired subsystem by subsystem in CT-02--CT-08.
; Generated routines and private virtual memory remain build-only oracle inputs.
; Do not put new gameplay into the generator or this compatibility layer.
legacy_active_tick:
        bsr     game_scene_update_fields
        bsr     input_update
        ifd NATIVE_SCORING
        bsr     game_score_tick
        else
        bsr     score_gate
        endif
        ifd NATIVE_GAMEPLAY
        bsr     game_play_tick
        bra     game_scene_finish_tick
        else
        bsr     lower_player_state
        bsr     upper_player_state
        bsr     ball_flight_update
        bra     player_movement_and_sprites
        endif

legacy_service_tick:
        bsr     irq_counter_prefix
        bsr     game_audio_tick
        bsr     game_apply_sound
        bra     game_scene_service

        include "build/translation/player-frame-routines.s"

; Temporary native-to-legacy new-match initialization. Scalar gameplay rules
; are explicit here; ordinary boot no longer copies an in-progress capture.
; D0=0 one player, 1 two players. CT-04/08 will own native player/audio state.
legacy_new_match:
        ifd NATIVE_SCORING
        clr.b   game_score_initialized
        endif
        move.b  d0,legacy_new_mode
        lea     $10(a5),a0
        move.w  #239,d7
legacy_clear_match:
        clr.b   (a0)+
        dbra    d7,legacy_clear_match
        lea     $10(a5),a0
        moveq   #39,d7
legacy_hide_records:
        move.b  #$c2,(a0)+
        dbra    d7,legacy_hide_records
        clr.b   $36(a5)
        move.b  #1,$37(a5)
        move.b  #15,$50(a5)
        move.b  #8,$45(a5)
        move.b  #88,$46(a5)
        move.b  #$fd,$48(a5)
        move.b  #152,$49(a5)
        move.b  #192,$4a(a5)
        move.b  #7,$4b(a5)
        move.b  #$f4,$4c(a5)
        move.b  #$80,$3a(a5)
        move.b  #$10,$3b(a5)
        move.b  #$81,$3c(a5)
        tst.b   legacy_new_mode
        beq.s   legacy_mode_ready
        move.b  #$80,$3c(a5)
        move.b  #$80,$3d(a5)
legacy_mode_ready:
        move.b  #$20,$42(a5)
        move.b  #1,$7c(a5)
        bsr     game_audio_reset
        bsr     game_scene_reset
        bsr     game_scene_build_players
        rts
legacy_new_mode: dc.b 0
        even

        ifd NATIVE_CONTROLS
; CT-03 ABI adapter only. The maintained controls module owns physical state
; and player/end identity; CT-04 still consumes logical-player packed nibbles.
input_update:
        moveq   #0,d0
        move.b  $3d(a5),d0
        move.b  d0,d1
        lsr.b   #7,d0
        lsr.b   #4,d1
        bsr     game_assign_players
        clr.b   $53(a5)
        clr.b   $56(a5)
        btst    #2,$3d(a5)
        bne.s   legacy_input_done
        bsr     sample_second_input_group
        move.b  d0,d3
        andi.b  #15,d0
        lsl.b   #4,d0
        move.b  d0,$53(a5)
        andi.b  #$30,d3
        bsr     read_game_input
        move.b  d0,d1
        andi.b  #15,d0
        or.b    d0,$53(a5)
        lsr.b   #4,d1
        or.b    d1,d3
        move.b  d3,$56(a5)
legacy_input_done:
        rts

; Existing callers pass a court end in D6 bit4 and a logical-player packed
; field in D0. Keep this ABI here; ownership comes from the native assignment.
normalize_input_for_player_side:
        move.b  game_lower_owner,d2
        btst    #4,d6
        beq.s   legacy_owner_ready
        move.b  game_upper_owner,d2
legacy_owner_ready:
        tst.b   d2
        beq.s   legacy_owner_selected
        rol.b   #4,d0
legacy_owner_selected:
        move.b  d0,d2
        rts
        endif

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
