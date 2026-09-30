; Temporary CT-01 bridge, retired subsystem by subsystem in CT-02--CT-08.
; Generated routines and private virtual memory remain build-only oracle inputs.
; Do not put new gameplay into the generator or this compatibility layer.
legacy_active_tick:
        bsr     game_before_scoreboard
        bsr     scoreboard_update
        bsr     game_after_scoreboard
        bsr     input_update
        bsr     score_gate
        bsr     lower_player_state
        bsr     upper_player_state
        bsr     ball_flight_update
        bra     player_movement_and_sprites

legacy_service_tick:
        bsr     irq_counter_prefix
        move.l  #psg_log,psg_ptr
        clr.b   psg_count
        bsr     audio_tick_adapter
        bsr     game_apply_sound
        move.l  #vdp_log,vdp_ptr
        clr.b   vdp_count
        bra     irq_vdp_tail

        include "build/translation/player-frame-routines.s"
