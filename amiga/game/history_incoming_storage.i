; One live latest incoming origin. Separate from canonical state/72 metadata.
game_history_incoming_storage:
game_history_incoming_state: ds.b GAME_CORE_STATE_SIZE
game_history_incoming_cursor: ds.l 2 ; complete POST-operation boundary
game_history_incoming_schema: ds.w 1
game_history_incoming_simulation: ds.w 1
game_history_incoming_epoch: ds.l 1
game_history_incoming_end: ds.w 1
game_history_incoming_valid: ds.b 1
game_history_incoming_pending: ds.b 1
game_history_live_epoch: ds.l 1
game_history_incoming_pending_end: ds.w 1
game_history_incoming_storage_end:
