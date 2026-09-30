# Test manifest

Review source: [test-manifest.json](test-manifest.json). Rebuild this document with `python scripts/render_test_manifest.py`. Every registered test belongs to exactly one family; recipes define individual scope. Candidates have stable IDs for discussion.

**Evidence snapshot (2026-10-01):** classifications below come from retained reports, not a fresh suite run. 52 green, 47 known-red. Green applies only to the stated scope. Known red means a test exists and exposes a reviewed implementation defect. Neither status closes other requirements.

## Candidate review

Priority is a recommendation for review, not an instruction to implement. Audit-first candidates must establish additional regression protection before capture. Prefer extending existing cases and reusing original evidence. Effort estimates are relative, not elapsed-time promises.

| ID | Candidate | Decision | Priority | Effort |
| --- | --- | --- | --- | --- |
| C01 | [Lower return action timing](#c01) | worth implementing | high | medium |
| C02 | [Serve action acceptance](#c02) | audit first | high | low audit; medium if gap |
| C03 | [Geometric contact edge](#c03) | audit first | medium | medium |
| C04 | [Court outcome to point attribution](#c04) | audit first | high | low audit; medium if gap |
| C05 | [Random decisions affecting play](#c05) | audit first | medium | low audit; medium if gap |
| C06 | [Physical input causes player/action response](#c06) | worth implementing | high | medium |
| C07 | [Physical control ownership after side exchange](#c07) | worth implementing | high | medium |
| C08 | [Input sample boundary and latency](#c08) | worth implementing | high | high |
| C09 | [Ordinary callback cadence and deadline](#c09) | worth implementing | high | medium |
| C10 | [Ordinary complete-match continuity](#c10) | worth implementing | high | high |
| C11 | [Remaining sound event classes](#c11) | worth implementing | high | medium |
| C12 | [Sound onset and duration](#c12) | worth implementing | high | high |
| C13 | [Emitted pitch/envelope and waveform fidelity](#c13) | worth implementing | medium | medium |
| C14 | [Stereo routing/filter policy](#c14) | audit first | medium | low decision; medium verification |
| C15 | [Generation-aligned accepted-mode image](#c15) | worth implementing | medium | medium |
| C16 | [Return/bounce/net/out rendering](#c16) | audit first | medium | low audit; medium if gap |
| C17 | [More movement, upper timing, status, round, result and mute variants](#c17) | skip as duplicate | none | none |
| C18 | [Active noise effect](#c18) | skip as unsupported | none | none |

### C01

**Lower return action timing — worth implementing.**

- Missing behaviour: Lower-player shot/action outcome around contact.
- Plausible regression: Using upper action rule or sampling action a callback late.
- Independent expectation: Original reachable lower contact with legitimate before/at/after action captures.
- Stop when: Distinct original action outcomes and subsequent flight compared; equivalent outcomes share one case.
- Existing protection/overlap: I09 covers ordinary lower returns; I10 only upper action edge.
- Work: Focused source capture and existing core runner extension.
- Evidence readiness: New focused source evidence required.
- Dependencies: Existing I09 rally and I10 action-boundary harness.

### C02

**Serve action acceptance — audit first.**

- Missing behaviour: Held/released/early action acceptance around serve handoff.
- Plausible regression: Premature launch, stuck serve or double acceptance.
- Independent expectation: Original serve phases and, only if absent, adjacent legitimate action timings.
- Stop when: Every distinct serve action outcome protected through first flight.
- Existing protection/overlap: I01/I07 already cover several serves; identify absent outcome before capture.
- Work: Index existing serve inputs/outcomes first.
- Evidence readiness: Existing evidence requires audit.
- Dependencies: Audit I01/I07 first.

### C03

**Geometric contact edge — audit first.**

- Missing behaviour: Adjacent reachable hit/miss positions at contact.
- Plausible regression: Off-by-one collision/contact range.
- Independent expectation: Original legitimate adjacent player positions; hit/miss and point records.
- Stop when: One pair per genuinely distinct lower/upper contact rule.
- Existing protection/overlap: I09 accepts returns but does not deliberately bracket collision bounds.
- Work: Source edge discovery and core comparisons.
- Evidence readiness: New reachable edge evidence likely needed.
- Dependencies: C04 contact/outcome inventory and reachable legitimate controls.

### C04

**Court outcome to point attribution — audit first.**

- Missing behaviour: Distinct bounce/net/out rule effects and eventual winning player.
- Plausible regression: Wrong bounce count, net reflection, out classification or scorer.
- Independent expectation: Existing R1/R2 callback/contact/score records.
- Stop when: Index distinct outcomes; add comparison only when existing state streams or fault controls miss one.
- Existing protection/overlap: I01/I09 carry state/points; first mismatch can conceal later outcomes.
- Work: Map event to trajectory/flags/point, then choose missing local interval.
- Evidence readiness: Original full records present; semantic indexing incomplete.
- Dependencies: Audit I01/I09 full-state extent and local-failure masking.

### C05

**Random decisions affecting play — audit first.**

- Missing behaviour: Refresh decision changes AI target/trajectory.
- Plausible regression: Ignoring entropy or applying its sign to wrong target.
- Independent expectation: Original consumed refresh choices and following reachable target/flight state.
- Stop when: Distinct observed effects linked to existing comparisons; add only meaningful absent outcome.
- Existing protection/overlap: I01/I07 compare state; observing both bits alone insufficient.
- Work: Index choice-to-effect and use declared entropy seam only if necessary.
- Evidence readiness: Existing records present; effect mapping incomplete.
- Dependencies: Map original entropy to actual target/trajectory consumers.

### C06

**Physical input causes player/action response — worth implementing.**

- Missing behaviour: Actual native control changes gameplay, not just decoded bits.
- Plausible regression: Correct reader output but wrong consumer/player/action.
- Independent expectation: Original control calibration plus reachable movement/serve/contact outcomes.
- Stop when: Representative direction/reversal/action response per distinct consumer; no exhaustive repeated bit matrix.
- Existing protection/overlap: I14 ends at readers; I08/I09 inject core inputs.
- Work: Extend actual hardware capture to consequent state.
- Evidence readiness: Original components present; combined windows need definition.
- Dependencies: I14 physical calibration; preserve known second-reader defect.

### C07

**Physical control ownership after side exchange — worth implementing.**

- Missing behaviour: Pads control correct players after round exchange.
- Plausible regression: Keep initial pad ownership or swap twice.
- Independent expectation: Original later movement and round records with pad ownership.
- Stop when: Each distinct ownership regime has a physical response comparison.
- Existing protection/overlap: I05 core phase and I14 initial ownership do not close integration.
- Work: One continuous or explicitly local physical exchanged-side window.
- Evidence readiness: Original later states present; native physical window needed.
- Dependencies: C06 response harness and original exchanged-side record.

### C08

**Input sample boundary and latency — worth implementing.**

- Missing behaviour: Input edge consumed on correct source update independent of presentation.
- Plausible regression: Sample twice, lose an edge, or tie action to video frame.
- Independent expectation: Original input-read epochs and source schedule; explicit Amiga host mapping.
- Stop when: Before/after edges for distinct direction/action consumers and bounded latency under ordinary scheduling.
- Existing protection/overlap: I10 source-core edge; I14 sustained physical windows.
- Work: Ordinary capture with timed physical edge; define epoch/latency criterion.
- Evidence readiness: Epoch mapping and precise edge scheduling needed.
- Dependencies: C09 clock mapping; precise physical edge scheduling.

### C09

**Ordinary callback cadence and deadline — worth implementing.**

- Missing behaviour: Correct source-rate gameplay/tail/result callbacks during ordinary execution.
- Plausible regression: One callback per PAL frame, accumulate drift, skip/update twice, slow wait.
- Independent expectation: Retained original timing baseline and regime intervals.
- Stop when: All distinct regimes plus long interval agree with defined source-rate schedule and no unexplained lateness.
- Existing protection/overlap: Local debugger captures deliberately do not establish cadence.
- Work: Read-only timing instrumentation of ordinary executable, source-rate and deadline assertions.
- Evidence readiness: Source timing evidence present; ordinary native measurement required.
- Dependencies: Source timing baseline; ordinary executable trace without single-step scheduling.

### C10

**Ordinary complete-match continuity — worth implementing.**

- Missing behaviour: No visible-line commit or stale/lost graphics/sound across sustained run and restart.
- Plausible regression: Prepare too slowly, publish incomplete state, lose event or leak state across round.
- Independent expectation: Original R1/R2 event/state progression; Amiga blanking hardware invariant.
- Stop when: Both control modes cover award, wait, resume, result and restart with deadlines and no visible commits.
- Existing protection/overlap: I18/I20 local scenes; I01 may stop early.
- Work: Ordinary run with compact commit/event trace; retain checkpoints rather than every frame.
- Evidence readiness: Original progression present; native run can expose current known failures.
- Dependencies: C09 trace and C11 sound-class inventory; current product failures remain recorded.

### C11

**Remaining sound event classes — worth implementing.**

- Missing behaviour: Native emitted upper serve/returns/point/round/result/restart effects.
- Plausible regression: Wrong event dispatch/channel, truncated result phrase or missing resumed sound.
- Independent expectation: Retained original named audio intervals and PSG streams.
- Stop when: First inventory distinct event/envelope/channel combinations; one actual output comparison per unique class.
- Existing protection/overlap: I13 first serve; I20 logical PSG does not prove Paula output.
- Work: Group retained 18 intervals by actual effect and extend audio runner.
- Evidence readiness: Original recordings present; effect grouping and native windows needed.
- Dependencies: Inventory retained original audio intervals; no prerequisite product fixes.

### C12

**Sound onset and duration — worth implementing.**

- Missing behaviour: Sound begins/ends in relation to source event schedule.
- Plausible regression: Delayed audio update, skipped phrase or extra tail after transition.
- Independent expectation: Original timed commands and measured audible boundaries.
- Stop when: Distinct scheduling regimes have defined onset/end criteria with justified clock/sample mapping.
- Existing protection/overlap: I13 signal/silence has wide windows; not exact onset/decay proof.
- Work: Align audio samples to event trace and measure boundaries before asserting tolerance.
- Evidence readiness: Original audio present; exact native sample/clock alignment needed.
- Dependencies: C09 clock mapping and C11 effect inventory.

### C13

**Emitted pitch/envelope and waveform fidelity — worth implementing.**

- Missing behaviour: Audible conversion matches intended pitch/relative envelope beyond registers.
- Plausible regression: Wrong waveform period/content, level handling or quantization.
- Independent expectation: Measured original WAV plateaus/frequency plus explicit native clock and integer quantization.
- Stop when: Independent waveform measurements reject pitch/level/data faults for distinct relevant effects.
- Existing protection/overlap: I13 register pitch/envelope known reds; bounded presence alone weak.
- Work: Extend existing audio cases with actual measurements and documented mapping.
- Evidence readiness: Original and first native WAVs present; fidelity criterion needs definition.
- Dependencies: Existing I13 audio measurements and explicit waveform mapping.

### C14

**Stereo routing/filter policy — audit first.**

- Missing behaviour: Documented native channel balance and filter treatment.
- Plausible regression: Accidentally silent side, cancellation, or unintended filtering.
- Independent expectation: Original mono output and explicit intended Amiga mapping; original alone cannot prescribe stereo.
- Stop when: Agree presentation policy, then test channel contributions and stable filter behaviour once.
- Existing protection/overlap: I13 per-channel silence prevents cancellation but does not specify balance.
- Work: Choose fidelity policy before measuring acceptance.
- Evidence readiness: Design decision needed; do not invent source-equivalent stereo requirement.
- Dependencies: Agree intended Amiga stereo/filter presentation.

### C15

**Generation-aligned accepted-mode image — worth implementing.**

- Missing behaviour: Accepted physical mode produces correct stable mode/court display.
- Plausible regression: Correct flag with stale title or wrong mode image.
- Independent expectation: Original accepted-mode generation and completed raster.
- Stop when: Extend both existing mode cases to aligned accepted image with stale/wrong-mode control.
- Existing protection/overlap: I19 exposes selection failures; its timed final screenshot is diagnostic.
- Work: Extend existing cases, not add two duplicate selection cases.
- Evidence readiness: Original image present; native acceptance absent is known failure, not excuse to claim coverage.
- Dependencies: Extend I19; classify missing acceptance as known red.

### C16

**Return/bounce/net/out rendering — audit first.**

- Missing behaviour: Specific ball/frame/shadow update unique to outcome event.
- Plausible regression: Only if named: freeze post-contact ball, wrong reflected frame, or stale shadow while earlier sprites remain correct.
- Independent expectation: Original uploaded sprite/VDP state and associated event/next completed raster.
- Stop when: For each unique missing render transition, prove targeted late fault rejection; skip if current images catch it.
- Existing protection/overlap: I12/I18 catch generic sprite origin and stale generations; I09 core trajectories.
- Work: Inspect current render contract and checkpoints first, reuse original media.
- Evidence readiness: Original event rasters present; unique missing fault not yet established.
- Dependencies: Audit I12/I18 checkpoint protection; name an escaping render fault.

### C17

**More movement, upper timing, status, round, result and mute variants — skip as duplicate.**

- Missing behaviour: No demonstrated additional requirement.
- Plausible regression: Existing equivalent fault already caught.
- Independent expectation: Existing original-backed comparisons.
- Stop when: Reopen only with named distinct regression escaping current tests.
- Existing protection/overlap: I03/I08/I10/I13/I16/I17/I18/I20.
- Work: No implementation proposed.
- Evidence readiness: Sufficient existing variants; no new evidence needed.
- Dependencies: None unless new distinct fault escapes current protection.

### C18

**Active noise effect — skip as unsupported.**

- Missing behaviour: No active gameplay noise requirement observed.
- Plausible regression: Invented effect would test behaviour not present in game.
- Independent expectation: Retained original R1/R2 audio noise remains muted.
- Stop when: Reopen only if actual original audible noise is discovered.
- Existing protection/overlap: Original audio inventory explicitly records muted noise.
- Work: No implementation proposed.
- Evidence readiness: No original evidence for active effect.
- Dependencies: Actual original audible-noise evidence.

## Implemented tests

The four criteria below describe each family. Individual cases inherit them and further narrow their contract in the linked recipe. Existing tests are retained; this inventory proposes no removals.

### I01: Continuous core replays

**Value:** keep.

- Behaviour protected: Serve and continuous R1/R2 state, event order and transitions.
- Plausible regression: Arithmetic, update-order, scoring or dispatch drift.
- Independent expectation: Frozen repeated original callback records.
- Stopping condition: Retain uninterrupted comparisons through their defined endings; known failures remain explicit.
- Limits/overlap: Baseline runs may stop at first known error; full-match references are not proof of full native parity.

| Case and exact recipe | Retained classification |
| --- | --- |
| [serve](../tests/cases/serve.json) | green |
| [round-transition](../tests/cases/round-transition.json) | known-red |
| [one-player-match](../tests/cases/one-player-match.json) | known-red |
| [two-player-match](../tests/cases/two-player-match.json) | known-red |

### I02: Local wait/resume/restart phases

**Value:** keep as diagnostics; review overlap with I06.

- Behaviour protected: Tail dispatch and independent resumed/restarted gameplay.
- Plausible regression: Wrong callback regime or state reset.
- Independent expectation: Slices validated against original continuous parents.
- Stopping condition: One continuous comparison per distinct regime.
- Limits/overlap: One-time local initialization does not establish upstream continuity.

| Case and exact recipe | Retained classification |
| --- | --- |
| [round-tail-phase](../tests/cases/round-tail-phase.json) | known-red |
| [resumed-play-phase](../tests/cases/resumed-play-phase.json) | known-red |
| [match-tail-phase](../tests/cases/match-tail-phase.json) | known-red |
| [restart-play-phase](../tests/cases/restart-play-phase.json) | green |

### I03: Deuce/advantage scoring

**Value:** keep.

- Behaviour protected: Deuce, advantage gained/lost/regained and game award.
- Plausible regression: Wrong scoring transition or accumulated point state.
- Independent expectation: Original continuous deuce sequence and five boundary records.
- Stopping condition: Existing continuous sequence plus boundary localization.
- Limits/overlap: Short boundary cases overlap sequence; do not add equivalent variants.

| Case and exact recipe | Retained classification |
| --- | --- |
| [deuce-enter-phase](../tests/cases/deuce-enter-phase.json) | green |
| [advantage-enter-phase](../tests/cases/advantage-enter-phase.json) | green |
| [advantage-lost-phase](../tests/cases/advantage-lost-phase.json) | green |
| [advantage-regained-phase](../tests/cases/advantage-regained-phase.json) | green |
| [advantage-game-phase](../tests/cases/advantage-game-phase.json) | green |
| [deuce-sequence-phase](../tests/cases/deuce-sequence-phase.json) | green |

### I04: Timer saturation

**Value:** keep.

- Behaviour protected: Reachable shared/status counter saturation.
- Plausible regression: Wrapping instead of saturating or wrong audio cadence.
- Independent expectation: Original reachable timer-boundary snapshots.
- Stopping condition: Retain full-state failure and restricted timer diagnostic separately.
- Limits/overlap: Restricted counter observation cannot establish full-state parity.

| Case and exact recipe | Retained classification |
| --- | --- |
| [shared-timer-saturation-phase](../tests/cases/shared-timer-saturation-phase.json) | green |
| [status-timer-saturation-phase](../tests/cases/status-timer-saturation-phase.json) | known-red |
| [status-timer-observation-phase](../tests/cases/status-timer-observation-phase.json) | green |

### I05: Lower receiver local movement

**Value:** keep.

- Behaviour protected: Receiver limits after side exchange behind an earlier failure.
- Plausible regression: Wrong bound or movement direction on later receiver.
- Independent expectation: Original natural approach/hold/reversal phase.
- Stopping condition: Existing four directional comparisons.
- Limits/overlap: Supplement continuous parents; do not replace them.

| Case and exact recipe | Retained classification |
| --- | --- |
| [movement-lower-receiver-right-phase](../tests/cases/movement-lower-receiver-right-phase.json) | green |
| [movement-lower-receiver-left-phase](../tests/cases/movement-lower-receiver-left-phase.json) | green |
| [movement-lower-receiver-up-phase](../tests/cases/movement-lower-receiver-up-phase.json) | green |
| [movement-lower-receiver-down-phase](../tests/cases/movement-lower-receiver-down-phase.json) | green |

### I06: Complete local awards and result regimes

**Value:** keep.

- Behaviour protected: Award through wait/reset or result/menu/restart.
- Plausible regression: Missing main-thread work, wrong waits, reset or handoff.
- Independent expectation: Validated original uninterrupted award intervals.
- Stopping condition: Both modes and both round ends plus result/restart intervals.
- Limits/overlap: Local starts; native hardware and ordinary continuity checked separately.

| Case and exact recipe | Retained classification |
| --- | --- |
| [one-player-round-lower-complete-phase](../tests/cases/one-player-round-lower-complete-phase.json) | known-red |
| [one-player-round-upper-complete-phase](../tests/cases/one-player-round-upper-complete-phase.json) | known-red |
| [one-player-match-complete-phase](../tests/cases/one-player-match-complete-phase.json) | known-red |
| [two-player-round-lower-complete-phase](../tests/cases/two-player-round-lower-complete-phase.json) | known-red |
| [two-player-round-upper-complete-phase](../tests/cases/two-player-round-upper-complete-phase.json) | known-red |
| [two-player-match-complete-phase](../tests/cases/two-player-match-complete-phase.json) | known-red |

### I07: Independent later serve handoffs

**Value:** keep.

- Behaviour protected: Resumed, upper, restarted and AI-launched serve completion.
- Plausible regression: Wrong serve timer/phase, flight or handoff.
- Independent expectation: Original later serve phases.
- Stopping condition: Existing distinct serve contexts.
- Limits/overlap: AI phase begins after launch; does not establish launch correctness.

| Case and exact recipe | Retained classification |
| --- | --- |
| [two-player-resumed-serve-complete-phase](../tests/cases/two-player-resumed-serve-complete-phase.json) | green |
| [one-player-upper-resumed-serve-complete-phase](../tests/cases/one-player-upper-resumed-serve-complete-phase.json) | green |
| [two-player-upper-resumed-serve-complete-phase](../tests/cases/two-player-upper-resumed-serve-complete-phase.json) | green |
| [two-player-restarted-serve-complete-phase](../tests/cases/two-player-restarted-serve-complete-phase.json) | green |
| [one-player-ai-launched-serve-complete-phase](../tests/cases/one-player-ai-launched-serve-complete-phase.json) | green |

### I08: Movement bounds

**Value:** keep.

- Behaviour protected: Both players, four bound rows, four directions with approach/hold/reversal.
- Plausible regression: Off-by-one limits, reversed directions, failure to resume.
- Independent expectation: Original direct movement-entry/return snapshots.
- Stopping condition: All 32 player/row/direction combinations already represented.
- Limits/overlap: Some continuous parents fail earlier; I05 independently exposes lower receiver.

| Case and exact recipe | Retained classification |
| --- | --- |
| [movement-serve-bounds](../tests/cases/movement-serve-bounds.json) | green |
| [movement-alternate-serve-bounds](../tests/cases/movement-alternate-serve-bounds.json) | green |
| [movement-receiver-right-bound](../tests/cases/movement-receiver-right-bound.json) | green |
| [movement-receiver-left-bound](../tests/cases/movement-receiver-left-bound.json) | green |
| [movement-receiver-up-bound](../tests/cases/movement-receiver-up-bound.json) | green |
| [movement-receiver-down-bound](../tests/cases/movement-receiver-down-bound.json) | green |
| [movement-lower-receiver-right-bound](../tests/cases/movement-lower-receiver-right-bound.json) | known-red |
| [movement-lower-receiver-left-bound](../tests/cases/movement-lower-receiver-left-bound.json) | known-red |
| [movement-lower-receiver-up-bound](../tests/cases/movement-lower-receiver-up-bound.json) | known-red |
| [movement-lower-receiver-down-bound](../tests/cases/movement-lower-receiver-down-bound.json) | known-red |
| [movement-lower-rally-down-bound](../tests/cases/movement-lower-rally-down-bound.json) | green |
| [movement-lower-rally-up-bound](../tests/cases/movement-lower-rally-up-bound.json) | green |
| [movement-lower-rally-left-bound](../tests/cases/movement-lower-rally-left-bound.json) | green |
| [movement-lower-rally-right-bound](../tests/cases/movement-lower-rally-right-bound.json) | green |
| [movement-upper-rally-up-bound](../tests/cases/movement-upper-rally-up-bound.json) | green |
| [movement-upper-rally-down-bound](../tests/cases/movement-upper-rally-down-bound.json) | green |
| [movement-upper-rally-left-bound](../tests/cases/movement-upper-rally-left-bound.json) | green |
| [movement-upper-rally-right-bound](../tests/cases/movement-upper-rally-right-bound.json) | green |

### I09: Consecutive two-player rally

**Value:** keep.

- Behaviour protected: Six accepted returns followed by intentional miss/point.
- Plausible regression: Contact or trajectory drift accumulated across successive returns.
- Independent expectation: Original legitimate control sequence.
- Stopping condition: Existing consecutive rally including both return paths and point.
- Limits/overlap: Does not establish physical Amiga input latency or pixels.

| Case and exact recipe | Retained classification |
| --- | --- |
| [two-player-rally](../tests/cases/two-player-rally.json) | green |

### I10: Upper return action boundary

**Value:** keep.

- Behaviour protected: Before/at/after action timing around an accepted upper return.
- Plausible regression: Action gate changes completed shot or accepts action at wrong epoch.
- Independent expectation: Repeated original action timing captures.
- Stopping condition: Three variants and targeted action-gate mutation already sufficient.
- Limits/overlap: Do not generalise to lower player or geometric edges.

| Case and exact recipe | Retained classification |
| --- | --- |
| [contact-upper-action-before](../tests/cases/contact-upper-action-before.json) | green |
| [contact-upper-action-at](../tests/cases/contact-upper-action-at.json) | green |
| [contact-upper-action-after](../tests/cases/contact-upper-action-after.json) | green |

### I11: Continuous restart extensions

**Value:** keep.

- Behaviour protected: Preserve original full match and extend to restarted serve release.
- Plausible regression: Restart loses state or chooses wrong serve phase.
- Independent expectation: Prefix-validated original replay extensions.
- Stopping condition: Both modes through restarted handoff.
- Limits/overlap: Early native error may block continuous comparison; local phases remain separate.

| Case and exact recipe | Retained classification |
| --- | --- |
| [one-player-restart-complete](../tests/cases/one-player-restart-complete.json) | known-red |
| [two-player-restart-complete](../tests/cases/two-player-restart-complete.json) | known-red |

### I12: Sprite and initial field presentation

**Value:** keep.

- Behaviour protected: Title, sprite placement, lower moving prefix, upper serve and score/status prefix.
- Plausible regression: Wrong sprite origin, generation, ball placement or field bank.
- Independent expectation: Original completed rasters with callback/hardware association.
- Stopping condition: Named launch/flight/point/expiry checkpoints and distinct upper serve.
- Limits/overlap: Court outcome images remain conditional; do not duplicate general sprite-origin protection.

| Case and exact recipe | Retained classification |
| --- | --- |
| [p1-title](../tests/cases/p1-title.json) | known-red |
| [p1-upper-player-placement](../tests/cases/p1-upper-player-placement.json) | known-red |
| [p1-moving-prefix](../tests/cases/p1-moving-prefix.json) | known-red |
| [p1-score-status-prefix](../tests/cases/p1-score-status-prefix.json) | green |
| [p1-upper-serve](../tests/cases/p1-upper-serve.json) | known-red |

### I13: First-serve Paula output

**Value:** keep.

- Behaviour protected: Pitch conversion, measured envelope, hardware and emitted mute.
- Plausible regression: Wrong period/table, residual sound or disconnected waveform.
- Independent expectation: Frozen original PSG events and measured WAV.
- Stopping condition: Existing pitch/envelope known reds and mute signal/silence controls.
- Limits/overlap: No exact onset/decay, later effects or complete waveform fidelity claim.

| Case and exact recipe | Retained classification |
| --- | --- |
| [p2-first-serve-pitch](../tests/cases/p2-first-serve-pitch.json) | known-red |
| [p2-first-serve-envelope](../tests/cases/p2-first-serve-envelope.json) | known-red |
| [p2-first-serve-mute](../tests/cases/p2-first-serve-mute.json) | green |

### I14: Initial physical input decoding

**Value:** keep.

- Behaviour protected: Both ports directions/buttons, simultaneous input, held/released samples.
- Plausible regression: Wrong port bit or omitted second reader.
- Independent expectation: Repeated original physical-control calibration.
- Stopping condition: Existing 13 windows with actual executable fault detection.
- Limits/overlap: Reader/normalisation checks do not establish game response, exchanged sides or latency.

| Case and exact recipe | Retained classification |
| --- | --- |
| [p3-input-p1-up](../tests/cases/p3-input-p1-up.json) | known-red |
| [p3-input-p1-down](../tests/cases/p3-input-p1-down.json) | known-red |
| [p3-input-p1-left](../tests/cases/p3-input-p1-left.json) | green |
| [p3-input-p1-right](../tests/cases/p3-input-p1-right.json) | green |
| [p3-input-p1-button1](../tests/cases/p3-input-p1-button1.json) | green |
| [p3-input-p1-button2](../tests/cases/p3-input-p1-button2.json) | known-red |
| [p3-input-p2-up](../tests/cases/p3-input-p2-up.json) | known-red |
| [p3-input-p2-down](../tests/cases/p3-input-p2-down.json) | known-red |
| [p3-input-p2-left](../tests/cases/p3-input-p2-left.json) | known-red |
| [p3-input-p2-right](../tests/cases/p3-input-p2-right.json) | known-red |
| [p3-input-p2-button1](../tests/cases/p3-input-p2-button1.json) | known-red |
| [p3-input-p2-button2](../tests/cases/p3-input-p2-button2.json) | known-red |
| [p3-input-simultaneous](../tests/cases/p3-input-simultaneous.json) | known-red |

### I15: Field renderer units

**Value:** keep.

- Behaviour protected: Score/game/status/mode selectors, inactive bank and blanking swaps.
- Plausible regression: Wrong glyph/selector, corruption outside field or front-bank mutation.
- Independent expectation: Original field rasters; six shared-font contexts explicitly distinguished.
- Stopping condition: Existing selector inventory and zero/adjacent-selector faults.
- Limits/overlap: No game callbacks; shared-font rows are not captured game scenes.

| Case and exact recipe | Retained classification |
| --- | --- |
| [p1-widget-point-a](../tests/cases/p1-widget-point-a.json) | green |
| [p1-widget-point-b](../tests/cases/p1-widget-point-b.json) | green |
| [p1-widget-games-a](../tests/cases/p1-widget-games-a.json) | green |
| [p1-widget-games-b](../tests/cases/p1-widget-games-b.json) | green |
| [p1-widget-status](../tests/cases/p1-widget-status.json) | green |
| [p1-widget-mode](../tests/cases/p1-widget-mode.json) | green |

### I16: Status lifecycles

**Value:** keep.

- Behaviour protected: Live appearance/expiry for all six messages (first in prefix).
- Plausible regression: Clear early, retain after expiry or wrong requested status.
- Independent expectation: Original point-driven requests and completed crops.
- Stopping condition: Existing distinct status appearances and expiries.
- Limits/overlap: Local cases; second-reader failure retained independently.

| Case and exact recipe | Retained classification |
| --- | --- |
| [p1-status-2-lifecycle](../tests/cases/p1-status-2-lifecycle.json) | green |
| [p1-status-3-lifecycle](../tests/cases/p1-status-3-lifecycle.json) | green |
| [p1-status-4-lifecycle](../tests/cases/p1-status-4-lifecycle.json) | green |
| [p1-status-5-lifecycle](../tests/cases/p1-status-5-lifecycle.json) | green |
| [p1-status-6-lifecycle](../tests/cases/p1-status-6-lifecycle.json) | known-red |

### I17: Deuce/advantage field transitions

**Value:** keep.

- Behaviour protected: Actual point requests and completed fields across equal/advantage changes.
- Plausible regression: Draw a callback early or freeze one field behind existing error.
- Independent expectation: Original draw-boundary records and completed score pixels.
- Stopping condition: Existing deuce/advantage/return-to-deuce transitions.
- Limits/overlap: Simulation scoring covered separately by I03.

| Case and exact recipe | Retained classification |
| --- | --- |
| [p1-deuce-fields](../tests/cases/p1-deuce-fields.json) | known-red |
| [p1-advantage-fields](../tests/cases/p1-advantage-fields.json) | known-red |
| [p1-return-deuce-fields](../tests/cases/p1-return-deuce-fields.json) | known-red |

### I18: Round hardware scenes

**Value:** keep.

- Behaviour protected: Award tally, reset pause, final pause and resumed display in four contexts.
- Plausible regression: Late stale score/sprites, missing reset or wrong event consumption.
- Independent expectation: Original full viewports and consecutive state/event observations.
- Stopping condition: Four distinct mode/end contexts with late compiled faults.
- Limits/overlap: Local initialization, known placement/reset errors; stop equivalent scenes.

| Case and exact recipe | Retained classification |
| --- | --- |
| [p1-first-round-scenes](../tests/cases/p1-first-round-scenes.json) | known-red |
| [p1-one-player-upper-round-scenes](../tests/cases/p1-one-player-upper-round-scenes.json) | known-red |
| [p1-two-player-lower-round-scenes](../tests/cases/p1-two-player-lower-round-scenes.json) | known-red |
| [p1-two-player-upper-round-scenes](../tests/cases/p1-two-player-upper-round-scenes.json) | known-red |

### I19: Ordinary physical mode selection

**Value:** keep.

- Behaviour protected: No active gameplay before choice; Delete/Tab select modes.
- Plausible regression: Bypass title, ignore two-player choice or keep wrong mode.
- Independent expectation: Original pre-choice and accepted-mode states; physical native requests.
- Stopping condition: Both requests expose gating/acceptance errors; aligned final image still open.
- Limits/overlap: Timed final image diagnostic while native acceptance absent; callback count is not gameplay.

| Case and exact recipe | Retained classification |
| --- | --- |
| [p1-accept-one-player](../tests/cases/p1-accept-one-player.json) | known-red |
| [p1-accept-two-player](../tests/cases/p1-accept-two-player.json) | known-red |

### I20: Result/title/restart hardware scenes

**Value:** keep.

- Behaviour protected: Local match award through title, physical selection and restarted flight.
- Plausible regression: Stale result/title/court, lost physical edge, reset or sound event.
- Independent expectation: Original validated extensions with completed rasters and event stream.
- Stopping condition: Both modes plus late sprite/field/refresh faults.
- Limits/overlap: Local interval and logical PSG events; not whole-match cadence or Paula waveform.

| Case and exact recipe | Retained classification |
| --- | --- |
| [p1-one-player-result-restart-scenes](../tests/cases/p1-one-player-result-restart-scenes.json) | known-red |
| [p1-two-player-result-restart-scenes](../tests/cases/p1-two-player-result-restart-scenes.json) | known-red |

## Supporting checks

These are not additional gameplay acceptance cases.

### S01: Original ROM assembly round trip

Entrypoints: [scripts/roundtrip_rom.py](../scripts/roundtrip_rom.py).

Protects: Byte-preserving reproducible annotated source. Limit: Not gameplay meaning or native port acceptance; no fresh result asserted here.

### S02: Reference integrity and source-derived phase validation

Entrypoints: [scripts/round_reference.py](../scripts/round_reference.py), [scripts/phase_reference.py](../scripts/phase_reference.py), [scripts/contact_reference.py](../scripts/contact_reference.py), [scripts/source_audio_reference.py](../scripts/source_audio_reference.py).

Protects: Oracles retain original provenance, prefix/phase correspondence and event associations. Limit: Validation is supporting evidence, not a new gameplay test.

### S03: Failure policy and actual executable controls

Entrypoints: [scripts/run_test_suite.py](../scripts/run_test_suite.py), [scripts/run_audio_tests.py](../scripts/run_audio_tests.py), [scripts/run_round_presentation_tests.py](../scripts/run_round_presentation_tests.py).

Protects: Known early failures do not conceal protected later changes; comparators reject faults. Limit: Controls have declared scopes; not every historical case has complete-observation digest or real fault control.

### S04: Coverage/timing inventories

Entrypoints: [scripts/inventory_match_references.py](../scripts/inventory_match_references.py), [scripts/source_timing_baseline.py](../scripts/source_timing_baseline.py), [scripts/inspect_mute_waveform.py](../scripts/inspect_mute_waveform.py).

Protects: Evidence discovery and gap identification. Limit: Diagnostics, not native acceptance tests.

## Remaining-requirement mapping

| Backlog requirement | Review rows |
| --- | --- |
| F2 contact/action | C01–C03; existing I09/I10 |
| F3 scoring | Existing I03; stop equivalent variants |
| F4 court outcomes | C04; C16 only for distinct rendering protection |
| F5 timer/random effects | Existing I04; C05 for choice-to-effect audit |
| P1 graphics and accepted mode | C15/C16; existing I12/I15–I20 |
| P2 audible sound | C11–C14; existing I13 |
| P3 physical input/cadence/continuity | C06–C10; existing I14/I19 |

Suggested review order: audit C04/C05 against existing evidence first to avoid duplicate core tests; then consider C06/C07 physical response, C09 ordinary cadence and C11 distinct sound classes. C10 brings sustained continuity together. C08/C12 require precise time mapping; C14 requires a presentation decision. C15 extends existing mode tests. C16 proceeds only with a named escaping render fault. This is a discussion order, not authorization to start the candidates.

No test-count target. Completion requires every required behaviour to have adequate original-backed protection or a reviewed reason why existing tests already protect it. Candidate discovery is not completion, and implementation defects may remain known red after useful tests are built.
