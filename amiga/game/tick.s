; Maintained native lifecycle and source-rate dispatcher, shared by live/replay.
; No source PC/callback kind selects this state. CT-02 owns title/new-game;
; CT-05 owns round transitions. Until then both enter the retained active scene.
; Hooks preserve registers; the temporary adapter owns its legacy register ABI.
GAME_SERVICE equ 0
GAME_PLAYING equ 1

game_begin_active:
        move.w  #GAME_PLAYING,game_lifecycle
        rts

game_source_tick:
        cmpi.w  #GAME_PLAYING,game_lifecycle
        bne.s   game_service_tick
        bsr     legacy_active_tick
game_service_tick:
        bsr     game_observe_pre_tail
        bra     legacy_service_tick

        even
game_lifecycle: dc.w GAME_SERVICE
