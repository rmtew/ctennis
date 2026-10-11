# Retained tutorial navigation and edited branches

Proposal carried forward to reviewed responsiveness product
`3d755826cc70536d92a9b33dca382df0b4d60a40`.
This document describes a source/proof boundary; none of the additions below
has been implemented or executed. Preparation can proceed independently of
appearance review; UI tuning and release integration remain pending.

## History constraints found in the source

`game_history_cursor` is both an unsigned64 lifetime cursor and the record-ring
address. Rewinding it to the selected moment would reuse discarded future
identities. Reattaching history would discard the retained past. Neither is an
acceptable branch operation.

Current seek chooses a checkpoint and validates at most63 contiguous logical
records. Preview resolution and continuation also increment that cursor. A
branch therefore needs an explicit segment boundary: discarded future bytes
must never become replayable merely because their ring slots still contain
valid operations.

Each12-byte attempt index contains its pre-operation origin, kind and end. It
has no completion cursor. An index originating before selection may complete in
the discarded future. Branch truncation cannot preserve that completed kind
without additional actual completion evidence.

## Proposed bounded storage

Keep the existing80318-byte record/checkpoint/index store and the318-byte
schema2/simulation3 canonical state. Add fixed private history metadata:

- An8-byte bitmap identifying valid checkpoint slots.
- An unsigned64 valid-end cursor for each of64 checkpoints:512 bytes.
- An unsigned64 completion cursor for each of128 attempts:1024 bytes.

These1544 bytes are an estimate of the declarations, not a measured RAM cost.
All are written by the actual recorder/hooks. Unfinished indexes remain kind0;
completion cursors are recorded at complete operation boundaries. No per-tick
allocation is introduced. Attach resets validity; ordinary checkpoint creation
maintains it. Both synchronous and sliced seek enumerate bitmap-valid slots rather than the
old count-prefix assumption, and validate the selected segment's end before
reading records, while retaining envelope/schema/simulation checks.

Branch preparation should reuse the existing734-byte paused seek scratch,
under an explicit seek/branch job-kind discriminator. A small staged validity
mask, cut slot/end and new boundary descriptor are additional private fields.
Seek APIs must reject branch jobs and branch APIs must reject seek jobs. Existing
selection identity and generation checks remain mandatory. Preview and branch
work are serialized; preview_active is never borrowed as a seek/branch owner.

## Navigation and context

Only completed human serve/return/miss indexes are candidates. A bounded,
resumable actual-core catalog pass must verify true incoming launch, probe and
human action/outcome identities. A raw origin>=oldest does not establish complete
incoming context. The pass excludes truncated entries and preserves the paused
store/live backup/public state on every yield. Its total cost and first-result
latency need measurement; scanning independently for every index is unsuitable.

The catalog is fixed at128 entries and remains stable while frozen. Default
selection is the newest qualified candidate. If none survives, fallback is only
the actual current human serve setup; arbitrary idle/title state is unavailable.
The UI count includes only qualified entries. It reports resolving progress
while the catalog is incomplete rather than presenting a final raw-index count.

Previous/next changes the catalog ordinal. Time movement chooses actual
pre-dispatch boundaries within true incoming launch through original human
contact/outcome. Completed serves retain their recorded pre-launch boundary.
The selected state's animation/end supplies the actual legal position table.
Navigation uses seek_begin/step/commit with actual timer admission, then requests
both previews from that selected state. Successful selection invalidates old
paths; pending navigation never changes the interrupted318-byte backup.

History traversal after branching follows explicit valid segments and canonical
branch checkpoints. A hypothetical continuation must not execute a later branch
snapshot as an unrequested position edit: at its retained segment end it switches
to the documented actual-core synthetic continuation policy. Resolver traversal
of original history can cross a branch only by restoring its validated canonical
checkpoint, with that discontinuity recorded in proof evidence.

## Explicit branch transaction

The options menu latches the displayed held/released alternative when it opens;
F/Enter confirmation and menu navigation do not change that choice.

Proposed begin arguments are expected job generation, expected published preview
generation and variant0/1. It validates frozen ownership, PLAYING/human context,
unchanged selected318/all72, READY preview identity and legal edited coordinates.
It copies the preview's edited initial318 into owned scratch, then uses the real
pad edge sampler twice, matching the existing preview priming, to establish
the selected action, preserving opponent input
and clearing human directions exactly as the reviewed preview policy does. It
restores selected318/all72/store/live backup before returning READY. Failure
changes no public or previously valid transaction state.

Commit rechecks generation and selected identity before any write. It preserves
original retained past through the selected boundary, invalidates later
checkpoint slots and indexes completing after selection, and ends the final
retained segment at selection. It then publishes a canonical checkpoint at
old_live_cursor+1. This cursor is strictly newer; overflow rejects before any
mutation. The discarded interval is inaccessible. Original past bytes remain
unchanged except an oldest checkpoint/index dependency may be evicted when no
checkpoint slot is free. Such eviction is explicit in the result.

Record-ring capacity is independent of checkpoint-slot capacity. Branch
invalidation can leave free checkpoint slots while the lifetime cursor continues
to alias the4096-operation ring. Before each record write, calculate which old
valid segments/checkpoints and attempt-context dependencies use the slot about
to be overwritten. Retire those dependencies and advance the accessible retained
boundary, or reject before mutation; free checkpoint slots never permit replay
of overwritten old operations. This pruning applies to ordinary continuation
after a branch and repeated branches, not only checkpoint creation. Seek and
catalog validation must reject retired dependencies even if their checkpoint
envelopes or index bytes remain intact.

The checkpoint contains the exact edited player position, actual sampled
held/pressed/released/latch state and current RNG, plus every other canonical
byte. Only this successful command discards old future. Stale/canceled/failed
commit cannot publish. Cancel preserves selection and all history. Successful
commit retires preview/cache and paused jobs; Resume latest retains its existing
exact interrupted-state behavior until an explicit branch commits.

The twice-sampled canonical inputs must reach their intended first dispatch
without further canonical work. This preserves the same held/pressed/released
bytes as the displayed preview; it does not invent a retained pressed edge.
Guard round poll, result sampling, pad sampling and native commands as well as
dispatch while this transaction is pending, because the native callback currently
polls before tutorial work. Commit and that dispatch are separately
admitted callback work. Physical/UI sampling continues into private state, but canonical work stays
blocked until the first declared branch dispatch; no seek/preview batch is added
to that callback. The first dispatch is recorded at the new branch cursor.

Physical action reconciliation uses a neutral-release barrier. Preserve the
selected player's chosen B1 only through the declared first dispatch. After that,
use the real sampler at every ordinary input boundary with only human B1
replaced by the chosen action until aggregate unfiltered physical B1 is neutral.
At that neutral boundary remove the override and sample zero normally. A held
choice with physical action already released produces one ordinary release
following its first dispatch. A held choice with physical action still held
remains held until actual release. A released choice with held confirmation
stays released until confirmation release, then hands over without an action
edge. Later real presses/releases work normally. Never restore prepared edge
bytes repeatedly, and preserve the sampler's existing latch semantics.

The barrier observes actual mapped keyboard and joystick aliases before entry
mask filtering; a masked held F must not appear neutral. Normal human directions
and opponent sampling resume after the first dispatch. Retire carried menu
navigation directions, B2/modifier and Enter aliases until their own neutral
boundary so they cannot leak into gameplay or a fresh tutorial gesture. Show a
persistent release-action synchronization hint while the barrier owns B1, using
the existing hint mechanism; exact wording/appearance remains for user review.
Before commit, cancellation/supersession preserve the original future and
interrupted Resume latest backup. After commit, the original future is invalid:
cancellation/supersession and Resume latest cannot restore that prebranch
backup. Pause may retain FIRST_DISPATCH_PENDING privately; reject or defer
other jobs until that first dispatch completes. The next tutorial entry captures
a new live backup from the committed branch. The first chosen action is guaranteed; subsequent continuation
follows this policy and physical inputs. Equality with the displayed trajectory
requires a declared matching logical continuation, not arbitrary physical input.

Independent preparation review recommends this policy over waiting for physical
re-press to match a virtual hold. Source and native proof are still required
before implementation. Cover already-neutral versus later-neutral action,
mixed aliases, input-source changes, press/release between callbacks, carried
menu directions and exact held/pressed/released/latch bytes. No visual tuning or
runtime branch code is implemented by this proposal.

## First focused actual-core proof

Use the preserved actual835-operation prefix, frozen at835, and selected569
from checkpoint512 (57 sliced bodies), after independently checking that569 is
its actual pre-dispatch boundary and that the completed candidate has full
incoming context. No later expected state is injected. Inputs initialize once;
all subsequent states/events come from the actual68000 APIs.

Test both action variants and one actual table-legal coordinate edit. Compare
the prepared checkpoint with a separately executed actual-core edit/edge sampler:
full318 bytes, RNG, ordered intents and input edge fields. Pending calls preserve
selected318/all72, store and interrupted backup. Before commit, cancel, failed
validation and supersession preserve the original future.

After commit, require a strictly new boundary836, the exact edited checkpoint,
and inaccessible570..835. Seek original retained boundaries through569 and
compare complete state/events with uninterrupted original execution. Record a
short declared continuation from836, then replay it from the branch checkpoint
and compare complete state/events and the actual chosen path. Chosen-path
comparisons use matching logical input/cadence policy; equal initial RNG alone
does not promise paired reactive-AI randomness.

Cover zero/free checkpoint slot, oldest eviction, a second branch, recording
through record-ring wrap after branching with free checkpoint slots, both seek
implementations over noncontiguous valid checkpoint slots, low-longword
carry/exhaustion, retained completed versus future-completed indexes, gap targets,
poisoned envelopes/operations, stale generation, cancellation immediately before
publication, released/held menu confirmation and first-dispatch ordering. Keep
each fixture finite and retain descriptive failures. Measure begin/commit/cancel
costs and stack separately from native callback/IRQ/UI costs.

No builder, emulator or actualCPU proof is authorized in this author worktree
while the prototype owner holds the shared runtime. The proposed layout and
semantics require independent source/design review before runtime code changes.

## Integration work queue

- [x] Preserve the reviewed PAL/NTSC static-court baseline and exact receipts.
- [x] Carry forward the completed author proposal into the integration repository.
- [x] Independently review the proposed segment validity, completion cursors and eviction policy,
  including record-slot overwrite pruning independent of checkpoint capacity.
- [x] Independently review the proposed two-sample prime and neutral-release barrier.
- [ ] Prove exact control reconciliation and first-dispatch ordering before native integration.
- [ ] Implement private metadata and transaction APIs in an isolated increment;
  keep the current court presentation unchanged.
- [ ] Run the first actual-core 835→569→836 proof described above, including
  poisoned working state, full state/events/cursors and gap rejection.
- [ ] Add bounded catalog qualification and seek-backed previous/next selection.
- [ ] Measure cold catalog, seek, begin/commit/cancel, first-dispatch and transition
  costs before admitting these jobs into native callbacks.
- [ ] Integrate with the existing controls after source/proof review; exercise
  menu-held/released reconciliation, stale generations and Resume latest.

Root owns eventual integration and the sole runtime controller. The independent
reviewer owns design/source review and completed exact evidence review. The
proposal's control synchronization and history eviction are review decisions;
its byte counts are estimates until assembled and measured. No optional sprite
milestone or new visual treatment belongs in these increments. The initial
branch proof should have no menu dependency: invoke the actual transaction APIs
from a finite native fixture after one initialization, then observe subsequent
actual execution rather than injecting expected state. Native controls/IRQ/UI
integration is a separate later proof. This queue is preparation, not a runtime
implementation or approval to merge PR38.

Independent docs-only review cleared this proposal for continued preparation on
2026-10-09 after the ring-overwrite and valid-slot corrections. Control
reconciliation now has a reviewed recommendation; exact source/native proof
remains required before branch runtime code;
this review does not approve implementation, visual choices or merge.
