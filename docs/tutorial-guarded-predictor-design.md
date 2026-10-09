# Guarded incoming preview dispatch

The selected increment reduces preview CPU work while preserving the existing
origin cache, full318 allocations, logical envelope slots, scheduler reserves,
path storage, endpoint API and normal sprite publication. It replaces only an
eligible incoming dispatch with actual shared `input_update`, `game_play_tick`,
`game_scene_finish_tick` and `game_advance_clocks`. Both players, reactive AI/RNG,
movement, handoff, animation and courtY effects remain native code.

The user's conditional authorization was reviewed independently from correctness
(`ratio32_review`) and timing/integration (`predictor_timing_review`) perspectives.
Both recommend this as the smallest coherent first increment. PR42's selective
40/40 supports a hypothesis; production admission and native benefit still need
expanded proof. No timing bound, scheduling gate, appearance or release hold is
cleared by this design.

## Alternatives and end-to-end benefit

| Alternative | Decision and reason |
|---|---|
| Reduced shared dispatch | Selected. Removes score/display/audio work without duplicating rules or changing public service/atomic ownership. |
| Batch/fuse envelopes or calibrate budget four | Likely greater eventual latency benefit, but changes atomic cost/admission and input/presenter gaps. Keep separate to avoid confounding this measurement; no reserve reduction from pair estimates. |
| Prediction between callbacks | Needs the separate deadline-owner/keyboard ACK/presenter specification. Polling attribution is not proof of available spare time. |
| Shared held/released incoming prefix | Viable later for fixed-XY ordinary returns. Fork before the final dispatch, not inside mutated contact. Input edges/latches and per-variant cursors still need independent proof; mainly saves second-alternative work. |
| Analytical/direct contact or projected trajectory cache | Actual phase, opponent RNG and scene effects remain necessary. Added guard/event priority burden outweighs the measured ball-arithmetic cost for this increment. |
| Pack reduced state | Small allocation gain beside8208 bytes of paths; adds schema/read-closure maintenance. Keep318 bytes and no new snapshot schema. |
| On-demand path points | May save RAM, but moves computation onto visible sample deadlines and needs phase/event/wrap/fallback proof. Retain dense actual samples and the existing bounded endpoint query. |

Existing finite native traces attribute about15% of request-to-contact time to
original dispatch and26% to all workers. A32% dispatch saving implies only about5%
under a simple unchanged-pacing estimate, not a measured speedup. Input service,
public-yield overhead and waiting dominate. Measure complete affected callbacks,
actual contact and COPJMP independently; do not promise large responsiveness gains.

## Exact versus observational interfaces

`game_preview_request` remains the exact full-state/output entry. All existing
recorder/seek/exact-preview proofs retain their original comparison contract.
`game_preview_request_projected` has identical arguments and opts into an
origin-qualified observational route. The normal tutorial uses this entry.
Both preserve stale/invalid no-write behavior, generation, cache identities,
per-envelope cursors/checks and public owner restoration.

The projected contract compares actual receiving-human attempts and phase gates,
accepted contact/serve timing and launch/target/height flags, exact8-byte
ball/shadow samples including colours/visibility/tick, and first geometric
landing/net/out or explicit no-contact/limit/lifecycle outcome. Incidental private
score/audio/display state and suppressed raster/audio sink ledgers may differ.
Complete paused canonical/history state must remain untouched and unread by
private CPU execution. No live hardware/entropy reads are introduced.

Reduced launch buffers are preview seeds, not complete original edited-branch
checkpoints. The existing Play from here control stays NOTREADY. A genuine
playable branch must reconstruct an explicit full original-core boundary with
the actual AI/input policy; a ball-only terminal preview excludes the next
opponent response and cannot supply it. Resume latest retains exact interrupted
state and physical-input reconciliation. This does not weaken branch/seek proofs.

## Admission and fallback

Choose both variant routes once in prepare from the immutable complete edited
opponent-postlaunch origin. The original full resolver/cache and copies remain.
Projected admission requires:

- Projected request, matching incoming context, kind0..2; human serve kind3 stays exact.
- PLAYING, initialized S_ACTIVE, no pending command or restart/round/result/title/input-suppression flags.
- One-human AI/active-score flags and mode/end/owner mapping consistent with the receiving human.
- A genuine already-launched incoming flight, correct receiving-side contact flag, and no initial terminal.

Guard rejection records a class and selects original replay from the start.
There is no mid-horizon fallback from divergent incidental state. The admitted
logical operation set remains actual pads/result/clear/latch/poll/tick; retained
init/select/title reset already causes the existing unsupported lifecycle result.
Stable S_ACTIVE only reacts to outcome bit7; the incoming worker stops at its
first terminal before a later scoring transition. Mode, scorer AI/stage and
command invariants cannot change through these admitted envelopes. Scene finish,
all clocks and both-player gameplay remain actual helpers. Broader contexts
must remain exact until separately proved.

Six added metadata bytes distinguish requested policy, per-variant route and
guard rejection class. The state schema/core simulation version and all native
match/replay code remain unchanged. Resource and stack changes will be measured.

## Proof and delivery gates

- Expanded emitted CPU comparison from independent immutable origins, multiple seeds, natural exchanged ends, handoff/phase, central/wide/low-height contacts, misses, net/out/fault boundaries, irregular envelopes and every budget1..4.
- Exact API/fallback retain complete318 and ordered-output equality. Projected API compares every required event/sample/logical cursor boundary, with different initial working state, omitted-field poison/read audit and complete canonical/history/store isolation.
- Stale/cancel/cache replacement and selection/history reset retain their no-write/retirement contracts; unsupported origins never enter the kernel.
- Shared emitted predictor bytes match native/standalone; original normalized core stays unchanged. No host rules model or oracle intermediate state injection.
- Selective resumable PAL/NTSC physical-input checks measure actual contact, endpoint publication, sprite/bank bytes, input/ACK/service gaps, complete callback headroom, code/data/BSS/RAM and stack. Finite observations are not WCET or full acceptance.
- Independent source and evidence review precede draft delivery. Integrator owns implementation/evidence; parent coordinates reviewers. No merge or release approval; existing appearance/resource/cold/full-release holds remain.
