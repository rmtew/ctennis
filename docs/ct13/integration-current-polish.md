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
