# Direct HUD measured comparison

This compares accepted PR #25 with the direct score/WIN implementation. Extrema are observed within named finite workloads, not proven bounds. Old ordinary workloads reuse their accepted summaries; only the missing display/ISR and dirty-HUD measurements use new bounded baseline probes. The old normal executable reproduced its accepted SHA256 exactly.

## Storage

| Metric | Before | After | Delta |
| --- | ---: | ---: | ---: |
| executable_bytes | 240,732 | 179,268 | -61,464 |
| code_bytes | 50,892 | 43,776 | -7,116 |
| data_bytes | 141,396 | 112,188 | -29,208 |
| bss_bytes | 14,336 | 9,424 | -4,912 |
| loaded_payload_bytes | 206,624 | 165,388 | -41,236 |
| relocation_bytes | 9,920 | 2,884 | -7,036 |
| relocations | 2,472 | 713 | -1,759 |
| symbol_bytes | 38,456 | 20,352 | -18,104 |
| cpu_instruction_bytes | 12,904 | 13,308 | +404 |

Hunk CODE includes tables and reserves; the instruction row is listing-backed. Loaded payload is not whole-machine chip usage. The loaded-payload reduction reconciles as 26,416 bytes of bitmap storage + 7,480 bytes of pointer tables + 7,704 bytes across three Copper lists + 40 bytes of other initialized tables/scalars − 404 added instruction bytes = 41,236 bytes. Relocation and symbol savings additionally reduce file size. Whole-machine RAM and cold loading remain in the linked complete resource report.

## Ordinary accepted workloads

PAL CCK frequency 3,546,895 Hz; divide CCK by 3,546.895 for milliseconds. Counts and receipt hashes are retained in the JSON. Profile names and measurement boundaries match; transition callbacks retain the existing observer rules.

| Workload / profile | Callbacks old/new | Minimum simulation deadline headroom CCK old → new | ms old → new |
| --- | ---: | ---: | ---: |
| cold-one / title | 8/9 | 3683.720 → 4739.137 | 1.039 → 1.336 |
| cold-one / one-player-rally | 3507/3507 | 30311.584 → 31467.055 | 8.546 → 8.872 |
| cold-one / two-player-rally | 1/1 | 36083.539 → 37222.088 | 10.173 → 10.494 |
| cold-one / match-end | 48/48 | 35235.403 → 36495.541 | 9.934 → 10.289 |
| cold-one / celebration | 887/888 | 34977.485 → 37550.623 | 9.861 → 10.587 |
| two / title | 6/6 | 4774.748 → 4757.137 | 1.346 → 1.341 |
| two / one-player-rally | 1/1 | 37330.842 → 37088.567 | 10.525 → 10.457 |
| two / two-player-rally | 9262/9262 | 30948.923 → 31936.665 | 8.726 → 9.004 |
| two / match-end | 48/48 | 36523.431 → 37269.431 | 10.297 → 10.508 |
| two / celebration | 887/887 | 34895.513 → 35765.513 | 9.838 → 10.084 |
| setup / title | 1233/1235 | 4276.889 → 4427.163 | 1.206 → 1.248 |
| setup / help | 575/575 | 4271.770 → 4282.751 | 1.204 → 1.207 |
| setup / one-player-rally | 31/31 | 35441.869 → 36292.806 | 9.992 → 10.232 |
| setup / pause | 88/88 | 791.005 → 2106.279 | 0.223 → 0.594 |
| demo / title | 1800/1800 | 4976.137 → 4757.137 | 1.403 → 1.341 |
| demo / demo | 11703/11703 | 5977.497 → 29077.497 | 1.685 → 8.198 |

## All-callback deadline minima

These new raw-capture reductions include transition/serve and input callbacks omitted from named-profile tables. The accepted baseline summary does not retain the corresponding global minima, and its raw captures were unavailable here; those before values are explicitly unavailable. A zero missed-deadline count is not a measured minimum. `minimum_phase_cck` is entry phase, not spare time.

| Workload | Completed callbacks | New minimum headroom CCK | ms | Callback at minimum |
| --- | ---: | ---: | ---: | ---: |
| cold-one | 11856 | 4739.137 | 1.336 | 1 |
| two | 23795 | 4757.137 | 1.341 | 1 |
| setup | 2133 | 2106.279 | 0.594 | 1984 |

## Callback work and entry lateness

Extrema are reported independently. Values in parentheses are milliseconds on the PAL target.

| Workload | Maximum callback work CCK (ms), old → new | Maximum entry lateness CCK (ms), old → new |
| --- | ---: | ---: |
| cold-one | 55192.000 (15.561) → 53606.000 (15.114) | 2734.905 (0.771) → 2568.841 (0.724) |
| two | 56673.000 (15.978) → 53570.000 (15.103) | 2690.580 (0.759) → 2435.046 (0.687) |
| setup, all completed callbacks | unavailable → 56608.000 (15.960) | unavailable → 1242.140 (0.350) |

## Like-for-like whole-machine memory

| Cold-one measurement category | Before bytes | After bytes | Delta bytes |
| --- | ---: | ---: | ---: |
| Initialized Exec pool through restarted flight | 315,248 | 270,920 | -44,328 |
| Runtime: CIA timer start through restarted flight | 312,160 | 270,920 | -41,240 |

Both categories include resident OS/application/stack. Pre-Exec-pool bootstrap remains unmeasured. The cold-pool peak and runtime peak are separate measurements even when their new values coincide; neither is interchangeable with loaded-payload bytes.

Supplemental probe work and lateness extrema include both CCK and converted milliseconds in JSON. Never subtract unrelated maxima to manufacture a minimum deadline margin. Ordinary live-AI runs use the same input protocol and observers; CIA entropy means these are workload extrema, not paired per-tick timings. The canonical demo retains its fixed input/seed trajectory.

## Bounded display/ISR comparison

Each run requests 24 fields, checks 23 complete fields and uses ordinary physical start/serve controls after a one-time startup-phase wait. Every scene/DMA/ownership assertion remains enabled.

| Target | Handover margin CCK old → new | ms old → new | ISR bus interval max CCK old → new | ms old → new |
| --- | ---: | ---: | ---: | ---: |
| PAL | 13226 → 13231 | 3.729 → 3.730 | 626 → 628 | 0.176 → 0.177 |
| NTSC | 1892 → 1912 | 0.529 → 0.534 | 625 → 625 | 0.175 → 0.175 |

Handover means actual COPJMP strobe to physical field restart. ISR bus timing starts at first register-save write and ends at last RTE frame read; entry and final CPU tail are excluded. PAL 50 Hz / NTSC 60 Hz display timing is distinct from the simulation interval. NTSC uses 3,579,545 CCK/s.

## Supplemental dirty-HUD callbacks

One-time native fixture initialization sets points 4/3, WIN 5/2 and status 6. Subsequent ticks and status expiry run normally, with no intermediate state injection. Cache changes classify callbacks: 31=both points/WIN plus status; 16=status; 0=no HUD cache change. End0 is normal orientation; end1 is exchanged. The probe reads the product-selected PAL/NTSC simulation interval. Both end orientations are measured.

| Target/end | Fields mask | Samples old/new | Callback max CCK old → new | Minimum simulation headroom CCK old → new | ms old → new |
| --- | ---: | ---: | ---: | ---: | ---: |
| pal-0 | 0 | 51/52 | 27232 → 27620 | 31112.137 → 30711.137 | 8.772 → 8.659 |
| pal-0 | 16 | 2/2 | 40352 → 25860 | 18180.529 → 32690.529 | 5.126 → 9.217 |
| pal-0 | 31 | 2/2 | 61378 → 32828 | -2537.726 → 25728.274 | -0.715 → 7.254 |
| pal-1 | 0 | 51/52 | 27417 → 27811 | 30927.137 → 30520.137 | 8.719 → 8.605 |
| pal-1 | 16 | 2/2 | 40542 → 26018 | 17951.529 → 32678.529 | 5.061 → 9.213 |
| pal-1 | 31 | 2/2 | 61616 → 33011 | -3078.726 → 25370.274 | -0.868 → 7.153 |
| ntsc-0 | 0 | 50/52 | 27629 → 27669 | 31249.006 → 31197.006 | 8.730 → 8.715 |
| ntsc-0 | 16 | 2/2 | 41049 → 26490 | 17748.183 → 32674.183 | 4.958 → 9.128 |
| ntsc-0 | 31 | 2/2 | 62247 → 33403 | -2778.989 → 25556.011 | -0.776 → 7.139 |
| ntsc-1 | 0 | 50/52 | 27819 → 27868 | 31053.006 → 31010.006 | 8.675 → 8.663 |
| ntsc-1 | 16 | 2/2 | 41219 → 26646 | 17750.183 → 32672.183 | 4.959 → 9.127 |
| ntsc-1 | 31 | 2/2 | 62406 → 33592 | -3019.989 → 25710.011 | -0.844 → 7.182 |

The old product misses a simulation deadline in each supplemental dirty-HUD fixture. All new fixture callbacks meet it. These new observations expose coverage absent from the previous release gate; they are not silently discarded or described as old accepted checks. Unchanged-field maxima do not show a universal speedup. Native full-match/reset/end-exchange and all-bank visual/DMA checks provide complementary coverage.

The initial probe stopped on the old miss and used a PAL-only interval for NTSC; those local attempts are retained but excluded. The final common probe records deadline failures explicitly and reads the actual cadence. No existing gate assertion was relaxed.

## Bindings

- Full data and receipt hashes: [direct-hud-comparison.json](direct-hud-comparison.json).
- The comparison JSON binds the complete PR #27 report. [current.md](current.md) describes the later product and has separate coverage.
- Preserved accepted baseline: [pre-direct-hud-current.json](baselines/pre-direct-hud-current.json).
- Before development SHA256: `1a5286650df54e65d4a3339557b1b54f5a0a7c398fcd552b3c7537e14d547e72`.
- After development SHA256: `21578578dcce14bc38fb83db06ee242cd848f41f0b03f07a9217d11a87cfbc05`.

Raw emulator captures and executables remain private and ignored. PR #27 is merged; these measurements describe that product.

Full-gate and focused-check bindings: [direct-hud-validation.md](direct-hud-validation.md).
