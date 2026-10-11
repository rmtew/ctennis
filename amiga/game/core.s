; One hardware-free simulation implementation, shared by native and standalone.
; Public phases: init; poll previous logical input; sample pads/commands; tick.
; A5 supplies the even 318-byte state base for every body and helper.
; Public live wrappers bind canonical state and preserve caller A5.
; Sink calls are synchronous and preserve registers; they never advance state.
game_core_code_begin:
GAME_CORE_SCHEMA_VERSION equ 2
GAME_CORE_SIMULATION_VERSION equ 3
GAME_ENTROPY_MODERN equ 0
GAME_ENTROPY_LEGACY_SHIFT equ 1
        include "amiga/game/core_input.s"
        include "amiga/game/core_controls.s"
        include "amiga/game/tick.s"
        include "amiga/game/integration.s"

; Complete initialization, including reserved bytes. D0/D7/A0 are scratch.
game_core_init_body:
        move.l  a5,a0
        move.w  #GAME_CORE_STATE_SIZE-1,d7
.clear: clr.b   (a0)+
        dbra    d7,.clear
        move.b  #1,game_upper_owner-game_core_state(a5)
        move.b  #2,game_audio_rate-game_core_state(a5)
        move.b  #2,game_audio_wait-game_core_state(a5)
        move.b  #2,game_scene_ball_layer-game_core_state(a5)
        move.b  #1,field_values+5-game_core_state(a5)
        move.w  #$ace1,game_match_seed-game_core_state(a5)
        move.w  #GAME_TITLE,game_lifecycle-game_core_state(a5)
        rts

; Compatibility observer label; each new match restores the caller's seed.
ui_seed_entropy:
game_core_seed_entropy:
        move.w  game_match_seed-game_core_state(a5),game_entropy_state-game_core_state(a5)
        move.w  game_match_seed-game_core_state(a5),game_legacy_entropy_state-game_core_state(a5)
game_core_seed_entropy_done:
        rts

; Galois16-b400-v2. MOVEQ precedes LSR so its cleared carry cannot erase the bit.
; Advance the modern stream even during historical playback. That recording's
; original carry-clearing bug is explicit legacy-shift16-v1 compatibility only.
; Takeover keeps the already advanced modern stream, with no second seed.
native_entropy_bit:
ui_demo_entropy:
        moveq   #0,d0
        move.w  game_entropy_state-game_core_state(a5),d1
        lsr.w   #1,d1
        bcc.s   .store
        eori.w  #$b400,d1
        moveq   #1,d0
.store: move.w  d1,game_entropy_state-game_core_state(a5)
        tst.b   game_entropy_policy-game_core_state(a5)
        beq.s   .done
        move.w  game_legacy_entropy_state-game_core_state(a5),d1
        lsr.w   #1,d1
        move.w  d1,game_legacy_entropy_state-game_core_state(a5)
        moveq   #0,d0
.done:
        rts

; A title request is a simulation command. UI publication is a separate sink.
game_core_return_title_body:
game_core_return_title_internal equ game_core_return_title_body
        clr.b   game_auto_continue-game_core_state(a5)
        clr.b   game_playback_active-game_core_state(a5)
        clr.b   game_core_command-game_core_state(a5)
        bsr     game_audio_reset
        cmpi.w  #GAME_RESULT_SOUND,game_lifecycle-game_core_state(a5)
        bne.s   .ordinary
        moveq   #0,d0
        bsr     game_new_match
.ordinary:
        bsr     game_celebration_reset
        bsr     game_core_begin_title
        bra     game_core_title_requested

game_clear_returned_status:
        clr.b   field_values+4-game_core_state(a5)
        bra     game_core_status_present

game_core_code_end:
        include "amiga/game/core_state.i"
