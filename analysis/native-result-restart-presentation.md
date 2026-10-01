# Native result/title/restart acceptance (CT06)

The maintained dispatcher now finishes a match, requests its result cue, returns
through the original title transition, and reuses the native mode selection to
restart. `amiga/game/result.s` owns that lifecycle; `result_adapter.s` explicitly
retains the existing audio stream ABI pending CT08. The display bridge remains
CT07 debt. Ordinary restart clears scores, mode/end state and pending phases.
Per-player action latches suppress buttons inherited through selection until each
physical button is released. Normal rally holds and direction input are preserved.

The application and replay use the same dispatcher and main/service paths.
A local phase initializes once from captured original conditions; it does not
inject subsequent source writes or choose dispatch by source PC. Ordinary runs
boot at the title and use real physical inputs without captured initialization.

| Local scene context | Initial callback | Tally | Result | Title | Selection | Court | Flight |
|---|---:|---:|---:|---:|---:|---:|---:|
| One player |11959|11964|12090|12286|12540|13362|13381|
| Two players |25618|25623|25749|25945|26199|27021|27040|

Each existing scene case compares all 1422 consecutive maintained observations,
six full 256x192 viewports and 36 crops, plus ordered logical PSG/entropy events.
Both normals pass these complete comparisons. Each retains all three actual
compiled sprite/field/extra-refresh faults and rejects them at a later observable
checkpoint while preserving the normal state sequence and early images.
The two existing maintained match-complete phases separately match 1451/1451
updates each. These captured phases are not ordinary full-match comparisons.

Semantic state acceptance uses the existing CT04 contract: 250 bytes, omitting
exactly C067–C06A retired arithmetic scratch. Separate 254-byte raw diagnostics
remain red: one-player first C067 at 13377 (expected57/actual0), two-player first
C067 at 27019 (expected43/actual0). No source fixtures, pixel tolerances or event
expectations were rebaselined. The two obsolete result semantic known-red
policies are removed; the raw mismatch is still reported explicitly.

## Diagnostic timing, separate from gameplay

The two-player field fault originally targeted callback 27021 but observed the
bank prepared at 27020. Poisoning at threshold27020 affected only the next bank;
its first visible mismatch occurred at27040. The retained before artifacts are
`build/ct06/field-timing-before/`. The diagnostic now poisons before generation
27020 is built (compiled threshold27019). The unchanged intended checkpoint27021
therefore detects point_b pixel(227,45), black versus7777ff. One-player likewise
uses threshold13360 for unchanged checkpoint13362. Machine assertions and
compiled-source/executable hashes are in `build/ct06/field-timing-after.json`.
This changes fault activation only, not normal gameplay, reference checkpoints
or the strict comparison. Sprite faults use the visible selected-court checkpoint
(result sprites are hidden); extra-refresh faults use the final flight checkpoint.

## Ordinary target evidence

Both modes start from an ordinary title boot, run continuously through the match
award and title return, select the opposite mode, and reach a restarted serve.
Both red buttons remain held across result/title/selection. Eighty callbacks at
the restarted serve prove physical raw bits16+16 are filtered to zero actions and
the ball remains stationary. After releasing both buttons for80 callbacks, a fresh
player1 press launches advancing flight. The existing two commands record only
actual lifecycle/score checkpoints, checking callback continuity throughout.

The final ordinary executable SHA256 is
`80b16463f5673f033241a10333ed38a6157f5d986b54e45f2d75cda5efff56fa`.
One→two records11807 consecutive observations; two→one records23753.
These are ordinary lifecycle/action acceptance, not original full-match parity.
The actual logs use PAL A500/68000/OCS/512KB chip/no expansion/Kickstart1.3,
with `RUST_LOG=info`.

```sh
RUST_LOG=info python scripts/run_result_presentation_tests.py --case=p1-one-player-result-restart-scenes --self-test
RUST_LOG=info python scripts/run_result_presentation_tests.py --case=p1-two-player-result-restart-scenes --self-test
RUST_LOG=info python scripts/run_regression_tests.py --subject=maintained --case=one-player-match-complete-phase
RUST_LOG=info python scripts/run_regression_tests.py --subject=maintained --case=two-player-match-complete-phase
RUST_LOG=info python scripts/run_ordinary_round_tests.py --mode=one --match
RUST_LOG=info python scripts/run_ordinary_round_tests.py --mode=two --match
RUST_LOG=info python scripts/progress.py
```

Root reports in ignored `build/tests/` contain atomic run state and source,
executable, reference, tool and exact-target provenance. The focused progress gate
requires full extent, semantic/raw labels, all three real faults, ordinary start,
ordered lifecycle, held-action proof and the current ordinary executable. It does
not count translated diagnostics or source integration as runtime acceptance.
Dependency discovery follows primary media's declared children and the recipe's
supplemental directories, avoiding an invented absent primary restart child while
still invalidating missing actual declared media.

Affected guards are maintained serve200, round-transition1566, both existing mode
checks and the ordinary build. Focused integrity unit checks reject wrong subject,
short extent, expanded scratch, missing faults, wrong executable, unordered/local
ordinary evidence and old-pass retention after failed/interrupted setup.

Cadence, peak chip RAM, ADF boot, Paula waveform equivalence and independent
exact-head validation remain unverified here. CT07/CT08 still own display/audio
bridge removal; CT09 still owns complete reference-matched uninterrupted play.
CT06 is ready for independent review only when the final machine progress report
shows all required current evidence; it is not merged or independently verified.
