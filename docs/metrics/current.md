# Native resource and loading metrics

Completion: **complete**. Acceptance is separate from metric coverage.
Product SHA256: `045bf76b5553886b9463aa161346c11508ff6437b6b422fd88ffe27dbb6216a8`.
Identity excludes generated report files and Git report commits; timestamps are not freshness evidence.

| Executable | Code | Data | BSS | Loaded payload |
|---:|---:|---:|---:|---:|
| 235180 | 49932 | 137980 | 14336 | 202248 |

Asset bytes: {'graphics': 95092, 'audio': 9892, 'replay_loaded_bytes': 1110}. These overlap loaded hunks.

Executable-size budget/headroom: unmeasured (no cap configured); size is not RAM.

Timing uses elapsed emulated colour clocks, including chip-bus waits; host time is unavailable.
PAL display budget: 70,824 CCK (~19.97 ms). Simulation budget: ~59,191.14 CCK (~16.69 ms).
Typical = median; p95 = nearest rank. Frozen/absent phase values remain unmeasured.

UI construction is grouped by page (title = menu; help includes controls/credits), independently of callback-entry profiles; menu-page redraws can occur during pause/input transitions. Pause-only UI construction remains unmeasured.

Release ADF executable: 197812 bytes; symbol bytes removed: 37368. Development retains symbols.
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
| cpu_instructions | 12,442 |
| font | 1,024 |
| front_court_and_title_copper_lists | 3,200 |
| hunk_header_table | 32 |
| hunk_payload_alignment_padding | 2 |
| hunk_record_headers_and_ends | 36 |
| initial_hardware_sprites | 576 |
| menu_font_mac | 1,024 |
| mode_banks | 3,072 |
| other_initialized_tables_and_scalars | 790 |
| pre_rendered_demo_options | 512 |
| pre_rendered_help_options | 768 |
| pre_rendered_menu_options | 1,024 |
| pre_rendered_title_ui_pages | 29,696 |
| pre_rendered_ui_pages | 14,848 |
| relocation_offsets | 9,800 |
| relocation_record_framing | 32 |
| replay_packets | 1,110 |
| reserved_back_copper | 3,064 |
| reserved_back_sprites | 576 |
| reserved_native_stack | 4,096 |
| reserved_state_and_work_buffers | 962 |
| reserved_ui_overlay | 512 |
| scene_animation_table | 36 |
| scene_pose_table | 112 |
| scene_robot_pose_table | 112 |
| scene_sprite_variants | 11,264 |
| score_game_banks | 21,504 |
| score_patch_pointer_tables | 8,008 |
| separate_debug_records | 0 |
| source_alignment_padding | 13 |
| square_led_construction_definitions | 48 |
| status_banks | 7,168 |
| symbol_name_padding | 1,530 |
| symbol_names | 24,438 |
| symbol_record_framing | 11,400 |
| title_bitplanes | 24,576 |
| ui_text_and_line_pointer_tables | 1,291 |
| **Exact file total** | **235,180** |

Mutually exclusive file-byte categories; code/data hunk sizes are a separate containing view, not added again. CPU instructions use actual emitted listing lengths, including operand extensions. Reserved dcb storage is file-backed, not HUNK_BSS. Zero debug means no emitted HUNK_DEBUG record; symbols are counted separately.
Byte-identical incbin payload bytes beyond first copies: 2,048 B. These remain included in the categories; aliasing safety is unproven.


| Case / profile | Samples | Update median / p95 / max ms | Sprite render / UI page construction max ms | Dispatcher max ms | Work / deadline headroom ms |
|---|---:|---:|---:|---:|---:|
| cold-one / title | 9 | 2.474 / 14.493 / 14.493 | unmeasured / 11.673 | 1.247 | 2.195 / 2.015 |
| cold-one / one-player-rally | 3507 | 5.687 / 6.136 / 7.716 | 1.609 / unmeasured | 3.970 | 8.972 / 8.776 |
| cold-one / two-player-rally | 1 | 5.694 / 5.694 / 5.694 | 1.363 / unmeasured | 2.228 | 10.994 / 10.852 |
| cold-one / match-end | 48 | 3.669 / 4.538 / 5.840 | 1.577 / unmeasured | 0.773 | 10.848 / 10.741 |
| cold-one / celebration | 887 | 3.104 / 3.515 / 5.886 | 0.918 / unmeasured | 1.263 | 10.802 / 10.256 |

cold-one: chip used 307,784 B; free 216,504 B; largest block 215,312 B; runtime peak 307784 B; cold initialized-pool peak 310888 B.
Deadlines/publications: `{'missed_native_callbacks': 0, 'missed_publications_counter': 0, 'publication_failures': 0}`. Allocation failures: unmeasured; pre-Exec bootstrap: unmeasured.

| Cold loading stage | Emulated seconds | Signed offset from previous listed milestone (ms) |
|---|---:|---:|
| reset | 0.000000 | unmeasured |
| boot_script_begins | unmeasured | unmeasured |
| loadseg_begin | unmeasured | unmeasured |
| loadseg_complete | 23.392447 | 23392.447 |
| executable_entry | 23.393450 | 1.003 |
| assets_ready | 23.426694 | 33.243 |
| first_complete_title_frame | 23.486006 | 59.312 |
| input_responsive | 23.513730 | 27.724 |

Total reset to successful input: 23513.730 ms; displayed title and input both ready: 23513.730 ms. Disk reads/seeks and host launch time: unavailable.
Emulated CCK only. LoadSeg catch is completion/entry, not start; file reads/relocation not independently separated. First complete title frame is a frame boundary after a full title-selected frame. Input-responsive point is successful normal selection after the existing first-callback input request; includes that workflow wait. Milestones may overlap: input can respond before a complete title frame. Listed-milestone differences are signed offsets, not invented sequential phase durations; boot complete requires both displayed title and successful input.


| Case / profile | Samples | Update median / p95 / max ms | Sprite render / UI page construction max ms | Dispatcher max ms | Work / deadline headroom ms |
|---|---:|---:|---:|---:|---:|
| two / title | 6 | 3.468 / 14.916 / 14.916 | unmeasured / 12.202 | 1.215 | 1.772 / 1.654 |
| two / one-player-rally | 1 | 6.113 / 6.113 / 6.113 | 1.404 / unmeasured | 2.272 | 10.575 / 10.461 |
| two / two-player-rally | 9262 | 5.639 / 6.096 / 7.447 | 1.608 / unmeasured | 3.719 | 9.241 / 9.017 |
| two / match-end | 48 | 3.576 / 4.068 / 5.768 | 1.360 / unmeasured | 0.758 | 10.920 / 10.788 |
| two / celebration | 887 | 3.115 / 3.524 / 5.943 | 0.921 / unmeasured | 1.126 | 10.745 / 10.425 |

two: chip used 341,520 B; free 182,768 B; largest block 182,192 B; runtime peak 341520 B; cold initialized-pool peak unmeasured.
Deadlines/publications: `{'missed_native_callbacks': 0, 'missed_publications_counter': 0, 'publication_failures': 0}`. Allocation failures: unmeasured; pre-Exec bootstrap: unmeasured.


| Case / profile | Samples | Update median / p95 / max ms | Sprite render / UI page construction max ms | Dispatcher max ms | Work / deadline headroom ms |
|---|---:|---:|---:|---:|---:|
| setup / title | 1236 | 2.191 / 2.198 / 14.801 | unmeasured / 12.204 | 12.513 | 1.888 / 1.698 |
| setup / help | 576 | 2.184 / 2.191 / 14.818 | unmeasured / 12.427 | 12.531 | 1.870 / 1.662 |
| setup / one-player-rally | 32 | 5.634 / 6.116 / 6.220 | 1.549 / unmeasured | 2.532 | 10.468 / 10.334 |
| setup / pause | 87 | 2.127 / 2.381 / 15.713 | unmeasured / unmeasured | 0.070 | 0.975 / 0.890 |

setup deadlines/publications: `{'missed_publications_counter': 0, 'missed_named_profile_deadlines': 0, 'missed_native_callbacks': 0, 'scope': 'Setup raw checker covers all callbacks; demo deadline counts cover named measured profiles only, unprofiled transitions remain unmeasured.'}`.


| Case / profile | Samples | Update median / p95 / max ms | Sprite render / UI page construction max ms | Dispatcher max ms | Work / deadline headroom ms |
|---|---:|---:|---:|---:|---:|
| demo / title | 1800 | 2.191 / 2.197 / 14.478 | unmeasured / unmeasured | 1.648 | 2.210 / 1.983 |
| demo / demo | 11703 | 5.437 / 6.105 / 10.631 | 6.844 / unmeasured | 3.967 | 6.057 / 5.901 |

demo deadlines/publications: `{'missed_publications_counter': 0, 'missed_named_profile_deadlines': 0, 'missed_native_callbacks': None, 'scope': 'Setup raw checker covers all callbacks; demo deadline counts cover named measured profiles only, unprofiled transitions remain unmeasured.'}`.


Coverage: title: measured, help: measured, one-player-rally: measured, two-player-rally: measured, demo: measured, pause: measured, match-end: measured, celebration: measured

Deltas: {"previous_identity": "ea32fefef08509b2817ddc05827848878c2fcfe606d30284cb811fac71096884", "previous_report": "docs/metrics/baselines/pre-title-score-current.json", "previous_report_sha256": "3f201f2af4bf6bf03f50d2a9685442e57b61bb207d2ab024e62d931fb7dbdede", "runtime": {"cold-one": {"profiles": {"celebration": {"dispatcher": {"max_cck": -46, "minimum_headroom_cck": 46.0, "p95_cck": -53, "typical_median_cck": -2.0}, "render": {"max_cck": -1, "minimum_headroom_cck": 1.0, "p95_cck": -6, "typical_median_cck": 0.0}, "ui_construction_render": null, "update_including_render": {"max_cck": -39, "minimum_headroom_cck": 39.0, "p95_cck": -24, "typical_median_cck": 2.0}}, "demo": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "help": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "match-end": {"dispatcher": {"max_cck": 18, "minimum_headroom_cck": -18.0, "p95_cck": -2, "typical_median_cck": -0.5}, "render": {"max_cck": -53, "minimum_headroom_cck": 53.0, "p95_cck": -57, "typical_median_cck": -53.0}, "ui_construction_render": null, "update_including_render": {"max_cck": 188, "minimum_headroom_cck": -188.0, "p95_cck": 257, "typical_median_cck": -203.0}}, "one-player-rally": {"dispatcher": {"max_cck": -24, "minimum_headroom_cck": 24.0, "p95_cck": 4, "typical_median_cck": -6.0}, "render": {"max_cck": -4, "minimum_headroom_cck": 4.0, "p95_cck": -7, "typical_median_cck": 0.0}, "ui_construction_render": null, "update_including_render": {"max_cck": -180, "minimum_headroom_cck": 180.0, "p95_cck": 57, "typical_median_cck": -21.0}}, "pause": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "title": {"dispatcher": {"max_cck": -22, "minimum_headroom_cck": 22.0, "p95_cck": -22, "typical_median_cck": 0.0}, "render": null, "ui_construction_render": {"max_cck": -3076, "minimum_headroom_cck": 3076.0, "p95_cck": -3076, "typical_median_cck": -2948.0}, "update_including_render": {"max_cck": -3072, "minimum_headroom_cck": 3072.0, "p95_cck": -3072, "typical_median_cck": -1903.0}}, "two-player-rally": {"dispatcher": {"max_cck": -264, "minimum_headroom_cck": 264.0, "p95_cck": -264, "typical_median_cck": -264.0}, "render": {"max_cck": -54, "minimum_headroom_cck": 54.0, "p95_cck": -54, "typical_median_cck": -54.0}, "ui_construction_render": null, "update_including_render": {"max_cck": -341, "minimum_headroom_cck": 341.0, "p95_cck": -341, "typical_median_cck": -341.0}}}, "reset_to_input_cck": -4809655, "runtime_memory_bytes": {"chip_free_bytes": -152, "chip_used_bytes": 152, "largest_chip_free_block_bytes": -176, "other_free_bytes": 0, "other_pool_bytes": 0, "other_used_bytes": 0}}, "demo": {"profiles": {"celebration": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "demo": {"dispatcher": {"max_cck": -95, "minimum_headroom_cck": 95.0, "p95_cck": 14, "typical_median_cck": 20.0}, "render": {"max_cck": 304, "minimum_headroom_cck": -304.0, "p95_cck": -9, "typical_median_cck": 0.0}, "ui_construction_render": null, "update_including_render": {"max_cck": 421, "minimum_headroom_cck": -421.0, "p95_cck": 24, "typical_median_cck": 20.0}}, "help": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "match-end": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "one-player-rally": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "pause": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "title": {"dispatcher": {"max_cck": -28, "minimum_headroom_cck": 28.0, "p95_cck": 0, "typical_median_cck": 0.0}, "render": null, "ui_construction_render": null, "update_including_render": {"max_cck": -2479, "minimum_headroom_cck": 2479.0, "p95_cck": 0, "typical_median_cck": 1.0}}, "two-player-rally": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}}}, "setup": {"profiles": {"celebration": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "demo": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "help": {"dispatcher": {"max_cck": 66, "minimum_headroom_cck": -66.0, "p95_cck": 0, "typical_median_cck": 0.0}, "render": null, "ui_construction_render": {"max_cck": 57, "minimum_headroom_cck": -57.0, "p95_cck": 57, "typical_median_cck": 2.0}, "update_including_render": {"max_cck": 49, "minimum_headroom_cck": -49.0, "p95_cck": -2, "typical_median_cck": -1.0}}, "match-end": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "one-player-rally": {"dispatcher": {"max_cck": 260, "minimum_headroom_cck": -260.0, "p95_cck": 166, "typical_median_cck": -24.5}, "render": {"max_cck": -193, "minimum_headroom_cck": 193.0, "p95_cck": -187, "typical_median_cck": -2.5}, "ui_construction_render": null, "update_including_render": {"max_cck": -157, "minimum_headroom_cck": 157.0, "p95_cck": -12, "typical_median_cck": 23.5}}, "pause": {"dispatcher": {"max_cck": 2, "minimum_headroom_cck": -2.0, "p95_cck": 2, "typical_median_cck": 2.0}, "render": null, "ui_construction_render": null, "update_including_render": {"max_cck": -2590, "minimum_headroom_cck": 2590.0, "p95_cck": 262, "typical_median_cck": 89.5}}, "title": {"dispatcher": {"max_cck": -2045, "minimum_headroom_cck": 2045.0, "p95_cck": 0, "typical_median_cck": 0.0}, "render": null, "ui_construction_render": {"max_cck": -2537, "minimum_headroom_cck": 2537.0, "p95_cck": -2537, "typical_median_cck": -2539.0}, "update_including_render": {"max_cck": -1759, "minimum_headroom_cck": 1759.0, "p95_cck": 0, "typical_median_cck": 2.0}}, "two-player-rally": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}}}, "two": {"profiles": {"celebration": {"dispatcher": {"max_cck": 27, "minimum_headroom_cck": -27.0, "p95_cck": -12, "typical_median_cck": 2.0}, "render": {"max_cck": 9, "minimum_headroom_cck": -9.0, "p95_cck": 38, "typical_median_cck": 0.0}, "ui_construction_render": null, "update_including_render": {"max_cck": 198, "minimum_headroom_cck": -198.0, "p95_cck": 3, "typical_median_cck": -1.5}}, "demo": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "help": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "match-end": {"dispatcher": {"max_cck": 7, "minimum_headroom_cck": -7.0, "p95_cck": 1, "typical_median_cck": 13.5}, "render": {"max_cck": 22, "minimum_headroom_cck": -22.0, "p95_cck": 34, "typical_median_cck": 2.5}, "ui_construction_render": null, "update_including_render": {"max_cck": -152, "minimum_headroom_cck": 152.0, "p95_cck": 7, "typical_median_cck": 44.5}}, "one-player-rally": {"dispatcher": {"max_cck": 318, "minimum_headroom_cck": -318.0, "p95_cck": 318, "typical_median_cck": 318.0}, "render": {"max_cck": -103, "minimum_headroom_cck": 103.0, "p95_cck": -103, "typical_median_cck": -103.0}, "ui_construction_render": null, "update_including_render": {"max_cck": 1277, "minimum_headroom_cck": -1277.0, "p95_cck": 1277, "typical_median_cck": 1277.0}}, "pause": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "title": {"dispatcher": {"max_cck": -128, "minimum_headroom_cck": 128.0, "p95_cck": -128, "typical_median_cck": -16.5}, "render": null, "ui_construction_render": {"max_cck": -2712, "minimum_headroom_cck": 2712.0, "p95_cck": -2712, "typical_median_cck": -2544.0}, "update_including_render": {"max_cck": -2714, "minimum_headroom_cck": 2714.0, "p95_cck": -2714, "typical_median_cck": -72.5}}, "two-player-rally": {"dispatcher": {"max_cck": 1, "minimum_headroom_cck": -1.0, "p95_cck": 4, "typical_median_cck": -3.0}, "render": {"max_cck": 3, "minimum_headroom_cck": -3.0, "p95_cck": 0, "typical_median_cck": -1.0}, "ui_construction_render": null, "update_including_render": {"max_cck": 146, "minimum_headroom_cck": -146.0, "p95_cck": 42, "typical_median_cck": -15.5}}}, "runtime_memory_bytes": {"chip_free_bytes": -152, "chip_used_bytes": 152, "largest_chip_free_block_bytes": -176, "other_free_bytes": 0, "other_pool_bytes": 0, "other_used_bytes": 0}}}, "state": "historical reviewed baseline; master has no accepted metrics report", "static_bytes": {"bss_bytes": 14336, "code_bytes": 368, "data_bytes": -14560, "executable_bytes": -13300, "loaded_payload_bytes": 144}}

Refresh hook: after merging new fonts/celebration, run the affected native checks or `RUST_LOG=info python scripts/native_metrics.py --refresh --record`; never copy results from an unfinished branch.
