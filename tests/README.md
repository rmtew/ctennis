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
sets match completion. Status2–6 remain visible31ticks from appearance to expiry
with the saturating224→255 clock. These facts transfer retained protection without
source memory or snapshots. Native hit pitch1688 comes from the approved octave2,
transpose0,key0 period entry; envelope starts at calibrated64/51 hardware levels.

Render expectations use immutable native assets and named fields, not expected
images made by the runtime renderer. Complete side-panel crops verify six compact
WIN words, solid grey remaining rows, Blue/Red earned rows, the stacked closed white frames
and the selected square LED points/advantage. All0–6 variants, both modes/ends and all three
physical Copper banks are checked by one-time native fixtures, with compiled
wrong WIN stamp, missing status/WIN repair and wrong-building-bank controls. Ordinary awards also verify actual full-panel pixels. Cadence
observes actual COP1LC at COPJMP1 against the latest completed prepared bank/epoch.
Court publication uses the conservative retired bottom interval starting at253; the
footer extends through251. Accepted clock is11838+14906/65536 PAL E-clock ticks,
with retained origin, fractional quantization and deadline bounds.

Receipts under ignored build/tests record exact head/inputs/tools/target and
extent. Failed/interrupted latest runs supersede older passes. `progress.py`
reads these receipts without running tests; missing/stale/partial/wrong-subject
results cannot certify acceptance. See risks for unmeasured claims. Historical
aggregate failures are available in Git history, not an active gate or archive.

The CT11 focused observer uses the native update entry to inspect the preceding
completed update, including enhanced title/menu callbacks. It verifies old-score
cleanup, opposite-mode reselection, exact early release/repress packets and
independent held-player exclusion; emitted audio is checked at returned-title
reset, enhanced restart cleanup and the actual fresh serve (no legacy intro).
`--self-test` compiles an actual skipped latch-retirement instruction and requires
the retained release assertion to catch it.

Status2–6 fixtures verify loaded hunks, scalar duration, actual completed
publication/bank association, and full1536-pixel visible/expired glyph crops, including DOUBLE FAULT.
The 96x8 region at native80,0 is decoded independently from the four committed
256-byte status planes and reviewed CT12 OCS palette. A wrong native status-bank
pointer control leaves scalars intact but must fail pixels. Fixtures explicitly
select the enhanced Copper layout, matching the maintained application.

`run_native_setup_tests.py --self-test` retains the continuous timer origin and
requires every raw callback to meet the existing deadline. It measures all
menu/help/controls/credits construction, repeated navigation,15-second idle and start/pause/return/restart,
checks representative actual scanout against the committed font and retained
layout, and independently compares native elapsed additions to wall CCK.
The diagnostic phase proposal is retained for historical comparison; it grants
no exemption. A compiled lost-wrap mask must lose exactly327680CCK and fail
accounting; a separate delayed construction must fail raw deadlines while the
unmodified32-bit timer accounts for the complete wrap. Both restore the normal
executable before final acceptance. See the follow-on report in
[verification issues](../docs/ct11/verification-issues.md).

Resource reporting is part of the existing checks and the finite gate. Builds
regenerate static sizes without emulation; record the compact accepted JSON and
readable summary alongside reviewed changes. For docs-only identical-product
reuse and the affected four-check refresh, see
[resource report workflow](../docs/metrics/README.md). Missing/stale/incomplete
metrics do not establish runtime coverage or a fresh green result.
Six unique square LED tiles, the retained-font WIN mask and three fixed
scene-owned HUD strips are constructed once by the native startup entry. Run
`python scripts/run_native_square_startup.py --self-test` to compare every byte
of all six generated point masks and the WIN mask with independent expectations,
and all three initialized strips with the unchanged court background, measure
construction time before the simulation
clock starts, and reject a compiled wrong advantage position. The masks in
`docs/sprites/square-led-contract.json` were sampled from the user-selected
preview before native implementation; tests/build must never regenerate them.
`run_native_scoreboard_tests.py --self-test` additionally verifies all 3,072 bytes of each completed HUD bank, status overlap and actual complete panel scanout in all28 mode/end/variant fixtures.

The requested stacked-frame layout uses role labels at native y34, score cells at
y48, and borders at y43/68/123. The point cells have four native blank pixels to
every border. Score glyphs retain their selected shapes and fixed tens/units positions within
the cells; a single0 has a blank tens cell. The scoreboard fixtures also check the two-row gap below A/B and both
HUMAN/AI and HUMAN/HUMAN label selections. Status raster checks now verify every
white frame pixel while the full-width status strips are active.

The finite gate also verifies three-bank sprite DMA in PAL and NTSC across six startup phases, both players/serve/pause/title transitions and alternating PAL field lengths, with native stale-bank/unknown-list/malformed-height controls. CPU MMIO reconstructs frozen banks independently of the pinned sidecar's unreliable data values; actual DMA addresses/registers/rows/header+4 progression and live whole-bank samples remain strict. Native startup selects the PAL or NTSC CIA interval once. Every observed clock-test callback is checked in CCK, applying the documented standard's E-clock frequency, independent of Copperline's PAL-derived host seconds.

Direct HUD DMA validation checks every fetched word across all 192 court rows and
four planes against the selected scene's fixed region pointers, including static
row restoration. CPU writes must target only the building strip, never front or
ready; independent live reads compare frozen strip bytes. Existing PAL/NTSC
publication and negative-control assertions remain enabled.

After the ordinary build has generated the matching native inputs, the bounded
supplementary cost probe is
`python scripts/measure_native_hud_cost.py /absolute/path/to/checkout`. It compiles
one startup-only fixture for each PAL/NTSC/end orientation, then observes actual
native callbacks without state injection. It reads the initialized native cadence,
reports dirty-field masks and deadline misses explicitly, and is a measurement,
not a replacement acceptance gate. Before/after receipts and limits are summarized
in [direct-hud-comparison.md](../docs/metrics/direct-hud-comparison.md).

Startup reads Kickstart1.3 VBlankFrequency once and selects conservative OCS
PAL/NTSC bounds. Actual-assembly tests cover all256 byte values; exact-release
cold-start checks cover both standards and zero/512KB slow RAM. See
[startup video standard selection](../docs/ct11/field-measurement.md).
