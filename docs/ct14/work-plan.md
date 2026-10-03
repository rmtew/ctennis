# Match simulation delivery checklist

Design: [deterministic core and Shot Doctor](README.md).
Status: proposal, **implementation blocked on user design review**. Checkboxes
track evidence-backed completion; none authorize code now. One concrete item is
active at a time. The user approved initial fixed preallocated rolling retention,
not overall implementation. Full recordings/background disk flushing are deferred.
Safe Exit is separate; PR #23 is now on master at
`70ed2e31b255f5161672944ef137af8b99bdd20d` and is not modified here.

Ownership: implementation integrator = this delegated implementation owner after
approval; reviewer assignment = parent coordinator; product decisions = user.
Independent review precedes every merge. Reviewers must not be the change author.
Reconcile with the accepted release commit before M1 and name it in receipts.

## Design review (current item)

- [x] Audit existing packets, entropy, scene/audio/control/lifecycle dependencies.
- [x] Propose state/input/events, history policy, branch semantics and gates.
- [ ] Parent assigns core/determinism and native/resource reviewers.
- [x] User approves a fixed preallocated rolling buffer, no allocations during
  play, with checkpoint-aware eviction and truthful oldest available history.
- [ ] User reviews live RNG change, pause/resume and branch policies; overall
  implementation approval remains pending.
- [ ] Resolve findings; approve design before runtime architecture work or merge.

## M1 — Deterministic isolated core

Owner: implementation integrator. Review: core/determinism + native/resource.

- [ ] First small proof: inventory ownership and observe complete native step
  order, then execute a short serve/contact/point-to-next-serve sequence with
  existing native routines in an isolated runner, including sound wait and a
  release/repress during transition. Initialize once; feed controls/entropy only.
  Compare all owned state and outputs each boundary. Prove repeated lifecycle
  polls are idempotent or retain the required explicit subphases. Stop for review
  if the proposed boundary changes timing; do not start recorder/UI work first.
- [ ] Produce machine-checkable writable-state inventory, relocation/pointer
  rules, bounded scratch/event contract and proposed canonical state layout.
- [ ] Specify and emit the minimum diagnostic schema at actual decisions, define
  missed-window eligibility/aggregation/tie-breaking and owned accumulator state;
  cover human/AI, automatic contacts, suppression and absent-action cases.
- [ ] Specify the recorded resume command, exact control-field allowlist and
  command cursor; world/score/RNG and other non-control state cannot change.
- [ ] Extract actual 68000 core shared by native and standalone; preserve widths,
  order, scoring and animation/status/cue semantics. Renderer and Paula are sinks.
- [ ] Seed deterministic entropy once; version streams and initialization; keep
  canonical attract seed/8-bit initialization and independently frozen hashes.
- [ ] Validate full-state/event differential runs, poisoned initialization,
  hardware-read/out-of-state-write guards, both modes/ends and lifecycle waits.
- [ ] Record state bytes, instruction/table/data/BSS deltas, stack, worst observed
  cycles/CCK including fresh input and transitions; distinguish static audit,
  host execution and native measurements.
- [ ] Gate: independent review, existing relevant contracts + canonical fixture,
  no unresolved hidden state/order mismatch; approved layout and capacity study.

## M2 — Record, checkpoint and seek

Owner: implementation integrator. Review: determinism + native/resource.

- [ ] Version header/state/input/event formats and exact build/table compatibility;
  validate corrupt/unsupported input without partially restoring state.
- [ ] Record logical controls/edges/phases, boundary commands and ordered events;
  choose 32/64-bit history index from duration/overflow and measured bytes/cycles.
  Implement bounded storage and atomic checkpoint/cursor commit.
- [ ] Freeze diagnostic payload widths, missed-window aggregation and maximum
  per-step event/encoded-byte burst before capacity selection. Include simultaneous
  contact/window/award/lifecycle/cue events and checkpoint all open accumulators.
- [ ] Prove transactional overflow: publish no partial batch, retain last complete
  boundary/status, stop capture explicitly, and preserve gameplay progression and
  required outputs. Inject event-buffer and storage exhaustion independently.
- [ ] Prove headless pause/live isolation through the instant before resume;
  replay recorded resume commands and verify only declared control fields/cursors
  change. Handle unrecordable resume through the explicit capture-stop contract.
- [ ] Measure uncompressed/encoded bytes per minute, point and observed match,
  compression behavior, worst bursts/noncompressible inputs and seek latency.
  Select H/K, live/doctor instance costs and bounded seek slice from that evidence;
  review measured capacity/retained-duration tradeoffs before freezing allocation.
- [ ] Preallocate the fixed rolling buffer and all required recording workspace
  before play; verify no allocations during play, including wrap and eviction.
- [ ] Add sparse complete checkpoints, nearest-checkpoint seek and atomic
  checkpoint-aware eviction retaining a complete replayable suffix. Expose the
  truthful oldest available history and capacity status; no dangling index/cursor.
- [ ] Retain recording-cost evidence for a later full-recording/background-disk-
  flushing decision; neither capability is part of this initial implementation.
- [ ] Replay every tick from each checkpoint through its next interval boundary;
  test all seek targets within capped-K intervals plus selected finite long-span/
  full-match runs. Avoid quadratic checkpoint-to-end campaigns. Compare full
  state/events/command and recorder cursors from poisoned working states.
- [ ] Exercise modulo-256 wrap, long rally/deuce, service waits, corrupt snapshots,
  capacity exhaustion, ring wrap/eviction and omitted-state negative controls.
- [ ] Gate: exact seek equivalence; bounded RAM/time on target and no silent loss;
  independent review and affected native metrics/contracts completed.

## M3 — Explanations and history UI

Owner: implementation integrator. Review: core rules + native UI/resource;
parent coordinates user review of diagnostic wording and browser behavior.

- [ ] Translate the M1/M2 reason/window records into factual explanations for
  human and AI shots, faults and missed opportunities. Schema/instrumentation and
  capacity contracts are already gated; any new requirement returns to M1/M2 review.
- [ ] Add keyboard-invoked paused history browser and state reconstruction with
  visible retention limit, actual shot/opportunity navigation and factual reasons.
- [ ] Connect the UI to the M2 isolation/resume contract during rally, sound wait,
  round exchange and result lifecycle; disable pre-match entry.
- [ ] Verify UI browsing/cancel preserves all live bytes/cursors until resume,
  then invokes the recorded control-only command. Measure UI construction and
  transition worst cases on target.
- [ ] Gate: independently checked diagnostic examples for faults, direction and
  failed/unexpected returns; no unsupported causal advice; native input/render/
  deadline tests and reviewed resource report pass for exact implemented head.

## M4 — Replay and counterfactuals

Owner: implementation integrator. Review: determinism + native/resource;
user reviews comparison semantics, parent coordinates final acceptance reviewers.

- [ ] Replay actual selected shot/window with full-state/event equivalence, bounded
  horizon and isolated, initially silent presentation.
- [ ] Fork before decision, edit tick-addressed logical actions, preserve original
  record and show first divergence/outcome; discard branch on exit.
- [ ] Implement and label reactive AI comparisons; demonstrate differing RNG call
  orders and avoid claiming same seed produces paired randomness.
- [ ] Separately review fixed-opponent trace scope: capture actual AI decision
  boundary/state and detect inapplicable decisions. Defer explicitly if not
  approved; never substitute joystick packets or a second AI model.
- [ ] Test repeated forks, unchanged-action identity, cancel/resume, old-history
  limits and bounded capacity/horizon, including branches crossing point/round.
- [ ] Gate: independent review, user comparison acceptance, exact-head finite
  native acceptance and reviewed state/code/RAM/worst-cycle metrics. Integrator
  assembles evidence; parent coordinates reviewer signoff before merge.

## Evidence for this docs-only proposal

Source audit at `5e3fa7434fc88f0688f8338bb30fb426b7559f14`; no runtime code,
recording, golden or metrics summary modified. PR #23 head was verified by
`git ls-remote --heads origin`, not inspected as another worker's workspace.

`python scripts/native_metrics.py --check` was attempted and **could not certify
reuse**: this checkout lacks
`build/amiga/interfaces/enhanced/baseline-rally.compile.json`. No emulator campaign
or native acceptance was run for these documents; this failure says nothing
about release acceptance. PR #23 subsequently landed at the release commit named
above; this update does not rerun or alter its acceptance. Docs validation checks local
Markdown links, whitespace and the docs-only diff. Publication receipt (commit,
PR head and actual checks) belongs in the handoff, not a self-referential document.
