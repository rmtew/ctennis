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
