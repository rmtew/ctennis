# Post-PR47 latency investigation: reviewed transfer and next reduction

This investigation continues from PR47 head `9a9aca59` and verified transfer
`63ed6aac37892cea382ab83dd798d973892e2e06`. Runtime is unchanged from
`6a0f7498`; native SHA256 remains
`ad4ec12c1aba9bd125a42074c468ed106f8eaeb197c84d0ad0581dffcc709c45`.
No new native execution, paired comparison or runtime acceptance is claimed.

## Measured accounting and independent local review

The immutable [accounting export](evidence/tutorial-latency/accounting.json)
and [custody manifest](evidence/tutorial-latency/custody-manifest.json) remain
unchanged. Fresh physical D input to qualified actual endpoint COPJMP:

| Disjoint elapsed interval, milliseconds | PAL | NTSC |
|---|---:|---:|
| Actual algorithm spans before endpoint-known upper bound | 59.278 | 59.466 |
| Scheduling and preview support before known | 252.119 | 247.842 |
| Hardware service and display production before known | 104.648 | 104.344 |
| Mandatory callback, controls and requests before known | 77.869 | 76.215 |
| Unclassified before known | 11.657 | 11.644 |
| Endpoint-known upper bound to qualified COPJMP | 21.399 | 22.443 |
| Total | 526.970 | 521.954 |

Independent reviewer `scheduler_design_review` recomputed all 18 exported
primary, endpoint-known suffix, service and collapsed integer CCK sums and all
primary millisecond conversions. Reducer and exact export hashes match the
transfer document. Of each region's 351 original bindings, 223 are available
locally and hash-match; 128 are absent. This establishes export consistency and
available-file identity, not independent validation of raw call boundaries,
original bank qualification or missing refusal/input causes.
All 64 originally bound amiga/ runtime files hash-match. Missing bindings are
108 old Python/PIL paths, 17 build paths and three tool/configuration paths.

Locally executed with pinned Python 3.12.14 and PYTHONPATH unset:
`python -m unittest discover -s tests/unit -p test_tutorial_latency_accounting.py -q`
(six pass) and the corresponding `test_matched_planner_capture.py` command
(seven pass). These host tests establish only their declared reducer/helper
extent. The matched helper remains unexecuted scaffolding.

The scheduling/support aggregate contains these disjoint pre-known components:

| Component, milliseconds | PAL | NTSC |
|---|---:|---:|
| Root owner remainder | 90.897 | 89.880 |
| Preview envelope/state support | 83.440 | 81.053 |
| Classification | 47.204 | 46.503 |
| Endpoint eligibility | 21.176 | 20.955 |
| Admission | 9.402 | 9.452 |

Whole-trial timer service is 77.038/79.310 ms, a subset of the primary service
category. Declined owner totals 64.670/71.614 ms overlap the primary categories;
they are not an additional latency bucket. The narrow repeated selected
classifier-zero cohort is only 5.962/1.292 ms. No dominant avoidable cost or
causal speedup is established by these measurements. Outside-callback time is
not necessarily idle or recoverable.

## Source-backed hypotheses, not correction decisions

Root routing and preview support are the larger unresolved ownership buckets.
Repeated eligibility includes 167 calls before the first selected contact
owner in each region, approximately 18.87/18.92 ms inclusive. Their accepted
generation and launch-saved state still need fencing. A cheap definitive
negative guard could address part of that work, but cannot explain the whole
latency. The private 318-byte state is retained in place; repeated public
retirement restores 72 history bytes. Full selected-state comparison is
PREVIEW_DEBUG-only, not a runtime cost to remove.

Timer calls have different duties. The first main-loop accounting supplies
keyboard ACK age through last_timer_count; the second tests whether the nominal
callback is due after hardware service; admission accounts planning age before
execution. Removing any call solely because the aggregate is large would lack
a timing/ACK justification. Faster spins can consume the same remaining
reservation capacity without advancing endpoint delivery.

Reason-qualified refusal suppression must be candidate-specific. Monotonic
slack within an unchanged nominal interval may justify a timer-only negative
result. Beam and latch refusals need reconsideration at their actual window or
visible rearm. Preserve selected endpoint refusal without dense advancement,
residual-turn rotation and refused-footer smaller-prefix fallback. Clear or
revalidate on every callback, any optional progress, generation/selection or
variant change, cancellation, seek, resume, title/entry, and relevant producer,
footer, animation or presentation changes. Positive cached budgets still need
current-slack fitting and fresh admission. No arbitrary delay is proposed.

## Minimal read-only queries for the coordinating parent

Use existing retained traces, sequentially PAL then NTSC, fresh-D only first.
Verify input hashes from the custody manifest and preserve original receipts.
Return a compact JSON/table; do not repeat native tests or transfer giant raw
files. Keep unavailable fields explicitly unknown. These queries request
observations, not reconstruction of an absent execution ledger.

1. Fence the accepted generation and split input-to-contact-owner,
   contact-to-endpoint-known and endpoint-known-to-COPJMP. Within each, split
   the original disjoint categories by accepted owner, declined owner and
   outside-owner. Retain IRQ elapsed once and instruction gaps unclassified.
2. Decompose preview support, root remainder, classification and remaining
   mandatory callback
   using existing nested call identities. Assign each primary segment to its
   deepest observed containing call, with enclosing self remainder explicit;
   report count and disjoint CCK by routine. Do not sum inclusive parents.
3. Export one row per callback epoch with accepted preview/endpoint owner
   budgets, actual operation sequence/spent count, branch variant and observed
   cursor/count/flight/query-stage progress. Include intervening no-progress
   owners, their class/admission call counts and measured spans. Distinguish
   selected, other-branch and footer-fallback routes only where witnessed.
   Retain available slack, beam and latch predicates beside budgets where
   observed; absent values remain unknown.
4. For repeated unchanged owners, report zero-budget and admission refusal
   separately. Identify predicates only where emitted control flow and captured
   inputs suffice. For the 167 pre-contact eligibility calls, fence generation
   and launch_saved using actual stores/snapshots; separate root checks from
   endpoint API validation. List missing values rather than invent reasons.
5. Split timer-accounting calls by emitted callsite (first main-loop, second
   main-loop, admission and other). Report count and primary-mask disjoint CCK;
   count coherent-read retries only where witnessed. Export post-callback slack
   and refusal slack/window observations where reconstructable. This tests
   whether service volume follows repeated futile root attempts.
6. For the 21–22 ms known suffix, export endpoint-ready return, qualified/dirty
   transition, producer entry/exit, complete_scene, ready-bank identity,
   latch/beam observations and qualified COPJMP. Preserve the distinction
   between endpoint computation, bank production and publication opportunity.

## Prerequisites and holds

At the transfer review this environment had pinned Python and native assets; an external kick13.rom
attachment is present. The pinned assembler, Copperline, machine68k, amitools,
local emulator configuration and preserved native development/listing products
were absent. Subsequent supported [tool setup](tutorial-latency-execution-setup.md)
establishes the tools/configuration and validates the ROM against both retained
bindings, without building or running the game. Preserved native products and
raw traces remain absent. Available storage here is ample; the old
proposal's small-storage observations do not describe this environment.

The missing traces are an internal handover, coordinated by the parent. Do not
ask Richard to supply them or upload them to Library/GitHub. A concrete
correction still requires independent review and matched deterministic states
and physical input schedules, preserving gameplay, preview/exact-resume
contracts, ACK, generation retirement and both-branch fairness. Appearance,
resources, normative deadlines, physical resume, stripped cold release and
full-release holds remain; no merge or release is authorized.
