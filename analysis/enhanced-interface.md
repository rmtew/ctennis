# Enhanced and original interfaces

This follow-on preserves the shared maintained gameplay. The normal builder
selects the enhanced interface; `--interface=original` is the immutable-layout
comparison aid. Both choices use the same game, lifecycle, scoring and audio.
There is no attract mode or tutorial.

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
