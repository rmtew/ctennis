; Owned preview scratch. Counts/generations guard unwritten path bytes.
game_preview_storage:
game_preview_state:
game_preview_generation: ds.l 1
game_preview_status: ds.w 1
game_preview_active: ds.b 1
game_preview_variant: ds.b 1
game_preview_budget: ds.w 1
game_preview_operation: ds.w 1
game_preview_end: ds.w 1
game_preview_kind: ds.w 1
game_preview_ordinal: ds.w 1
game_preview_cache_valid: ds.w 1
game_preview_x: ds.w 1
game_preview_y: ds.w 1
game_preview_selected: ds.l 2
game_preview_origin: ds.l 2
game_preview_cursor: ds.l 2
game_preview_incoming: ds.l 2
game_preview_action: ds.l 2
game_preview_incoming_valid: ds.b 1
game_preview_probe_seen: ds.b 1
game_preview_action_found: ds.b 1
game_preview_action_kind: ds.b 1
game_preview_incoming_pending: ds.b 1
; Explicit word alignment, included in resource attribution.
        ds.b 1
game_preview_prefix_count: ds.w 1
game_preview_counts: ds.w 2
game_preview_outcomes: ds.w 2
game_preview_launches: ds.b 2
game_preview_interceptions: ds.b 2
game_preview_stream_cursors: ds.l 4
game_preview_synthetic_phases: ds.w 2
game_preview_dispatches: ds.w 2
game_preview_flight_phases: ds.w 2
game_preview_primed: ds.w 1
game_preview_coincident: ds.w 1
; Separate generation-owned endpoints; dense status/count/outcomes remain exact.
game_preview_launch_saved: ds.b 2
game_preview_endpoint_attempted: ds.b 2
game_preview_endpoint_ready: ds.b 2
game_preview_endpoint_reasons: ds.w 2
game_preview_endpoint_phases: ds.w 2
game_preview_endpoint_outcomes: ds.w 2
game_preview_endpoints: ds.b 2*PREVIEW_POINT_BYTES
game_preview_state_end:
game_preview_history_saved: ds.b game_history_state_end-game_history_state
game_preview_selected_state: ds.b GAME_CORE_STATE_SIZE
game_preview_incoming_state: ds.b GAME_CORE_STATE_SIZE
game_preview_edited_state: ds.b GAME_CORE_STATE_SIZE
game_preview_held_state: ds.b GAME_CORE_STATE_SIZE
game_preview_released_state: ds.b GAME_CORE_STATE_SIZE
game_preview_launch_states: ds.b 2*GAME_CORE_STATE_SIZE
game_preview_endpoint_scratch: ds.b GAME_CORE_STATE_SIZE
game_preview_paths: ds.b 2*PREVIEW_POINTS*PREVIEW_POINT_BYTES
game_preview_storage_end:
