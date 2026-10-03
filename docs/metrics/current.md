# Native resource and loading metrics

Completion: **complete**. Acceptance is separate from metric coverage.
Product SHA256: `21578578dcce14bc38fb83db06ee242cd848f41f0b03f07a9217d11a87cfbc05`.
Identity excludes generated report files and Git report commits; timestamps are not freshness evidence.

| Executable | Code | Data | BSS | Loaded payload |
|---:|---:|---:|---:|---:|
| 179268 | 43776 | 112188 | 9424 | 165388 |

Asset bytes: {'graphics': 73588, 'audio': 9892, 'replay_loaded_bytes': 1110}. These overlap loaded hunks.

Executable-size budget/headroom: unmeasured (no cap configured); size is not RAM.

Timing uses elapsed emulated colour clocks, including chip-bus waits; host time is unavailable.
PAL display budget: 70,824 CCK (~19.97 ms). Simulation budget: ~59,191.14 CCK (~16.69 ms).
Typical = median; p95 = nearest rank. Frozen/absent phase values remain unmeasured.

UI construction is grouped by page (title = menu; help includes controls/credits), independently of callback-entry profiles; menu-page redraws can occur during pause/input transitions. Pause-only UI construction remains unmeasured.

Release ADF executable: 158916 bytes; symbol bytes removed: 20352. Development retains symbols.
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
| cpu_instructions | 13,308 |
| font | 1,024 |
| front_court_and_title_copper_lists | 648 |
| hunk_header_table | 32 |
| hunk_record_headers_and_ends | 36 |
| initial_hardware_sprites | 576 |
| menu_font_mac | 1,024 |
| mode_banks | 3,072 |
| other_initialized_tables_and_scalars | 777 |
| pre_rendered_demo_options | 512 |
| pre_rendered_help_options | 768 |
| pre_rendered_menu_options | 768 |
| pre_rendered_title_ui_pages | 29,696 |
| pre_rendered_ui_pages | 14,848 |
| relocation_offsets | 2,852 |
| relocation_record_framing | 32 |
| replay_packets | 1,110 |
| reserved_back_copper | 504 |
| reserved_back_sprites | 576 |
| reserved_native_stack | 4,096 |
| reserved_state_and_work_buffers | 968 |
| reserved_third_copper | 504 |
| reserved_third_sprites | 576 |
| reserved_ui_overlay | 512 |
| scene_animation_table | 36 |
| scene_pose_table | 112 |
| scene_robot_pose_table | 112 |
| scene_sprite_variants | 11,264 |
| score_patch_pointer_tables | 528 |
| separate_debug_records | 0 |
| source_alignment_padding | 15 |
| square_led_construction_definitions | 48 |
| status_banks | 7,168 |
| symbol_name_padding | 1,058 |
| symbol_names | 12,974 |
| symbol_record_framing | 6,320 |
| title_bitplanes | 24,576 |
| ui_text_and_line_pointer_tables | 1,756 |
| **Exact file total** | **179,268** |

Mutually exclusive file-byte categories; code/data hunk sizes are a separate containing view, not added again. CPU instructions use actual emitted listing lengths, including operand extensions. Reserved dcb storage is file-backed, not HUNK_BSS. Zero debug means no emitted HUNK_DEBUG record; symbols are counted separately.
Byte-identical incbin payload bytes beyond first copies: 8,192 B. These remain included in the categories; aliasing safety is unproven.


| Case / profile | Samples | Update median / p95 / max ms | Sprite render / UI page construction max ms | Dispatcher max ms | Work / deadline headroom ms |
|---|---:|---:|---:|---:|---:|
| cold-one / title | 9 | 2.327 / 15.114 / 15.114 | unmeasured / 11.989 | 1.254 | 1.575 / 1.336 |
| cold-one / one-player-rally | 3507 | 6.008 / 6.189 / 7.693 | 1.595 / unmeasured | 3.802 | 8.995 / 8.872 |
| cold-one / two-player-rally | 1 | 5.999 / 5.999 / 5.999 | 1.413 / unmeasured | 2.091 | 10.689 / 10.494 |
| cold-one / match-end | 48 | 3.998 / 4.644 / 6.219 | 1.410 / unmeasured | 0.772 | 10.469 / 10.289 |
| cold-one / celebration | 888 | 3.395 / 3.715 / 6.002 | 0.976 / unmeasured | 1.142 | 10.686 / 10.587 |

cold-one: chip used 270,920 B; free 253,368 B; largest block 252,176 B; runtime peak 270920 B; cold initialized-pool peak 270920 B.
Deadlines/publications: `{'missed_native_callbacks': 0, 'missed_publications_counter': 0, 'publication_failures': 0}`. Allocation failures: unmeasured; pre-Exec bootstrap: unmeasured.

| Cold loading stage | Emulated seconds | Signed offset from previous listed milestone (ms) |
|---|---:|---:|
| reset | 0.000000 | unmeasured |
| boot_script_begins | unmeasured | unmeasured |
| loadseg_begin | unmeasured | unmeasured |
| loadseg_complete | 19.951619 | 19951.619 |
| executable_entry | 19.953134 | 1.515 |
| assets_ready | 20.014452 | 61.318 |
| first_complete_title_frame | 20.080702 | 66.250 |
| input_responsive | 20.101537 | 20.835 |

Total reset to successful input: 20101.537 ms; displayed title and input both ready: 20101.537 ms. Disk reads/seeks and host launch time: unavailable.
Emulated CCK only. LoadSeg catch is completion/entry, not start; file reads/relocation not independently separated. First complete title frame is a frame boundary after a full title-selected frame. Input-responsive point is successful normal selection after the existing first-callback input request; includes that workflow wait. Milestones may overlap: input can respond before a complete title frame. Listed-milestone differences are signed offsets, not invented sequential phase durations; boot complete requires both displayed title and successful input.


| Case / profile | Samples | Update median / p95 / max ms | Sprite render / UI page construction max ms | Dispatcher max ms | Work / deadline headroom ms |
|---|---:|---:|---:|---:|---:|
| two / title | 6 | 3.620 / 15.103 / 15.103 | unmeasured / 11.978 | 1.327 | 1.585 / 1.341 |
| two / one-player-rally | 1 | 6.140 / 6.140 / 6.140 | 1.406 / unmeasured | 2.245 | 10.548 / 10.457 |
| two / two-player-rally | 9262 | 5.965 / 6.149 / 7.471 | 1.596 / unmeasured | 3.570 | 9.217 / 9.004 |
| two / match-end | 48 | 3.892 / 4.407 / 6.061 | 1.278 / unmeasured | 0.758 | 10.627 / 10.508 |
| two / celebration | 887 | 3.394 / 3.722 / 6.287 | 0.981 / unmeasured | 1.118 | 10.402 / 10.084 |

two: chip used 304,656 B; free 219,632 B; largest block 219,056 B; runtime peak 304656 B; cold initialized-pool peak unmeasured.
Deadlines/publications: `{'missed_native_callbacks': 0, 'missed_publications_counter': 0, 'publication_failures': 0}`. Allocation failures: unmeasured; pre-Exec bootstrap: unmeasured.


| Case / profile | Samples | Update median / p95 / max ms | Sprite render / UI page construction max ms | Dispatcher max ms | Work / deadline headroom ms |
|---|---:|---:|---:|---:|---:|
| setup / title | 1235 | 2.201 / 2.259 / 15.280 | unmeasured / 11.992 | 12.981 | 1.408 / 1.248 |
| setup / help | 575 | 2.193 / 2.255 / 15.296 | unmeasured / 12.567 | 13.005 | 1.392 / 1.207 |
| setup / one-player-rally | 31 | 5.985 / 6.165 / 6.288 | 1.578 / unmeasured | 2.389 | 10.400 / 10.232 |
| setup / pause | 88 | 2.105 / 2.158 / 15.960 | unmeasured / unmeasured | 0.067 | 0.728 / 0.594 |

setup deadlines/publications: `{'missed_publications_counter': 0, 'missed_named_profile_deadlines': 0, 'missed_native_callbacks': 0, 'scope': 'Setup raw checker covers all callbacks; demo deadline counts cover named measured profiles only, unprofiled transitions remain unmeasured.'}`.


| Case / profile | Samples | Update median / p95 / max ms | Sprite render / UI page construction max ms | Dispatcher max ms | Work / deadline headroom ms |
|---|---:|---:|---:|---:|---:|
| demo / title | 1800 | 2.200 / 2.257 / 15.103 | unmeasured / unmeasured | 1.651 | 1.585 / 1.341 |
| demo / demo | 11703 | 5.727 / 6.186 / 8.315 | 2.998 / unmeasured | 3.779 | 8.373 / 8.198 |

demo deadlines/publications: `{'missed_publications_counter': 0, 'missed_named_profile_deadlines': 0, 'missed_native_callbacks': None, 'scope': 'Setup raw checker covers all callbacks; demo deadline counts cover named measured profiles only, unprofiled transitions remain unmeasured.'}`.


Coverage: title: measured, help: measured, one-player-rally: measured, two-player-rally: measured, demo: measured, pause: measured, match-end: measured, celebration: measured

Deltas: {"previous_identity": "ea32fefef08509b2817ddc05827848878c2fcfe606d30284cb811fac71096884", "previous_report": "docs/metrics/baselines/pre-title-score-current.json", "previous_report_sha256": "3f201f2af4bf6bf03f50d2a9685442e57b61bb207d2ab024e62d931fb7dbdede", "runtime": {"cold-one": {"profiles": {"celebration": {"dispatcher": {"max_cck": -476, "minimum_headroom_cck": 476.0, "p95_cck": -53, "typical_median_cck": -28.0}, "render": {"max_cck": 205, "minimum_headroom_cck": -205.0, "p95_cck": -294, "typical_median_cck": 34.5}, "ui_construction_render": null, "update_including_render": {"max_cck": 373, "minimum_headroom_cck": -373.0, "p95_cck": 685, "typical_median_cck": 1033.0}}, "demo": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "help": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "match-end": {"dispatcher": {"max_cck": 16, "minimum_headroom_cck": -16.0, "p95_cck": 46, "typical_median_cck": -46.5}, "render": {"max_cck": -647, "minimum_headroom_cck": 647.0, "p95_cck": -657, "typical_median_cck": -37.0}, "ui_construction_render": null, "update_including_render": {"max_cck": 1534, "minimum_headroom_cck": -1534.0, "p95_cck": 634, "typical_median_cck": 964.0}}, "one-player-rally": {"dispatcher": {"max_cck": -620, "minimum_headroom_cck": 620.0, "p95_cck": -321, "typical_median_cck": -53.0}, "render": {"max_cck": -54, "minimum_headroom_cck": 54.0, "p95_cck": -121, "typical_median_cck": 30.0}, "ui_construction_render": null, "update_including_render": {"max_cck": -260, "minimum_headroom_cck": 260.0, "p95_cck": 248, "typical_median_cck": 1119.0}}, "pause": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "title": {"dispatcher": {"max_cck": 4, "minimum_headroom_cck": -4.0, "p95_cck": 4, "typical_median_cck": -8.0}, "render": null, "ui_construction_render": {"max_cck": -1954, "minimum_headroom_cck": 1954.0, "p95_cck": -1954, "typical_median_cck": -1821.5}, "update_including_render": {"max_cck": -870, "minimum_headroom_cck": 870.0, "p95_cck": -870, "typical_median_cck": -2425.0}}, "two-player-rally": {"dispatcher": {"max_cck": -751, "minimum_headroom_cck": 751.0, "p95_cck": -751, "typical_median_cck": -751.0}, "render": {"max_cck": 125, "minimum_headroom_cck": -125.0, "p95_cck": 125, "typical_median_cck": 125.0}, "ui_construction_render": null, "update_including_render": {"max_cck": 742, "minimum_headroom_cck": -742.0, "p95_cck": 742, "typical_median_cck": 742.0}}}, "reset_to_input_cck": -16912345, "runtime_memory_bytes": {"chip_free_bytes": 36712, "chip_used_bytes": -36712, "largest_chip_free_block_bytes": 36688, "other_free_bytes": 0, "other_pool_bytes": 0, "other_used_bytes": 0}}, "demo": {"profiles": {"celebration": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "demo": {"dispatcher": {"max_cck": -760, "minimum_headroom_cck": 760.0, "p95_cck": -262, "typical_median_cck": -135.0}, "render": {"max_cck": -13335, "minimum_headroom_cck": 13335.0, "p95_cck": -114, "typical_median_cck": 29.0}, "ui_construction_render": null, "update_including_render": {"max_cck": -7791, "minimum_headroom_cck": 7791.0, "p95_cck": 310, "typical_median_cck": 1050.0}}, "help": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "match-end": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "one-player-rally": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "pause": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "title": {"dispatcher": {"max_cck": -18, "minimum_headroom_cck": 18.0, "p95_cck": 0, "typical_median_cck": 0.0}, "render": null, "ui_construction_render": null, "update_including_render": {"max_cck": -261, "minimum_headroom_cck": 261.0, "p95_cck": 210, "typical_median_cck": 32.5}}, "two-player-rally": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}}}, "setup": {"profiles": {"celebration": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "demo": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "help": {"dispatcher": {"max_cck": 1747, "minimum_headroom_cck": -1747.0, "p95_cck": 1, "typical_median_cck": 0.0}, "render": null, "ui_construction_render": {"max_cck": 551, "minimum_headroom_cck": -551.0, "p95_cck": 551, "typical_median_cck": 543.0}, "update_including_render": {"max_cck": 1745, "minimum_headroom_cck": -1745.0, "p95_cck": 226, "typical_median_cck": 32.0}}, "match-end": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "one-player-rally": {"dispatcher": {"max_cck": -248, "minimum_headroom_cck": 248.0, "p95_cck": -250, "typical_median_cck": -13.0}, "render": {"max_cck": -89, "minimum_headroom_cck": 89.0, "p95_cck": -102, "typical_median_cck": 22.0}, "ui_construction_render": null, "update_including_render": {"max_cck": 82, "minimum_headroom_cck": -82.0, "p95_cck": 161, "typical_median_cck": 1267.0}}, "pause": {"dispatcher": {"max_cck": -6, "minimum_headroom_cck": 6.0, "p95_cck": -6, "typical_median_cck": -6.0}, "render": null, "ui_construction_render": null, "update_including_render": {"max_cck": -1715, "minimum_headroom_cck": 1715.0, "p95_cck": -529, "typical_median_cck": 11.5}}, "title": {"dispatcher": {"max_cck": -385, "minimum_headroom_cck": 385.0, "p95_cck": 0, "typical_median_cck": 0.0}, "render": null, "ui_construction_render": {"max_cck": -3290, "minimum_headroom_cck": 3290.0, "p95_cck": -3290, "typical_median_cck": -1564.0}, "update_including_render": {"max_cck": -59, "minimum_headroom_cck": 59.0, "p95_cck": 219, "typical_median_cck": 36.0}}, "two-player-rally": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}}}, "two": {"profiles": {"celebration": {"dispatcher": {"max_cck": 0, "minimum_headroom_cck": 0.0, "p95_cck": -39, "typical_median_cck": -25.0}, "render": {"max_cck": 221, "minimum_headroom_cck": -221.0, "p95_cck": -305, "typical_median_cck": 35.0}, "ui_construction_render": null, "update_including_render": {"max_cck": 1418, "minimum_headroom_cck": -1418.0, "p95_cck": 705, "typical_median_cck": 988.5}}, "demo": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "help": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "match-end": {"dispatcher": {"max_cck": 4, "minimum_headroom_cck": -4.0, "p95_cck": -1, "typical_median_cck": -19.0}, "render": {"max_cck": -268, "minimum_headroom_cck": 268.0, "p95_cck": -240, "typical_median_cck": 21.5}, "ui_construction_render": null, "update_including_render": {"max_cck": 885, "minimum_headroom_cck": -885.0, "p95_cck": 1211, "typical_median_cck": 1164.0}}, "one-player-rally": {"dispatcher": {"max_cck": 222, "minimum_headroom_cck": -222.0, "p95_cck": 222, "typical_median_cck": 222.0}, "render": {"max_cck": -98, "minimum_headroom_cck": 98.0, "p95_cck": -98, "typical_median_cck": -98.0}, "ui_construction_render": null, "update_including_render": {"max_cck": 1374, "minimum_headroom_cck": -1374.0, "p95_cck": 1374, "typical_median_cck": 1374.0}}, "pause": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "title": {"dispatcher": {"max_cck": 268, "minimum_headroom_cck": -268.0, "p95_cck": 268, "typical_median_cck": -15.0}, "render": null, "ui_construction_render": {"max_cck": -3504, "minimum_headroom_cck": 3504.0, "p95_cck": -3504, "typical_median_cck": -2630.0}, "update_including_render": {"max_cck": -2051, "minimum_headroom_cck": 2051.0, "p95_cck": -2051, "typical_median_cck": 465.0}}, "two-player-rally": {"dispatcher": {"max_cck": -527, "minimum_headroom_cck": 527.0, "p95_cck": -247, "typical_median_cck": -27.0}, "render": {"max_cck": -41, "minimum_headroom_cck": 41.0, "p95_cck": -100, "typical_median_cck": 30.0}, "ui_construction_render": null, "update_including_render": {"max_cck": 230, "minimum_headroom_cck": -230.0, "p95_cck": 230, "typical_median_cck": 1141.5}}}, "runtime_memory_bytes": {"chip_free_bytes": 36712, "chip_used_bytes": -36712, "largest_chip_free_block_bytes": 36688, "other_free_bytes": 0, "other_pool_bytes": 0, "other_used_bytes": 0}}}, "state": "historical reviewed baseline; master has no accepted metrics report", "static_bytes": {"bss_bytes": 9424, "code_bytes": -5788, "data_bytes": -40352, "executable_bytes": -69212, "loaded_payload_bytes": -36716}}

Refresh hook: after merging new fonts/celebration, run the affected native checks or `RUST_LOG=info python scripts/native_metrics.py --refresh --record`; never copy results from an unfinished branch.
