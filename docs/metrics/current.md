# Native resource and loading metrics

Completion: **incomplete**. Acceptance is separate from metric coverage.
Product SHA256: `fc069ea65b35fb162c35a391238e180b4d9de29f0b2047bfc36468bcac20d4c4`.
Identity excludes generated report files and Git report commits; timestamps are not freshness evidence.

| Executable | Code | Data | BSS | Loaded payload |
|---:|---:|---:|---:|---:|
| 186272 | 46644 | 112700 | 89744 | 249088 |

Asset bytes: {'graphics': 73588, 'audio': 9892, 'replay_loaded_bytes': 1110}. These overlap loaded hunks.

Executable-size budget/headroom: unmeasured (no cap configured); size is not RAM.

Timing uses elapsed emulated colour clocks, including chip-bus waits; host time is unavailable.
PAL display budget: 70,824 CCK (~19.97 ms). Simulation budget: ~59,191.14 CCK (~16.69 ms).
Typical = median; p95 = nearest rank. Frozen/absent phase values remain unmeasured.

UI construction is grouped by page (title = menu; help includes controls/credits), independently of callback-entry profiles; menu-page redraws can occur during pause/input transitions. Pause-only UI construction remains unmeasured.

Release ADF executable: 163036 bytes; symbol bytes removed: 23236. Development retains symbols.
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
| cpu_instructions | 15,986 |
| font | 1,024 |
| front_court_and_title_copper_lists | 648 |
| hunk_header_table | 36 |
| hunk_payload_alignment_padding | 2 |
| hunk_record_headers_and_ends | 48 |
| initial_hardware_sprites | 576 |
| menu_font_mac | 1,024 |
| mode_banks | 3,072 |
| other_initialized_tables_and_scalars | 968 |
| pre_rendered_demo_options | 512 |
| pre_rendered_help_options | 768 |
| pre_rendered_menu_options | 768 |
| pre_rendered_title_identities | 512 |
| pre_rendered_title_ui_pages | 29,696 |
| pre_rendered_ui_pages | 14,848 |
| relocation_offsets | 3,568 |
| relocation_record_framing | 40 |
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
| symbol_name_padding | 1,192 |
| symbol_names | 14,988 |
| symbol_record_framing | 7,056 |
| title_bitplanes | 24,576 |
| ui_text_and_line_pointer_tables | 1,756 |
| **Exact file total** | **186,272** |

Mutually exclusive file-byte categories; code/data hunk sizes are a separate containing view, not added again. CPU instructions use actual emitted listing lengths, including operand extensions. Reserved dcb storage is file-backed, not HUNK_BSS. Zero debug means no emitted HUNK_DEBUG record; symbols are counted separately.
Byte-identical incbin payload bytes beyond first copies: 8,192 B. These remain included in the categories; aliasing safety is unproven.


| Case / profile | Samples | Update median / p95 / max ms | Sprite render / UI page construction max ms | Dispatcher max ms | Work / deadline headroom ms |
|---|---:|---:|---:|---:|---:|
| cold-one / title | 8 | 2.864 / 16.342 / 16.342 | unmeasured / 11.695 | 0.957 | 0.346 / 0.264 |
| cold-one / one-player-rally | 4062 | 6.716 / 7.011 / 8.654 | 1.610 / unmeasured | 4.256 | 8.034 / 7.929 |
| cold-one / two-player-rally | 1 | 6.924 / 6.924 / 6.924 | 1.422 / unmeasured | 2.491 | 9.764 / 9.607 |
| cold-one / match-end | 48 | 4.704 / 5.113 / 5.498 | 1.426 / unmeasured | 1.129 | 11.190 / 11.064 |
| cold-one / celebration | 888 | 4.410 / 4.825 / 7.488 | 0.995 / unmeasured | 1.351 | 9.200 / 9.106 |

cold-one: chip used 354,632 B; free 169,656 B; largest block 168,464 B; runtime peak 354632 B; cold initialized-pool peak 354632 B.
Deadlines/publications: `{'missed_native_callbacks': 0, 'missed_publications_counter': 0, 'publication_failures': 0}`. Allocation failures: unmeasured; pre-Exec bootstrap: unmeasured.

| Cold loading stage | Emulated seconds | Signed offset from previous listed milestone (ms) |
|---|---:|---:|
| reset | 0.000000 | unmeasured |
| boot_script_begins | unmeasured | unmeasured |
| loadseg_begin | unmeasured | unmeasured |
| loadseg_complete | 20.444302 | 20444.302 |
| executable_entry | 20.445306 | 1.003 |
| assets_ready | 20.469864 | 24.558 |
| first_complete_title_frame | 20.523772 | 53.908 |
| input_responsive | 20.573999 | 50.228 |

Total reset to successful input: 20573.999 ms; displayed title and input both ready: 20573.999 ms. Disk reads/seeks and host launch time: unavailable.
Emulated CCK only. LoadSeg catch is completion/entry, not start; file reads/relocation not independently separated. First complete title frame is a frame boundary after a full title-selected frame. Input-responsive point is successful normal selection after the existing first-callback input request; includes that workflow wait. Milestones may overlap: input can respond before a complete title frame. Listed-milestone differences are signed offsets, not invented sequential phase durations; boot complete requires both displayed title and successful input.

| two: not run | | | | | |
| setup: not run | | | | | |
| demo: not run | | | | | |

Coverage: title: measured, help: unmeasured, one-player-rally: measured, two-player-rally: measured, demo: unmeasured, pause: unmeasured, match-end: measured, celebration: measured

Deltas: {"previous_identity": "ea32fefef08509b2817ddc05827848878c2fcfe606d30284cb811fac71096884", "previous_report": "docs/metrics/baselines/pre-title-score-current.json", "previous_report_sha256": "3f201f2af4bf6bf03f50d2a9685442e57b61bb207d2ab024e62d931fb7dbdede", "runtime": {"cold-one": {"profiles": {"celebration": {"dispatcher": {"max_cck": 267, "minimum_headroom_cck": -267.0, "p95_cck": 453, "typical_median_cck": 373.0}, "render": {"max_cck": 273, "minimum_headroom_cck": -273.0, "p95_cck": -259, "typical_median_cck": 71.0}, "ui_construction_render": null, "update_including_render": {"max_cck": 5642, "minimum_headroom_cck": -5642.0, "p95_cck": 4620, "typical_median_cck": 4632.5}}, "demo": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "help": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "match-end": {"dispatcher": {"max_cck": 1281, "minimum_headroom_cck": -1281.0, "p95_cck": 610, "typical_median_cck": 375.5}, "render": {"max_cck": -588, "minimum_headroom_cck": 588.0, "p95_cck": -594, "typical_median_cck": 28.5}, "ui_construction_render": null, "update_including_render": {"max_cck": -1025, "minimum_headroom_cck": 1025.0, "p95_cck": 2298, "typical_median_cck": 3468.5}}, "one-player-rally": {"dispatcher": {"max_cck": 990, "minimum_headroom_cck": -990.0, "p95_cck": 395, "typical_median_cck": 606.0}, "render": {"max_cck": -2, "minimum_headroom_cck": 2.0, "p95_cck": -84, "typical_median_cck": 64.0}, "ui_construction_render": null, "update_including_render": {"max_cck": 3148, "minimum_headroom_cck": -3148.0, "p95_cck": 3163, "typical_median_cck": 3629.5}}, "pause": {"dispatcher": null, "render": null, "ui_construction_render": null, "update_including_render": null}, "title": {"dispatcher": {"max_cck": -1051, "minimum_headroom_cck": 1051.0, "p95_cck": -1051, "typical_median_cck": 209.0}, "render": null, "ui_construction_render": {"max_cck": -2997, "minimum_headroom_cck": 2997.0, "p95_cck": -2997, "typical_median_cck": -3135.5}, "update_including_render": {"max_cck": 3489, "minimum_headroom_cck": -3489.0, "p95_cck": 3489, "typical_median_cck": -520.5}}, "two-player-rally": {"dispatcher": {"max_cck": 669, "minimum_headroom_cck": -669.0, "p95_cck": 669, "typical_median_cck": 669.0}, "render": {"max_cck": 156, "minimum_headroom_cck": -156.0, "p95_cck": 156, "typical_median_cck": 156.0}, "ui_construction_render": null, "update_including_render": {"max_cck": 4022, "minimum_headroom_cck": -4022.0, "p95_cck": 4022, "typical_median_cck": 4022.0}}}, "reset_to_input_cck": -15236571, "runtime_memory_bytes": {"chip_free_bytes": -47000, "chip_used_bytes": 47000, "largest_chip_free_block_bytes": -47024, "other_free_bytes": 0, "other_pool_bytes": 0, "other_used_bytes": 0}}, "demo": {"state": "incompatible or unmeasured"}, "setup": {"state": "incompatible or unmeasured"}, "two": {"state": "incompatible or unmeasured"}}, "state": "historical reviewed baseline; master has no accepted metrics report", "static_bytes": {"bss_bytes": 89744, "code_bytes": -2920, "data_bytes": -39840, "executable_bytes": -62208, "loaded_payload_bytes": 46984}}

Refresh hook: after merging new fonts/celebration, run the affected native checks or `RUST_LOG=info python scripts/native_metrics.py --refresh --record`; never copy results from an unfinished branch.
