# Isolated shot preview foundation

This increment is under implementation and has no acceptance result yet. It adds
an internal frozen-history API and fixed scratch storage, with no tutorial UI or
live branch commit. Preview execution uses the actual shared 68000 core.

`game_preview_request` accepts the current generation, a retained completed
attempt ordinal (or `ffff` for explicit current serve setup), and legal byte X/Y.
The selected boundary is the existing `game_history_position`. A completed serve
requires its pre-launch boundary. A return or miss requires a retained preceding
opponent launch and a selection from that launch through the original action's
pre-operation boundary. A raw probe origin alone is insufficient. Missing or
truncated incoming context is unavailable; fallback requires actual current serve
setup and never resets the game.

The resolver replays from the oldest checkpoint through the original action.
`game_preview_step` accepts a generation and a budget of one to four logical API
operations, including resolver operations. Each operation saves its working
canonical context and restores the selected 318 bytes and all 72 history metadata
bytes before yielding. The original recorder mode remains frozen (mode 2); the
history ring, live backup, cursors, and existing output state are preserved.
Request and worker copying costs are additional to the operation cap. Total
resolver work and repeated position-edit cost must be measured before making a
responsiveness claim.

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

Storage is 5,546 bytes: 106 metadata, 72 saved history metadata, four 318-byte
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
