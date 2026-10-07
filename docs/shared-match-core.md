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
RUST_LOG=info python scripts/run_shared_match_core.py --two --restart --seconds 8
RUST_LOG=info python scripts/run_shared_match_core.py --demo --seconds 300
RUST_LOG=info python scripts/run_shared_match_core_fixtures.py --case all
python scripts/check_shared_core_poll.py build/tests/shared-match-core-pal-demo/report.json
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

## Focused evidence at the reviewed boundaries

Production assembly boundary: `228c31ecbdc27c32a34c08d5da7588dfa48ad4ad`.
Validation/schema boundary: `3ba1babc0396421ca36743a502cfc5f7340b91ee`.
The development executable remained byte-identical across those boundaries:
`e9420c22893b0c6e1abf5ad1fac2437ef2e8018ff78211f95bf9503c294752cc`.
The isolated executable is
`462becbdabc101841ba880dec980a2250a77a467289cbe3744a44a3c148ea482`.
These identities describe local focused evidence, not a completed native gate.

The 300-second PAL native/standalone comparison at `3ba1bab` passed 71,907
operations and 17,976 completed callbacks. It covered title, selection, play,
round pause, round sound, result sound, one completed title request and a second
demo selection. All 314 state bytes were written and compared; ordered semantic
outputs, both complete poison replays, the relocated 2,000-operation replay and
all four forbidden-access/initialization controls passed. The 240-second earlier
extent ended in result sound and is superseded by this longer case.

The PAL two-human physical selection, pause, confirmed title return and opposite
one-human selection passed 2,876 operations across 778 callbacks, including 120
paused sampling callbacks without dispatch. Both selections and final play were
asserted. The early two-human harness attempt pressed its key before native
startup sampling was installed and selected one-player mode through joystick
fire; it did not establish two-human coverage. The corrected harness waits for
the initialized native menu and asserts the actual mode commands.

Each of the five retained scoring starts passed 1,920 operation comparisons over
480 callbacks, with one native initial fixture state and no later state writes.
They retained deuce 5/5, advantage 4/6, return to deuce 5/5, advantage game award
0/0 with games 2/2, and match award 0/0 with games 6/2. Whole-fixture poisoned and
relocated replays passed. These fixtures are separate from ordinary match play.

The frozen independent trajectory passed all 10,958 ticks, with 31 flight-side
changes and zero missed publications, at production boundary `228c31e`.
Its executable hash is the same `e9420c...` product checked above; this is explicit
byte-identity reuse, not a fresh full-trajectory rerun at `3ba1bab`. Native input
sampling passed 11 checks. The host suite passed 70 tests. The early NTSC
eight-second differential passed 1,894 operations/473 callbacks, both complete
poison replays and four negative controls; its receipt binds the then-current
validation source hashes and is a bounded smoke extent, not full NTSC lifecycle
coverage. Final current-head NTSC validation remains required.

The existing emitted-byte classifier verified the standalone file against its
listing and assets. Loaded bytes reconcile as follows:

| Component | Bytes |
| --- | ---: |
| Actual shared CPU instructions | 7,538 |
| Immutable simulation tables | 10,396 |
| Shared source alignment | 2 |
| Complete canonical state | 314 |
| Eight standalone RTS sinks | 16 |
| Hunk alignment | 2 |
| Total standalone loaded bytes | 18,268 |

The native development file is 181,016 bytes; the stripped release file is
159,864 bytes with SHA256
`d70d1a0b1b5208b3798a054a64fea28d6ad775528bc3508a147b8ca9b97ab1f4`.
Native loaded code/data/BSS totals 166,228 bytes. Release stripping removes only
symbols. These sizes are not a whole-machine RAM measurement or a release cold
boot pass. The maximum observed isolated stack extent is 128 bytes; the PAL
300-second core execution accumulated 170,572,718 CPU cycles. This accumulated
total is not worst-frame cost, native contention timing or a hardware budget.

The first smoke attempt failed because its final observer call supplied both a
PC and seconds target to `run_until`; the corrected bounded breakpoint call
passed. The initial CPU dependency build failed because the environment's
default compiler was missing `clang`; the successful recovery used GCC and then
reinstalled with the existing hash-pinned requirements. Receipts and raw private
runtime state stay outside Git. Ordinary cadence, sprite publication, resource
coverage, the finite native gate and independent review remain outstanding at
this document boundary. No history buffers have been allocated.
