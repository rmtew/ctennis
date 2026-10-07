; Native lifecycle dispatcher shared by live play and seeded attract playback.
GAME_SERVICE equ 0
GAME_PLAYING equ 1
GAME_TITLE equ 2
GAME_SELECTION_HELD equ 3
GAME_ROUND_PAUSE equ 4
GAME_ROUND_SOUND equ 5
GAME_RESULT_SOUND equ 6
GAME_TITLE_TRANSITION equ 7
GAME_TITLE_SOUND equ 8
GAME_RESTART_SOUND equ 9
GAME_RESTART_SERVE_SOUND equ 10

game_begin_active:
        clr.b   game_score_initialized
        move.w  #GAME_PLAYING,game_lifecycle
        rts

        ifd CORE_TRACE
game_tick_dispatch_body:
        else
game_tick_dispatch:
        endif
        tst.b   game_core_command
        beq.s   .dispatch
        moveq   #0,d0
        move.b  game_core_command,d0
        clr.b   game_core_command
        subq.b  #1,d0
        bra     game_core_start_choice
.dispatch:
        cmpi.w  #GAME_TITLE,game_lifecycle
        beq     game_returned_title_tick
        cmpi.w  #GAME_SELECTION_HELD,game_lifecycle
        beq     game_selection_tick
        cmpi.w  #GAME_PLAYING,game_lifecycle
        bne.s   game_service_tick
        bsr     game_active_tick
game_service_tick:
        bsr     game_observe_pre_tail
        bra     game_service_tail

        even

        include "amiga/game/menu.s"

; Returned title preserves the original waiting animation/scoreboard service,
; with mode bit2 suppressing physical gameplay input. Fresh boot stays frozen.
game_returned_title_tick:
        tst.b   game_restart_context
        beq     game_menu_tick
        bsr     game_active_tick
        bra     game_service_tick

game_selection_tick:
        tst.b   game_restart_context
        beq     game_menu_tick
        bra     game_service_tick
