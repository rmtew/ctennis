# Native resource and loading metrics

Completion: **complete**. Acceptance is separate from metric coverage.
Product SHA256: `1a5286650df54e65d4a3339557b1b54f5a0a7c398fcd552b3c7537e14d547e72`.
Identity excludes generated report files and Git report commits; timestamps are not freshness evidence.

| Executable | Code | Data | BSS | Loaded payload |
|---:|---:|---:|---:|---:|
| 240732 | 50892 | 141396 | 14336 | 206624 |

Asset bytes: {'graphics': 95092, 'audio': 9892, 'replay_loaded_bytes': 1110}. These overlap loaded hunks.

Executable-size budget/headroom: unmeasured (no cap configured); size is not RAM.

Timing uses elapsed emulated colour clocks, including chip-bus waits; host time is unavailable.
PAL display budget: 70,824 CCK (~19.97 ms). Simulation budget: ~59,191.14 CCK (~16.69 ms).
Typical = median; p95 = nearest rank. Frozen/absent phase values remain unmeasured.

UI construction is grouped by page (title = menu; help includes controls/credits), independently of callback-entry profiles; menu-page redraws can occur during pause/input transitions. Pause-only UI construction remains unmeasured.

Release ADF executable: 202276 bytes; symbol bytes removed: 38456. Development retains symbols.
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
| cpu_instructions | 12,904 |
| font | 1,024 |
| front_court_and_title_copper_lists | 3,216 |
| hunk_header_table | 32 |
| hunk_record_headers_and_ends | 36 |
| initial_hardware_sprites | 576 |
| menu_font_mac | 1,024 |
| mode_banks | 3,072 |
| other_initialized_tables_and_scalars | 817 |
| pre_rendered_demo_options | 512 |
| pre_rendered_help_options | 768 |
| pre_rendered_menu_options | 768 |
| pre_rendered_title_ui_pages | 29,696 |
| pre_rendered_ui_pages | 14,848 |
| relocation_offsets | 9,888 |
| relocation_record_framing | 32 |
| replay_packets | 1,110 |
| reserved_back_copper | 3,072 |
| reserved_back_sprites | 576 |
| reserved_native_stack | 4,096 |
| reserved_state_and_work_buffers | 968 |
| reserved_third_copper | 3,072 |
| reserved_third_sprites | 576 |
| reserved_ui_overlay | 512 |
| scene_animation_table | 36 |
| scene_pose_table | 112 |
| scene_robot_pose_table | 112 |
| scene_sprite_variants | 11,264 |
| score_game_banks | 21,504 |
| score_patch_pointer_tables | 8,008 |
| separate_debug_records | 0 |
| source_alignment_padding | 15 |
| square_led_construction_definitions | 48 |
| status_banks | 7,168 |
| symbol_name_padding | 1,593 |
| symbol_names | 25,135 |
| symbol_record_framing | 11,728 |
| title_bitplanes | 24,576 |
| ui_text_and_line_pointer_tables | 1,756 |
| **Exact file total** | **240,732** |

Mutually exclusive file-byte categories; code/data hunk sizes are a separate containing view, not added again. CPU instructions use actual emitted listing lengths, including operand extensions. Reserved dcb storage is file-backed, not HUNK_BSS. Zero debug means no emitted HUNK_DEBUG record; symbols are counted separately.
Byte-identical incbin payload bytes beyond first copies: 8,192 B. These remain included in the categories; aliasing safety is unproven.


| Case / profile | Samples | Update median / p95 / max ms | Sprite render / UI page construction max ms | Dispatcher max ms | Work / deadline headroom ms |
|---|---:|---:|---:|---:|---:|
| cold-one / title | 8 | 2.844 / 15.561 / 15.561 | unmeasured / 12.490 | 1.250 | 1.128 / 1.039 |
| cold-one / one-player-rally | 3507 | 6.129 / 6.483 / 7.990 | 1.612 / unmeasured | 3.954 | 8.699 / 8.546 |
| cold-one / two-player-rally | 1 | 6.382 / 6.382 / 6.382 | 1.410 / unmeasured | 2.453 | 10.306 / 10.173 |
| cold-one / match-end | 48 | 4.104 / 4.569 / 6.611 | 1.601 / unmeasured | 0.773 | 10.077 / 9.934 |
| cold-one / celebration | 887 | 3.492 / 3.907 / 6.280 | 0.976 / unmeasured | 1.119 | 10.408 / 9.861 |

cold-one: chip used 312,160 B; free 212,128 B; largest block 210,936 B; runtime peak 312160 B; cold initialized-pool peak 315248 B.
Deadlines/publications: `{'missed_native_callbacks': 0, 'missed_publications_counter': 0, 'publication_failures': 0}`. Allocation failures: unmeasured; pre-Exec bootstrap: unmeasured.

| Cold loading stage | Emulated seconds | Signed offset from previous listed milestone (ms) |
|---|---:|---:|
| reset | 0.000000 | unmeasured |
| boot_script_begins | unmeasured | unmeasured |
| loadseg_begin | unmeasured | unmeasured |
| loadseg_complete | 23.662798 | 23662.798 |
| executable_entry | 23.663799 | 1.001 |
| assets_ready | 23.751637 | 87.838 |
| first_complete_title_frame | 23.800892 | 49.255 |
| input_responsive | 23.822045 | 21.153 |

Total reset to successful input: 23822.045 ms; displayed title and input both ready: 23822.045 ms. Disk reads/seeks and host launch time: unavailable.
Emulated CCK only. LoadSeg catch is completion/entry, not start; file reads/relocation not independently separated. First complete title frame is a frame boundary after a full title-selected frame. Input-responsive point is successful normal selection after the existing first-callback input request; includes that workflow wait. Milestones may overlap: input can respond before a complete title frame. Listed-milestone differences are signed offsets, not invented sequential phase durations; boot complete requires both displayed title and successful input.


| Case / profile | Samples | Update median / p95 / max ms | Sprite render / UI page construction max ms | Dispatcher max ms | Work / deadline headroom ms |
|---|---:|---:|---:|---:|---:|
| two / title | 6 | 3.544 / 15.182 / 15.182 | unmeasured / 11.977 | 1.254 | 1.506 / 1.346 |
| two / one-player-rally | 1 | 6.081 / 6.081 / 6.081 | 1.572 / unmeasured | 2.015 | 10.607 / 10.525 |
| two / two-player-rally | 9262 | 6.076 / 6.441 / 7.764 | 1.613 / unmeasured | 3.761 | 8.924 / 8.726 |
| two / match-end | 48 | 4.013 / 4.642 / 6.179 | 1.458 / unmeasured | 0.775 | 10.509 / 10.297 |
| two / celebration | 887 | 3.490 / 3.890 / 6.304 | 0.972 / unmeasured | 1.288 | 10.384 / 9.838 |

two: chip used 345,896 B; free 178,392 B; largest block 177,816 B; runtime peak 345896 B; cold initialized-pool peak unmeasured.
Deadlines/publications: `{'missed_native_callbacks': 0, 'missed_publications_counter': 0, 'publication_failures': 0}`. Allocation failures: unmeasured; pre-Exec bootstrap: unmeasured.


| Case / profile | Samples | Update median / p95 / max ms | Sprite render / UI page construction max ms | Dispatcher max ms | Work / deadline headroom ms |
|---|---:|---:|---:|---:|---:|
| setup / title | 1233 | 2.200 / 2.252 / 15.240 | unmeasured / 12.501 | 13.009 | 1.448 / 1.206 |
| setup / help | 575 | 2.193 / 2.259 / 15.275 | unmeasured / 12.540 | 12.974 | 1.413 / 1.204 |
| setup / one-player-rally | 31 | 6.072 / 6.470 / 6.604 | 1.601 / unmeasured | 2.504 | 10.084 / 9.992 |
| setup / pause | 88 | 2.135 / 2.386 / 16.387 | unmeasured / unmeasured | 0.067 | 0.301 / 0.223 |

setup deadlines/publications: `{'missed_publications_counter': 0, 'missed_named_profile_deadlines': 0, 'missed_native_callbacks': 0, 'scope': 'Setup raw checker covers all callbacks; demo deadline counts cover named measured profiles only, unprofiled transitions remain unmeasured.'}`.


| Case / profile | Samples | Update median / p95 / max ms | Sprite render / UI page construction max ms | Dispatcher max ms | Work / deadline headroom ms |
|---|---:|---:|---:|---:|---:|
| demo / title | 1800 | 2.200 / 2.253 / 15.040 | unmeasured / unmeasured | 1.706 | 1.648 / 1.403 |
| demo / demo | 11703 | 5.794 / 6.466 / 14.917 | 6.372 / unmeasured | 3.955 | 1.771 / 1.685 |

demo deadlines/publications: `{'missed_publications_counter': 0, 'missed_named_profile_deadlines': 0, 'missed_native_callbacks': None, 'scope': 'Setup raw checker covers all callbacks; demo deadline counts cover named measured profiles only, unprofiled transitions remain unmeasured.'}`.


Coverage: title: measured, help: measured, one-player-rally: measured, two-player-rally: measured, demo: measured, pause: measured, match-end: measured, celebration: measured

Deltas: {"previous_identity": "ea32fefef08509b2817ddc05827848878c2fcfe606d30284cb811fac71096884", "previous_report": "docs/metrics/baselines/pre-title-score-current.json", "previous_report_sha256": "3f201f2af4bf6bf03f50d2a9685442e57b61bb207d2ab024e62d931fb7dbdede", "runtime": {"cold-one": {"profiles": {"celebration": {"dispatcher": {"max_cck": -558, "minimum_headroom_cck": 558.0, "p95_cck": -3, "typical_median_cck": 2.0}, "render": {"max_cck": 207, "minimum_headroom_cck": -207.0, "p95_cck": 113, "typical_median_cck": 20.0}, "ui_construction_render": null, "update_including_render": {"max_cck": 1357, "minimum_headroom_cck": -1357.0, "p95_cck": 1364, "typical_median_cck": 1378.0}}, "demo": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "help": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "match-end": {"dispatcher": {"max_cck": 21, "minimum_headroom_cck": -21.0, "p95_cck": 2, "typical_median_cck": -11.0}, "render": {"max_cck": 30, "minimum_headroom_cck": -30.0, "p95_cck": 16, "typical_median_cck": 160.5}, "ui_construction_render": null, "update_including_render": {"max_cck": 2923, "minimum_headroom_cck": -2923.0, "p95_cck": 369, "typical_median_cck": 1340.0}}, "one-player-rally": {"dispatcher": {"max_cck": -78, "minimum_headroom_cck": 78.0, "p95_cck": 30, "typical_median_cck": 70.0}, "render": {"max_cck": 5, "minimum_headroom_cck": -5.0, "p95_cck": -36, "typical_median_cck": 32.0}, "ui_construction_render": null, "update_including_render": {"max_cck": 791, "minimum_headroom_cck": -791.0, "p95_cck": 1289, "typical_median_cck": 1548.0}}, "pause": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "title": {"dispatcher": {"max_cck": -9, "minimum_headroom_cck": 9.0, "p95_cck": -9, "typical_median_cck": -1.0}, "render": null, "ui_construction_render": {"max_cck": -178, "minimum_headroom_cck": 178.0, "p95_cck": -178, "typical_median_cck": -1151.5}, "update_including_render": {"max_cck": 716, "minimum_headroom_cck": -716.0, "p95_cck": 716, "typical_median_cck": -592.0}}, "two-player-rally": {"dispatcher": {"max_cck": 534, "minimum_headroom_cck": -534.0, "p95_cck": 534, "typical_median_cck": 534.0}, "render": {"max_cck": 114, "minimum_headroom_cck": -114.0, "p95_cck": 114, "typical_median_cck": 114.0}, "ui_construction_render": null, "update_including_render": {"max_cck": 2102, "minimum_headroom_cck": -2102.0, "p95_cck": 2102, "typical_median_cck": 2102.0}}}, "reset_to_input_cck": -3716093, "runtime_memory_bytes": {"chip_free_bytes": -4528, "chip_used_bytes": 4528, "largest_chip_free_block_bytes": -4552, "other_free_bytes": 0, "other_pool_bytes": 0, "other_used_bytes": 0}}, "demo": {"profiles": {"celebration": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "demo": {"dispatcher": {"max_cck": -136, "minimum_headroom_cck": 136.0, "p95_cck": 91, "typical_median_cck": 99.0}, "render": {"max_cck": -1369, "minimum_headroom_cck": 1369.0, "p95_cck": 5, "typical_median_cck": 32.0}, "ui_construction_render": null, "update_including_render": {"max_cck": 15624, "minimum_headroom_cck": -15624.0, "p95_cck": 1304, "typical_median_cck": 1289.0}}, "help": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "match-end": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "one-player-rally": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "pause": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "title": {"dispatcher": {"max_cck": 175, "minimum_headroom_cck": -175.0, "p95_cck": 0, "typical_median_cck": 0.0}, "render": null, "ui_construction_render": null, "update_including_render": {"max_cck": -486, "minimum_headroom_cck": 486.0, "p95_cck": 196, "typical_median_cck": 32.0}}, "two-player-rally": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}}}, "setup": {"profiles": {"celebration": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "demo": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "help": {"dispatcher": {"max_cck": 1639, "minimum_headroom_cck": -1639.0, "p95_cck": 1, "typical_median_cck": 0.0}, "render": null, "ui_construction_render": {"max_cck": 457, "minimum_headroom_cck": -457.0, "p95_cck": 457, "typical_median_cck": 473.0}, "update_including_render": {"max_cck": 1668, "minimum_headroom_cck": -1668.0, "p95_cck": 239, "typical_median_cck": 32.0}}, "match-end": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "one-player-rally": {"dispatcher": {"max_cck": 158, "minimum_headroom_cck": -158.0, "p95_cck": 106, "typical_median_cck": 70.5}, "render": {"max_cck": -9, "minimum_headroom_cck": 9.0, "p95_cck": -13, "typical_median_cck": 59.5}, "ui_construction_render": null, "update_including_render": {"max_cck": 1205, "minimum_headroom_cck": -1205.0, "p95_cck": 1243, "typical_median_cck": 1575.0}}, "pause": {"dispatcher": {"max_cck": -6, "minimum_headroom_cck": 6.0, "p95_cck": -6, "typical_median_cck": -6.0}, "render": null, "ui_construction_render": null, "update_including_render": {"max_cck": -201, "minimum_headroom_cck": 201.0, "p95_cck": 280, "typical_median_cck": 120.0}}, "title": {"dispatcher": {"max_cck": -285, "minimum_headroom_cck": 285.0, "p95_cck": 0, "typical_median_cck": 0.0}, "render": null, "ui_construction_render": {"max_cck": -1482, "minimum_headroom_cck": 1482.0, "p95_cck": -1482, "typical_median_cck": -1569.0}, "update_including_render": {"max_cck": -201, "minimum_headroom_cck": 201.0, "p95_cck": 193, "typical_median_cck": 34.0}}, "two-player-rally": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}}}, "two": {"profiles": {"celebration": {"dispatcher": {"max_cck": 600, "minimum_headroom_cck": -600.0, "p95_cck": -2, "typical_median_cck": 2.0}, "render": {"max_cck": 191, "minimum_headroom_cck": -191.0, "p95_cck": 88, "typical_median_cck": 20.0}, "ui_construction_render": null, "update_including_render": {"max_cck": 1480, "minimum_headroom_cck": -1480.0, "p95_cck": 1300, "typical_median_cck": 1331.5}}, "demo": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "help": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "match-end": {"dispatcher": {"max_cck": 67, "minimum_headroom_cck": -67.0, "p95_cck": 21, "typical_median_cck": 26.5}, "render": {"max_cck": 369, "minimum_headroom_cck": -369.0, "p95_cck": 380, "typical_median_cck": 18.5}, "ui_construction_render": null, "update_including_render": {"max_cck": 1304, "minimum_headroom_cck": -1304.0, "p95_cck": 2044, "typical_median_cck": 1594.5}}, "one-player-rally": {"dispatcher": {"max_cck": -595, "minimum_headroom_cck": 595.0, "p95_cck": -595, "typical_median_cck": -595.0}, "render": {"max_cck": 491, "minimum_headroom_cck": -491.0, "p95_cck": 491, "typical_median_cck": 491.0}, "ui_construction_render": null, "update_including_render": {"max_cck": 1163, "minimum_headroom_cck": -1163.0, "p95_cck": 1163, "typical_median_cck": 1163.0}}, "pause": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "title": {"dispatcher": {"max_cck": 11, "minimum_headroom_cck": -11.0, "p95_cck": 11, "typical_median_cck": 9.5}, "render": null, "ui_construction_render": {"max_cck": -3509, "minimum_headroom_cck": 3509.0, "p95_cck": -3509, "typical_median_cck": -2712.5}, "update_including_render": {"max_cck": -1771, "minimum_headroom_cck": 1771.0, "p95_cck": -1771, "typical_median_cck": 196.5}}, "two-player-rally": {"dispatcher": {"max_cck": 149, "minimum_headroom_cck": -149.0, "p95_cck": 26, "typical_median_cck": 55.0}, "render": {"max_cck": 21, "minimum_headroom_cck": -21.0, "p95_cck": 20, "typical_median_cck": 38.0}, "ui_construction_render": null, "update_including_render": {"max_cck": 1270, "minimum_headroom_cck": -1270.0, "p95_cck": 1266, "typical_median_cck": 1533.0}}}, "runtime_memory_bytes": {"chip_free_bytes": -4528, "chip_used_bytes": 4528, "largest_chip_free_block_bytes": -4552, "other_free_bytes": 0, "other_pool_bytes": 0, "other_used_bytes": 0}}}, "state": "historical reviewed baseline; master has no accepted metrics report", "static_bytes": {"bss_bytes": 14336, "code_bytes": 1328, "data_bytes": -11144, "executable_bytes": -7748, "loaded_payload_bytes": 4520}}

Refresh hook: after merging new fonts/celebration, run the affected native checks or `RUST_LOG=info python scripts/native_metrics.py --refresh --record`; never copy results from an unfinished branch.
