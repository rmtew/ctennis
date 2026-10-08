# Bounded rolling history and seek

Tutorial increment 2 uses the actual shared 68000 core. No tutorial UI, preview,
branch command or persistent file is implemented here. Schema 2 / simulation 3
canonical states remain exactly 318 bytes; record envelopes reject other versions
and invalid audio clip IDs/offsets before restoration.

The native and standalone programs reserve one fixed 21,470-byte history BSS
buffer, plus two bytes of hunk alignment and 72 bytes of recorder metadata.
The measured baseline on the 512 KB, no-expansion target had 252,368 bytes free
at the cold one-player runtime peak and 218,632 bytes free in the two-player
measurement. This buffer uses a modest part of that measured space. Final
resource and callback evidence must establish the changed build's actual cost.

The first two cold one-player attempts failed the title transition deadline
by 1,226 and 1,068 CCK respectively. The latter callback included a 41,238 CCK
menu copy followed by match initialization. The aligned 60-byte play, 28-byte
score and 96-byte audio resets now use longword clears with the same final
pointers and counters. A sequential comparison of the prior and changed actual
68000 executables covered 1,165 logical operations across both selections,
ticks, input clearing, return-to-title and reinitialization: canonical state,
ordered outputs, all registers and SR matched at every boundary. Match
initialization saved 2,668 isolated CPU cycles; this is a diagnostic measurement,
not a native deadline pass. Fresh native evidence must supersede the failures.

There are 1,024 14-byte logical-operation records, sixteen 330-byte canonical
checkpoints, 128 twelve-byte shot/attempt entries and a separate 318-byte saved
interruption state. Checkpoints occur every 64 logical operations. The oldest
checkpoint and its dependent records/index entries retire together: retained
history spans 960–1,023 operations after filling. This counts polls, logical
sampling and lifecycle commands as well as ticks; it is not a match-duration or
shot-count guarantee. Deuce and a long match never stop recording permanently.

The cursor is an unsigned 64-bit operation boundary. The core's byte tick and
the cursor's low longword may wrap independently. A 64-bit lifetime exhaustion
disables recording instead of aliasing old boundaries. Attach accepts only the
program's exact preallocated buffer and size, rejecting null, odd, foreign and
wrong-sized inputs without touching canonical state. There are no runtime
allocations per tick, checkpoint or shot. The existing OS LoadSeg allocation
boundary precedes machine takeover; unavailable application storage prevents
entry rather than an unchecked runtime allocator call.

Every public logical core operation preserves its incoming and outgoing register/SR
context through recording. Only declared word arguments enter a record; omitted
argument slots are zero, independent of caller register contents. A seek restores the nearest retained canonical checkpoint
and replays at most 63 logical operations through the same actual routines.
Freeze saves the complete interrupted state once and blocks external logical
samples while allowing internal replay. Resume latest restores those exact
318 bytes. Seek never writes records, indexes or the live cursor. Failed seeks preserve the
selected canonical state and its persisted position cursor; target/origin/candidate
fields are scratch and may change on rejection. The native
presentation, title and Paula sinks suppress hardware work during replay.
The API requires the caller to stop the physical dispatcher while frozen; there
is no user entry path in this increment.

Indexes come from actual gameplay entry/exit points. A human serve launch has
kind 3. Incoming human return geometry probes begin one episode (kind 0), so
repeated collision checks do not create repeated misses. Accepted contact
upgrades the episode to kind 1; actual point/lifecycle termination upgrades it
to kind 2 (miss). Kind 0 remains pending. Eviction removes dependent episodes
and cancels a pending origin before any later outcome can publish it. Each
retained index identifies its operation boundary and physical court end; the
canonical state resolves logical ownership. These are internal observations,
not a second collision or trajectory model.
An origin is the boundary before the recorded operation that first observes
an eligible probe. If an incoming episode starts before retained history, later
eligible probes can begin a retained origin after eviction. That origin is
replayable, but its incoming context is truncated; the index does not guarantee
retention of the complete flight or the preceding opponent shot.

Seek currently runs synchronously while frozen. Isolated CPU cycles include
observation traps and exclude native contention; they do not establish a display
frame deadline. A future UI must schedule seek/preview work within its display
budget. This increment does not claim preview performance or tutorial rendering.

The initial four-case campaign remains failed: its third cold observation passed
native deadlines, but the controller rejected generated version/title/product
changes from the pre-commit build. The original attempts are preserved. A separate
reviewed private revalidation is required to record the usable cold observation without
changing that campaign's outcome; a new focused campaign selects only
`history-cpu`, `history-pal` and `history-ntsc`. CPU proofs cover empty history, complete uninterrupted
state/output equivalence, every retained boundary in both directions, repeated
seeks, long play, byte tick/ring/low-longword wrap, invalid envelopes/operations,
poison/relocation, all nine APIs and frozen external calls, pending-origin eviction,
register/SR equivalence and actual emitted native sink suppression. Fresh sixteen-second
PAL/NTSC captures compare native recorder bytes with isolated actual execution;
the existing cold cadence case measures affected ordinary callback/RAM costs.
Raw captures, binaries and receipts remain ignored and private. A focused pass
does not establish a complete native gate or physical-hardware coverage.
CPU reports distinguish isolated canonical-copy cost and recorded-call overhead
by API, changed pad inputs, checkpoint creation and checkpoint eviction. Their
sample distributions exclude native bus contention and hardware sink work.
History receipts label `evidence.target` as a legacy validator reference, never
as their execution target. Native receipts record the exact actual video, CPU,
chipset and RAM configuration in `evidence.actual_target` and the report target;
CPU receipts explicitly identify isolated 68000 execution without an emulator.
Native captures read the real selected presentation line and simulation interval
after execution: PAL uses line 311 and 11838 + 14906/65536 E-clock ticks; NTSC
uses line 261 and 11947 + 13180/65536. These reads verify the native selector's
result independently of the command's video label.
The trace-only fixture copies the exact main source and score include, relaxing
only two renderer LEAs that exceed PC-relative range with instrumentation. It
hashes original and generated sources and verifies that the emitted shared core
matches the standalone core after address-fixup normalization. The ordinary
product and its cold observation retain their exact bytes. Failed receipt and
trace-build attempts remain saved; completed proof computations are separately
saved as unvalidated diagnostics until their acceptance receipt passes.
