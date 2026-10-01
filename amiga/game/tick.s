; Maintained native lifecycle and source-rate dispatcher, shared by live/replay.
; No source PC/callback kind selects this state. CT-05 owns round transitions.
; Hooks preserve registers; the temporary adapter owns its legacy register ABI.
GAME_SERVICE equ 0
GAME_PLAYING equ 1
GAME_TITLE equ 2
GAME_SELECTION_HELD equ 3
GAME_ROUND_PAUSE equ 4
GAME_ROUND_SOUND equ 5

game_begin_active:
        ifd NATIVE_SCORING
        clr.b   game_score_initialized
        endif
        move.w  #GAME_PLAYING,game_lifecycle
        rts

game_source_tick:
        cmpi.w  #GAME_TITLE,game_lifecycle
        beq     game_menu_tick
        cmpi.w  #GAME_SELECTION_HELD,game_lifecycle
        beq     game_menu_tick
        cmpi.w  #GAME_PLAYING,game_lifecycle
        bne.s   game_service_tick
        bsr     legacy_active_tick
game_service_tick:
        bsr     game_observe_pre_tail
        bra     legacy_service_tick

        even
game_lifecycle: dc.w GAME_SERVICE

        include "amiga/game/menu.s"
