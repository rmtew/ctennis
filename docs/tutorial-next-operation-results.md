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

The first campaign `8c12a251abf942eb8aa22d66cb4942e1` failed before any latency
result: its PAL20–32ms D hold fell between actual control samples at17.787953
and34.613091ms. Physical press/release ACKs did retire. Immutable failure is
`build/tests/next-operation-matched-pal/efdcefb84d864fe1a7f8ff718d1b4c1d/failure.json`.
The fixed press was changed to28ms for both regions with the same12ms hold;
no runtime or adaptive measured-pass scheduling changed.

Matched native campaign `cea7ce21b5db473fae91b5928a60975b` uses the same
complete saved machine, controls and deterministic input schedule for original
baseline replay and candidate. Only the complete root-owner code range changes;
padding is unreachable. Candidate and padded-original code match outside that
range, with all other symbols and hunk sizes equal. The CPU proof separately
qualifies frozen PR49 against padded-original behavior and cycles. The frozen original, padded reference and
candidate products and raw receipts remain outside Git.

The campaign closes with both selected cases passed, not full acceptance.
Baseline1 and baseline2 replay objects agree exactly. All passes accept the same
single new-generation `(98,152,variant0)` request, retain frozen canonical,
history and records, retire physical press/release ACK and publish the same
nonzero held endpoint through actual completed banks/native sprites at COPJMP.
This is publication, not first scanout. The fixed observation window is1.2s with
at most30ms owner-closure tail, with no adaptive latency stop.

| Region | Original COPJMP ms | Candidate ms | Change |
|---|---:|---:|---:|
| PAL |511.533891|491.500312|−20.033579|
| NTSC |484.964430|484.965547|+0.001117 (4 CCK)|

The minimal gate is **retained**: this matched PAL workload demonstrates a useful
publication improvement and NTSC is effectively neutral. Readiness advances
5.004095ms PAL and1.190095ms NTSC. Publication phase absorbs NTSC's advance;
PAL's shorter known-to-publication suffix contributes15.029484ms of its gain.
The entire20ms cannot be assigned directly to removed wrapper execution.
These are finite matched pairs, not a promise for other states/schedules.

Both regions execute216 logical operations and48 actual dispatches before
readiness. Public grants change110→89 PAL and85→84 NTSC as the clock schedule
changes. Endpoint wrapper calls fall227→14 PAL and254→13 NTSC; their inclusive
spans fall26.070972→1.949029ms and29.229972→1.803861ms. Exclusive wrapper spans
fall22.230430→1.709382ms and24.951216→1.584838ms. These diagnostics already
overlap support; they are never added as extra latency buckets. The gates also
have a cost: positive CPU fixtures add118 cycles while negative routes save
558–924 cycles. Unchanged early exclusions have zero cycle difference.

## Non-overlapping elapsed accounting

Every integer CCK from scheduled physical press through qualifying COPJMP is
assigned once by the established nested-span priority. Endpoint-known is the
actual new-generation held-ready store after request clear; point/outcome stores
precede it in unchanged code. Its suffix is removed from all other buckets.
Observed call spans include IRQ; instruction tails, outside-call gaps and missing
contexts remain unclassified. Outside-callback time is not necessarily idle or
recoverable. Cost classes are not universal bounds.

| Exclusive elapsed partition, ms | PAL original | PAL candidate | NTSC original | NTSC candidate |
|---|---:|---:|---:|---:|
| Actual mathematics before known |60.048296|59.997265|59.870458|59.860122|
| Scheduling/preview support before known |262.838342|248.549224|258.961125|246.263422|
| Hardware service/display production before known |103.666728|111.654842|100.733752|110.973322|
| Mandatory callback/controls/requests before known |43.967188|43.972545|42.810469|42.806278|
| Unclassified before known |11.783264|13.125847|11.690033|12.972598|
| Known-ready store to qualified COPJMP |29.230073|14.200590|10.898592|12.089805|
| Total |511.533891|491.500312|484.964430|484.965547|

The measured aggregate support reduction is14.289118ms PAL and12.697703ms
NTSC. Hardware-service/display spans rise as the execution schedule changes;
the causal conclusion is limited to this complete treatment and matched inputs,
not independent subtraction of unchanged service maxima.

Fresh immutable reports:
`build/tests/next-operation-matched-pal/d25583bb5cfb488aa60cb3731b52dd05/report.json`
and `build/tests/next-operation-matched-ntsc/497248162e2f4373b5326ab0723befb8/report.json`.
The committed `docs/evidence/tutorial-latency/next-operation-summary.json`
binds reports, exact product, raw traces, saved anchors and reproducible reducer.
`next-operation-custody.json` binds retained private files, including failure.
Raw artifacts/ROM stay outside Git; no Library uploads.

Existing unaffected receipts remain reused; no broad duplicate campaign was run.
The endpoint API, classifier, game/preview bodies, rendering and input code are
unchanged. This does not newly certify all asynchronous fairness/ACK edges,
normative transport/deadline bounds, physical exact resume or full release.
Existing appearance, resource, deadline, physical-resume and full-release holds
remain; no merge or release is authorized by these selected checks.

Independent source, CPU, native and accounting review clears retaining the gate
within this scope. It independently recomputed both partitions, checked all882
CPU evidence bindings and327 per native region, and verified all799 retained
custody files. It distinguishes declared phase4 routing from physical phase
progression and notes unchanged active-owner exclusion was not an added fixture.

`python3 scripts/native_metrics.py --require-runtime --record` records the
current static product and exits1 for incomplete existing runtime coverage.
Both tracked metric files are updated together; no resource or full gate pass is
claimed. Compared with the actual PR49 product, this experiment adds44 code
bytes, whereas the older tracked metric product comparison includes earlier
changes as well. No duplicate resource collectors were started.
