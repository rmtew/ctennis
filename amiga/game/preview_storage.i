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
game_preview_projection_requested: ds.w 1
; Explicit full current origin, with no retained-record cursor interpretation.
game_preview_full_origin: ds.w 1
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
; Route0 keeps original full state; route1 owns observational private state.
game_preview_predictor_routes: ds.b 2
game_preview_predictor_reason: ds.w 1
; Scheduler call ownership is not serialized into match/history records.
game_preview_explicit: ds.w 1
game_preview_requested_variant: ds.w 1
game_preview_launch_before: ds.w 1
game_preview_counts: ds.w 2
game_preview_outcomes: ds.w 2
game_preview_launches: ds.b 2
game_preview_interceptions: ds.b 2
game_preview_stream_cursors: ds.l 4
game_preview_synthetic_phases: ds.w 2
game_preview_dispatches: ds.w 2
game_preview_flight_phases: ds.w 2
game_preview_primed: ds.w 1
game_preview_primed_mask: ds.w 1
game_preview_geometry_cursor: ds.w 1
game_preview_coincident: ds.w 1
; Separate generation-owned endpoints; dense status/count/outcomes remain exact.
game_preview_launch_saved: ds.b 2
game_preview_endpoint_attempted: ds.b 2
game_preview_endpoint_ready: ds.b 2
game_preview_endpoint_reasons: ds.w 2
game_preview_endpoint_phases: ds.w 2
game_preview_endpoint_outcomes: ds.w 2
game_preview_endpoints: ds.b 2*PREVIEW_POINT_BYTES
; Per-variant cooperative query stages, reset with each request.
game_preview_query_workspaces: ds.b 2*48
; Root-only synthetic serve dispatch. Each branch retains its own continuation.
game_preview_dispatch_stages: ds.w 2
game_preview_dispatch_generations: ds.l 2
game_preview_dispatch_finished: ds.w 1
game_preview_dispatch_commit: ds.w 1
game_preview_dispatch_launches: ds.b 2
game_preview_dispatch_interceptions: ds.b 2
game_preview_dispatch_origin_phases: ds.b 2
game_preview_state_end:
; D0-D7/A0-A6 and CCR, padded to an independent 64-byte owner.
game_preview_dispatch_registers: ds.b 2*64
game_preview_dispatch_history: ds.b 2*(game_history_state_end-game_history_state)
game_preview_history_saved: ds.b game_history_state_end-game_history_state
game_preview_selected_state: ds.b GAME_CORE_STATE_SIZE
game_preview_incoming_state: ds.b GAME_CORE_STATE_SIZE
game_preview_edited_state: ds.b GAME_CORE_STATE_SIZE
game_preview_held_state: ds.b GAME_CORE_STATE_SIZE
game_preview_released_state: ds.b GAME_CORE_STATE_SIZE
game_preview_launch_states: ds.b 2*GAME_CORE_STATE_SIZE
game_preview_endpoint_scratch: ds.b GAME_CORE_STATE_SIZE
; Independent query candidates; compatibility scratch holds last complete query.
game_preview_query_states: ds.b 2*GAME_CORE_STATE_SIZE
game_preview_paths: ds.b 2*PREVIEW_POINTS*PREVIEW_POINT_BYTES
game_preview_storage_end:
