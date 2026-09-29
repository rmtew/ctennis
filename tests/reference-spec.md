# Original-game reference specification

Agreed 2026-09-30. This specifies evidence to collect from the original cartridge
and compare against the maintained Amiga port. It is a coverage plan, not a
claim that the captures or port implementation are complete.

## Strategy

Use two complementary continuous replays as the main protection against
accumulated state drift. Initialize once and carry the actual state through
successive serves, rallies, points, games, waits and match completion. Compare
every logical callback so a later visible error is traced to its first state
divergence. Replay length alone does not establish variety: record the meaningful
behaviours actually observed. Do not pursue every input combination or arbitrary
instruction/branch coverage.

Add a short focused case only when an important source behaviour is absent
from both replays. Prefer a reachable captured starting state and a short input
sequence. State injection is acceptable only with documented source invariants
and an explanation of why the state is reachable. Expected behaviour comes from
the cartridge and annotated source, not assumed standard tennis rules.

## Primary replays

| ID | Required sequence | Purpose | Current evidence |
|---|---|---|---|
| R1: one-player match | Reset, select one-player mode, play a complete match, finish the result sequence and start another game. Include successive game transitions and the first resumed serve after each. | AI/random decisions, accumulated ball/player/score state, clocks, sound, round resets and match/restart behaviour. | Exact prefix fixture now covers 1,566 updates through first game, tail-only pause and resumed serve flight; port matches 1,332 and fails at the known round transition. The older 2202-callback capture remains partial evidence. Full-match capture/comparison remain required. |
| R2: two-player varied match | Reset, select two-player mode, use both controls, play a complete match and restart. Deliberately vary movement and action timing, rally length, point winners and scoring sequences. | Complement AI play with both human input paths and varied consecutive state transitions. | Required; no complete reference fixture or port comparison established. |

Choose scripts based on observed source behaviour. Seek serving from both ends,
returns by both players, wins by both sides, short and longer rallies, and the
source's deuce/advantage-like score transitions. If one replay cannot produce a
desired behaviour reliably, keep its observed coverage and add a focused case;
do not label an intended outcome as captured coverage. Mode and side labels
must be correlated with actual source input/display evidence.

The existing S1 serve case remains a fast regression during edits. It covers
200 callbacks of serve, flight, return and a point, with continuous RAM and
ordered sound comparisons. It is a prefix-sized reference, not a replacement
for R1/R2.

## Behaviour inventory

For each row, record which replay and callback interval establishes it. A row
without evidence remains a gap. One interval may establish several rows.

| Behaviour | Observable evidence required |
|---|---|
| Startup and mode selection | Selected mode/control flags, initial positions, score and first serve; selected title/mode screenshots. |
| Both player controls | Press, hold, release and direction changes; normalized input, movement cadence and action result for each side. |
| Movement limits | Approach and hold against each distinct source-defined court limit; exact stopped coordinates. |
| Both serve paths | Waiting/attached ball, action or AI trigger, animation phases, launch trajectory and update timing from each end. |
| Rally and returns | Court and displayed ball coordinates, flight vector/step, contact outcome and replacement trajectory; returns by each player. |
| Court/net outcomes | Source-defined bounce, net contact and out-of-court sequences, resulting flags and eventual point attribution. |
| Input/contact ordering | Input at a meaningful contact/serve boundary; whether the action is accepted and the resulting trajectory. |
| Point scoring | Awards to both sides, pending display update, sound and next serve state across consecutive points. |
| Deuce/advantage-like scoring | Entry, advantage gain, return to equal score, and game award from advantage, using source point codes as authority. |
| Game transition | Award, point clearing, position/animation reset, tail-only callback interval, timed/audio waits, mode/side setup and first resumed serve. |
| Match completion/restart | Source winning condition, result/sound sequence, menu/round reset and a playable subsequent serve. |
| AI/random state | Source PRNG evolution and explicit refresh-bit decisions at their actual consumption points; resulting targets/trajectories. |
| Clock accumulation | Source primary tick wrapping and auxiliary timer saturation where reachable; timers and audio countdowns through gameplay and waits. |
| Presentation and sound | Score/status/mode selection and expiry, sprite priority/position and prior-buffer presentation lag, ordered sound events and selected visible/audible checkpoints. |

The source point-code and game-count rules are documented in
[the static review](../analysis/static-rom-review.md) and
[the update contract](../analysis/frame-update-contract.md). Their inferred
user-facing labels must not replace exact captured codes in the oracle.

## Fixture contract

Each reference case must retain:

- Case ID, purpose, actual observed coverage intervals and explicit gaps.
- Cartridge SHA-256, source emulator version, machine/input configuration,
  capture script/version and capture hashes.
- Reset/setup input sequence and the exact captured initial state. A fast
  state-start replay must retain its relationship to the reset-derived run.
- Ordered input press/release events and the boundary where they become
  visible. Record both players' normalized inputs for simulation replay;
  retain raw control events for separate input integration checks.
- PRNG initial state and any external random decisions, including consumed
  Z80 refresh bits. Do not regenerate expected results using the port or a
  Python game model, or silently assume a fixed refresh bit for new cases.
- A monotonically increasing logical callback ordinal, callback kind
  (gameplay or tail-only), and source frame/time as separate metadata.
- State after gameplay where applicable, state after the common tail, and
  ordered PSG events associated with that callback. Include main-thread
  transition actions between callbacks so their ordering and state effects
  are reproducible. Tail-only callbacks must not acquire gameplay work.
- Selected source screenshots and sound/presentation event timing at named
  transitions, separate from the simulation state oracle.

Capture twice from the same reset/setup and require identical state, input and
sound-event records. If source entropy prevents repeatability, identify and
control or record it explicitly before accepting a deterministic fixture.
Do not silently filter differing records. Freeze reference data separately
from normal port tests; changing it requires an explicit capture operation.

Do not assume one callback per video frame. The existing long capture includes
multiple callbacks in a frame at the round transition. Frame-end observations
are sufficient for the established S1 active-play case, but must not be used
as substitutes for exact callback/main-thread boundaries in R1/R2 transitions.

## Comparison and acceptance

Compare discrete simulation values exactly at corresponding logical boundaries:
player/ball coordinates and trajectories, phases/flags, scoring, AI/PRNG state,
timers and audio state/events. Keep arithmetic widths and update order visible.
Initially retain byte comparisons where meanings or representations are not
fully decoded. Map known fields through `state-fields.json`; explicitly name
unassigned bytes rather than invent semantics.

The S1 suite excludes only source callback-pointer bytes C000-C001. For future
native state layouts, document each mapping and any exclusion of hardware
addresses, display buffers or diagnostic counters. Never broaden exclusions
merely to make a failing replay pass. Preserve meaningful graphics-selection
state even when the actual rendering buffers differ.

On failure, return a failing exit status and retain the first divergent callback,
boundary, named field/event, expected/actual values, neighbouring state and the
input/random prefix needed to reproduce it. Keep routine/source/executable and
fixture hashes. A deliberately introduced gameplay mutation must demonstrate
that the runner detects differences; restore it before accepting the suite.

Simulation acceptance requires no unexplained differences throughout each
required replay and focused gap case. Hardware acceptance remains separate:
real controller sampling, native Copper/bitplane/sprite presentation, Paula
playback, source-rate scheduling, blanking deadlines and complete-match live
play on the target PAL A500 profile. The accelerated harness cannot prove those.

## Coverage status and next capture

Use these statuses independently: **required**, **captured** (repeatable source
fixture), **passing** (port comparison), and **gap** (missing behaviour or
comparison). A partial capture or sampled match does not promote the entire
case to passing.

S1 is captured and passing at every retained boundary: 200 callbacks, 254 RAM
bytes at two boundaries, and 40 ordered PSG bytes. R1 now has a twice-identical
exact prefix through first game, 136 tail-only callbacks and resumed serve
flight: 1,566 updates, 285 PSG bytes, eight refresh decisions and all intervening
RAM writes. The actual runner matches 1,332 updates and 250 PSG bytes, then fails
at callback 1333 before the native round transition is implemented. R1 is not
a complete captured or passing match. R2 remains required.

Next implement the native round transition against that frozen R1 prefix,
and extend the source recording to match completion/restart. Obtain R2 with complementary
input/scoring variety, assess the inventory above, and add only the focused
cases justified by remaining gaps. Reuse the current suite and capture helpers;
this specification does not require a new test framework.
