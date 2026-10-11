# PR47 fresh-D: six read-only queries

Requested instructions were fetched from commit
`866999df0037879dce4a935020cb5f61c5acde87`, branch
`tutorial-latency-accounting`, draft PR48. This reduction appends evidence to
`transfer/tutorial-latency-investigation`; it does not rewrite the earlier
transfer or its accounting. No runtime change, build, native test, emulator,
PR45 action or raw-data publication occurred.

[Compact JSON](evidence/tutorial-latency/fresh-d-queries.json) contains the six
queries for PAL attempt9 and NTSC attempt2, fresh-D only, processed sequentially.
It is approximately1.2 MB, reduced from two approximately22 MB compressed
structured captures and two approximately46 MB compressed literal transcripts.
Private state/bank buffers are replaced with length/hash metadata; selected
cursor/count/outcome values and public output identities are observations.
The original files remain unchanged. [Validation binding](evidence/tutorial-latency/fresh-d-queries-validation.json)
records the exact reducer/result hashes, command, interpreter and host-test extent.
The JSON SHA256 is
`5c7b1d80e87c7e596f02ee93987bdd03b68aaaa468a4f0a94b15e2c1f352fe33`.

All351 original file/input/tool bindings per region are currently available and
hash-match in this retained execution environment. This differs from the fresh
worker's partially populated environment described in PR48. The five principal
retained files per region were also verified against the immutable
[custody manifest](evidence/tutorial-latency/custody-manifest.json). Run/source,
product identity, exact raw paths and hashes accompany each JSON region.

## 1. Generation and phase attribution

| Disjoint physical-input interval, ms | PAL | NTSC |
|---|---:|---:|
| Input → first selected contact-owner entry | 474.390 | 468.832 |
| Contact-owner entry → selected endpoint-ready return | 31.181 | 30.679 |
| Endpoint-ready return → qualifying actual COPJMP | 21.399 | 22.443 |
| Total | 526.970 | 521.954 |

Each phase retains every original primary category separately for an owner that
executed optional work, an owner that executed none, and outside-owner time.
These ownership classes refer to work execution, not accepted-generation status
or a reconstructed admission predicate. A second disjoint axis labels the
source-fenced new generation, witnessed previous generation and unknown/outside.
Every category and phase sum equals the frozen earlier accounting.

There is exactly one projected request API in each window. Generation99 is
observed after its return and at endpoint/publication. Before the request,
18PAL/16NTSC owners have next-entry generation98. The new request-return upper
bounds are44516059PAL and44851809NTSC CCK. Owners after that sole return with
next-entry generation99 are fenced using the source rule that optional root
jobs do not change generations. This is an explicit inference from control flow
and snapshots, not an observed generation-store position or exact acceptance tick.

## 2. Disjoint nested routine ownership

`q2` assigns each segment in the four requested primary categories to its
deepest observed containing call. The enclosing routine's self remainder is its
own named row; parents are not added inclusively. Largest rows include:

| Routine/category, whole-window disjoint ms | PAL | NTSC |
|---|---:|---:|
| tutorial_background / root remainder | 71.985 | 73.433 |
| ui_sample / remaining mandatory callback | 47.897 | 46.508 |
| tutorial_background_class / classification | 28.535 | 30.532 |
| game_preview_step_variant / preview support | 23.018 | 22.252 |
| tutorial_dispatch_allowance / classification | 15.692 | 12.500 |
| game_preview_continue_one / preview support | 14.360 | 14.024 |
| game_preview_copy_history / preview support | 10.496 | 10.164 |

All routines and counts are exported. These are IRQ-inclusive emitted-call wall
spans, not CPU self costs. Uncalled IRQ instructions and instruction tails can
remain in their enclosing call. This decomposition does not establish which
cost is avoidable or imply an equivalent wall latency saving.

## 3–4. Callback epochs, progress and refusals

`q3_callback_epochs` exports32 epochs per region, with one row per intervening
owner. Rows include accepted chunk telemetry, budgets/cost/reservation,
operation sequence, recorded branch cursors/counts/outcomes/synthetic phases,
endpoint before/after stage/cursor/ready flags, class/admission counts and union
spans, observed admission timer inputs, generation samples and entry beam.
Actual spent return count and flight phase are null. Flight phase has not been
decoded from retained private318 snapshots by this reduction; it is not asserted
missing from raw data. A timer phase write after each callback is retained where
observed; it is not the exact completion slack.

Route labels describe variant-write witnesses only. `selected_primary_witness`
means a sole active-variant store, not proof that the preview worker ran; inspect
the chunk job kind to distinguish producer/footer work. One primary variant store,
one toggle, or multiple writes have distinct labels; multiple writes are only
fallback-possible, not a complete footer-fallback control-flow proof.

| No-job owners | PAL | NTSC |
|---|---:|---:|
| Classifier budget0 with no admission call | 38 | 11 |
| Admission call(s) returned with no executed job | 48 | 94 |
| Earlier guard/route unclassified | 258 | 261 |

Partial plan-signature repeats within one callback and without optional progress
are24/6 zero-budget and28/54 admission-return/no-job cases. They do not establish
unchanged private state, guard inputs or presentation ownership. A callback or
any executed optional job clears the repeat group. The JSON keeps these counts
separate from the earlier narrowly selected classifier cohort.

There are167 pre-contact root `game_preview_endpoint_pending` calls per region.
Each row has its caller, nested selection-check count, next-entry controller and
preview generations, and snapshot position. Endpoint API profiles are separate.
Guard-time `launch_saved`, exact generation stores, complete classifier inputs,
blank latch and branch outcomes are not established. Refusal causes and complete
unchanged-state proof remain null. “Unknown” means unestablished by this structured
capture reduction, not a claim that no usable literal-RPC record exists.

## 5. Timer callsites

| Emitted timer role | PAL calls / disjoint CCK | NTSC calls / disjoint CCK |
|---|---:|---:|
| First main-loop accounting | 518 /119007 | 533 /122232 |
| Second main-loop accounting | 518 /118689 | 533 /123373 |
| Admission accounting | 154 /35550 | 168 /38287 |

The two main-loop PCs are distinguished by emitted source order; admission uses
its captured caller. Nested presenter/keyboard spans take priority over timer
spans, preventing IRQ service double counting. Their total is the earlier timer
service77.038/79.310 ms. Repeated first-byte-read witnesses are11/12/3PAL and
9/16/4NTSC across these callsites. Those establish retries only where the same
first read repeats; they do not identify which coherent-read comparison failed.
Per-owner admission reads retain available phase/interval; exact refusal slack
and window predicates are unknown. Volume alone does not justify removing
mandatory clock/ACK/admission service.

## 6. Known suffix and publication

The JSON retains the matching READY profile, producer/presenter spans,
`complete_scene`, callback snapshots, bank/surface identities, native publication
proof and observed beams. The key suffix positions are:

| Observation, CCK | PAL | NTSC |
|---|---:|---:|
| Selected READY return upper bound | 46236095 | 46587099 |
| Producer tutorial_progress_slice entry | 46241906 | 46638137 |
| complete_scene entry /exit | 46247148 /46248329 | 46643531 /46644738 |
| Producer return | 46248507 | 46644918 |
| Qualifying actual COPJMP | 46311994 | 46667435 |

The completed bank metadata has placement_dirty255; the captured live controller
at qualifying COPJMP has placement_dirty0. Qualification uses the live fields;
this distinction must survive downstream analysis. Exact dirty-store/rearm time,
ready-write time and first scanout remain unknown. Producer, endpoint compute
and publication opportunity are distinct observations; the suffix is not all
idle waiting.

## Review and repeatability

Independent `/root/ratio32_review` cleared this transfer after checking result,
reducer and manifest hashes, every Q1 ownership/generation/category sum, every
Q2 category sum, timer priority/source callsite scope and null-field limits.
No reviewer giant load or native execution occurred.

Run `python scripts/tutorial_latency_queries.py` only where custody files and
original bound executable/tool inputs remain available. The reducer loads PAL,
reduces/releases it, then NTSC. It verifies custody, checks every primary total
against the frozen export, and writes only the new reduced JSON. Preserve any
existing result before rerunning. There is no projection-reuse execution path.
Five pinned-Python host tests cover interval ownership, nested IRQ service,
original-core scope, snapshot/private-byte handling and repeat invalidation.
They are not runtime acceptance. Existing resource/acceptance/WCET, matched
causality and release holds remain unchanged. No correction is proposed by this
transfer; the new worker should assess these observations before further work.
