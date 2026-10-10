# Native resource and loading metrics

Completion: **complete**. Acceptance is separate from metric coverage.
Product SHA256: `0c9824cc42004496d51c19f8ca503b0100eaa604373a1b998252367fcec0588b`.
Identity excludes generated report files and Git report commits; timestamps are not freshness evidence.

| Executable | Code | Data | BSS | Loaded payload |
|---:|---:|---:|---:|---:|
| 216864 | 62352 | 112700 | 152492 | 327544 |

Asset bytes: {'graphics': 73588, 'audio': 9892, 'replay_loaded_bytes': 1110}. These overlap loaded hunks.

Executable-size budget/headroom: unmeasured (no cap configured); size is not RAM.

Timing uses elapsed emulated colour clocks, including chip-bus waits; host time is unavailable.
PAL display budget: 70,824 CCK (~19.97 ms). Simulation budget: ~59,191.14 CCK (~16.69 ms).
Typical = median; p95 = nearest rank. Frozen/absent phase values remain unmeasured.

UI construction is grouped by page (title = menu; help includes controls/credits), independently of callback-entry profiles; menu-page redraws can occur during pause/input transitions. Pause-only UI construction remains unmeasured.

Release ADF executable: 182404 bytes; symbol bytes removed: 34460. Development retains symbols.
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
| cpu_instructions | 30,960 |
| font | 1,024 |
| front_court_and_title_copper_lists | 648 |
| hunk_header_table | 40 |
| hunk_record_headers_and_ends | 60 |
| initial_hardware_sprites | 576 |
| menu_font_mac | 1,024 |
| mode_banks | 3,072 |
| other_initialized_tables_and_scalars | 1,704 |
| pre_rendered_demo_options | 512 |
| pre_rendered_help_options | 768 |
| pre_rendered_menu_options | 768 |
| pre_rendered_title_identities | 512 |
| pre_rendered_title_ui_pages | 29,696 |
| pre_rendered_ui_pages | 14,848 |
| relocation_offsets | 7,204 |
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
| symbol_name_padding | 1,711 |
| symbol_names | 22,893 |
| symbol_record_framing | 9,856 |
| title_bitplanes | 24,576 |
| ui_text_and_line_pointer_tables | 1,756 |
| **Exact file total** | **216,864** |

Mutually exclusive file-byte categories; code/data hunk sizes are a separate containing view, not added again. CPU instructions use actual emitted listing lengths, including operand extensions. Reserved dcb storage is file-backed, not HUNK_BSS. Zero debug means no emitted HUNK_DEBUG record; symbols are counted separately.
Byte-identical incbin payload bytes beyond first copies: 8,192 B. These remain included in the categories; aliasing safety is unproven.


| Case / profile | Samples | Update median / p95 / max ms | Sprite render / UI page construction max ms | Dispatcher max ms | Work / deadline headroom ms |
|---|---:|---:|---:|---:|---:|
| cold-one / title | 7 | 2.156 / 15.968 / 15.968 | unmeasured / 11.642 | 0.988 | 0.720 / 0.555 |
| cold-one / one-player-rally | 4292 | 5.864 / 6.163 / 8.368 | 1.672 / unmeasured | 4.537 | 8.320 / 8.112 |
| cold-one / two-player-rally | 1 | 5.852 / 5.852 / 5.852 | 1.484 / unmeasured | 1.973 | 10.836 / 10.750 |
| cold-one / match-end | 48 | 4.010 / 4.535 / 4.781 | 1.349 / unmeasured | 0.948 | 11.907 / 11.737 |
| cold-one / celebration | 887 | 3.867 / 4.304 / 6.555 | 1.052 / unmeasured | 1.370 | 10.133 / 10.056 |

cold-one: chip used 433,096 B; free 91,192 B; largest block 89,992 B; runtime peak 433096 B; cold initialized-pool peak 434384 B.
Deadlines/publications: `{'missed_native_callbacks': 0, 'missed_publications_counter': 0, 'publication_failures': 0}`. Allocation failures: unmeasured; pre-Exec bootstrap: unmeasured.

| Cold loading stage | Emulated seconds | Signed offset from previous listed milestone (ms) |
|---|---:|---:|
| reset | 0.000000 | unmeasured |
| boot_script_begins | unmeasured | unmeasured |
| loadseg_begin | unmeasured | unmeasured |
| loadseg_complete | 22.391803 | 22391.803 |
| executable_entry | 22.392809 | 1.006 |
| assets_ready | 22.417465 | 24.656 |
| first_complete_title_frame | 22.476764 | 59.299 |
| input_responsive | 22.504181 | 27.417 |

Total reset to successful input: 22504.181 ms; displayed title and input both ready: 22504.181 ms. Disk reads/seeks and host launch time: unavailable.
Emulated CCK only. LoadSeg catch is completion/entry, not start; file reads/relocation not independently separated. First complete title frame is a frame boundary after a full title-selected frame. Input-responsive point is successful normal selection after the existing first-callback input request; includes that workflow wait. Milestones may overlap: input can respond before a complete title frame. Listed-milestone differences are signed offsets, not invented sequential phase durations; boot complete requires both displayed title and successful input.


| Case / profile | Samples | Update median / p95 / max ms | Sprite render / UI page construction max ms | Dispatcher max ms | Work / deadline headroom ms |
|---|---:|---:|---:|---:|---:|
| two / title | 4 | 8.887 / 15.938 / 15.938 | unmeasured / 11.648 | 0.980 | 0.750 / 0.646 |
| two / two-player-rally | 9263 | 5.770 / 6.031 / 8.136 | 1.671 / unmeasured | 4.053 | 8.552 / 8.459 |
| two / match-end | 48 | 3.933 / 4.605 / 4.646 | 1.350 / unmeasured | 0.969 | 12.042 / 11.854 |
| two / celebration | 887 | 3.761 / 4.338 / 6.432 | 1.053 / unmeasured | 1.372 | 10.256 / 10.020 |

two: chip used 466,832 B; free 57,456 B; largest block 56,872 B; runtime peak 466832 B; cold initialized-pool peak unmeasured.
Deadlines/publications: `{'missed_native_callbacks': 0, 'missed_publications_counter': 0, 'publication_failures': 0}`. Allocation failures: unmeasured; pre-Exec bootstrap: unmeasured.


| Case / profile | Samples | Update median / p95 / max ms | Sprite render / UI page construction max ms | Dispatcher max ms | Work / deadline headroom ms |
|---|---:|---:|---:|---:|---:|
| setup / title | 1237 | 2.012 / 2.316 / 14.882 | unmeasured / 11.634 | 0.980 | 1.806 / 1.559 |
| setup / help | 575 | 2.150 / 2.312 / 14.559 | unmeasured / 11.787 | 0.468 | 2.129 / 1.888 |
| setup / one-player-rally | 32 | 5.728 / 6.101 / 6.256 | 1.633 / unmeasured | 2.074 | 10.432 / 10.310 |
| setup / pause | 88 | 1.761 / 2.131 / 5.960 | unmeasured / unmeasured | 0.162 | 10.728 / 10.597 |

setup deadlines/publications: `{'missed_publications_counter': 0, 'missed_named_profile_deadlines': 0, 'missed_native_callbacks': 0, 'scope': 'Setup raw checker covers all callbacks; demo deadline counts cover named measured profiles only, unprofiled transitions remain unmeasured.'}`.


| Case / profile | Samples | Update median / p95 / max ms | Sprite render / UI page construction max ms | Dispatcher max ms | Work / deadline headroom ms |
|---|---:|---:|---:|---:|---:|
| demo / title | 1800 | 2.012 / 2.294 / 14.587 | unmeasured / unmeasured | 0.988 | 2.101 / 1.841 |
| demo / demo | 11703 | 5.650 / 6.146 / 8.626 | 2.962 / unmeasured | 4.538 | 8.062 / 7.833 |

demo deadlines/publications: `{'missed_publications_counter': 0, 'missed_named_profile_deadlines': 0, 'missed_native_callbacks': None, 'scope': 'Setup raw checker covers all callbacks; demo deadline counts cover named measured profiles only, unprofiled transitions remain unmeasured.'}`.


Coverage: title: measured, help: measured, one-player-rally: measured, two-player-rally: measured, demo: measured, pause: measured, match-end: measured, celebration: measured

Deltas: {"previous_identity": "ea32fefef08509b2817ddc05827848878c2fcfe606d30284cb811fac71096884", "previous_report": "docs/metrics/baselines/pre-title-score-current.json", "previous_report_sha256": "3f201f2af4bf6bf03f50d2a9685442e57b61bb207d2ab024e62d931fb7dbdede", "runtime": {"cold-one": {"profiles": {"celebration": {"dispatcher": {"max_cck": 332, "minimum_headroom_cck": -332.0, "p95_cck": 542, "typical_median_cck": 476.0}, "render": {"max_cck": 475, "minimum_headroom_cck": -475.0, "p95_cck": 517, "typical_median_cck": 269.0}, "ui_construction_render": null, "update_including_render": {"max_cck": 2332, "minimum_headroom_cck": -2332.0, "p95_cck": 2774, "typical_median_cck": 2708.0}}, "demo": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "help": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "match-end": {"dispatcher": {"max_cck": 639, "minimum_headroom_cck": -639.0, "p95_cck": 730, "typical_median_cck": 462.0}, "render": {"max_cck": -862, "minimum_headroom_cck": 862.0, "p95_cck": -864, "typical_median_cck": -238.0}, "ui_construction_render": null, "update_including_render": {"max_cck": -3568, "minimum_headroom_cck": 3568.0, "p95_cck": 247, "typical_median_cck": 1006.0}}, "one-player-rally": {"dispatcher": {"max_cck": 1988, "minimum_headroom_cck": -1988.0, "p95_cck": -839, "typical_median_cck": -589.0}, "render": {"max_cck": 218, "minimum_headroom_cck": -218.0, "p95_cck": 130, "typical_median_cck": 289.0}, "ui_construction_render": null, "update_including_render": {"max_cck": 2134, "minimum_headroom_cck": -2134.0, "p95_cck": 153, "typical_median_cck": 608.5}}, "pause": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "title": {"dispatcher": {"max_cck": -938, "minimum_headroom_cck": 938.0, "p95_cck": -938, "typical_median_cck": 332.0}, "render": null, "ui_construction_render": {"max_cck": -3184, "minimum_headroom_cck": 3184.0, "p95_cck": -3184, "typical_median_cck": -3223.0}, "update_including_render": {"max_cck": 2162, "minimum_headroom_cck": -2162.0, "p95_cck": 2162, "typical_median_cck": -3033.0}}, "two-player-rally": {"dispatcher": {"max_cck": -1167, "minimum_headroom_cck": 1167.0, "p95_cck": -1167, "typical_median_cck": -1167.0}, "render": {"max_cck": 375, "minimum_headroom_cck": -375.0, "p95_cck": 375, "typical_median_cck": 375.0}, "ui_construction_render": null, "update_including_render": {"max_cck": 222, "minimum_headroom_cck": -222.0, "p95_cck": 222, "typical_median_cck": 222.0}}}, "reset_to_input_cck": -8390419, "runtime_memory_bytes": {"chip_free_bytes": -125464, "chip_used_bytes": 125464, "largest_chip_free_block_bytes": -125496, "other_free_bytes": 0, "other_pool_bytes": 0, "other_used_bytes": 0}}, "demo": {"profiles": {"celebration": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "demo": {"dispatcher": {"max_cck": 1931, "minimum_headroom_cck": -1931.0, "p95_cck": -851, "typical_median_cck": 293.0}, "render": {"max_cck": -13464, "minimum_headroom_cck": 13464.0, "p95_cck": 158, "typical_median_cck": 292.0}, "ui_construction_render": null, "update_including_render": {"max_cck": -6688, "minimum_headroom_cck": 6688.0, "p95_cck": 169, "typical_median_cck": 778.0}}, "help": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "match-end": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "one-player-rally": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "pause": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "title": {"dispatcher": {"max_cck": -2370, "minimum_headroom_cck": 2370.0, "p95_cck": 1393, "typical_median_cck": 331.0}, "render": null, "ui_construction_render": null, "update_including_render": {"max_cck": -2091, "minimum_headroom_cck": 2091.0, "p95_cck": 342, "typical_median_cck": -637.0}}, "two-player-rally": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}}}, "setup": {"profiles": {"celebration": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "demo": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "help": {"dispatcher": {"max_cck": -42720, "minimum_headroom_cck": 42720.0, "p95_cck": 1411, "typical_median_cck": 355.0}, "render": null, "ui_construction_render": {"max_cck": -2213, "minimum_headroom_cck": 2213.0, "p95_cck": -2213, "typical_median_cck": -2597.5}, "update_including_render": {"max_cck": -869, "minimum_headroom_cck": 869.0, "p95_cck": 426, "typical_median_cck": -121.0}}, "match-end": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "one-player-rally": {"dispatcher": {"max_cck": -1365, "minimum_headroom_cck": 1365.0, "p95_cck": -999, "typical_median_cck": -887.5}, "render": {"max_cck": 107, "minimum_headroom_cck": -107.0, "p95_cck": 121, "typical_median_cck": 280.5}, "ui_construction_render": null, "update_including_render": {"max_cck": -30, "minimum_headroom_cck": 30.0, "p95_cck": -66, "typical_median_cck": 357.0}}, "pause": {"dispatcher": {"max_cck": 330, "minimum_headroom_cck": -330.0, "p95_cck": 330, "typical_median_cck": 330.0}, "render": null, "ui_construction_render": null, "update_including_render": {"max_cck": -37183, "minimum_headroom_cck": 37183.0, "p95_cck": -624, "typical_median_cck": -1207.5}}, "title": {"dispatcher": {"max_cck": -42952, "minimum_headroom_cck": 42952.0, "p95_cck": 1406, "typical_median_cck": 331.0}, "render": null, "ui_construction_render": {"max_cck": -4558, "minimum_headroom_cck": 4558.0, "p95_cck": -4558, "typical_median_cck": -3091.0}, "update_including_render": {"max_cck": -1469, "minimum_headroom_cck": 1469.0, "p95_cck": 418, "typical_median_cck": -633.0}}, "two-player-rally": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}}}, "two": {"profiles": {"celebration": {"dispatcher": {"max_cck": 898, "minimum_headroom_cck": -898.0, "p95_cck": 545, "typical_median_cck": 479.0}, "render": {"max_cck": 478, "minimum_headroom_cck": -478.0, "p95_cck": 510, "typical_median_cck": 272.0}, "ui_construction_render": null, "update_including_render": {"max_cck": 1935, "minimum_headroom_cck": -1935.0, "p95_cck": 2890, "typical_median_cck": 2292.5}}, "demo": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "help": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "match-end": {"dispatcher": {"max_cck": 754, "minimum_headroom_cck": -754.0, "p95_cck": 683, "typical_median_cck": 481.0}, "render": {"max_cck": -15, "minimum_headroom_cck": 15.0, "p95_cck": 16, "typical_median_cck": 276.5}, "ui_construction_render": null, "update_including_render": {"max_cck": -4132, "minimum_headroom_cck": 4132.0, "p95_cck": 1915, "typical_median_cck": 1309.0}}, "one-player-rally": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "pause": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "title": {"dispatcher": {"max_cck": -960, "minimum_headroom_cck": 960.0, "p95_cck": -960, "typical_median_cck": 1750.5}, "render": null, "ui_construction_render": {"max_cck": -4676, "minimum_headroom_cck": 4676.0, "p95_cck": -4676, "typical_median_cck": -3692.0}, "update_including_render": {"max_cck": 911, "minimum_headroom_cck": -911.0, "p95_cck": 911, "typical_median_cck": 19146.5}}, "two-player-rally": {"dispatcher": {"max_cck": 1183, "minimum_headroom_cck": -1183.0, "p95_cck": -835, "typical_median_cck": -610.0}, "render": {"max_cck": 225, "minimum_headroom_cck": -225.0, "p95_cck": 183, "typical_median_cck": 292.0}, "ui_construction_render": null, "update_including_render": {"max_cck": 2589, "minimum_headroom_cck": -2589.0, "p95_cck": -191, "typical_median_cck": 447.5}}}, "runtime_memory_bytes": {"chip_free_bytes": -125464, "chip_used_bytes": 125464, "largest_chip_free_block_bytes": -125496, "other_free_bytes": 0, "other_pool_bytes": 0, "other_used_bytes": 0}}}, "state": "historical reviewed baseline; master has no accepted metrics report", "static_bytes": {"bss_bytes": 152492, "code_bytes": 12788, "data_bytes": -39840, "executable_bytes": -31616, "loaded_payload_bytes": 125440}}

Refresh hook: after merging new fonts/celebration, run the affected native checks or `RUST_LOG=info python scripts/native_metrics.py --refresh --record`; never copy results from an unfinished branch.
