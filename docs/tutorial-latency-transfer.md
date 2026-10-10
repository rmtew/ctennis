# Latency investigation transfer — runtime work stopped

Parent stopped implementation on 2026-10-10 and requested preservation for a
fresh task. This transfer contains analysis and unexecuted test tooling only.
No runtime, build, CPU execution, emulator campaign, native observer or catalog
change was made during this investigation. Do not treat the old PR45 request as
the active task. Resume only the latency investigation when separately authorized.

The transfer branch is `transfer/tutorial-latency-investigation`, based on
`9a9aca59e7f6b04cf756d5bb9b9d973a18996ee3` (open draft
[PR47](https://github.com/rmtew/ctennis/pull/47)); its parent is PR46. No PR was
created for this transfer and nothing was merged. Runtime remains the PR47
product: native SHA256
`ad4ec12c1aba9bd125a42074c468ed106f8eaeb197c84d0ad0581dffcc709c45`.
Original capture source/product commit is
`d51f2b3b31d761ca98561f3005eaa28e8e98c531`, distinct from the docs checkout.
The earlier runtime-changing source ancestor is
`6a0f74984d2e67ce539bd3fbe452c784c0167c93`.

## Finding and accounting

Fresh physical D edit to first qualifying actual endpoint COPJMP:

| Disjoint elapsed interval (ms) | PAL | NTSC |
|---|---:|---:|
| Actual algorithm spans before known endpoint | 59.278 | 59.466 |
| Scheduling and preview support before known endpoint | 252.119 | 247.842 |
| Hardware service and display production before known endpoint | 104.648 | 104.344 |
| Mandatory callback, controls and requests before known endpoint | 77.869 | 76.215 |
| Unclassified before known endpoint | 11.657 | 11.644 |
| Known endpoint upper bound to qualifying COPJMP | 21.399 | 22.443 |
| Total | 526.970 | 521.954 |

The large scheduling/support aggregate is measured elapsed ownership, not proven
avoidable CPU work. Actual algorithm spans include shared dispatch/landing/ball,
not a separately instrumented instruction-cost oracle. No dominant avoidable
cost has been established. Across fresh-D plus six contact cases latency is
501.539–611.531 ms PAL and 479.228–594.101 ms NTSC. Initial-held and aligned-held
also exist in the export; aligned-held includes continuing physical edits and
superseded generations and must not be reported as settled compute latency.

The reducer uses exhaustive half-open partitions of emitted call stack-store to
final RTS-read spans. Earlier categories take priority over overlapping parents;
IRQ wall time is included once. Instruction tails and gaps remain unclassified.
It does not model or execute the game. The compact table subtracts the endpoint
known-to-publication suffix from every category before collapsing it to one bin.
Endpoint-known is a matching-generation READY API return (or sampled released
outcome), an upper bound on the actual ready write. COPJMP is the first qualified
live-clean, completed immutable bank with matching native sprite state, not
first scanout. Full category and disjoint nested service splits are in the JSON.
Secondary owner, eligibility and cohort diagnostics overlap primary categories;
do not add them to the table. Waiting/input/reservation/display causes remain
null: the captures lack complete failed-admission and consumed-input ledgers.
Latest accepted-request generation attribution is explicitly unverified.

## Preserved artifacts and review

- [Reducer](../scripts/tutorial_latency_accounting.py): SHA256
  `932b55338e08141e805d6e626e8156f0bbfe4f9f6d1b05c05a2278c58845fd29`.
- [Reduced results](evidence/tutorial-latency/accounting.json): exact 190142-byte
  original receipt, SHA256
  `44029ab9e0c1da67878c9cb4809d69476e39fc481b30748d24657d5d6b601d7e`.
  Contains all18 per-trial exact CCK partitions, converted ms, endpoints,
  qualified-bank digests, branch/phase/service/cohort diagnostics, input extrema,
  policy and identity/holds. `accounting_commit` is the pre-transfer checkout;
  the reducer is independently hash-bound, not claimed committed at that base.
- [Custody manifest](evidence/tutorial-latency/custody-manifest.json): absolute
  and relative local paths, byte sizes, hashes and all351 original input/tool
  bindings per region. Metadata only; no raw trace, asset or executable bytes.
- [Six interval/cohort tests](../tests/unit/test_tutorial_latency_accounting.py).
- [Matched-controller proposal](tutorial-matched-planner-capture-plan.md),
  [helper](../scripts/matched_planner_capture.py) and
  [seven host tests](../tests/unit/test_matched_planner_capture.py).
  This helper is incomplete execution scaffolding, not an approved capture route.

Independent reviewer `/root/ratio32_review` verified all18 primary, service and
collapsed sums against the exported receipt and current reducer; cleared transfer.
The initial secondary service split double-counted nested IRQ service; the final
receipt corrects it with priority masks intersected with the primary service
partition. The selected cohort now uses the NEXT callback-entry snapshot:
`boundaries` are callback ENTRY, so the preceding snapshot can precede the
current callback's controls. Its fixture covers that fencing error, job
invalidation and exclusion of residual variant1→0. Review did not load giant raw
traces or run native tests. No normative deadline/admission/WCET proof or causal
paired speedup is claimed.

## Candidate status and invalidation requirements

A cache suppressing repeated selected classification at budget0 was considered
but never coded. Narrow source-backed witnesses require one classifier, no
admission, one sole variant0 write, final budget0 and next-entry activevariant0.
They establish classifier-zero, NOT its refusal reason. Fresh-D PAL has36
witnesses,24 repeats after first in the same callback/generation without executed
optional work; repeat classifier union21148 CCK =5.962 ms. NTSC has8 witnesses,
6 repeats,4623 CCK =1.292 ms. Six contact cases repeat spans are3.865–7.763 ms PAL
and5.694–9.846 ms NTSC. All declined owners total64.670/71.614 ms fresh-D but are
heterogeneous; that total is not the candidate opportunity. Cache overhead and
wall latency savings are unmeasured. Reviewer and author agree this cohort does
not justify a dominant-cost correction; retain runtime unchanged.

If reconsidered after new evidence, distinguish the original primary selected
`.preview` route from `.other_branch` and footer fallback sharing that label.
Keep eligibility, animation/producer, endpoint/result/footer and fresh admission
checks. Do not cache beam refusal or positive budgets. Clear at EVERY
`tutorial_tick` entry (including early returns), any executed optional job,
request/cancel/resume/seek/selection changes. Prove callback epoch, both tutorial
and preview generation, variant/private branch state and presentation invalidation.
Accounted time increases within the callback interval and capacity decreases;
clear/reconsider at next callback, never add arbitrary polling delays. Public
mutators outside the owner must have explicit invalidation or a revision key.
`tutorial_animation_due` is nominal-update based, not merely physical time.
The normal `game_preview_selection_valid` has four cheap guards; the full318/72
comparison is PREVIEW_DEBUG-only. Do not optimize an imagined runtime comparison.

## Retained private traces and access

Only local custody is established. The `build` symlink in
`/workspace/ctennis-coherent-scheduler` resolves to
`/workspace/ctennis-coherent-build`. Exact local traces:

| Region | File under that build root | SHA256 |
|---|---|---|
| PAL | tests/coherent-contact-native-pal/report.json | 84a9de8441a5e9e6d47127dcdee264e43a152d6b6d2ecfa78470221398d1e6a3 |
| PAL | tests/coherent-contact-native-pal/latency.json.gz | 57fd24c48e01d1e9f3d1845c707e6a3761c61126bbf279f220bf574b0d1cb742 |
| PAL | tests/coherent-contact-native-pal/literal-rpc.jsonl.gz | e6364df2f8ec6e81a26c269f69b7ad6aa9e240b81d2af220fafbfa3e7f208071 |
| NTSC | tests/coherent-contact-native-ntsc/report.json | 6a82f1e91ec02e6f8233bc97c82fcdaa1f3f2ff71b87f64682aa929ac0634dfa |
| NTSC | tests/coherent-contact-native-ntsc/latency.json.gz | 96b3e3942dc46461cf1e0fe880f61ca72e3fed7f09e80a8d174982dfbb9173e0 |
| NTSC | tests/coherent-contact-native-ntsc/literal-rpc.jsonl.gz | e57a3805785f45ef8e00d9948420d9f6ee7a1f69480db42e2743cc82c9b142ff |

Campaign `7c2cac9edbe64d9a8aeb30e51496380f` closed complete SELECTED SUBSET,
not full acceptance. PAL run `f52a873403c7415fa21dde09ea011373`; NTSC run
`c58919c303434c13acf6fcd32941e370`. Both complete, no changed-during-run inputs;
351 original bindings were verified in each reduction. Service/log/tool hashes
and sizes are in the manifest. Prior failed attempts1–3 had lost raw traces;
retained metadata is not recovered raw evidence. Never erase unique evidence.

A fresh cloud task can clone/fetch this Git branch for all exported small files.
Git does NOT retrieve these ignored local traces. A task using this SAME retained
execution filesystem can read the absolute paths and verify manifest hashes.
Persistence or shared storage across a new cloud environment has not been
established; paths and run IDs are not download links. If the new task receives
another environment, an explicitly authorized PRIVATE file transfer or mounted
artifact store is required to reach raw traces. No such export/store was created
here, and no raw data was uploaded to GitHub or Library. The manifest is custody
metadata, not a remote retrieval capability.

Without raw data, use the committed JSON to recompute sums, category groupings,
service/branch comparisons, candidate scale and qualification limits without
repeating tests. It cannot re-derive individual call boundaries or reconstruct
missing admission/input reasons; any finer instrumentation needs authorized new
capture, not invented attribution. With local traces, rerun the reducer
sequentially (it verifies every original binding); avoid concurrent giant JSON
loads and preserve its original output before writing a new receipt.

## Matched validation proposal and remaining blockers

Existing independent PAL/NTSC live seeds and adaptively timed edits are not a
matched pair. Retained buffers are incomplete whole-scheduler restart snapshots.
Same seed alone does not imply paired randomness/input timing. The proposal uses
one candidate executable, a declared disabled/enabled config word set once after
full-machine state.load and before fixed absolute physical D press/release.
Save at settled main_loop/SP top with ACK retired, no active helper/producer.
Pinned Copperline state.save/load supports full-machine state; load drops input
queues and debugger hooks must be freshly installed. First require
baseline→baseline full state/events/cursors/CCK replay equality, then treatment;
separately compare old actual core with disabled candidate. No config ABI or
runtime candidate exists. Observer adapter, reviewed physical anchor/window,
fixed-end owner-cutoff contract and storage budget are also unresolved. Current
helper rejects open owners; a bounded completion tail was proposed but not
implemented or reviewed. No build or emulation is authorized by this transfer.

## Checkout and verification

At handoff checkout branch was `feature/tutorial-latency-accounting`, HEAD9a9aca5.
There were no tracked modifications. Untracked: `.tools` and `build` local
symlinks; reducer/test; matched helper/test/plan. All five authored files are
preserved on this transfer branch; both symlinks remain local and excluded.
No changes exist to amiga/, policies, native capture observers or acceptance
catalog. Prior PR47 work checkpoint is historical, not this active task status.

Ran `env -u PYTHONPATH /tmp/ctennis-shared-core-python/bin/python -m unittest
discover -s tests/unit -p 'test_tutorial_latency_accounting.py'` (6pass) and same
with `test_matched_planner_capture.py` (7pass). `scripts/native_metrics.py --check`
failed with `Accepted metrics are incomplete`, the pre-existing PR47 resource
hold; no metric refresh or build was performed. Syntax and whitespace checks
pass. Resource/full acceptance, normative admission, complete interference/WCET,
transport limits, appearance and stripped cold-release gates remain open.

Next worker should read this document and JSON before choosing a new experiment,
verify available raw custody, and establish a dominant avoidable cost before any
runtime edits. Independent reviewers must review a concrete correction and its
matched actual-core proof; the parent coordinates reviewer/integrator ownership.
