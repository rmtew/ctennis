# Native resource and loading metrics

Completion: **complete**. Acceptance is separate from metric coverage.
Product SHA256: `49de1fc1b4f9c1ad65d932e2453e7eb47b4b2cb216ab05dbb0c3d699fe37b6ad`.
Identity excludes generated report files and Git report commits; timestamps are not freshness evidence.

| Executable | Code | Data | BSS | Loaded payload |
|---:|---:|---:|---:|---:|
| 219312 | 63464 | 112700 | 152788 | 328952 |

Asset bytes: {'graphics': 73588, 'audio': 9892, 'replay_loaded_bytes': 1110}. These overlap loaded hunks.

Executable-size budget/headroom: unmeasured (no cap configured); size is not RAM.

Timing uses elapsed emulated colour clocks, including chip-bus waits; host time is unavailable.
PAL display budget: 70,824 CCK (~19.97 ms). Simulation budget: ~59,191.14 CCK (~16.69 ms).
Typical = median; p95 = nearest rank. Frozen/absent phase values remain unmeasured.

UI construction is grouped by page (title = menu; help includes controls/credits), independently of callback-entry profiles; menu-page redraws can occur during pause/input transitions. Pause-only UI construction remains unmeasured.

Release ADF executable: 183816 bytes; symbol bytes removed: 35496. Development retains symbols.
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
| cpu_instructions | 32,032 |
| font | 1,024 |
| front_court_and_title_copper_lists | 648 |
| hunk_header_table | 40 |
| hunk_record_headers_and_ends | 60 |
| initial_hardware_sprites | 576 |
| menu_font_mac | 1,024 |
| mode_banks | 3,072 |
| other_initialized_tables_and_scalars | 1,744 |
| pre_rendered_demo_options | 512 |
| pre_rendered_help_options | 768 |
| pre_rendered_menu_options | 768 |
| pre_rendered_title_identities | 512 |
| pre_rendered_title_ui_pages | 29,696 |
| pre_rendered_ui_pages | 14,848 |
| relocation_offsets | 7,504 |
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
| symbol_name_padding | 1,734 |
| symbol_names | 23,690 |
| symbol_record_framing | 10,072 |
| title_bitplanes | 24,576 |
| ui_text_and_line_pointer_tables | 1,756 |
| **Exact file total** | **219,312** |

Mutually exclusive file-byte categories; code/data hunk sizes are a separate containing view, not added again. CPU instructions use actual emitted listing lengths, including operand extensions. Reserved dcb storage is file-backed, not HUNK_BSS. Zero debug means no emitted HUNK_DEBUG record; symbols are counted separately.
Byte-identical incbin payload bytes beyond first copies: 8,192 B. These remain included in the categories; aliasing safety is unproven.


| Case / profile | Samples | Update median / p95 / max ms | Sprite render / UI page construction max ms | Dispatcher max ms | Work / deadline headroom ms |
|---|---:|---:|---:|---:|---:|
| cold-one / title | 8 | 2.013 / 15.785 / 15.785 | unmeasured / 11.706 | 1.080 | 0.903 / 0.716 |
| cold-one / one-player-rally | 4873 | 5.876 / 6.185 / 8.474 | 1.670 / unmeasured | 4.610 | 8.215 / 8.080 |
| cold-one / two-player-rally | 1 | 5.737 / 5.737 / 5.737 | 1.444 / unmeasured | 1.946 | 10.951 / 10.692 |
| cold-one / match-end | 48 | 4.015 / 4.446 / 5.205 | 1.351 / unmeasured | 0.965 | 11.483 / 11.220 |
| cold-one / celebration | 888 | 3.828 / 4.349 / 6.565 | 1.054 / unmeasured | 1.372 | 10.124 / 9.853 |

cold-one: chip used 434,504 B; free 89,784 B; largest block 88,584 B; runtime peak 434504 B; cold initialized-pool peak 436048 B.
Deadlines/publications: `{'missed_native_callbacks': 0, 'missed_publications_counter': 0, 'publication_failures': 0}`. Allocation failures: unmeasured; pre-Exec bootstrap: unmeasured.

| Cold loading stage | Emulated seconds | Signed offset from previous listed milestone (ms) |
|---|---:|---:|
| reset | 0.000000 | unmeasured |
| boot_script_begins | unmeasured | unmeasured |
| loadseg_begin | unmeasured | unmeasured |
| loadseg_complete | 22.443461 | 22443.461 |
| executable_entry | 22.444464 | 1.003 |
| assets_ready | 22.469177 | 24.714 |
| first_complete_title_frame | 22.522650 | 53.473 |
| input_responsive | 22.572773 | 50.123 |

Total reset to successful input: 22572.773 ms; displayed title and input both ready: 22572.773 ms. Disk reads/seeks and host launch time: unavailable.
Emulated CCK only. LoadSeg catch is completion/entry, not start; file reads/relocation not independently separated. First complete title frame is a frame boundary after a full title-selected frame. Input-responsive point is successful normal selection after the existing first-callback input request; includes that workflow wait. Milestones may overlap: input can respond before a complete title frame. Listed-milestone differences are signed offsets, not invented sequential phase durations; boot complete requires both displayed title and successful input.


| Case / profile | Samples | Update median / p95 / max ms | Sprite render / UI page construction max ms | Dispatcher max ms | Work / deadline headroom ms |
|---|---:|---:|---:|---:|---:|
| two / title | 4 | 8.889 / 15.819 / 15.819 | unmeasured / 11.636 | 0.988 | 0.870 / 0.696 |
| two / two-player-rally | 9263 | 5.771 / 6.034 / 8.266 | 1.675 / unmeasured | 4.129 | 8.423 / 8.298 |
| two / match-end | 48 | 3.941 / 4.485 / 4.655 | 1.351 / unmeasured | 0.970 | 12.033 / 11.926 |
| two / celebration | 888 | 3.777 / 4.254 / 6.328 | 1.057 / unmeasured | 1.369 | 10.360 / 10.281 |

two: chip used 468,240 B; free 56,048 B; largest block 55,464 B; runtime peak 468240 B; cold initialized-pool peak unmeasured.
Deadlines/publications: `{'missed_native_callbacks': 0, 'missed_publications_counter': 0, 'publication_failures': 0}`. Allocation failures: unmeasured; pre-Exec bootstrap: unmeasured.


| Case / profile | Samples | Update median / p95 / max ms | Sprite render / UI page construction max ms | Dispatcher max ms | Work / deadline headroom ms |
|---|---:|---:|---:|---:|---:|
| setup / title | 1237 | 2.012 / 2.317 / 14.871 | unmeasured / 11.632 | 1.080 | 1.817 / 1.579 |
| setup / help | 575 | 2.150 / 2.395 / 14.538 | unmeasured / 11.763 | 0.572 | 2.151 / 1.923 |
| setup / one-player-rally | 32 | 5.730 / 6.124 / 6.225 | 1.658 / unmeasured | 2.067 | 10.463 / 10.296 |
| setup / pause | 88 | 1.759 / 2.127 / 5.935 | unmeasured / unmeasured | 0.162 | 10.753 / 10.567 |

setup deadlines/publications: `{'missed_publications_counter': 0, 'missed_named_profile_deadlines': 0, 'missed_native_callbacks': 0, 'scope': 'Setup raw checker covers all callbacks; demo deadline counts cover named measured profiles only, unprofiled transitions remain unmeasured.'}`.


| Case / profile | Samples | Update median / p95 / max ms | Sprite render / UI page construction max ms | Dispatcher max ms | Work / deadline headroom ms |
|---|---:|---:|---:|---:|---:|
| demo / title | 1800 | 2.012 / 2.295 / 14.596 | unmeasured / unmeasured | 0.989 | 2.092 / 1.832 |
| demo / demo | 11703 | 5.653 / 6.149 / 8.624 | 2.967 / unmeasured | 4.672 | 8.064 / 7.842 |

demo deadlines/publications: `{'missed_publications_counter': 0, 'missed_named_profile_deadlines': 0, 'missed_native_callbacks': None, 'scope': 'Setup raw checker covers all callbacks; demo deadline counts cover named measured profiles only, unprofiled transitions remain unmeasured.'}`.


Coverage: title: measured, help: measured, one-player-rally: measured, two-player-rally: measured, demo: measured, pause: measured, match-end: measured, celebration: measured

Deltas: {"previous_identity": "ea32fefef08509b2817ddc05827848878c2fcfe606d30284cb811fac71096884", "previous_report": "docs/metrics/baselines/pre-title-score-current.json", "previous_report_sha256": "3f201f2af4bf6bf03f50d2a9685442e57b61bb207d2ab024e62d931fb7dbdede", "runtime": {"cold-one": {"profiles": {"celebration": {"dispatcher": {"max_cck": 339, "minimum_headroom_cck": -339.0, "p95_cck": 539, "typical_median_cck": 476.0}, "render": {"max_cck": 483, "minimum_headroom_cck": -483.0, "p95_cck": 511, "typical_median_cck": 269.0}, "ui_construction_render": null, "update_including_render": {"max_cck": 2367, "minimum_headroom_cck": -2367.0, "p95_cck": 2933, "typical_median_cck": 2570.5}}, "demo": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "help": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "match-end": {"dispatcher": {"max_cck": 702, "minimum_headroom_cck": -702.0, "p95_cck": 672, "typical_median_cck": 457.0}, "render": {"max_cck": -856, "minimum_headroom_cck": 856.0, "p95_cck": -863, "typical_median_cck": -239.0}, "ui_construction_render": null, "update_including_render": {"max_cck": -2064, "minimum_headroom_cck": 2064.0, "p95_cck": -67, "typical_median_cck": 1026.0}}, "one-player-rally": {"dispatcher": {"max_cck": 2248, "minimum_headroom_cck": -2248.0, "p95_cck": -823, "typical_median_cck": -569.0}, "render": {"max_cck": 213, "minimum_headroom_cck": -213.0, "p95_cck": 132, "typical_median_cck": 288.0}, "ui_construction_render": null, "update_including_render": {"max_cck": 2508, "minimum_headroom_cck": -2508.0, "p95_cck": 232, "typical_median_cck": 652.0}}, "pause": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "title": {"dispatcher": {"max_cck": -613, "minimum_headroom_cck": 613.0, "p95_cck": -613, "typical_median_cck": 330.5}, "render": null, "ui_construction_render": {"max_cck": -2958, "minimum_headroom_cck": 2958.0, "p95_cck": -2958, "typical_median_cck": -2940.0}, "update_including_render": {"max_cck": 1512, "minimum_headroom_cck": -1512.0, "p95_cck": 1512, "typical_median_cck": -3538.0}}, "two-player-rally": {"dispatcher": {"max_cck": -1265, "minimum_headroom_cck": 1265.0, "p95_cck": -1265, "typical_median_cck": -1265.0}, "render": {"max_cck": 232, "minimum_headroom_cck": -232.0, "p95_cck": 232, "typical_median_cck": 232.0}, "ui_construction_render": null, "update_including_render": {"max_cck": -188, "minimum_headroom_cck": 188.0, "p95_cck": -188, "typical_median_cck": -188.0}}}, "reset_to_input_cck": -8147130, "runtime_memory_bytes": {"chip_free_bytes": -126872, "chip_used_bytes": 126872, "largest_chip_free_block_bytes": -126904, "other_free_bytes": 0, "other_pool_bytes": 0, "other_used_bytes": 0}}, "demo": {"profiles": {"celebration": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "demo": {"dispatcher": {"max_cck": 2406, "minimum_headroom_cck": -2406.0, "p95_cck": -846, "typical_median_cck": 296.0}, "render": {"max_cck": -13447, "minimum_headroom_cck": 13447.0, "p95_cck": 150, "typical_median_cck": 291.0}, "ui_construction_render": null, "update_including_render": {"max_cck": -6696, "minimum_headroom_cck": 6696.0, "p95_cck": 180, "typical_median_cck": 788.0}}, "help": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "match-end": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "one-player-rally": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "pause": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "title": {"dispatcher": {"max_cck": -2368, "minimum_headroom_cck": 2368.0, "p95_cck": 1400, "typical_median_cck": 331.0}, "render": null, "ui_construction_render": null, "update_including_render": {"max_cck": -2059, "minimum_headroom_cck": 2059.0, "p95_cck": 347, "typical_median_cck": -637.0}}, "two-player-rally": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}}}, "setup": {"profiles": {"celebration": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "demo": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "help": {"dispatcher": {"max_cck": -42350, "minimum_headroom_cck": 42350.0, "p95_cck": 1411, "typical_median_cck": 355.0}, "render": null, "ui_construction_render": {"max_cck": -2299, "minimum_headroom_cck": 2299.0, "p95_cck": -2299, "typical_median_cck": -2599.0}, "update_including_render": {"max_cck": -947, "minimum_headroom_cck": 947.0, "p95_cck": 721, "typical_median_cck": -120.0}}, "match-end": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "one-player-rally": {"dispatcher": {"max_cck": -1390, "minimum_headroom_cck": 1390.0, "p95_cck": -1031, "typical_median_cck": -861.5}, "render": {"max_cck": 194, "minimum_headroom_cck": -194.0, "p95_cck": -392, "typical_median_cck": 283.5}, "ui_construction_render": null, "update_including_render": {"max_cck": -139, "minimum_headroom_cck": 139.0, "p95_cck": 18, "typical_median_cck": 364.5}}, "pause": {"dispatcher": {"max_cck": 329, "minimum_headroom_cck": -329.0, "p95_cck": 329, "typical_median_cck": 329.0}, "render": null, "ui_construction_render": null, "update_including_render": {"max_cck": -37272, "minimum_headroom_cck": 37272.0, "p95_cck": -640, "typical_median_cck": -1213.0}}, "title": {"dispatcher": {"max_cck": -42598, "minimum_headroom_cck": 42598.0, "p95_cck": 1407, "typical_median_cck": 331.0}, "render": null, "ui_construction_render": {"max_cck": -4565, "minimum_headroom_cck": 4565.0, "p95_cck": -4565, "typical_median_cck": -3056.0}, "update_including_render": {"max_cck": -1509, "minimum_headroom_cck": 1509.0, "p95_cck": 424, "typical_median_cck": -633.0}}, "two-player-rally": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}}}, "two": {"profiles": {"celebration": {"dispatcher": {"max_cck": 890, "minimum_headroom_cck": -890.0, "p95_cck": 547, "typical_median_cck": 480.0}, "render": {"max_cck": 492, "minimum_headroom_cck": -492.0, "p95_cck": 502, "typical_median_cck": 271.0}, "ui_construction_render": null, "update_including_render": {"max_cck": 1565, "minimum_headroom_cck": -1565.0, "p95_cck": 2590, "typical_median_cck": 2347.5}}, "demo": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "help": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "match-end": {"dispatcher": {"max_cck": 759, "minimum_headroom_cck": -759.0, "p95_cck": 753, "typical_median_cck": 484.0}, "render": {"max_cck": -11, "minimum_headroom_cck": 11.0, "p95_cck": 12, "typical_median_cck": 271.0}, "ui_construction_render": null, "update_including_render": {"max_cck": -4101, "minimum_headroom_cck": 4101.0, "p95_cck": 1488, "typical_median_cck": 1338.5}}, "one-player-rally": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "pause": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "title": {"dispatcher": {"max_cck": -931, "minimum_headroom_cck": 931.0, "p95_cck": -931, "typical_median_cck": 1768.5}, "render": null, "ui_construction_render": {"max_cck": -4718, "minimum_headroom_cck": 4718.0, "p95_cck": -4718, "typical_median_cck": -3818.0}, "update_including_render": {"max_cck": 486, "minimum_headroom_cck": -486.0, "p95_cck": 486, "typical_median_cck": 19156.5}}, "two-player-rally": {"dispatcher": {"max_cck": 1455, "minimum_headroom_cck": -1455.0, "p95_cck": -842, "typical_median_cck": -611.0}, "render": {"max_cck": 239, "minimum_headroom_cck": -239.0, "p95_cck": 179, "typical_median_cck": 293.0}, "ui_construction_render": null, "update_including_render": {"max_cck": 3049, "minimum_headroom_cck": -3049.0, "p95_cck": -179, "typical_median_cck": 451.5}}}, "runtime_memory_bytes": {"chip_free_bytes": -126872, "chip_used_bytes": 126872, "largest_chip_free_block_bytes": -126904, "other_free_bytes": 0, "other_pool_bytes": 0, "other_used_bytes": 0}}}, "state": "historical reviewed baseline; master has no accepted metrics report", "static_bytes": {"bss_bytes": 152788, "code_bytes": 13900, "data_bytes": -39840, "executable_bytes": -29168, "loaded_payload_bytes": 126848}}

Refresh hook: after merging new fonts/celebration, run the affected native checks or `RUST_LOG=info python scripts/native_metrics.py --refresh --record`; never copy results from an unfinished branch.
