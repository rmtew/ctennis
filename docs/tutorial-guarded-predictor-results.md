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

No scene-clamp, outgoing-out/fault or tick-wrap witness was obtained. Natural
upper-end coverage uses only seedACE1; broader upper seeds remain unproved.
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
