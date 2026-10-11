# Native resource and loading metrics

Completion: **incomplete**. Acceptance is separate from metric coverage.
Product SHA256: `f5314aee9216ae02216cd111925836c22bac79ec92ac3d52a9c0bf99eafc9ca9`.
Identity excludes generated report files and Git report commits; timestamps are not freshness evidence.

| Executable | Code | Data | BSS | Loaded payload |
|---:|---:|---:|---:|---:|
| 212356 | 60064 | 112700 | 151192 | 323956 |

Asset bytes: {'graphics': 73588, 'audio': 9892, 'replay_loaded_bytes': 1110}. These overlap loaded hunks.

Executable-size budget/headroom: unmeasured (no cap configured); size is not RAM.

Timing uses elapsed emulated colour clocks, including chip-bus waits; host time is unavailable.
PAL display budget: 70,824 CCK (~19.97 ms). Simulation budget: ~59,191.14 CCK (~16.69 ms).
Typical = median; p95 = nearest rank. Frozen/absent phase values remain unmeasured.

UI construction is grouped by page (title = menu; help includes controls/credits), independently of callback-entry profiles; menu-page redraws can occur during pause/input transitions. Pause-only UI construction remains unmeasured.

Release ADF executable: 179420 bytes; symbol bytes removed: 32936. Development retains symbols.
RAM measures whole initialized machine pools including OS/stack. Direct-executable and cold ADF startup differ; compare RAM within the same startup case.

| Mutually exclusive executable category | Bytes |
|---|---:|
| audio_envelopes | 128 |
| audio_period_table | 3,072 |
| audio_scores | 1,504 |
| build_version_text | 14 |
| celebration_period_table | 3,072 |
| celebration_scores | 2,112 |
| celebration_square_wave | 4 |
| court_bitplanes | 24,576 |
| cpu_instructions | 28,674 |
| font | 1,024 |
| front_court_and_title_copper_lists | 648 |
| hunk_header_table | 40 |
| hunk_record_headers_and_ends | 60 |
| initial_hardware_sprites | 576 |
| menu_font_mac | 1,024 |
| mode_banks | 3,072 |
| other_initialized_tables_and_scalars | 1,702 |
| pre_rendered_demo_options | 512 |
| pre_rendered_help_options | 768 |
| pre_rendered_menu_options | 768 |
| pre_rendered_title_identities | 512 |
| pre_rendered_title_ui_pages | 29,696 |
| pre_rendered_ui_pages | 14,848 |
| relocation_offsets | 6,508 |
| relocation_record_framing | 48 |
| replay_packets | 1,110 |
| reserved_back_copper | 504 |
| reserved_back_sprites | 576 |
| reserved_native_stack | 4,096 |
| reserved_state_and_work_buffers | 966 |
| reserved_third_copper | 504 |
| reserved_third_sprites | 576 |
| reserved_ui_overlay | 512 |
| scene_animation_table | 36 |
| scene_pose_table | 112 |
| scene_robot_pose_table | 112 |
| scene_sprite_variants | 11,264 |
| score_patch_pointer_tables | 528 |
| separate_debug_records | 0 |
| source_alignment_padding | 14 |
| square_led_construction_definitions | 48 |
| status_banks | 7,168 |
| symbol_name_padding | 1,643 |
| symbol_names | 21,813 |
| symbol_record_framing | 9,480 |
| title_bitplanes | 24,576 |
| ui_text_and_line_pointer_tables | 1,756 |
| **Exact file total** | **212,356** |

Mutually exclusive file-byte categories; code/data hunk sizes are a separate containing view, not added again. CPU instructions use actual emitted listing lengths, including operand extensions. Reserved dcb storage is file-backed, not HUNK_BSS. Zero debug means no emitted HUNK_DEBUG record; symbols are counted separately.
Byte-identical incbin payload bytes beyond first copies: 8,192 B. These remain included in the categories; aliasing safety is unproven.

Cold loading completion issues: Missing/invalid cold milestone: reset; Missing/invalid cold milestone: loadseg_complete; Missing/invalid cold milestone: executable_entry; Missing/invalid cold milestone: assets_ready; Missing/invalid cold milestone: first_complete_title_frame; Missing/invalid cold milestone: input_responsive; Continuous loaded-title selection evidence missing/invalid

| cold-one: not run | | | | | |
| two: not run | | | | | |
| setup: not run | | | | | |
| demo: not run | | | | | |

Coverage: title: unmeasured, help: unmeasured, one-player-rally: unmeasured, two-player-rally: unmeasured, demo: unmeasured, pause: unmeasured, match-end: unmeasured, celebration: unmeasured

Deltas: {"previous_identity": "ea32fefef08509b2817ddc05827848878c2fcfe606d30284cb811fac71096884", "previous_report": "docs/metrics/baselines/pre-title-score-current.json", "previous_report_sha256": "3f201f2af4bf6bf03f50d2a9685442e57b61bb207d2ab024e62d931fb7dbdede", "runtime": {"cold-one": {"state": "incompatible or unmeasured"}, "demo": {"state": "incompatible or unmeasured"}, "setup": {"state": "incompatible or unmeasured"}, "two": {"state": "incompatible or unmeasured"}}, "state": "historical reviewed baseline; master has no accepted metrics report", "static_bytes": {"bss_bytes": 151192, "code_bytes": 10500, "data_bytes": -39840, "executable_bytes": -36124, "loaded_payload_bytes": 121852}}

Refresh hook: after merging new fonts/celebration, run the affected native checks or `RUST_LOG=info python scripts/native_metrics.py --refresh --record`; never copy results from an unfinished branch.
