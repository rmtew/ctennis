# Native resource and loading metrics

Completion: **complete**. Acceptance is separate from metric coverage.
Product SHA256: `82225743796c9e35476daa71fc291e03dc4a62c07473113361352ca2848d7e6f`.
Identity excludes generated report files and Git report commits; timestamps are not freshness evidence.

| Executable | Code | Data | BSS | Loaded payload |
|---:|---:|---:|---:|---:|
| 181480 | 44264 | 112700 | 9424 | 166388 |

Asset bytes: {'graphics': 73588, 'audio': 9892, 'replay_loaded_bytes': 1110}. These overlap loaded hunks.

Executable-size budget/headroom: unmeasured (no cap configured); size is not RAM.

Timing uses elapsed emulated colour clocks, including chip-bus waits; host time is unavailable.
PAL display budget: 70,824 CCK (~19.97 ms). Simulation budget: ~59,191.14 CCK (~16.69 ms).
Typical = median; p95 = nearest rank. Frozen/absent phase values remain unmeasured.

UI construction is grouped by page (title = menu; help includes controls/credits), independently of callback-entry profiles; menu-page redraws can occur during pause/input transitions. Pause-only UI construction remains unmeasured.

Release ADF executable: 160072 bytes; symbol bytes removed: 21408. Development retains symbols.
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
| cpu_instructions | 13,780 |
| font | 1,024 |
| front_court_and_title_copper_lists | 648 |
| hunk_header_table | 32 |
| hunk_payload_alignment_padding | 2 |
| hunk_record_headers_and_ends | 36 |
| initial_hardware_sprites | 576 |
| menu_font_mac | 1,024 |
| mode_banks | 3,072 |
| other_initialized_tables_and_scalars | 796 |
| pre_rendered_demo_options | 512 |
| pre_rendered_help_options | 768 |
| pre_rendered_menu_options | 768 |
| pre_rendered_title_identities | 512 |
| pre_rendered_title_ui_pages | 29,696 |
| pre_rendered_ui_pages | 14,848 |
| relocation_offsets | 3,008 |
| relocation_record_framing | 32 |
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
| source_alignment_padding | 12 |
| square_led_construction_definitions | 48 |
| status_banks | 7,168 |
| symbol_name_padding | 1,116 |
| symbol_names | 13,692 |
| symbol_record_framing | 6,600 |
| title_bitplanes | 24,576 |
| ui_text_and_line_pointer_tables | 1,756 |
| **Exact file total** | **181,480** |

Mutually exclusive file-byte categories; code/data hunk sizes are a separate containing view, not added again. CPU instructions use actual emitted listing lengths, including operand extensions. Reserved dcb storage is file-backed, not HUNK_BSS. Zero debug means no emitted HUNK_DEBUG record; symbols are counted separately.
Byte-identical incbin payload bytes beyond first copies: 8,192 B. These remain included in the categories; aliasing safety is unproven.


| Case / profile | Samples | Update median / p95 / max ms | Sprite render / UI page construction max ms | Dispatcher max ms | Work / deadline headroom ms |
|---|---:|---:|---:|---:|---:|
| cold-one / title | 9 | 2.353 / 16.010 / 16.010 | unmeasured / 11.668 | 1.230 | 0.678 / 0.570 |
| cold-one / one-player-rally | 3756 | 6.150 / 6.339 / 7.859 | 1.595 / unmeasured | 3.806 | 8.829 / 8.705 |
| cold-one / two-player-rally | 1 | 6.444 / 6.444 / 6.444 | 1.570 / unmeasured | 2.223 | 10.244 / 10.162 |
| cold-one / match-end | 48 | 4.216 / 4.608 / 4.815 | 1.586 / unmeasured | 0.785 | 11.873 / 11.694 |
| cold-one / celebration | 888 | 3.873 / 4.272 / 6.696 | 0.980 / unmeasured | 1.135 | 9.992 / 9.896 |

cold-one: chip used 271,920 B; free 252,368 B; largest block 251,176 B; runtime peak 271920 B; cold initialized-pool peak 271920 B.
Deadlines/publications: `{'missed_native_callbacks': 0, 'missed_publications_counter': 0, 'publication_failures': 0}`. Allocation failures: unmeasured; pre-Exec bootstrap: unmeasured.

| Cold loading stage | Emulated seconds | Signed offset from previous listed milestone (ms) |
|---|---:|---:|
| reset | 0.000000 | unmeasured |
| boot_script_begins | unmeasured | unmeasured |
| loadseg_begin | unmeasured | unmeasured |
| loadseg_complete | 19.969873 | 19969.873 |
| executable_entry | 19.970876 | 1.003 |
| assets_ready | 19.994613 | 23.737 |
| first_complete_title_frame | 20.064505 | 69.892 |
| input_responsive | 20.115238 | 50.733 |

Total reset to successful input: 20115.238 ms; displayed title and input both ready: 20115.238 ms. Disk reads/seeks and host launch time: unavailable.
Emulated CCK only. LoadSeg catch is completion/entry, not start; file reads/relocation not independently separated. First complete title frame is a frame boundary after a full title-selected frame. Input-responsive point is successful normal selection after the existing first-callback input request; includes that workflow wait. Milestones may overlap: input can respond before a complete title frame. Listed-milestone differences are signed offsets, not invented sequential phase durations; boot complete requires both displayed title and successful input.


| Case / profile | Samples | Update median / p95 / max ms | Sprite render / UI page construction max ms | Dispatcher max ms | Work / deadline headroom ms |
|---|---:|---:|---:|---:|---:|
| two / title | 4 | 9.272 / 16.182 / 16.182 | unmeasured / 11.680 | 1.236 | 0.506 / 0.391 |
| two / one-player-rally | 1 | 6.324 / 6.324 / 6.324 | 1.413 / unmeasured | 2.250 | 10.365 / 10.243 |
| two / two-player-rally | 9262 | 6.111 / 6.301 / 7.603 | 1.595 / unmeasured | 3.551 | 9.085 / 8.928 |
| two / match-end | 48 | 4.032 / 4.490 / 4.810 | 1.441 / unmeasured | 0.767 | 11.878 / 11.699 |
| two / celebration | 888 | 3.914 / 4.186 / 6.668 | 0.980 / unmeasured | 1.162 | 10.020 / 9.946 |

two: chip used 305,656 B; free 218,632 B; largest block 218,056 B; runtime peak 305656 B; cold initialized-pool peak unmeasured.
Deadlines/publications: `{'missed_native_callbacks': 0, 'missed_publications_counter': 0, 'publication_failures': 0}`. Allocation failures: unmeasured; pre-Exec bootstrap: unmeasured.


| Case / profile | Samples | Update median / p95 / max ms | Sprite render / UI page construction max ms | Dispatcher max ms | Work / deadline headroom ms |
|---|---:|---:|---:|---:|---:|
| setup / title | 1237 | 2.351 / 2.401 / 15.013 | unmeasured / 11.636 | 1.238 | 1.676 / 1.518 |
| setup / help | 575 | 2.343 / 2.416 / 14.627 | unmeasured / 11.769 | 0.133 | 2.061 / 1.871 |
| setup / one-player-rally | 30 | 6.118 / 6.299 / 6.311 | 1.579 / unmeasured | 2.258 | 10.378 / 10.213 |
| setup / pause | 88 | 2.181 / 2.292 / 6.142 | unmeasured / unmeasured | 0.019 | 10.546 / 10.347 |

setup deadlines/publications: `{'missed_publications_counter': 0, 'missed_named_profile_deadlines': 0, 'missed_native_callbacks': 0, 'scope': 'Setup raw checker covers all callbacks; demo deadline counts cover named measured profiles only, unprofiled transitions remain unmeasured.'}`.


| Case / profile | Samples | Update median / p95 / max ms | Sprite render / UI page construction max ms | Dispatcher max ms | Work / deadline headroom ms |
|---|---:|---:|---:|---:|---:|
| demo / title | 1800 | 2.351 / 2.401 / 14.747 | unmeasured / unmeasured | 1.202 | 1.941 / 1.753 |
| demo / demo | 11703 | 5.891 / 6.354 / 8.534 | 2.878 / unmeasured | 3.801 | 8.154 / 8.038 |

demo deadlines/publications: `{'missed_publications_counter': 0, 'missed_named_profile_deadlines': 0, 'missed_native_callbacks': None, 'scope': 'Setup raw checker covers all callbacks; demo deadline counts cover named measured profiles only, unprofiled transitions remain unmeasured.'}`.


Coverage: title: measured, help: measured, one-player-rally: measured, two-player-rally: measured, demo: measured, pause: measured, match-end: measured, celebration: measured

Deltas: {"previous_identity": "ea32fefef08509b2817ddc05827848878c2fcfe606d30284cb811fac71096884", "previous_report": "docs/metrics/baselines/pre-title-score-current.json", "previous_report_sha256": "3f201f2af4bf6bf03f50d2a9685442e57b61bb207d2ab024e62d931fb7dbdede", "runtime": {"cold-one": {"profiles": {"celebration": {"dispatcher": {"max_cck": -499, "minimum_headroom_cck": 499.0, "p95_cck": -23, "typical_median_cck": -15.0}, "render": {"max_cck": 220, "minimum_headroom_cck": -220.0, "p95_cck": -295, "typical_median_cck": 34.0}, "ui_construction_render": null, "update_including_render": {"max_cck": 2832, "minimum_headroom_cck": -2832.0, "p95_cck": 2658, "typical_median_cck": 2727.5}}, "demo": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "help": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "match-end": {"dispatcher": {"max_cck": 64, "minimum_headroom_cck": -64.0, "p95_cck": 70, "typical_median_cck": -32.0}, "render": {"max_cck": -23, "minimum_headroom_cck": 23.0, "p95_cck": -38, "typical_median_cck": -25.0}, "ui_construction_render": null, "update_including_render": {"max_cck": -3446, "minimum_headroom_cck": 3446.0, "p95_cck": 507, "typical_median_cck": 1739.0}}, "one-player-rally": {"dispatcher": {"max_cck": -603, "minimum_headroom_cck": 603.0, "p95_cck": -302, "typical_median_cck": -65.0}, "render": {"max_cck": -54, "minimum_headroom_cck": 54.0, "p95_cck": -135, "typical_median_cck": 32.0}, "ui_construction_render": null, "update_including_render": {"max_cck": 328, "minimum_headroom_cck": -328.0, "p95_cck": 780, "typical_median_cck": 1624.0}}, "pause": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "title": {"dispatcher": {"max_cck": -81, "minimum_headroom_cck": 81.0, "p95_cck": -81, "typical_median_cck": -181.0}, "render": null, "ui_construction_render": {"max_cck": -3093, "minimum_headroom_cck": 3093.0, "p95_cck": -3093, "typical_median_cck": -3064.0}, "update_including_render": {"max_cck": 2310, "minimum_headroom_cck": -2310.0, "p95_cck": 2310, "typical_median_cck": -2332.0}}, "two-player-rally": {"dispatcher": {"max_cck": -283, "minimum_headroom_cck": 283.0, "p95_cck": -283, "typical_median_cck": -283.0}, "render": {"max_cck": 679, "minimum_headroom_cck": -679.0, "p95_cck": 679, "typical_median_cck": 679.0}, "ui_construction_render": null, "update_including_render": {"max_cck": 2321, "minimum_headroom_cck": -2321.0, "p95_cck": 2321, "typical_median_cck": 2321.0}}}, "reset_to_input_cck": -16863750, "runtime_memory_bytes": {"chip_free_bytes": 35712, "chip_used_bytes": -35712, "largest_chip_free_block_bytes": 35688, "other_free_bytes": 0, "other_pool_bytes": 0, "other_used_bytes": 0}}, "demo": {"profiles": {"celebration": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "demo": {"dispatcher": {"max_cck": -685, "minimum_headroom_cck": 685.0, "p95_cck": -282, "typical_median_cck": -153.0}, "render": {"max_cck": -13763, "minimum_headroom_cck": 13763.0, "p95_cck": -111, "typical_median_cck": 30.0}, "ui_construction_render": null, "update_including_render": {"max_cck": -7015, "minimum_headroom_cck": 7015.0, "p95_cck": 906, "typical_median_cck": 1633.0}}, "help": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "match-end": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "one-player-rally": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "pause": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "title": {"dispatcher": {"max_cck": -1611, "minimum_headroom_cck": 1611.0, "p95_cck": -179, "typical_median_cck": -179.0}, "render": null, "ui_construction_render": null, "update_including_render": {"max_cck": -1525, "minimum_headroom_cck": 1525.0, "p95_cck": 723, "typical_median_cck": 567.0}}, "two-player-rally": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}}}, "setup": {"profiles": {"celebration": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "demo": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "help": {"dispatcher": {"max_cck": -43908, "minimum_headroom_cck": 43908.0, "p95_cck": -155, "typical_median_cck": -156.0}, "render": null, "ui_construction_render": {"max_cck": -2278, "minimum_headroom_cck": 2278.0, "p95_cck": -2278, "typical_median_cck": -2314.0}, "update_including_render": {"max_cck": -630, "minimum_headroom_cck": 630.0, "p95_cck": 794, "typical_median_cck": 566.0}}, "match-end": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "one-player-rally": {"dispatcher": {"max_cck": -712, "minimum_headroom_cck": 712.0, "p95_cck": -324, "typical_median_cck": -26.5}, "render": {"max_cck": -85, "minimum_headroom_cck": 85.0, "p95_cck": -70, "typical_median_cck": 13.5}, "ui_construction_render": null, "update_including_render": {"max_cck": 163, "minimum_headroom_cck": -163.0, "p95_cck": 638, "typical_median_cck": 1739.5}}, "pause": {"dispatcher": {"max_cck": -179, "minimum_headroom_cck": 179.0, "p95_cck": -179, "typical_median_cck": -179.0}, "render": null, "ui_construction_render": null, "update_including_render": {"max_cck": -36537, "minimum_headroom_cck": 36537.0, "p95_cck": -55, "typical_median_cck": 282.0}}, "title": {"dispatcher": {"max_cck": -42037, "minimum_headroom_cck": 42037.0, "p95_cck": -179, "typical_median_cck": -179.0}, "render": null, "ui_construction_render": {"max_cck": -4551, "minimum_headroom_cck": 4551.0, "p95_cck": -4551, "typical_median_cck": -2716.0}, "update_including_render": {"max_cck": -1007, "minimum_headroom_cck": 1007.0, "p95_cck": 721, "typical_median_cck": 569.0}}, "two-player-rally": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}}}, "two": {"profiles": {"celebration": {"dispatcher": {"max_cck": 155, "minimum_headroom_cck": -155.0, "p95_cck": -20, "typical_median_cck": -13.0}, "render": {"max_cck": 219, "minimum_headroom_cck": -219.0, "p95_cck": -306, "typical_median_cck": 36.0}, "ui_construction_render": null, "update_including_render": {"max_cck": 2770, "minimum_headroom_cck": -2770.0, "p95_cck": 2349, "typical_median_cck": 2835.5}}, "demo": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "help": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "match-end": {"dispatcher": {"max_cck": 39, "minimum_headroom_cck": -39.0, "p95_cck": 83, "typical_median_cck": -4.0}, "render": {"max_cck": 309, "minimum_headroom_cck": -309.0, "p95_cck": 334, "typical_median_cck": 22.5}, "ui_construction_render": null, "update_including_render": {"max_cck": -3550, "minimum_headroom_cck": 3550.0, "p95_cck": 1507, "typical_median_cck": 1662.5}}, "one-player-rally": {"dispatcher": {"max_cck": 237, "minimum_headroom_cck": -237.0, "p95_cck": 237, "typical_median_cck": 237.0}, "render": {"max_cck": -71, "minimum_headroom_cck": 71.0, "p95_cck": -71, "typical_median_cck": -71.0}, "ui_construction_render": null, "update_including_render": {"max_cck": 2024, "minimum_headroom_cck": -2024.0, "p95_cck": 2024, "typical_median_cck": 2024.0}}, "pause": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "title": {"dispatcher": {"max_cck": -53, "minimum_headroom_cck": 53.0, "p95_cck": -53, "typical_median_cck": 1895.0}, "render": null, "ui_construction_render": {"max_cck": -4563, "minimum_headroom_cck": 4563.0, "p95_cck": -4563, "typical_median_cck": -3799.0}, "update_including_render": {"max_cck": 1774, "minimum_headroom_cck": -1774.0, "p95_cck": 1774, "typical_median_cck": 20513.5}}, "two-player-rally": {"dispatcher": {"max_cck": -597, "minimum_headroom_cck": 597.0, "p95_cck": -242, "typical_median_cck": -31.0}, "render": {"max_cck": -42, "minimum_headroom_cck": 42.0, "p95_cck": -103, "typical_median_cck": 32.0}, "ui_construction_render": null, "update_including_render": {"max_cck": 698, "minimum_headroom_cck": -698.0, "p95_cck": 767, "typical_median_cck": 1656.0}}}, "runtime_memory_bytes": {"chip_free_bytes": 35712, "chip_used_bytes": -35712, "largest_chip_free_block_bytes": 35688, "other_free_bytes": 0, "other_pool_bytes": 0, "other_used_bytes": 0}}}, "state": "historical reviewed baseline; master has no accepted metrics report", "static_bytes": {"bss_bytes": 9424, "code_bytes": -5300, "data_bytes": -39840, "executable_bytes": -67000, "loaded_payload_bytes": -35716}}

Refresh hook: after merging new fonts/celebration, run the affected native checks or `RUST_LOG=info python scripts/native_metrics.py --refresh --record`; never copy results from an unfinished branch.
