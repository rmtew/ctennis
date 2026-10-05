# Native checks

Run the host checks without a ROM, source captures or emulator:

```sh
python -m unittest discover -s tests/unit -q
python scripts/native_assets.py
```

For native checks, install the tools in `tools.lock.json`. Set the Copperline
path and a legitimate external Kickstart 1.3 path in `config.local.ini`.
The standard target is PAL A500, 68000, OCS, 512 KB chip RAM and no expansion.
Some checks also cover NTSC or the stated slow-RAM configuration.

Run the finite gate from a clean, committed checkout. Use empty output directories
and the versioned native inputs. Keep original-platform inputs outside the checkout.

```sh
RUST_LOG=info python scripts/native_acceptance.py
```

The gate runs the checks below in sequence. It also packages the game twice and
checks the embedded executable and artifact hashes. A failure stops the gate.
Copperline is the maintained emulator target. These results do not establish
WinUAE or physical-hardware coverage.

| Entry point | Protection |
|---|---|
| `build_native_adf.py --self-test` | Repeatable packaging and release executable bytes. |
| `run_enhanced_menu_tests.py --adf` | Cold load, menu, help, pause and lifecycle through physical input. |
| `run_native_inputs.py` | Raw input packets and key aliases through the native sampler. |
| `run_video_standard_tests.py` | Actual startup selector for all 256 OS frequency-byte values. |
| `run_startup_publication_tests.py` | Exact release cold boot in PAL/NTSC with zero or 512 KB slow RAM. |
| `run_native_video_clock_tests.py` | PAL/NTSC callback intervals measured in colour clocks. |
| `run_sprite_dma_tests.py --self-test` | Three-bank sprite and HUD DMA, startup phases and negative controls. The gate also uses `--ntsc`. |
| `run_native_scoreboard_tests.py --self-test` | Complete scoreboard pixels and HUD bank bytes. |
| `run_native_contracts.py --case=...` | Scoring, status and audio fixtures. The gate lists all cases and required negative controls. |
| `run_celebration_tests.py --winner=blue` | Winner celebration. The gate covers both winners, both ends and a negative control. |
| `run_demo_match_tests.py` | The frozen 10,958-tick trajectory. The gate also uses `--takeover`. |
| `run_attract_cycle_tests.py` | Two uninterrupted attract cycles and title return. |
| `run_enhanced_feedback_tests.py --mode=one` | Visible game-win labels and tally progression. The gate covers both modes. |
| `run_ordinary_round_tests.py --mode=one --match --cadence --adf` | Uninterrupted lifecycle, cadence and bank publication. The gate also covers two-player mode, stale-bank rejection and restart audio/input. |
| `run_native_setup_tests.py --self-test` | UI construction, raw callback deadlines and complete elapsed-time accounting. |
| `native_metrics.py --require-runtime` | Required resource-report coverage from existing receipts. |

Paths in this table are relative to `scripts/`. The command list in
`native_acceptance.py` defines the complete gate. Use focused checks for a bounded
change. Host checks alone do not establish native acceptance.

Native fixtures initialize state once through product initialization. They then
use the actual dispatcher and controls. Do not inject intermediate expected state
or generate expected pixels from the renderer under test. A fixture result is
not evidence of an ordinary complete match.

Scoring fixtures preserve the accepted tuples: deuce 5/5, advantage 4/6 and return
to deuce 5/5. Winning advantage awards the correct logical player. A player
completes the match by winning their sixth game. Status values 2–6 remain visible for 31 ticks with the
saturating 224–255 clock. The hit pitch is 1688 from octave 2, transpose 0, key 0.
The envelope starts at the calibrated hardware levels 64/51.

Raster checks use immutable native assets and named fields. The scoreboard checks
cover all 28 mode/end/variant fixtures, all three Copper banks and each complete
3,072-byte HUD strip. They check six WIN words, remaining grey rows, earned
Blue/Red rows, closed white frames and the selected point/advantage masks.
Negative controls corrupt the WIN stamp, status repair or bank selection.
Ordinary game awards also check the full visible panel.

Scoreboard role labels start at native y=34. Score cells start at y=48, with
borders at y=43, 68 and 123. The point cells have four blank native pixels to
each border. A single zero leaves the tens cell blank. Checks cover the two-row
gap below A/B and both HUMAN/AI and HUMAN/HUMAN labels.

Status fixtures check loaded hunks, duration, completed bank publication and all
1,536 pixels in each visible or expired glyph crop. The 96×8 native region at
(80, 96) uses four committed 256-byte planes and the reviewed OCS palette.
Checks include DOUBLE FAULT and every white frame pixel. A wrong-bank control
must fail the pixel check even when scalar state is correct.

Cadence checks compare COP1LC at COPJMP1 with the latest completed bank and epoch.
The court publication interval starts at line 253; the footer ends at line 251.
The accepted PAL interval is 11,838 + 14,906/65,536 E-clock ticks. Checks retain
the timer origin, fractional quantization and deadline bounds. NTSC uses its
specified E-clock frequency. Host seconds do not determine either result.

DMA checks cover six startup phases, both players, serve/pause/title transitions
and alternating PAL field lengths. CPU writes reconstruct frozen sprite banks
because the pinned sidecar's data values are unreliable. Checks still require
correct DMA addresses, registers, rows, header progression and live bank bytes.
HUD checks compare every fetched word across 192 court rows and four planes,
including static-row restoration. Writes must target only the building strip.

Setup checks cover menu, help, controls, credits, repeated navigation, 15 seconds
of idle, start, pause, title return and restart. They compare scanout with the
committed font and layout. Every raw callback must meet its deadline. A compiled
lost-wrap mask must lose exactly 327,680 colour clocks and fail accounting.
Delayed construction must fail its deadline while the normal 32-bit timer still
accounts for the full wrap. Neither control creates a setup exemption.

Restart checks inspect completed native updates. They check old-score cleanup,
opposite-mode reselection, early release/repress packets and held-player exclusion.
Audio checks cover title return, restart cleanup and the next serve. The latch
negative control skips an actual retirement instruction and must fail.

For a separate startup measurement, run:

```sh
python scripts/run_native_square_startup.py --self-test
```

This check compares all six generated point masks, the WIN mask and three initial
HUD strips with independent expectations. It measures construction before the
simulation clock starts. A wrong advantage position must fail. The masks in
`docs/sprites/square-led-contract.json` came from the selected preview before
implementation. Do not regenerate them from build or test output.

After a normal build, the optional HUD cost probe is:

```sh
python scripts/measure_native_hud_cost.py /absolute/path/to/checkout
```

It compiles one startup fixture per PAL/NTSC and end orientation. It then observes
native callbacks without more state injection. Results include dirty-field masks
and deadline misses. This measurement does not replace the acceptance gate.
See [measurement definitions](../docs/metrics/README.md#comparison-measurements).

Receipts under ignored `build/tests` bind the commit, inputs, tools, target and
checked extent. A failed or interrupted rerun replaces an older pass.
`python scripts/progress.py` reads these receipts without running native checks.
Missing, stale, partial or wrong-subject results cannot establish acceptance.

Builds regenerate static resource sizes without emulation. Existing native checks
collect runtime metrics. Follow [the metric workflow](../docs/metrics/README.md)
to review and record results. See [current limits](../docs/limits.md) for claims
that remain unmeasured. Keep the [frozen trajectory](fixtures/native-demo/README.md)
bound to its recording and seed.

The optional [bounded match-core proof](../docs/match-core-proof.md) compares the
same 68000 routines in native and isolated execution. It is separate from the
acceptance gate and does not certify a complete deterministic match core.
