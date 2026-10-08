; Native presentation/controller state only. Canonical state remains unchanged.
tutorial_state:
tutorial_active: ds.b 1
tutorial_pending: ds.b 1
tutorial_menu: ds.b 1
tutorial_menu_selection: ds.b 1
tutorial_x: ds.b 1
tutorial_y: ds.b 1
tutorial_end: ds.b 1
tutorial_active_variant: ds.b 1
tutorial_input_source: ds.b 1
tutorial_packet: ds.b 1
tutorial_previous_packet: ds.b 1
tutorial_modifier_used: ds.b 1
tutorial_enter_pending: ds.b 1
tutorial_title_pending: ds.b 1
tutorial_tap_pending: ds.b 1
tutorial_resume_defer: ds.b 1
tutorial_enter_pressed: ds.b 1
tutorial_previous_menu_packet: ds.b 1
tutorial_work_pending: ds.b 1
        ds.b 1
tutorial_status: ds.w 1
tutorial_animation_index: ds.w 1
tutorial_progress_operations: ds.w 1
tutorial_render_generation: ds.w 1
tutorial_published_generation: ds.w 1
tutorial_resume_count: ds.w 1
tutorial_generation: ds.l 1
tutorial_selected_cursor: ds.l 2
tutorial_tap_time: ds.l 1
tutorial_repeat_time: ds.l 1
tutorial_animation_time: ds.l 1
tutorial_double_ticks: ds.l 1
tutorial_repeat_ticks: ds.l 1
tutorial_render_surface: ds.l 1
tutorial_visible_surface: ds.l 1
tutorial_render_offset: ds.l 1
; Returned-worker observations; no additional court buffers.
tutorial_presentation_generation: ds.l 1
tutorial_marker_generation: ds.l 1
tutorial_animation_generation: ds.l 1
tutorial_available_counts: ds.w 2
tutorial_available_outcomes: ds.w 2
tutorial_placement_dirty: ds.b 1
tutorial_placement_ready: ds.b 1
tutorial_marker_ready: ds.b 1
tutorial_animation_ready: ds.b 1
tutorial_ball_mode: ds.b 1
tutorial_waiting_ready: ds.b 1
; Reserved optional-trail preference; default0, no trail passes scheduled.
tutorial_trails_enabled: ds.b 1
        ds.b 1
tutorial_build_generation: ds.w 1
tutorial_text_row: ds.w 1
tutorial_render_phase: ds.w 1
tutorial_render_path: ds.w 1
tutorial_render_point: ds.w 1
tutorial_render_variant: ds.b 1
tutorial_line_active: ds.b 1
tutorial_ghost_actor: ds.w 1
tutorial_ghost_row: ds.w 1
tutorial_line_x: ds.w 1
tutorial_line_y: ds.w 1
tutorial_line_end_x: ds.w 1
tutorial_line_end_y: ds.w 1
tutorial_line_dx: ds.w 1
tutorial_line_dy: ds.w 1
tutorial_line_sx: ds.w 1
tutorial_line_sy: ds.w 1
tutorial_line_error: ds.w 1
tutorial_line_colour: ds.w 1
tutorial_line_dash: ds.w 1
tutorial_paths: ds.l 2
tutorial_counts: ds.w 2
tutorial_outcomes: ds.w 2
tutorial_coincident: ds.w 1
        ds.w 1
tutorial_scene_objects: ds.b 64
tutorial_sprite_source: ds.l 1
tutorial_scene_layer: ds.b 1
        ds.b 1
tutorial_state_end:
tutorial_interrupted_state equ game_history_live_backup
        section tutorial_display,bss,chip
tutorial_surface0: ds.b 4*6144
tutorial_surface1: ds.b 4*6144
tutorial_surfaces_end:
        section code,code
