# Native resource and loading metrics

Completion: **complete**. Acceptance is separate from metric coverage.
Product SHA256: `e81fe61be19e28cb585f4c0f5808ebc96aa038d77a5f6667780e14f79f30f46c`.
Identity excludes generated report files and Git report commits; timestamps are not freshness evidence.

| Executable | Code | Data | BSS | Loaded payload |
|---:|---:|---:|---:|---:|
| 198960 | 40140 | 114540 | 0 | 154680 |

Asset bytes: {'graphics': 105172, 'audio': 5408, 'replay_loaded_bytes': 1110}. These overlap loaded hunks.

Executable-size budget/headroom: unmeasured (no cap configured); size is not RAM.

Timing uses elapsed emulated colour clocks, including chip-bus waits; host time is unavailable.
PAL display budget: 70,824 CCK (~19.97 ms). Simulation budget: ~59,191.14 CCK (~16.69 ms).
Typical = median; p95 = nearest rank. Frozen/absent phase values remain unmeasured.

UI construction is grouped by page (title = menu; help includes controls/credits), independently of callback-entry profiles; menu-page redraws can occur during pause/input transitions. Pause-only UI construction remains unmeasured.

Release ADF executable: 163876 bytes; symbol bytes removed: 35084. Development retains symbols.
RAM measures whole initialized machine pools including OS/stack. Direct-executable and cold ADF startup differ; compare RAM within the same startup case.

| Mutually exclusive executable category | Bytes |
|---|---:|
| audio_envelopes | 128 |
| audio_period_table | 3,072 |
| audio_scores | 2,208 |
| build_version_text | 14 |
| court_bitplanes | 24,576 |
| cpu_instructions | 11,118 |
| font | 1,024 |
| front_court_and_title_copper_lists | 3,256 |
| hunk_header_table | 28 |
| hunk_payload_alignment_padding | 2 |
| hunk_record_headers_and_ends | 24 |
| initial_hardware_sprites | 576 |
| mode_banks | 3,072 |
| other_initialized_tables_and_scalars | 738 |
| paula_square_wave | 4 |
| pre_rendered_ui_pages | 10,240 |
| relocation_offsets | 9,120 |
| relocation_record_framing | 24 |
| replay_packets | 1,110 |
| reserved_back_copper | 3,120 |
| reserved_back_sprites | 576 |
| reserved_native_stack | 4,096 |
| reserved_state_and_work_buffers | 704 |
| reserved_ui_overlay | 512 |
| scene_animation_table | 36 |
| scene_pose_table | 112 |
| scene_sprite_variants | 8,192 |
| score_game_banks | 21,504 |
| score_patch_pointer_tables | 7,604 |
| score_point_banks | 14,336 |
| separate_debug_records | 0 |
| source_alignment_padding | 13 |
| status_banks | 7,168 |
| symbol_name_padding | 1,383 |
| symbol_names | 22,989 |
| symbol_record_framing | 10,712 |
| title_bitplanes | 24,576 |
| ui_text_and_line_pointer_tables | 993 |
| **Exact file total** | **198,960** |

Mutually exclusive file-byte categories; code/data hunk sizes are a separate containing view, not added again. CPU instructions use actual emitted listing lengths, including operand extensions. Reserved dcb storage is file-backed, not HUNK_BSS. Zero debug means no emitted HUNK_DEBUG record; symbols are counted separately.
Byte-identical incbin payload bytes beyond first copies: 26,624 B. These remain included in the categories; aliasing safety is unproven.


| Case / profile | Samples | Update median / p95 / max ms | Sprite render / UI page construction max ms | Dispatcher max ms | Work / deadline headroom ms |
|---|---:|---:|---:|---:|---:|
| cold-one / title | 8 | 2.876 / 11.228 / 11.228 | unmeasured / 8.466 | 1.236 | 5.460 / 5.250 |
| cold-one / one-player-rally | 3507 | 5.630 / 6.059 / 7.631 | 1.586 / unmeasured | 3.927 | 9.057 / 8.880 |
| cold-one / two-player-rally | 1 | 5.880 / 5.880 / 5.880 | 1.388 / unmeasured | 2.373 | 10.808 / 10.714 |
| cold-one / match-end | 193 | 3.826 / 4.229 / 4.509 | 1.546 / unmeasured | 0.745 | 12.179 / 11.934 |

cold-one: chip used 260,208 B; free 264,080 B; largest block 262,912 B; runtime peak 260208 B; cold initialized-pool peak 322840 B.
Deadlines/publications: `{'missed_native_callbacks': 0, 'missed_publications_counter': 0, 'publication_failures': 0}`. Allocation failures: unmeasured; pre-Exec bootstrap: unmeasured.

| Cold loading stage | Emulated seconds | Signed offset from previous listed milestone (ms) |
|---|---:|---:|
| reset | 0.000000 | unmeasured |
| boot_script_begins | unmeasured | unmeasured |
| loadseg_begin | unmeasured | unmeasured |
| loadseg_complete | 20.582720 | 20582.720 |
| executable_entry | 20.583725 | 1.005 |
| assets_ready | 20.595379 | 11.654 |
| first_complete_title_frame | 20.636332 | 40.952 |
| input_responsive | 20.665747 | 29.415 |

Total reset to successful input: 20665.747 ms; displayed title and input both ready: 20665.747 ms. Disk reads/seeks and host launch time: unavailable.
Emulated CCK only. LoadSeg catch is completion/entry, not start; file reads/relocation not independently separated. First complete title frame is a frame boundary after a full title-selected frame. Input-responsive point is successful normal selection after the existing first-callback input request; includes that workflow wait. Milestones may overlap: input can respond before a complete title frame. Listed-milestone differences are signed offsets, not invented sequential phase durations; boot complete requires both displayed title and successful input.


| Case / profile | Samples | Update median / p95 / max ms | Sprite render / UI page construction max ms | Dispatcher max ms | Work / deadline headroom ms |
|---|---:|---:|---:|---:|---:|
| two / title | 5 | 3.517 / 12.269 / 12.269 | unmeasured / 9.511 | 1.240 | 4.419 / 4.310 |
| two / one-player-rally | 1 | 5.600 / 5.600 / 5.600 | 1.346 / unmeasured | 2.166 | 11.088 / 10.655 |
| two / two-player-rally | 9262 | 5.595 / 6.027 / 7.412 | 1.586 / unmeasured | 3.680 | 9.276 / 9.089 |
| two / match-end | 193 | 3.740 / 4.174 / 4.257 | 1.429 / unmeasured | 0.717 | 12.431 / 12.233 |

two: chip used 293,944 B; free 230,344 B; largest block 229,792 B; runtime peak 293944 B; cold initialized-pool peak unmeasured.
Deadlines/publications: `{'missed_native_callbacks': 0, 'missed_publications_counter': 0, 'publication_failures': 0}`. Allocation failures: unmeasured; pre-Exec bootstrap: unmeasured.


| Case / profile | Samples | Update median / p95 / max ms | Sprite render / UI page construction max ms | Dispatcher max ms | Work / deadline headroom ms |
|---|---:|---:|---:|---:|---:|
| setup / title | 1237 | 2.169 / 2.175 / 12.349 | unmeasured / 9.484 | 10.153 | 4.339 / 4.253 |
| setup / help | 372 | 2.162 / 2.169 / 11.831 | unmeasured / 8.275 | 9.552 | 4.857 / 4.658 |
| setup / one-player-rally | 31 | 5.617 / 6.050 / 6.170 | 1.575 / unmeasured | 2.316 | 10.518 / 10.298 |
| setup / pause | 88 | 2.118 / 2.349 / 12.500 | unmeasured / unmeasured | 0.062 | 4.188 / 4.117 |

setup deadlines/publications: `{'missed_publications_counter': 0, 'missed_named_profile_deadlines': 0, 'missed_native_callbacks': 0, 'scope': 'Setup raw checker covers all callbacks; demo deadline counts cover named measured profiles only, unprofiled transitions remain unmeasured.'}`.


| Case / profile | Samples | Update median / p95 / max ms | Sprite render / UI page construction max ms | Dispatcher max ms | Work / deadline headroom ms |
|---|---:|---:|---:|---:|---:|
| demo / title | 1800 | 2.169 / 2.174 / 11.151 | unmeasured / unmeasured | 1.680 | 5.537 / 5.323 |
| demo / demo | 11703 | 5.353 / 6.011 / 11.398 | 7.841 / unmeasured | 3.976 | 5.291 / 5.067 |

demo deadlines/publications: `{'missed_publications_counter': 0, 'missed_named_profile_deadlines': 0, 'missed_native_callbacks': None, 'scope': 'Setup raw checker covers all callbacks; demo deadline counts cover named measured profiles only, unprofiled transitions remain unmeasured.'}`.


Coverage: title: measured, help: measured, one-player-rally: measured, two-player-rally: measured, demo: measured, pause: measured, match-end: measured, celebration: unavailable in this product; remeasure when implemented

Deltas: {"state": "no previous accepted compatible report"}

Refresh hook: after merging new fonts/celebration, run the affected native checks or `RUST_LOG=info python scripts/native_metrics.py --refresh --record`; never copy results from an unfinished branch.
