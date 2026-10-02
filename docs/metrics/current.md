# Native resource and loading metrics

Completion: **complete**. Acceptance is separate from metric coverage.
Product SHA256: `0240658feac160753239ca9bfdbed30858b56049ecf68f0a8647d5158bd26ea9`.
Identity excludes generated report files and Git report commits; timestamps are not freshness evidence.

| Executable | Code | Data | BSS | Loaded payload |
|---:|---:|---:|---:|---:|
| 248480 | 49564 | 152540 | 0 | 202104 |

Asset bytes: {'graphics': 109380, 'audio': 9892, 'replay_loaded_bytes': 1110}. These overlap loaded hunks.

Executable-size budget/headroom: unmeasured (no cap configured); size is not RAM.

Timing uses elapsed emulated colour clocks, including chip-bus waits; host time is unavailable.
PAL display budget: 70,824 CCK (~19.97 ms). Simulation budget: ~59,191.14 CCK (~16.69 ms).
Typical = median; p95 = nearest rank. Frozen/absent phase values remain unmeasured.

UI construction is grouped by page (title = menu; help includes controls/credits), independently of callback-entry profiles; menu-page redraws can occur during pause/input transitions. Pause-only UI construction remains unmeasured.

Release ADF executable: 211920 bytes; symbol bytes removed: 36560. Development retains symbols.
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
| **Exact file total** | **248,480** |

Mutually exclusive file-byte categories; code/data hunk sizes are a separate containing view, not added again. CPU instructions use actual emitted listing lengths, including operand extensions. Reserved dcb storage is file-backed, not HUNK_BSS. Zero debug means no emitted HUNK_DEBUG record; symbols are counted separately.
Byte-identical incbin payload bytes beyond first copies: 22,528 B. These remain included in the categories; aliasing safety is unproven.


| Case / profile | Samples | Update median / p95 / max ms | Sprite render / UI page construction max ms | Dispatcher max ms | Work / deadline headroom ms |
|---|---:|---:|---:|---:|---:|
| cold-one / title | 8 | 3.011 / 15.359 / 15.359 | unmeasured / 12.540 | 1.253 | 1.329 / 1.161 |
| cold-one / one-player-rally | 3507 | 5.693 / 6.119 / 7.767 | 1.610 / unmeasured | 3.976 | 8.922 / 8.743 |
| cold-one / two-player-rally | 1 | 5.790 / 5.790 / 5.790 | 1.378 / unmeasured | 2.302 | 10.898 / 10.815 |
| cold-one / match-end | 48 | 3.726 / 4.465 / 5.787 | 1.592 / unmeasured | 0.767 | 10.901 / 10.707 |
| cold-one / celebration | 887 | 3.104 / 3.522 / 5.897 | 0.918 / unmeasured | 1.276 | 10.791 / 10.474 |

cold-one: chip used 307,632 B; free 216,656 B; largest block 215,488 B; runtime peak 307632 B; cold initialized-pool peak 311640 B.
Deadlines/publications: `{'missed_native_callbacks': 0, 'missed_publications_counter': 0, 'publication_failures': 0}`. Allocation failures: unmeasured; pre-Exec bootstrap: unmeasured.

| Cold loading stage | Emulated seconds | Signed offset from previous listed milestone (ms) |
|---|---:|---:|
| reset | 0.000000 | unmeasured |
| boot_script_begins | unmeasured | unmeasured |
| loadseg_begin | unmeasured | unmeasured |
| loadseg_complete | 24.786221 | 24786.221 |
| executable_entry | 24.787227 | 1.007 |
| assets_ready | 24.799342 | 12.115 |
| first_complete_title_frame | 24.841747 | 42.404 |
| input_responsive | 24.869748 | 28.002 |

Total reset to successful input: 24869.748 ms; displayed title and input both ready: 24869.748 ms. Disk reads/seeks and host launch time: unavailable.
Emulated CCK only. LoadSeg catch is completion/entry, not start; file reads/relocation not independently separated. First complete title frame is a frame boundary after a full title-selected frame. Input-responsive point is successful normal selection after the existing first-callback input request; includes that workflow wait. Milestones may overlap: input can respond before a complete title frame. Listed-milestone differences are signed offsets, not invented sequential phase durations; boot complete requires both displayed title and successful input.


| Case / profile | Samples | Update median / p95 / max ms | Sprite render / UI page construction max ms | Dispatcher max ms | Work / deadline headroom ms |
|---|---:|---:|---:|---:|---:|
| two / title | 6 | 3.488 / 15.682 / 15.682 | unmeasured / 12.966 | 1.251 | 1.007 / 0.869 |
| two / one-player-rally | 1 | 5.753 / 5.753 / 5.753 | 1.433 / unmeasured | 2.183 | 10.935 / 10.718 |
| two / two-player-rally | 9262 | 5.644 / 6.084 / 7.406 | 1.607 / unmeasured | 3.719 | 9.282 / 9.115 |
| two / match-end | 48 | 3.564 / 4.066 / 5.811 | 1.354 / unmeasured | 0.756 | 10.877 / 10.690 |
| two / celebration | 888 | 3.115 / 3.524 / 5.887 | 0.918 / unmeasured | 1.118 | 10.801 / 10.423 |

two: chip used 341,368 B; free 182,920 B; largest block 182,368 B; runtime peak 341368 B; cold initialized-pool peak unmeasured.
Deadlines/publications: `{'missed_native_callbacks': 0, 'missed_publications_counter': 0, 'publication_failures': 0}`. Allocation failures: unmeasured; pre-Exec bootstrap: unmeasured.


| Case / profile | Samples | Update median / p95 / max ms | Sprite render / UI page construction max ms | Dispatcher max ms | Work / deadline headroom ms |
|---|---:|---:|---:|---:|---:|
| setup / title | 1236 | 2.191 / 2.198 / 15.296 | unmeasured / 12.919 | 13.090 | 1.392 / 1.286 |
| setup / help | 576 | 2.184 / 2.192 / 14.804 | unmeasured / 12.411 | 12.512 | 1.884 / 1.713 |
| setup / one-player-rally | 31 | 5.627 / 6.119 / 6.265 | 1.603 / unmeasured | 2.459 | 10.424 / 10.213 |
| setup / pause | 88 | 2.101 / 2.307 / 16.443 | unmeasured / unmeasured | 0.069 | 0.245 / 0.083 |

setup deadlines/publications: `{'missed_publications_counter': 0, 'missed_named_profile_deadlines': 0, 'missed_native_callbacks': 0, 'scope': 'Setup raw checker covers all callbacks; demo deadline counts cover named measured profiles only, unprofiled transitions remain unmeasured.'}`.


| Case / profile | Samples | Update median / p95 / max ms | Sprite render / UI page construction max ms | Dispatcher max ms | Work / deadline headroom ms |
|---|---:|---:|---:|---:|---:|
| demo / title | 1800 | 2.191 / 2.197 / 15.177 | unmeasured / unmeasured | 1.656 | 1.511 / 1.299 |
| demo / demo | 11703 | 5.431 / 6.099 / 10.512 | 6.758 / unmeasured | 3.994 | 6.176 / 5.972 |

demo deadlines/publications: `{'missed_publications_counter': 0, 'missed_named_profile_deadlines': 0, 'missed_native_callbacks': None, 'scope': 'Setup raw checker covers all callbacks; demo deadline counts cover named measured profiles only, unprofiled transitions remain unmeasured.'}`.


Coverage: title: measured, help: measured, one-player-rally: measured, two-player-rally: measured, demo: measured, pause: measured, match-end: measured, celebration: measured

Deltas: {"previous_identity": "2dd4e5c571ce765c989e09ed08ad74372ee8d1b495ec90da0aeafe0efeb5a24d", "previous_report": "docs/metrics/baselines/pre-pr19-release.json", "previous_report_sha256": "fc6136389b5a7912105b6434235eab47eb25d96159e6be022a3dabc4f1657786", "runtime": {"cold-one": {"state": "incompatible or unmeasured"}, "demo": {"state": "incompatible or unmeasured"}, "setup": {"state": "incompatible or unmeasured"}, "two": {"state": "incompatible or unmeasured"}}, "state": "historical reviewed baseline; master has no accepted metrics report", "static_bytes": {"bss_bytes": 0, "code_bytes": 9424, "data_bytes": 38000, "executable_bytes": 49520, "loaded_payload_bytes": 47424}}

Refresh hook: after merging new fonts/celebration, run the affected native checks or `RUST_LOG=info python scripts/native_metrics.py --refresh --record`; never copy results from an unfinished branch.
