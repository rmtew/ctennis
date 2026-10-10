# Existing next-query descriptor experiment

Base is PR49 `4c84c05225a4e1dc009f3369d55816853f028878`. Its runtime is
identical to PR48. This experiment does not restore the withdrawn top-up.

## Dependencies and retained state

Operation selection already retains each branch's cursor, synthetic phase,
prime bit, launch seed, flight phase, query workspace stage, readiness and
outcome. The 318-byte private branch persists across public grants; only its
72-byte history tail is restored at ownership boundaries. Incoming prefixes
already group up to four envelopes and stop at dispatch. Prime, resolution and
outgoing flight each receive one operation.

Incoming classification depends on lifecycle, score initialization, command,
restart, entropy, mode, score/AI flags, player owners and phases, contact/flight
masks, court overlap and serve clock. Its poll classification also depends on
lifecycle, score initialization, command, restart, entropy and mode. A prefix
depends on cursor/phase progression and available interval minus service/margin.
The actual admission additionally reads current clock, beam and visible latch.
The existing cost classes remain hypotheses, not WCET measurements.

A separate saved complete operation/cost descriptor would duplicate retained
state and require updates after all legacy and coherent operations, synthetic
padding, result transitions and query mutations. Updating it on every grant
could repeat rather than remove classification. This experiment therefore uses
the existing partial next-query descriptor directly, without new storage or key
comparison: selected launch saved, flight phase at least4, endpoint not attempted.
These necessary conditions are checked inline before the full endpoint wrapper.

The retained narrow PR49 baselines call that wrapper229/239 times before
readiness, spanning26.437208/27.519419 ms PAL/NTSC inclusive and
22.574111/23.501870 ms exclusive. Those spans overlap scheduling/support;
they are not additional accounting buckets or promised savings. This is a
concrete avoidable repeated check, while total support is not all recoverable.

## Refusal invalidation and reconsideration

No refusal or live admission result is cached. Every root visit reads the
current selected branch. A missing launch, phase below4 or attempted query takes
the original preview fallback. A positive result enters the unchanged full API,
which still checks generation/sentinel, variant, ownership, status, prime,
workspace phase, selection, readiness/outcome and the upper phase bound. Actual
endpoint admission still uses current4000E cost, timer, beam, latch, service and
margin. No delay, quota or reservation is introduced.

| Authoritative transition | Reconsideration |
|---|---|
| New request, reuse, placement prepare | Clear branch launch/attempt/readiness bookkeeping; existing root generation/presentation checks apply. |
| Actual launch capture | Publish saved immutable branch seed and launch-saved flag. |
| Actual outgoing flight | Advance retained flight phase; phase4 becomes eligible on the next root visit. |
| Query completion or rejection | Publish attempted; successful completion also publishes readiness/outcome. |
| Cancel or history mutation/invalidation | Retire generation and clear launch/attempt/readiness and query workspace. |
| Variant selection | Index current variant each visit; no previous branch key survives. |
| Prime, query workspace or status change | Positive full API validates current state; negative necessary conditions cannot accept work. |
| History seek/replay or active private owner | Existing root guards and full API selection validation remain. |
| Menu, placement producer, due animation | Existing earlier root priority remains. |
| Timer/beam/latch, keyboard ACK or presentation change | Existing live admission and service pumps reconsider on each visit. |

The negative gates only skip a read-only wrapper that would return zero. They
preserve its fallback, residual rotation, held/released branch fairness and
exact-resume separation. Endpoint-first priority remains for positive cases.
Presentation IRQ preserves the registers and does not mutate these query fields.

## Verification scope

Runtime commit `72388799d459786b0df9ad3dfc945afd6f4742bd` adds44 loaded code
bytes and no BSS/data allocation. Development executable SHA256:
`44886e1d5f18ebe55151a9b43cc288f2c231c22420c3493ee956c641a05351cf`.

Actual68000 proof report:
`build/tests/next-operation-cpu/14207405c70443219a3a7777cbc1d25c/report.json`.
All658 fixtures pass against original PR49, a layout-matched padded original and
candidate. Both variants, phases0/3/4/255/256, launch/attempt/readiness/outcome,
workspace stages0–3, generation/presentation, seek/replay, producer and menu
routes are initialized once. Three actual root calls are followed by actual
cancel and invalidate APIs. Complete owner bytes, ordered outputs and root
state agree; original/reference cycles match. A declared4000E gap refuses bodies
before clock/MMIO: these are routing/mutation fixtures, not hardware timing,
universal reachability or a native deadline proof. Phases3/4 test the exact
eligibility boundary; actual progression is covered by matched native execution.

Matched native campaign `8c12a251abf942eb8aa22d66cb4942e1` uses the same
complete saved machine, controls and deterministic input schedule for original
baseline replay and candidate. Only the complete root-owner code range changes;
padding is unreachable. Original and padded code match outside that range, with
all symbols and hunk sizes equal. The frozen original, padded reference and
candidate products and raw receipts remain outside Git.

Native timings, exhaustive disjoint accounting and the final retention decision
will be recorded after the campaign closes. Existing unaffected receipts remain
reused; no broad duplicate campaign is requested. Existing appearance, resource,
deadline, physical-resume and full-release holds remain.
