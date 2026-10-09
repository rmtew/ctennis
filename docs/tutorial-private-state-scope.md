# Supplied private state: bounded next-step scope

Private state does **not** need to wait behind comparison/copy micro-optimizations.
The previous ranking treated its proof burden as a reason to defer it before
checking the actual register and addressing scope. This source audit supports
making it the next structural candidate, subject to user approval. No runtime
change or alternative implementation was built for this review.

## Concrete inventory

The same [318-byte block](../amiga/game/core_state.i) already owns simulation
state. [state.i](../amiga/game/state.i) aliases gameplay/scorer fields;
`G_`, `S_`, `AV_`, `D_` and `O_` equates already supply packet-relative offsets.
Gameplay uses A4 for its packet and A3 for players; scoring also uses A4, while
audio/scene derive local packet pointers. These accesses can remain unchanged.

A recursive textual audit of `core.s` found 106 state labels/aliases, 300
instruction lines mentioning state and 14 absolute state-pointer table entries
in 16 `.s` files. Some expressions are already relative and need no rewrite,
such as the pad-latch difference from A0. The retained actual native hunk has
250 state `RELOC32` operands inside the core: **236 instruction operands and
14 scorer pointers**, all offsets 0–316. This is a bounded addressing migration,
not a new physics implementation. Read-only audit inventories are
`/tmp/ctennis-private-base-source-audit.json` and
`/tmp/ctennis-private-base-relocations.json`; counts are static, not execution
measurements.

Most fixed operands are in result/lifecycle, integration, round, menu, input
and audio. The ball/contact/AI routines mostly already use A4/A3-relative
operands. Preserve the absolute canonical labels for native adapters, snapshots
and debuggers; add named offsets relative to `game_core_state` for core access.
Do not redefine canonical labels as offsets or create duplicate live/predictor
versions of the routines.

## Register and call contract

**A5 is the practical candidate.** The recursively included core has no A5
operand except the entropy helper's complete register save/restore. A4 remains
the current subsystem packet base. A6 remains available to startup's Exec calls;
using it offers no advantage. The core makes no Exec/library calls itself.

Reserve A5 only for the duration of a core call, as a supplied even state base.
Live public wrappers save the caller's A5, install the canonical base and restore
it on return. Private execution installs its actual working buffer and calls the
same bodies. Retained envelopes need a body-operation table or explicit private
entry that bypasses live wrappers: the current operation table points at wrappers
and would otherwise reinstall the canonical base. No logical input word changes.
Standalone direct body callers supply A5 explicitly; normal public API callers
retain their existing contract.

Preview request and seek already use A5 as temporary bookkeeping, so their
existing save/restore boundary must bracket private calls. The bulk copy helper
clobbers A5 internally but saves/restores it. Score Copper patching uses A5 but
also saves/restores it. The presentation IRQ saves all D/A registers and publishes
completed hardware banks, not a live simulation packet. Its preserved A5 must
not select a private context for canonical display consumers. Do not replace
absolute native-adapter reads globally.

## Dependencies and minimum migration

1. Convert core fixed state reads/writes and packet LEAs to `offset(A5)`; retain
   immutable table addressing and all existing physics, RNG, score, audio,
   scene, lifecycle and instruction order.
2. Replace the scorer's 14 absolute pointer entries with state offsets and form
   each field address from A5. Keep its import/export semantics. A fixed-width
   offset table is sufficient; shrinking its format is optional.
3. Make state-observing sinks read the supplied context. Native live sinks still
   consume canonical state; preview suppresses physical output and observes
   private state. Contact/serve hooks preserve registers but inspect state and
   route through history/preview, so they must be audited too. Audio completion,
   scene clocks and `courtY` remain part of the private state and run unchanged.
4. Point resolver/held/released bodies and path/outcome readers at their current
   buffer. Convert seek's working execution similarly, or explicitly bind its
   existing canonical working path until that small follow-on is reviewed.
5. Update the isolated CPU harness's owned regions, event reads and poisoned
   register setup to understand a supplied base. Require the native and standalone
   builds to share identical normalized core bytes and offset-table contents.

Beyond the 16 core files, inspect the 41 state-reference lines in preview,
9 in history, 6 in seek, 8 in main and 8 in the native adapter. These are review
counts, not a demand to convert all of them: canonical checkpoint/commit,
resume and native presentation reads should remain canonical. `core_trace.s`
needs entry binding despite having no direct canonical-state reference.

## What disappears and what remains

Each worker currently loads a 318-byte working state into the canonical block,
saves it back, then restores the selected block. Direct private execution removes
those three recurring transfers and their owner-release bookkeeping; switching
variants becomes selecting an address. Selected/action snapshots, initial
edited/held/released copies, checkpoints and explicit seek/resume commit copies
remain necessary. The measured worker state-copy function costs 224,966 exclusive
bus CCK; that identifies opportunity, not a promised wall-time reduction.

**Private addressing alone does not remove the external selection guard.** Keep
the full 318+72-byte comparison at public request/step/result boundaries initially,
plus generation, paused mode, retention/cursor, bounds, job exclusion and cancel
checks. Live state is never swapped, which simplifies that proof. A trusted owned
job can later validate once per callback instead of each subcall, but requires
an audit of every writer and external mutation path. Do not infer immutability
from a hash or a pointer.

The current recorder's `replaying`/`replay_low` scratch and history metadata still
change during retained execution. Keep the 72-byte metadata save/restore in the
minimum migration, with balanced replay-flag retirement. Eliminating it requires
a separate private replay-envelope context. Hardware sink suppression and
publication-generation checks also remain; a private pointer is not an output
permission. Cancellation may discard private work without canonical restoration.

## Cost, proof and recommended order

State layout remains 318 bytes; existing buffers suffice. For the 236 emitted
absolute instruction operands, absolute-long to displacement addressing can
save two encoded bytes each: **472 bytes of local potential**, before wrapper,
table and branch changes. PC-relative accesses may have equal sizes already.
This is an estimate, not a new assembled code size. Displacement access usually
removes an address-extension fetch relative to absolute-long; table address
formation and scoped entry binding add work. Measure native code bytes and actual
68000/ChipRAM costs rather than assume every access improves. Offsets fit signed
16-bit displacement without enlarging the state or allocating a pointer bank.

The migration is broader than a longword comparison but narrower than kernel
extraction: roughly 300 source reference lines, a scorer table, entry/sink binding
and caller/harness updates. Batching also changes scheduler/preemption semantics
and still leaves global swapping. Longword comparison is smaller and lowest risk,
but need not be a prerequisite or distract from structural savings.

Recommended order after approval: **supplied A5 core first**, then private preview
execution in a separately reviewable integration step; retain the external guard
and metadata restoration. Establish unchanged live behavior before removing swaps.
Compare complete state, events, paths, RNG positions and history cursors across
different poisoned bases, alternating independent contexts and every retained
checkpoint/tick; trap out-of-context writes and aliases. Then measure fresh input,
cancel/resume, ownership transitions and worst PAL/NTSC callbacks/publication
tails. Follow with guard amortization or longword comparison only if measurement
still justifies them. No removal of audio/scene/scorer semantics is required.

The integration owner owns this migration only after approval; the parent
coordinates independent review. The current approval question remains unanswered.
This scope supersedes the automatic deferment implied by the earlier hotspot
ranking; it does not authorize implementation or merge PR38.
