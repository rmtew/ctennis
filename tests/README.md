# Finite native acceptance

Host checks need no ROM, source captures or emulator:

```sh
python -m unittest discover -s tests/unit -q
python scripts/native_assets.py
```

Configure only the pinned Copperline and legitimate external Kickstart1.3 for the
finite gate. Target: PAL A500/68000/OCS/512KB chip/zero slow/fast RAM. Copperline is
accepted; no additional WinUAE gate. Run from a fresh checkout with empty outputs,
versioned native inputs and pinned tools, and no original inputs in its active
filesystem:

```sh
RUST_LOG=info python scripts/native_acceptance.py
```

The gate packages twice, checks embedded executable/hash equality, runs host
contracts, ordinary menu/pause/cold-load and physical raw input checks, native
scoring/status/audio fixtures, both-mode uninterrupted lifecycle/cadence,
canonical10958-tick demo/takeover, visible tally progression, restart audio and
early-release latch behavior. The delayed real stale-bank control and compiled
field/pitch/envelope controls must be rejected. Native fixtures initialize once
through product initialization and thereafter use the actual dispatcher.
They are labeled local fixtures, never ordinary complete-play evidence.

Scoring contract: deuce5/5, advantage4/6 and return-deuce5/5 preserve the independently
accepted tuples. Winning advantage awards the correct logical player; sixth game
sets match completion. Status2–5 remain visible31ticks from appearance to expiry
with the saturating224→255 clock. These facts transfer retained protection without
source memory or snapshots. Native hit pitch1688 comes from the approved octave2,
transpose0,key0 period entry; envelope starts at calibrated64/51 hardware levels.

Render expectations use immutable native assets and named fields, not expected
images made by the runtime renderer. Tally crops count actual gold scanout pixels
against the versioned bank mask (one mark23 logical/46 doubled pixels). Cadence
observes actual COP1LC at COPJMP1 against the latest completed prepared bank/epoch.
Court publication precedes sprite header DMA at line25 or uses blank>=252; the
footer extends through251. Accepted clock is11838+14906/65536 PAL E-clock ticks,
with retained origin, fractional quantization and deadline bounds.

Receipts under ignored build/tests record exact head/inputs/tools/target and
extent. Failed/interrupted latest runs supersede older passes. `progress.py`
reads these receipts without running tests; missing/stale/partial/wrong-subject
results cannot certify acceptance. See risks for unmeasured claims. Historical
aggregate failures are available in Git history, not an active gate or archive.
