; Fixed BSS partitions; labels expose the owned layout to actual-core proofs.
game_history_buffer:
        ds.b HISTORY_CHECKPOINT_OFFSET
game_history_checkpoints:
        ds.b HISTORY_CHECKPOINTS*HISTORY_CHECKPOINT_BYTES
game_history_attempts:
        ds.b HISTORY_ATTEMPTS*HISTORY_ATTEMPT_BYTES
game_history_live_backup:
        ds.b GAME_CORE_STATE_SIZE
game_history_buffer_end:
