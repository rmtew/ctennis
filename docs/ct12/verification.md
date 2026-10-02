# CT12 verification

Target: PAL A500/68000/OCS,512KB chip,zero slow/fast expansion, legitimate external
Kickstart1.3; pinned Python3.12.14, vasm1.9d, Copperline1.0.0-rc.1 and Pillow12.3.0.
Reproduced assembler SHA2560332feebc562e06bf245c1d60bef3fd7598c464a4be8162429be5e3e3a061e39.
Pinned amitools0.8.1 packages the baseline-rally disk/executable/startup.

Focused implementation checkpoint:

- `python -m unittest discover -s tests/unit -q`:23 tests pass.
- `python scripts/native_assets.py`:115 explicit inputs validated. Imported
  hashes are preserved alongside reviewed intentional revision hashes.
- `RUST_LOG=info python scripts/run_enhanced_menu_tests.py --adf`:69 checks pass;
  actual full mode crop and unchanged lifecycle/pause/restart/controls checks.
- `RUST_LOG=info python scripts/run_native_contracts.py --case=status-6 --self-test`:
  full1536-pixel DOUBLE FAULT and expiry pass; compiled late-field and actual
  status-bank pointer faults are rejected. Scalar timing stays31ticks.
- `RUST_LOG=info python scripts/run_native_contracts.py --case=status-5`: focused
  FAULT scanout and expiry check; latest result remains in ignored build/tests.
- `RUST_LOG=info python scripts/run_enhanced_feedback_tests.py --mode=one`:
  two Red game awards and end exchange pass, actual upper/lower player colour
  pixels and logical tally/win identities checked.

Before screenshots are exact merged43e1118 native scanout. After screenshots
are local CT12 implementation checkpoint scanout with BUILD43e1118 + LOCAL,
not a final packaged revision claim; the title glyph expectation is independently
spelled from font bits. Their captured code has the approved identity/layout
changes. The after-exchange view shows Red below and Blue above after an exchange.
The raw screenshot bank/epoch associations and fault details remain ignored.

Final sequential command: `RUST_LOG=info python scripts/native_acceptance.py`.
It runs deterministic packages twice, host/asset checks, cold ADF menu, physical
inputs, scoring/status/audio contracts, canonical10958 replay and takeover,
Blue/Red feedback at both ends/modes, full ordinary lifecycle/cadence and chip
memory, stale-bank rejection, restart/audio/latch controls, strict UI timing and
compiled lost-wrap/UI-overrun rejection. CT12 adds DOUBLE FAULT including its
pointer-fault control to the finite gate. Final exact accepted commit, command
exit codes and executable/ADF hashes are recorded in ignored build/acceptance
and the draft PR, then appended to this document as a separate evidence commit.
No broad historical campaign or second emulator is asserted.

Limits: pre-Exec chip-pool bootstrap memory is unmeasured; no whole-game original
pixel/audio parity, new ownership or public distribution claim. Music/celebration,
recording/save/seek, rule/difficulty changes and repository rename remain excluded.
