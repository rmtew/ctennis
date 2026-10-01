        include "amiga/game/gameplay_state.i"
; All native gameplay functions use A4 for state, A3/D7 for player/end.
; The adapter imports/exports only at the boundary until CT-05/07/08 retire it.
game_play_tick:
        lea     game_play_state,a4
        bsr     legacy_import_gameplay
        lea     G_LOWER(a4),a3
        moveq   #0,d7
        bsr     game_player_tick
        lea     G_UPPER(a4),a3
        moveq   #1,d7
        bsr     game_player_tick
        bsr     game_ball_tick
        lea     G_LOWER(a4),a3
        moveq   #0,d7
        bsr     game_move_player
        lea     G_UPPER(a4),a3
        moveq   #1,d7
        bsr     game_move_player
        bra     legacy_export_gameplay

        include "amiga/game/gameplay_math.s"
        include "amiga/game/gameplay_ball.s"
        include "amiga/game/gameplay_players.s"
        include "amiga/game/gameplay_contact.s"
        include "amiga/game/gameplay_ai.s"
        even
game_play_state: dcb.b G_SIZE,0
