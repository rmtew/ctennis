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
flavor still preserves the exact executable bytes; enhanced remains the default.
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
`assets/interface/demo-inputs.json` holds300 frames of run-length encoded physical
port2 packets, measured during ordinary native play on the original comparison
executable. `record_demo_inputs.py` is an offline ordinary-input recorder; no
capture import, source-machine RAM or test harness enters runtime. Input playback
is deterministic by gameplay callback; native timer entropy remains ordinary.
One-player AI continues naturally. The short recording loops until takeover,
input exit, or the ordinary result/title lifecycle.

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
round rules, and the score asset generator are untouched.
