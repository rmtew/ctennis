# Post-PR47 latency: unchanged-key scan correction

This continues draft PR47 at `9a9aca59`, runtime `6a0f7498`, using the verified
`63ed6aac`/`f1d31982` transfers. The previous
[disjoint accounting](tutorial-latency-next-analysis.md) remains immutable:
526.970 ms PAL /521.954 ms NTSC for its fresh-D trials, including
21.399/22.443 ms from endpoint-known return upper bound to actual qualified
COPJMP. Its11.657/11.644 ms pre-known gaps remain unclassified; outside-callback
spans are not necessarily idle or recoverable. Declined-owner65–72 ms overlaps
those categories and must not be added again.

## Correction and evidence

The [six-query reduction](tutorial-latency-six-query-results.md) assigns
47.897/46.508 ms to `ui_sample` in those original trials. This is the largest
identified homogeneous avoidable operation, not a claim that all root/support
latency is avoidable. The larger root remainder has heterogeneous and
unclassified control work. Source review found that the nominal sampler scans
128 keys even when nearly all current/previous bytes are equal.

Runtime commit `fdd257c` compares four exactly unchanged key bytes at once.
Changed groups execute the original ascending scalar recognition, including
nonboolean transitions; unchanged previous bytes already contain the complete
correct snapshot. Joystick edges, supported-key recognition, register saves,
keyboard polling/ACK, tutorial requests and all downstream code remain intact.
There is no scheduler cache, new delay, experiment configuration word or change
to dispatch reservations. The 68000 long reads have even addresses. Serial
keyboard polling cannot reenter this sampler; the presentation IRQ has no
consumer or writer of previous-key state.

Pinned actual-68000 proof passes9,225 finite fixtures, comparing the original
`ad4ec12c…` executable, a padded original-reference image and final candidate.
It covers every128 key position's press/release/held/nonboolean transitions,
group boundaries, simultaneous/unsupported/menu keys, lifecycle branches,
takeover, asymmetric pads and carried/released histories. It compares complete
named UI/core/matrix state and history/record hashes, restores all D/A registers,
audits writes and compares ordered presentation/title sink calls and Paula writes.
The presentation/title sinks are explicit observations, not native-render proof.
CPU cycles exclude chip waits/IRQ and establish no native elapsed bound:

| Fixture | Original | Padded reference | Candidate CPU cycles |
|---|---:|---:|---:|
| Unchanged keys |10,368|10,368|3,264|
| Fresh D |10,730|10,730|3,878|
| All128 keys newly changed |148,192|148,192|149,152|

The all-changed case regresses960 CPU cycles. Original/reference tutorial cycles
are identical; two non-tutorial resume branches widen because of unreachable
padding, which is not part of the measured tutorial path. The proof binds
executables, listings, proof source and pinned machine68k implementation in
`build/tests/ui-scan-cpu-proof-final.json`.

Final development executable SHA256:
`32a2a2d76c40aea9cd9244e89285082d32eebf44d0eb0a423888e92966c06de8`.
Padded reference SHA256:
`ea85bb8bf687f40cb05543f3336cd33a7e56e7ebbacadb2168cee38e440635a7`.
The exact reference hash is authoritative in the linked summary/byte audit;
executables and original reports remain private under ignored `build/`.

## Matched native comparison

Actual normal play, physical tutorial controls and physical alignment to an
observed incoming sample establish a real receiving/contact anchor. No gameplay
state or expected trajectory is injected. At stopped `main_loop`/stack-top with
ACK and owners settled, save the complete native machine once. Each pass restores
that same anchor. Two reference passes gate the untouched final candidate pass.

Reference replacement touches only the complete input routine and one audited
two-byte `ui_resume -> ui_input_draw` branch operand. Hunk addresses/sizes and
all external state/table/IRQ addresses agree; loaded bytes outside those ranges
are exactly equal. Whole512 KB RAM and registers are audited after replacement,
and every declared range is read back against relocated reference bytes. The
candidate restore executes unchanged production bytes. No instruction cache,
live PC, return address or IRQ consumer occupies the patch ranges.

The measured window is fixed1.2 physical seconds, with identical watches,
inputs and a separately bounded30 ms complete-owner tail. Input is a fixed12 ms
D pulse: PAL press20 ms after anchor, NTSC press28 ms. These offsets bracket one
nominal sample in each region; they were fixed before their final baseline
passes. Each final comparison requires exactly one identical accepted
`(relative generation1,x98,y152,variant0)` request, the same held endpoint bytes
and landing outcome1, frozen canonical/history/records, physical ACK retirement,
complete owners, no loss and immutable-bank/native-sprite qualification.
Endpoint bytes are `716371630242007a0000000000000000` in all accepted passes.

Baseline replay equality covers normalized observed emulated events, callback
and stack spans, bank/publication observations, final registers and retained
UI/preview/seek/tutorial/canonical/history/record regions. It does not directly
compare every CIA/device component. Copperline's cumulative retired-instruction
counter is not restored by `state.load`; its per-pass delta is compared instead.

| Region | Baseline1 | Baseline2 | Candidate | Saved ms |
|---|---:|---:|---:|---:|
| PAL |518.414|518.414|498.384|20.030|
| NTSC |506.861|506.861|490.145|16.716|

These are one deterministic contact state/window per region, about one display
period saved. They are not distributions, WCET or universal latency guarantees.
They are separate matched states from the original transfer's trials; the old
527/522 ms values must not be used as causal baselines for these candidates.

## Exhaustive elapsed accounting

The [compact reduced evidence](evidence/tutorial-latency/ui-scan-matched-summary.json)
binds exact original report/raw/anchor hashes and integer CCK sums. Nested emitted
call wall spans, including IRQ time, are assigned once with the original reducer's
category priority. Instruction tails and gaps remain unclassified. The new cutoff
is the actual held-ready flag store after the accepted request cleared readiness;
unchanged source writes the terminal point/outcome before that store. This is more
precise than the old return upper bound and is still not first visible scanout.

| Disjoint interval, ms | PAL baseline | PAL candidate | NTSC baseline | NTSC candidate |
|---|---:|---:|---:|---:|
| Actual algorithm before ready store |60.208|60.403|59.974|59.874|
| Scheduling/preview support before ready |245.588|256.560|243.485|261.745|
| Hardware service/display production before ready |98.203|101.072|98.250|102.177|
| Mandatory callback/controls/requests before ready |76.021|43.858|71.799|42.736|
| Unclassified before ready |11.039|11.402|11.129|12.008|
| Ready store → qualified actual COPJMP |27.354|25.090|22.223|11.605|
| Total |518.414|498.384|506.861|490.145|

Rounding can affect displayed sums; all integer sums are exact. Input-scan spans
within these bins fall from44.898→13.815 ms PAL and42.375→13.397 ms NTSC before
readiness. They are included in mandatory work, not an additional bucket.
Scheduling/support and service rise as the faster sampler leaves more main-loop
work opportunities. Saved scan time therefore does not translate one-for-one to
physical latency. No outside-callback interval is labeled idle/recoverable.

## Repeated refusal: reviewed, not cached

A general refusal cache is not justified by the available snapshots. The original
source-fenced reduction identifies only5.962/1.292 ms of repeated selected
classifier-zero time. Earlier guard refusals remain individually unclassified;
partial repeated plan signatures do not prove equivalent private state.

Any future bounded memo must invalidate on a nominal callback, accepted request
or generation/cancellation/origin change, selected variant/animation lookahead
change, any preview/history/seek cursor/phase/priming/readiness/outcome/private
context mutation, producer/footer stage or bank readiness change, and residual
turn/route changes caused by a declined attempt even with zero executed work.
Its key must cover every classifier/eligibility input, not just job kind/budget.
A timer-insufficient refusal can persist only while its proven remaining-time
predicate decreases in the same epoch. Beam/DMA refusals can become eligible
within that epoch: cheap beam/ownership guards must be reconsidered each main
loop or at a proven earlier eligibility event. A callback, publication or state
mutation must reconsider eligibility promptly. Never replace that with an
arbitrary delay or skip the existing keyboard/ACK/presentation/timer service.
The present correction keeps all original per-loop eligibility and held/released
routing, generation cancellation and exact-resume machinery.

## Receipts, failures and remaining holds

Accepted PAL run `ab3251ea52c74a48956e19d137ff619b`, observer commit`3c2b43e`,
private report `build/tests/ui-scan-matched-pal/546fbe4f39f04a79bd3f5a208b37171e/report.json`.
Its case passed in campaign`a19dd7759c0748a8bc4e8bd37f7d68da`; that combined
campaign subsequently failed NTSC's missed input pulse. Do not call it a whole
campaign pass.
Accepted NTSC run `c9efc17033274cfab6b2ead5aee0f86f`, observer commit`de1a943`,
private report `build/tests/ui-scan-matched-ntsc/9b9eead2304a486e983953f5cea7f3ef/report.json`.
Selected-only campaign`68b89bdefa7a46bb821641df858dd7f6` closed pass.
The sole source change between those observers adjusts only NTSC's press offset;
PAL is reused in its immutable source-bound extent, not silently relabeled as a
fresh current-helper execution.

Retained earlier campaigns: `2c02bad5…` observer counter initialization failure;
`52827c37…` lifetime-counter replay mismatch; `fd5238dc…` missed-contact fallback
with negligible2 CCK timing change and missing product provenance rejection;
`625e7d21…` byte-width alignment failure; `47668487…` unequal one/two request
sequences; and the combined campaign's missed NTSC pulse. Their raw transcripts,
branch/partial/failure JSON, controller completion records and logs remain under
ignored build directories. None is upgraded to acceptance or hidden behind an
older pass.

The six-query host tests(5), partition tests(6) and hunk tests(4) pass. The earlier
matched-helper tests(7) remain limited host evidence. Independent reviewer `scheduler_design_review` independently recomputed all six
primary/suffix/collapsed partitions and conversions, verified exact baseline
replays and report/raw/anchor/reducer hashes, and streamed the raw new-request
clears and held-ready stores. All327 NTSC bindings match; all326 available current
PAL bindings match, with its one intentionally historical observer-script binding
recovered from the recorded commit. The reviewer clears only this finite matched
single-placement correction; approximately498/490 ms remains.

Focused ordinary physical-input campaign `70ef15b497054bf49d120547754e4191`
closed pass with11 checks: diagonal/actions, aliases, opposing directions,
releases and mixed keyboard/joystick controls. Its private receipt is
`build/tests/native-inputs/report.json`. The native builder still reproduces the
same candidate executable hash. This does not claim full-match or resume coverage.
`python scripts/native_metrics.py --check` fails with the preexisting
"Accepted metrics are incomplete" hold. No accepted profile is regenerated. Original unaffected
worker/core evidence is retained without repeating the costly nine-trial campaigns.
Appearance/resources, normative complete-path/deadline/transport bounds, physical
exact resume, stripped cold boot and full release remain held. No merge, release,
Library upload or accepted-metrics replacement occurs.
