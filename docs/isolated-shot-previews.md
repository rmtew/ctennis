# Isolated shot preview foundation

This increment is under implementation. The first small actual CPU proof passed
at `652c89d`. The cache extension passed its focused actual CPU proof at
`96a158a` and independent receipt review; broader acceptance remains pending. It adds
an internal frozen-history API and fixed scratch storage, with no tutorial UI or
live branch commit. Preview execution uses the actual shared 68000 core.

`game_preview_request` accepts the current generation, a retained completed
attempt ordinal (or `ffff` for explicit current serve setup), and legal byte X/Y.
The selected boundary is the existing `game_history_position`. A completed serve
requires its pre-launch boundary. A return or miss requires a retained preceding
opponent launch and a selection from that launch through the original action's
pre-operation boundary. A raw probe origin alone is insufficient. Missing or
truncated incoming context is unavailable; fallback requires actual current serve
setup and never resets the game. Every request requires the selected lifecycle
to be PLAYING, including historical candidates. A timed human serve remains
selectable through its complete boundary at serve clock 16; the actual launch
reads clock 16 on entry, then the service tail advances it to 17. Timed phase
20 at a later clock is unavailable. Setup/wait phase priority follows the actual
player dispatcher.

The resolver replays from the oldest checkpoint through the original action.
`game_preview_step` accepts a generation and a budget of one to four logical API
operations, including resolver operations. Each operation saves its working
canonical context and restores the selected 318 bytes and all 72 history metadata
bytes before yielding. The original recorder mode remains frozen (mode 2); the
history ring, live backup, cursors, and existing output state are preserved.
Request and worker copying costs are additional to the operation cap. Total
resolver work and repeated position-edit cost must be measured before making a
responsiveness claim. The first return fixture required 773 resolver operations
and about 12.4 million isolated CPU cycles for a repeated one-operation edit
(~1.73 seconds at nominal 7.16 MHz), motivating the compact cache extension.

Four canonical scratch images hold the selected state, common edited start,
held continuation and released continuation. Only the requested human X/Y change
in the common start; both variants retain its exact RNG. Legal bounds come from
the actual phase-selected movement tables. Each variant first calls the actual
pad edge sampler, including when selection follows that tick's original pads.
Every subsequent pad sample clears human directions/button 2 and forces button 1
held or released while preserving opponent inputs. Actual latches, waits and
reactive AI remain in use. Equal initial seeds do not guarantee paired AI draws.

Recorded future API order and arguments continue until retained history ends.
Afterward the explicit continuation is poll, pads, zero result metadata, dispatch;
opponent inputs retain the last sampled value and reactive AI remains actual core
behavior. Observed full boundaries classify landing, net, out, interception,
no-contact, lifecycle interruption, or the finite path limit. A no-contact path
never claims a fabricated outgoing shot.

Each of two paths contains at most 256 eight-byte samples: court X/Y, actual
projected ball X/Y, contact, flight, packed ball/shadow colour nibbles, and tick.
Projection and visibility come from actual core outputs; no independent height
model is introduced. Common incoming samples precede each alternative. Coincidence
compares court/projected geometry and visibility at matching sample ordinals and
ticks, while retaining contact, phase and outcome diagnostics separately.

Storage is 5,550 bytes: 110 metadata, 72 saved history metadata, four 318-byte
canonical images and 4,096 sample bytes. The enclosing hunk adds two alignment
bytes. Counts and generations guard unpublished storage. Results become visible
only after both current variants finish or honestly truncate. Stale requests,
steps, cancellations and result reads reject before mutation; cancellation
invalidates the generation. Generation exhaustion rejects instead of aliasing.

The first focused CPU proof is deliberately small: a completed serve, a completed
return selected after pads, and that return immediately before dispatch. It
compares each chunked variant with an uninterrupted actual-core execution from
its edited start, including canonical state, projected path and ordered semantic
outputs. Every yield snapshots the entire loaded image outside preview scratch
and the existing output queue; frozen history writes are forbidden. Native sink,
cadence, eviction/fallback and wider outcome coverage remain pending.

Publication also requires that the selected canonical state and complete history
metadata still match the request. Current-serve fallback rejects an AI server.
Continuation stops before retained init/select/title operations and checks
lifecycle after every operation, so a reset cannot silently become a new preview.
The small proof checks its observed call stream independently against the known
fixture and explicit continuation policy, preserving every opponent/result
argument and observing the first dispatch's actual assigned human action.

Completion of this increment additionally requires eviction/truncated-context
and current-human fallback proofs; lifecycle operations between dispatches;
no-contact/net/out/interception/limit/coincidence coverage; generation exhaustion
and cancellation; relocation and full-image native sink suppression; measured
native typical and fresh-input/transition costs; and a measured decision on total
resolver latency and repeated-position edits. A first-small CPU pass satisfies
only its stated finite extent.

The AI-serving negative uses a separate actual init/select/control sequence.
`game_score_flags` bit 1 marks lower AI ownership, so the fallback's bit-1
selection chooses the human end. In a genuine AI serve setup the human end has
no serve phase; rejection proves unavailable human serve context. It does not
isolate the defensive AI-ownership check with fabricated inconsistent flags.

The compact cache reuses a fully published original incoming prefix, action
boundary and context identity only when the selected 318 canonical bytes, all
72 history metadata bytes, requested ordinal, retained origin, kind and end still
match. It stores only a validity word and ordinal. A warm position edit starts a
new generation and clears all variant bookkeeping; old outgoing suffix bytes
stay inaccessible until both new variants finish. Cancellation and successful
external history mutations invalidate cache and publication and retire the old
generation. Generation retirement saturates at `ffffffff`; history operations
continue, but new preview requests reject rather than alias. Internal request
restoration of the oldest checkpoint uses an explicit active-3 bypass.

History seek now saves its 72 metadata bytes on the stack after pure range
checks. Any rejected checkpoint envelope or operation restores those bytes;
canonical restoration still occurs only after complete upfront validation. A
failed seek preserves READY publication and cache. The focused CPU proof observed 204 bytes maximum stack, including request
nesting and the backup; this is a finite observation, not a universal bound. The new proof compares an actual warm edit against a forced cold edit
with identical position, both full contexts, paths and ordered outputs. It also
checks prefix immutability and invalidation by seek/back, different attempt,
cancel, eviction and generation exhaustion, plus READY corrupt checkpoint and
operation negatives. These are CPU claims only; native sink/cadence and resource
coverage remain pending.

At `96a158a`, the three initial serve/return cases and cache proof passed using
actual 68000 execution. The warm edit performed zero resolver operations versus
773 for its identical forced-cold edit. Warm request cost was 18,200 CPU cycles;
its workers used 6,177,874 cycles across 114 calls, with 81,450 maximum per call.
Cold request cost was 21,572 cycles; workers used 15,137,104 cycles across 308
calls, with 95,112 maximum. Both variants had identical full edited/final canonical
states, paths and ordered outputs between warm and cold execution; 52 original
incoming samples were preserved. Every edited byte outside requested human X/Y,
including RNG, remained unchanged. READY checkpoint schema/simulation/state and
operation failures preserved canonical/history/cache/generation/publication;
observed failure costs were 12,082–12,818 cycles (190 for an out-of-range target).
Seek/back, different attempt, cancel, actual eviction and exhaustion checks passed.

The cache reduces this fixture's worker CPU cost about 59%, but the warm result
still needs approximately 0.86 seconds at nominal 7.16 MHz. At one four-operation
worker call per PAL frame, 114 calls would take about 2.28 seconds. No UI frame
budget or instant edit response is established. Editing before READY, changing
time/attempt, or canceling can require a cold resolver. Native interrupts, display
work and DMA contention were absent from these CPU observations.

The compiled standalone image is 109,436 loaded bytes, 280 more than the first
small implementation (276 code and four fixed metadata bytes). This is a
standalone compile measurement, not current native RAM/cadence acceptance. The
fixed preview allocation is 5,550 bytes plus two enclosing alignment bytes;
72 bytes of failed-seek rollback are stack storage. Current native resource
metrics have not been refreshed with this product. Native/full outcome/eviction
context coverage, practical performance, tutorial UI and branch commit remain
pending. Historical failed attempt 000001 and first-small attempt 000002 remain
preserved privately; current cache proof is attempt 000003 of its selective CPU
campaign, with no complete native gate claim.

The next focused proof is stage A1: actual current human serve fallback and timed
prelaunch boundaries, stale title and postlaunch rejection, no-contact and the
256-sample limit, partial calculation replacement, resets between dispatches,
and a retained completed probe whose earlier incoming launch has evicted. It
uses uninterrupted actual-core continuations and checks recorded API order and
inputs independently. A1 passed at `59152fa`, selective CPU attempt 000004, and
independent receipt review cleared its source/tool/product bindings. Earlier
attempts remain preserved. This is partial CPU acceptance; A2 endpoint discovery,
A3 relocation/native sink/history regression, current native resources, practical
performance, tutorial UI and branch commit remain pending. The current standalone
image is 109,464 loaded bytes, 28 more than the previously tested cache image;
this does not establish native RAM or frame acceptance.

The A1 current human wait-phase fixture produced a held landing path of 66
samples and a released limit of 256 samples with no human launch. The limit is
incomplete attached-ball observation, without a claimed outgoing shot. Complete
timed boundaries at clocks 15 and 16 were accepted before an actual launch; the
launch hook read entry clock 16 and the first postlaunch complete boundary read
17 and was rejected. A real returned-title state retained wait phase 64, but
both fallback and historical requests rejected without changing frozen state.

A completed actual miss produced two no-contact paths of 65 samples. Interrupted
RESOLVE and HELD requests changed legal X from 111 to 112, retired old results,
and restarted cold: each replacement resolver used 773 one-operation calls and
12,406,566 CPU cycles. The edited 318-byte start changed only requested human
coordinates, including unchanged RNG. Init/select/return-title operations after
clear/latch/result calls stopped before reset execution, with zero path samples.
The truncated-context fixture retained completed kind 1 at probe 696 while its
actual incoming launch 564 was older than oldest 576. Its resolver used 325
operations, ended unavailable, and exposed no result/cache. The fixture used
193 dispatches and 4,608 logical operations within its declared 512/8,192 bounds.

The current-serve limit required 323 four-operation workers and 15,680,438 CPU
cycles; the missed-contact fixture required 328 workers and 16,131,256 cycles.
Across the combined small/cache/A1 receipt, the maximum observed worker cost was
95,158 CPU cycles and observed stack depth was 204 bytes. Every checked public
call preserved selected canonical state, all 72 history metadata bytes, the
history store and live output queue. These finite isolated CPU measurements
exclude native interrupts, DMA, presentation and UI work.
