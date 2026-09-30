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
and [agent instructions](AGENTS.md): establish the maintained product boundary,
then complete mode selection, physical controls, serve/rally, rounds, results,
native graphics/sound, ordinary full-play verification and a bootable ADF.
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
