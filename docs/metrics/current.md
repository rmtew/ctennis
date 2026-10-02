# Native resource and loading metrics

Completion: **incomplete**. Acceptance is separate from metric coverage.
Product SHA256: `a307ec8c5d0289bc4fd8df6d5ada3deab7c3a6c184dcb36431b4d02b0d548df1`.
Identity excludes generated report files and Git report commits; timestamps are not freshness evidence.

| Executable | Code | Data | BSS | Loaded payload |
|---:|---:|---:|---:|---:|
| 248488 | 49572 | 152540 | 0 | 202112 |

Asset bytes: {'graphics': 109380, 'audio': 9892, 'replay_loaded_bytes': 1110}. These overlap loaded hunks.

Executable-size budget/headroom: unmeasured (no cap configured); size is not RAM.

Timing uses elapsed emulated colour clocks, including chip-bus waits; host time is unavailable.
PAL display budget: 70,824 CCK (~19.97 ms). Simulation budget: ~59,191.14 CCK (~16.69 ms).
Typical = median; p95 = nearest rank. Frozen/absent phase values remain unmeasured.

UI construction is grouped by page (title = menu; help includes controls/credits), independently of callback-entry profiles; menu-page redraws can occur during pause/input transitions. Pause-only UI construction remains unmeasured.

Release ADF executable: 211928 bytes; symbol bytes removed: 36560. Development retains symbols.
RAM measures whole initialized machine pools including OS/stack. Direct-executable and cold ADF startup differ; compare RAM within the same startup case.

| Mutually exclusive executable category | Bytes |
|---|---:|
| audio_envelopes | 128 |
| audio_period_table | 3,072 |
| audio_scores | 1,504 |
| build_version_text | 22 |
| celebration_period_table | 3,072 |
| celebration_scores | 2,112 |
| celebration_square_wave | 4 |
| court_bitplanes | 24,576 |
| cpu_instructions | 12,186 |
| font | 1,024 |
| front_court_and_title_copper_lists | 3,184 |
| hunk_header_table | 28 |
| hunk_record_headers_and_ends | 24 |
| initial_hardware_sprites | 576 |
| menu_font_mac | 1,024 |
| mode_banks | 3,072 |
| other_initialized_tables_and_scalars | 750 |
| pre_rendered_demo_options | 512 |
| pre_rendered_help_options | 768 |
| pre_rendered_menu_options | 1,280 |
| pre_rendered_title_ui_pages | 29,696 |
| pre_rendered_ui_pages | 14,848 |
| relocation_offsets | 9,740 |
| relocation_record_framing | 24 |
| replay_packets | 1,110 |
| reserved_back_copper | 3,048 |
| reserved_back_sprites | 576 |
| reserved_native_stack | 4,096 |
| reserved_state_and_work_buffers | 962 |
| reserved_ui_overlay | 512 |
| scene_animation_table | 36 |
| scene_pose_table | 112 |
| scene_robot_pose_table | 112 |
| scene_sprite_variants | 11,264 |
| score_game_banks | 21,504 |
| score_patch_pointer_tables | 7,972 |
| score_point_banks | 14,336 |
| separate_debug_records | 0 |
| source_alignment_padding | 14 |
| status_banks | 7,168 |
| symbol_name_padding | 1,503 |
| symbol_names | 23,889 |
| symbol_record_framing | 11,168 |
| title_bitplanes | 24,576 |
| ui_text_and_line_pointer_tables | 1,304 |
| **Exact file total** | **248,488** |

Mutually exclusive file-byte categories; code/data hunk sizes are a separate containing view, not added again. CPU instructions use actual emitted listing lengths, including operand extensions. Reserved dcb storage is file-backed, not HUNK_BSS. Zero debug means no emitted HUNK_DEBUG record; symbols are counted separately.
Byte-identical incbin payload bytes beyond first copies: 22,528 B. These remain included in the categories; aliasing safety is unproven.

Cold loading completion issues: Missing/invalid cold milestone: reset; Missing/invalid cold milestone: loadseg_complete; Missing/invalid cold milestone: executable_entry; Missing/invalid cold milestone: assets_ready; Missing/invalid cold milestone: first_complete_title_frame; Missing/invalid cold milestone: input_responsive; Continuous loaded-title selection evidence missing/invalid

| cold-one: stale | | | | | |
| two: stale | | | | | |
| setup: stale | | | | | |
| demo: stale | | | | | |

Coverage: title: unmeasured, help: unmeasured, one-player-rally: unmeasured, two-player-rally: unmeasured, demo: unmeasured, pause: unmeasured, match-end: unmeasured, celebration: unmeasured

Deltas: {"state": "no previous accepted compatible report"}

Refresh hook: after merging new fonts/celebration, run the affected native checks or `RUST_LOG=info python scripts/native_metrics.py --refresh --record`; never copy results from an unfinished branch.
