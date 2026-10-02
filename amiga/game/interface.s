; Enhanced interface owns only UI state. Scorer state and tally banks are read-only.
; UI edges sample physical packets/matrix before any demo playback substitution.
UI_UP equ 1
UI_DOWN equ 2
UI_LEFT equ 4
UI_RIGHT equ 8
UI_ACTION equ 16
UI_ESCAPE equ 32
UI_PAUSE equ 64
UI_IDLE_TICKS equ 1800 ; 30.04 seconds at the unchanged native callback rate

        include "amiga/game/interface_state.i"
        include "amiga/game/interface_input.s"
        include "amiga/game/interface_pause.s"
        include "amiga/game/interface_menu.s"
        include "amiga/game/interface_render.s"
        include "amiga/game/interface_demo.s"
        include "amiga/game/interface_feedback.s"
        include "amiga/game/interface_text.s"
        even
ui_state: dcb.b U_SIZE,0
        section display_data,data,chip
ui_font: incbin "assets/native/title/font.bin"
ui_overlay_plane: dcb.b 512,0
        section code,code
