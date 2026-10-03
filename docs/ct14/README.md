# Deterministic match core, recording and Shot Doctor

Status: **design proposal; user review required before implementation**.
Audit base: `5e3fa7434fc88f0688f8338bb30fb426b7559f14` (master).
PR #23 has since landed on master at
`70ed2e31b255f5161672944ef137af8b99bdd20d`. This docs-only proposal does not
modify that release or supply its acceptance evidence. The source audit below
remains at the stated older base; reconcile against the accepted release before
implementation. Safe Exit remains
separate unfinished work, not a prerequisite. Delivery tracking is in
[the milestone checklist](work-plan.md).

## Intended experience and constraints

A keyboard command pauses the match at a complete simulation boundary and opens
Shot Doctor. Browse human and AI serves, returns, attempted returns and missed
contact opportunities. Explain faults, chosen direction and unexpected or failed
returns using facts captured where the native rules make the decision. Replay
the actual shot, then try different simulation actions from the same prior state.
Closing the doctor resumes the untouched live match. A speculative branch never
silently becomes the live match.

One compact 68000 core must run in the native game and a standalone test harness.
No separately rewritten physics/scoring model, callback-regime injection or
expected-state injection. Preserve integer widths, wrapping, comparison order,
scoring, animation-dependent timing, sound-gated transitions and existing
input suppression. PAL A500/OCS, 512KB chip, no slow/fast RAM remains the target.
Optimal means measured simplicity: contiguous state, static immutable tables,
preallocated bounded buffers and no allocations during play; do not claim optimality before
measuring code size and worst-case cost.

## Findings rechecked in the repository

| Evidence at audit base | Design consequence |
| --- | --- |
| [gameplay_state.i](../../amiga/game/gameplay_state.i) declares 60 bytes; [scoring_state.i](../../amiga/game/scoring_state.i) declares 28 | These packets are not the complete simulation. |
| [state.i](../../amiga/game/state.i), [controls.s](../../amiga/game/controls.s), [tick.s](../../amiga/game/tick.s), round/result integration own flags, clocks, held/edge/latch and lifecycle state outside those packets | Inventory all mutable dependencies, not just named gameplay packets. |
| [audio_state.i](../../amiga/game/audio_state.i) has three 32-byte voices (96 bytes), including native pointers; [result_audio.s](../../amiga/game/result_audio.s) observes `AV_DONE` | Sound sequencing affects the next serve/round. A silent runner must advance deterministic cue state; copying raw voice pointers is not a portable snapshot. |
| [scene.s](../../amiga/game/scene.s) changes animation flags, images, clocks and court Y; [scene_fields.s](../../amiga/game/scene_fields.s) exports display flags/status clock | Removing rendering calls alone changes gameplay. Move these semantic mutations into the core in the same order. |
| [main.s](../../amiga/main.s) polls `game_round_poll` between callbacks, samples input before dispatch, renders previous prepared geometry; [round.s](../../amiga/game/round.s) advances lifecycle | Callback entry alone is not a complete step. Define and prove the inter-callback boundary, including release during sound waits. |
| [interface_demo.s](../../amiga/game/interface_demo.s) uses `galois16-b400-v1`, seed `$ace1`, RLE packets; [metrics](../metrics/current.md) attributes 1,110 loaded bytes to replay packets | A deterministic attract input source exists, not a native match recorder or checkpoint system. The table size is one recording, not a capacity forecast. |
| [main.s](../../amiga/main.s) mixes CIA timer bit with the 8-bit `game_random_seed`; [gameplay_players.s](../../amiga/game/gameplay_players.s) updates it as `5*x+1` modulo 256 | Live entropy must become match-seeded and entirely state-owned. |
| [fixture manifest](../../tests/fixtures/native-demo/manifest.json) binds 10,958 digests to a 90-byte preimage (60+28+2) and its recording/seed | Host hashes are regression evidence, not snapshots or completeness proof. Keep them frozen. |
| [integration.s](../../amiga/game/integration.s) wraps `game_tick` at 256; scoring permits repeated deuce and rallies have no finite bound | History needs a separate monotonic index and an explicit finite-memory retention policy. |

These are source/layout observations, not a completed writable-global audit or
measurements of a proposed core. No `.agents/skills` directory or additional
`SKILL.md` was present in this checkout; repository `AGENTS.md`, README, tests
README and CT11 risks govern the work.

## Proposed ownership and interfaces

Use a state-base register and assembly offsets rather than an object framework.
Link the **same assembled core routines and rule tables** into native and
standalone targets; compare their normalized code/table bytes (accounting only
for declared relocations). The host runner executes that 68000 code in a CPU
harness with no CIA/Paula/Copper services. It may supply memory, stack, input and
collect output; it must not implement game rules. Native target checks retain
hardware timing/publication coverage the standalone harness cannot establish.

Proposed logical interface; symbols and exact packed offsets are M1 review work:

| Entry / record | Contract |
| --- | --- |
| `match_init(config, seed, initial_controls, state)` | Initializes every owned byte, including padding; mode, rules version and logical A/B identity explicit. Selection-held suppression is initialized explicitly. No hardware reads. |
| `match_step(state, input, event_buffer)` | Advances one scheduled simulation tick through defined pre/post phases; mutates only state, bounded event output and declared scratch/stack; returns ordered events and a read-only view. No I/O, wall clock, allocations or global singleton dependencies. |
| `MatchState` | Gameplay/scoring; logical player/end/controller ownership; held/edge history and suppression gates; lifecycle and pending transitions; animation/status clocks and semantic display flags; all RNG state/cursors; logical sound sequence/cue state; monotonic tick and event sequence. Add any dependency found by audit. |
| `TickInput` | Tick index, logical A/B held masks and pressed/released masks, ordered within-tick phase if more than one semantic sample is necessary; match commands at explicit boundaries. Directions and action1/action2, not hardware keycodes. Validate edge consistency. |
| `TickEvents` | Tick, phase, sequence, actor, kind and typed payload; stable order. Includes resolved AI decisions, contact diagnostics, launches, bounces, faults, awards, end exchange, lifecycle and sound requests. Bounded capacity with explicit overflow result, never silent truncation. |
| `match_encode/decode` | Canonical complete state with lengths, endian/width rules, zero reserved bytes, validation and integrity checks; no native addresses. Restore failure leaves destination untouched. |
| `match_view(state)` | Pure derived scene/score/status values. Rebuilding or skipping a view must not advance simulation or RNG. |

The state inventory must classify every writable symbol and alias as core,
input adapter, presentation/audio hardware, recorder, or scratch. For each
excluded value document why it is derivable or overwritten before read. Include
cached flags, counters, queued requests and indirect-pointer targets, not just
`dc` declarations. Raw CPU registers/stack are not checkpoint state: save only at
returned step boundaries with no suspended call frames.

Physical sampling, keyboard mapping and device merging belong to the input
adapter. Record the canonical logical controls **before simulation suppression**;
keep suppression gates in MatchState so replay can explain an ignored press.
If intra-tick input ordering affects behavior, retain ordered phase-stamped
logical samples; do not collapse press/release to a final held value. Pause/UI
keys are session commands, not ball-control data. AI internals remain core-owned:
record their resolved actions/decisions as output as well as human input, so both
actors can be inspected without pretending AI consumes joystick packets today.

Renderer ownership includes Copper lists, sprite DMA, palette banks and prepared
geometry. Move animation/court/status mutations out of renderer paths, preserve
the previous-scene publication relationship through the adapter, and rebuild
presentation from state on seek. Renderer callbacks cannot write MatchState.

Audio has two parts: a deterministic logical sequencer (including cues that gate
lifecycle) and a Paula sink. Initially retain the existing sequence semantics,
including last-loaded `AV_DONE` versus complete-phrase distinctions, using clip
IDs/offsets rather than addresses. Immutable timing tables are rules dependencies.
Only remove redundant voice fields after equivalence proves they cannot affect
future state/events. Muting or omitting Paula must not change the core. Exact
waveform phase during doctor resume is a separate presentation policy, not a
source of match progression.

### Step order and lifecycle proof

Define `S[n]` as the quiescent state immediately before canonical controls for
tick n; `step(S[n], I[n]) -> S[n+1], E[n]`. Tick n covers service-only waits as
well as active rally work. The modulo-256 gameplay clock remains unchanged;
a separate unsigned history index advances once per step. Choose 32 versus 64
bits at M1/M2 using supported recording duration, overflow handling, state/storage
bytes and measured 68000 cost; encode the width in the schema. Exhaustion ends
recording explicitly, never wraps into an old record.

First instrument the existing call order: between-callback round/result polls,
physical/logical samples and latch retirement, dispatch, scene semantic changes,
scoring, gameplay, clock advance and audio sequencing. Propose a fixed pre-input
lifecycle phase, existing dispatch/tail order, then a post-tail lifecycle drain
to the next wait. **This is conditional on proof**, not permission to move a
poll across input: test repeated polls for idempotence and all transition cases.
If polling observes distinct samples or has repeated non-idempotent effects,
encode the required bounded semantic subphases/input sequence instead. Neither
wall-time poll counts nor captured callback kinds may select a replay regime.
Boundary/order uncertainty blocks extraction acceptance, not just UI delivery.

### Entropy and behavior migration

Acquire a seed once outside the core at match start (CIA sampling permitted
there), or accept an explicit test seed. Store the seed, PRNG algorithm/version
and initial streams in the header; every subsequent draw uses state-owned PRNG.
Proposed first implementation retains the existing 8-bit game PRNG plus the
16-bit deterministic entropy adapter initialized once; no mid-match reseeding.
Reject/map zero LFSR seed by a specified rule. The canonical demo retains its
recorded `$ace1`/initial-8-bit-zero configuration and frozen expectations.
A stronger generator or independent streams would require a new rules version
and review, not an incidental refactor.

Structural extraction should preserve behavior for identical inputs and supplied
entropy. Live CIA removal intentionally changes live random trajectories; it
cannot promise the same unrecorded historical live match. Separate that change
from extraction with controlled entropy comparisons and user approval. Do not
regenerate the 10,958-tick golden from the new implementation to hide drift.

## Recording, checkpoints and seek

Version a recording header with magic, container/schema version, rules/PRNG/input/
event/state versions, exact core build identity, immutable table hashes, mode,
seed, initial controls, tick rate, byte order, retention origin and completeness.
Initially support exact compatible builds only; reject unknown versions, table
mismatch, corrupt length/checksum or unsupported rules. Display a clear
incompatibility result. Cross-build migration/replay requires a separately tested
reader/core version, not a best-effort decode of today's offsets.

Record control changes with tick deltas/RLE only after preserving held states,
edges and phase ordering. Keep ordered output events and an index of shots,
opportunities and point boundaries. A checkpoint contains a complete encoded
MatchState and recorder reconstruction metadata: absolute tick, input block/run
cursor including remaining count and held baseline, event cursor/sequence,
index origin and rules/build identity. No pointer into ring storage survives
serialization; cursors use validated sequence IDs/offsets. State and recorder
cursors are a single committed boundary. Indexes can be rebuilt from retained
events; indexes referencing evicted events are invalidated.

Checkpoint sparsely at a measured periodic interval K plus useful point/serve
boundaries. Bound the maximum gap by K even during arbitrarily long rallies.
Seek chooses the newest checkpoint at or before target n, restores into a
separate working instance, and runs the same core through inputs to S[n]. It
compares/reconstructs events in order without presenting old sounds or awarding
live points. Checkpoint exactly-at-target does no extra step. Browsing uses
bounded work slices so the paused UI can cancel a long seek.

A complete match cannot be guaranteed in finite RAM: deuce and rally length are
unbounded. **User-approved initial retention policy:** a fixed-size, preallocated
rolling buffer, with no allocations during play. Show the truthful oldest
available tick and “earlier history unavailable” notice. Evict only complete
checkpoint-led segments, atomically retaining a complete replayable suffix: a
usable base checkpoint and all controls, commands and events from that base to
the completeness watermark. If a segment cannot fit, stop recording with an
explicit capacity status while play continues; never retain an unseekable tail
or overwrite live/doctor state. Pinning a browse range cannot grow the buffer.

The numeric capacity is not yet chosen. Measure bytes per minute, point and
match, compression behavior, worst bursts and seek latency before final capacity
selection. Full recordings, export/streaming and possible background disk flushing
are deferred, evidence-based future decisions, outside initial scope. Finite
observed match sizes do not establish a bound for every possible match. Approval
of this retention policy does not approve implementation of the overall design.

Each recorder append is transactional: reserve/stage the complete input/command,
event and index batch, then publish its cursors and completeness watermark
atomically. On event-buffer or storage overflow, discard the uncommitted batch,
retain the last complete prefix and publish an out-of-band recording-stopped
reason plus last complete tick. Never mark a partial tick complete or continue
with an unmarked gap. Gameplay advances exactly once regardless of diagnostic
storage failure; required sound/lifecycle effects use core state or a separately
bounded required-output path, never depend on a lossy diagnostic queue. An event
buffer overflow also fails validation of the claimed maximum burst. Reserve the
small failure-status record independently of history capacity. Restarting capture
requires a new complete checkpoint/segment with a declared gap, not cursor reuse.

## Pause, explanations and alternative branches

Enter through a keyboard-to-session command at a completed tick; latch the live
state, recorder cursors and pending adapter presentation/audio context. Live
stepping, RNG, logical audio and recording stop. Doctor owns its own working
state and bounded event/scratch area. Playback sound is muted initially. All live
MatchState bytes and recorder cursors remain exactly invariant throughout browsing
and immediately before resume, including suppression gates. Restore adapter
presentation and discard doctor inputs/branches without changing that state.

Resume is an explicit recorded boundary command, ordered before the next tick's
controls. Its payload contains logical A/B held samples and carried-action masks;
it may change only the declared held/pressed/released baselines and suppression
gates, retiring carried action buttons until release without a synthesized serve
edge. The M1 state manifest names this exact allowlist. World, score, lifecycle,
clocks, tick, logical audio and RNG state remain unchanged by the command itself.
Commit the command/cursor transaction before subsequent recorded tick input;
replay applies the same command exactly once. Multiple commands at one tick use
an ordered boundary-command cursor, included in checkpoints. If recording cannot
commit, apply the command for live play but stop capture at the prior complete
boundary under the overflow contract; never imply that resume was recorded.

M1 specifies this command and M2 proves pause isolation/resume headlessly; M3
exposes the keyboard/browser flow. Seek/replay cannot append to live history.
Proposal allows any active-match quiescent boundary, including sound waits,
round exchange and match end; doctor entry before a match is disabled.

Define the minimum diagnostic schema and emission sites in M1, and validate the
encoded sizes, aggregation and maximum per-step burst in M2 **before freezing
history capacity**. M3 consumes these records for wording/UI, not a new schema or
late instrumentation. Minimum common fields are schema/kind, tick/phase/sequence,
logical actor and court end, shot/opportunity ID and causal parent ID. Typed
payloads must cover:

- Contact decision: controls/suppression, evaluated predicate ID, operands and
  threshold, accepted/rejected reason and relevant phase/contact flags.
- Launch/AI decision: serve/return kind, timing, resolved direction/target/vector,
  action choice and random perturbation/draw identity needed to explain it.
- Opportunity summary: start/end tick, outcome, closest evaluated geometry with
  its tick and predicate, and final failure reason; ongoing aggregation is owned
  checkpoint state, not a hidden UI accumulator.
- Fault/bounce/award/lifecycle: result kind, causal shot ID and outcome/transition;
  sound requests retain deterministic cue identity/order.

Packed widths, unavailable-field tags and maximum records/bytes per step require
M1/M2 review. Instrument decisions where rules execute, not a second explanation
model. A contact attempt event records actor/end, relevant phase/contact flags, input and
suppression, geometry/height, threshold comparison and accepted/rejected reason.
Existing contact checks include receiving side, flags, vertical distance <4,
horizontal distance <17 and height in [0,29); these are audit examples, not new
rules. Record first failing predicate plus measured operands; do not assert other
predicates were evaluated. A launch event includes serve/return kind, timing,
direction inputs, computed target/vector and any random perturbation. Fault,
net/out/bounce and point events link back to the causal shot.

A missed opportunity is not limited to action-button edges: some native contacts
are automatic. Define windows from the actual receive/contact eligibility
checks; summarize their open/close, closest evaluated geometry and outcome.
Define eligibility, close conditions and deterministic closest-sample tie-breaking
in M1. Maintain one bounded accumulator per actor/window; coalesce repeated
rejections, emitting a summary at close and explicit accepted/attempt decisions
as specified by the schema. Account for simultaneous close/open, contact, award,
lifecycle and cue outputs in the M2 maximum-burst bound. Rejected checks outside
a relevant window must not flood the history each tick.
Suppressed/unavailable action is separately distinguishable from an evaluated
geometric miss. Window aggregation and its state/size/burst contract must pass
M1/M2 review before capacity is frozen.
Human text translates recorded reasons: “outside contact width: …”, not “you
should have pressed …” unless that counterfactual was actually simulated.

Actual replay uses recorded controls and original RNG state, verifies identical
full state/events and highlights the selected shot/window. Alternatives fork
from a retained checkpoint reconstructed to **before** the relevant decision.
Change explicit logical actions over a tick range; preserve earlier history.
Label alternatives, edited controls, fork tick and first divergence. Compare
contact acceptance, target/direction, fault/return and point outcome within a
bounded horizon; do not present predictions beyond the simulated horizon.

Two distinct comparison modes must be visible:

- **Reactive AI** (proposed initial mode): the same core AI reacts to changed
  state, starting with the same RNG state. Different branches may make different
  random calls. Same seed does not guarantee paired randomness or an equally
  lucky opponent.
- **Fixed opponent trace** (later, separately gated): apply recorded opponent
  decisions at a documented AI decision boundary, including hidden target/shot
  decisions needed by this implementation. A joystick trace alone is insufficient.
  If the altered world makes a decision inapplicable, stop/mark the comparison;
  do not quietly fall back to reactive AI. This is a controlled scenario, not a
  prediction of normal opponent behavior.

No branch is committed to live play. Shared event-keyed random draws would be a
new rules model; defer rather than claiming the seed solves paired comparison.

## Resource process and completeness gates

Audited layout facts are 60+28 bytes for two packets and 96 bytes for raw audio
voices; their 184-byte sum is **not** an estimated complete checkpoint. The
existing report at this base lists 202,248 loaded payload bytes and a 182,192-byte
largest free block in its two-player case. These historical observations are
not a feature allowance, do not certify PR #23, and exclude some startup peaks.
No core/checkpoint size, K, history cap, seek latency or new worst cycles has
been measured. No proposed numeric allocation is approved here.

Before selecting capacities, measure state and checkpoint bytes, actual emitted
instruction/table/data/BSS bytes, stack high water, live+doctor working copies,
input/event/index costs, checkpoint scratch and largest contiguous chip demand.
Use `H >= checkpoints*(C+metadata) + inputs + events + indexes` and include all
non-history allocations separately in peak RAM. Stress noncompressible input and
maximum event bursts, not just the 1,110-byte attract table. Report uncompressed
and encoded bytes per minute, point and completed observed match, compression
ratios and worst bursts for named workloads; include long rallies/deuce and
noncompressible input. Measure seek latency across checkpoint intervals and
worst-case bounded slices. Establish maximum encoded record sizes and overflow
behavior before choosing final capacity. Choose H/K and the visible retention
promise from this evidence, then preallocate before play; if two instances do not fit, return
to design review rather than silently raising the hardware target.

Measure 68000 instruction cycles where available and elapsed native CCK including
contention; do not equate host runtime with target cycles. Track typical, p95 and
observed maxima separately from any proven upper bound. Include fresh presses,
release/repress and input merging, checkpoint creation/eviction, simultaneous
contact/award/audio events, service-only steps, serve/round/result transitions,
doctor entry/exit and worst seek slices as well as ordinary rallies. Existing
callback deadlines and publication checks remain mandatory. Record exact build,
inputs, target and checked extent; use the established metrics workflow only
after affected implementation validation.

Programmatic completeness is a release gate, not confidence from one hash:

1. Enumerate writable globals/aliases and transitive read/write dependencies;
   maintain a machine-checkable ownership manifest and explicit derived fields.
   Static reference audit plus emulator bus-write checks reject writes outside
   state/event/scratch/stack and reads of hardware/undeclared mutable globals.
2. Run identical inputs from initialization in native and standalone cores;
   compare every canonical state byte, ordered event payload and RNG/cursor at
   every boundary. Use native ordinary-flow observations in addition to fixtures.
3. From every checkpoint, replay every tick through the next checkpoint (or
   retained tail), comparing full state, events, input/RLE, boundary-command and
   event/index cursors with the uninterrupted run. Test every seek target within
   those intervals; cap K in the test plan so per-target seek tests cost O(N*K),
   not a checkpoint-to-match-end quadratic campaign. Add selected long-span and
   full-match replays with explicit finite extents. Cover exact boundaries,
   gameplay tick 255 wrap, service waits and ring eviction.
4. Decode each checkpoint into instances with different poisoned initial memory
   and relocated immutable tables/working addresses. Replay must agree. Poison
   scratch on entry; reserved serialization bytes are canonical. Repeat with
   renderer/audio sink omitted, muted or invoked at different display rates.
5. Negative controls omit a latch, RNG state, cue cursor or pending transition;
   inject an out-of-state write or stale cursor. The suite must reject each.
   Hashes may accelerate detection but byte/event diffs prove the mismatch.
6. Retain the independent 10,958-tick fixture and scoring/input/status contracts;
   add full-state differential evidence without claiming it is an independent
   rules oracle. Long deuce/rally, both modes/ends, restart and capacity tests
   use actual controls after one-time initialization, never intermediate state
   injection. Browsing/branches leave live bytes/cursors invariant through the
   instant before resume. Separately verify the recorded resume command changes
   only its declared control fields/cursors, preserves world/score/RNG, and replays
   exactly. Inject event/storage overflow: play must match a sufficient-capacity
   run while history ends at its last complete boundary with a failure status.
   The existing finite native gate remains the final native gate.

## Decisions requiring user review

The user has approved the initial fixed preallocated rolling-buffer policy.
Full recordings and possible background disk flushing remain outside initial
scope, to be reconsidered using measured recording costs. Numeric capacity and
overall implementation approval remain pending.

Approve the core/shared-runner boundary and lifecycle proof approach before any
architecture code. Specifically approve: match-start-only entropy as an intended
live behavior change; silent doctor replay and action-release
resume policy with its recorded control-only boundary command; reactive AI first,
fixed-opponent trace deferred, and the explicit limits of paired randomness.
Review measured H/K, complete state layout and timing evidence at M1/M2 before
freezing allocations. The fixed-opponent decision trace is an additional M4 gate,
not a promised free consequence of recording inputs. Reject or revise these
choices in the design PR; do not merge the proposal before review.

The implementation integrator owns future shared-core work and integration only
after approval. The parent coordinator assigns independent core/determinism and
native/resource reviewers, resolves feedback with the user and controls delivery
sequencing. No reviewer identity or acceptance is assumed by this document.
