# Champion Tennis SG-1000 to Amiga 500 port

The goal is a native, playable unexpanded PAL A500 version with the cartridge's gameplay preserved. The [roadmap](Champion-Tennis-Amiga-Port-Agent-Roadmap.md) defines the target and phase gates; the [worklog](WORKLOG.md) gives the current result and next action.

The cartridge and Kickstart ROM are local inputs configured in ignored `config.local.ini`; see [config.example.ini](config.example.ini). Do not commit ROM images, generated listings, or unmodified extracted assets.

The authoritative reconstruction is generated from the local cartridge and the tracked inputs in `analysis/`:

```powershell
python scripts/roundtrip_rom.py
python scripts/check_source_ball_update.py
```

The first command writes ignored `build/analysis/champion-tennis-classified.asm`, assembles it, and requires an exact 8,192-byte match. [Whole-ROM review](analysis/static-rom-review.md), [annotation audit](analysis/annotation-audit.md), and [frame-update contract](analysis/frame-update-contract.md) explain the current interpretation and its limits. The Python source model in `scripts/` is a checking aid. [The original evidence map](analysis/rom-map.md) and [archived worklog](analysis/history/WORKLOG-pre-port-cleanup-2026-09-29.md) retain the investigation history.

Current work follows the finite [playable native implementation queue](PLAYABLE-PLAN.md)
and [agent instructions](AGENTS.md). CT-01 provides the shared maintained native
dispatcher in `amiga/game/` and `python scripts/build_native_game.py`; the default
serve replay exercises that dispatcher. CT-02 adds ordinary native title boot,
Delete/Tab mode selection and runtime match initialization. CT-03 adds native
two-pad controls and stable player ownership across court ends. CT-04 replaces
serve, contact, ball flight, movement and AI with maintained native 68000 logic
and fixes resumed-launch arithmetic. Focused product replays cover both-end
serves, a six-return rally and point ownership, movement limits and shot choice;
they do not establish continuous rounds or complete matches. Temporary
score/lifecycle, sprite/VDP and sound adapters remain CT-05–CT-08 debt. Next
complete rounds, results, native graphics/sound, ordinary full-play verification
and a bootable ADF. See [CT-04 evidence](analysis/native-gameplay-regression.md).
Completing an exhaustive test suite is not a prerequisite to fixing the game.
Reuse existing original-backed checks; add one only for a concrete fix or
demonstrated behavioural gap.

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
