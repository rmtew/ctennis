# Enhanced and original interfaces

This follow-on preserves the shared maintained gameplay. The normal builder
selects the enhanced interface; `--interface=original` is the immutable-layout
comparison aid. Both choices use the same game, lifecycle, scoring and audio.
The later approved menu/pause/attract extension is documented below; the
checkpoint sections retain their original narrower scope.

## Build and private output

Run the existing explicit offline `scripts/prepare_native_assets.py` first.
Then use `RUST_LOG=info python scripts/build_native_game.py
--interface=enhanced` (or `original`). Executables are separately named
`build/amiga/interfaces/<flavor>/ctennis-<flavor>`, with their own listing,
compile manifest and atomic build receipt. `scripts/build_native_adf.py
--interface=<flavor> --self-test` packages independently named private disks
under that flavor's `delivery/` directory. Neither overwrites the verified
CT10 delivery directory. Generated assets, captures and disks stay ignored.

The original flavor preserves the merged CT10 executable and ADF bytes.
Enhanced layout fetches the same 32-byte rows at DDFSTRT/STOP$48/$c0 instead of
$38/$b0. Hardware sprite X origin becomes$a0 instead of$80. Only the actual
midline score-bank waits move+$10; row-start and end-row restoration waits and
all bank byte offsets stay unchanged. The same initial Copper list is copied
into the second buffer. The sprite-safe publication cutoff remains24, before
PAL sprite header DMA starts at25; changing interface never changes that rule.
Logical gameplay coordinates remain unchanged.

## Physical controls

Main1/2 select one/two players. Delete/Tab remain aliases. P1 uses WASD and
F/G (red/blue), P2 uses cursor keys and period/slash (red/blue). P2 also accepts
keypad8/4/2/6 directions and keypad0/decimal red/blue. Joystick P1 remains
connector2 and P2 connector1. Key legends refer to the conventional US layout;
the implementation uses raw Amiga positions, not host text/ASCII.

The CIA serial receiver retains each key separately, including releases and
aliases. Each physical sample ORs keyboard and joystick masks *before* the
existing pressed/released edges, inherited-action latches, player/end ownership
and one-player AI exclusion. Releasing one alias/source cannot release another
held source. Opposing direction bits preserve existing game behavior: bounded
down then up, right then left movement, including the existing boundary order.
No priority or normalization has been inserted into gameplay.

Raw positions were checked against the target's pinned Copperline
`src/video/window/host_input.rs` mapping and the AmigaOS [Keyboard Device
reference](https://wiki.amigaos.net/wiki/Keyboard_Device). Tests use actual
`input.key` events and the CIA path. The emulated A500 keyboard also models
matrix ghost suppression; arbitrary four-key rectangles are not guaranteed
rollover. The retained failed four-WASD probe demonstrated this, rather than a
missing game input. Separate opposing pairs and the declared simultaneous
player/diagonal/action combinations are observed without bypassing the keyboard.

## Offline title and small font

The original title oracle/assets remain unchanged. The enhanced title retains
the large logo and copyright, replaces only instruction rows144–191, and uses
native precomputed bitplanes. `assets/interface/small-font-additions.json`
contains newly authored missing uppercase JQWXZ, digits4567, lowercase and
common punctuation in the existing small-font style. The original glyphs are
read offline from the verified private capture; no extracted glyphs are
committed. No runtime font renderer or net-message redesign is introduced.

## Finite acceptance and provenance

`run_interface_tests.py --mode=one` / `--mode=two` exercise ordinary title,
intended instruction raster, clean margins, main/legacy held selection, the
first completed selected-mode label against immutable original pixels, raw
keyboard press/hold/release, diagonals/actions/simultaneous players, all keypad
aliases, opposing pairs, combined joystick/key release, actual movement/reversal,
one-player exclusion and blue serve. The mode check compares only the existing
40×8 label crop, not complete first-frame equivalence or ball-pose alignment.
The historical mode-selection runner explicitly builds original and retains its
full established original viewport/ball-pose and compiled-fault checks. `--ownership` starts once from the existing
verified exchanged-end source phase and checks real keyboard movement/reversal
and player2 keypad-blue serve. It does not establish ordinary reachability.

Presentation/status runners accept explicit `--interface` and write separately
named receipts/captures. Enhanced original-pixel comparison shifts only the
native crop from[62,16,574,208] to[126,16,638,208] (32 logical pixels), retaining
source pixels/checkpoints/regions and the exact generation4131 supplement.
Full moving-scene comparison includes sprites and score alignment, with separate
black margins[62,16,126,208] and[638,16,702,208]. Existing sprite/expiry mutations
remain actual compiled faults. There is no softened enhanced pixel tolerance.

The existing ordinary cadence runner accepts `--interface` and `--keyboard`.
The latter uses actual main1/2 and F/period fire events for its complete ordinary
match/title/opposite-mode restart/held-action release/repress milestones;
keyboard and joystick recordings have separate output names. Cold ADF and
wrong-bank controls retain exact target, actual loaded bytes, physical beam
positions and initialized-Exec-pool memory observations.

Compile manifests derive interface identity from the actual compiled enhanced
marker. Result/provenance identity must agree; `status(interface_flavor=...)`
rejects another flavor or missing identity. `scripts/progress.py --interface`
adds a separate finite follow-on view requiring that exact flavor, complete
existing pixel/status extents, ordinary cadence, local controls and package
reproducibility. Its historical CT queue view remains separately labelled;
old diagnostic counts/source integration cannot certify this follow-on. Reports
and their source/executable/reference/tool/target fingerprints remain private.
Independent review and merge authorization remain separate from local passes.

## Current local review checkpoint (2026-10-02 UTC)

At the independently reviewed9155b60 checkpoint both flavor views reported
`evidenced within stated scope`; the26 then-current receipts
in the ignored `build/interface-checkpoint/interface-evidence-index.json` were
fresh and passed. That exact head was independently source/runtime cleared;
subsequent receipt-only changes require their own delta review.
The original executable SHA256 is
`b3ac773721e62f2cabe7806523f5650192386e4bc99e2e4a30aa880260d1d492`;
original ADF SHA256 is
`aff2a3df026ba888724a6f32ae3c055184829b425ecd97ae06cbfcf347934401`,
both byte-identical to merged CT10. Enhanced executable SHA256 is
`b5ed3d68c5a169e526cf8887e98887d8d91b55c6251f8aad9afd883dc83c6eee`;
enhanced ADF SHA256 is
`9367da9f2781236f7aa2d0deb96d58178e93c4a4dda36d50288f5a376d92b303`.

The two-player keyboard ordinary run completes23836 callbacks and19698
verified publications. Cold enhanced ADF completes11890 callbacks and9761
publications, verifies actual relocated executable bytes, and measures237384
chip bytes from initialized Exec pools onward (233760 from timer start). Its
pending11891 entry is explicitly excluded from completed callbacks. Original
ordinary cadence completes11890 callbacks/9763 publications. Both packages
pass two clean byte-identical rebuilds. Pre-pool usage, complete original
full-game raw/pixel/waveform parity and another emulator/real machine remain
unmeasured. Local exchanged keyboard ownership starts at original callback2672,
not ordinary reachability.

Affected command ledgers/logs remain ignored in `build/interface-checkpoint/`.
Earlier successful receipts invalidated by final helper changes remain historical;
final `ui-final-commands.json` and `post-placement-fix-commands.json` record22
and8 completed commands. Current provenance, rather than those counts, governs
acceptance. Final42 unit tests pass; original title/mode fault guards and the
maintained200-update serve mutation/restoration checks remain green. No aggregate
suite was repeated for this interface follow-on.

### Exact enhanced upper checkpoint correction

The earlier requested4131 row captured completed scene4130. The corrected
observer explicitly waits for the requested completed scene, with a three-frame
bound and rejection if the scene has been skipped. Callback/state checkpoint
4131 stays unchanged. The receipt separately records the actual callback reached
at scanout (4133 in this run), completed scene4131, and the immutable original
supplement hardware5430/pixel5432. All three normal crops match; the actual
sprite fault is detected at each exact requested scene. The progress proof
rejects the preceding-generation receipt. Other reports are retained evidence
at the reviewed head; conservative helper fingerprints may mark them stale
after this diagnostic change. They were not rewritten or broadly rerun.

## Approved menu, help and gameplay-interface extension (2026-10-02)

Richard approved this extension after the preceding comparison-interface scope.
It supersedes the earlier statement excluding attract/tutorial work. The original
flavor preserves interface behavior; the authorized tally integration changes
only its96 WAIT bytes against the retained pre-fix comparison. Enhanced remains
the default.
The implementation is isolated in `amiga/game/interface*.s` and the typed
`interface_state.i` record. Scoring, physics, AI, and tally-bank routines are
unchanged. `interface_feedback.s` only reads the logical game cells.

The title offers Start game, Players 1/2, How to play and Controls. Up/down
select, either action or Enter activates, and left/right toggle Players. Main
1/2 and Delete/Tab still immediately start the chosen mode. Help, Controls and
Credits share three pages, left/right wrap and either action or Escape exits.
Player count survives title returns and the one-player demo. Credits display
an actual build revision, with `+ LOCAL` for tracked working-tree changes.
The help rules were checked against the manual scan supplied in this session:
automatic returns by position; either action serves and selects the special
lob near the net/drop from the rear; 15/30/40/game, deuce/advantage, and six games
to win. The supplied web URLs returned403 here; the attached scan resolved
that rules-text blocker. No difficulty or rule changes are introduced.

Blue is logical player1 (native style2, palette `$55e`); Pink is logical player2
(style3, `$c5b`). Their controls remain attached to identity after exchanging
ends. Controls are presented as movement and serve/shot purposes. Both actions
have the same game meaning. Existing court A/B artwork is preserved; new text
uses Blue/Pink. Read-only feedback reports either colour winning a game and the
updated numeric tally; YOUR SERVE appears only while a human is waiting to serve.
The independent tally-bank investigation remains separate.

Attract begins after1800 idle title callbacks (30.04seconds at the unchanged
59.922738Hz source rate), followed by the ordinary64-callback selection gate.
There is no demo hotkey and key3 has no assigned behavior. The demo uses normal
`game_new_match` and the same native input dispatcher/gameplay/scoring/render/audio.
`assets/interface/demo-inputs.json` uses schema2: native-rules-v1, input clock,
entropy-provider version, explicit seedACE1, initial game PRNG0, target and source
provenance, plus run-length physical port2 packets. It records a complete ordinary
native one-player match:10958 active input ticks,277 runs,194.2168seconds elapsed,
Blue0/Pink6. The data table is1110bytes (277 duration/mask word pairs plus a
zero terminator); the seed is an authored2-byte immediate and the entropy provider
has2 bytes of runtime state. Input ticks exclude service/round pauses; those run
normally. At the terminator playback supplies neutral input and never loops.

`record_demo_inputs.py` is an offline ordinary-native boot/title/start recorder.
Its performer sends real joystick movement/action events using read-only current
observations, not world writes. A private offline-only build chooses seeded
entropy while UI demo/playback is off; no recorder or capture-import machinery
ships. Its executable hash and private trajectory digests bind the actual capture.
The generated input table contains only physical masks and durations. Gameplay,
scoring, rendering and audio run normally; one-player AI continues naturally.

Demo randomness uses the same entropy adapter consumers and the native game PRNG.
The inspected gameplay nondeterminism beyond physical input was the adapter's
CIA timer bit. Demo/offline recording substitutes a16-bit Galois LFSR, B400 taps,
seedACE1; normal player games retain live CIA entropy. Match creation initializes
only UI entropy state; ordinary game initialization clears native PRNG to0 as
before. Takeover stops input playback and switches the entropy adapter to live
CIA input, preserving the current world and native PRNG. No new difficulty or
scoring rule is introduced.

DEMO explicitly offers G / port2 button2 to take over Blue. Only player1 owns
takeover; player2 slash/keypad decimal are ordinary fresh-input exits to title.
The takeover press is consumed by the existing per-player action latch until
physical release. Score, ball, players, clocks and audio are preserved at the
handover; the next normal gameplay tick advances them. Physical keyboard/pad
edges are sampled before playback, and keyboard/joystick sources are observed separately before their OR.
Entry-held controls are filtered until their own physical release, including
after takeover; a fresh joystick button2 remains eligible while G is entry-held. Other fresh supported gameplay/menu input returns to title and
consumes the event.

P or Escape pauses live/round/result court states. PAUSED provides Resume and
Return to title; return requires an explicit Yes confirmation, defaulting to No.
Paused simulation callbacks continue sampling physical input but skip native
game clocks, gameplay, scoring, sequencer and round/result polling. Paula is
muted using its actual native voice levels (write-only hardware volumes are not
read by the game), then restored on resume; held actions are latched until release.
The free-running scheduling timer and keyboard handshake continue, preventing
an elapsed-time catch-up or lost key release on resume.

The footer is a separate16-row,512-byte white bitmap, fetched after the192-row
court. It appends Copper commands after all existing score commands and changes
only the enhanced display stop and late-blank publication threshold (252 rather
than236; the sprite-safe early cutoff24 is unchanged). It neither changes score-bank offsets nor
writes to tally assets. Both Copper buffers receive the same initialized footer
pointers. Title text uses the existing native bitplanes and a private offline
font; the sole new committed glyph is the authored selection star.

Exact integration touchpoints for the tally worker: `controls.s` observes/filter
raw joystick sources before keyboard OR; `keyboard.s` retires entry-held keys
on real releases and filters them during keyboard merge; `menu.s` delegates enhanced
selection/remembered count; `integration.s` calls `ui_playback` after normal
player assignment; `result.s` returns enhanced results to the title menu;
`gameplay_integration_probe.s` samples UI, gates pause polling/ticks, initializes
footer pointers and includes UI modules; `sprite_probe_display.i` appends the
footer after the score command include. `score_copper_patch.i`, scoring modules,
and round rules are untouched by the interface work. The independently reviewed
tally generator change from PR14 is now cherry-picked separately, with original
commit references preserved through final documentation head5ae440f.


## Full-match replay verification

The earlier300-tick five-second loop was rejected as the finished attract
experience and replaced, rather than stretched or repeated. Full seeded playback
reproduced all10958 captured native world/score/entropy boundaries and the ordinary
six-game match result.31 flight-side changes were observed; ordinary movement,
rallies, end exchange, WIN marks and the DEMO prompt were pixel-inspected. This is
local native capture/replay repeatability, not original-platform parity.

`run_demo_match_tests.py` checks metadata against the actual initialized seed,
compares read-only per-input native trajectory digests, and has a halfway takeover
case that preserves world/score/voices/clocks/entropy at the handover, consumes G,
retains AI ownership and verifies live advancement and stopped demo entropy.
No state injection or captured-world snapshot occurs in game runtime. The private
trajectory is an observer's test receipt, not a shipped oracle. Future player
recording, persistence, seek/rewind and checkpoints remain specification only.

## Combined checkpoint, 2026-10-02

Feature source c171349 is based on2337278. Authorized tally commits b50fae6,
49e018a,8a85dd5 and5ae440f were cherry-picked with `-x` references through
combined source c38d42d. WORKLOG prepend conflict retained both original entries
and legacy file bytes. No scoring or gameplay rule change accompanies the UI.

Cold PAL A50068000 OCS512KB chip/no expansion Kickstart1.3 route passes69
finite actual emulated-input checks. Report:
`build/tests/enhanced-menu-cold/report.json`. Enhanced executable:
`71f970cc1176f79c18d2bf8da4aba84e51ddde507911d56d8b756df9e7fc8d44`;
ADF:`11b64c2bc0d22cd2538602159297371034be6efee60b9a28d819681dea96cddd`.
These private artifacts use BUILD c38d42d. No user-run WinUAE result is claimed
for this combined artifact. Target config is verified from actual emulator log.
An initial rerun completed assertions but lacked RUST_LOG=info; it was excluded
and replaced with this target-logged successful run. Units43 pass.

Source-only result-media dependency unit coverage now mocks declared primary
manifest metadata in memory; it preserves all dependency assertions and does not
create a runtime oracle. Historical original presentation/audio guards remain
unrun here: `tests/reference/presentation/manifest.json`, one/two match child
manifests/images and `tests/reference/audio/manifest.json` plus source WAV/event/
frame-time bindings are absent. They are needed to verify original-reference
picture/audio parity. Bounded title asset recovery does not restore this archive;
no broad capture reconstruction or aggregate acceptance promotion is claimed.


Final published product checkpoint:840e3ff, source tree480cedabdcb804fbfc9dba11960fc1fdcae6787f.
The shell push lost credentials; authorized GitHub blob/tree/commit/ref operations
published the same tree as preserved local3a2c5ae. Fetch and read-only tree
comparison verified equality; enhanced-local-checkpoint retains local history.
The original title generator remains exactly the published c38d42d version.
Automatic review rejected its proposed validation/seed-emission update twice;
the safe final design removes that delta and keeps seed in native code, checked
against actual initialized state. No private conversion assets/dependencies were
uploaded. There is no pending approval or rejected-file retry in the final change.

Cold-ADF final product build840e3ff (clean tracked working tree) passes69 checks.
Executable:`5d7fcfecc52d931a1466e13fc93945a66c1cd16ad2da6bb9fb69471a234600f7`;
ADF:`1e0a0b1396bbf77ccb82da2de043263bc4b729284b092aa76ab37817b210b3b0`.
Mid-match takeover independently matches5480 native input boundaries before
joining at5479, after three awards; zero missed publications. Full-match repeat
and final two-colour feedback receipts accompany the final documentation entry.
Units43 pass. Draft PR15 stays unmerged; parent owns independent review.

Final full repeat on clean BUILD840e3ff reproduced all10958 boundaries and the
Blue0/Pink6 result,31 observed flight-side changes and zero missed publications.
Its executable SHA equals the final cold-ADF executable above. Recording JSON
is10013bytes; generated assembly text4965bytes; shipped table1110bytes. A raw
one-byte-per-active-input representation would be10958bytes; run lengths reduce
that payload by89.87percent. Seed/provenance metadata is separate from the input
table; no entropy stream or world snapshot is stored. Demo-specific playback
state is8 bytes (cursor4/count2/mask1/flag1) plus entropy2. Total interface RS
record300 bytes also contains menu/input-edge/pause/feedback state; private font
and512-byte footer are separate and not part of the recording footprint.

Final two-player feedback: Blue1/Pink0 at callback1258, then Blue1/Pink1 at3553
with end exchange and logical style mapping verified; zero missed publications.
Maintained serve self-test passes200 updates/40 PSG bytes, detects real skipped
dispatcher mutation and passes after restoration. Original packaging self-test
passes two-clean reproducibility. Post-tally original executable:
`1d7421946c8e3de8fbf7ccc7b5bff95ee68d83017ea237a47fc74d0104812829`;
ADF:`7f6dcacb2746d2c3fe6c60bbd0faa6845539d8b9ed63303ff51f1daad822dad6`.
Against retained pre-tally original executable b3ac7737, lengths are equal166120
and exactly96 bytes differ, all minus2. Pre-fix original executable/ADF remain
in `build/ui-baseline/original` as separate comparison artifacts. Progress reporter
was run after final builds; historical gates remain unverified/stale as reported.
No complete aggregate rerun or new original-reference gate promotion occurred.

Playback/entropy routines occupy108 bytes of native code (74 playback,34 seed/
entropy); the adapter and initialization hooks add22 bytes. Together with the
1110-byte table this is1240 executable/resident bytes, excluding shared UI code,
font/footer and mutable playback state. Seed immediate bytes are already included
in the34-byte code count. All title/page/footer static strings fit their28-character
native row capacity; menu/help/pause/demo and both game-win pixels were inspected.
