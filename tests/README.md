# 68000 simulation regression suite

[Original-game reference specification](reference-spec.md) defines the two
primary continuous replays, required observations and remaining coverage gaps.

Run from the repository root:

```powershell
python scripts/run_regression_tests.py
```

The command rebuilds the byte-exact annotated source and shared 68000 gameplay
routines, assembles the harness, runs Copperline, and compares against the saved
MAME oracle. It exits **0** for a match, **1** for a behaviour difference, or **2**
for a setup/build/run error. Results and native logs are in `build/tests/`.
A difference identifies the first callback, boundary, named field, expected
value and actual value. Run `--self-test` to additionally build a temporary
one-pixel ball-position mutation and require the suite to detect it. The
mutated source and executable are removed afterwards.

## Local prerequisites and reference capture

Use the existing `config.local.ini`, supplied cartridge and Kickstart 1.3,
local vasm, Copperline, and ROM round-trip tools. The first reference capture
also requires the existing MAME 0.289 installation and configured cartridge
archive under `build/mame/roms`. Python uses only the standard library for this
suite.

```powershell
python scripts/capture_test_reference.py
```

This explicitly runs MAME SC-3000 twice and requires byte-identical captures.
It saves `tests/reference/serve.json`. That directory ignores reference data
because the initial RAM and audio records contain ROM-derived bytes. Ordinary
regression runs never invoke MAME or rewrite the expected fixture. Re-capture
deliberately when extending a reference case, and review resulting differences.

## What the first case establishes

The harness initializes RAM once, finishes the initial source IRQ tail, then
carries RAM forward through 200 consecutive updates. It invokes the same
generated `player-frame-routines.s` and hand-written `translated_audio_tick.s`
included by the live executable. It supplies normalized input bytes at the
source input-reader boundary; it does not synthesize another game in Python.

The serve fixture covers source frames 1300-1499: serve animation, launch,
flight, a return and a point award. It compares 254 state bytes at both the
post-gameplay/pre-counter-write boundary and after the IRQ tail, plus all 40
ordered PSG writes. MAME captures the latter RAM observation at frame end;
the bounded active-play case has one callback per source frame, with no
intervening main-thread state changes in the compared fields. The first
initial tail is checked too. Callback pointer bytes C000-C001 are excluded
because they are source code addresses rather than portable game state.

The case definition records the input schedule. Source PRNG state comes from
the initial capture. Native refresh-register sign input is fixed to zero by
the current shared macros; this deterministic source capture agrees with it
for this case. This is not a general solution for random choices in longer
games. The runner rejects cases requesting a different refresh input until
that adapter is implemented.

The target is PAL A500, OCS, 68000, 512 KB chip RAM, no slow/fast RAM,
Kickstart 1.3. Execution does not wait for presentation or source wall-clock
cadence. Display writes are intercepted, and PSG bytes are recorded without
Paula playback. This suite checks simulation and sound-event behaviour;
existing live probes remain responsible for actual joystick reads, native
display, audio DMA and real-time cadence. It does not cover title boot,
between-game transitions, match completion or arbitrary starting states.

`tests/state-fields.json` names byte fields using the source symbols and known
record layouts. Unassigned bytes retain explicit address-based names rather
than invented meanings. Wider trajectory values retain their byte positions
to preserve exact arithmetic evidence.

## First game, pause and resumed serve reference

Capture or validate the longer independent source record:

```powershell
python scripts/capture_test_reference.py --case round-transition
python scripts/capture_test_reference.py --case round-transition --verify-only
python scripts/run_regression_tests.py --case round-transition --reference-only
```

Capture runs MAME twice from reset and requires identical raw event streams.
The frozen local fixture is `tests/reference/round-transition.json`; raw streams,
logs and capture report are under `build/tests/round-reference-capture/`.
`--reference-only` loads and validates that fixture and materializes input,
initial RAM, refresh values and harness configuration. It does not run the port
or claim a passing comparison.

This fixture contains 1,566 updates after the initial callback: 1,430 gameplay
and 136 tail-only callbacks, 285 PSG bytes, eight consumed refresh decisions,
and 50 between-callback RAM writes. The first game award is update 1204; the
pause begins at 1333; gameplay resumes at 1469; the resumed serve first advances
in flight at 1566. Source frame 2631 contains two callbacks. State is observed
at exact callback entry, common-tail entry and return, not at frame end.

The capture uses [MAME debugger actions](https://docs.mamedev.org/luascript/ref-debugger.html)
that print observations and immediately resume, with `-debugger none` and no
interactive window. It neither steps the CPU nor changes source inputs/random
state beyond the documented physical input script. The whole retained pre-tail
RAM prefix, including the initial callback, matches all 1,567 checkpoints in the
older non-debugger source capture.

Schema version 2 retains `initial_callback`, per-update entry/pre-tail/post-tail
RAM, callback kind and source frames, input-reader return values, consumed
refresh values, ordered PSG events, and an ordered `timeline`. Each update's
`before_events` records intervening routine-entry markers, RAM writes (old/new
value and source PC), and sound events. Validation reconstructs source entry
RAM solely to verify capture continuity; **these writes are never injected
into the port**. The native harness receives initial state, input and recorded
entropy, then carries its own state forward.

Run the actual comparison:

```powershell
python scripts/run_regression_tests.py --case round-transition
```

The present port matches 1,332 updates, including 250 PSG bytes, then returns
exit 1 at callback 1333: the original main thread has requested display/round
setup before the first tail-only callback, and the port has not. The full first
difference and preceding source actions are in
`build/tests/round-transition-report.json`. This is the known unimplemented
boundary, not a weakened or passing reference. The default short serve test
continues to pass. A complete match/restart, the complementary two-player
record, and source presentation snapshots remain future reference work.

## Complete one-player source replay

```powershell
python scripts/capture_test_reference.py --case one-player-match
python scripts/capture_test_reference.py --case one-player-match --verify-only
python scripts/run_regression_tests.py --case one-player-match
```

The capture runs MAME twice with a frozen physical input schedule, requires
identical raw recordings and exact agreement with the existing round prefix,
and saves the private reference through the first advancing restarted serve.
It carries source state across all 13,378 updates, including match/title resets.
The actual native replay currently returns exit 1 at callback-entry 1333:
deferred display setup request expected 129, actual 1. The first 1,332 updates
and 250 PSG bytes agree. This is the known unimplemented round transition;
later native behaviour is not validated by that matching prefix.

## Registered suite and known failures

```powershell
python scripts/run_test_suite.py --baseline-check --self-test
```

This runs all currently registered native cases, checks exact first-divergence
signatures against `tests/known-failures.json`, verifies gameplay mutation
detection, and rejects changed signatures and unexpected passes. Strict mode
(without `--baseline-check`) also rejects known red. Tool errors are never
classified as known red. Full reports and runner logs are in `build/tests/`;
`suite-report.json` lists results and missing requirements.

The aggregate runner is an incomplete-suite checkpoint: it currently exits 2
in both modes because R2, meaningful gap inventory/cases, phase-specific later
comparisons and P1-P3 references/adapters remain missing. A matching known-red
baseline does not make missing requirements pass.

## Independent phase diagnostics

Run `python scripts/phase_reference.py` to derive four retained phase fixtures
from the twice-identical full one-player source reference. Each fixture is
validated against its exact parent bytes and tracked case recipe on every run;
changed snapshots or stale parent hashes are rejected. The original continuous
replay stays registered. These are reachable source starts, not evidence that
the port reached those starts correctly.

The aggregate runner also executes `round-tail-phase`, `resumed-play-phase`,
`match-tail-phase` and `restart-play-phase`. Individual cases use the usual
`python scripts/run_regression_tests.py --case <name>` command. Phase reports
show both local and original source update IDs. Initialization runs the captured
initial callback's common tail; subsequent updates carry native state without
injecting source main-thread writes.

Current later-regime results: restarted play now matches 50 callbacks through
handoff and animation release, including 20 PSG events. Match-tail now spans
448 callbacks through menu selection: 192 match before the missing title/menu
display request differs at local 193. The previous 40-callback prefix still
matches. Round-tail spans 136 callbacks through reset/resume and retains its
first failure at local 1. Resumed play retains the launch failure at local 96.
Six full award-to-completed-serve phases cover both ends and both modes; separate
post-reset starts protect working serves beyond known transition failures.
See [later-regime evidence](../analysis/later-regime-regression.md) for exact
boundaries, failures and source-prefix preservation. These are diagnostic
comparisons; P1/P2/P3 hardware acceptance remains separate.

The resumed-launch root cause is confirmed: triangular-root register-pair
assembly clobbers the carry input before SUBX. For product $1040, source root
64 becomes native 65. Run `python scripts/diagnose_phase_launch.py` to reproduce
the baseline difference, test temporary carry preservation against all 200
independent phase updates, and restore the unmodified generated source. This
is a diagnostic; the registered baseline intentionally stays known red until
a reviewed implementation change. Earlier root-cause-pending text is superseded.

Two-player input mapping is independently captured with `python scripts/capture_input_map.py`; see analysis/two-player-input-map.md. The private record retains exact callbacks and physical fields. Calibration does not count as the required full varied R2 match.

## Varied two-player full match

Reproduce with `python scripts/capture_test_reference.py --case two-player-match`
and validate the saved fixture with the same command plus `--verify-only`.
`python scripts/run_regression_tests.py --case two-player-match` executes the
actual native replay. The frozen schedule includes individual and simultaneous
movement, action changes, a full 4-6 match, result/reselection and restarted serve.
The 27,037-update reference was captured twice identically. It contains 5,414
PSG bytes, no refresh reads, and 1,203 between-callback RAM writes. Optional
source entry markers prove 11 lower and 23 upper successful contact launches.
Run `python scripts/inventory_match_references.py` for indexed scoring, contact,
clock and refresh observations in `build/tests/match-inventory.json`.

The native replay matches 2,535 updates/350 PSG bytes and first diverges at
callback-entry 2536 (frame 3834), display setup request expected 129 actual 1:
the known unimplemented round transition. Full report is
`build/tests/two-player-match-report.json`. The harness uses a long input index
and supports up to 65,535 updates, with a 360-second process watchdog for long
runs. Source callback count and frame count remain distinct.

R2 is still missing a rally containing successful returns by both players.
The 34 observed returns occur in separate point intervals. This remains explicit
missing coverage in the aggregate runner. The saved continuous match is retained
while normal-return discovery and focused cases address the gap; no intended
rally is claimed as observed.

## Deuce and advantage regression cases

The retained R2 includes the complete natural sequence: deuce at source update
9134, advantage 9588, deuce again 9869, advantage again 10328, then game award
10782. The source game counts change from 1-2 to 2-2. No score state is injected.
`python scripts/phase_reference.py` materializes five four-update boundary
fixtures plus `deuce-sequence-phase`, a continuous 1,649-update replay initialized
once before the first deuce transition. Tracked source score/game checkpoints
are checked against the parent; an altered scoring checkpoint is rejected.

The actual native continuous case passes every retained entry/pre-tail/post-tail
state and all 260 PSG bytes. All five boundary cases also pass. They are registered
in the aggregate runner via the phase list. Run individually with
`python scripts/run_regression_tests.py --case deuce-sequence-phase` (or
`deuce-enter-phase`, `advantage-enter-phase`, `advantage-lost-phase`,
`advantage-regained-phase`, `advantage-game-phase`). These diagnose the scoring
sequence beyond the earlier full-match failure; they do not establish upstream
parity, native scoreboard pixels or complete presentation coverage.

## Later timer saturation and audio cadence

Three additional source-derived cases cover shared/status timer boundaries.
`shared-timer-saturation-phase` checks reaching 255 at source update 2183 and
remaining 255 on the following callback; its full native state passes.
`status-timer-saturation-phase` retains the full comparison at source updates
12535-12536 and is known red at initialization: audio countdown expected 1,
actual 2 (RAM offset 131). The source skips audio on alternate callbacks when
its reload value is 2; the native harness and live callback call the interpreter
unconditionally and reload 2. This is an explained cadence defect, not a timer
failure or a setup error.

`status-timer-observation-phase` runs the same native executable/source window
with an explicitly scoped seven-counter observation (C06B-C071). It passes,
including the status timer's 254-to-255 transition. PSG/refresh event checks
remain enabled. Its report declares seven compared RAM bytes; it does not claim
full state or audio parity, and the full-state known-red case stays registered.
All existing cases keep their full 254-byte comparisons. The observation layout
is temporary diagnostic scaffolding subject to the behavioural-test migration.
Timer checkpoints are checked against the independent parent reference and
incorrect checkpoint recipes are rejected.

The matched R1 prefix already observes both refresh-sign outcomes and five
primary counter wraps. The inventory identifies the earlier C06D/C06E/C06F/C071
saturations; the two new windows cover later C06C/C070 saturation. This indexes
clock evidence without duplicating every arbitrary counter value. It does not
complete movement/contact/court or native hardware cadence coverage.

Baseline-check mode now executes known-red continuous cases through their
recorded first-divergence boundary (at least one update for an initialization
failure). The reference is validated in full before selecting that native prefix;
reports distinguish `updates`, `reference_updates` and `full_replay_executed`.
All green cases and independent later-phase cases still run their retained
sequences. A matching prefix without the expected failure is unexpected green
and fails baseline review; it does not promote the full replay to passing.
Strict aggregate mode and individual runs without `--through-update` continue
to execute the complete retained replay. This avoids running an already-diverged
suffix merely to reconfirm its first failure. Full and optimized 17-case runs
verified the same 11 green/six known-red classifications. Required missing
coverage remains failing in both modes.

## Source presentation references and first native graphics case

Capture explicitly with `python scripts/capture_presentation_reference.py`,
then repeat with `--case two-player-match`. Each replay runs twice and must
preserve its frozen callback recording exactly. Retain native RGB bitmap words,
lossless PNGs, contemporaneous RAM/VRAM, actual paired/masked VDP registers and PC.
The verified active crop is (12,12)-(268,204), without interpolation.

Run `python scripts/freeze_presentation_reference.py` to check source hashes,
all required named P1 windows and displayed fields, then retain private media
under `tests/reference/presentation/manifest.json` and its two case directories.
The current record has 263 R1 and 312 R2 rasters plus 122 field observations.
It includes both serve ends, first marked returns by both players, bounce/net/out,
all observed point pairs, all six status messages appearing/disappearing, and
game/match/result/title-return/restart windows. Actual captured pixels remain
the oracle. The test-only VDP decoder cross-checks these pixels and records
which captured hardware states match; it never supplies expected gameplay.

`python scripts/run_presentation_tests.py --case p1-title --self-test` builds
and executes the actual native application, then captures hardware output using
the installed Copperline control bridge. The exact measured native viewport is
(62,16)-(574,208) in a 716x285 capture: two identical horizontal pixels per
source pixel and one vertical pixel. Palette mapping is declared independently
in `tests/cases/presentation.json`; no fuzzy pixel tolerance or GUI scaling is used.
The title case is registered in the one-command suite. Its expected failure is
the existing application starting at the court/serve state instead of the title.

Other native P1 cases, P2/P3, same-rally R2 and remaining behavioural/phase gaps
still prevent suite completion. See [capture details](../analysis/source-presentation-regression.md)
and the authoritative worklog. The old nearly-blank title diagnosis was based
on misleading previews: retained title files contain complete, identical pixels.


## Callback-aligned native sprite placement

`python scripts/run_presentation_tests.py --case p1-upper-player-placement --self-test`
executes the unmodified native application with physical joystick fire held.
The assembler listing supplies relocated code-symbol offsets; a conditional
Copperline breakpoint stops at entry to callback 18, after exactly 17 updates.
All 254 compared simulation bytes must match the frozen source before accepting
this graphics comparison. The checked upper-player rectangle (60,0)-(112,40)
is identical in every retained source frame 1314-1320, and the native beam has
passed those scanlines. No moving-sprite lag is inferred from this invariant.

The current known red is exact pixel (74,12), expected black and observed pink.
The entire pink silhouette is shifted 20 logical pixels left; the application
uses horizontal sprite origin $6c instead of the viewport's $80. This case is
registered alongside the title case. It covers this placement contract only,
not the complete serve/rally presentation requirements.

`python scripts/capture_native_presentation.py` additionally records actual state,
beam positions, front Copper pointer, readiness and screenshots at selected live
callbacks. Those screenshots may contain partial rasters and are diagnostic
observations, not automatically accepted full-frame graphics comparisons.
Its uncontrolled native refresh choice starts differing at an AI target byte
by the later recorded checkpoints; controlled source entropy remains necessary
before using them as deterministic full-state presentation cases.

Latest aggregate baseline/self-test: 19 cases, 11 green and eight exact known red;
six explicit missing requirement groups still cause failure.


## Completed native rasters and source generation

`python scripts/capture_native_presentation.py --recorded-entropy --track-commits --completed-rasters`
uses the existing native replay entropy seam with bits copied directly from
independently captured R1 refresh reads. No Python gameplay model chooses them.
A private source copy changes only the entropy include path; normal production
source remains unchanged. The existing replay define also enables diagnostic
logging, so these observations do not prove ordinary-build timing performance.
Native consumption order/count/value is checked at the actual refresh helper.
Actual game state must still match at each graphics checkpoint.

Commit breakpoints record the actual front Copper pointer, prepared callback,
selected fields and beam position. Completed rasters are captured at physical
beam wrap. Finishing a raster can advance simulation past adjacent requested
callbacks; use separated targets rather than manufacturing a missing state.
Source expected images are selected through independently validated VDP/pixel
associations: the source callback is active and its captured VRAM sprite records
match that callback's recorded entry buffer. Ambiguous associations are errors.
No native visual similarity or arbitrary lag selects the expected frame.

`python scripts/run_presentation_tests.py --case p1-moving-prefix --self-test`
compares seven complete rasters at requested callbacks 17,63,138,168,471,809,1207. It remains
known red for the sprite-origin defect. All subsequent checks stay in its report.
`python scripts/run_presentation_tests.py --case p1-score-status-prefix --self-test`
compares six fields at each of those boundaries, passing 42 exact comparisons.
This protects consecutive point graphics through the first game tally and
IN status appearance/expiry along one continuous live history; it does not complete other score/status variants,
upper serve, all rally/outcomes, later transitions or P2/P3.

Latest aggregate after extending both generation cases through the first game
tally: 21 cases, 12 green and nine exact known red. The field case has 42 checks;
six explicit missing requirement groups still cause failure.


## Original audio references and first native pitch case

Capture source sound explicitly:

```powershell
python scripts/capture_source_audio_reference.py
python scripts/capture_source_audio_reference.py --case two-player-match
python scripts/freeze_audio_reference.py
```

Each full replay runs twice, preserving the exact parent callback hash while
recording native PCM16 WAVs and precise PSG/frame timestamps. Eighteen named
intervals cover serve, return, point, round, result and restart evidence across
both parents. Files remain private and ignored under tests/reference/audio/.
This is source capture/association evidence; waveform response measurements
and native comparisons for all intervals still remain.

`python scripts/run_audio_tests.py --case p2-first-serve-pitch --self-test`
compares actual Paula registers and captures the native waveform. The first
serve is known red: source tone divisor 213 requires nearest period 1688,
while actual AUD3PER is 1687 because the native ratio approximation is low.
The self-test changes an actual instruction in the private executable and
observes period 1691, then rebuilds and recaptures the unmodified application.
It never modifies product source or saved expected sound. The audio case is
registered in the same one-command suite; this single pitch criterion does
not complete P2. See ../analysis/source-audio-regression.md for evidence and
source/native WAV formats, timing and remaining sound criteria.

Latest aggregate baseline/self-test: 22 cases, 12 green and ten exact known red;
six explicit missing groups still cause failure.


`python scripts/run_audio_tests.py --case p2-first-serve-envelope --self-test`
measures the captured source wave's stable plateau amplitudes and compares all
15 decay steps with actual native volumes. It is known red at callback 39:
nearest source-equivalent volume 3, actual 2. The independent
`--case p2-first-serve-mute` passes at callback 40 with all mapped channels muted.
Both use uninterrupted native gameplay through callback 42; neither hides the
pitch failure or claims full sound-path acceptance. Self-tests alter actual
private executable-table bytes, detect the output changes through the same
comparator, then rebuild/recapture normal outputs.

Latest aggregate baseline/self-test: 24 cases, 13 green and eleven exact known
red; six explicit missing coverage groups still cause failure.
# Coverage inventory

The registered `movement-serve-bounds` case compares 742 consecutive original
callbacks against actual shared 68000 gameplay routines. Reproduce its capture
with `python scripts/capture_test_reference.py --case movement-serve-bounds`;
run `python scripts/run_regression_tests.py --case movement-serve-bounds --self-test`
to verify parity and movement mutation detection. Its source evidence validator
enforces approach, eight held attempts and four reversal attempts for all eight
initial-row limits. Remaining rows and physical native control sampling stay
open. See [the movement evidence](../analysis/movement-regression.md).

`movement-alternate-serve-bounds` adds the alternate initial row after a natural
point/reset: 1,322 continuous callbacks and 50 PSG bytes, with exact equality
to the first 485 R2 callbacks checked as source provenance. Use the same
capture/test commands with that case ID. The combined inventory now reports
only rows 2 and 3 remaining per player. Each case's own remaining-row list
describes that case alone.

`movement-receiver-right-bound` covers the upper receiver row-2 positive X
limit over 1,348 continuous callbacks and 190 PSG bytes. Its optional source
snapshots bracket actual movement; a separate ordinary run must match after
those snapshots are removed. Use the same capture/test commands with that case
ID. Its self-test alters upper X only in the active receiver row. The combined
inventory now lists missing direction/player/row combinations, avoiding closure
of a whole row from one passing limit.

For read-only interval discovery, use
`python scripts/capture_movement_observations.py --case two-player-rally` or
`--case two-player-match`. Both captures must repeat exactly and recover the
previous raw source stream byte-for-byte without the optional observations.
This is source evidence, not a fresh native test run or completed F1 claim.

The companion `movement-receiver-left-bound`, `movement-receiver-up-bound` and
`movement-receiver-down-bound` cases now cover the other upper receiver limits.
Each uses 242 continuous callbacks, 20 PSG bytes, exact natural-prefix equality,
direct source movement snapshots and targeted native boundary-escape mutation
detection. Use the same capture/test commands with these IDs. Upper row two
is complete; lower row two and both players' row-three limits remain open.

`movement-lower-receiver-right-bound` captures the natural later upper serve
through 4,593 callbacks. Its continuous comparison is known red at callback
2536. `movement-lower-receiver-right-phase` independently compares the 24 later
callbacks, passes, and detects a receiver-boundary mutation. Capture the parent
with the usual capture command, run `python scripts/phase_reference.py`, then
run either registered case with the ordinary regression command. The phase
checks its source parent/recipe on every invocation and does not claim upstream
continuous parity.

The lower-receiver left/up/down bound and phase companions use the same
capture/rebuild/test commands. Their native phases pass 26/30/24 callbacks,
each with nine PSG bytes; the continuous parents independently reproduce the
existing callback-2536 failure. Both receiver rows are complete. Eight movement
combinations remain, covering row three for both players.

`python scripts/inventory_match_references.py` validates both source match
fixtures and every registered source-derived phase. It writes the ignored
`build/tests/coverage-inventory.json` with reference hashes, observed returns,
counter boundaries, refresh bits and exact phase callback intervals. Native
results in this inventory are explicitly the last available reports; use the
aggregate command for fresh verification.

[`coverage-backlog.json`](coverage-backlog.json) defines the open requirement
groups and their concrete next tasks. The aggregate report includes this same
backlog. Captured observations and short passing phases do not close broader
requirements automatically. The final implementation remains maintained native
Amiga code; raw source-state checks are temporary diagnostics, to be replaced
only after equivalent behavioural comparisons preserve their coverage.

## Supplementary two-player rally

`two-player-rally` preserves continuous state through six alternating returns
and a point award. Its frozen physical input schedule is captured twice from
reset and the actual native comparison passes all 1,390 callbacks and 290 PSG
bytes. The source validator requires at least four accepted returns by both
players within one completed rally; it rejects one-sided or cross-point counts.
The full R2 match remains unchanged.

```text
python scripts/capture_test_reference.py --case two-player-rally
python scripts/run_regression_tests.py --case two-player-rally --self-test
```

The assembled-code mutation is detected at callback one and removed afterward.
See [rally provenance and limits](../analysis/two-player-rally-regression.md).
The R2-rally requirement moves to completed coverage; five open requirement
groups remain. Historical checkpoints above retain their original counts.

All eight final movement-row bounds have continuous cases:
`movement-{lower,upper}-rally-{up,down,left,right}-bound` (expand one case ID per
command). Capture with `python scripts/capture_test_reference.py --case <case-id>`
and compare with `python scripts/run_regression_tests.py --case <case-id> --self-test`.
Each preserves a natural full-R2 prefix and verifies the actual row at movement
entry/return; no source flags, coordinates or intermediate expected writes are
injected. Their green comparisons complete the 32-combination F1 bounds inventory.
Other focused behaviours and native hardware acceptance remain open.

The bounded `contact-upper-action-before`, `contact-upper-action-at` and
`contact-upper-action-after` cases protect the upper-return trajectory choice
around contact. Capture/test commands use these IDs. `python scripts/contact_reference.py`
validates their source relationship; the aggregate includes that proof and runs
contact-specific mutation detection. See [contact timing evidence](../analysis/contact-timing-regression.md).
This boundary is complete; equivalent onset variants are unnecessary.

## Current suite boundary after later-regime coverage

`python scripts/run_test_suite.py --baseline-check --self-test` classifies
63 cases: 39 green and 24 exact known red, with no unexplained/tool failures.
Four missing requirement groups still make the suite fail: remaining focused
F2/F4/F5 behaviour, P1 graphics, P2 audio and P3 ordinary native execution.
Known-red case counts do not count independent product defects. Complete
later-regime comparisons and source extensions are described in
[later-regime evidence](../analysis/later-regime-regression.md). Earlier count
reports below/above are historical milestones.

## Native upper-serve graphics

Run `python scripts/run_presentation_tests.py --case p1-upper-serve --self-test`.
The independent start is validated against its retained source phase; subsequent
simulation state is carried normally. Three completed upper-court rasters cover
windup and early flight, retaining the known 20-pixel sprite placement error.
An actual assembled sprite-position mutation is detected at all three
checkpoints while simulation state remains identical. This covers a fixed upper
court region, not scoreboard initialization, handoff or continuous round parity.
See [evidence and limits](../analysis/native-upper-serve-graphics.md).

Generation display and native audio cases now use separate capture directories.
Reports record their capture-report paths/hashes; later cases no longer overwrite
earlier screenshot or WAV evidence. Mutations use separate private directories.

Current verified aggregate after this addition: **64 cases, 39 green and 25 exact
known red**, with mutation/signature checks and no unexplained/tool failures.
Four required coverage groups still cause suite failure. Capture-report hashes
for all three generation display cases and all three audio cases, screenshot
existence and native WAV hashes were rechecked after the entire suite completed.
Next: native physical press/hold/release tests for both input paths.

## Native physical input baseline

`python scripts/run_physical_input_tests.py --all --self-test` runs one
continuous native hardware calibration and writes 13 control-window reports.
Use `--case p3-input-p1-left` (or another registered input case) for one report.
The original input-map fixture stays unchanged; its timeline drives actual
Amiga pads at live sampling boundaries. Every case compares one neutral,
24 held and 16 release samples from both readers and normalized control fields.

Pad1 Left/Right/Button1 pass. Its Up/Down/Button2, all six pad2 controls and
simultaneous movement expose existing omissions. Actual sampler mutation is
rejected in every case. The aggregate invokes the batch once, validates all
reports and preserves normal/mutated captures separately. See
[exact input evidence and limits](../analysis/native-physical-input-regression.md).
Game response, side exchange, real-time latency and ordinary cadence/deadlines
remain P3 requirements; these byte diagnostics can migrate to named native
input intents without retaining SG device-reader routines in production.

Latest complete aggregate: **77 cases, 42 green and 35 exact known red**.
Mutation/signature checks pass, with no unexplained/tool failures. Four missing
groups still cause suite failure. Earlier counts are historical milestones.
Next: distinct captured native point/status/mode field comparisons.

## Native widget renderer units

`python scripts/run_widget_tests.py --all --self-test` compares38 selector
values in six field cases through the shared native Copper backend. It prepares
inactive lists, commits in blanking and captures full completed rasters. Thirty-two
contexts use that exact original field/column; six explicitly reuse an identical
opposite-column font. Expected images remain captured original pixels.
Asymmetric inputs and actual zero/adjacent-selector mutations check independence;
all pixels outside field rectangles remain unchanged. Game callbacks are paused
in this unit wrapper, so this does not prove game-driven update/expiry timing.
See [widget evidence](../analysis/native-widget-regression.md).

Latest aggregate: **83 cases,48 green,35 exact known red**, all mutation/signature
checks pass and no unexplained/tool failures. Four missing groups remain.
Next: actual game-driven status appearance/expiry; stop font-bank variants.
