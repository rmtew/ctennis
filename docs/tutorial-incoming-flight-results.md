# Incoming/contact/outgoing delivery evidence

This draft changes the normal tutorial ball sequence to opponent incoming,
actual edited human contact or miss, then outgoing flight through the first
landing, flagged net collision or out. The actual dispatcher determines contact
eligibility and timing. After human launch the original ball tick supplies dense
samples without the next opponent response. Terminal samples dwell for 30
nominal callbacks before the sequence repeats. PR38's appearance and release
hold remains; this is focused evidence, not release approval.

## Identity and completed checks

Product commit: `9d2ea596cb3e944bc8df15638fcb314bb5473bde`.
Development executable SHA256:
`de3d6aba52df919914d3df94701a32fbe43462ff8004fadd76154b031e25bab6`.
Standalone SHA256:
`b2da208762903b7788f281018592b6bd0e24cd2e18d7d051e638715d5ccc02d7`.

The finite campaign `155e9d645e064b5ca917853955f89be3` completed all three
selected cases (`incoming-flight-cpu`, `incoming-flight-pal`,
`incoming-flight-ntsc`) with pass. Its `acceptance_passed` is false: the standard
release catalog was not run. Local receipts are in
`build/acceptance/campaigns/155e9d645e064b5ca917853955f89be3/report.json`
and `build/tests/incoming-flight-{cpu,native-pal,native-ntsc}/report.json`.
Raw transcripts remain private and outside Git.

The CPU proof runs actual recorded logical bodies until the human launch and
actual ball ticks afterward. Across 18 trials and alternate poisoned working
states it compares every completed 318-byte private state, every path sample,
ordered events and final state, with protected canonical/history/live-event
storage unchanged at public yields. It proves changed contact phases 52, 46,
41 and 33 plus misses, identical READY reuse, ten unfinished-work restarts,
stale-generation rejection, mismatched-context cold resolution and current
incoming expiry after real return/miss. Requested XY remains actual XY; the
movement code rejects directional proposals rather than clamping existing XY.

The native probes load the unmodified shipping executable on PAL and NTSC
A500/68000/OCS/512 KB, use physical inputs to pause an incoming episode and edit
placement, and verify actual COPJMP publication, native sprite headers/images,
an outgoing sample and terminal-to-zero repeat. Full frozen 318-byte state,
72-byte history metadata and live backup are guarded at completed boundaries.
Both stack stores and matching emitted RTS reads are observed. These checks
verify published RAM, not complete sprite DMA or user appearance acceptance.

`python scripts/check_shared_core_bytes.py` passed: 17,606 normalized shared
bytes, seven relocations and fourteen named synchronous sink branches each;
SHA256 `99c543c170c036137be81d07ebd30b522ef3abdff04bd7b1af38f00047bb99d5`.
The actual core remains shared. Host suite: 236 passed.

## Measured extent

| Measurement | PAL | NTSC |
|---|---:|---:|
| Initial cold held publication | 2.050 s | 1.811 s |
| 95-pixel physical held edit through publication | 3.355 s | 3.227 s |
| Fresh one-pixel D edit through publication | 0.746 s | 0.639 s |
| Completed callbacks | 681 | 654 |
| Largest complete callback | 54,383 CCK | 54,500 CCK |
| Minimum observed absolute deadline headroom | 4,062.137 CCK | 4,557.006 CCK |
| Observed stack high-water | 324 B | 320 B |
| Whole-machine chip free / largest block | 65,480 / 64,896 B | 74,440 / 73,856 B |

Fresh edits reuse immutable resolved incoming context even while the other
alternative is unfinished. The measured accepted path is 121 samples: initial,
52 incoming dispatches and 68 outgoing phases, ending at actual landing. The
initial placement misses. The preceding `5fab776` measurements were 2.060 s
PAL and 1.836 s NTSC for fresh edits; these are historical independent native
runs with live entropy, not paired per-tick randomness or a universal speedup.

Static current totals: executable 206,772 B, code 56,964 B, data 112,700 B,
BSS 149,856 B, loaded payload 319,520 B. Relative to PR40: executable +760 B,
code +492 B, data unchanged, BSS +4,436 B and loaded payload +4,928 B. Paths
expand to two 513-sample buffers; incoming state adds 318 B. Match tick remains
a wrapping byte; separate counters bound incoming and outgoing segments.

`python scripts/native_metrics.py --require-runtime --record` regenerated both
tracked reports and exited 1 with explicit incomplete coverage: all eight
standard resource profiles and cold loading remain unmeasured for this product.
Focused measurements above do not fill those standard profiles. The subsequent
`--check` also rejects the incomplete accepted report; this is an open gate,
not a successful resource check.

## Preserved failures and remaining gates

Earlier campaigns `c543f27d86dd4b7bb2cb47469bf8bdae` and
`9e2b6bbc23d64ca78accd78b2f5ea0da` hit diagnostic raw-capture caps. Their
receipts remain under `build/tests/incoming-flight-failures/`; they are failures,
not passes. The second exposed a READY-cache initial sample placed in the wrong
variant, now fixed and differentially covered. Campaign
`59d47474183c4969980ef6b7307f9945` passed selected cases for the preceding
product; its historical copies remain under `incoming-flight-baselines/5fab776`.

Before merge/release:

- [ ] Independent final source and receipt review; parent coordinates reviewers.
- [ ] Extend exact-cap-256, wrapped attempt ring/controller selection, upper human
  and exchanged-end proofs, plus short/rejected/fault and transition workloads.
- [ ] Migrate older mandatory preview fixtures from their 256-sample/full-core
  outgoing assumptions and run the affected standard native gates.
- [ ] Complete standard resource coverage, cold stripped-ADF loading, appearance
  approval and the full finite release gate. Do not merge ahead of these holds.

The integrator owns implementation, evidence and follow-up integration. This
slice keeps dense original ticks; PR40's guarded endpoint query is not integrated
into shipping because it does not eliminate dense sample cost by itself. A cold
incoming cursor hint remains an optional separately proved optimization; initial
entry latency above remains open. No trail/sprite experiments or scheduling
changes are included. No merge has been requested or performed.
