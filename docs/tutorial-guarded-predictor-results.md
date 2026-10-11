# Guarded incoming preview results

The tutorial now requests an observational preview from the retained incoming
shot origin. Eligible active one-human flights use the actual shared input,
both-player gameplay, scene-finish and clock helpers. Unsupported origins use
original replay from the start. The exact request API retains complete-state
and ordered-output equality. No scheduler reserve or input cadence changed.
See [the design and alternatives](tutorial-guarded-predictor-design.md).

The reduced launch buffer is a preview seed; Play from here remains NOTREADY.
Resume restores the exact interrupted live state and reconciles physical input.
A playable alternative requires reconstruction to a complete original-core
boundary. The branch trial starts at the resolved immutable incoming origin;
the cold resolver still replays from the oldest retained checkpoint, potentially
match start. Outgoing ball previews exclude the next opponent response.

## Identity and selected gate

Campaign `10028cdf8b384c37bd77ea5bb6db74b5` completed on 2026-10-09:
`predictor-cpu` attempt000003, `predictor-pal` attempt000002,
`predictor-ntsc` attempt000001 and `incoming-flight-cpu` attempt000001 all passed
fresh. This is selected coverage; `acceptance_passed` is false and the full
native catalog is not covered.

- Runtime product source: `4e94ee1583d3ac7f296b6c09548aebecaec89232`.
- Observer source: `0495e7f80b0bcb1f567f94e79cffe0c67022167b`.
- Native development SHA256: `f24bb18c1a8b1443a67d951be7bdc77cca8f6578be65cfb7ea4b08d017e95a66`.
- Standalone SHA256: `788a827f1041edafbf0e83815967ed386802256380f8998fab2f575477282655`.
- CPU report SHA256: `f3cfa8e5757f7eba98417075246121bea58987cada9c7144a1ab12a2ec15edf7`.
- PAL report SHA256: `90c2e8585265c2ed8811c8859a6b84ce465b02d651fd1eafd3195185b5a01683`.
- NTSC report SHA256: `e688f99d52c253f6313c720fe2e04085bd2f440d0b3beaeedc49da586c733103`.

Raw reports remain outside Git under `build/tests/`; campaign attempts bind
source, compiled inputs, tool environment and evidence hashes. The execution
environment uses Python3.12.14, machine68k0.4.1 and Pillow12.3.0.

## Actual CPU correctness and cost

56 admitted comparisons cover three lower-end seeds, a naturally exchanged
upper-end context, held/released actions, two working-state poisons, central and
wide contacts, low-height net contacts and misses. Two additional irregular
envelope streams exercise clear/latch/pads/poll boundaries. Independently
executed original and reduced helpers agree on every required causal boundary,
input attempt/launch ledger, RNG call count, cursor, phase, termination and
8-byte path sample. Reduced execution showed no observed initial dependence on
the108 poisoned incidental bytes; admission inspects the intact full origin,
and this audit does not prohibit reads after a field is written.
Canonical/history memory and live sinks remain isolated. Incidental full final
states differ as allowed by the observational contract.

16 public API cases exercise four contexts at budgets1..4, full incoming cache,
active and completed projected-to-exact replacement, cancellation and stale
requests. 26 admission controls exercise rejection classes and register/store
isolation; safe fallback cases retain full318-byte and event equality. The
existing exact incoming proof also passed18 rows, four history boundaries,
endpoint queries and prefix-policy checks.

Compared logical calls consumed41,774,832 original versus29,030,664 candidate
CPU cycles: a30.51% reduction in this finite comparison, excluding admission.
Admission took858–860 cycles. Maximum observed projected public step was33,628
CPU cycles; API stack was208 bytes. These are not callback WCET bounds.
The normalized original core remains17,606 bytes; the shared predictor matches
between native and standalone at272 bytes, seven relocations and five external
branches (SHA256 `684cf9ca6f5db1d7b2863e59fade1fbb58175ba551e956017011daaa4d7831ef`).

## Native input, timing and publication

Both physical-input runs verify loaded hunks, complete paused318-byte state,
72-byte history metadata, retained recording, actual contact/miss observations,
sprite bytes and actual Copper publication. Captured native incoming envelopes
replayed through the original core agree through incoming resolution and the
available outgoing prefix. Complete outgoing state equality is relative to the
captured preview seed, not a playable edited-match checkpoint. Resume during
active prediction restores exact state/history without a new held-F edge.

| Finite observation | PAL | NTSC |
|---|---:|---:|
| Complete callbacks | 676 | 655 |
| Maximum callback CCK | 54,983 | 55,107 |
| Minimum simulation headroom CCK | 3,517.137 | 3,949.006 |
| Fresh-edit request to accepted contact seconds | 0.504373 | 0.460566 |
| Contact to dispatch return seconds | 0.001092 | 0.001075 |
| Dispatch return to COPJMP seconds | 0.128526 | 0.057666 |
| Fresh-edit request to COPJMP seconds | 0.633991 | 0.519307 |
| Cold miss publication seconds | 1.988185 | 1.932765 |
| Alignment publication seconds | 3.143164 | 2.964687 |
| Keyboard ACK hold CCK | 505–520 | 500–630 |
| Maximum actual keyboard-poll entry gap CCK | 39,463 | 41,205 |
| Maximum physical input to matrix CCK | 31,644 | 29,038 |
| Maximum observed stack bytes | 320 | 260 |
| Chip free / largest free block bytes | 62,616 / 62,032 | 71,576 / 70,992 |

Contact intervals use observed bus boundaries; their small instruction tails
remain measurement uncertainty. Receive-ready ICR gaps are separately39,465
and41,200CCK. Dropped notifications were zero in both successful runs.
Earlier live fresh-edit observations0.697s PAL and0.683s NTSC are unpaired
historical workloads. These new measurements establish neither a paired
speedup nor universal headroom/input bounds.

## Resources, failures and remaining gates

Development executable210,028 bytes; loaded code58,840, data112,700 and
BSS150,848 bytes. Against the previous incoming-flight product this adds332
code bytes and four loaded BSS bytes. Six logical metadata bytes consume two
existing padding bytes. Preview storage is10,980 bytes; state remains318.
[The recorded resource summary](metrics/current.md) is explicitly incomplete:
`native_metrics.py --require-runtime --record` exited1 because the eight standard
profiles and cold-loading coverage were not collected for this product. Both
tracked summaries were refreshed; selected diagnostics cannot fill those gates.

CPU attempt000001 failed receipt finalization because the runner replaced the
recorded environment; preserving it fixed provenance without changing runtime.
PAL attempt000001 lost402 observer notifications during court-copy work and
remains failed. Its raw capture is retained in
`/tmp/ctennis-predictor-failures/10028cdf8b384c37bd77ea5bb6db74b5-pal-000001/`
(compressed trace SHA256
`b4ec519f01a55f51b915c1416f699673d7eb478563446e46e760aad5be4cf698`).
Read-only court/footer entry drain stops corrected capture loss; they do not
write guest state, advance its clock or select callbacks. The fresh runs above
supersede no failure silently.

The original56-row fixture obtained no scene-clamp, outgoing-out/fault or
tick-wrap witness and used only seedACE1 for natural upper-end coverage. The
supplement below addresses these particular CPU partitions; it does not add
native timing observations for those boundaries.
Independent correctness reviewer `ratio32_review` cleared the refreshed CPU
receipts after verifying277 predictor and211 exact-incoming bindings and
rechecking58 raw pairs. Timing reviewer `predictor_timing_review` cleared both
native receipts after independently verifying334 evidence hashes per region,
all callback/input arithmetic, frozen state, resume and publication intervals.
All256 host unit tests pass. `git diff --check` passes; the documentation-only
metrics check rejects the explicitly incomplete summary as expected.
Appearance, general scheduling/input bounds,
standard resource profiles, cold ADF and full release acceptance remain held.
This result authorizes neither merge nor release.

## Supplemental boundary coverage

Focused campaign `6624faa8e27d40838022715a1917b0fb` completed fresh
`predictor-boundaries-cpu` attempt000002 on 2026-10-09. Supplemental report
SHA256 `556d9addeb629393f39290ec4ca695f0d035beeaaebf558ee0c23e6bcc3430a7`.
Harness/validator source: `07d96ae2f45e8b634d7211652553169808009d61`.
The stronger extent requires exact guard identities, register preservation and
successful byte-audit verdicts; attempt000001 passed before this hardening and
was rerun to bind the final validator. Execution used the selected case only:
`RUST_LOG=info /tmp/ctennis-shared-core-python/bin/python scripts/native_acceptance.py --resume --campaign 6624faa8e27d40838022715a1917b0fb --start --case predictor-boundaries-cpu`.

The supplemental proof changes only CPU harness/catalog code and documentation.
It rebuilds and requires the same native/standalone SHA256 identities above,
then uses independently initialized original and projected executions. The
original56-row and native measurements remain evidence for their original
extent; PAL/NTSC evidence is reused for unchanged product and observer inputs.
The timing reviewer verified all668 prior native evidence bindings still match.

Five once-declared complete incoming geometries exercise scene clamp with
tick255→0, incoming outside, incoming special-net reflection, incoming court-out
bounce, and outgoing court-out following actual accepted human contact and
unmodified launch derivation. Each has held/released input and two initial
poisons. The original/projected comparison still checks every causal logical
boundary, attempts/launches, RNG calls, exact samples, cursors and isolation.
Public cached request/worker fixtures run budgets1..4, compare both variants,
then replace projected requests with exact requests and compare complete318
and ordered outputs. No oracle state is injected during logical execution.

These are declared API-boundary/cache fixtures, not naturally discovered
opponent launches and not cold-resolver tests. All318 origin bytes and cache
metadata are initialized before the first tested request. Actual dispatch
produces BALL192/COURT193 before scene writes COURT194; tick samples cross255→0
while the logical cursor stays independent. Incoming terminal flags yield
NO_CONTACT without a human launch. Outgoing OUT requires an actual phase1
human return and subsequent original ball ticks; outgoing velocities are never
patched after launch.

Five separate trials start from complete terminals produced by these original
executions: admission rejects class7, runs zero predictor ticks and preserves
full original state/events. Two additional once-declared serve retry latches at
an actual outside terminal check first/second fault fallback: queued status5/6,
point-pause stage, retry latch and no-point/point award respectively. Visible
fault announcements and sound lifecycle are not tested by this supplement.
Human serve kind3 remains excluded from projection through the existing guard.

Additional natural upper-end discovery reaches seed1 at2,788 dispatches and
seedBEEF at1,758, using actual controls and end exchange. Both add held/released
poison pairs and public budgets1..4 with existing cache/replacement/isolation
checks. Together with the earlier ACE1 fixture this is three natural upper
seeds, not exhaustive AI/gameplay state coverage. Upper-origin trials include
an outgoing OUT with seed1 and NET with seedBEEF. Scene-clamp and specifically
placed terminal geometries remain declared CPU cases; none adds native timing
witnesses. Maximum observed new projected public step is33,716 CPU cycles in
the upper seed1 case; declared exact replacement peaks at35,524. These are
finite observed maxima, not scheduler admission or WCET bounds.

There are28 admitted comparison pairs,20 declared cached API cases and eight
additional natural-upper API cases, five generated-terminal fallback pairs,
two declared fault-latch fallback pairs and the26 admission controls. Eleven
read-only altered/lost-evidence controls are rejected by the extent validator,
including missing clamp/wrap/contact, duplicate guards, lost budget/upper seed,
wrong fault status, lost exact fallback and failed byte audits.

An initial orchestration attempt (`1c02b5c4019d4aa6a18ac219d87b09cb`) omitted
the explicit selected case at startup and ran only host units. All256 tests
passed, but its receipt was rejected for dependency drift; the campaign stopped
before any native case. That failed campaign remains retained. The corrected
selected campaign above is separate and does not turn that failure into a pass.
No broad or new native campaign was run.

Independent `ratio32_review` reduced all28 admitted raw pairs and the public
and exact fallback evidence, then verified all229 final receipt bindings and
unchanged byte audits. The corrected design/results documentation is cleared
for draft publication. All256 final host unit tests and diff checks pass.
The documentation-only metrics check still rejects the recorded incomplete
resource summary; no missing standard resource or release gate is cleared.

## Cold origin caching recommendation

The top-to-bottom review overlooked live capture of the latest incoming origin.
It optimized contact work after cache resolution without adequately considering
this smaller cold-start improvement. Existing128 shot slots hold12-byte human
episode/serve indexes, not complete snapshots; the cold resolver scans from
the oldest checkpoint to discover the preceding AI launch. Repeated edits
already reuse the resolved318-byte incoming cache.

Recommend a separately reviewed latest opponent post-launch boundary cursor
first:8 bytes plus identity/validity bookkeeping, naming the boundary after
the launch operation. Reconstruct that target with at most63 recorded operations
from the nearest sparse checkpoint at/before it. The existing pre-operation
event cursor instead can require64 operations across a checkpoint alignment.
A complete latest origin needs330 bytes
plus bookkeeping and one318-byte post-dispatch copy per qualifying launch
(318 bytes read and318 written; cycles remain unmeasured). Complete origins
for all128 existing slots need42,240 bytes plus staging/bookkeeping, substantial
beside observed PAL chip memory. No runtime cache extension is implemented.

Capture only in live recording, publish after full dispatch/service/history
advancement, and retain match/end/version identity. Seek/preview hooks must not
overwrite the live cache. Evict dependent launch identities with history; a
snapshot does not restore expired input/entropy records or extend retention.
Historical browsing still needs associations or cold fallback, and playable
branches still require exact original-core reconstruction. See [the design's
storage comparison and ownership requirements](tutorial-guarded-predictor-design.md#cold-origin-recommendation-overlooked-alternative).
