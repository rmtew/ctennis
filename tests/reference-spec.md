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

## Behavioural contract versus translation diagnostics

The required behaviour coverage survives changes to the Amiga implementation.
Current byte-level RAM and ordered PSG comparisons are temporary diagnostics
for the translated starting point, not an obligation to retain its state
layout, register emulation, callback pointers or original hardware interfaces.
The final suite observes actual maintained native code through a small test-only
adapter: named gameplay state/outcomes, input acceptance, timing, displayed
content and audible events. Independent source captures remain the oracle.

When replacing a subsystem, establish its behavioural comparison alongside
existing diagnostics, retain continuous and focused cases, and document each
mapping/exclusion before retiring obsolete checks. Preserve arithmetic effects,
update ordering and cadence where they affect behaviour; internal addresses,
register choices and routine structure may change. Captured source starts and
random inputs need documented mappings to native initial conditions and choices,
not a production emulation layer. The adapter must not calculate expected game
behaviour or inject expected intermediate writes. Audio and graphics acceptance
must compare equivalent observable output with explicit timing/tolerance rules.

The suite-first baseline remains required in full. Later diagnostic retirement
must preserve every required behaviour and reviewed known-failure status; it
cannot silently weaken coverage or classify missing adapters as passing. See
[the native endpoint and migration gates](../Champion-Tennis-Amiga-Port-Agent-Roadmap.md).

## Primary replays

| ID | Required sequence | Purpose | Current evidence |
|---|---|---|---|
| R1: one-player match | Reset, select one-player mode, play a complete match, finish the result sequence and start another game. Include successive game transitions and the first resumed serve after each. | AI/random decisions, accumulated ball/player/score state, clocks, sound, round resets and match/restart behaviour. | Exact prefix fixture now covers 1,566 updates through first game, tail-only pause and resumed serve flight; port matches 1,332 and fails at the known round transition. The older 2202-callback capture remains partial evidence. Full R1 now captures 13,378 updates through match result/restart twice identically, preserves the prefix exactly, and executes the native replay with the same first divergence at 1333. Later native regimes remain obscured until phase-specific comparisons exist. |
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
bytes at two boundaries, and 40 ordered PSG bytes. R1 is now captured twice
identically through match result and first advancing restarted serve: 13,378
updates, 3,344 PSG bytes, 50 refresh reads and 1,002 between-callback RAM writes.
Its existing 1,566-update prefix remains exactly identical. The actual runner
executes the complete replay, matches 1,332 updates and 250 PSG bytes, then first
diverges at callback 1333 before the native round transition is implemented.
This is known red; later native regimes still need independent phase cases.
R2 remains missing.

Next complete the suite before port cleanup: obtain R2 with complementary
input/scoring variety, assess the inventory above, add only meaningful focused
gaps and phase cases, and collect P1-P3 references/adapters. The registered
aggregate runner now checks known-red signatures and mutation detection while
reporting missing coverage as failure. Reuse the current suite and capture
helpers; this specification does not require a new test framework.

## Execution plan and artifacts

The remaining work below is an actionable capture backlog. Proposed filenames
are destinations to implement, not files or CLI options that already exist.
Keep the existing S1 and R1-prefix fixtures unchanged while developing longer
captures. Each accepted recording must have its own case definition and oracle.

| Case | Case definition | Private oracle | Raw evidence and report |
|---|---|---|---|
| S1, existing | `tests/cases/serve.json` | `tests/reference/serve.json` | Existing `build/tests/` serve outputs |
| R1-prefix, existing | `tests/cases/round-transition.json` | `tests/reference/round-transition.json` | `build/tests/round-reference-capture/` |
| R1 full match | `tests/cases/one-player-match.json` | `tests/reference/one-player-match.json` | `build/tests/one-player-match/` |
| R2 full match | `tests/cases/two-player-match.json` | `tests/reference/two-player-match.json` | `build/tests/two-player-match/` |
| Focused F1-F5 | `tests/cases/<case-id>.json` | `tests/reference/<case-id>.json` | `build/tests/<case-id>/` |
| Presentation P1-P3 | `tests/cases/presentation.json` | `tests/reference/presentation/manifest.json` and media | `build/tests/presentation/` |

Each directory must contain the two raw capture streams and logs, a validation
report, a coverage manifest, and hashes identifying the frozen case, scripts,
emulator and oracle. Presentation directories additionally contain the media
listed below. Keep ROM-derived data and media ignored. Track case definitions,
scripts, field mappings and concise conclusions. Never replace a fixture merely
because the port fails it.

The coverage manifest must identify, for each behaviour ID below: source case,
callback start/end, relevant fields/events, source evidence or screenshot/audio
IDs, capture status, and port comparison status. Missing rows are gaps, not
passes. This manifest is evidence indexed by case; WORKLOG.md remains the
authoritative overall status and next action.

## R1: extend the existing one-player input script

1. Reuse the verified reset sequence: SC-3000 NTSC, key PA3 mask 0x10 pressed
   after source frame 120 and released after 420; port-1 fire pressed after
   frame 1300. Begin exact callback capture at the existing initial boundary.
2. Hold fire without movement through the first complete match. Preserve all
   callback kinds and main-thread activity through every game and the final
   result. Do not stop at six games without observing what the source does next.
3. Identify the result-to-menu/round transition from the source mode flags,
   callback routing and displayed state. Release held fire at the first verified
   input-accepting restart boundary, wait through the source's debounce/release
   condition, then apply the verified selection action again. Capture the first
   advancing serve flight after restart before stopping.
4. Discovery of the restart boundary/action is explicit work: inspect the menu
   and match-end source path, perform a short source input probe, and retain the
   accepted flags and displayed mode. Do not guess a fixed wait or reuse a key
   merely because it selected the initial mode.
5. During discovery, source-state guards may select physical input changes.
   Freeze the resulting exact event schedule, then replay that schedule twice
   from reset to accept the oracle. The port never drives the reference policy.
6. Require the first 1,566 updates to match the frozen R1-prefix in entry,
   pre-tail/post-tail RAM, input, refresh and PSG observations. The prefix's
   final partial timeline must also agree up to its last recorded return.

R1 is complete only when the source has awarded the match, completed its result
sequence, accepted restart, and advanced a fresh serve with reset scores and
the correct source initial round state. Record each game's winner, award,
pause, setup and resumed serve. Held-fire play may miss some outcomes; retain
those as gaps for R2/focused cases rather than adding arbitrary randomness.

Use a finite capture watchdog, initially 120,000 logical callbacks after the
initial checkpoint. This is a diagnostic bound, not a success condition. If
the required stop predicate is not reached, preserve the partial capture and
last phase/input/score, report incompleteness, and adjust the script or bound
from that evidence. Do not silently accept a time-limited partial match.

## R2: input calibration and complementary match recipe

The original's two-player control mapping is a prerequisite with a concrete
deliverable, not an assumed joystick layout. Create a source input-map record:
for each physical direction/action and mode-selection key, record the MAME
port/field, press/release value, returns from both input readers, normalized
direction/action bytes, affected player and observed response. Preserve the
mode/side changes that exchange control ownership. Probe each control alone,
then simultaneous controls for both players. Select two-player mode and prove
that each player responds independently before recording R2.

Use this deterministic recipe to construct the R2 input schedule:

| Stage | Physical input plan | Required observation / stopping guard |
|---|---|---|
| Setup | Reset and apply the calibrated two-player selection/release sequence. | Two-player mode, both input groups and initial serve state confirmed. |
| Control exercise | During reachable serve waits, press each direction for 12 callbacks, release for 4, reverse for 12, release for 4; repeat for both players when movement is allowed. Include one simultaneous movement interval. | Press/hold/release, reversal, movement parity and independent players; blocked movement is documented, not counted as movement coverage. |
| Short points | Trigger the current server's action; leave the receiver action released for one point. Exchange intended winner on the next point using a verified reachable miss policy. | Actual points awarded to both sides; record intended versus observed winner. |
| Rally | Move each receiver toward a source-observed contact target and trigger its calibrated return action. Vary action onset by one callback around a previously successful return. | At least one continuous rally containing a return by each player and at least four successful returns in total. |
| Scoring variety | Use deliberate returns/misses to alternate actual point winners until the source reaches point codes 5/5. Then gain advantage, lose it back to 5/5, regain it and finish the game. | The exact source score transitions, not a presumed count of points. If this policy cannot produce them reliably, isolate F3 and retain R2's real coverage. |
| Complete match | Continue deterministic play, with both sides winning at least one game, until the source ends the match. | Both serve ends, repeated round changes, game wins for both sides and source match completion. |
| Restart | Release/selection sequence calibrated for the result/menu state. | Scores reset and a new advancing serve flight. |

The numbers above specify input durations for script development, not expected
movement distances. Positions come from the source. A contact-target policy
may use captured source state during discovery, but must not inject ball,
score or player state into the continuous match. Freeze the resulting physical
input schedule before the two acceptance captures. Use the same diagnostic
watchdog and incomplete-run reporting as R1.

An impossible intended outcome is not a reason to invent state. Preserve the
replay, explain the missing behaviour and create the smallest reachable focused
case below. If human-assisted input discovery is necessary, record it as an
exact replayable schedule; neither final reference run may depend on live input.

## Focused cases, only for observed gaps

Assess R1/R2 first. A case is unnecessary when the same evidence already exists
in a continuous replay; link that interval instead. Required behaviours remain
required even if a focused case must supply them.

| ID | When needed | Construction and observations |
|---|---|---|
| F1 movement boundaries | A distinct reachable bounds row/direction is absent. | Start from a retained reachable state for that player/animation bounds row. Hold toward the limit until position is unchanged for four accepted movement callbacks, continue four, then reverse for four. Record exact positions, tick parity, direction and movement-blocking flags. Repeat for each missing direction/player/row. |
| F2 contact/input timing | A meaningful timing boundary is absent. | Retain state before a verified successful serve/return. Replay action onset one callback earlier, at the successful onset, and one later, holding duration otherwise identical. Record acceptance, player phase and resulting flight vector. For a missing geometric contact edge, obtain adjacent reachable player positions and repeat; do not assume which coordinate is inside/outside. |
| F3 scoring sequence | Required equal/advantage or winner sequences are absent. | Prefer a source replay prefix reaching the missing score pair, followed by actual played points. Record the source point codes, winner selection, game counts, reset timers, redraw and PSG events. A shorter score-state injection must cite reachable source invariants and retain the natural prefix that proves the state. |
| F4 court/net outcomes | A distinct bounce, net or out outcome is absent. | Reuse reachable pre-launch/contact states and vary legitimate source actions/player positions until the original produces the missing outcome. Retain launch/flight vectors, contact flags, displayed/court coordinates, eventual point attribution and sound. No fabricated trajectory constants. |
| F5 clocks/random choices | Wrapping, saturation or a meaningful refresh-sign outcome is absent. | Prefer intervals already in the long replays. Otherwise extend a reachable wait/idle sequence across the missing timer boundary. For random-sign comparison retain reachable PRNG state and explicitly controlled consumed R decisions; label entropy injection separately from unmodified source captures. Record target/trajectory effects and subsequent consecutive state. |

Every focused case has an initial state, its provenance, an exact input/entropy
schedule, a finite stop guard and the named outcome being tested. Re-capture
twice. Do not turn this list into tests of every arbitrary RAM value or every
arithmetic instruction.

## Presentation checkpoint manifest

P1 is graphics, P2 is audio and P3 is timing/input hardware. Reference collection
can be completed before the Amiga presentation matches it. Store a source
callback ordinal and video frame for every image/audio interval, because a
displayed sprite buffer may belong to the preceding simulation update.

| Checkpoint ID | Source capture trigger | Required artifacts |
|---|---|---|
| P1-title / mode | Stable title, then accepted one-player and two-player selections. | Native-resolution lossless screenshots, mode flags, palette and layout/field geometry. |
| P1-serve-lower / upper | Waiting attached ball, action accepted, launch and first advancing flight for each end. | Screenshots and sprite records at each stage; pattern/colour/priority and court-versus-displayed ball position. |
| P1-rally | First successful return by each player, a bounce and each missing net/out outcome. | Screenshots for the event and following display update; source sprite records and ball/contact state. |
| P1-points | Each distinct point-code graphic observed, including equal/advantage pairs. | Score-field crops and whole-screen screenshot at the first displayed update, with logical score and consumed redraw flag. |
| P1-status | Each reachable status text first appears and first disappears. | Whole-screen images, status field/expiry timer and callback IDs; identify source render lag. |
| P1-game / match / restart | Game tally displayed, round reset, final result displayed and first restarted serve. | Before/after screenshots and field/sprite state; short lossless frame sequence for each transition. |
| P2-events | Serve, return/contact, point, round setup and match/result sound sequences actually present. | Ordered PSG writes with callback IDs, source tone/attenuation state and WAV intervals including onset through silence or the next event. Label noise events explicitly if any occur. |
| P3-cadence / controls | Sustained play plus each distinct tail-only/result regime; calibrated press/release for both players. | Source frame/time-to-callback mapping, raw control events, input-reader consumption boundary and displayed-state relationship. |

For graphics comparisons, crop borders and use the source's 256x192 logical
image without interpolation. Compare court/field geometry, glyph content,
sprite shape/placement/priority and timing exactly; list palette differences
separately. Account for the chosen Amiga palette and display dimensions through
documented mappings, not an arbitrary global pixel-difference percentage.
Dynamic object and scoreboard comparisons must identify the source presentation
generation, not merely choose visually similar frames.

For sound, PSG event order and callback assignment are exact simulation checks.
Paula waveform samples need not equal a PSG emulator's WAV. Compare mapped tone
frequencies, mute/envelope sequence and onset/duration against the source event
schedule and measured Paula period/sample-rate quantization. Define attenuation,
waveform, stereo and any noise differences explicitly before accepting them;
unexplained differences remain open. No numerical audio tolerance is approved
by this specification without measurement.

For timing, the port must preserve source callback order and measured source
cadence independently of PAL presentation. Record scheduling lateness and sound
continuity through each regime, require zero visible-line presentation commits,
and inspect the complete-match display for missing/corrupted frames. Independent
WinUAE verification remains a separate target-hardware gate. Presentation P1-P3
are not passed by the accelerated simulation harness.

## Iteration order and completion checklist

1. Generalize the current exact capture beyond its hard-coded first-round end
   and supported callback addresses. Read the source result/restart path and
   enumerate any additional callback/main-thread regimes before changing it.
2. Discover and freeze R1's result/restart input sequence; capture the full R1
   twice, validate continuity and verify its existing prefix unchanged.
3. Calibrate two-player controls and mode ownership; develop/freeze R2's input
   schedule, capture twice and verify actual outcomes.
4. Populate the behaviour coverage manifest from real intervals. Obtain only
   the missing F1-F5 cases; extend the runner for their starting-state/entropy
   needs without changing the expected source records.
5. Capture P1-P3 source checkpoints and media. Document their matching rules and
   measured target differences when native presentation is tested.
6. Run the actual port against every frozen simulation case. Preserve failures
   with first-divergence evidence until implementation fixes them.

The source dataset is complete when R1 and R2 reach their stated restart/serve
stop guards, repeat identically, satisfy the fixture contract, and every required
behaviour has either a real replay interval or an accepted focused reference.
All P1-P3 source artifacts and event/time associations must be present, and all
remaining ambiguities must have explicit, executable follow-up tasks rather
than unnamed TODOs. The dataset may be complete while port comparisons fail.

The port suite is complete only when those simulations pass and the separate
presentation/hardware criteria pass. Neither source completeness nor passing
selected cases establishes the other.
