# Native artwork and contracts

The current game uses Classic human and robot bodies. Logical player A is
human. Player B is a robot in one-player mode and human in two-player mode.
Blue and Red follow logical ownership across court-end changes. Demo takeover
keeps the same roles. Pose geometry, physics and the frozen recording remain
unchanged.

`classic-generated-masks.png` is the retained ImageGen source. It is not a
runtime atlas. Body masks were sampled at native size and clipped to the
retained pose bounds. The original one-pixel edges preserve seams, wrists and
feet. White rackets, pose offsets, animation, ball, shadow and court remain
Sega-derived. The composite assets are not claimed to be clean-room work.

The native atlas contains 24 human body masks and 24 robot body masks. Both
pose tables cover all 14 poses with the same racket references and offsets.
The robot masks add 3,072 bytes. The robot pose table adds 112 bytes.
Unused logo slots 28–30 are blank. The old court logo rectangle is also blank.

The independent contracts remain test inputs. Do not regenerate them from the
implementation to fix a test failure.

| Contract | Purpose | Consumer |
| --- | --- | --- |
| `native-contract.json` | Original court pixels outside approved edit regions; racket, pose, animation and physics hashes | `test_classic_players.py`, `test_scoreboard_assets.py` |
| `square-led-contract.json` | Selected point-score pixels, captured before implementation | `scripts/native_square_scores.py` and native startup checks |
| `score-layout-contract.json` | Fixed score cells, role labels and closed frame geometry | Classic and scoreboard host tests |

See [score layout](score-layout.md), [square LED scores](square-led.md) and
[title layout](title-side-layout.md) for the current artwork rules.

Historical branch reports and static review PNGs are in Git history. They
show earlier artwork and do not certify the current product. The retained
ImageGen source preserves authoring provenance. Current native validation uses
actual assets and emulator output. See [native acceptance](../../tests/README.md).
