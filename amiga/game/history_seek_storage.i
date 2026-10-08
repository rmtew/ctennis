; Private paused navigation state; never part of the public72 metadata.
game_history_seek_storage:
game_history_seek_generation: ds.l 1
game_history_seek_status: ds.w 1
game_history_seek_remaining: ds.w 1
game_history_seek_active: ds.b 1
        even
game_history_seek_target: ds.l 2
game_history_seek_cursor: ds.l 2
game_history_seek_history: ds.b game_history_state_end-game_history_state
game_history_seek_selected: ds.b GAME_CORE_STATE_SIZE
game_history_seek_working: ds.b GAME_CORE_STATE_SIZE
game_history_seek_storage_end:
