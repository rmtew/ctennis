# Native upper-serve graphics comparison

`p1-upper-serve` compares actual completed Amiga rasters with independently
captured original-game pixels. It adds the upper serving end beyond the first
round failure, without recapturing an equivalent source sequence or changing
product code. The finite set is windup, first advancing flight and early flight.
This completes those local comparison checkpoints, not all P1 coverage.

## Reachable initial state and output scope

The test starts once at source callback 4110 using the validated
`one-player-upper-resumed-serve-complete-phase` initial post-tail state. Its
parent is the unchanged full one-player reference. The phase validator rebuilds
the fixture from its parent and recipe; an altered snapshot is rejected.
The temporary executable changes only its initial RAM and diagnostic callback
counter. Subsequent native routines, input sampling, scheduling, sprite upload,
Copper preparation and blanking commits use the existing live application.
Recorded source entropy is consumed at its original global callback index.
No expected intermediate state or graphics writes are injected.

The capture adapter rejects targets beyond the independently validated phase.
The report hashes the initial phase, native executable, source, emulator,
bridge, ROM and presentation references. Three requested callback stops compare
native RAM against original post-tail RAM, excluding only existing callback
pointer bytes. All three match. An out-of-phase target and an altered initial snapshot were
rejected in negative validation checks. This is local state parity, not proof the
native application reached callback 4110 through the round transition.

The compared rectangle is x48..207, y0..71: the upper court, serving player and
ball. Score/mode/status fields are excluded because the independent phase does
not initialize the renderer's prior field selections. Those fields remain
separate required comparisons. This rectangle is fixed in the public case;
no mismatch-derived masking, image fitting or interpolation is permitted.

## Completed raster associations and failure

| Requested callback | Actual displayed generation | Verified original pixel frames |
|---:|---:|---|
| 4111 | 4111 | 5407..5412 |
| 4128 | 4128 | 5429 |
| 4131 | 4130 | 5431 |

Displayed generations come from actual blanking commits and completed physical
beam wraps. The final requested stop displays generation 4130, not the most
recent completed simulation callback. Source association uses captured active
callbacks and uploaded sprite bytes, then verified raster/VDP associations.
All candidate original rasters must be identical. The original captured pixels
remain the oracle; static hardware decoding does not manufacture an expectation.

The first difference is generation 4111 at logical x57/y1: expected black,
actual white. The source's white pixels on that row are x77/78; native white
pixels are x57/58. This confirms the existing 20-pixel sprite origin error at
the opposite serving end with matching simulation state. The other checkpoints
also retain sprite placement differences. The exact first signature is public
in `tests/known-failures.json`; a changed failure or unexpected pass fails the
baseline policy.

## Sensitivity and verification

With `--self-test`, the runner also assembles a separate private executable in
which the unique sprite x-origin instruction changes from
`ADDI.W #$6c,D0` to `ADDI.W #$6d,D0`. Captures use a separate directory so they
do not overwrite normal evidence. Generation display cases and native audio
cases also retain normal captures in separate case directories, with their
capture-report paths and hashes, preserving earlier suite evidence. Simulation state still matches at all three
checkpoints. Every compared raster detects the actual hardware rendering
change; its first differing x moves one pixel. Normal source/executable remain
unchanged. Pixel-comparator sensitivity is also checked independently.

Run `python scripts/run_presentation_tests.py --case p1-upper-serve --self-test`.
The case returns 1 with an actual measured known-red report, not a tool error.
The aggregate runner registers this case and applies exact failure policy and
self-tests. Native/source screenshots and logs remain ignored private artifacts.

Stop equivalent upper-serve-start windows. Upper handoff/release display,
returns, remaining court outcomes, field variants and later transitions remain
open in P1. Prefer those distinct outputs next; do not duplicate the already
measured placement defect with arbitrary extra frame targets. P2 and P3 remain
separate acceptance requirements.

The complete aggregate baseline/self-test subsequently completed all 64 cases:
39 green, 25 exact known red, no unexplained differences or tool errors. Four
missing requirement groups keep the suite failing. After completion, retained
capture-report hashes and screenshot existence for all three generation display
cases and capture-report/WAV hashes for all three audio cases were verified;
all six evidence directories remain distinct.
