# CT-04 maintained native gameplay evidence

Verified 2026-10-01 UTC on PAL A500 / OCS / 68000 / 512 KB chip /
zero slow and fast RAM / Kickstart 1.3, with `RUST_LOG=info`.
Tools: vasm 1.9d, Copperline 1.0.0-rc.1 and MAME 0.289. Private inputs,
original captures and generated binaries remain ignored local inputs.

## Product boundary

The ordinary application and `PRODUCT_REPLAY` dispatcher call
`amiga/game/gameplay.s:game_play_tick`. Native player records and ball vectors
have a separate named layout in `gameplay_state.i`. Maintained routines cover
serve setup/wait/launch/handoff, human/AI contact and shot choice, ball flight,
court/net reflection, movement limits, deterministic PRNG and AI intercept/
tracking. Native arithmetic uses normal 68000 values; it does not assemble
emulated Z80 registers or flags. The least-root calculation retains its carry
in ordinary long arithmetic and repairs the resumed launch.

Reference generation excludes the replaced routines from the native build,
while `--subject translated` still compiles the original diagnostic paths.
Native module hash protection includes the state `.i` file. Tests select the
actual dispatcher, supply initial source state once plus inputs/recorded
entropy, and compare actual outcomes; callback kinds and intermediate source
writes do not drive the product. Ordinary entropy uses the existing native
refresh adapter; deterministic comparisons consume recorded source decisions.

`gameplay_adapter.s` imports/exports at one explicit boundary. Score/round
lifecycle, previous-update animation/sprite/VDP presentation and PSG/Paula
stream interpretation remain temporary CT-05/07/08 debt. This is not the final
adapter-free runtime. Only obsolete arithmetic scratch C067–C06A is omitted
from maintained comparisons; all 250 remaining selected bytes are exact at
all boundaries, including AI targets, ball vectors and point/owner state.
Translated diagnostics retain their original scratch assertions.

## Executed acceptance

Run the following from the repository root with `RUST_LOG=info`:

- `python scripts/build_native_game.py`: ordinary title build succeeded.
- `python scripts/run_regression_tests.py --case serve`: 200/200 updates,
  40 ordered PSG bytes matched, two boundaries per update.
- `python scripts/run_regression_tests.py --case resumed-play-phase --self-test`:
  200/200 matched. Incrementing the native root fails at update 96, frame 2864,
  launch byte C057 expected 199 / actual 200. Restoring source rebuilds the
  identical executable and passes all 200 updates again.
- `python scripts/run_regression_tests.py --case two-player-rally`:
  1,390/1,390 matched, including six alternating returns by both players and
  player-1 point award at update 1,050 (score 2–0 to 3–0). The original marker
  validator identifies the rally; the native records compare at every update.
- `python scripts/run_regression_tests.py --case one-player-upper-resumed-serve-complete-phase`:
  50/50 matched from the existing reachable upper serve start, including launch,
  receiver handoff and completed serve state. This is a local start.
- Existing `MOVEMENT_CASES` excluding four continuous lower-receiver prefixes,
  plus their four existing `MOVEMENT_PHASES`, all with `--subject maintained`:
  18 complete windows / 11,078 matched updates. Both serving rows, both
  receiving ends and both rally ends reach limits, hold and reverse. Continuous
  lower-receiver prefixes still depend on unimplemented round transitions.
- Existing `contact-upper-action-before`, `-at`, `-after`, with
  `--subject maintained`: all 722/722 each matched. These protect shot-choice
  timing, not new geometric hit/miss threshold coverage.
- `python scripts/run_physical_input_tests.py --all --ownership`: all 561
  calibration updates and 105 exchanged-end updates passed, comparing eight
  actual player outcomes and input/ownership edges at each callback.
- `python scripts/run_mode_selection_tests.py --case p1-accept-one-player` and
  `--case p1-accept-two-player`: both passed ordinary title/selection/hold/release,
  complete accepted viewport at the retained ball pose, actual movement/reverse/
  release and physical serve. They are ordinary starts with native entropy.
- `python scripts/run_amiga_live_serve_probe.py`: passed the existing live state,
  flight-slot, point-field pixel change and audible serve-tone checks. This
  older probe starts in an explicitly captured diagnostic phase and retains its
  weak historical left check; ordinary movement above supplies the stronger
  control evidence.

The 25 focused replay reports total 15,084 matched updates, not 25 independent
product capabilities. Raw translated serve still passes; raw translated resumed
play still fails at update 96 / C057. Only the migrated native resumed case is
removed from `known-failures.json`; 33 unrelated known failures remain recorded.
No full 99-case campaign, continuous full match, cadence/memory peak measurement,
ADF boot or independent-emulator/hardware validation was run for CT-04.

## Ordinary display prerequisite

The faster native path exposed a right-point field artifact at logical pixel
(210,40) in both ordinary mode checks. The same assets passed with translated
gameplay. Debug captures showed matching sprite records/buffer and all 224
correct Copper pointers, isolating a mid-scanline fetch boundary. Moving the
right-point pointer switch from wait A1/byte 28 to wait 99/byte 26 completes it
before the x=208 fetch. Both unchanged whole-viewport expectations now pass;
the existing live scored-point probe also passes. This is a narrow display
prerequisite, not completion of CT-07.

## Local artifacts and limits

`build/ct04/evidence/acceptance-summary.json` mechanically records the 25
subjects, executable/reference hashes, full executed/matched extent and native
module hashes. Individual reports/logs are under `build/tests/` and
`build/ct04/evidence/`; restored original captures were validated through
existing `capture_test_reference.py` recipes with identical repeats.
Ordinary executable SHA-256:
`ec2fa1aef64f309008801d4c23e446671965691af76d0663f4e8a4844026f1e0`
(234,252 file bytes, **not** a RAM-usage measurement).

These fresh executions were checked against the current module hashes, but
legacy reports do not yet include complete runner/build/tool/configuration
freshness provenance. The separately authorized follow-on will invalidate
older/unverified reports and track interrupted invocations; this document does
not claim that mechanism is already implemented. CT-04 is ready for source and
runtime evidence review. Do not merge it or begin CT-05 without authorization.
