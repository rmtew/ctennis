# Movement boundaries and current regression evidence

The annotated source uses two four-row bounds tables at ROM `$144D` and
`$147C`. Animation bits 5–6 select the row; animation bit 7 or point-outcome
bit 2 suppresses movement. Accepted movement attempts use steps of one and two
alternately, from the interrupt counter's prior parity. Positive steps must
remain strictly below their table limit; negative steps may equal it. There is
no clamp: a rejected step leaves the coordinate unchanged.

| Player | Row | Inclusive Y range | Inclusive X range |
|---|---:|---:|---:|
| Lower | 0 | 152–153 | 128–199 |
| Lower | 1 | 152–153 | 40–111 |
| Lower | 2 | 128–153 | 40–199 |
| Lower | 3 | 98–153 | 40–199 |
| Upper | 0 | 7–9 | 80–111 |
| Upper | 1 | 7–9 | 128–159 |
| Upper | 2 | 7–31 | 64–175 |
| Upper | 3 | 7–62 | 64–175 |

These are allowed destination ranges, not proof that every destination occurs
in every phase. A two-byte Y range explains why a held direction sometimes
does nothing even though movement is enabled. Opposing direction bits are
processed sequentially; this capture deliberately uses one direction at a time.
Mode bit 4 exchanges the players' controller nibbles, as documented in
[the physical input map](two-player-input-map.md).

## Captured and compared initial row

`movement-serve-bounds` selects two-player mode from reset, leaves fire released,
and moves both players through down/up/down and right/left/right holds. The
frozen policy writes only physical controller fields. Both captures agree
exactly: 742 consecutive gameplay callbacks, no PSG writes, no refresh reads
or between-callback RAM changes. The complete case passes against the assembled
routines shared with the application: 254 bytes at entry, pre-tail and return.
This is simulation/input-reader replay evidence, not ordinary native joystick
sampling or display timing acceptance.

`scripts/movement_reference.py` verifies eight player/direction observations:
actual approach, eight stopped attempts covering both step sizes, then four
accepted reversal attempts with a coordinate response. Relevant animation,
mode, point-block and consumed direction values are checked. Narrow vertical
ranges need not move on all four reversal attempts. A neutral interval between
holds remains in the continuous replay.

| Direction | Approach/hold callbacks | Four reversal callbacks |
|---|---:|---:|
| Down | 21–124; stopped 117–124 | 141–144 |
| Up | 141–244; stopped 237–244 | 261–264 |
| Right | 381–484; stopped 477–484 | 501–504 |
| Left | 501–604; stopped 597–604 | 621–624 |

Source raw capture SHA256:
`352b2a0849c138140d92f41ab7b60253129b5ceba5bc9d514652c3f24129d22e`.
Frozen fixture SHA256:
`9741dfe015d72e6db81bff5e624431521273f4463f179669d50e048a8bd9f711`.
Private raw streams, logs and validation report remain in
`build/tests/movement-serve-bounds-capture/`; source-derived data stays ignored.

Reproduce with:

```text
python scripts/capture_test_reference.py --case movement-serve-bounds
python scripts/run_regression_tests.py --case movement-serve-bounds --self-test
python scripts/inventory_match_references.py
```

The deliberate native lower-X increment is detected at callback 1, pre-tail,
sprite record 1 X: expected 192, actual 193. Temporary mutated source and
executable are removed. An altered source held-direction observation is also
rejected by the behavioural evidence validator.

## Remaining F1 work

Rows 1–3 for each player still need approach/hold/reversal evidence. Existing
R2 post-body observations include all four unblocked animation row selections,
but that alone does not establish their bounds, movement inputs or the exact
row used earlier within the callback. Read the phase/reset/trajectory writers
and index intervals before collecting missing sequences. Preserve the existing
continuous matches and the new independent case; do not manufacture animation
flags or substitute the old Python movement model for original-game evidence.
