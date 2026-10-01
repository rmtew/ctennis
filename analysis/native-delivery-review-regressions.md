# CT10 independent-review repair

PR11 remains draft and unmerged. This record supersedes any earlier description
of the six affected guards as historical or harmless observer gaps.

Independent comparison proved all six guards passed master41b9e16. Previous
head2da9460 broke moving-prefix pixels and first-complete-raster observation for
upper serve and status lifecycles2–5. Ordinary matches and semantic replay counts
did not override those failures.

## Native publication boundary

The old early-window cutoff admitted publication at frame694, line29:h109.
The unchanged moving-prefix check failed generation471, pixel(83,33): black
expected, purple actual. The captured image showed sprite stream corruption.
Pinned Copperline source `src/bus.rs` defines PAL sprite DMA first active line25
(`PAL_SPRITE_DMA_FIRST_ACTIVE_VPOS = 0x19`); `bus/frame_capture.rs` describes its
control-word fetch and beam-time data reads before visible bitplanes.

The native cutoff is now24, leaving a line before sprite header DMA, rather than
43 before visible bitplanes. VHPOSR's low8bits also admit physical late-blank
lines256–279 and exclude280–311. That narrower late window is deliberate; these
wrapped lines are not claimed to be early-frame positions. Existing ordinary
cadence checks cover the change. Both the nonstopping observer and receipt proof
reject court publication at actual physical lines25–235. Static title selection
retains the visible-bitplane boundary and is independently identified.

## Actual prepared scene and complete scanout

The captured-phase observer records native preparation at a zero-byte label:
actual started callback, back bank, scene objects and prepared fields. Publication
must select the latest completed prepared bank. Frozen/menu service callbacks can
advance without preparing a new court, so the prepared epoch may lag the service
counter. It may never exceed the completed counter.

Returned title selects an independent static asset. Its expected address is
resolved from the actual LoadSeg chip-data hunk and compiled title symbol; the
native title flag does not grant arbitrary bank acceptance. Result/title/restart
coverage exercises this branch and retains the strict court-bank check.

The first phase callback may publish in late blank for the next frame. The
observer waits for that actual scene's first full scanout, bounded to three
frames, instead of capturing the preceding unassociated raster. It does not
write game state, alter expected pixels, or enable logging to hide timing.

## Exact upper-serve original raster

The old base PASS requested callback4131 but selected generation4130, original
hardware5429/pixel5431. The corrected observer selects actual generation4131.
Its original hardware sample5430 existed, but the frozen media lacked the next
validated raster. Different SAT bytes forbid substituting generation4130.

The existing capture/freezing tools now supply one separate bounded supplement:
`tests/cases/presentation-upper-serve-generation-4131.json`. Nine adjacent source
samples are captured twice, and both runs preserve the complete frozen original
callback recording. The independent static-hardware/captured-pixel validation
associates **generation4131 → hardware5430 → pixel5432**. Primary manifests,
primary media, source replay and the declared upper-serve recipe/checkpoint/region
remain unchanged. The runner selects this supplement only for that exact missing
checkpoint, including its existing sprite mutation. Provenance includes the
supplement recipe, manifest, validation, captured files and generator tools.
Private samples remain ignored; expected images are actual original-emulator
captures, not a manufactured renderer or rebaseline.

## Status and progress integrity

Status lifecycles2–5 preserve their original35 callback comparisons/3 rasters.
Their existing retain/early-expiry controls now fault the maintained selector in
`scene_fields.s`, in a private diagnostic wrapper. The previous wrapper mutation
hit the unrelated returned-title clear; its failure is retained, not called a
product pass. Maintained sources are never modified for these faults.

The status runner now uses the existing atomic run-start/final provenance wrapper.
Missing/interrupted/failed latest invocations cannot retain an old successful
receipt. CT10 explicitly requires all six repaired guard receipts. Its package/
cold-boot branch preserves the initial conjunction instead of overwriting it.
Declared timing/pixel/fault extent is checked as well as freshness and subject.
The finite unit control calls actual progress() with other delivery proofs made
positive; each of six guards being failed/stale/interrupted/unrun blocks CT10.
A separate altered raw receipt with court publication at line29 is rejected by
the actual cadence validator; no actual receipt or game state is rewritten.

## Evidence and limits

Exact fresh commands, start/completion times, exits and log fingerprints are
retained privately in `build/ct10/review-regressions/final-review-commands.json`.
The newest WORKLOG entry records final results and hashes. Earlier failure logs,
failed latest-invocation receipts and the checkpoint are retained in that folder.
The historical99-case aggregate remains failed; it is not rerun or promoted.

This repair does not implement keyboard hints/centering/font options, claim all
ordinary frames equal the original, or measure pre-Exec-pool bootstrap RAM peak.
Copperline is the user-approved target; other hardware/emulators were not tested.
Final source/runtime independent review and merge authorization remain separate.
