# Isolated shot preview foundation

The isolated-preview implementation has passed independently reviewed actual
68000 CPU proofs through relocation, emitted native sink suppression and focused
history regressions and bounded same-owner batching at `9648bfc` (selective
attempt 000009). Real native interrupt
isolation, paused execution latency and runtime resources remain pending. This
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

History seek backs up 72 metadata bytes on the stack after pure range guards.
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

The standalone image has 109,560 loaded bytes. Fresh native static attribution
reconciles 49,832 code, 112,700 data and 95,296 BSS bytes (257,828 loaded bytes),
adding 96 code bytes with no storage growth. BSS remains 95,294 declared bytes
plus two final HUNK alignment bytes. The native file is 192,788 bytes. These
compile measurements do not establish actual initialized chip-RAM free space,
stack safety or native deadlines. Current runtime metrics remain incomplete;
older PR36 runtime observations are historical.

Private campaign receipts preserve the missing-AI-fixture failure (000001),
bounded discovery failure (000005), and native-proof ledger-helper failure
(000007), alongside passed scoped attempts. Native assembly-range and measurement
alignment preflight failures are also preserved. Attempt 000009 and its source,
tool, product and artifact bindings passed independent review. Remaining work
is real paused native interrupt/input/audio/presentation isolation, practical
latency and resources, then independent increment review. Tutorial UI and live branch commit
remain later increments.
