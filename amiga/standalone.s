; CPU-only executable: exactly the product simulation code and immutable tables.
; Observation adapters preserve every register and have no physical side effects.
        section match_core,code
        include "amiga/game/core.s"
        include "amiga/game/history.s"
        include "amiga/game/core_trace.s"

game_render_sprites:
        rts
game_scene_present_fields:
        rts
game_core_title_requested:
        rts
game_core_status_present:
        rts
game_audio_write_period:
        rts
game_audio_write_level:
        rts
game_observe_pre_tail:
        rts
game_apply_sound:
        rts

        section history,bss
game_history_buffer: ds.b HISTORY_BUFFER_BYTES
game_history_buffer_end:
; HUNK longword padding, outside the attach buffer
        ds.b 2
