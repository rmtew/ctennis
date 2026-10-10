# Coherent tutorial scheduler implementation plan

The user approved this design after independent architecture and timing review. Implement one deadline admission owner, independently resumable alternatives and bounded useful prefixes, preserving the actual shared physics and existing record format. [The normative specification](tutorial-deadline-scheduling-design.md) defines pass/fail requirements; this document maps that end-state to reviewable increments. Implementation is authorized; merge and release remain held.

## Why the architecture changes

[PR46's retained contact probe](tutorial-physics-background-results.md) accepted sixteen contacts, all nominal and none inside background owners. Preceding gaps were 32,112–32,926 CCK, but prerequisite preparation and intervening service often consumed roughly 8,000 CCK before dispatch became ready. The experimental dispatch admission required 25,000 CCK and a beam ceiling of line141. Other gaps lost prerequisite beam eligibility first. Motion-only admitted owners peaked at 8,112/8,140 CCK; those observations do not bound contact or transition tails. The 20,000 CCK owner allowance remains an unverified hypothesis.

The issue is scheduling readiness and ownership, not a reason to exclude contacts to obtain passing coverage. A two-envelope patch addresses only one repeated-wrapper cost. Whole-contact atomic execution would instead make an unbounded flight monopolize service. Arbitrary instruction preemption would introduce register/state ownership problems throughout the actual core. The approved design uses existing logical boundaries and separates expensive completion jobs.

The worker already retains private318 in place across operations; public release restores72 bytes of history metadata. This plan reduces redundant public validation/accounting/service and hidden tails, not a fictitious318-byte copy on every envelope. Actual overhead and benefit require new measurements.

## End-state

One native main-loop scheduler derives actual deadlines and chooses bounded optional jobs both during the nominal scheduling path and between callbacks. Mandatory callbacks keep original logical sampling, live-update duties, fractional time and catch-up behavior. Preview never resets clocks, adds live samples or acquires hardware-service authority. Transport pumping is distinct from logical edge consumption. There is one admission/class policy, rather than separate callback and background allowances.

Held and released alternatives each own their progress, phase, cursor, private state, dense samples, endpoint and terminal status. Origin resolution may remain shared immutable preparation. The scheduler-facing interface selects one variant and executes a bounded ordered prefix toward the next simulated tick/sample or explicit safe phase boundary. It retains preparation if dispatch cannot fit, then resumes without repeating envelopes. Contact/outcome is a goal reached over many prefixes, not the quantum. Preserve the legacy step API and its deterministic default; independently completing released first cannot imply both are ready.

Every envelope retains its actual shared-core call, order, checks, RNG effects, event and cursor updates. Recording remains simulation data, not a list of worker packets; grouping needs no recording-schema change. Exact recorder/seek/playable/preview APIs retain complete318 plus ordered-output equality. The already qualified observational preview API retains its declared launch/sample/outcome/cursor contract and complete public isolation; reduced private incidental state cannot become a playable checkpoint. Unsupported origins begin exact fallback from the immutable edited origin.

The worker reports its next phase/class and progress at safe boundaries. Admission may cover a verified multi-envelope prefix, avoiding re-entering public wrappers for each preparation operation. Time is checked freshly before admission and at declared extension/transition fences; already-accounted slack can cheaply reject hopeless work. A fence cannot retrospectively make an oversized atomic body safe. No live hardware/input reentry is allowed while private simulation owns history metadata.

Endpoint queries, geometry comparison, rendering and producer completion are explicit generation-owned jobs with their own cost classes. Appending a terminal sample cannot silently run a geometry scan, outgoing continuation or other alternative. A contact/lifecycle shared helper needs a justified complete bound; if it cannot meet service obligations atomically, add an explicit safe cooperative continuation in that actual helper, preserving its ordered algorithm and intermediate-state contract. Do not duplicate physics or arbitrarily preempt instructions.

Priority is mandatory service and due visible work, selected endpoint prerequisites/query, finite selected sample lookahead, then eligible residual alternatives and optional raster jobs. Normal-speed animation consumes actual samples at the existing nominal cadence; computation does not accelerate visible motion. Exhausted lookahead holds the last actual sample and reports waiting. A finite lookahead waterline and eligible-opportunity age make residual service accountable, without promising progress under sustained edits, open menus or overload. Stable-generation waiting and insufficient capacity must remain visible in evidence.

Private prediction is constrained by obligations it can delay, not a blanket beam-line ceiling. Preserve the exact guarded publication window, coherent beam reads, interrupt masking, immutable banks and one-commit-per-field transaction. An IRQ may publish an earlier complete bank during private work, but cannot finish a producer or provide visible-line latch rearming. The current empty first-window attempt consumes that field opportunity; this plan does not silently change the latch rule.

Background production needs an audited generation-owned completion path. Existing `complete_scene` can already mark completion between completed callbacks when started equals completed, so this plan does not require a new readiness ABI/counter. Reuse existing bank rotation after all bank/sprite bytes and generation identity are complete; never fabricate a completed callback. Callback rendering remains a declared conservative fallback until a particular background class is supported. Generation change, cancellation, selection/history mutation, seek, resume and title transitions retire dependent jobs and ready markers before live work resumes.

## Stage 1 implementation and declared extent

The working implementation now provides the coherent owner and explicit jobs below. This is source implementation status, not independent correctness, ownership or timing clearance. The machine-readable [cost policy](tutorial-coherent-cost-policy.json), schema1, deliberately reports `experimental-hypotheses-only` and `normative_s05_s18_g2_safety=false`. Existing recording schema and physics are unchanged.

| Interface/job | Implemented boundary and contract | Experimental reservation, E-ticks |
|---|---|---:|
| Legacy `game_preview_step` | Generation plus budget1..4; retains deterministic legacy behavior and complete legacy tails | Complete applicable call must be reserved |
| `game_preview_step_variant` | Generation, budget1..4, variant0..1; independent branch progress, no implicit branch switch or geometry scan | Prefix sums each admitted envelope |
| Cheap envelope/rejection | Original ordered body/check/cursor; persisted preparation | 1,000 per envelope |
| Guarded projected dispatch | Old causal one-root phase/geometry domain retained for the cheaper class | 4,000 |
| Other projected/full dispatch or resolution | Actual shared dispatch; not excluded merely because physics/contact is expensive | 10,000 |
| Outgoing ball step | Actual shared continuation | 4,000 |
| Endpoint query | Separate selected-variant query | 9,000 |
| `game_preview_complete` | At most eight original geometry-point comparisons; branch results remain available before pair READY | 1,000 |
| Placement/animation producer | Generation-owned actual render and existing bank completion | 4,000 |
| Menu renderer | One unit per root job | 9,000 |
| Footer stage | Build unchanged caption bytes in private512-byte scratch; request/redraw only marks dirty | 9,000 |
| `tutorial_footer_commit` | Separate generation-qualified512-byte live overlay copy, admitted outside actual DMA lines236..251 | 1,000 |
| Result metadata | Separate result publication bookkeeping | 1,000 |

Every admission additionally reserves500 E-ticks for root service and500 for residual uncertainty; next nominal sampling and complete callback bounds remain separate. At five CCK per E-tick, guarded dispatch retains the old20,000 CCK owner hypothesis; other projected/full dispatch uses50,000 CCK, not a threshold reduced to force a contact witness. Full/endpoint/footer and producer reservations retain earlier experimental magnitudes. Newly broadened contexts, outgoing/geometry/footer paths still need complete measurement and analysis. Neither inherited nor new allowances are approved WCET.

The root chooses selected endpoint prerequisites/query, then an eight-sample lookahead waterline. After readiness/lookahead, residual other-branch progress alternates with eligible footer stage/commit; only fitting eligible work progresses. This is a finite internal policy, not an approved wall-time fairness guarantee. One renderer unit per root job and explicit footer staging keep live overlay construction out of prediction tails. The actual byte output, DMA exclusion and generation retirement still require verification.

Source-declaration attribution is10 additional preview metadata bytes,16 bytes of root job/residual/completion metadata,6 footer ready/generation bytes and512 bytes of footer scratch:544 additional declared mutable bytes. These counts are not linked-image RAM telemetry or target-fit evidence. Added executable bytes, stack peaks, memory placement, initialized chip free/largest block and full resource profiles remain to be measured and reviewed. Match state318, public release metadata72 and recording schema do not grow from worker grouping.

No stage1 implementation checkbox implies the expensive full/lifecycle classes, read/write ownership, IRQ entry/tail interference, coherent-read/beam bounds or resource gate passed. Unsupported or violated classes must remain explicitly blocked or experimental; retaining their failure evidence is mandatory.

## Implementation sequence and tracked checklist

The integrator owns source integration and evidence reconciliation. Colocated architecture/correctness and timing/integration reviewers challenge each increment and the final enabled path. The parent coordinates review. Review gates constrain claims; they do not require repeated user approval for authorized mechanical work.

- [x] State the complete coherent end-state and revise S02–S10/S18/S21–S23 authority and verification scope. This check marks drafting only; independent review remains pending.
- [x] Implement the explicit variant worker, independent progress/persisted preparation and separate eight-point geometry completion alongside the legacy API. Source drafted; equivalence/ownership evidence remains pending.
- [x] Complete the first proof: selected released-first and held-first executions with preparation-only yield, intermediate grouping comparison and canonical/history isolation. The reviewed56-case CPU receipt and independent-reference qualifications are recorded in [verification results](tutorial-coherent-scheduler-results.md); this is not native scheduling acceptance.
- [x] Implement one root optional-job admission owner, classed prefixes and obligation-specific beam checks; remove competing optional callback work. Source drafted; input/repeat, clock and deadline correctness still require review.
- [ ] Audit every class/transition tail and clock/read/IRQ/release path against actual input, latch and publication obligations.
- [x] Implement selected endpoint priority, eight-sample waterline, residual alternation and explicit one-unit producer/menu/footer jobs. Footer has private staging and a named live commit. Source drafted; capacity, fairness, completion/publication and unchanged output evidence remain pending.
- [ ] Verify producer/completion ownership and legacy fallback extent, selected sample cadence and eligible residual age under actual workloads.
- [ ] Extend actual-core differential proofs and negative controls; obtain reviewed class bounds or declare experimental hypotheses/unsupported classes. Bound expensive contact/net/out/fault/lifecycle paths or implement actual-core cooperative continuations where necessary.
- [ ] Run selective resumable paired PAL/NTSC checks with actual substantive background contact, input/ACK, producer/readiness/publication and sample observations. Retain every failure and unsupported partition; report exact declared extent.
- [ ] Reconcile code/data/RAM/stack and initialized target resource profiles; publish reviewed source/docs/evidence on draft with verified remote head. Preserve appearance/full-release merge holds.

## Verification and policy decisions

CPU proofs run actual emitted shared routines against matching original edited-origin references. Compare complete state/events/cursors for exact entry points and every declared observation for projected entry points at all intermediate envelope/tick/contact/outcome boundaries. Exercise poisoned working state, randomized grouping/interleaving, both branch orders, repeated/stale calls, changed input, both ends, cancel/seek/resume, retention/generation wrap and terminal/geometry transitions. Audit writable globals, unclassified writes and forbidden canonical reads. Preserve the independent frozen recording/seed; do not generate expectations from the new worker.

Native checks use physical production controls with fixed origin/seed for paired comparisons. They must witness background contact rather than merely a successful contact somewhere in the capture. Include fresh and held edits, releases/aliases, long chunks, selected switches, short/rejected queries, missed contact and costly serve/net/out/fault/lifecycle tails. Verify actual completed bank bytes, producer epochs, COPJMP, sprite/DMA ownership and normal-speed samples. Measure useful simulation, wrapper/validation, accounting/service, refusal/wait and completion/render costs without double-counting nested spans. Report elapsed distributions, worst observed paths, entry lateness, input/ACK gaps, endpoint/sample/publication latency and explicit unsupported coverage.

Cost classes include complete ownership/release and mandatory deadline tails with stated chip-DMA/IRQ assumptions. A maximum observed cost plus margin is a hypothesis, not WCET. Conservative reversible internal calibration values may be selected and labeled for experimentation; no invented speedup, resource ceiling, no-frame-drop guarantee or normative safety pass is allowed. Unbounded or unsupported work declines optional admission. Preserve immutable resumable campaign receipts, stable IDs and shared locks; inspect ownership before reconnecting, never duplicate a long campaign after disconnect.

The remaining genuine product choices are an explicit supported input/transport response contract, terminal visible dwell policy if it changes existing behavior, and finite lookahead/residual fairness guarantees supported by capacity. Propose evidence-backed values; ask only if the choice changes user-visible behavior or the desired guarantee is unattainable. Continue independent implementation while such a decision is pending. Pure implementation staging, record grouping and reversible internal calibration do not require another scope approval.

Historical PR46 negative evidence remains unchanged. This plan establishes no new runtime acceptance. Appearance, complete resource coverage, exact stripped-release cold boot, full native release catalog and independent merge review remain open. No asset/raw-evidence uploads or optional sprite/trail redesign are part of this work.
