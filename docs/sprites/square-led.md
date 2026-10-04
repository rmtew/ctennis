# Square LED point scores

The user selected the square LED design from Library preview
`libfile_154a4a5e61f48191b284c13acd5b18aa`, version 0. The selected pixels include
a right-aligned zero, a single A and a blank opponent score. State indices
0–6 mean 0, 15, 30, 40, A, 40 and blank. See [score layout](score-layout.md)
for the current cell positions.

The 48-byte native definition contains 28 rectangle bytes, six character
segment masks and 14 state selectors. Startup constructs six unique point
masks and the WIN mask before the simulation clock starts. The current game
uses three fixed HUD strips. Earlier stored point-bank allocations are retired.

`square-led-contract.json` contains 224 expected pixel bytes sampled from the
selected preview before native implementation. The source preview SHA256 is
`4508697e2cc7999b151d38cff4270bf5bebc9da76c77511245756ff17e9ec7df`.
These expected pixels are independent test inputs. The product does not load
them. Do not regenerate them from the runtime implementation.

Run the focused checks from the repository root:

```sh
python -m unittest discover -s tests/unit -q
python scripts/native_assets.py
RUST_LOG=info python scripts/run_native_square_startup.py --self-test
RUST_LOG=info python scripts/run_native_scoreboard_tests.py --self-test
```

The startup check compares every generated mask byte. A compiled fault moves
the advantage glyph and must fail the independent comparison. The scoreboard
check covers seven point/tally states, both controller modes and both ends.
It checks actual panel pixels, all three banks and a wrong WIN-mask control.
These focused checks do not establish a complete native acceptance pass.
