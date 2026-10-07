; One hardware-free simulation implementation, shared by native and standalone.
; Public phases: init; poll previous logical input; sample pads/commands; tick.
; Sink calls are synchronous and preserve registers; they never advance state.
game_core_code_begin:
        include "amiga/game/core_controls.s"
        include "amiga/game/tick.s"
        include "amiga/game/integration.s"

; Complete initialization, including reserved bytes. D0/D7/A0 are scratch.
game_core_init:
        lea     game_core_state,a0
        move.w  #GAME_CORE_STATE_SIZE-1,d7
.clear: clr.b   (a0)+
        dbra    d7,.clear
        move.b  #1,game_upper_owner
        move.b  #2,game_audio_rate
        move.b  #2,game_audio_wait
        move.b  #2,game_scene_ball_layer
        move.b  #1,field_values+5
        move.w  #$ace1,game_match_seed
        rts

; Compatibility observer label; each new match restores the caller's seed.
ui_seed_entropy:
game_core_seed_entropy:
        move.w  game_match_seed,game_entropy_state
        rts

; Galois16-b400-v1, unchanged demo algorithm; live play now uses it too.
; The game PRNG still owns its original 8-bit state and call order.
native_entropy_bit:
ui_demo_entropy:
        move.w  game_entropy_state,d1
        lsr.w   #1,d1
        moveq   #0,d0
        bcc.s   .store
        eori.w  #$b400,d1
        moveq   #1,d0
.store: move.w  d1,game_entropy_state
        rts

; A title request is a simulation command. UI publication is a separate sink.
game_core_return_title:
        clr.b   game_auto_continue
        clr.b   game_playback_active
        clr.b   game_core_command
        bsr     game_audio_reset
        cmpi.w  #GAME_RESULT_SOUND,game_lifecycle
        bne.s   .ordinary
        moveq   #0,d0
        bsr     game_new_match
.ordinary:
        bsr     game_celebration_reset
        bsr     game_core_begin_title
        bra     game_core_title_requested

game_clear_returned_status:
        clr.b   field_values+4
        bra     game_core_status_present

game_core_code_end:
        include "amiga/game/core_state.i"
