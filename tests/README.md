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
