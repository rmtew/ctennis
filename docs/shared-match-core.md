# Production shared match core

This is increment 1 of the authorized tutorial roadmap. History, seek, shot
previews and tutorial controls are not implemented. The historical PR #32
[362-update proof](match-core-proof.md) remains separate evidence; its 307-byte
inventory and copied native executable are not this production boundary.

## Code and ownership

`amiga/game/core.s` includes the actual controls, dispatcher, gameplay, scoring,
scene and audio routines in both `amiga/main.s` and `amiga/standalone.s`.
The standalone executable does not include physical input, UI construction,
graphics banks, hardware output or hardware clocks. It has synchronous output
sinks. All simulation rules and lifecycle decisions execute on the 68000.

The canonical block is 314 contiguous bytes, including reserved packet bytes.
The machine-checked ownership and checkpoint-envelope contract is
`scripts/match_core_state.py`; packet interiors retain the assembly G_, S_, AV_,
D_ and O_ definitions. Schema version 1 and simulation version 2 bind the current
layout and seeded-entropy policy. A checkpoint envelope binds the exact compiled
standalone rules hash as well as both versions and complete byte length.
The validator checks audio clip IDs and aligned offsets, including completion
at the exclusive clip boundary. It does not certify arbitrary corrupt state:
other table-index validation remains a requirement for a future restore API.

`game_core_init` clears the complete block and enters TITLE. A new match gets
one explicit 16-bit seed; zero maps to `$ace1`. Live play samples a hardware seed
only at native selection. Both live play and the attract demo thereafter use
the existing Galois16-b400-v1 generator, alongside the unchanged game PRNG.
The full current generator state is canonical. Audio AV_NEXT stores an offset
from the immutable audio-table base; no relocated pointer is checkpointed.

## Logical boundary

The public boundary comprises init, select(mode, seed), sample_pads(A, B),
sample_result(continue held/pressed, automatic continuation, playback active/
mask, selection held), clear_inputs, latch_actions, return_title, round_poll
and tick_dispatch. Selection and title requests are commands, not direct
adapter writes to lifecycle state. Native physical aliases, UI gestures, demo
packet cursors and presentation timers remain outside canonical state.

An unpaused native callback polls the previous logical input once, samples the
physical controls into logical pads, processes UI actions and result metadata,
accepts any selection command, then dispatches. The dispatcher decides its own
lifecycle path from canonical state. Native rendering and publication surround
these calls. The operation recording captures API arguments and order; it never
chooses a callback regime or supplies an intermediate expected state.

Paused ordinary play still samples logical pads and metadata without dispatch.
This retains existing release and action-latch behavior. Ordered logical
operations, including these samples, are required for exact replay; recording
only the final held mask at dispatched ticks would lose a release/repress.
Tutorial interruption isolation is later work and is not established here.
Button 2 retains existing shot behavior until the tutorial UI increment.

The ordered semantic output comparison covers calls inside logical operations:
scene objects/ball layer and display fields at render, field/status publication,
title requests, and each logical voice period/level. Physical pre-dispatch
render calls and native bank publication are presentation work outside these
semantic operation traces; existing native raster/publication checks protect
that integration. Shot/no-contact explanations are not added in this increment.

## Validation

Use the normal pinned native tools, legitimate external Kickstart 1.3 and the
hash-pinned CPU dependency in `tests/match-core-proof-requirements.txt`:

```sh
CC=gcc CXX=g++ python -m pip install --require-hashes --no-binary=machine68k \
  -r tests/match-core-proof-requirements.txt
RUST_LOG=info python scripts/run_shared_match_core.py --seconds 8
RUST_LOG=info python scripts/run_shared_match_core.py --ntsc --seconds 8
RUST_LOG=info python scripts/run_shared_match_core.py --two --seconds 8
RUST_LOG=info python scripts/run_shared_match_core.py --demo --seconds 300
RUST_LOG=info python scripts/run_demo_match_tests.py
```

The native trace is compiled only with CORE_TRACE. Production emits neither
mailbox storage nor trace instructions. Trace wrappers preserve registers and
SR; internal calls remain inside the root operation. A native write observer
rejects dropped events, non-core writers and canonical writes outside a logical
API, reconstructs all state bytes, and checks one final direct native read.
LoadSeg hunks are verified against the compiled fixture before running.

The isolated CPU starts with poisoned memory/registers, executes actual 68000
calls, compares complete state and ordered outputs after every operation, and
audits reads against narrow immutable-table declarations. Independent replays
start from the initializer with two poison patterns and consume only recorded
arguments. Negative controls must detect omitted initialization, hardware reads,
out-of-state writes and undeclared data reads. These are safety and determinism
checks, not a second implementation of the game.

Case-specific receipts under ignored `build/tests/shared-match-core-*` identify
source/input/tool/ROM hashes, exact executable hashes, target, operation extent,
observed lifecycle coverage, stack high-water and isolated CPU cycles. A rerun
invalidates that case's prior pass before building. CPU cycles exclude Amiga
contention and physical presentation work. They do not prove native deadlines
or a worst-case budget. Native acceptance, resource reports and independent
review remain required before calling the increment complete.
