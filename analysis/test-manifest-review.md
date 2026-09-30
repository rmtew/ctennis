# Test manifest relevance and coverage review ? 2026-10-01

The suite has useful original-backed protection, especially the continuous rally,
scoring sequence, movement limits, green field/status comparisons and actual
compiled output fault controls. It is not yet sufficient to support unrestricted
rewriting of a maintained Amiga core. The highest-value next proposals strengthen
existing test execution and acceptance, rather than collect more scene variants.
This review implements no candidate and makes no product changes.

## Material coverage corrections

1. **Test subject and dispatch.** `prepare_gameplay()` regenerates translated
   routines on each build. `simulation_harness.s` calls the gameplay sequence
   every iteration and then its tail; it never dispatches from the original
   callback kind. All 56 core cases use this harness. Their original tail-regime
   references expose mismatches but do not test the maintained application's
   actual dispatcher. Hardware cases exercise maintained integration code with
   that regenerated core. C19 proposes a shared maintained gameplay/dispatch
   boundary; translation conformance remains a useful distinct tier.

2. **Known-error masking.** The current classifier accepts 35 of47 known-red
   cases solely from their first signature. Eight require a complete observation
   digest; four require an explicit complete state/output interval. First-only
   acceptance is appropriate only for the protection actually asserted; later
   retained observations cannot be credited as gated regression protection.
   Copied-report controls added a later mismatch to moving-prefix, physical-input
   and first-pitch reports: all remained known red. Changing a late pixel in a
   complete round digest became unexpected red. These are classifier controls,
   not new emulator fault captures; retained reports were not edited. C21 targets
   existing relevant multi-observation cases, not every single-observation red.

3. **Reference length versus proven native extent.** R1 currently matches1332
   callbacks and executes1333 of13378 retained source callbacks. R2 matches2535
   and executes2536 of27037. The restart extensions stop at the same earlier
   mismatch. Local hardware round/result cases provide valuable separate later
   observations; they do not establish ordinary complete-match continuity.
   The manifest now shows matched/executed/reference extents for every core case.

4. **Representation versus observable behaviour.** Full RAM equality is strong
   evidence for the translated representation but binds the port to original
   layout and flags. C20 proposes original-derived named observations that survive
   a correct internal rewrite. It does not propose a Python game model, abandon
   existing oracles or remove raw-state translator diagnostics.

5. **Action timing meaning.** The upper action set retains accepted returns in
   all three cases. Before/at action produce the same changed shot vector; after
   action preserves the baseline vector. This tests action-dependent shot choice,
   not hit/miss acceptance. Lower-action expansion is conditional until a missing
   distinct outcome is established. Contact geometry remains an audit candidate.

6. **Avoid fidelity expansion without a requirement.** Emitted pitch/relative
   level can matter; reproducing an emulator's filter, exact waveform phase or
   sample bytes is not an established requirement. C13 now requires an output
   fault escaping current protection; C14 needs an explicit presentation policy.
   Return/bounce/net/out raster additions likewise need an event-specific fault
   that escapes existing placement/generation checks. Active noise is unsupported
   by the retained original gameplay and remains a skip proposal.

7. **Overlap can be useful for diagnosis.** Short scoring boundaries overlap the
   continuous deuce sequence, and the placement crop overlaps the first moving
   viewport. They are localization aids, not additional requirements protected.
   Retain them while useful; do not multiply equivalent variants. The green
   score/status prefix remains independently valuable behind a red whole viewport.

## Worthwhile open protection

Physical controls causing actual gameplay and correct ownership after exchange;
ordinary source-rate cadence and complete-match deadlines; distinct audible effect
classes and their timing; accepted-mode display tied to the correct generation.
Court/random/contact expansion first needs an index of unique effects and existing
matched intervals. Source evidence containing an event is not native protection.
C19/C21 and the observable contract address weaknesses in how those behaviours
would be protected, before adding more cases behind existing failures.

## What changed and what was verified

Updated `tests/test-manifest.json` and regenerated `tests/TEST-MANIFEST.md`.
Twenty families still enumerate all99 registered cases exactly once. Every case
has current retained classification and known-failure acceptance strength; core
rows also expose actual comparison extent. Candidate decisions are now11 worthwhile
(including three improvements to existing-suite assurance), eight audit-first,
one duplicate skip and one unsupported skip. These are proposals for scope review.

Inspection covered the registry/classifier, core build and harness, phase/source
validation, contact assertions, presentation/round comparisons, physical input
comparisons, audio assertions and all retained native reports. No fresh emulator
run or full source-integrity recapture was necessary to establish these findings.
Original references remain the independent oracle; no goal completion is claimed.
