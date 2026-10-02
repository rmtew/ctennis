# CT12 verification

Target: PAL A500/68000/OCS,512KB chip,zero slow/fast expansion, legitimate external
Kickstart1.3; pinned Python 3.12.14, vasm 1.9d, Copperline 1.0.0-rc.1 and Pillow 12.3.0.
Reproduced assembler SHA256 0332feebc562e06bf245c1d60bef3fd7598c464a4be8162429be5e3e3a061e39.
Pinned amitools 0.8.1 packages the baseline-rally disk/executable/startup.

Focused implementation checkpoint:

- `python -m unittest discover -s tests/unit -q`:23 tests pass.
- `python scripts/native_assets.py`:115 explicit inputs validated. Imported
  hashes are preserved alongside reviewed intentional revision hashes.
- `RUST_LOG=info python scripts/run_enhanced_menu_tests.py --adf`:69 checks pass;
  actual full mode crop and unchanged lifecycle/pause/restart/controls checks.
- `RUST_LOG=info python scripts/run_native_contracts.py --case=status-6 --self-test`:
  full 1536-pixel DOUBLE FAULT and expiry pass; compiled late-field and actual
  status-bank pointer faults are rejected. Scalar timing stays31 ticks.
- `RUST_LOG=info python scripts/run_native_contracts.py --case=status-5`: focused
  FAULT scanout and expiry check; latest result remains in ignored build/tests.
- `RUST_LOG=info python scripts/run_enhanced_feedback_tests.py --mode=one`:
  two Red game awards and end exchange pass, actual upper/lower player colour
  pixels and logical tally/win identities checked.

Before screenshots are merged 43e1118 native scanout. Before DOUBLE FAULT is
an isolated native status 6 fixture on that exact product base: only the test
runner's case allow-list was extended; game code/assets were unchanged. After
screenshots are actual accepted ccaffc7 scanout, with that BUILD identifier on
Credits. Status screenshots are one-time local fixtures with native completed
bank/epoch associations; ordinary menu/play/exchange/attract images use physical
product flows. No original cartridge or captures were used. The separate native
mode0 DEMO fixture initializes its native mode flag once before dispatch; normal
attract still uses1 PLAYER header and DEMO footer. An initial supplementary check
mistakenly expected bank 0 during attract, then confirmed all three canonical
attract checkpoint crops correctly match bank 1 under unchanged mode semantics.

Final sequential command: `RUST_LOG=info python scripts/native_acceptance.py`.
It runs deterministic packages twice, host/asset checks, cold ADF menu, physical
inputs, scoring/status/audio contracts, canonical 10958 replay and takeover,
Blue/Red feedback at both ends/modes, full ordinary lifecycle/cadence and chip
memory, stale-bank rejection, restart/audio/latch controls, strict UI timing and
compiled lost-wrap/UI-overrun rejection. CT12 adds DOUBLE FAULT including its
pointer-fault control to the finite gate. Final exact accepted commit, command
exit codes and executable/ADF hashes are recorded in ignored build/acceptance
and the draft PR, and are summarized below in this separate documentation-only evidence commit.
No broad historical campaign or second emulator is asserted.

Limits: pre-Exec chip-pool bootstrap memory is unmeasured; no whole-game original
pixel/audio parity, new ownership or public distribution claim. Music/celebration,
recording/save/seek, rule/difficulty changes and repository rename remain excluded.

## Final finite gate: PASS

Accepted implementation: `ccaffc7b971145e15c13d5c6fcec268113229fa4`.
Base: `43e1118d878453809a68c257deef20a937697e15`.
`RUST_LOG=info python scripts/native_acceptance.py` exited 0; 26 sequential commands
all exited 0, with complete fresh native status and unchanged head throughout.
Run: 2026-10-02 12:00:28.601341–12:28:29.279218 UTC.

This evidence commit changes documentation/screenshots/instructions only. It does
not rebuild the accepted artifact to alter its BUILD identifier. Runtime modules,
assets, test implementations, lockfile and compiled artifacts are unchanged from
the accepted implementation; compatible receipts are reused transparently after
this evidence commit. The accepted artifact identifies ccaffc7, not the later
Git revision of these documents. Rebuilding a later documentation revision will
change generated BUILD text and binary hashes; that is not a claim of another
fresh full native gate.

| Artifact | Bytes | SHA256 |
|---|---:|---|
| `build/amiga/interfaces/enhanced/baseline-rally` | 198960 | `5e184f5c3e3e51403d21fcdf2fd7f43216e379bdd38cb8f7ce29298afae4a855` |
| `build/amiga/interfaces/enhanced/delivery/baseline-rally.adf` | 901120 | `d726202d9546cdfb904a1803c51ff7c46e24faf643a07ceafda05673c3364e25` |

Fresh gate extent:

- 23 host tests ; 115 declared native assets; deterministic ADF/executable equality,
 including embedded executable bytes and boot startup.
- Canonical 10958-tick trajectory, six-game result and31 flight-side changes pass;
 recording SHA256 4684b75c22a085644e32b09de749ba119aac0fd9649270aab09b3f8c3cbf8289;
 frozen trajectory payload 17dd5ddba0499a70956b2d588f084786a00c294672510f69ef991858734d79e6.
 Takeover preserves world/score/audio/clocks/entropy at 5480 verified input ticks.
- Status 2–6 visible/expired full 1536-pixel crops,31-tick clock, physical Copper
 pointers and completed banks/epochs pass; both status 2 and DOUBLE FAULT compiled
 field/pointer controls are rejected. Scoring and hit pitch/envelope controls pass.
- Cold ADF menu69 checks, help/controls/credits/pause/return/opposite-mode selection,
 held player exclusion and keyboard/joystick aliases pass. Both-mode game awards
 include Blue and Red, actual sprite colours at both ends and native gold tallies.
- Cold one-player→two-player restart:11,371 uninterrupted callbacks,9,272 actual
 publications, max update40,147CCK. Two-player→one-player restart:23,316 callbacks,
 19,168 publications, max update43,516CCK. Strict entry/completion bounds and
 latest completed physical Copper epoch checks pass; no observer phase rebase.
- Court publication stays before25 or blank>=252; footer still ends251. The real
 delayed stale-bank control is detected without relying only on counters.
- UI strict raw deadline checks pass 1933 callbacks through navigation, idle, play,
 pause/return and restarted flight. No gameplay/score writes inside construction.
 Lost-wrap control detects 327680CCK lost elapsed time; overrun control detects 100
 raw deadline failures. These are rejected controls, not accepted timing waivers.
- Restart emitted audio, result/title cleanup, exact early release/repress packets,
 fresh serve and independently held-player exclusion pass; compiled skipped
 latch retirement is rejected.
- Measured chip peaks after initialized Exec pools: cold boot 322,840 bytes;
 cold ordinary/application run 260,208 bytes; two-player direct run 293,944 bytes.
 512KB target has no slow/fast expansion. Pre-pool bootstrap remains unmeasured.

Exact sequential gate commands (all under RUST_LOG=info and pinned Python):

```sh
python -m unittest discover -s tests/unit -q
python scripts/native_assets.py
python scripts/build_native_adf.py --self-test
python scripts/run_enhanced_menu_tests.py --adf
python scripts/run_native_inputs.py
python scripts/run_native_contracts.py --case=deuce --self-test
python scripts/run_native_contracts.py --case=advantage
python scripts/run_native_contracts.py --case=return-deuce
python scripts/run_native_contracts.py --case=advantage-game
python scripts/run_native_contracts.py --case=match-award
python scripts/run_native_contracts.py --case=status-2 --self-test
python scripts/run_native_contracts.py --case=status-3
python scripts/run_native_contracts.py --case=status-4
python scripts/run_native_contracts.py --case=status-5
python scripts/run_native_contracts.py --case=status-6 --self-test
python scripts/run_native_contracts.py --case=audio-hit --self-test
python scripts/run_demo_match_tests.py
python scripts/run_demo_match_tests.py --takeover
python scripts/run_enhanced_feedback_tests.py --mode=one
python scripts/run_enhanced_feedback_tests.py --mode=two
python scripts/run_ordinary_round_tests.py --mode=one --match --cadence --adf
python scripts/run_ordinary_round_tests.py --mode=two --match --cadence
python scripts/run_ordinary_round_tests.py --mode=one --bank-control
python scripts/run_ordinary_round_tests.py --mode=one --match --early-release --audio --self-test
python scripts/run_native_setup_tests.py --self-test
python scripts/build_native_adf.py --self-test
```

Additional bounded pixel reviews: complete 896-pixel one/two-player mode crops in
ordinary checks; retained DEMO bank 0 actual native fixture; original DBF native
fixture; all 115 input hashes reviewed with imported hashes preserved;22,848
unchanged court/net scanout pixels. Title/field expectations spell text directly
from committed font bits, with no runtime-derived expected screenshot regeneration.
Main scheduler, gameplay/scoring/control code, poses/animations/atlas, recording
and frozen trajectory remain byte-identical inputs to merged 43e1118. Target
receipts/raw reports remain ignored under build; no ROM/ADF/executable is committed.

Pinned Copperline ELF SHA256 26d655f07484412d00ad20eb5f0b363498eccb83d2261526c0cbb21ad8c723e8.
Official AppImage SHA256 e69e732fc027d35f74874ea6720cc39f2f194006997d7000dc94b870ae989ce5.
No acceptance blocker remains; independent parent review/merge is separate.
