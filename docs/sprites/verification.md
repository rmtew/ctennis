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

## Approved WIN scoreboard implementation

The authoritative native UI specification is now implemented: six always-visible
WIN rows per player, earned Blue/Red and remaining dim grey333; plain retained
point/advantage glyphs; white top/sides with padding and no bottom; black background.
Hearts, GAME and green rails are removed. A/B headings and controller-role labels
are retained. The same panels, court geometry, scoring rules and footer are used.

No additional bitmap data, bank, plane, Copper command, allocation or product
instruction is required. Indices1/3 are released by the removed score decorations;
unused6 supplies the other grey. A6→4 and B3→1 each toggle existing plane1. Net
gradient index5=77f, court/net/sprite colours and all Copper pointer/fetch/restore
include bytes are preserved. Frozen host contracts cover all0–6 variants, exact
original point glyphs and every court pixel outside the authorized panels/logo.

At3a4e094 the fresh28-case native scoreboard gate passed, including two stable
full-panel captures per case, both physical Copper banks, all242 selected/fixed
restore pointers and a compiled wrong-pointer control with unchanged score
scalars. The control failed exactly552 doubled pixels for six incorrect A rows.
Pillow12.3.0 and its input files are pinned in the receipt. Ordinary one/two-player
feedback passed full-panel pixels and human/robot ownership through end exchange.
The10958-tick frozen replay and5480-tick takeover also passed at this WIN checkpoint,
both with zero missed publications. These are new results, not inherited passes.

A separate focused physical pause/quit/title/opposite-mode restart check passed
both A6→0 and B6→0. Two stable captures per case showed every WIN row grey, both
points/tallies zero and HUMAN labels on both sides; no RAM writes or new builds.
Script/report/captures remain ignored under build/tests/native-scoreboard-reset.

The initial full gate at3a4e094 failed only its cold-boot allocator observer after
completing all ordinary match/restart milestones and meeting every timing/
publication assertion. Raw68000 writes proved mh_Free's lowword fad8 arrived
before highword0003. Sampling the lowword immediately mixed in oldhigh0004 and
invented a65536-byte discrepancy. The actual header/freechain contained260824
free bytes, using263464 bytes. The corrected test-only observer waits for all4
bytes from the same instruction in either bus order and rejects incomplete
mutations; the final free-chain agreement assertion remains intact.
Independent raw-trace review found902 eligible writes,451 complete stores and
no pending halves, with corrected cold-boot peak267016 bytes. Four focused
collector regressions and35 total host tests pass. No product code, allocation,
memory limit or timing guard was changed by this fix.

The final corrective gate runs at the committed clean head recorded in
build/acceptance/report.json; that receipt and the worker's final handoff are
authoritative for completion/checked extent. An earlier failed gate must never
be cited as an aggregate pass. Combined CT13/title integration requires its own
verification.

The selected concept source libfile_dd1161148de481918a8b2aab8a07c1e6 could not be
materialized locally. The parent inspected it and supplied the complete native
implementation specification, explicitly confirming it is a concept with final
pixel fitting required. No concept pixels are imported and no local inspection
is claimed. The parent will compare the actual native render during review.

CT13 retains footer/selector and celebration lifecycle ownership. No merge or
public publication has occurred. Parent will create the draftPR; denied PR
creation will not be repeated.
