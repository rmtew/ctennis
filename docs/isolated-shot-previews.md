# Isolated shot preview foundation

The isolated-preview implementation has independently reviewed actual 68000 CPU
evidence at `9648bfc` (selective attempt 000009). The seek scheduling repair has
fresh independently reviewed CPU evidence at `363fad8` (sliced-seek attempt
000004), including emitted native instructions and relocation. The earlier
preview proof remains historical evidence for its exact worker/product; unchanged
simulation endpoint qualification is the only proposed inheritance for the new
native cases. Real native interrupt isolation, paused execution latency and
runtime resources remain pending. This
increment has no tutorial UI or live branch commit and is not a complete native
acceptance gate.

## API and isolation contract

`game_preview_request` accepts the current generation, a retained completed
attempt ordinal (or `ffff` for explicit current human serve setup), and legal
byte X/Y. The selected boundary is `game_history_position`. A completed serve
requires its recorded pre-launch boundary. A return or miss requires a retained
preceding opponent launch and a selection from that launch through the original
action's pre-operation boundary. A raw probe origin alone is insufficient.
Truncated incoming context is unavailable. Current-serve fallback requires real
human serve setup and never resets the game. All requests require PLAYING.

Complete timed-serve boundaries at clocks 15 and 16 remain eligible: the actual
launch reads entry clock 16, and the service tail advances the complete boundary
to 17. Timed phase 20 at clocks above 16 is unavailable. Setup/wait phase priority
follows the actual player dispatcher. The genuine AI-serving negative proves
absence of human serve context; it does not claim to isolate the defensive AI
flag guard using inconsistent injected state.

The resolver replays from the oldest checkpoint through the original action.
`game_preview_step` accepts one to four logical API operations, including resolver
work. The current implementation saves its working context and restores the
selected 318 canonical bytes and all 72 history metadata bytes at each ownership
transition and before every public return. Within one call, up to four operations
sharing an owner retain their working canonical context; owner identity is
recomputed from persistent phase metadata after every actual body. Recorder mode remains frozen (2).
History storage, live backup, cursors and the interrupted output queue stay
unchanged. Copying and request costs are additional to the operation count.

Four canonical scratch images hold the selected state, common edited start,
held continuation and released continuation. Only requested human X/Y change in
the common start; both variants retain its exact RNG. Legal bounds come from the
actual selected-animation movement tables. Each variant primes the actual pad
edge sampler, including selections after the original pads call. Every subsequent
pad sample neutralizes human directions/button 2 and forces button 1 held or
released, while retaining opponent arguments. Latches, waits and reactive AI use
the actual core. Equal initial seeds do not promise paired AI random draws.

Recorded future API order and arguments continue until retained history ends.
The explicit continuation afterward is poll, pads, zero result metadata,
dispatch; opponent inputs retain their last sampled value. Init/select/title
operations stop before reset execution, and lifecycle is checked after every
operation. Outcomes use complete actual boundaries: landing, net, out,
interception, no contact, lifecycle interruption or the finite limit. No-contact
and incomplete attached-ball observations do not invent an outgoing shot.

## Storage, generations and cache

Two paths each hold at most 256 eight-byte samples: court X/Y, actual projected
ball X/Y, contact, flight, packed ball/shadow colour nibbles and tick. Incoming
samples count toward that limit. Geometry and visibility come from actual core
outputs. Coincidence compares drawn geometry/visibility at matching ordinals and
ticks; different diagnostic fields and outcomes remain separately available.

Fixed storage is 5,550 bytes: 110 metadata, 72 saved history metadata, four
318-byte canonical images and 4,096 sample bytes. The enclosing BSS hunk adds two
final alignment bytes. Counts and generations guard unpublished bytes. Results
become visible only after both current variants finish or honestly truncate and
the selected canonical/history identity still matches. Stale API calls reject
before mutation. Cancellation retires the generation; exhaustion never wraps.

The compact cache reuses only a fully published, validated original incoming
prefix/action with identical selected 318 bytes, all 72 metadata bytes, ordinal,
retained origin, kind and end. Warm edits start a new generation and clear
variant bookkeeping. Old outgoing suffixes remain inaccessible. Cancellation
and successful external history mutation invalidate publication/cache and retire
the old generation, saturating at `ffffffff`. Internal request-owned oldest-seek
restoration has an explicit active-3 bypass. Editing before READY or changing
selection/attempt can require cold resolution.

Synchronous history seek backs up 72 metadata bytes on the stack before shared
bounded validation.
Rejected checkpoint envelopes or operations restore them; canonical restoration
starts only after complete upfront validation. Failed seeks preserve READY,
cache and the selected moment. Rollback storage is stack memory, not another
canonical scratch image.

## Current evidence and limits

The accepted CPU receipt covers independent uninterrupted actual-core
continuations from each edited start, complete canonical/path/ordered-output
comparisons, independently known API/input policy and only-X/Y edits. Checked
public returns preserve the full loaded image outside preview scratch and the
interrupted output queue. Frozen history writes are forbidden by full-extent
bus guards. The first dispatch observes the actual held/released human controls,
including after-pads selection.

API/context proofs cover genuine human serve wait; timed 15/16 acceptance and
17 rejection; stale TITLE rejection for both fallback and historical requests;
no contact; the honest 256-sample limit; changed-position replacement during
RESOLVE/HELD; non-dispatch reset boundaries; and a completed retained probe whose
true incoming launch has evicted. The truncated case has incoming 564 below
oldest 576 and retained completed probe 696; it reports CONTEXT_MISSING without
publishing a result or cache. READY schema/simulation/state/opcode failures
preserve all 72 metadata bytes, canonical state, store, generation and results.
Seek/back, different attempt, cancellation, eviction and exhaustion invalidate
as specified.

Bounded endpoint discovery keeps seeds `ace1/0001/1234/beef`, at most 512
dispatches/2,049 ordinary operations per seed, first two completed human returns,
and at most 72 jobs. Actual recorded incoming states select three legal contact
times and three lateral positions. Twelve jobs at `ace1` found meaningful
launched coincidence and net at selection 728, and interception/out at 1100.
Classification uses actual canonical flags and accepted contact-hook order;
the first applicable terminal boundary must be the last sampled boundary.
Coincidence requires both human launches and actual outgoing samples.

The three chosen input descriptors pass at standalone bases `10000` and `30000`
and in the emitted native image. Native setup uses observation traps outside the
proof; every emitted adapter entry is restored before freeze. A read-only
observer records semantic intents without changing registers, SR, SP or PC.
Actual native mode-2 sink bodies execute while bus guards reject hardware and
nonstate writes. The native uninterrupted reference establishes real frozen
metadata before installing the edited canonical start once. Full canonical
states, path bytes, outcomes and ordered intents agree across images. This is
emitted-code CPU evidence, not execution with real native interrupts or DMA.

Focused current history regressions cover the empty boundary, all nine logical
APIs with register/SR equivalence, and a ring/cursor-wrap stream of 4,161
operations: 4,034 retained boundaries and 8,072 seeks. Native image-specific seeks
also preserve the interrupted ledger and reproduce recorded full states. The
normalized shared simulation bytes match at 18,020 bytes with 257 verified
relocations and 14 sink branches; fixture/worker identities have separate input
and compiled-artifact bindings.

The combined receipt's maximum observed worker cost is 96,924 CPU cycles and
preview stack depth is 204 bytes. Focused history seek observes 208 stack bytes
and a 350,326-cycle maximum. These are finite observations, not universal bounds
or native frame headroom. The representative warm edit resolves zero operations
and costs 4,176,756 worker cycles plus 18,232 request cycles over 114 calls.
Cold resolution uses 773 operations and costs 9,667,676 worker cycles plus
21,604 request cycles over 308 calls. Compared with the reviewed pre-batching
attempt 000008 on the same descriptors, total CPU work falls 32.3917% warm and
36.1326% cold; call counts remain unchanged. The finite A3 peak rises slightly
from 95,534 to 96,482 cycles. These observations do not establish practical
native latency or frame deadlines. Budget-1/2/3/4 proofs independently compare
actual body counts, all five owner transitions, restoration before each next
owner/READY, and full uninterrupted state/path/outcome/output equality.

The repaired native static attribution reconciles 50,728 code, 112,700 data and
96,028 BSS bytes (259,456 loaded bytes), adding 896 code and 732 loaded BSS
bytes. The private seek job declares 734 bytes; it consumes the preceding two
final alignment bytes. The development file is 194,600 bytes. Symbol removal
produces a 168,336-byte release file with identical loaded bytes; that release
has no fresh cold-boot proof. These compile measurements do not establish actual
initialized chip-RAM free space or native deadlines. Current runtime metrics
remain incomplete; older PR36 runtime observations are historical.

The bounded native observer cases may inherit unchanged simulation endpoint
qualification from the independently reviewed CPU9 receipt only after checking
its immutable and canonical passing bytes and latest execution ledger. Exact
removal of the three added seek-ownership guards must reproduce the older preview
source hash, with unchanged normalized simulation bytes and sinks. This does not
reuse old worker scheduling, current product or ownership acceptance. The fresh
sliced-seek receipt must independently bind current products, inputs, tools and
latest execution, and new native cases must compare actual complete states,
paths and ordered events. Missing or failed evidence blocks inheritance.

Native observer attempts remain failed and preserved. Direct prime/synthetic
body calls require read-only emitted-entry and stack-matched return observations;
wrapper markers alone do not capture them. The observer now pairs complete
318-byte states and ordered intents at those bodies without changing gameplay
bytes, and archives literal RPC and event transcripts with lossless gzip under
the unchanged 256 MiB stored-artifact cap. Compressed storage and uncompressed
transcript lengths are reported separately. This correction has host checks,
with fresh native execution still pending.

The preserved failed PAL observer attempt 000003 also exposes a real timing
blocker: callback 536 takes 167,076 CCK, including a 159,175-CCK synchronous seek,
with observed deadline headroom of -108,565.44 CCK. That failed callback is not
exempted from timing acceptance. Practical paused latency remains unresolved.

### Implemented seek repair and remaining native gate

The approved repair uses the retained failing selection: checkpoint operation
512 through completed probe 569. `game_history_seek_begin` accepts the expected
generation and 64-bit target, validates the complete bounded replay plan and
captures the selected 318 canonical bytes plus all 72 public metadata bytes.
`game_history_seek_step` accepts the generation and an external admission bit;
it advances at most one actual core operation. Between calls its 734-byte job
holds a private cursor, selected state/metadata and working state. Every pending
return restores the full selected public state and metadata and clears replaying.
Seek bodies use their own active flag, with preview ownership zero.

`game_history_seek_commit` publishes the complete target state/cursor only when
the generation and selected identity still agree. Cancellation retires the job;
a stale call cannot restore an older selection. Begin, commit and cancellation
retire preview publication/cache as appropriate. Pending or ready seek jobs reject
preview request/step/result, serializing the two owners. External synchronous
seek remains available for offline callers and retires pending jobs; its shared
validator retains complete rollback. No partial target is published.

Fresh selective CPU campaign `69cd1780198c4e55a7f8d6c25484c239`, attempt 000004,
passed independent source and completed-evidence review at `363fad8`. Receipt
SHA256 is `1a0a8cc933c5c9f42507ca8b2f1cc7c260db769fffbd0a50570b35beb712995c`.
It binds 216 files and the standalone/native products. All 57 working boundaries
match separate uninterrupted actual-core references in standalone, relocated
standalone and emitted-native roles: complete states, ordered events and cursors
agree while selection 835 remains public until commit to 569. Different initial
working memory, full bus guards, 16 negative controls per role, six synchronous
rollback controls, cursor rollover and a fresh post-commit preview/cancel are
included. No separate simulation model supplies expected state.

Observed CPU costs are begin 24,730 cycles, maximum step 37,604 standalone and
37,884 emitted-native, commit 8,156, cancel 296, and stack 204 bytes. These finite
CPU observations establish neither contention/IRQ costs nor native deadlines.
The first three failed attempts remain preserved: two static declaration/parser
failures before execution and one completed computation with a missing receipt
identity field. Only attempt 000004 is an acceptance pass for this selective case.

The native-only fixture is being adapted to admit work using actual remaining
CIA callback time; any reserve is an estimate until measured. Begin validation,
state swaps, admission-zero returns, interrupts, commit/cancel and callback tails
remain inside unchanged timing acceptance. Required fresh PAL and NTSC evidence
includes the actual retained seek, cancellation/supersession, owner transitions,
physical input edges, full state/event/cursor equality, audio/publication isolation,
initialized RAM/stack and positive complete callback headroom. Older failed PAL
callback 536 remains a blocker until the affected fresh native gate passes.

The history/preview author owns the repair; the root integrator owns the single
controller and delivery. The coordinating parent assigns independent source and
completed-evidence reviewers. PR #37 stays draft/unmerged until those native
checks and reviews clear. The approved on-court tutorial prototype then requires
user visual review; live branch commit remains later work.

Private campaign receipts preserve the missing-AI-fixture failure (000001),
bounded discovery failure (000005), and native-proof ledger-helper failure
(000007), alongside passed scoped attempts. Native assembly-range and measurement
alignment preflight failures are also preserved. Attempt 000009 and its source,
tool, product and artifact bindings passed independent review. Remaining work
is real paused native interrupt/input/audio/presentation isolation, practical
latency and resources, then independent increment review. Tutorial UI and live branch commit
remain later increments.
