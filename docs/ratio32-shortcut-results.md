# Exact divisor-32 shortcut: implementation and measured scope

The shared native/standalone core now uses a table-free `game_ratio32` for its
ball displacement and height calls. The general variable divider is unchanged.
This implements the [reviewed derivation](ball-query-math-proof.md), including
legacy overflow: `96*90/32` returns 254, not the ordinary quotient's byte 14.
Runtime source commit: `d6146ff696696aba5e7a466169ea01f1defcd75f` (based on reviewed PR38 head
`5623420afbbcb347b823c09b0f8e94d601516e34`). PR38 remains unmerged.

## Contract and exhaustive comparisons

Inputs are masked to bytes; D0 returns the zero-extended result, D2 is 32,
D3 is the result's low bit, D4 is `$0000ffff`, and final CCR is 4 for zero,
otherwise 0, including cleared X. D1's low word is scratch; its high word is
zero. D5–D7 and address registers are preserved. The displacement caller's
complete returned D1 matches the original. Only the two fixed-divisor call sites change.

`scripts/run_ratio32_proof.py` calls assembled instructions, comparing the old
and new native products and the actual standalone core. It checks:

- All 65,536 byte factor pairs, all 65,536 word products against both emitted
  dividers, and all 65,536 signed displacement velocity/phase pairs.
- Poisoned preserved registers and incoming CCR, with explicit all-32-CCR cases.
- 4,112 one/two-player private-core operations, full 318-byte state, ordered
  outputs, owners and canaries; no intermediate expected state injection.
- Retained PAL and NTSC recordings, 818 logical operations each, comparing old
  native, new native and relocated standalone state/events; the native snapshot
  at operation 552 in each region.
- Byte-identical general divider and normalized native/standalone shared code:
  17,606 bytes, seven relocations, fourteen sink branches,
  SHA256 `99c543c170c036137be81d07ebd30b522ef3abdff04bd7b1af38f00047bb99d5`.

The completed selected campaign `b132585a734f4aeea397cec54bf876ee` passed
236 host tests, `ratio32-cpu`, `tutorial-court-pal` and `tutorial-court-ntsc`.
An independent reviewer reran the exhaustive arithmetic and full-state replay
comparisons and checked the completed native prediction receipts.

| Emitted helper domain | Cases | Original CPU cycles | Shortcut CPU cycles | Saved cycles |
| --- | ---: | ---: | ---: | ---: |
| Product below 8,192 | 25,461 | 934–1,318 | 170–186 | 764–1,132 |
| Legacy overflow | 40,075 | 974–1,316 | 274–288 | 698–1,030 |

Every applicable factor pair is faster. These CPU-runner counts exclude Amiga
bus contention. Removing the caller's `MOVEQ #32` saves another four cycles;
that instruction is excluded from the original helper column.

## Native prediction observations

Fresh bounded PAL/NTSC checks exercised physical input, pause isolation, actual
fresh edits, completed generation/variant publication, Copper markers, sprite
headers, paths and resume. The old and new observations are finite runs with
different callback phases; they are not paired per-tick performance trials.

| Native observation, old → new | PAL | NTSC |
| --- | --- | --- |
| Fresh endpoint, provider seconds | 0.452152 → 0.414530 | 0.439431 → 0.388355 |
| Movement input → player, provider seconds | 0.027817 → 0.026383 | 0.036955 → 0.034455 |
| Held choice → existing endpoint, provider seconds | 0.019087 → 0.037354 | 0.034227 → 0.031724 |
| Complete callbacks | 655 → 619 | 613 → 601 |
| Maximum callback work, CCK | 54,937 → 54,921 | 55,028 → 55,021 |
| Minimum absolute headroom, CCK | 3,573.137 → 3,583.137 | 4,023.006 → 4,023.006 |
| Observed stack span, bytes | 316 → 320 | 320 → 320 |
| Free chip RAM, bytes | 70,488 → 70,408 | 79,448 → 79,368 |
| Largest free block, bytes | 69,904 → 69,824 | 78,864 → 78,784 |

The provider uses the PAL clock for its seconds field in both regions. NTSC
physical seconds multiply these durations by `3546895/3579545`: fresh endpoint
is approximately 0.435423 → 0.384812 seconds. Publication timing is not pixel
scanout timing. The slower PAL held-choice observation prevents a claim that
every UI latency improved.

## Bounded native live-play costs

Campaign `a04dcae87f194f0893acd9152b23144e` exercises physical one-player
selection and serve input, with a two-second ball window, no state injection and
309 actual applicable helper calls per case. These are independently measured
CIA-entropy workloads; the exhaustive CPU proof supplies paired correctness.
The timing interval uses the first stack write through the final RTS stack read,
includes bus contention and interrupts, and excludes entry/exit tails.

| Native helper CCK, min / median / p95 / max | Original | Shortcut |
| --- | --- | --- |
| PAL, 309 calls each | 495 / 563 / 629 / 643 | 87 / 89 / 92 / 94 |
| NTSC, 309 calls each | 509 / 566 / 632 / 659 | 87 / 90 / 92 / 97 |

| Complete live callback CCK, min / median / p95 / max | Original | Shortcut |
| --- | --- | --- |
| PAL, 119 callbacks each | 21,878 / 25,203 / 26,396 / 30,802 | 21,973 / 23,775 / 24,916 / 30,779 |
| NTSC, 119 original / 120 shortcut | 22,129 / 25,507 / 26,661 / 31,230 | 22,165 / 24,145 / 24,967 / 31,210 |

The callback distributions include other game work and differ in phase and
trajectory. They do not establish universal callback savings or frame rate.
The live observer's tutorial-active freeze guard has zero active boundaries;
pause isolation is established by the fresh prediction checks above.

## Resources and product identity

Loaded CODE grows 56,388 → 56,472 bytes (+84); DATA stays 112,700 and BSS
145,420. Normalized shared code grows by 82 bytes. The helper is 86 bytes and
its two callers lose four bytes. There is no table or dynamic allocation.
Observed whole-machine free-chip loss is 80 bytes, reflecting allocation
alignment rather than a claim that executable bytes equal machine RAM.

Development executable: 205,908 → 206,012 bytes (+104, including symbols).
Symbol-stripped release: 175,004 → 175,088 bytes (+84). This is a packaging
measurement, not cold-release boot acceptance.

- Original native SHA256:
  `9bfd85797f8b3a997cff8fa1489be8bfdfca45a0396001935da019c3fc117454`.
- Candidate native SHA256:
  `158f25910598de48ca266b9af459eda779cc3ccee3fac861e0690fb920e0698d`.
- Candidate standalone SHA256:
  `2b82218b3eb31909e3d694cd7bf4fae5dcc34ca5b62e43687ed47029d96e672b`.
- Candidate stripped release SHA256:
  `ff0f42d521d27f1b5e8521a3e5826a542259355306ae30c6f19e36a0d58b1cf7`.

## Retained failures and limits

Failed attempts remain recorded. The frozen physics fixture initially rejected
the deliberate call substitution; it now normalizes only that exact call for
its existing surrounding-code hash. Host cache changes caused two dependency
closure rejections despite passing tests; the closure guard remains strict.
The first native check rejected its old shared-code identity and was refreshed
to the measured identity above.

A PAL held-input fixture reached the right boundary and therefore produced no
fresh edit. Its replacement moves left and requires both coordinates and the
actual generation to change; publication checks remain strict. The failed
capture was preserved. The first live timing observer used a nonexistent span
field; it was corrected to the actual completed `elapsed_bus_cck` field. These
are observer failures, not evidence of arithmetic correctness. Workspace disk
exhaustion and a missing explicit baseline environment stopped later starts;
all evidence was preserved and neither attempt counts as a pass.

After the completed native campaign, current-core validators and their positive
fixtures were refreshed only to the measured extent/hash above. The direct host
unit suite passed all 236 tests again. Historical product profilers retain their
original identities; these edits do not certify new retained/seek captures.

`python scripts/native_metrics.py --require-runtime --record` exited 1 because
standard resource coverage is unmeasured. Both tracked current reports now name
the candidate product and explicitly record incomplete coverage. The focused
prediction/live measurements above do not fill that standard coverage.

Full release acceptance, retained-preview native recapture and cold stripped
release boot were not run in this focused change. The resource report's missing
standard runtime coverage must remain explicit. The guarded landing query is a
separate next task: it cannot skip player/contact/AI/RNG ticks of the full match
core merely because a ball-only endpoint can be found more cheaply.

## Local receipt identities

Raw captures, ROMs, executables and runtime reports remain private and ignored.
These hashes identify the completed receipt JSON files retained locally:

| Receipt | SHA256 |
| --- | --- |
| `ratio32-cpu` | `c95c564e4fb536d9f132314ea00dd49a3c59f49e24622c076979eca555025c84` |
| `tutorial-court-pal` | `b87dbac74d7e86e04adf50e10488cf326ccfe894cd79d773e7c144b31ac7f6e6` |
| `tutorial-court-ntsc` | `d30928e62277fcf3df1641cca86e02da101109de6e65b4d7b0c7f20fe62b0f2d` |
| `ratio32-live-baseline-pal` | `5c71a753a05f5843c1289b63e4246a6ad1b94989b8c0fd5624ca1fd732470b61` |
| `ratio32-live-baseline-ntsc` | `63f4eb5b2cbd10123ec88e38ca73970fadab4c4b0ad4b139ec0aec6d1fa23831` |
| `ratio32-live-candidate-pal` | `a5d689066c8f0e4969d5a1b7deacecf2b6185fdf0bf9c483f0c280929121799b` |
| `ratio32-live-candidate-ntsc` | `5137a5a4d27917077aa223f96b73069d12d6c18bb6323ed3bb4c93490c58bbea` |
