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

; Temporary native-to-legacy new-match initialization. Scalar gameplay rules
; are explicit here; ordinary boot no longer copies an in-progress capture.
; D0=0 one player, 1 two players. CT-04/08 will own native player/audio state.
legacy_new_match:
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
; Initialize ring buffers and envelope timing without copying ROM templates.
        move.b  #$bc,$80(a5)
        move.b  #$19,$81(a5)
        move.b  #2,$82(a5)
        move.b  #2,$83(a5)
        lea     $85(a5),a0
        move.w  #$af,d0
        moveq   #2,d7
legacy_init_audio_channel:
        move.b  d0,(a0)
        move.b  #$c0,1(a0)
        move.b  #32,2(a0)
        move.b  #7,5(a0)
        move.b  #2,7(a0)
        move.b  #16,8(a0)
        move.b  #16,11(a0)
        adda.w  #14,a0
        addi.w  #32,d0
        dbra    d7,legacy_init_audio_channel
        bsr     build_player_sprites
        rts
legacy_new_mode: dc.b 0
        even
