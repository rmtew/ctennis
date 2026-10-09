# Guarded incoming preview dispatch

Measured selective validation is in [the results](tutorial-guarded-predictor-results.md).

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

## Cold origin recommendation: overlooked alternative

The top-to-bottom review missed live capture of the latest incoming origin.
It reviewed retaining the existing resolved cache and reducing subsequent
contact work, but did not compare this small cold-start improvement adequately.
No runtime caching extension is included in this PR; it needs separate review.

The128 current12-byte shot/attempt slots are human episode/serve indexes:
64-bit pre-operation cursor, kind and physical end. They are not per-shot
snapshots and do not index every AI launch. Complete sparse checkpoints are
330 bytes (318 state plus cursor/schema/simulation versions),64 slots at
64-operation spacing. Ordinary seek selects the nearest preceding checkpoint
and replays at most63 operations. Cold incoming discovery instead scans from
the oldest checkpoint to find the preceding opponent launch. A checkpoint near
human contact can already be after that launch. Once resolved, repeated edits
reuse the complete318-byte incoming cache and avoid this discovery scan.

| Proposed storage | Minimum extra bytes | Added live capture work |
|---|---:|---|
| Latest opponent post-launch boundary cursor |8| Store the post-operation cursor; cold request reconstructs that complete boundary from a checkpoint at/before it, at most63 operations |
| Latest complete opponent-launch origin |330| Copy318 bytes after the launching dispatch returns; store cursor and versions |
| Post-launch boundary cursor associated with each existing128 episode slots |1,024 plus latest staging| Store and associate post-operation cursor; bounded reconstruction for historical selections |
| Complete origin associated with each existing128 episode slots |42,240 plus latest staging| Store40,704 state bytes and1,536 cursor/version bytes; copy/associate complete origins |

These are storage arithmetic, excluding validity, match/end/generation identity
and association bookkeeping. Complete per-slot origins require staging until
the subsequent human episode is indexed, potentially another330 bytes. Each
318-byte copy reads318 and writes318 bytes; cycles and callback headroom remain
unmeasured. Current history storage is80,318 bytes and preview storage10,980.
Observed PAL chip free memory62,616 bytes does not authorize a42KB allocation.

Recommend the latest post-launch boundary cursor as the smallest next proof. Capture only
during live recording, with replay and preview ownership inactive; shared hooks
invoked by seek/preview must not overwrite the live origin identity. Mark the
launch inside the existing hook, publish the post-operation boundary only after
the full dispatcher/service tail and history cursor advancement complete, and
identify its receiving end/match/history epoch.
Use the existing bounded seek worker to reconstruct post-launch state; the
launch hook's partial state is not a complete snapshot. A latest complete
origin is the next option if measured residual seek latency justifies its
copy cost. Neither option changes repeated edit/contact work.

Retire launch identities on history eviction, title/init/select, match/end
changes and version mismatch. The post-launch boundary and all needed logical
records must remain retained; a standalone state copy does not restore expired
input/entropy history or silently extend shot retention. Freeze source and
cache identity before trials, keep live/latest/selected/private owners separate,
and reject stale requests. Historical browsing needs per-episode associations
or the existing cold fallback. Sparse seek contracts remain unchanged. A
complete unedited origin may seed exact branch reconstruction; projected
launch/endpoint states still cannot become playable checkpoints.

The proposed cursor names the boundary after the launch operation, unlike the
existing event index's pre-operation cursor. Choose the nearest checkpoint at
or before this post-operation target to preserve the63-operation bound; using
a checkpoint before a pre-operation launch cursor can require64 operations
when that launch crosses a checkpoint alignment.
