# Sprite branch verification

Verified product commit: `f4e1b69db7a7a0ee116b142bdb413ebae5d3e3de`.
Base: `93bb640700aa5dc407a081104475233321a5dd8d`.
The later documentation commit changes no native product or test inputs.

`RUST_LOG=info python scripts/native_acceptance.py` completed steps0–17:
28 host tests, asset verification, build/package, cold ADF title/input/header
scanout, native controls, scoring/deuce/advantage/match-award/status/audio guards,
full frozen demo replay and mid-demo takeover. Full replay verified10958 ticks
and the original0–6 result. Takeover verified5480 ticks. Both reported zero
missed publications and preserved the independently frozen trajectory.
Actual scene observations checked human A and AI robot B across end exchange;
takeover preserved the roles and native state/clocks/audio/entropy.

The gate was intentionally interrupted during step18, ordinary feedback in
one-player mode, after the newly selected scoreboard design expanded scope.
The aggregate receipt is incomplete/interrupted, never passed. Two-player
feedback, the remaining ordinary-round/setup cases and combined CT13 acceptance
are not certified. Raw reports/captures remain ignored under build/.

Independent read-only review found no material bug in the implemented sprite,
A/B header and residual-logo scope. It confirmed the two replay receipts.

## Exact verified artifacts

- Native executable SHA256:
  `d88703c858b8802691d855f3623d15a8366bae73bada969dc3bf75049eb0ee7d`
- Cold ADF SHA256:
  `080697cb6f941ce4bcc86689c764958822d107f8cbd75876ac23f7029b707104`
- Sprite atlas SHA256:
  `cf1b94f8a8f804df28cc928472e600cfe5d57579967e36344a58fd104a4606ef`
- Robot pose table SHA256:
  `044bb1c5b8b96182a5844d09fc2e8537b896f747d097a71144ce7ef12cf62363`

Target: PAL A500,68000,OCS,512KB chip,zero slow/fast, external legitimate
Kickstart1.3. Recovered locked vasm1.9d and official Copperline1.0.0-rc.1 using
the documented CT12 procedure; hashes match the existing locks. No cartridge
extraction or alternate emulator/compiler was used.

## Newly selected scoreboard: pending, not implemented

The later approved design is six dim grey WIN words per logical player,
earned words in Blue/Red, clean numeric points and a thin white border across
the top and both sides, open at the bottom. This supersedes hearts, GAME and
green rails. It is not present in these native assets or preview images.

The selected source `libfile_dd1161148de481918a8b2aab8a07c1e6` resolves through
Library, but two fresh current-helper downloads failed with
`library file transfer failed: download failed`. Its pixels have not been
inspected. The supplied earlier screenshot has the separately documented
materialization failure. Do not claim either reference was inspected.

Hardware audit found a possible fit preserving the existing 4-plane playfield,
7 variants per side,48-row game banks and Copper pointer/fetch timings.
Unused indices6/7 could hold dim grey; Blue4 remains unchanged. Index5 occurs
only in the authorized scoreboard region and could become a duplicate Red for
earned B WIN words. Thus A6→4 and B7→5 both toggle only the already switched
plane1. Numeric points and all static index5 pixels must be refitted/audited
before accepting this allocation. This is a feasibility finding, not tested
or implemented artwork. Preserve white frame bits in every bank and verify
all0–6 transitions, both presentation banks, end exchange, point/advantage,
expiry/stale-pixel and fault guards before proposing integration.

CT13 owns the footer selector/layout and celebration lifecycle. Master is
unchanged. No merge or public publication is authorized by this receipt.
