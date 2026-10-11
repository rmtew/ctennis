# Bounded preparation-to-dispatch top-up experiment

The experiment is **withdrawn**. Neither matched region establishes a useful
physical-input-to-endpoint-publication improvement. The final runtime files are
identical to PR48 head `8b99f1798801c2e4834cd548afa42ec8a8b917e0`.
Experimental commits remain available for review; this is a draft result stacked
on PR48, not release approval or a change to PR45 publication.

## What was already grouped

Inspection of `preview.s`, `preview_predictor.s` and `tutorial_deadline.s` found
that incoming prefixes already group up to four actual record envelopes. A
dispatch ends the planned prefix. Prime, resolution and outgoing flight receive
one operation. The complete 318-byte private branch persists in place; it is not
copied at each step. Within a grant the worker already retains A5 and private
ownership. Public return restores only 72 bytes of history metadata.

The retained PR48 matched traces show216 logical operations and48 dispatches
before endpoint readiness in both regions. PAL requires 112 public grants,
including 35 dispatch-only grants and 28 preparation3-only grants; NTSC requires 84,
including 24 dispatch-only grants and 27 preparation3-only grants. There is only
one prime grant. Prime batching therefore cannot explain the main cost here.

Measured scheduling/preview support is a dominant aggregate (approximately
256.56/261.75 ms in PR48's preserved PAL/NTSC captures). That aggregate includes
useful checks and support, not a proven recoverable budget. Actual mathematics,
mandatory service, display work and unclassified gaps remain separate. Repeated
declined owners overlap this aggregate; they are never added as another bucket.

## Bounded design and refusal reconsideration

Commit `54cae13e47861d6093fcf513a20b68cfeb91c369` adds a root-owned entry with a
single possible dispatch top-up after actual preparation. It retains the existing
four-operation total cap and complete 1,000E/4,000E/10,000E hypotheses. It does not
raise quotas, lower reservations or insert delays. Every actual body, cursor
advance, lifecycle check, launch capture, path sample and outcome observation
remains ordered.

The first version enters its review hook too often. The narrower version,
`332ce3d`, enables it only for the selected primary incoming synthetic branch,
already primed, with no launch, whose initial phase plus admitted prefix length
equals3. That prefix ends immediately before dispatch. Retained work, priming,
resolution, outgoing flight, residual owners and prefixes that already dispatch
retain their yields. Explicit permission is granted only on the primary selected
root route, not inferred from variant equality on a residual/footer fallback.

At the boundary, the hook preserves all worker registers including A5. It reads
the saved authoritative 72-byte history tail, rather than transient replay scratch.
It rejects a completed dispatch, generation/presentation mismatch, owner/status
change, unprimed branch, launch, outcome, endpoint readiness, active keyboard ACK,
menu work, placement production or due animation. It freshly classifies the
actual private dispatch state and invokes unchanged coherent beam/latch and
actual-timer admission with service/margin reservations. It never pumps input,
presentation or callbacks while private history ownership is active. An accepted
extension replenishes one worker slot and increments the cumulative root budget;
only acceptance increases the accumulated cost hypothesis. A refused review's
time remains part of its original executed owner, including its guard tails.

There is no persistent refusal cache. Refusal retires private ownership and
returns immediately to the root clock, keyboard and presentation pumps. Every
subsequent root visit reconsiders eligibility from current generation, branch,
status, launch/query phase, producer obligations, timer slack and visible latch.
Thus input/ACK progress, beam movement, clock movement, a new request, branch
selection, completed work or changed presentation obligations can all change
the next decision. No arbitrary retry delay can suppress timely reconsideration.

The retained native snapshots and API fixtures do not establish universal WCET,
all refusal reasons, every asynchronous edge or new physical-resume acceptance.
The existing elapsed allowances remain hypotheses. Withdrawal removes these new
runtime paths from the final branch.

## Matched evidence

Code growth changes loaded addresses, so the earlier PR48 machine images cannot
be reused directly. They remain preserved. Each new comparison establishes one
physical incoming/contact state, enters tutorial with real controls, aligns from
actual samples, holds F, and saves a settled main-loop anchor. The anchor includes
complete canonical/history/records/preview/seek/tutorial snapshots, registers,
settled flags and a complete emulator state. Each pass restores that same anchor;
RAM/register audits permit only the two declared complete code-owner ranges to
differ. Production candidate bytes are compared to actual PR48 source padded at
unreachable function tails. All other loaded bytes, hunk sizes and symbols match.
No gameplay state is injected during the measured window.

Baseline1, identical baseline2 replay and candidate receive the same scheduled
D edge, 12 ms hold and fixed1.2-second observation window, followed by a bounded
tail closing actual callbacks/owners. PAL uses 20 ms and NTSC 28 ms from its anchor
to physical D press. The replay comparison includes normalized notifications,
all recorded callback/stack/publication data and final registers/owner snapshots;
it is not a full final-device-state comparison. Lifetime instruction counts are
normalized to each pass's origin. All passes accept exactly one equivalent
new-generation `(x98,y152,variant0)` request, preserve frozen 318/72/history bytes,
retire D release and ACK, have actual held contact and agree on exact endpoint
point/outcome. Publication qualifies actual completed banks, generations and
native sprites at COPJMP. This is not first scanout.

Each version also passes 34 actual-68000 API fixtures against both original PR48
and its padded reference. Complete private owners, paths, cursors, ordered
outputs and intermediate body returns agree. Original/reference CPU cycles match
in all fixtures. The hardware timer and beam reads in these API fixtures are
explicit sinks; native elapsed time is measured separately. Fixture initialization
occurs once and does not feed expected state back into execution.

| Version / region | Baseline COPJMP ms | Candidate COPJMP ms | Change |
|---|---:|---:|---:|
| Initial PAL |512.683629|512.684757|+0.001128|
| Initial NTSC |495.274120|511.989932|+16.715812|
| Narrow PAL |485.346197|485.345633|−0.000564 (2 CCK)|
| Narrow NTSC |494.031225|494.030107|−0.001117 (4 CCK)|

Initial campaign `ebb9074ab2be47f48a8b6b02f599a12b` and narrow campaign
`0e0b0085e13b47288ce3d6d708bef11c` both close with the two selected diagnostic
cases passed. These are correctness passes, not improvement passes or full
acceptance. Different versions have different anchors and publication phases;
do not compare across rows to infer a speedup over PR48's earlier498/490 ms.

Before readiness, the initial version reduces grants 104→87 PAL and 110→88 NTSC,
but invokes 87/88 hooks, only 13/19 accepted. The narrow version reduces grants
104→93 PAL and98→88 NTSC. Its 33/27 hook attempts include 9/4 accepted and 24/23
refused. Those hook spans consume 13.174622/11.087722 ms, **already included** in
the accounting below. Changes in other initial prefix grants also reflect the
changed clock/phase schedule; total grant reduction is not simply accepted
extension count.

## Non-overlapping accounting, narrow version

Every integer CCK from physical injection through qualifying COPJMP is assigned
once by the documented nested-span priority. The endpoint-known boundary is the
actual new-generation held-ready store; point/outcome stores precede it. The
store-to-COPJMP suffix is removed from every other bucket. IRQ time inside an
observed span is retained. Instruction tails, outside-call gaps and missing
contexts remain unclassified; outside-callback time is not necessarily idle.

| Exclusive elapsed partition, ms | PAL base | PAL candidate | NTSC base | NTSC candidate |
|---|---:|---:|---:|---:|
| Actual mathematics before endpoint known |60.182498|60.119062|60.277773|59.956503|
| Scheduling and preview support before known |257.262479|261.190703|259.883030|263.234294|
| Hardware service and display production before known |100.656490|97.208967|103.296089|99.969130|
| Mandatory controls/requests before known |43.969726|43.964087|44.065656|44.085491|
| Unclassified before known |11.606490|11.044026|12.089525|11.603989|
| Known-ready store to qualifying COPJMP |11.668516|11.818788|14.419151|15.180700|
| Total |485.346197|485.345633|494.031225|494.030107|

Readiness advances only 535 PAL CCK (0.150836 ms) and 2,730 NTSC CCK
(0.762667 ms). The next publication absorbs almost all of that difference.
Scheduling/support rises3.928225/3.351264 ms. The inference supported by these
pairs is that this particular batching/review tradeoff does not improve endpoint
publication latency. It does not show that all batching is ineffective, all
support can be removed, or a different unmatched anchor is faster. A third
speculative quota or reservation change is not justified by these results.

## Custody and final product

Public numerical reductions:

- [Initial summary](evidence/tutorial-latency/topup-attempt1-summary.json).
- [Narrow summary](evidence/tutorial-latency/topup-attempt2-summary.json).
- [Custody](evidence/tutorial-latency/topup-custody.json).
- [Runtime restoration audit](evidence/tutorial-latency/topup-runtime-restoration.json).

Private reports/raw/anchors are retained, never uploaded to Library or Git:

- Initial PAL `build/tests/topup-matched-pal/7cdb17f6f4744eeeb46cb53a04dd39f7/`.
- Initial NTSC `build/tests/topup-matched-ntsc/2d1a971fccd54ee295ad867f14fe93cb/`.
- Narrow PAL `build/tests/topup-matched-pal/cb56baee6f7c4b83bbac334caf3a1fb9/`.
- Narrow NTSC `build/tests/topup-matched-ntsc/6d6705c0f6444f279b2e4c85d7edcca9/`.
- CPU initial `build/tests/topup-cpu/afc2751f29144c798f2d5b1a827b02a1/`;
  narrow `build/tests/topup-cpu/244adcd21aea4c7ba12512fc49359523/`.

The first CPU prototype failed with a fixture-only missing
`tutorial_batch_remaining` symbol in original PR48. Its failure and partial raw
files remain at `build/tests/topup-cpu/`; later passes do not upgrade it.
The first accounting revision omitted the coherent-entry support alias. Its
private reducer/summaries remain in `build/tests/topup-analysis/`; the published
new reduction adds that alias. Combined buckets are unchanged; the old individual
support/root subcategories should not be compared.

Candidate 54cae13 SHA256 is `ad78cc5faba82a293f53296aeacb35927ee3be2b174e7d3967ec93073f7b1af8`;
candidate 332ce3d is `64a577edf605eefd9c7112c17b1034b7edaa3788c40f332e995fb250336ed57d`.
Both development executables and listings are frozen privately. The first
candidate was recovered exactly from committed source and explicit generated
inputs in an isolated private root after the canonical build was replaced;
executable and original listing hashes match the immutable native receipt.
No release executable was built or claimed.

Restoration commit `037d606` removes the entire runtime experiment. The rebuilt
development product is `0d41b1c0a0b2cbffe96f2efe62a57859cf6efc05dfd1788db33c5fb079e3bc99`.
All five hunk sizes and symbols match PR48's frozen `32a2a2d7…` product; every
loaded byte outside the authored BUILD label and title identity cache is equal.
Only 97 build-identity bytes differ. Final runtime source equality supports reuse
of PR48's unaffected tests; no claim is made that the final-label product passed
a new broad native campaign.

`python3 scripts/native_metrics.py --check` still fails with
`Accepted metrics are incomplete`, the pre-existing hold. Resource sizes return
to PR48; incomplete accepted metrics are not replaced with a green summary.
Appearance, resource, deadline, physical-resume and full-release holds persist.
No merges, deployments or releases occurred.

## Reproduction and review

The experimental native commands require an isolated checkout of 332ce3d, not the
final restored runtime. Use the declared tools/ROM/private native inputs, build
with `python3 scripts/build_native_game.py`, generate the private reference with
`python3 scripts/build_topup_reference.py`, then use normal ownership:

```
python3 scripts/native_acceptance.py --plan --case topup-matched-pal --case topup-matched-ntsc
RUST_LOG=info python3 scripts/native_acceptance.py --start --case topup-matched-pal --case topup-matched-ntsc
PYTHONPATH=.tools/proof-python python3 scripts/topup_cpu_proof.py
```

CPU proof additionally consumes the frozen actual PR48 executable under
`build/tests/bounded-topup-pr48/`. Existing files must not be overwritten to
manufacture a receipt. The read-only reducer accepts immutable report paths and
an explicit matching executable:

```
python3 scripts/topup_matched_accounting.py REPORT_PAL REPORT_NTSC --executable MATCHING_EXECUTABLE --output NEW_SUMMARY
```

Independent review verifies the retained raw partitions, grouping, CPU triples,
product bindings and withdrawal decision. Fresh tests are the two diagnostic
campaigns and two 34-fixture CPU comparisons. PR48 input/equivalence evidence and
the earlier coherent scheduler, endpoint, fairness and exact-resume results are
reused with their original extent; broad native tests are not rerun. Remaining
uncertainty concerns recoverable cost in the unchanged scheduler and broader
coverage, not a claimed batching correction awaiting release.
