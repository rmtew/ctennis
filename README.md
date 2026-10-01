# Champion Tennis SG-1000 to Amiga 500 port

The goal is a native, playable unexpanded PAL A500 version with the cartridge's gameplay preserved. The [roadmap](Champion-Tennis-Amiga-Port-Agent-Roadmap.md) defines the target and phase gates; the [worklog](WORKLOG.md) gives the current result and next action.

The cartridge and Kickstart ROM are local inputs configured in ignored `config.local.ini`; see [config.example.ini](config.example.ini). Do not commit ROM images, generated listings, or unmodified extracted assets.

The authoritative reconstruction is generated from the local cartridge and the tracked inputs in `analysis/`:

```powershell
python scripts/roundtrip_rom.py
python scripts/check_source_ball_update.py
```

The first command writes ignored `build/analysis/champion-tennis-classified.asm`, assembles it, and requires an exact 8,192-byte match. [Whole-ROM review](analysis/static-rom-review.md), [annotation audit](analysis/annotation-audit.md), and [frame-update contract](analysis/frame-update-contract.md) explain the current interpretation and its limits. The Python source model in `scripts/` is a checking aid. [The original evidence map](analysis/rom-map.md) and [archived worklog](analysis/history/WORKLOG-pre-port-cleanup-2026-09-29.md) retain the investigation history.

Current work follows the finite [playable native queue](PLAYABLE-PLAN.md).
CT01–CT09 are merged: maintained gameplay, scoring/rounds, result/restart,
physical controls, native graphics/sound and bounded ordinary cadence are in
place. CT10 removes the final generated clock/state integration and packages
the private native executable as a bootable ADF. Copperline is the user-approved sufficient validation target; exact-head
independent review and current delivery receipts remain required. Pre-Exec-pool
transient RAM usage is unmeasured.
See [delivery instructions](analysis/native-delivery.md) and [WORKLOG](WORKLOG.md).
Source-format captured replays are test-only observations/initialization;
ordinary assembly consumes prepared native assets and vasm, without translation
regeneration, source virtual memory or emulator debug calls. No cartridge is
required at runtime. This is not a whole-game pixel/waveform/raw parity claim.

The [test commands](tests/README.md), [manifest review](analysis/test-manifest-review.md)
and [coverage backlog](tests/coverage-backlog.json) retain their evidence and
unresolved requirements. Generated fixed-dispatch core checks are translation
diagnostics until migrated to the maintained product boundary. Local passing
cases and retained reports do not establish ordinary full-match or complete
hardware acceptance. See the [worklog](WORKLOG.md) for the current item and one
next action.

Controls: Delete selects one player; Tab selects two. Player 1 uses joystick
connector 2, player 2 connector 1, with four directions and red/blue actions.
Two-button sticks are required for both actions; no keyboard substitute for a
missing second button is assigned. Pads remain attached to their players after
an end exchange. In one-player mode connector 1 does not control the opponent.

Use `RUST_LOG=info python scripts/progress.py` to check current local evidence
before and after focused work. It reports behavior extents, compiled runtime
dependencies and target delivery separately. Legacy or changed evidence is
unverified; compatible retained evidence is reused, not a fresh execution.
See [report integrity](analysis/evidence-freshness.md).
