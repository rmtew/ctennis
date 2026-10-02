# Combined integration checkpoint

Branch: integration/current-polish. Base master:
93bb640700aa5dc407a081104475233321a5dd8d. Master is unchanged.

Imported source heads, preserved by merge commits:
- UI/music: 1c03090cd3dbe2c75536fc1259b05faff6166e7b
- Classic sprites/scoreboard: 291250182de735cb8b102cb96eb6b126aca46a14
- Font-Mac: 9beb616fe34f61ef2eda4a50c79be81b5e8b0e4a, including
  80df928024c37dd1dda822af2d307e05c638bcc3.

These pinned imports are not final author clearance. Final core deltas and
source freeze are pending; the combined finite gate has not run.

Conflicts: kept CT13 demo selector/isolation, footer ownership and celebration;
kept Classic A/B controls, scene roles, scoreboard and asset edits. Combined
manifest retains both authored Battle Hymn and sprite provenance. Combined demo
observer retains physical takeover consumption, role checks, WIN scanout and
post-celebration publication observation. No golden trajectory was regenerated.

Integration implements Font-Mac menus/help with 8x8 ASCII and 2–3 pixels leading,
plain rules and exact font credits; status/footer remain in the retained font.
Build page baking rejects missing glyphs. The staged extraction validator remains
unchanged. Native title figures use ready7 A and ready0 B, including retained
white rackets, at native size. Pure menu-owned caches choose B human/robot without
gameplay state changes. Menu captions are Human vs AI/Human vs Human.

Status banks now restore the court/net at y96..103. White full-word notices use
black x80..175; outside that rectangle the original court pixels remain. Existing
net-row Copper slots select the status banks; plane1 restore slots preserve
adjacent WIN banks. Top-row status commands are removed. Timers and event logic
are unchanged. Independent source Copper contracts remain frozen outside the
explicitly authorized status-pointer change, using the pinned sprite source.

Focused validation so far: all35 host tests,121 native inputs,5504 extraction
pixel comparisons/81 ASCII glyphs, locked vasm build, deterministic ADF packaging,
actual DOUBLE FAULT scanout and expiry passed. Raw receipts and actual captures
remain ignored under build/tests. Native menu, pointer controls, strict cadence,
memory, both roles, WIN progression/reset and frozen demo checks remain pending
or in progress. No combined acceptance or release readiness is claimed.

Setup: vasm official commit685a87e5ed14285350ccdb6581c9771bc8df6c7d reproduced
locked SHA2560332feebc562e06bf245c1d60bef3fd7598c464a4be8162429be5e3e3a061e39.
Official CopperlineHQ/Copperline tagv1.0.0-rc.1 points to
e65a9584ccd0c86e678661ed5d2c18622da63fd4. AppImage SHA256
 e69e732fc027d35f74874ea6720cc39f2f194006997d7000dc94b870ae989ce5.
Portable mode uses ignored .tools. External supplied Kickstart only; no cartridge
was opened or used. An api.github.com curl request failed CONNECT403; official
GitHub clone and release download succeeded without escalation or proxy changes.

## Focused follow-up

Ordinary menu/input passed89 checks, including actual full title scanout with
both B roles, pause/confirmation inversion, selector isolation and physical
keyboard/joystick takeover. Strict native setup then detected excess work from
a separate figure copy; that intermediate check failed and was superseded.
Baking complete coloured title pages reduces runtime to one copy per plane.
The latest strict setup check passed all callbacks, repeated menu/help/controls/
credits/idle/start/pause/return/restart, with no deadline failures or catchup
callbacks. This uses13KB more static chip cache than the intermediate layout;
combined memory acceptance remains pending. No deadline exemption was added.

DOUBLE FAULT passed108 checks including full actual pixels, net restoration,
31-tick expiry, completed bank association and physical plane pointers.
Compiled wrong-field and wrong-pointer controls were detected. These focused
runs used e0df7b4 plus the documented local copy optimization; final clean-head
build/package hashes are in ignored build reports. Ordinary menu passed before
the copy optimization; strict setup rechecked the optimized title/page pixels.

Commands:
- python -m unittest discover -s tests/unit -q
- python scripts/native_assets.py
- python assets/interface/font-mac/extract.py --text 'Start game' --text 'Font-Mac - creator unknown'
- RUST_LOG=info python scripts/build_native_game.py
- RUST_LOG=info python scripts/build_native_adf.py --self-test
- RUST_LOG=info python scripts/run_enhanced_menu_tests.py
- RUST_LOG=info python scripts/run_native_setup_tests.py
- RUST_LOG=info python scripts/run_native_contracts.py --case status-6 --self-test

Remaining finite combined gate after final core freeze: memory and physical
publication across ordinary game/celebration, both modes/poses, WIN0–6/reset,
canonical trajectory and intentional celebration-tail updates, two unattended
full demo cycles and proof of no court flash after returned title. The pending
parent-relayed legacy title/court/title fix is not presumed present or cleared.
No release readiness, master merge, public release or full-source parity claim.

## Approved help navigation and columns

The follow-up user request replaces the old instruction sentence with one centred
BACK / EXIT / NEXT row at nativey182..189. Words begin atx48/112/176, with equal
32-pixel gaps. NEXT is inverted/default on entry; left/right clamps selection;
Enter or either action activates; Escape exits. BACK/NEXT wrap and preserve the
selected action across page changes. Re-entry resets NEXT. Main title hotkeys
and remembered human/AI choice remain intact.

Pages are now1How to play,2Scoring and demo,3Controls,4Credits. Splitting the
rules preserves their meaning and native8x8 Font-Mac size while fitting explicit
wrapped explanations. Leading labels share safex16; right explanations end at
safex240, occupy at most112pixels and leave at least32pixels between columns.
Rows have2pixels leading; title/body/count/navigation remain separate. Heading
starts atnativey76, body rowsy88..165, centred page county168..175, navigation
y182..189; no text extends beyond the192-row title viewport. Credits remain last
with the exact Font-Mac/archive attribution. Build-time tables validate column
widths, wrapped row heights, margins and glyph coverage. No layout engine or
new gameplay state is introduced; one padded UI-only navigation word is added.

Focused physical help navigation passed43 assertions, including defaults, all
three actions, boundary clamping, held/repeated controls, both wrap directions,
Enter/Escape and full actual page/blank/navigation pixels. Strict setup passed
with no raw deadline failures, preserving continuous timer accounting, repeated
navigation/idle/start/pause/return/restart and exact title/page scanout. Initial
larger copies failed at return-to-title; normal two-human captions are now baked
into existing colour pages and copy loops use128-byte blocks. No timing bound
or clock rule was relaxed. Static UI cache increase relative to48cf4e0 is11264
bytes; full combined memory acceptance remains pending after core source freeze.

Commands added/updated:
- RUST_LOG=info python scripts/run_enhanced_menu_tests.py --help-only
- RUST_LOG=info python scripts/run_native_setup_tests.py

Raw actual screenshots remain private underbuild/tests/help-navigation and
build/tests/native-setup. User-facing preview uses716x537TV aspect from the
716x285raw field; it is exact nearest-row presentation scaling, not redrawn
or generated content. No full combined campaign or master merge occurred.

## Source freeze and combined candidate

Parent froze product sources atUI1c03090, sprites2912501 and font9beb616 plus
approved integration changes. Tests-only CT13 handoff6e43e7c5ee4a7b39d513b9124f5a614375da4883
was merged with its history; its four changed files contain no product delta.
The legacy .title_wait path now returns directly to title at its existing timer
boundary. Its deliberate returned-court rendering/mode/intro sequence and unused
court-display hook are removed. Modern human celebration/full-play/fresh-fire and
unattended first-complete-phrase return are unchanged.

The imported two-cycle observer now starts after ordinary initialization and
watches the entire title bitmap and Copper control block, every actual COP1LC
publication, and every PAL field during both returned-title idle windows.
Frame digests must equal the independently font/mask-checked initial title;
sequence gaps or unexpected bitmap/control writes fail. The first wholly
returned-title field is identified from actual bank publication. No runtime
state or input is injected. Eight actual title rasters and three automatic
entries remain checked, together with exact926-tick first phrase and1800-tick
idle per cycle. This tightens the author's helper to the combined pixel extent.

Help/navigation clean-head checks at5a4c0fd passed43 physical assertions and
2136 strict setup callbacks with no source changes during either run. The same
Library image now has version2, showing page1/4 with NEXT selected at716x537TV
aspect. This evidence predates the neutral legacy-path cleanup; final combined
acceptance runs once at the published frozen candidate, with no master merge.

## Finite gate observer correction

The first combined run at a14e01fb passed commands0–23, including all10958
canonical input ticks and5480 takeover ticks, then stopped at the unattended
observer: Copperline's bounded per-field MMIO queue dropped3847 events during
legitimate bulk returned-title construction. This is a harness failure, not a
product pass. The correction activates the full bitmap write watch after the
first actual title-bank publication and removes it at the next automatic demo
entry; lifecycle, control-block and physical publication watches remain active
through construction. Every PAL title-field digest and all eight pixel captures
remain required, with no dropped events permitted. Product sources and assets
are identical to a14e01fb. Continue only the failed observer and commands25–32;
reuse earlier unchanged-dependency receipts transparently, without a new full
campaign or a claim that the initial aggregate passed.
