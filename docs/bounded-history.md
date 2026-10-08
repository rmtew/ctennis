# Bounded rolling history and seek

Tutorial increment 2 uses the actual shared 68000 core. No tutorial UI, preview,
branch command or persistent file is implemented here. Schema 2 / simulation 3
canonical states remain exactly 318 bytes; record envelopes reject other versions
and invalid audio clip IDs/offsets before restoration.

The native and standalone programs reserve one fixed 80,318-byte history BSS
buffer, plus two bytes of hunk alignment and 72 bytes of recorder metadata.
The measured baseline on the 512 KB, no-expansion target had 252,368 bytes free
at the cold one-player runtime peak and 218,632 bytes free in the two-player
measurement. A later reviewed cold observation with the original 21,470-byte history buffer
had 228,520 bytes free at peak. The chosen capacity adds 58,848 bytes. The fresh
cold one-player case measured 354,632 bytes used and 169,656 bytes free at peak,
with a largest free block of 168,464 bytes. This covers the initialized Exec pool
through restarted flight; pre-pool bootstrap and other full runtime profiles
remain unmeasured for this product.

The first two cold one-player attempts failed the title transition deadline
by 1,226 and 1,068 CCK respectively. The latter callback included a 41,238 CCK
menu copy followed by match initialization. The aligned 60-byte play, 28-byte
score and 96-byte audio resets now use longword clears with the same final
pointers and counters. A sequential comparison of the prior and changed actual
68000 executables covered 1,165 logical operations across both selections,
ticks, input clearing, return-to-title and reinitialization: canonical state,
ordered outputs, all registers and SR matched at every boundary. Match
initialization saved 2,668 isolated CPU cycles; this is a diagnostic measurement,
not a native deadline pass. The replacement cold observation passed with zero
missed deadlines or publications, 4,062 one-player rally callbacks and 935.6 CCK
minimum title deadline headroom. Its maximum callback work was 57,965 CCK;
rally maximum was 30,695 CCK. The earlier failed observations remain preserved.

There are 4,096 14-byte logical-operation records, sixty-four 330-byte canonical
checkpoints, 128 twelve-byte shot/attempt entries and a separate 318-byte saved
interruption state. Checkpoints occur every 64 logical operations. The oldest
checkpoint and its dependent records/index entries retire together: retained
history spans 4,032–4,095 operations after filling. This counts polls, logical
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
Future preview/navigation must derive the actual retained incoming-flight origin,
distinguish complete-context candidates from probe-only or truncated entries, and
choose a usable retained candidate or fallback when the requested context expired.

An actual-68000 development comparison replayed the same saved PAL/NTSC rows
with 1,024, 2,048 and 4,096 records, checking canonical state and ordered outputs
at every operation. Each video sequence had three actual misses; their incoming
flights lasted 62–64 dispatches (PAL 1.037–1.070 seconds, NTSC 1.046–1.080).
The 1,024-record buffer retained none at the next human serve; 2,048 retained one;
4,096 retained one then two with their preceding incoming origins available.
A fixed-control sequence included two accepted returns and three misses, with
52–88 dispatches of incoming flight. At its second subsequent serve, 2,048 had
lost all previous outcomes while 4,096 retained three complete contexts. These
finite observations justify the larger fixed budget without guaranteeing a
number of shots or complete context for arbitrary play. Roughly 75% of recorded
calls in the native fixtures were poll/input calls whose state and events were
unchanged; they remain recorded because call order, arguments and caller outputs
are part of the replay contract.

Seek currently runs synchronously while frozen. Isolated CPU cycles include
observation traps and exclude native contention; they do not establish a display
frame deadline. The maximum observed seek used 349,142 isolated CPU cycles, roughly 49 ms at
7.16 MHz, and 136 bytes of stack. A future UI must schedule seek/preview work
within its display budget or define display skipping. This increment does not
claim preview performance or tutorial rendering.

The initial four-case campaign remains failed: its third cold observation passed
native deadlines, but the controller rejected generated version/title/product
changes from the pre-commit build. A separate reviewed private revalidation
preserves that usable observation without changing the campaign outcome. A
subsequent three-case campaign passed the original small-buffer implementation;
its evidence does not prove corrected terminal indexing or the larger capacity.

The replacement selective campaign `e7ba28877dc44ac98611925eb714ec08` passed
all four fresh cases at product commit `0079f04`: `ordinary-one-cold`,
`history-cpu`, `history-pal` and `history-ntsc`. CPU proofs cover empty history,
12,289 operations across three traversals of the fixed ring, every retained boundary in both
directions, repeated seeks, byte tick/ring/low-longword wrap, invalid
envelopes/operations, poison/relocation, all nine APIs and frozen external calls,
pending-origin eviction, register/SR equivalence and actual emitted native sink
suppression. Actual scoring bit 7 closes a miss and cannot create a new pending
probe after terminal flight. The long proof observed three accepted returns and
five misses; native captures each observed four misses and ended with three
completed misses and three serves retained.

Fresh 24-second PAL/NTSC captures matched native recorder bytes to isolated
actual execution, including checkpoint eviction and terminal-outcome checks:

| Capture | Operations | Retained operations / seconds | Video fields / tick dispatches | Boundaries / seeks |
|---|---:|---:|---:|---:|
| PAL | 5,749 | 4,085 / 17.0509 | 852 / 1,022 | 4,086 / 8,176 |
| NTSC | 5,697 | 4,033 / 16.9889 | 1,008 / 1,009 | 4,034 / 8,072 |

Video fields count observed frame IDs; tick dispatches count API calls, not
necessarily byte-clock advances. A separate actual-CPU context measurement over
these accepted rows observed 62–66 dispatches from actual preceding opponent
launch to miss: PAL 1.037–1.104 seconds, NTSC 1.046–1.114 seconds. At the next
human serves, one, two and then three prior completed misses retained their
incoming origins. All three final retained misses had complete observed
incoming context. This finite evidence supports the capacity choice; the raw
index still requires the eligibility/fallback checks described above.

Raw captures, binaries and receipts remain ignored and private. A focused pass
does not establish a complete native gate or physical-hardware coverage.
CPU reports distinguish isolated canonical-copy cost and recorded-call overhead
by API, changed pad inputs, checkpoint creation and checkpoint eviction. Their
sample distributions exclude native bus contention and hardware sink work.
Canonical copy used 1,772 isolated CPU cycles. Long-proof recording overhead
was 360 / 490 / 864 cycles (median / p95 / maximum) for ordinary operations and
2,860 / 3,206 / 3,484 at checkpoints. Checkpoints before eviction had a maximum
of 2,488 cycles; checkpoints with eviction reached 3,484. Changed-pad-input
maximum was 428 cycles. These costs include actual observer index work and are
reported separately from the contended ordinary callback measurements.
The resource summary remains explicitly incomplete: full two-player, setup,
demo, help and pause coverage was not refreshed, and the selected campaign is
not the full native acceptance gate.
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
