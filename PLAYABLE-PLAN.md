# Playable native A500 implementation queue

## Decision and scope

The next implementation goal is a playable, maintainable native Amiga game, followed by a reproducible bootable ADF. Completing every proposed test is **not** a prerequisite to implementing it. This queue supersedes the old suite-first work order in the roadmap, README and historical worklog. It does not mark those old requirements complete, erase failures, or weaken any existing assertion.

This document defines the implementation queue; verification below records subsequent product work. Work in order, with one active item. Repair a prerequisite defect under its owning item rather than opening a parallel test project.

Target: PAL A500, 68000, OCS, 512 KB chip RAM, no slow/fast RAM, Kickstart 1.3. Preserve original rules, update order and feel at the measured source cadence, independently of PAL presentation. Deliver concise maintained native logic and direct Amiga input, rendering and sound. The translated Z80/68000 representation, original captures and ROM roundtrip remain behaviour oracles and diagnostics, not the final runtime architecture.

### Evidence boundary

Repository review base: [f5de85f](https://github.com/rmtew/ctennis/commit/f5de85f57f167e227e3d8160707de5c79779400e). Review performed 2026-09-30 UTC; existing entries dated 2026-10-01 are preserved as recorded, not redated.

- Direct code inspection confirms live-state startup, unconditional gameplay dispatch, incomplete physical input, a second-reader stub, generated gameplay dependencies and the sprite-origin constant described below.
- Prior recorded results, **not rerun for this plan**: exact 8,192-byte ROM reconstruction; native integration through first game award; incremental 99-case classification of 52 green / 47 known red. The last aggregate is not a full fresh 99-case execution.
- The [test review](analysis/test-manifest-review.md) records 56 core cases using regenerated fixed-dispatch code, 35/47 known-red policies accepting only a first signature, eight full digests and four explicit complete intervals.
- R1 currently matches 1,332 callbacks before failure at 1,333 of 13,378 retained original callbacks; R2 matches 2,535 before failure at 2,536 of 27,037. Local later phases do not prove continuous native completion.
- ROMs, private captures and emulator/tool installations were not available in this review workspace. This is a source-backed plan, not fresh hardware or regression verification. Future execution must find legitimate configured inputs, not invent passing results.

## How to use this queue

Statuses: **ready** (prerequisites met, not started), **queued**, **active**, **blocked**, **verified**. CT-01 is verified and merged; CT-02 is verified with ordinary title/physical-choice evidence (see WORKLOG.md). CT-03 is verified with focused physical-control evidence; CT-04 is verified with bounded native gameplay evidence; CT-05 is verified and merged; CT-06 is active; CT-07–CT-10 remain queued.

At session start read AGENTS.md and the latest WORKLOG.md entry, select the first unfinished item whose dependencies are met, and state one concrete next change. At session end leave either a product change with focused evidence, a precisely isolated blocker with a reproduction, or a verified milestone. Test creation, extra captures, increased case counts, and repeating an unchanged baseline alone are not progress.

Each item may take several small commits. Its listed checks are a finite acceptance set, not permission to build an exhaustive suite. Prefer existing cases and original media. Add or extend a check only to protect that item's concrete fix or a demonstrated observable gap. A new test requires a named fault, independent expectation, and stopping condition. Keep one focused failing reproduction, fix the game, rerun the reproduction and affected green checks, then move on.

During migration, raw-state translator cases remain their own diagnostic tier. Product checks must execute the maintained module and actual dispatcher. Project existing captured source observations and actual native outputs into named values only as each changed subsystem needs them; do not first build an all-encompassing observation framework or a second Python game.

## CT-01 — Establish the maintained product execution boundary

**Status:** verified (2026-09-30 UTC). **Dependencies:** none.

Evidence: shared `amiga/game/tick.s` dispatcher in live application and maintained serve replay; 200 updates/40 PSG bytes matched, maintained dispatch fault rejected at update 1, source restored and rebuilt, regeneration hashes unchanged. Native live input/cadence/serve/display/audio checks passed. Temporary adapter remains explicit CT-02–CT-08 debt; no later milestone is claimed.

**Verified blocker:** `prepare_gameplay()` regenerates the routines on every build; both live and test code include `build/translation/player-frame-routines.s`. The harness calls a fixed gameplay sequence instead of the application's regime dispatcher. A clean native edit therefore has no protected maintained home.

**Targets:** [prepare_gameplay](scripts/run_translated_player_frame_probe.py), [live build](scripts/run_amiga_gameplay_integration_probe.py), [simulation_update and includes](amiga/gameplay_integration_probe.s), [simulation harness](amiga/tests/simulation_harness.s), [regression runner](scripts/run_regression_tests.py). Proposed tracked modules: `amiga/game/` and a native build entry point; final filenames are an implementation choice.

**Change:** establish one maintained source-tick entry point and explicit native lifecycle state, shared by the application and product replay. Keep the translated baseline separately selectable. Initially retain the working routines behind a clearly temporary adapter; replace them in CT-02–CT-08 rather than freezing arcane generated code as the endpoint. Regeneration writes only reference/build outputs. Check the existing source/asset policy before checking in ROM-derived translated bytes.

**Observable acceptance:** a maintained gameplay/dispatch edit changes the executable used by product checks; invoking reference regeneration cannot overwrite it. An unchanged short serve still works. The test harness does not select a regime by copying the source callback kind into the product.

**Lightweight validation:** build the real native executable and run the existing serve case through the shared entry point; one temporary maintained-code gameplay or dispatch fault must be detected by that same check, then restore and rebuild. Record native module/executable hashes and actual selected test subject. Do not migrate all 99 cases or invent all future semantics before CT-02.

## CT-02 — Boot to title and accept the chosen mode

**Status:** verified and merged in [PR #2](https://github.com/rmtew/ctennis/pull/2) (2026-09-30 UTC). **Dependencies:** CT-01.

**Resolved blocker:** `start` copies a source live-game snapshot; the builder selects original frame 1299 and applies its tail. Gameplay is already active before either choice. Delete and Tab both leave one-player mode; accepted-mode generation is absent.

**Targets:** [startup](amiga/gameplay_integration_probe.s), [initial-state construction](scripts/run_amiga_gameplay_integration_probe.py), [mode evidence](analysis/native-mode-selection-regression.md), [mode runner](scripts/run_mode_selection_tests.py), original setup/menu labels in [ROM symbols](analysis/rom-symbols.def).

**Change:** implement native title/wait/selection and new-game initialization. Preserve current declared keys: Delete selects one player; Tab selects two players. Do not initialize R2 state as a substitute for accepting Tab. Use lifecycle state from CT-01; implement direct native state, not source-PC emulation.

**Observable acceptance:** fresh ordinary boot shows the title and waits without active play; either physical key selects its actual mode, transitions to the correct court and waits for legitimate serve action. A held key does not repeatedly restart a match. The completed accepted display belongs to that accepted choice.

**Lightweight validation:** reuse `p1-title`, `p1-accept-one-player` and `p1-accept-two-player`. Extend the two existing mode checks to their first stable accepted generation, not two new case families. One fresh boot per choice, including press/hold/release. A source-rate callback count during title is not itself premature gameplay.

Evidence: ordinary boot exactly matches the original title; both physical key
choices pass hold/release, one-time acceptance, completed chosen mode label,
exact accepted viewport at the retained serve-wait ball pose, ignored selection
re-press and physical-fire serve response. Existing wrong-mode and sprite faults
are rejected. The documented sprite-origin constant is corrected solely as this
acceptance prerequisite. Captured active-scene checks now require explicit
`LIVE_PHASE_START`; they do not establish ordinary boot or full matches.

## CT-03 — Complete physical controls and preserve player ownership

**Status:** verified and merged in [PR #3](https://github.com/rmtew/ctennis/pull/3) (2026-09-30 UTC). **Dependencies:** CT-02.

**Resolved blocker:** `sample_amiga_joystick` previously read only connector-2 left/right/fire; `sample_second_input_group` returned zero. Recorded input calibration has three green and ten known-red windows. **Remaining verification:** reaching a side exchange continuously remains CT-05/CT-09 work. Ordinary player-1 physical serve and local exchanged-end player-2 serve are verified below.

**Targets:** [samplers](amiga/gameplay_integration_probe.s), [physical runner](scripts/run_physical_input_tests.py), [mapping](analysis/two-player-input-map.md), [physical evidence](analysis/native-physical-input-regression.md). Native input state replaces packed source fields as logic is migrated.

**Change:** read both declared joystick connectors, four directions and both declared action buttons; map connector 2 to source player 1 and connector 1 to source player 2. Keep logical player identity separate from court end. Implement native ownership mapping and consistent press/hold/release consumption.

**Observable acceptance:** each player can move, reverse and act independently; neutral/release clears input, simultaneous opposite-player controls remain independent, and a side exchange does not give a pad the wrong player. One-player control leaves the intended opponent under AI control.

**Lightweight validation:** reuse the single 13-window physical batch and extend observation to representative actual player movement and serve/action response, not merely returned bits. Reuse one reachable exchanged-side source window to check ownership locally; CT-05/CT-09 must additionally establish reaching it continuously. No new exhaustive bit matrix. If final hardware needs a keyboard alternative for a single-button stick, document/ask for that control policy rather than silently dropping the second action.

Evidence: maintained `amiga/game/controls.s` samples both two-button pads and
owns held/pressed/released state and player/end mapping. The 13-window original
batch passes 561 updates, including eight actual player fields and independent
movement; the existing compiled input fault is rejected. Ordinary boot proves
move/reverse/release for both players, player-2 exclusion from one-player control,
and player-1 physical serve. One reachable exchanged-end phase (source callback
2672, 105 executed updates) proves swapped end ownership, both players' reversal
and player-2 blue-button serve. No intermediate state injection. This local
phase does not prove reaching the exchange continuously; CT-05/CT-09 retain that
gate. Gameplay still runs through the temporary adapter. See WORKLOG.md and
[physical evidence](analysis/native-physical-input-regression.md).

## CT-04 — Maintain native serve, rally, movement and AI logic

**Status:** verified and merged in [PR #4](https://github.com/rmtew/ctennis/pull/4) (2026-10-01 UTC). **Dependencies:** CT-03.

**Resolved blocker:** serve/rally logic was regenerated translation; the resumed-launch triangular-root helper lost carry before SUBX. The retained diagnostic temporarily corrected all 200 phase updates and restored the unfixed baseline. **Not assumed broken:** existing six-return rally and movement/scoring phases have substantial green coverage.

**Targets:** translated extraction boundaries `lower_player_state`, `upper_player_state`, `ball_flight_update`, `player_movement_and_sprites`, `triangular_root_step` in [generator](scripts/run_translated_player_frame_probe.py); [launch diagnosis](scripts/diagnose_phase_launch.py); [update contract](analysis/frame-update-contract.md). Implement maintained counterparts under the CT-01 boundary.

**Change:** port these active-play routines in small behaviour-preserving slices into readable 68000 functions and named state. Fix launch arithmetic in the maintained implementation, preserving proven widths/order while removing emulated registers/flag assembly from replaced paths. Preserve AI choice effects with a test-only recorded entropy input; ordinary play uses native entropy.

**Observable acceptance:** both ends can serve; the ball advances correctly; both players can return in one rally; a point is awarded to the correct player; movement limits and action-dependent shot choice remain correct; resumed serve no longer inherits the diagnosed launch error.

**Lightweight validation:** existing `serve`, `resumed-play-phase`, `two-player-rally`, affected movement cases and existing upper action timing cases. Reuse the 200-update failure reproduction. Upper before/at/after action cases protect shot choice, not geometric hit/miss thresholds. Audit existing court/entropy outcomes only when a changed path needs an uncovered outcome; one bounded missing example is enough.

Evidence: the application and maintained replay now use named native player,
ball, movement and AI routines. Serve 200, resumed launch 200, upper completed
serve 50, six-return rally 1,390, all 18 affected movement windows (11,078
updates) and three upper action windows (722 each) match every selected boundary.
The repaired launch is independently faulted at update 96, then restored and
rerun. Ordinary mode checks pass full retained viewport/physical movement/serve;
the existing live serve probe passes state, changed point field and tone. A
right-point Copper switch is moved before its fetch after the faster native
path exposed a display artifact. Raw translated launch still fails at update
96; only the migrated product case is promoted. Score/lifecycle, animation/VDP
and audio remain explicit temporary adapters. Local starts do not establish
continuous rounds, complete matches or independent-hardware parity. See
[CT-04 evidence](analysis/native-gameplay-regression.md).

## CT-05 — Score, pause, exchange ends and resume the next game

**Status:** verified and merged in [PR #6](https://github.com/rmtew/ctennis/pull/6), master `8cb8c87`. Bounded native scoring/round acceptance independently cleared at `cbbaf89`; raw scratch diagnostics remain separate. **Dependencies:** CT-04.

**Resolved boundary:** shared native main-path polling now switches to service-only, requests the display/player reset, advances serve/end ownership, waits for phase/audio completion and resumes. Maintained R1 crosses callback 1333 through its full 1566-update round window; maintained R2 matches a declared 2800-update prefix beyond callback 2536. Native deuce/advantage and four complete round phases match. Three round-scene full raw-state reports still differ only at retired contact scratch offsets 0x67–0x68; all four pixel/field contexts match. Scenes now apply the existing CT04 maintained scratch contract for semantic acceptance, while separately preserving all254 raw diagnostic bytes and their failures. See [CT-05 evidence](analysis/native-scoring-round-regression.md).

**Targets:** [simulation_update](amiga/gameplay_integration_probe.s), native lifecycle from CT-01; [round evidence](analysis/long-game-replay.md), [frame contract](analysis/frame-update-contract.md), [round runner](scripts/run_round_presentation_tests.py), existing continuous/phase recipes.

**Change:** implement native point/game scoring and round lifecycle: award once, show tally, pause gameplay while counters/sound/pending presentation continue, initialize next round, exchange ownership/serve state as the original does, then resume. Explicit native states replace source callback pointers and source main-thread writes; do not inject expected writes from the fixture.

**Observable acceptance:** ordinary play crosses the first-game boundary and completes a subsequent serve in each mode; no scoring twice, moving players during the pause, stale score or stuck reset. Deuce → advantage → deuce → advantage → game remains correct. Both serving ends and both ownership regimes work.

**Lightweight validation:** existing `deuce-sequence-phase`, `round-transition`, relevant completed-serve phases, and four existing round-scene contexts. Run continuous R1/R2 beyond their old first failure; a passing local reset phase alone is insufficient. Fix/review changed failure baselines explicitly rather than accepting the old early signature.

## CT-06 — Finish a match, return to title and restart

**Status:** active, implementation and focused acceptance ready for independent review (2026-10-01 UTC). Not merged or independently verified. **Dependencies:** CT-05.

**Resolved boundary:** native result/title/restart state now handles sound requests, return display, shared mode selection and old-action release gating. Complete local scene checks remain separate from ordinary continuous match/restart acceptance; see the evidence record below.

**Targets:** native lifecycle; [result evidence](analysis/native-result-restart-presentation.md), [result runner](scripts/run_result_presentation_tests.py), [restart recipes](tests/cases/one-player-restart-complete.json) and [two-player recipe](tests/cases/two-player-restart-complete.json).

**Change:** implement native match award, result presentation/sound request, title return, release/reselection handling and fresh-game reset. Reuse CT-02 selection, not a second menu implementation.

**Observable acceptance:** both modes reach their result, return to title, accept a new mode selection and launch a restarted serve. Old score, side assignment, held action and audio state do not leak into the restarted match.

**Lightweight validation:** reuse the two existing six-checkpoint result/restart cases and their complete state/pixel/event acceptance. Then carry ordinary/continuous play from fresh mode selection through the result and restarted serve; retain checkpoints rather than all frames. Do not create more equivalent result-scene permutations.

Evidence: both complete maintained match phases match1451/1451; both six-scene windows pass1422 states/42 images each and all six compiled late faults. Ordinary one→two11807 and two→one23753 consecutive callbacks cross match/title/reselection and held-action release/repress through restarted flight. Final executable `80b16463f5673f033241a10333ed38a6157f5d986b54e45f2d75cda5efff56fa`; progress reports CT06 evidenced within this scope with all required reports fresh. Raw scratch diagnostics remain separately red; cadence/full reference match/peak RAM/waveform/ADF/independent validation remain open. See [CT06 evidence](analysis/native-result-restart-presentation.md).

## CT-07 — Correct native graphics and remove the display translation bridge

**Status:** queued. **Dependencies:** CT-06. Presentation fixes needed for earlier acceptance are made in those items, not deferred artificially.

**Resolved prerequisite in CT-02:** `upload_sprite_attributes` now uses horizontal origin $80; the previously recorded $6c/20-pixel shift blocked accepted-mode display verification. **Remaining blockers:** Later layouts remain stale behind missing lifecycle work. Runtime still translates source sprite records and shadows VDP writes. **Unverified risk:** complete-match rendering/deadlines on independent hardware.

**Targets:** [sprite upload, scoreboard and double buffers](amiga/gameplay_integration_probe.s), [display include](amiga/sprite_probe_display.i), [score patches](amiga/score_copper_patch.i), existing presentation/status/widget/round/result runners.

**Change:** fix alignment and maintain direct Amiga sprite/bitplane/Copper presentation from native scene state. Preserve previous-update sprite semantics and delayed score/status draw boundaries where observable. Retire virtual VDP/shadow-memory operations from product paths after their direct replacements are protected.

**Observable acceptance:** players, ball and shadow align with court; mode/score/status and round/result/title displays represent the correct completed generation; no stale or partially prepared scene is published. Preserve eight-channel/colour capacity behaviour or provide a measured native solution for a real overflow.

**Lightweight validation:** existing placement and moving-prefix pictures, green score/status fields, and round/result checkpoints. Reuse already captured return/bounce/net/out images only if a named changed rendering behaviour escapes these checks. For a relevant multi-observation known-red case, make a temporary late fault fail the check; an unchanged first error is not protection of later frames.

## CT-08 — Maintain native sound timing and audible effects

**Status:** queued. **Dependencies:** CT-07. Lifecycle audio requests may be implemented earlier; this item removes remaining sound debt.

**Verified blockers:** live and harness tails call `audio_tick_adapter` unconditionally after the counter prefix even when original countdown reload is two. Recorded first-serve pitch/envelope cases expose a one-period conversion and a low-volume difference; bounded mute is already protected. Runtime still interprets source PSG-oriented streams.

**Targets:** [tail call sites](amiga/gameplay_integration_probe.s), [current sound interpreter](amiga/translated_audio_tick.s), [Paula output](amiga/paula_tone_output.s), [source tail evidence](scripts/source_irq_tail.py), [audio runner](scripts/run_audio_tests.py).

**Change:** fix due-service cadence, pitch/level conversions where required by existing criteria, and express effects in native event/voice data driving Paula directly. Preserve audible timing and duration of serve, return, point, round, result and restart; do not retain a runtime SG PSG compatibility layer as the finished design.

**Observable acceptance:** required effects are audible at the right event, cadence is correct in play and waits, result phrases finish, mute is silent, and restart does not leave a stuck voice.

**Lightweight validation:** existing pitch/envelope/mute checks and `status-timer-saturation-phase`; inventory the 18 retained original audio intervals into distinct effect/scheduling classes and use one representative output window per distinct class. Verify normal after any fault build. No byte-identical waveform/filter/phase target, new active-noise implementation or stereo-fidelity gate without original evidence or an explicit design decision.

## CT-09 — Verify uninterrupted native cadence and complete play

**Status:** queued. **Dependencies:** CT-08.

**Verified existing evidence:** CIA-B timing targets 59.922738 Hz; prior long replay and ordinary prefix measured no visible-line Copper commits. **Open verification, not a newly diagnosed defect:** normal execution across all regimes, input latency and complete matches has not passed the final acceptance gate.

**Targets:** [timer, loop and presentation commit](amiga/gameplay_integration_probe.s), [timing baseline](analysis/source-timing-baseline.md), [long-game runner](scripts/run_amiga_long_game_probe.py), maintained native build.

**Change if needed:** repair measured drift, lost/double updates, scheduling overrun, input delay or missed publication in the actual native loop. Keep production instrumentation compact and observational; debugger-step timing is not ordinary execution timing.

**Observable acceptance:** two ordinary play-throughs, one per mode, cover selection, physical serve/rally, point/game award, pause/resume, match result and restarted serve. Simulation remains at source cadence while PAL presentation is separate; no visible-line commits or lost/stale event sequence. Memory stays within the unexpanded target.

**Lightweight validation:** record compact callback/regime/input/event/commit timestamps and milestone screenshots/audio; measure expected update counts against elapsed emulated E-clock time, including menu/tail/result intervals. Document measurement resolution and source/native clock mapping before setting tolerances; do not fit tolerance to the observed failure. Probe one before/after input edge for a direction and action at the source-tick boundary. Use recorded entropy only for deterministic comparison, and separately run ordinary native entropy. Report actual full matched/executed extents, runtime, peak chip-memory use and any unresolved risk.

## CT-10 — Remove residual scaffolding and deliver the bootable ADF

**Status:** queued. **Dependencies:** CT-09.

**Verified blocker:** current product includes generated routines, virtual source memory and source snapshots; the reviewed tracked tree has no finished native build/ADF packaging recipe. **Unknown until execution:** final memory/boot-path costs and independent-emulator/hardware behaviour.

**Targets:** maintained build entry, all product includes from [current executable](amiga/gameplay_integration_probe.s), [setup script](scripts/setup-emulators.ps1), README; proposed reproducible executable/ADF build and boot files.

**Change:** remove remaining translated register/flag/macro machinery, virtual Z80 memory, SG VDP/PSG runtime adapters, duplicate implementations and implicit regeneration from the product build. Keep them as separately labelled reference tools only where still useful. Package the maintained native executable and legitimately generated assets with a documented Kickstart-compatible boot path. No cartridge is required at runtime; ROM images, private captures and unmodified extracted assets stay uncommitted.

**Observable acceptance:** clean reproducible build yields the native executable and ADF; product logic builds without the translation generator (asset preparation can remain a separate explicit local step). ADF cold-boots on the exact 512 KB profile, accepts real controls, plays a complete match and restarts with sound. Direct executable and disk boot have equivalent behaviour. Architecture review finds no residual runtime source-machine compatibility layer.

**Lightweight validation:** record pinned tool versions, commands, executable/ADF hashes, memory footprint and profile. Cold-boot the ADF itself, not only direct-launch its executable. Run affected regression guardrails and one complete aggregate report at this delivery milestone, classifying translator-only diagnostics separately without relabelling failures. Verify in an independent emulator/real A500 under the roadmap. If unavailable, deliver the available build/evidence but leave CT-10 blocked with the exact missing verification; that final gate remains unverified. Deliver source/build instructions, ADF, evidence and a concise limitations list. Do not claim Phase 4/5 complete while their checks remain unverified.

## Deliberate deferrals and stopping rules

- The 21 manifest candidates are proposals, not 21 additional prerequisites. Fold C19 into CT-01, C20 only into each changed subsystem, and C21 only into relevant affected multi-observation checks.
- C06/C07/C15 are bounded support for actual control/mode fixes; C08–C12 support CT-08/CT-09 when that behaviour is being fixed or verified.
- C01–C05/C13/C14/C16 remain conditional audits. No geometric-contact, randomness, extra court raster or waveform project without a distinct missing observable protection.
- C17 duplicate variants and C18 unsupported active-noise work stay deferred.
- Existing tests and source evidence are retained; no wholesale deletion, weakened expected output, automatic known-red rebaselining or invented complete-suite claim.
- Do not stop a product fix just because the historical suite has unrelated known reds or open broad coverage groups. Record them separately. An unexpected affected regression must be explained/fixed before promoting the item.
- Complete this queue only when all CT-10 acceptance gates are verified. Otherwise report the exact authorization/input/tool/verification blocker, leave the affected item blocked and final completion unclaimed. Do not add another test-completion phase by default.

## Progress record

WORKLOG.md holds the newest session entry. Use the AGENTS.md template. Each entry names one item, before/after visible capability, actual product files, checks run on the final build, checks reused/not run, the unresolved blocker and one next action. Update this document's status only with linked evidence; this initial plan has no verified product items.
