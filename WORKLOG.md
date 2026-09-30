## 2026-09-30 UTC â€” Defined the playable-native implementation queue

- Status: plan defined; no product queue item implemented or verified.
- Current decision: PLAYABLE-PLAN.md and AGENTS.md supersede the historical suite-first work order. Work through CT-01â€“CT-10 with one item active: maintained product execution boundary; title/mode; physical controls/ownership; native serve/rally/AI; scoring/round reset; result/restart; graphics; sound; ordinary cadence/full play; scaffolding retirement and ADF.
- Each item records dependencies, verified versus uncertain blockers, code targets, observable acceptance and a finite lightweight validation set. Tests are guardrails for product changes; add or extend one only for a concrete fix or demonstrated behavioural gap. The 21 manifest candidates are not a new prerequisite queue.
- Source inspection at f5de85f57f167e227e3d8160707de5c79779400e confirms live-state startup, fixed gameplay dispatch, incomplete input/second-reader stub, generated gameplay dependencies and the sprite-origin constant. Existing analyses supply the recorded launch, reset, result and audio defects; these were not rerun.
- Documentation-only change: added PLAYABLE-PLAN.md and AGENTS.md; updated README current priority and prepended a roadmap precedence notice. Historical roadmap/worklog text is preserved, including existing entries dated 2026-10-01. This entry uses the review session's actual UTC date and explicitly changes priority rather than pretending to be a historical execution.
- Verification scope: reviewed repository code, test manifest/review, known failures, architecture, physical/mode/round/result/audio evidence and source update contract. Checked document links, queue completeness and preservation of prior history. No emulator run, original capture, product build, new test or product fix.
- Retained baseline only: incremental 99 cases, 52 green / 47 known red; 56 generated fixed-dispatch core cases; 35 first-signature-only red policies. R1/R2 match 1332/2535 callbacks before their existing failures. These are repository-recorded results, not fresh execution or full-match acceptance.
- Next action when implementation is requested: CT-01, establish one maintained native source-tick/dispatcher entry shared by the application and product replay, prove reference regeneration cannot overwrite it, and reuse the short serve check. Do not start another test-expansion pass first.
- Environment limit: this review did not have configured private ROM/capture inputs or an execution toolchain; future product verification must locate those legitimate inputs and report any exact blocker. No Phase 4/5, completed-suite, playable-match or ADF gate is claimed.

---

## 2026-10-01 ? Reviewed test relevance and corrected coverage claims

Reviewed actual registry, core regeneration/fixed-dispatch harness, contact and hardware/audio/input assertions, strict classifier and all retained reports. Findings: 56 core cases exercise generated fixed gameplay dispatch, not maintained application dispatcher;35 of47 red policies accept only first signature (8 digest,4 explicit interval); R1/R2 match1332/2535 callbacks, not full source lengths13378/27037; raw RAM equality constrains internal rewrites; upper action cases are shot-choice timing, not hit/miss acceptance. Copied-report late-fault controls demonstrate masking in moving-prefix/input/pitch and rejection by complete round digest. No emulator fault run claimed.

Corrected families and renderer (subject, acceptance and actual extent), demoted lower action/extra fidelity to audit-first, added C19/C20/C21 existing-suite assurance proposals. Current21 candidates:11 worth,8 audit,2 skip; no candidate or product change implemented. Added analysis/test-manifest-review.md. Scope remains under discussion; no silent new completion gate or test expansion. Existing classifications unchanged. Full test goal remains incomplete.

## 2026-10-01 ? Enumerated test manifest for scope review

User requested implemented tests and viable candidates to evaluate. Added tests/test-manifest.json, generated tests/TEST-MANIFEST.md and scripts/render_test_manifest.py. All 99 registered cases are assigned exactly once across 20 requirement families; exact recipe links and retained classifications are enumerated. Eighteen candidate rows state missing behaviour, plausible fault, independent original expectation, stop condition, overlap, evidence readiness, relative effort and dependencies: ten worth implementing, six audit first, two skip proposals. Supporting validators/roundtrip/diagnostics are separated from product acceptance tests. All remaining backlog groups map to manifest rows.

Renderer inspected actual retained reports using current strict classifier: 52 green,47 known red. No emulator tests or source captures executed, no product fixes and no candidate implemented. Scope choices are proposals pending discussion, not authorized expansion. Roadmap/README point to the manifest; active full test goal remains incomplete.

## 2026-10-01 ? Existing mute case completed; stop for scope discussion

Extended p2-first-serve-mute rather than adding a new case. Original WAV establishes a 5ms audible pre-mute window and a 20ms silent post-mute window. Native output matches at source PCM16 precision, per channel. Actual private mute-volume1 fault produces residual peak166; actual zero-waveform fault removes the pre-mute signal while period/volume/length controls stay unchanged. Normal peak332 before mute, zero after. Three successful self-test captures; normal rebuilt last. Initial harness assertion compared all custom registers and rejected expected changed DMA sample data; corrected control comparison and reran all three.

No product/source media changes. Bounded signal/silence closed; no waveform fidelity, exact onset/decay or complete P2 acceptance claimed. User asked to finish this case then discuss scoping; no additional test work should begin before that discussion. Full goal remains incomplete. See analysis/native-emitted-mute-regression.md for proof and scope.

## 2026-10-01 ? Requirement-driven coverage audit and mute waveform evidence

Previous goal turn was no progress (selection discussion only). Inspected current clean worktree, backlog, moving-prefix case, rally inventory code and audio runner. Deferred automatic additional court screenshots: six-return continuous R2 state comparison and existing launch/pre-bounce pictures must be accounted for first. Retained all open requirements.

Added and executed scripts/inspect_mute_waveform.py against existing hash-validated source/native WAVs. Three fully retained 20ms windows after mute: original PCM is zero; native float32 decays from peak 2.23e-35 to subnormal 1.40e-45. This changes next action: exact-zero floating-point acceptance is invalid; define format-aware emitted-silence comparison and prove real unmuted-channel mutation detection. No new cases, product edits, emulator launches or waveform acceptance claimed. Aggregate is unchanged; no suite rerun. Roadmap and test docs now supersede the automatic next-scenes instruction.

# Current checkpoint: both result/title/restart scene sequences (2026-10-01)

Previous turn made progress: physical mode-request failures registered790bc8a. This turn adds both local result/title/physical-restart sequences:2844 states,12 full viewports,72 geometry crops (48 matching), six compiled late mutants rejected. Physical fire release, Delete/Tab selection press/release and fire repress applied at source epochs; no expected transition writes. Source120 rasters repeat identically and preserve the original extension callback streams; primary575 unchanged. Tail IRQ$06B1 omits sprite upload but can change VDP registers, so explicit title association uses captured hardware and unique source pixels. All four old round comparisons remain identical from actual captures.

Harness correction: fixed10-second inter-checkpoint deadline could not reach the14-second restart gap; now scales with callback distance. Initial failed attempt terminal before rerun. Eight successful result captures (two normals/six mutants). Logical PSG/event differences retained; no P2 waveform acceptance claimed.

Corrected and reran both mode tests: simulation_updates counts tail/menu work, so nonzero count alone is not a gameplay failure. Assert active player phases outside waiting mode against verified original pre-choice frame119. Both remain known red, repeated normals agree, all four compiled mutants rejected. Eight successful mode captures this turn. Source-rate counts are diagnostics.

Current incremental99-case aggregate:52 green,47 exact known red, no unexpected/tool failures. Four cases executed/rerun;95 prior reports retained with provenance. Current policy/classifications verified. No full99-case execution claimed. Four groups remain open; goal active.

Next: both return scenes and distinct bounce/net/out presentation, then remaining F2/F4/F5, audio and ordinary native cadence/input/deadline requirements. Generation-aligned startup acceptance remains open. Stop equivalent result/menu/restart variants. Evidence:analysis/native-result-restart-presentation.md. Historical worklog bytes preserved.

---

# Current checkpoint: physical mode-request failures registered (2026-10-01)

Previous goal turn made progress: finite round matrix and stopping rules committed314e648. This turn adds two actual ordinary native physical-key selection tests. Identical R1 startup for both choices; no R2 selected-state injection. Source Del/Ins and Func map to native Delete/Tab. Existing accepted-mode1299 images/RAM verified without new MAME captures.

Both starts complete120 gameplay callbacks before choice; Tab retains one-player flags0 rather than$80. Both normal outputs repeat identically. Four compiled sprite/mode mutations rejected despite the unchanged earlier failure. Eight actual native launches. Final timed viewport is diagnostic; generation-aligned accepted-mode presentation remains open because acceptance is absent. No product fixes.

Current incremental aggregate97:52 green,45 exact known red. Two new cases executed,95 previous reports reused with provenance; no full97-case run claimed. Failure policy and all actual mutant classifications pass. Four groups remain open; goal active.

Next: distinct match/result/menu/restart presentation via existing source generations, then remaining court/contact/random outcomes, audio and ordinary execution requirements. Stop equivalent missing-mode variants. Evidence:analysis/native-mode-selection-regression.md. Worklog historical bytes preserved.

---

# Current checkpoint: complementary round presentation complete (2026-10-01)

Roadmap requires missing observable behaviour, a plausible regression, independent expectations and a finite stop for each task. Equivalent permutations and unchanged full-suite repeats are not progress.

Four local round contexts:1072 state checks,16 whole viewports,96 matching fields and12 compiled late sprite/field/refresh mutation checks. Three new cases expose existing reset/origin/second-reader defects. No product fixes or source reset injection. Added40 twice-identical missing source rasters; primary575 and replay controls preserved. See analysis/native-complementary-round-scenes.md.

95-case aggregate:52 green,43 exact known red, no unexpected/tool failures. Four round runners executed with self-tests and complete digest acceptance;91 unchanged reports reused from prior full92-case proof. suite-report.json records incremental provenance, not full95-case execution. Policy checks pass. Four groups remain open; suite goal remains incomplete.

Next: actual accepted one/two-player mode selections using physical native input and completed presentation generations. Initialized mode preservation is insufficient. Then distinct result/menu/restart and remaining F2/F4/F5, P2 and P3. Stop equivalent round windows.

---

## 2026-10-01 - First-round whole-viewport suite checkpoint

- Full runtime suite completed:92 cases,52 green,40 exact known red; all
  compiled mutations and policy controls pass, no unexplained/tool failures.
  Command: python scripts/run_test_suite.py --baseline-check --self-test.
  Owned session47253 is terminal (PowerShell exit1; Python aggregate returns2
  for the four open coverage groups). The goal remains active.
- The new p1-first-round-scenes initializes once1203 before award1204;
  checkpoints1208/1335/1468/1471 cover stable tally, reset pause, final pause
  and resumed gameplay. Reuses validated full round phase and original rasters.
  No original main-thread writes or callback routing are injected.
- 268 consecutive post-tail states:129 match before missing reset diverges1333.
  Score/status/mode:24 crops match. Four whole-viewport pictures expose the
  existing sprite-origin error and stale round layout. State differences at
  checkpoints0/20/30/48; normal source-event consumption has no differences.
- Expanded the initial partial court ROI to all256x192 pixels after inspection
  found115/115/119 differing reset-head pixels outside it in the later scenes.
  Rechecked the same full-suite normal and three compiled-mutant captures,
  validating pinned capture reports, executables, native/source reference hashes
  and unchanged earlier pixel regions. No runtime code/captures changed.
  Actual reports and aggregate record comparison followup/provenance; all
  current reports were reclassified against the reviewed whole-viewport policy.
- Whole-view first failure:1208 at50,36, black expected/pink actual. Later
  reset failures begin94,12, blue expected/black actual. Every compared state
  difference and expected/actual pixel/event observation participates in the
  strict known-failure digest, so earlier sprite failure cannot hide later work.
- Three late compiled mutants preserve game RAM and that earlier failure: extra
  sprite pixel shift, wrong second point, extra refresh read. All classify new
  failures. Extra read is a behaviour difference1335 ([] versus[0]), not a
  capture exception. Default strict source-event checks remain for older cases.
- Explicit tail-only association now handles short same-frame callbacks using
  matching contemporaneous hardware SAT plus independent unique raster pixels.
  Correction to preceding history: active_updates uses begin_frame < frame <=
  end_frame and does not filter callback kinds. Reset hardware2632/pixels2633.
- Updated roadmap, backlog, test instructions and spec. Evidence:
  analysis/native-round-presentation-regression.md. No product fixes. ROMs,
  full generated data and captured images remain local/ignored.
- Stop equivalent first-round windows. Next: complementary serving-end and
  two-player round presentation; first inspect existing source windows and
  capture only genuinely missing bounded checkpoints. Accepted mode, result/
  menu/restart scenes and all other F2/F4/F5/P2/P3 requirements stay in scope.
  No whole-match/native hardware gate or complete-suite claim.

## 2026-10-01 - First round presentation comparison (aggregate running)

- Added p1-first-round-scenes: one native initialization before award1204,
  stable tally1208, reset pause1335, final pause1468, resumed gameplay1471.
  Reuses the validated full round phase and existing original media; no new
  original capture and no injected main-thread resets.
- Corrects the preceding index note: active_updates uses begin_frame < frame
  <= end_frame, not a gameplay-kind filter. Short same-frame tail callbacks
  lack entries; crossing tail callbacks have entries. Explicit tail association
  admits contemporaneous endpoints only with matching captured/source SAT and
  unchanged independent raster validation. Hardware reset appears2632, pixels2633.
- 268 state checks:129 match then the known missing round reset diverges1333.
  All24 score/status/mode crops pass; four court crops retain the known origin
  shift and stale round placement. Normal full observations repeated identically.
- Three actual compiled late mutations preserve game RAM and the earlier sprite
  failure: extra sprite shift, wrong second point field, extra refresh read.
  All classify unexpected red under the complete state/pixel/event digest.
  Unexpected entropy read is recorded1335, expected[]/actual[0], not a tool error.
- First entropy-mutant build used the wrong adapter symbol; corrected to the
  existing read_refresh_adapter and ran it successfully. Failed partial runner
  did not publish a completed case report. Full suite will recreate all evidence.
- python scripts/run_test_suite.py --baseline-check --self-test is currently
  running (owned exec session47253). Last full verified aggregate remains91
  cases,52 green,39 known red; do not claim92 until this run completes.
  Four coverage groups remain open and the goal remains active.

## 2026-10-01 - Native point draw boundaries and complete aggregate verification

- Added p1-deuce-fields, p1-advantage-fields and p1-return-deuce-fields,
  reproducible source phases, point_reference.py and run_point_tests.py. Each
  starts once four callbacks before the original award and holds both physical
  fire inputs. Original awards9134/9588/9869 draw on9135/9589/9870.
- Observe actual native bootstrap field selections at the first simulation
  entry; never seed expected previous scores or inject intermediate values.
  Preserve those selections until the source draw boundary, then compare both
  points, both games and mode. Pre-draw prior-screen parity is outside these
  local starts. The continuous scoring replay remains accumulation evidence.
- All27 consecutive request observations and30 completed field crops match.
  Every one of27 post-tail states has only C056 expected17/actual1, the existing
  combined-control omission caused by the missing second input reader. First
  failures9131/9585/9866 remain exact known red; these are not new defects.
- All six compiled mutations are detected: early consumers at9134/9588/9869,
  frozen second-point fields at9135/9589/9870. Mutants preserve normal game RAM
  and classify as unexpected red despite the unchanged earlier input failure.
  Known-red acceptance requires the complete state stream and green outputs.
- First capture attempt exposed Copperline single-PC-breakpoint uniqueness.
  Corrected test-only bootstrap observation to finish and remove its breakpoint
  before adding later callback targets. No product implementation changed.
- Full command python scripts/run_test_suite.py --baseline-check --self-test
  completed:91 cases,52 green,39 exact known red; all compiled/signature checks
  pass, no unexpected outcomes or tool errors. Verified every reported case and
  classification against the current registry and actual reports. The aggregate
  deliberately remains failed for the four open requirement groups (Python
  return2, PowerShell session reports1). The goal remains active.
- Both primary original replay hashes remain unchanged. Source supplement and
  generated captures stay ignored. Updated roadmap, backlog, reference spec and
  test instructions; evidence is analysis/native-point-field-regression.md.
- Next: first round pause/reset/resume presentation using existing primary media.
  Original frames2632-2635 exist but have no active_updates because that index
  excludes tail-only callbacks. Add an explicit tail-only association contract;
  do not recapture the full match. Compare actual paused/reset/resumed output,
  recording behaviour/event-consumption discrepancies rather than converting
  known incomplete transitions into tool errors. Preserve existing state cases.
  Stop equivalent point permutations; F2/F4/F5, other P1 scenes, P2 and P3 stay
  in full scope. No Phase4/Phase5 or full hardware acceptance claim.

## 2026-10-01 - Useful-test selection and bounded point references

- Roadmap now requires a named behavioural gap, plausible detected defect,
  implementation decision and finite stopping condition for each test effort.
  Prioritize missing behaviours; stop equivalent variants and diagnostics that
  no longer protect behaviour. Case/script counts are not completion evidence.
- Proceeded with three distinct P1 gaps: deuce, advantage and return-to-deuce.
  Captured 30 original rasters twice from the unchanged two-player replay;
  repeats are identical and the full original callback record is preserved.
  Supplemental media is separate from the primary frozen presentation media.
- Verified all five score/game/mode regions at two stable callbacks per
  transition (30 field observations). Each region has unambiguous independently
  validated original pixels. Existing full-image reference lookup still works.
  Recipe, freeze helper and optional region/supplement lookup are maintained;
  ROM and generated source media remain ignored. No product logic was changed.
- This completes source-reference preparation, not native regression coverage.
  Suite baseline remains 88 cases, 52 green and 36 known red; no aggregate rerun
  or new native cases claimed. Next: three bounded native point-transition
  cases, checking draw timing and completed field pixels, then compiled early
  consumer/frozen-field mutations and strict later-failure rejection. Stop
  equivalent point permutations after those checks pass.

## 2026-10-01 - Two-player status6 and known-failure masking protection

- Added p1-status-6-lifecycle and its reproducible source phase. Initialize once
  from original callback20921, before the point event; hold both physical Amiga
  joystick fire buttons, with both ports configured as joysticks. The pinned
  original reads both groups as16 throughout the complete37-callback window.
  No expected reader returns, pending statuses, selectors or later game states
  are injected. Source parent, initial phase and native inputs are explicit.
- All37 status requests and three completed status raster crops match. The case
  remains exact known red for input/state parity: callback20922, C056 expected17
  versus actual1. This is the combined button/control field; the missing second
  group contributes bit16. Every consecutive post-tail state has only this
  meaningful RAM difference. Existing native second-reader zero stub explains
  it; no product fix or correct two-player controls are claimed.
- Actual retained-text mutation is detected at expiry20956; actual early-clear
  mutation at20955. The earlier input difference remains the overall first
  failure. Mutation-specific differences and classifications are recorded.
- Tightened this case's known-red policy: require precisely the declared input
  mismatch in every one of37 callbacks plus green request/raster checks. Any
  later pixel/state regression or partial change to the known stream is rejected.
  Both actual compiled mutants classify as unexpected red despite the identical
  earlier input failure. Synthetic policy controls also reject later pixels,
  later changed state and partial fixes; first-signature agreement is insufficient.
- Extended the capture/build/reference adapters to the correct one/two-player
  parent and declared physical ports, preserving the one-player defaults. Optional
  consecutive native post-tail observation uses the existing replay routine.
  Original/actual native data, wrappers, executables and PNGs remain hashed.
- Initial20923 experiment found the first requested screenshot could precede
  any completed native generation. Starting at20921 allows three updates before
  that target while preserving the original point event. Invalid missing-generation
  evidence is now explicitly rejected. Source-derived initial state remains
  inactive; no expected display state is written to conceal the prerequisite.
- Full command: python scripts/run_test_suite.py --baseline-check --self-test.
  Aggregate88 cases:52 green,36 exact known red; no unexplained/tool failures.
  Four missing requirement groups cause the expected nonzero completion gate.
  After tightening policy, reran the new native case with both actual compiled
  mutants, then reclassified every actual aggregate report with current policy:
  all classifications unchanged. All new capture/executable/wrapper/PNG hashes
  verified. This added red is another context for an existing input defect.
- All six status messages now have local appearance/expiry comparisons (status1
  remains covered by the first-game prefix). Stop equivalent status windows.
  Updated roadmap, backlog, README, reference spec and evidence notes; historical
  roadmap milestones are now explicitly separated from current suite status.
- Next: actual game-driven point/mode transitions, including equal/advantage and
  return-to-equal, then remaining round/result/restart scenes. Preserve source
  draw timing and detect early/stale/misrouted field updates with a compiled
  mutation. Renderer units alone do not establish when the game requests output.
  P1/P2/P3 and F2/F4/F5 remain in full scope; no suite-goal completion is claimed.

## 2026-10-01 - Game-driven status appearance and expiry

- Added four local one-player lifecycles for status selectors 2/3/4/5. Each
  source-derived initial state precedes its point event; the actual native
  application then runs through message expiry without intermediate expected
  game-state or selector writes. Held fire is an actual joystick input.
- Source timing expectations come from the original drawn-message latch in the
  pinned continuous recording. Three stable original raster crops per case
  validate that projection separately from physical scanout. The exact draw
  callback can still have older pixels; no callback-to-PAL-frame shortcut is used.
- All 140 consecutive native requests and 12 completed status raster crops pass.
  Original/native input flags and timers agree every observed selection;
  meaningful RAM agrees at each raster checkpoint. Initial state is written
  once only; no Python gameplay analogue or product source changes were added.
- Two actual compiled mutations per case are detected: retained text fails at
  expiry; comparing timer254 instead of255 clears one callback early and fails
  there even though the later cleared screenshot is correct. Mutation captures
  preserve source/native simulation state at the raster checkpoints.
- Added scripts/status_reference.py, scripts/run_status_tests.py, four public
  lifecycle recipes and their reproducible phase recipes. Ignored phases are
  rebuilt from the pinned original by the runner. Capture adapters now optionally
  observe live selections and compile private source mutations; existing callers
  preserve their normal path. Reports retain private-wrapper/capture/PNG hashes.
- Full verification: python scripts/run_test_suite.py --baseline-check --self-test.
  Aggregate87 cases:52 green,35 exact known red; all prior classifications
  unchanged, no unexplained failures/tool errors. Four required groups still
  cause expected nonzero completion-gate exit. All new capture, executable,
  wrapper and screenshot hashes verified after the full aggregate run.
- Supplemental checker verification: first differences are ordered by actual
  callback across request/state/pixel observations. Re-evaluated all twelve
  hashed normal/mutation native captures after that ordering change; every
  checked result is identical. No additional emulator capture was needed.
- See analysis/native-status-lifecycle-regression.md for source intervals, exact
  scope and reproducible commands. Roadmap, reference spec, README and backlog
  updated. Stop equivalent one-player status windows; existing prefix covers
  status1. This does not close continuous transition parity or all P1 evidence.
- Next: two-player status6, appearance20925/expiry20956, local start20923. Source
  media and both held-button observations already exist. Extend the native
  adapter to that source parent and both physical ports; preserve the existing
  known second-reader failure instead of supplying its expected input or pending
  message. Remaining point/mode/scene, P2/P3 and F2/F4/F5 scope is unchanged.

## 2026-09-30: native widget renderer matrix complete

Full baseline/self-test completed83 cases:48 green,35 exact known red; no
unexplained/tool failures. Four missing groups remain; goal incomplete. Six
renderer cases add38 selector checks without changing product code or prior
known failure classifications.

Mined existing frozen P1 rasters beyond named checkpoints:32 direct field/value
contexts (point_a0..5,point_b0..3/5/6,games_a0/1/4,games_b0..6,status0..6,mode0..2).
Source recipe/media/association/parent/cartridge hashes verified; field tile
records checked against actual ROM, PNG RGB hashes checked, visible obscuration/
partial writes excluded. Expected pixels are original cropped rasters. Six extra
font-unit checks use identical opposite-field records/bank geometry:point_a6
fromB6,point_b4 fromA4,games_a2/3/5/6 fromB. Reports mark donor provenance; no
original scene/opposite-winner coverage claimed. Aliased score3/5 routes tested.

Private native wrapper drives only renderer inputs, not game RAM. Seven
asymmetric tuples exercise all selector slots through existing sprite upload,
score-pointer patching and blanking commit paths. Original displayed Copper bytes
unchanged during preparation; front/back switch on every commit. Completed
frames account for high-blank commits requiring an extra beam wrap. All outside-
field pixels unchanged across scenes. Game callbacks remain0 (unit scope).

Actual assembled selector-zero and adjacent-field mutations detected by each
field case; separate captures retained. Normal/mutation capture hashes, native
image hashes, alternating pointers and outside-field stability verified after
full suite. Batching prevents six repeated captures and rejects stale/partial
reports. No MAME recapture/new dependency or production fix.

Roadmap/spec/backlog/instructions updated; analysis/native-widget-regression.md
records limits. Stop font-bank snapshot variants. Next: game-driven status
appearance/expiry, using live-produced selections and committed pixels. Validate
source display-state projections against existing original field rasters; do not
feed an expected selection tape into the game/renderer integration. Isolate later
source-derived starts as needed; retain input and independent source-rate mapping.
Remaining P1 timings/scenes, P2 audio, P3 response/side/latency/cadence/deadlines,
F2/F4/F5 and original unobserved winner contexts remain in full scope.

## 2026-09-30: actual native physical-input baseline

Full baseline/self-test completed77 cases:42 green,35 exact known red; no
unexplained failures/tool errors. Four broader groups still cause suite failure;
goal remains incomplete. Product code unchanged. Earlier64-case baseline
preserved all classifications; thirteen physical-control windows added.

Reused unchanged twice-captured input-map oracle:562 source callbacks/1124
reader observations, raw SHAe6fa3b7fb4b5862eb7b4dac70e0a1b74a297764fcc840b2882b6eb58bffbb3da,
fixture SHA3ff7a462b3178d42abbbc5c171337a727e0ab231e4ef556a5d45abef36d4b636.
Source timeline/raw-reader/state agreement verified; all13 neutral+24held+16
release windows validate. Twenty-six shortened/shifted recipes rejected. No
source emulator run/recapture or new external dependency needed.

Native adapter initializes once at captured source callback0 post-tail state,
maps source pad1 to Amiga2 and pad2 to Amiga1, buttons to red/blue, and drives
actual joystick lines at live callback sampling points. Actual reader-return
bytes are collected via real stack return addresses; normalized fields observed
after input update. No expected intermediate RAM writes or Python game model.
Counter checks prove561 consecutive native callbacks and complete last callback.
Full normal/mutated captures and all13 normal/mutation hashes verified.

Green:pad1 Left/Right/Button1. Known red:pad1 Up/Down/Button2 at21/61/221;
all pad2 Up/Down/Left/Right/Button1/Button2 at261/301/341/381/421/461;
simultaneous pad1Right+pad2Left at521. Missing reader value always0 versus
original2/8/32 (pad1) or2/8/4/1/16/32/4 (pad2/simultaneous). Exact callback/frame,
group and values recorded in known-failure policy. These cases expose existing
vertical/second-button and second-reader omissions, not new product regressions.

Actual assembled temporary sampler toggles pad1Right at input_ready. Each case
rejects this wrong/cross-player direction at its otherwise-matching neutral
boundary. Normal/mutated directories separate. Aggregate executes one full batch
and independently classifies13 reports, deleting stale reports and rejecting
failed/incomplete batches as tool errors. No13-fold repeated capture.

Roadmap/spec/instructions/backlog updated; analysis/native-physical-input-
regression.md records details and limits. Byte-format diagnostics may migrate to
named native input intents; no SG reader retention required in final port.
Stop equivalent initial-side control windows. P3 response/side exchange, sampling
edges/real-time latency, ordinary cadence/deadlines remain open. Next: native
point/status/mode field comparisons from retained original rasters, a finite set
of distinct outputs with actual hardware sensitivity. P1 other outcomes/later
regimes, P2 audio and remaining F2/F4/F5 stay in full scope.

## 2026-09-30: native upper-serve rasters and preserved hardware evidence

Full python scripts/run_test_suite.py --baseline-check --self-test completed64
cases:39 green,25 exact known red; no unexplained failures/tool errors. Four
missing groups remain and the goal is incomplete. Production code unchanged.

Added p1-upper-serve: initialize once from validated upper resumed-serve phase
at source4110, retain source global callback/entropy indexing, and compare real
completed rasters at requested4111/4128/4131 (displayed4111/4128/4130). All three
native RAM snapshots match source. Fixed upper-court rectangle x48..207/y0..71
excludes prior scoreboard renderer selections; handoff/fields/continuous round
parity remain separate. Actual pixels retain20px sprite-origin failure: source
white pixels at77/78 on row1, native57/58. Exact known signature4111/x57/y1.

Temporary assembled ADDI.W sprite-origin instruction changed6c to6d in a
separate private executable. Every raster detects the one-pixel change while
simulation remains unchanged. Normal evidence is preserved. Out-of-phase
endpoint4161 and altered initial snapshot were rejected before execution.

Generation display and native audio cases previously reused a capture directory.
Now each case and mutation has its own directory and reports retain capture
paths/hashes. Full suite verifies existing classification unchanged; afterward
all six normal capture-report hashes, display screenshot existence and native
WAV hashes were checked against retained files. No source recapture needed.

Roadmap/spec/instructions updated; analysis/native-upper-serve-graphics.md records
scope, associations and mutation evidence. Stop equivalent upper-start frames.
Next concrete gap: P3 physical controls. Live source inspection shows lower
horizontal/fire sampling and second input group returning0; core replay inputs
bypass those paths. Build original-input-backed press/hold/release/direction/
action native comparisons for both mapped ports, making omissions known red.
Retained P1 returns/handoff/field/outcome/later presentation, P2 audio, F2/F4/F5
and complete ordinary cadence/deadlines remain in full scope.

## 2026-09-30: complete bounded later-regime diagnostic coverage

Aggregate baseline/self-test completed: 63 cases, 39 green, 24 exact known red;
no unexplained failures/tool errors. Four missing groups still fail the suite:
remaining focused F2/F4/F5, P1, P2, P3. Goal remains incomplete. No product fixes.

Two independently repeated original-game extensions preserve every old full
R1/R2 callback and initial state, extending to 13413/27072 updates through
restarted-serve handoff/release. Six complete award intervals cover both ends
and both modes, including match/result/menu/restart. Actual full native runs
completed before signatures were registered; aggregate known-red runs stop at
first failure. Main-thread reference writes are never injected. Expanded match
tail matches 192 callbacks before missing menu setup: the old green 40 prefix
still matches. Five 50-callback direct serves and one 32-callback post-AI-launch
phase pass, with mutation detection. Source interval shortening is rejected.
Contact choice validation now checks actual active flight vector, not input
scratch. All prior contact comparisons remain green.

Exact boundaries, source hashes, failure evidence and limitations are in
analysis/later-regime-regression.md. Roadmap/reference spec/test instructions
updated. The later-phases diagnostic backlog group is closed without claiming
continuous parity or P1/P2/P3 acceptance. Stop equivalent window expansion.
Next: actual native graphics/audio comparisons at distinct retained checkpoints;
remaining contact/court/random behaviours and ordinary execution stay in scope.

## 2026-09-30: bounded upper-return action-timing set complete

Fresh python scripts/run_test_suite.py --baseline-check --self-test completed50 cases:35 green,15 exact known red, no tool errors or unexplained failures. All mutation/signature checks passed. Five broader requirement groups remain open; full goal active/incomplete. Movement exploration remains closed after its32 combinations; upper before/at/after action timing is now also a completed finite boundary. Roadmap records behaviour/gap/plausible-regression/stopping-condition discipline and prioritizes full later-regime/hardware coverage.

Added contact-upper-action-before/at/after with frozen physical pad2 button1 pulses at source frames2005/2006/2007, each held four frames. Independently repeated original-game recordings preserve natural rally prefixes of705/706/707 callbacks. Original input-reader observations consume exactly four action samples. Upper contact remains accepted at callback707/frame2006 for all three, at player Y8/X101 and ball court Y45/X97. Before/at select the same action trajectory; late action preserves the normal launch. Each continuous native case compares all254 bytes at entry/pre-tail/return for722 callbacks and151 ordered PSG events; total2166 callbacks/453 sound writes. Source data/model is never substituted for native execution or injected as intermediate game state.

scripts/contact_reference.py validates the natural prefix, accepted source marker, launched phase, exact action pulse/consumption, release and subsequent flight, then cross-checks the three source launch choices. Aggregate and inventory include this proof. Validators reject missing contact, incorrect sampled action and shortened post-release flight in all cases. scripts/capture_test_reference.py supports explicit capture/verify-only; normal regression never recaptures an oracle.

First generic action-gate inversion was detected earlier in the shared prefix at contact379, so it did not demonstrate the intended boundary. Tightened the temporary mutation to the captured contact geometry, preserving original CCR/stack on every other path. All three now first diverge at707/frame2006, pre-tail ball motion flags: before/at expected66 actual64; after expected64 actual66. Runner requires the intended callback. Temporary artifacts removed; production code unchanged. Source collection happens before this native mutation and is independently repeated.

Fixture SHA256s: before04c4b7fe8dbf07c7ff305fcff7a87b27163a2f0e034a3fdae223f1a3bd713765; at72f5f6c8b5149253aaf8f01571cd264d6feff2a52c3883ad84cb0beb352274e2; after1998b25f5c85cbdf9b86be295920f1cd5e8ce6017daf05914312b85aca50226b. Raw capture hashes and reproduction commands in private source reports and analysis/contact-timing-regression.md. Maintained scripts/policies/cases/conclusions are public; source-derived fixtures/logs stay ignored. Aggregate removes its old report before validating the source cohort to avoid retaining stale success after a failed source validation.

Next action: prioritize complete round/reset/resume and match/result/menu/restart intervals for both modes. Reuse validated full source milestones: R1 first game1204, tail1333, resume1469, resumed flight1566, match11960, menu selection12537, restart gameplay13360, restarted flight13378; R2 counterparts2407/2536/2672/2690/25619/26196/27019/27037. Define ends by actual handoff/animation completion rather than arbitrary short windows. Existing full references stop at the first advancing restarted serve, so their18-callback restart phases do not prove a complete serve. Inspect/extend retained source endpoint where necessary, preserving the old complete prefix and physical control schedule, then derive native cases without expected intermediate writes. Do not expand equivalent upper action timings. Remaining distinct F2 serve/lower-return/geometric edges, F4/F5 and P1/P2/P3 stay in scope.

## 2026-09-30: complete movement bounds and bound further test exploration

Fresh python scripts/run_test_suite.py --baseline-check --self-test completed 47 cases: 32 green, 15 exact known red, with no tool errors or unexplained failures. Five broader requirement groups remain open. F1 bounds inventory establishes all 32 player/row/direction combinations; stop further movement exploration absent a new concrete behaviour gap.

Eight independently repeated original-game rally-row captures preserve natural R2 prefixes. Each also matches an observer-free capture after removing only snapshots. Complete native comparisons from reset pass 6,836 callbacks and 899 PSG bytes across the eight cases. Exact movement-entry/return snapshots prove approach, eight enabled held attempts over both parities, and four reversals. Validators reject wrong rows, blocked holds and false holds for every case. Mutation guards require the tested row/direction/limit; all eight escapes are detected. Source hashes, callback intervals and reproduction commands are in analysis/movement-regression.md. Private fixtures/reports remain ignored. Existing full matches and exact upstream transition failures are preserved; no product fix applied.

The initial upper-down candidate crossed a point award and changed mode, so it was rejected rather than weakening validation. The accepted case starts natural callback930/frame2229 and stays in the same enabled row and controller ownership. Movement registries now use OBSERVED_BOUNDS/MOVEMENT_PHASES names because both receiver and rally rows use them.

Roadmap now requires each proposed test to name behaviour, concrete coverage gap, plausible regression and finite stopping condition. Case/trace/branch counts alone are not progress. Preserve the full objective while avoiding exhaustive equivalent variants. Next priority after the bounded F2 timing set is missing round/reset, result/restart and hardware output coverage.

Source-only F2 discovery: original two-player rally upper contact remains accepted at callback707/frame2006 for pad2 action onset frames2005/2006/2007 held four frames. Before/at contact select launch-state bytes 56..65 =108c257e1b612d7b47558c257e1b612d; late onset retains normal =00914e521b612da0472a914e521b612d. All share contact sound C5/0D/DF/D0. These one-pass discovery captures under build/tests/contact-timing-discovery are not frozen references or native acceptance. Next action: freeze just these three cases with repeated source captures, unchanged natural rally prefixes, accepted-return marker and captured trajectory checks, then actual continuous native comparisons plus mutation detection. Do not infer that action controls contact acceptance: source geometry accepts contact before action modifies the trajectory.

## 2026-09-30: complete receiver-row bounds with three green later phases

Current status: fresh python scripts/run_test_suite.py --baseline-check --self-test completed 39 cases: 24 green and 15 exact known red, with no tool errors or unexplained signatures. Mutation/signature checks passed. The three additional continuous reds reproduce the existing round-transition defect; they are not new product regressions. Five missing requirement groups keep the goal active and incomplete. Movement bounds now establish 24 of 32 combinations; only both row-three rectangles remain.

Added lower receiver left/up/down observed source captures, repeated twice and checked against independent observer-free recordings. Natural R2 prefixes and main-thread effects are preserved. Mode bit 4 assigns lower movement to physical pad2. Left starts X56 and reaches X40, holds eight enabled attempts and reverses through 41/43/44/46. Up starts Y152 and reaches Y128, holds eight enabled attempts and reverses through 129/131/132/134. Down starts Y152 and reaches Y153, holds eight enabled attempts and reverses through 152/150/149/147. Exact movement snapshots establish row two, enabled movement, both step parities and actual reversal; stationary blocked movement cannot count.

The source-derived native phases initialize once from source callbacks 4853/5315/4569, then carry actual state for 26/30/24 callbacks. All 254 state bytes at entry/pre-tail/return and nine PSG writes per phase match. Targeted mutations detect X40->39 at source4865/frame6164, Y128->127 at source5332/frame6631, and Y153->154 at source4571/frame5870. Temporary mutation artifacts removed. Shortened phase recipes that omit the full held/reversal span are rejected.

Continuous parents retain 4879/5345/4593 source updates respectively. Each actual native comparison reaches the unchanged known-red callback2536/frame3834: callback-entry deferred display setup request at RAM offset2 expected129 actual1, tail-only. Exact signatures are registered without broadening acceptance. Parent fixture SHA256: left 6b6ea9b7657d3db68ef974f98d99c34a38766583041b645d7920754057e2d19a; up 52682944d95d43d1b5f027ed59671f9d1737d23c57dac31a689e7926c3ddd3f3; down 9936b6cf4581b9f56ea4e6dbff3427935433b4831da968bf6e58acd7fc147ab7.

Reproduce: python scripts/capture_test_reference.py --case movement-lower-receiver-{left,up,down}-bound (one case per invocation); python scripts/phase_reference.py; python scripts/run_regression_tests.py --case movement-lower-receiver-{left,up,down}-phase --self-test; python scripts/inventory_match_references.py. Private fixtures and reports remain ignored. Source policies, case recipes and conclusions are maintained. No product code or source oracle model changed.

Next action: establish the eight row-three movement limits using legitimate source controls and exact before/after movement observations. Lower row three spans X40..199/Y98..153; upper spans X64..175/Y7..62. Select natural serve/rally windows, accounting for contact animation and outcome movement blocking, then preserve complete approach/held/reversal intervals in independent cases. F2/F4, later phases and native P1/P2/P3 remain required in full before implementation cleanup.

## 2026-09-30: green later lower-receiver phase with explicit continuous red

Current status: fresh python scripts/run_test_suite.py --baseline-check --self-test completed33 cases:21 green,12 exact known red, no tool errors or unexplained signatures. All mutation/signature checks passed. The additional known red is a newly registered continuous source prefix at the existing transition defect, not a new product regression. Five missing groups keep the goal active/incomplete. Movement inventory establishes21 combinations and leaves11: lower receiver left/up/down plus both row-three rectangles.

Added movement-lower-receiver-right-bound: two observed MAME captures repeat through4593 updates (4321 gameplay,272 tail-only),690 PSG bytes,100 between-callback writes and duplicate source frames3834/5699. Observer-free source recording matches after removing snapshots. Natural R2 prefix is preserved through4569 callbacks including ordered main-thread effects; only observer-added debugger sequence numbering is normalized. Mode92 swaps controller ownership, so physical pad2 now controls lower. At frames5869-5886 it holds Right, at5887-5890 Left, then releases before stop5892. Exact movement snapshots prove row two enabled, X192 approaches199, eight held attempts at callbacks4580-4587, and four reversals4588-4591 yield198/196/195/193. Parent fixture SHA ee00135bb5a13df54068f79931bb908eed943c77a8a14f4e4e1db04eca90e6c3; raw source SHA d6ab21cbe98acebdc89c24b11a29d113564dec2269c560de8e7b36049c8a28f5.

The continuous native parent retains exact known-red callback2536/frame3834, callback-entry deferred display setup request expected129 actual1 at RAM offset2, tail-only. The existing unimplemented main-thread round setup/tail dispatch explains it; no signature widened or product fix applied. It stays registered alongside the original full R2 replay.

Added movement-lower-receiver-right-phase: initialize once from source post-tail callback4569 and carry actual native state through24 callbacks4570-4593. Full254-byte entry/pre-tail/return comparisons and nine PSG bytes pass. Targeted boundary escape199->200 is detected local callback6/source4575/frame5874, pre-tail sprite record1 X expected199 actual200. Temporary mutation source/executable removed. Phase fixture SHA aef80d00460096c9e4939e0dc08cf1ec40852eef0afca3d55bf406b30559950d. Phase validation reconstructs the exact parent/recipe and requires its span include the complete approach/hold/reverse evidence; an eight-callback shortened phase is rejected. No expected intermediate writes injected, and green later phase does not imply upstream continuous parity or hardware presentation/input/timing acceptance.

Reproduce: python scripts/capture_test_reference.py --case movement-lower-receiver-right-bound; python scripts/phase_reference.py; python scripts/run_regression_tests.py --case movement-lower-receiver-right-phase --self-test. Parent continuous comparison is available with its bound case ID, and baseline aggregate verifies its exact first-failure signature. Private source logs/reference stay ignored. See analysis/movement-regression.md and tests/reference-spec.md; inventory includes the source limit and exact later-phase interval.

Next action: apply this natural-parent plus independent-native-phase pattern to lower receiver left/up/down. Source4854/frame6153 starts X56 under mode9A; twenty held-left callbacks plus four reverse-right fit its27-callback row-two window and can reach X40. Source4570/frame5869 starts Y152 under mode92 and permits a held-down approach153. Source5316/frame6615 starts Y152 and its33-callback window permits up-to128, eight held attempts, then four reversals. Pad2 controls lower in these modes. Preserve observed pre-movement row, exact source prefix/main-thread events (normalize only debugger sequence numbering), source initial-state provenance and unchanged full replays. Then finish both row-three rectangles and other F2/F4/later-phase/P1/P2/P3 requirements in full.

## 2026-09-30: all four upper receiver limits green

Current status: fresh python scripts/run_test_suite.py --baseline-check --self-test completed 31 cases: 20 green, 11 exact known red. No tool errors, unexpected signatures or unexplained failures; all mutation/signature checks passed. Five open requirement groups remain and the full goal stays active/incomplete. Existing full replays and product code unchanged.

Added movement-receiver-left-bound, movement-receiver-up-bound and movement-receiver-down-bound. Each independent source capture preserves the first 212 R2 callbacks through frame1511 exactly, then presses pad2's requested direction at frame1512 through1535 and reverses at1536 through1539. Finite stop1541 is before bounce changes the row at1542. Each source fixture contains 242 consecutive callbacks and 20 PSG bytes; observed captures repeat twice and match a separate observer-free recording after removing snapshots. Exact pre/post movement state proves receiver row two and enabled movement, not an animation block.

Source upper limits: X88 approaches64 (left), Y8 approaches7 (up) and Y8 approaches31 (down). Final eight held attempts are callbacks229-236; four reversals237-240 produce X66/67/69/70, Y9/10/12/13, and Y29/28/26/25 respectively. The actual native routines pass every 254-byte entry/pre-tail/return comparison and all sound writes. The source validators reject animation-blocked held attempts. Receiver contract and mutation code are shared across directions while retaining each independently measured oracle.

Targeted native boundary-escape mutations detected: left at callback229/frame1528, pre-tail sprite record5 X expected64 actual63; up at215/frame1514, sprite record5 Y expected15 actual14; down at228/frame1527, sprite record5 Y expected39 actual40. The Y sprite observations include descriptor offset; actual player-coordinate limits remain7 and31. Mutations affect only the active receiver row at its tested boundary; temporary source/executables removed.

Fixture SHA256s: left 0538d1c317b789cba8c36ce1f6286bd355590285e76b22e1b388248e3c9e259e; up 086cb9bd6e8aa341137450a5c011863b6a1d3807fd47459c56307eef419c9640; down db1a21184f005da1b8f8a970b8ba9d73e4c4794083043857fb9b81b6d0f7bcd2. Raw capture hashes and independent ordinary hashes are in each private fixture/manifest. Reproduce using python scripts/capture_test_reference.py --case <case-id> then python scripts/run_regression_tests.py --case <case-id> --self-test. See analysis/movement-regression.md and build/tests/<case-id>-capture. Combined inventory now records20/32 movement combinations, with12 missing: four lower receiver limits and eight row-three limits. This is not overall certainty or complete F1; ordinary native hardware input/presentation/timing remain separate.

Next action: capture lower receiver limits using natural full-R2 service prefixes, then derive independent native phases because the known continuous failure at2536 obscures them. Exact source lower row-two windows:4570-4595/frame5869 onward, mode92 starting Y152 X192;4854-4880/frame6153 onward, mode9A Y152 X56;5316-5348/frame6615 onward, mode92 Y152 X184;5779-5814/frame7078 onward, mode9A Y152 X56;6079-6109/frame7378 onward, mode92 Y152 X184. Mode bit4 is set, so pad2 now controls lower. The first window is suitable for right199/down153, the second for left40, and the longer third for up128. Verify actual held/reverse attempts via movement snapshots. Preserve parent provenance and source main-thread prefix without injecting intermediate writes; observer-added raw sequence numbers need normalization when comparing older between-callback event metadata. Then finish both row-three rectangles and remaining F2/F4, later-phase/P1/P2/P3 requirements in full.

## 2026-09-30: exact source movement observations and green receiver limit

Current status: fresh python scripts/run_test_suite.py --baseline-check --self-test completed 28 cases: 17 green, 11 exact known red, no tool errors or changed signatures. All existing mutation/signature checks passed. A stronger targeted receiver-limit mutation was then checked separately against the unchanged normal executable and passed detection. Five open requirement groups remain; full goal incomplete and active.

Added optional read-only source snapshots immediately before both player movement calls at 13B9 and after them at 13BF. The ROM bytes confirm CALL 1404 followed by CALL 145D. Debugger actions print RAM and resume; no CPU/game state writes or instruction stepping. scripts/capture_movement_observations.py repeats each extended capture twice, strips only its snapshots and restores raw sequence numbers, requiring byte-for-byte equality to the prior ordinary source capture. Both complete rally and full R2 passed. Raw observed hashes: rally 135724ae50a43355f5be4f3391908c3b63aeb01e11446eeec8d54de893db1912; full R2 8b6d22f6b409c58fae2c577d1362b26ee128e7e70c92c3ad4b4200f77d70c12a. Full R2 raw includes one extra callback after the retained parent; indexed observations explicitly restrict to the 27,037 retained updates plus initial callback. No frozen parent reference replaced.

The observations found a reachable upper receiver row-two interval in the alternate lower serve: source callbacks 1321-1355 begin at X160. Added movement-receiver-right-bound, preserving all first 1,320 R2 callbacks through frame 2619 and then holding pad2 Right at 2620-2642, Left at 2642-2646. Exact pre/post movement snapshots establish row two, enabled movement and controller ownership, approach to X175, eight stopped attempts across both step parities, and four reversal coordinates 173/172/170/169. Ordinary source collection disables hooks unless explicitly declared; this case additionally captures observer-free source output and requires exact raw equality after removing snapshots before freezing. Source row corruption is rejected.

Two observed captures agree across 1,348 callbacks and 190 PSG bytes; actual shared assembled gameplay routines match all 254 state bytes at entry/pre-tail/return plus all sound events. Targeted self-test modifies native upper movement only at row-two X175, causing boundary escape to X176: detected callback 1331/frame2630, pre-tail sprite record 5 X expected175 actual176. Normal source/executable unchanged; temporary mutation source and binary removed. This accelerated comparison does not establish ordinary native input/presentation/timing acceptance.

Raw source fixture capture SHA256 5895f458630c61769b3658899e64b54dcce9e4f9a45ad9c47e993caa34fc2c3f; fixture SHA256 5d9aabd25124f451f35014fa87e247acde56f036019674259f29e23cab596530. Reproduce with python scripts/capture_test_reference.py --case movement-receiver-right-bound and python scripts/run_regression_tests.py --case movement-receiver-right-bound --self-test. Private capture/logs/report include without-observer.tsv under build/tests/movement-receiver-right-bound-capture. Observer reports live under build/tests/<case>-movement-observations. See analysis/movement-regression.md.

Fixed combined coverage accounting to track every player/row/direction, rather than incorrectly completing an entire row after observing one direction. Seventeen of 32 movement combinations are established; 15 remain, with rows two/three still incomplete for both players. This is a bounds inventory, not a percentage of overall game certainty. No goal scope, product defect or known-red signature changed.

Next action: use the exact observer intervals to capture the other seven receiver-row limits, selecting natural service-side starting positions close enough to reach the limit within each transient handoff. Upper row-zero X80 can reach the negative limit X64; alternate row-one X160 reaches positive175 as now proven. Lower receiver intervals first appear in full R2 at source4570-4595, then 4854-4880, 5316-5348, 5779-5814 and 6079-6109, from observed starting X192/56/184/56/184. Longer intervals permit Y128 approach/hold/reversal. Preserve physical side ownership, natural prefixes and complete source snapshots; add source-derived native phase cases where the existing 2536 failure obscures those later tests. Then obtain remaining row-three limits and F2/F4 behaviours, while later-phase/P1/P2/P3 scope remains required in full.

## 2026-09-30: green six-return two-player rally and completed R2 rally requirement

Current status: fresh python scripts/run_test_suite.py --baseline-check --self-test completed 27 cases: 16 green and 11 exact known red, with no tool errors or unexpected signatures. Mutation/signature checks passed. The R2 same-rally requirement is completed with independent supplementary evidence; five remaining requirement groups keep the full goal incomplete and active. Full R1/R2 records and their known transition failures are unchanged.

Added two-player-rally: frozen physical controls from reset produce six alternating accepted returns at callbacks 707/762/816/870/925/979 (upper/lower alternating), then deliberate controller movement away from contact starts at source frame 2289. Original point award at callback 1050/frame 2349 changes point codes 2/0 to 3/0. Two original-game captures agree byte-for-byte across 1,390 continuous callbacks and 290 PSG bytes, with no refresh reads or between-callback RAM writes. The actual assembled gameplay comparison passes all 254 bytes at entry/pre-tail/return and all sound bytes. Temporary ball-X mutation is detected at callback 1, pre-tail, court X expected 212 actual 213; temporary source/executable removed.

Source geometry guided discovery: contact Y separation below four, X below seventeen, and height below twenty-nine. Moving upper forward to Y31 caused low contact (height six), special short trajectory and net failure. Upper Y8 plus lower Y128 gave two returns but lower horizontal lag sent the return outside the sloping left court boundary. Keeping lower deeper at Y152 gave enough travel time for alignment; diagnostic steering then produced 56 consecutive alternating returns. Only physical controller fields changed. The accepted policy freezes actual controls through six returns and then a deliberate miss; it contains no state-dependent input or cartridge RAM writes. Diagnostic scripts/captures remain private under build/tests/rally-discovery.

scripts/rally_reference.py indexes actual accepted-launch markers and captured launched-flight/contact-animation states by source scoring boundaries, requires at least four returns by both players in a completed rally, and verifies its deliberate physical miss precedes the award. It rejects removal of all lower-return markers. Captured per-return ball court/display positions, active vectors and both player positions are included in the report. Missing, one-sided or cross-point return accumulation cannot close the requirement. The aggregate preserves the actual full R2 test and adds this independent green case rather than replacing its expected data.

Reproduction: python scripts/capture_test_reference.py --case two-player-rally; python scripts/run_regression_tests.py --case two-player-rally --self-test; python scripts/inventory_match_references.py. Raw capture SHA256 01edaffe41ef371983620330729ac7a692e3f76108fd95f465c046b11b4f8208; fixture SHA256 2ebf77b07faa0af4e7504094f5395b38b49cb5ddbdc173ccdb0728aeff1cbcbf. Private evidence: build/tests/two-player-rally-capture and tests/reference/two-player-rally.json. See analysis/two-player-rally-regression.md. This simulation/input-reader comparison does not establish ordinary native input, audible output, rally rasters or timing hardware acceptance.

Next action: obtain read-only exact movement-entry observations for candidate row-two/three intervals, confirming instrumentation leaves ordinary source replay state/events unchanged. Index reachable bounds and contact geometry in the successful rally and existing full matches, then obtain only missing F1/F2/F4 cases. Distant row-two limits may be restricted by transient phase duration; prove reachability instead of fabricating animation flags. Later phase, P1, P2 and P3 adapters/captures remain required in full; no product defect fixed or known red weakened.

## 2026-09-30: green alternate-service movement bounds

Current status: fresh python scripts/run_test_suite.py --baseline-check --self-test completed 26 cases: 15 green, 11 exact known red. No tool errors, unexplained failures or changed known-red signatures. Mutation and signature checks passed. Six explicit missing requirement groups remain; the overall goal is incomplete and active.

Added movement-alternate-serve-bounds, a physical-control-only sequence from reset. It preserves the first 485 original R2 callbacks exactly through frame 1784, including its natural point award and player reset. Scoring toggles mode bit 3; initialize_round_state selects animation row 1 for both players. Leaving actions released then holding down/up/down and left/right/left proves all eight row-one limits: lower Y 152/153 X 40/111, upper Y 7/9 X 128/159. The upper reset starts at X 160 outside the positive destination range, so the sequence first moves left; no clamp or fabricated position is assumed.

Two MAME captures agree byte-for-byte across 1,322 callbacks and 50 ordered PSG bytes. Actual shared native routines match all 254 compared bytes at three boundaries per callback and all sound events. Temporary lower-X mutation is detected at callback 1, pre-tail sprite record 1 X expected 192 actual 193; temporary source/executable removed. Source validator checks natural-prefix equality to its hashed R2 parent every run; an altered point/reset prefix is rejected. This remains simulation/input-reader replay evidence, not ordinary native controller/display/timing acceptance.

Source capture SHA256 b0a91d89f4472f1f4a1f0e2c2f6fc608bc44b232279dceb5d2207913dcd811ad; fixture SHA256 592a872488874a9099767f31a56e3cf892ecef37f31ebf61e2adde4305cf15e5. Private raw capture/log/report: build/tests/movement-alternate-serve-bounds-capture. Reproduce with python scripts/capture_test_reference.py --case movement-alternate-serve-bounds and python scripts/run_regression_tests.py --case movement-alternate-serve-bounds --self-test. Combined coverage inventory validates both service-row cases and reports only movement rows two and three remaining per player. Details in analysis/movement-regression.md.

Static follow-up: receiving-player row two is selected by the serve handoff; first R2 upper row-two post-body interval is callbacks 213-242 before bounce at 243. Bounce replaces both animation row selectors with row three. Completed serve/contact animation also enables row-three movement. This is a candidate-interval index, not proof of every row-two limit being reachable or held. Distant row-two limits may be constrained by its transient duration and starting service position; establish actual reachability before imposing a hold or constructing an explicit documented injection.

Next action: obtain exact movement-entry observations for rows two/three and reachable contact geometry. Determine which bounds can be reached during those phases, then record only missing legitimate sequences; use the row-three forward movement/contact analysis to obtain the required longer two-player rally. Preserve all source references and full match replays. Later-phase/P1/P2/P3 requirements and all known defects stay open; no product fix is included.

## 2026-09-30: green original-game initial movement bounds case

Current status: fresh aggregate python scripts/run_test_suite.py --baseline-check --self-test has 25 registered cases: 14 green, 11 exact known red, no unexpected signatures or tool errors. All assembled-code and hardware-output mutation checks passed. Six explicit requirement groups still keep the suite incomplete; the goal remains active.

Added movement-serve-bounds: select two-player mode from reset, keep fire released, and physically hold down/up/down then right/left/right for both controllers. Two independent MAME captures agree byte-for-byte across 742 consecutive callbacks. Both players' initial animation row stays zero, movement is unblocked, and all eight limits have observed approach, eight stopped accepted attempts spanning both counter parities, and four accepted reversal attempts with a response. Lower Y 152/153, X 128/199; upper Y 7/9, X 80/111. Narrow Y ranges do not move on every accepted attempt. No RAM state injection, Python gameplay oracle, PSG events, refresh reads or between-callback writes.

The native full-state comparison passes all 742 callbacks at entry/pre-tail/return (254 bytes each). Temporary lower-X increment is detected at callback 1, pre-tail sprite record 1 X expected 192 actual 193; mutated source and executable are removed. Altered source held input is rejected by the evidence validator. This is accelerated simulation/input-reader evidence, not ordinary physical Amiga joystick or presentation timing acceptance.

Added finite focused-source fixture construction alongside existing transition fixtures. Rebuilt round-transition, full R1 and full R2 from their retained raw streams using the refactored shared assembly helper: every resulting fixture is exactly unchanged. Original milestones and transition checks remain required for those match references. Focused captures require a final complete callback and finite source stop, with the F1 behavioural recipe enforced separately before freezing and before native execution.

Reproduction: python scripts/capture_test_reference.py --case movement-serve-bounds; python scripts/run_regression_tests.py --case movement-serve-bounds --self-test; python scripts/inventory_match_references.py. Source capture SHA256 352b2a0849c138140d92f41ab7b60253129b5ceba5bc9d514652c3f24129d22e; fixture SHA256 9741dfe015d72e6db81bff5e624431521273f4463f179669d50e048a8bd9f711. Private raw captures/logs/report are build/tests/movement-serve-bounds-capture; coverage-inventory.json now includes exact F1 intervals. See analysis/movement-regression.md for all static bounds rows and coverage limits.

Next action: read the animation-row writers in reset/contact/serve paths and index legitimate R2 intervals for rows 1-3. All four unblocked post-body row selections occur for both players, but this alone is not proof of the actual within-callback bounds row or approach/hold/reversal. Obtain only missing physical-input sequences, retaining reachable source phase provenance. Longer same-rally returns and all remaining later-phase/P1/P2/P3 requirements stay open. No product defect fixed or known red weakened.

## 2026-09-30: explicit suite coverage backlog and evidence inventory

Current status: the last full aggregate remains 24 cases, 13 green and 11 exact known red. This documentation/inventory change does not claim a fresh emulator run, new behavioural coverage or any product fix. Six requirement groups remain open.

Added tests/coverage-backlog.json with concrete R2 rally, F1-F5, later-phase, P1, P2 and P3 tasks. The aggregate runner reads and embeds the same backlog rather than maintaining vague duplicate descriptions. The goal remains a complete reference-backed suite followed by concise maintained native Amiga implementation; original RAM/register/PSG checks are temporary diagnostics, not architectural obligations.

Extended scripts/inventory_match_references.py to validate all 13 phase fixtures against their source parents and record exact callback intervals, comparison scope and explicitly historical native results. build/tests/coverage-inventory.json is private generated evidence. Source matches retain hashes and observed score/counter/random data. R1: 52 primary wraps and both refresh bits; return markers absent, so no zero-return claim. R2: 105 wraps, 11 lower and 23 upper returns, none in a qualifying same-rally four-return sequence.

Verification: python scripts/inventory_match_references.py passed parent validation. All known-failure classification/signature rejection checks passed via run_test_suite.verify_failure_policy; six open groups retained. Gameplay, frozen references and failure signatures unchanged, so no repeated emulator suite was necessary for this inventory-only change.

Next action: read source movement bounds and correlate frozen R2 control/position intervals, identifying the missing F1 rows and legitimate inputs needed for the R2 rally. Use source analysis first; obtain new twice-identical recordings only for actual behavioural gaps. Do not count source capture or historical phase reports as native acceptance.

## Current checkpoint (2026-09-30, measured serve envelope and green native mute)

Extended scripts/run_audio_tests.py with separate pitch, measured-envelope and mute criteria. The uninterrupted native run now reaches callback 42, with all 254 compared source state bytes matching and ordered PSG events retained. The source first serve has decay steps 0-7, a held step, then 8-14 and final mute at callback 40. The waveform calibrator uses actual frozen mono PCM, requiring all other source channels/noise muted, and extracts the two plateaus by lower/upper quartiles. Levels are identical with 2/3/4 ms edge trims; peak overshoot is excluded rather than used as amplitude. No waveform or game model generates the expected levels, and no numerical waveform tolerance is inferred.

Registered p2-first-serve-envelope: 15 source plateau measurements range from 8191 at attenuation 0 to 326 at attenuation 14. Nearest 0-64 Paula volumes are 64/51/40/32/25/20/16/13/10/8/6/5/4/3/3. Fourteen native steps match; at callback 39 actual AUD3VOL is 2 rather than 3. Signature: update 39, paula-events-applied, Paula volume for source tone 2, expected 3 actual 2. This identifies the final nonmute entry of paula_volume_table independently of the existing pitch error. No product correction is applied.

Registered p2-first-serve-mute: at source callback 40 all source tone/noise channels are muted; actual mapped Paula volumes (channels 0,1,3) are [0,0,0], so this criterion is green. It validates the hardware mute action, not an unmeasured analog/filter decay threshold or the remaining sound classes. Pitch and amplitude failures remain separately visible.

Self-tests mutate the unique private assembled volume table: full volume 64->63 for the envelope case, and mute 0->1 for the mute case. The same audio comparator detects changed output at callback 17 and a real green-case failure at callback 40 ([0,0,1]). Normal executables and audio outputs are rebuilt/recaptured last. No production source, source capture or expected waveform changes remain. The existing pitch instruction mutation also remains checked.

Fresh python scripts/run_test_suite.py --baseline-check --self-test completes all 24 cases: 13 green, eleven exact known red, no unexpected registered results. Mutation and changed-signature/unexpected-pass policies pass. Reports include build/tests/p2-first-serve-envelope-report.json, p2-first-serve-mute-report.json and suite-report.json. No process is pending. Six missing groups still cause failure: same-rally R2, meaningful F1-F5 inventory/cases, remaining phases, remaining P1, complete P2 and P3. Goal remains active and incomplete.

Next: extend native audio observations to the remaining retained effects and callback regimes, including event/mute timing and waveform response; complete P1 variants/transitions and P3, and resolve the remaining behavioural inventory/rally/phase gaps. Preserve independent capture provenance, continuous histories and separate passing criteria when another property is red.

## Current checkpoint (2026-09-30, repeated P2 source audio and actual Paula pitch failure)

Added capture_audio_policy.lua and capture_source_audio_reference.py. Both frozen full source replays run twice from reset, observing PSG IO and actual frame timestamps without writing game state. The accepted callback hash remains exact. WAV, PCM, PSG timestamps and frame timestamps repeat byte-identically. R1: mono PCM16 48 kHz, 11,808,001 sample frames (246 seconds plus one sample), 4,240 timed writes; R2: 22,752,001 frames (474 seconds plus one sample), 6,299 writes. Timing records preserve integer seconds/attoseconds. Finite emulated stop guards complete each process; no capture is restarted or terminated on an observation timeout.

Added source_audio_reference.py and freeze_audio_reference.py. R1 associates 3,353 raw PSG writes, 3,352 in the retained parent timeline; R2 associates 5,423 raw/5,422 retained. Extra final raw extent remains distinguished. Eighteen WAV intervals across both parents cover both serves/returns, point, round tail/resume, match award/result sound and restarted gameplay, with tone/attenuation state and callback provenance. Full intervals preserve phrases beyond intermediate silence. No active gameplay noise or noise-control write is observed; noise-volume mute FF and reset output are explicit. Private frozen evidence is under tests/reference/audio/manifest.json (SHA256 c2959d424d71ec67f2e6ad5688ffdb85af5bb896c96384906f09cc675d8064f4). Complete P2 comparison is false; response/onset/level measurements and all native intervals remain required.

Pinned MAME mame0289 primary sources establish SC-3000 SN76489A clock 3,579,545 Hz, register latching, non-Sega zero divisor 1024 and attenuation rules; summarized locally in analysis/source-audio-regression.md with links/credit. The decoder interprets captured hardware commands and generates no expected waveform or game logic. A changed frozen timestamp file was rejected; original bytes were restored and reverified.

Registered p2-first-serve-pitch via scripts/run_audio_tests.py. Native capture observes paula_events_done, verifies ordered PSG bytes, reads actual custom registers and records emitted audio. Native WAV is stereo float32 44.1 kHz; audio_wave.py reads its extended RIFF format explicitly (standard Python wave rejects it). At source callback 17, tone 2 divisor 213 is 525.167987 Hz. Four-sample Paula output requires nearest integral period 1688 at stock PAL 3,546,895 Hz; actual AUD3PER is 1687 due ratio 507/64 versus exact 7.927029832. Signature: update 17, paula-events-applied, Paula period for source tone 2, expected 1688 actual 1687. Native crossing estimate about 525.622 Hz is consistent with the register, but introduces no unmeasured waveform tolerance. No product fix is applied.

The self-test mutates the unique private assembled MULU.W #507,D3 to #508, observes actual period 1691 and a distinct executable hash, then rebuilds/recaptures the normal executable last. Normal outputs/report remain authoritative; no product source mutation or expected-source change remains. All compared source state bytes match through callback 20. Fresh python scripts/run_test_suite.py --baseline-check --self-test completes 22 cases: 12 green, ten exact known red, no unexpected registered results. Gameplay/image/audio mutation and signature policies pass. Reports: build/tests/suite-report.json and build/tests/p2-first-serve-pitch-report.json. No process is pending.

Six missing groups still fail suite completion. Next: extend native P2 through envelope/mute, timing and the remaining retained effects/regimes; finish remaining P1 variants/transitions, P3 hardware timing/input and R2 same-rally/F1-F5/phase gaps. Source waveform response/stereo/filter differences must remain explicit rather than inventing a global tolerance. Goal remains active and incomplete.

## Current checkpoint (2026-09-30, completed native rasters and 42 green field comparisons)

The native capture adapter now observes actual blanking commits and recorded source entropy. Replay signs come directly from frozen R1 refresh_reads, not the old Python analogue. A private wrapper changes only the existing replay entropy include path; production source remains unchanged. LONG_GAME_REPLAY also enables existing diagnostic logging, so ordinary-build timing/performance is not inferred from this instrumented run. Actual refresh helper breakpoints verify consumption order/count/value, including partial current callbacks correctly. Source fixture and media hashes are checked. Finishing a raster can pass an adjacent callback; separated targets are required, and already-passed targets fail explicitly instead of fabricating state.

Added scripts/associate_presentation_generations.py. Native front-Copper commits identify prepared generations and their visible frames; beam-wrap captures identify completed rasters. Source selection requires the corresponding callback to be active and captured VRAM sprite records to equal its recorded entry buffer. Frozen raster/VDP associations supply original captured pixels; multiple candidate images must be identical. No native visual similarity or guessed lag chooses the oracle. A changed source VRAM file was rejected, its bytes restored, and the original association reverified.

Registered p1-moving-prefix and p1-score-status-prefix along one uninterrupted actual native history at requested callbacks 17/63/138/168/471/809/1207. Completed frames show generations 16/62/138/168/471/809/1206, associated with source VDP frames 1315/1361/1437/1467/1770/2108/2505 and original pixel windows 1314-1318/1363/1436-1438/1467-1469/1771-1772/2109-2110/2506-2507. All 254 compared simulation bytes match at every retained checkpoint. Seven whole-screen checks retain the explained 20-pixel sprite-origin defect; first difference is generation 16, presentation-generation-whole_display, pixel (74,12), expected 000000 actual cc55bb. Six fields per checkpoint (points, games, status and mode) produce 42 exact green comparisons, covering consecutive point graphics, IN appearance/expiry and the first game tally.

Final instrumented run reaches 1208 completed callbacks, records 998 commits (all vpos<44 or >=236), and consumes exact source choices at updates 103/435/466 (bit 0) and 772/800/803/805/1110 (bit 1). Observed native field generations change at 136/167/471/502/808/839/1206, with visible frames retained in the report. This is prefix evidence, not complete P3 hardware or main-thread transition proof. Instrumented executable SHA256 91e8b8d60a9bb0bd79c5200d0ee398fe8b63b79867652bde3090934ccfeb8365; normal executable remains unchanged.

Fresh python scripts/run_test_suite.py --baseline-check --self-test completed all 21 cases: 12 green, nine exact known red, no unexpected registered results; mutation/signature checks passed. Reports: build/tests/suite-report.json, build/tests/p1-moving-prefix-report.json, build/tests/p1-score-status-prefix-report.json and build/tests/native-presentation-recorded/report.json. An earlier four-checkpoint aggregate also passed its registered baseline, then the cases were extended and the final full aggregate rerun. No process remains pending. Six explicit missing groups still fail suite completion; other score/status variants, both complete serve paths, remaining rally/outcomes and later transitions are not covered by this prefix.

Next: extend generation-aware native comparisons to the remaining P1 checkpoints, with appropriate source/native regimes; collect repeatable source WAVs and event intervals for P2, then native audio comparisons. Complete P3 and the remaining R2 same-rally/F1-F5/phase gaps. Preserve continuous replays, known reds and independent source provenance. Goal remains active and incomplete.

## Current checkpoint (2026-09-30, callback-aligned native graphics and sprite origin defect)

Added scripts/capture_native_presentation.py. The assembler listing supplies code offsets without changing executable bytes; Copperline LoadSeg supplies the relocated hunk. Conditional simulation_update breakpoints record exact callback counts, actual state, beam position, readiness, front Copper address and screenshots. Physical joystick fire drives the normal application; no game RAM is written or scheduling bypassed. At 0/17/18/63 completed callbacks all 254 compared source bytes match. Later diagnostic checkpoints 134/135/136/166 differ at AI target C076 (212 source/172 native in this run) after an uncontrolled native refresh choice. They are not deterministic presentation comparisons; partial rasters remain diagnostic.

Registered p1-upper-player-placement at completed update 17, with all 254 source bytes matching. Source crop (60,0)-(112,40) is identical throughout frames 1314-1320; native beam line 166 is past those scanlines. The pink silhouette is exactly translated (-20,0): source X88-103/native X68-83, both Y12-39, 254 pixels each. The native sprite origin adds $6c instead of the viewport's $80. Known first divergence: update 17, lower-serve-launch-upper-player, pixel (74,12), expected 000000 actual cc55bb. No product fix is applied. A five-second initial-state comparison was rejected because gameplay continues; experimental cases were removed and no failure registered from that experiment.

Fresh python scripts/run_test_suite.py --baseline-check --self-test completed 19 cases: 11 green, eight exact known red, no unexpected results. Mutation/signature checks passed. Executable SHA256 remains d974224c00c1c27b60cb5eda75009b21bfbede9d8b50a0376c9dd78a7c38a1ed. Reports: build/tests/suite-report.json, build/tests/p1-upper-player-placement-report.json and build/tests/native-presentation-alignment/report.json. Six missing groups still cause aggregate failure. No emulator process remains pending. This invariant sprite region does not complete moving serve/rally presentation, scoreboard/status transitions or P2/P3.

Next: identify native presentation generation at actual blanking commits and provide captured source refresh choices through a test-only entropy adapter for deterministic moving P1 cases. Complete native field/transition comparisons, P2/P3 and remaining behavioural/phase inventory. Goal remains active and incomplete.

## Current checkpoint (2026-09-30, verified P1 source windows and native title baseline)

The suite protects observable behaviour, not translated internals. The roadmap explicitly permits replacing memory layout, routines and translation machinery with concise maintained native Amiga code. Before retiring detailed diagnostics, establish equivalent behavioural comparisons from independent source evidence. No source hardware model or translation layer is required in the final executable. The complete-suite goal remains active; this checkpoint does not complete it.

Source P1 collection now retains 263 R1 and 312 R2 rasters, each captured twice with exact accepted parent callback hashes. Direct native pixel capture retains contemporaneous RAM/VRAM/register/PC observations. The verified source active area is (12,12)-(268,204). Named windows cover title/modes, both serve ends, returns, bounce/net/out, observed scores, six status messages, game/match/result/restart. There are 122 verified field observations (57 R1, 65 R2), with no missing first-captured field displays. Required named checkpoints match captured VDP state; unmatched neighbouring frames and generation associations remain explicit. This is scoped checkpoint evidence, not whole-match graphics or P3 timing proof. Private frozen fixtures are under tests/reference/presentation/ and remain ignored. Public recipes, validators and evidence are documented in analysis/source-presentation-regression.md and tests/README.md.

Correction to the preceding capture checkpoint: the nearly blank/partial title diagnosis came from the image preview. Byte-level RGB comparison and original-resolution inspection show complete identical title images at the examined frames, including frame 119 and frames 299-302. Claims of alternating source output, partial frame 119 or a MAME snapshot defect are withdrawn. No such source/render defect is demonstrated.

Added a stdio Copperline control adapter using the installed bridge. Native capture has a uniquely calibrated viewport (62,16)-(574,208), exact horizontal doubling and no vertical scaling. The P1 title case assembles the actual gameplay_integration_probe.s executable, uses the same initial bytes as the existing application, resumes past LoadSeg, and captures after an explicit physical beam wrap. Latest focused report confirms frame 552, vpos 0, and the registered first difference at stable-title pixel (74,12): expected 000000, actual cc55bb. The current application opens the court/serve instead of the original title; this is an explained product failure, not a capture error. No product fix was applied.

The aggregate baseline/self-test completed all 18 cases: 11 green, seven exact known red, no unexpected registered results. Mutation and failure-signature checks passed. The final focused title recheck after tightening beam-wrap/profile validation preserves its signature; the full aggregate was not unnecessarily repeated after that adapter-only refinement. Reports: build/tests/suite-report.json and build/tests/p1-title-report.json. Capture-integrity testing rejected a changed raw pixel file; the original bytes were restored. Missing coverage still causes aggregate failure: R2 same-rally return, meaningful F1-F5 gaps, remaining phase comparisons, remaining native P1, P2 audio, and P3 timing/input.

Next: extend actual native P1 comparisons to the retained gameplay, score/status and transition checkpoints, then complete the remaining behavioural and P2/P3 requirements. Keep continuous replays, known reds and source provenance intact. No emulator run is pending at this checkpoint.

## Current checkpoint (2026-09-30, source presentation capture foundation)

Added scripts/capture_presentation_reference.py and capture_presentation_policy.lua. Commands: python scripts/capture_presentation_reference.py and the same with --case two-player-match. Each executes the actual cartridge twice with the existing frozen physical input policy and callback recorder. Every raw callback recording must have the exact accepted parent capture hash; decoded RGB pixels, contemporaneous 1KB RAM, 16KB VRAM, eight VDP registers and PC must repeat identically. ROM/archive identity is checked. BF register observation tracks actual two-byte control commands and cancels the latch on status reads. No source CPU/game state is written.

Named windows include startup, stable-title candidate frame 300, selection input, initial serve, every distinct observed point-code pair, all existing game/match/restart milestones and the first marked lower/upper R2 contacts. Each retains neighbouring lossless rasters. Capture manifests identify completed and active callbacks rather than falsely asserting frame_done RAM is a post-tail snapshot. The raw 280x216 MAME border remains; the active crop and first visible update still need verification. Media are ignored under build/tests/{one-player-match,two-player-match}-presentation/{a,b}/; each directory's manifest.json lists exact frame and state/pixel hashes. This is source capture foundation, not accepted complete P1 coverage or a native comparison. P1's remaining serve stages, bounce/net/out/status windows, lag/crop/geometry rules and native adapter, P2/P3 and the other suite gaps remain open. The current suite classifications are unchanged (11 green, six known red; missing groups still fail).

Latest successful runs retained 88 R1 and 112 R2 rasters, each twice identical with exact parent callback hashes. Inspection found alternating full and nearly blank title rasters even at frames 299-302 with identical VDP registers. This is unresolved; do not promote these captures to accepted graphics expectations. Manifests are explicitly marked accepted_graphics_oracle=false. Next action: establish whether the alternation is the headless MAME snapshot/render path or actual source output, then verify crop/lag and complete P1 windows/native comparisons. No emulator process remains pending.

During development, Lua assert's multiple returns caused a register serialization error; fixed by assigning the asserted value first. A final-frame request exceeded the frozen policy stop; clipped to final callback end plus one. Both were capture tooling errors, not gameplay regressions. Inspect title media rather than assuming a frame number is a stable title: frame 100 is black startup and frame 119 is partially drawn.

## Current checkpoint (2026-09-30, later timer boundaries and audio cadence defect)

Added source-derived shared-timer-saturation-phase (R1 initial 2182, updates 2183-2184), status-timer-saturation-phase (initial 12534, updates 12535-12536) and status-timer-observation-phase. Shared timer's full-state native comparison passes through reaching and holding 255. The full status case is explained known red at initial-post-tail RAM offset 131: audio tick countdown expected 1 actual 2. Source initial C082/C083 are 2/2; the counter prefix decrements countdown to 1, and the source skips its conditional audio call. Both native run_tail and the live gameplay callback call audio_tick_adapter unconditionally; its final reload writes 2 back to C083. No production fix is applied.

The separate status observation runs the exact same native executable and retained source window, compares only the seven explicitly named counter offsets C06B-C071, and passes the status timer's 254-to-255 boundary. PSG/refresh comparisons remain active; its report accurately says seven RAM bytes. The full-state/audio failure remains registered and visible. Existing cases retain full 254-byte observations. Invalid/empty offset profiles are rejected. Timer checkpoint recipes are validated against the independently captured parent; a deliberately incorrect checkpoint was rejected.

Known-failure signature policy exposed a suite self-test bug: fixed actual=2 was unchanged for this new failure whose actual value already is 2. Changed-signature tests now derive a different value and run before emulator work. Direct policy checks for every known failure pass. The older loaded aggregate did terminate with the anticipated policy assertion, not a game regression. A corrected full aggregate then completed all 17 cases: 11 green, six exact known red, no unexpected registered results; mutation/signature checks passed. Full-replay reports are retained in build/tests/full-replay-checkpoint/. A subsequent optimized baseline aggregate also verified identical case classifications and signatures, with full references validated and known-red native replays ending at their recorded divergence boundaries. Latest report: build/tests/suite-report.json. Both aggregates still fail on explicit missing coverage. No process remains pending.

R1's matched prefix already protects both consumed refresh bits and five tick wraps; C06D/C06E/C06F/C071 first saturate before its first red. The new phases cover C06C/C070 later saturations. F5 evidence indexing can now name these windows, while meaningful movement/contact/court gaps, result transitions and P1-P3 references/native comparisons remain incomplete. This does not satisfy the full active goal.

## Current checkpoint (2026-09-30, natural deuce/advantage sequence protected)

The R2 inventory proves the entire F3 sequence was already played naturally: source updates 9134 deuce (5/5), 9588 advantage (4/6), 9869 deuce again, 10328 advantage again, 10782 game award (point codes 0/0 and game counts 1/2 to 2/2). Added five four-update source-derived boundary recipes plus deuce-sequence-phase, 1,649 consecutive updates initialized once before the first deuce boundary. The parent is the twice-identical R2; no score injection or expected intermediate writes are used. Tracked score/game checkpoints are enforced in phase_reference.py, and a deliberately wrong sequence was rejected.

Individual actual native comparisons all pass. The continuous 1,649-update replay matches entry/pre-tail/post-tail state and all 260 PSG bytes; the five boundary cases also match. Reference SHA256 35f16987caaea1278f7c77ddc30c8f97a3d2cb2a9e1ce0238233b5398abca9da; continuous executable SHA256 b8248d42ac93419ff63a0b971c85dd18e818151bb166b557ca002c3583c36f7b. These cases expose later scoring independently of the earlier full-match round failure. They do not prove upstream parity or native scoreboard graphics.

Fresh aggregate baseline/self-test run completed all 14 registered cases: nine green and five exact known red, no unexpected registered results; native mutation and changed-signature/unexpected-pass checks passed. Overall still fails on six explicit missing groups. Report: build/tests/suite-report.json. The goal is still incomplete: same-rally two-player return, remaining meaningful F1/F2/F4/F5 inventory/cases, remaining result-transition phases, and P1-P3 source/native adapters. F3's named sequence now has independent source and green native evidence; do not duplicate it as missing merely because the full replay has an earlier red.

Next useful clock work: R1's matched prefix already contains both refresh bits (updates 103,435,466 versus 772,800,803,805,1110), five tick wraps, and saturation of C06D/C06E/C06F/C071. Shared C06C first saturates at source update 2183 and status C070 at 12536; independent short reachable windows can protect these later timer boundaries. Keep remaining inventory/presentation requirements explicit.

## Current checkpoint (2026-09-30, two-player calibration and full R2 baseline)

Calibrated both physical MAME pads and two-player Func selection. python scripts/capture_input_map.py captures twice identically, verifies individual normalized input-reader values and simultaneous independent movement, and retains 562 exact callbacks/14 observations with ROM/emulator/script provenance in private tests/reference/input-map.json. Public findings: analysis/two-player-input-map.md. Initial mode 80h maps pad 1 to lower and pad 2 to upper; source normalize_input_for_player_side exchanges nibble ownership when mode bit 4 changes. Some directional holds are phase/bounds blocked, not successful movement coverage.

Frozen the source-discovered varied match schedule in tests/cases/two-player-match.json and scripts/capture_two_player_match.lua. python scripts/capture_test_reference.py --case two-player-match records twice byte-identically through 4-6 match award, result, two-player reselection and first advancing restarted serve: 27,037 updates (24,542 gameplay/2,495 tail-only), 5,414 PSG bytes, zero refresh reads, 1,203 between-callback RAM writes. Raw SHA256 e15dbcf10c5545ab74e0a7ca7ad61cc82b7c19686aedd64cd188cb31b23212ce; fixture SHA256 72c7aad2ef3bf58f02cbabb3aa718175ce31ff9ce2a1fc9a8092ea59deca25f9. Source-only accepted-contact markers at 0C9F/0FD3 prove 11 lower and 23 upper returns. Match award update 25619/frame 26918; restarted flight 27037/frame 28336. Both sides win games; deuce and one advantage pair are observed. Required same-rally return by both players remains missing: all 34 contacts occur in separate point intervals.

The harness input offset now uses 32-bit addressing and accepts up to 65,535 updates; native long-run watchdog is 360 seconds. No gameplay/product fix is made. Native R2 executes all 27,037 updates, agrees through 2,535 updates/350 PSG bytes, then differs at callback-entry 2536/frame 3834, deferred display setup request expected 129 actual 1, tail-only: the known round transition. Executable SHA256 f18d08a54ae08707994571aadbda9a84a7edf1d5af91cc1087bb9029a9529c32. Its signature is registered. The widened harness still passes serve and mutation detection.

Added scripts/inventory_match_references.py: retained source indexes for point-code transitions, instrumented contacts/rallies, counter wraps, timer saturation and refresh bits in build/tests/match-inventory.json. R1 observes 52 tick wraps and both refresh bits; R2 observes 105 wraps. R1 lacks new contact markers, so its return count is unknown in this inventory rather than inferred as zero coverage. These observations do not yet constitute the full F1-F5 coverage manifest or all native phase checks.

Fresh python scripts/run_test_suite.py --baseline-check --self-test completed all eight registered native cases: three green, five exact known red, no unexpected registered results; mutation and changed-signature tests passed. Overall remains failing on six explicit missing requirement groups, with R2 now described precisely as a same-rally gap rather than missing full match. Report build/tests/suite-report.json. Additional regular-return discovery (both actions pulsed for serves, released for returns) completed a match/restart by frame 23776 but still produced no same-point two-player rally: 20 upper and nine lower contacts, maximum one contact per point. It remains rejected discovery data for the missing rally requirement. A prior predictive-movement discovery did not establish a same-rally return; a per-end serve-action probe stalled due swapped control ownership and is rejected. Source reading shows contact is automatic when geometry permits, while held actions select an alternate trajectory. The current probe pulses both actions only while waiting for serve, releasing them during play. Its outcomes are not accepted reference data yet.

Next: inspect the current discovery, freeze only proven new rally behaviour or obtain a reachable focused rally case; complete meaningful gap/phase inventory and P1-P3 source/native adapters. Goal remains active and incomplete. Prior R2-missing status is superseded by this checkpoint.

## Current checkpoint (2026-09-30, resumed-launch failure explained)

Located the resumed-play launch discrepancy in triangular_root_step. Source debugger observations at callback 1565 and temporary native register tracing agree through the multiplication result 1040h. The source triangular root returns 64, whereas translated code returns 65. Generated SBC HL,BC assembles BC/HL using MAKE_BC_NO_AR and MAKE_HL_NO_AR before SUBX; these shifts change the 68000 X carry input instead of preserving the source borrow. The first source subtraction should include the SCF borrow; the translated setup loses it, allowing one extra triangular-root iteration at this exact boundary. Source/native traces are private build/tests/math-source.tsv and math-native-diagnostic.log.

Added reproducible python scripts/diagnose_phase_launch.py: execute the unmodified actual native phase and require the known update-96 signature, then temporarily preserve CCR around both register-pair preparations in this helper. The corrected native executable matches all 200 phase updates, including entry/pre-tail/post-tail RAM, ordered PSG and refresh events. Finally restore the original generated source. Command passed, with build/tests/root-carry-diagnostic-report.json recording both outcomes and restoration. No generator/product fix is applied and the known-red baseline remains unchanged. Known-failure reason/evidence is updated from unresolved arithmetic discrepancy to this confirmed carry-loss mechanism.

Next goal work remains R2 control calibration/full continuous capture, meaningful gap inventory/cases, remaining result-transition phases and P1-P3 source/native adapters. This investigation explains a known failure; it does not complete missing coverage or the active suite goal. Older pending root-cause notes below are superseded.

## Current checkpoint (2026-09-30, independent later-phase diagnostics)

Added scripts/phase_reference.py and four tracked case recipes. Fixtures are exact slices of the independently twice-captured full R1, initialized from a retained reachable source callback's pre-tail state; native initialization executes its tail, then carries its own state across later updates. Every run reconstructs the expected slice from the validated parent and checks exact equality/provenance. A deliberately changed snapshot was rejected. No source main-thread writes are injected into port state, and the continuous replay remains registered.

Individual native results: restart-play-phase passes all 18 updates/five PSG bytes; match-tail-phase passes the selected 40 updates/113 PSG bytes, which does not prove dispatch correctness because extra gameplay currently leaves the compared state unchanged in that interval. round-tail-phase is known red at local update 1/source 1334/frame 2632, pre-tail input direction B expected 1 actual 0 (gameplay executed during a source tail-only callback). resumed-play-phase matches 95 updates then differs at local update 96/source 1565/frame 2864, pre-tail launch trajectory expected 199 actual 200. Entry RAM matches exactly; no refresh read occurs at that update. Six launch/vector bytes differ, so this is a newly exposed calculation discrepancy, not carried upstream round-reset drift. Root cause still needs investigation; no fix or full behaviour equivalence is claimed.

Both red signatures are registered; all four cases are included by scripts/run_test_suite.py. Aggregate baseline/self-test validation completed: three green cases (serve, match-tail, restart-play), four known red with matching signatures, no unexpected registered-case results; mutation and changed-signature checks succeeded. Overall remains failing on the six explicit missing requirement groups. Report: build/tests/suite-report.json. Remaining goal scope includes R2 calibration/full replay, gap inventory/cases, longer/result-transition phases, P1-P3 references/native adapters and explanation of the exposed launch discrepancy. The native-endpoint/testing decision below remains in force.

## Current decision (2026-09-30, native endpoint and lasting tests)

User confirmed that the suite should enable iterative replacement of the translated starting point with concise, targeted native Amiga code, with no remaining implementation debt from the original architecture. Roadmap and tests/reference-spec.md now distinguish temporary byte-level RAM/register/callback/PSG diagnostics from lasting behavioural tests. Internal layouts and routine structure may change; direct native hardware paths remain the product endpoint.

Subsystem migration must establish independent-reference-backed behavioural comparisons alongside existing diagnostics before retiring them, retain continuous/focused cases and known-failure visibility, and document state/input/entropy/output mappings and exclusions. The test-only adapter reads actual native results; it must not reconstruct expected gameplay or inject expected intermediate writes. Retire obsolete translation macros, virtual machine state, generator dependencies and duplicate implementations once replacements are verified. Final cleanup requires a standalone maintained native build, preserved behavioural coverage and target hardware/performance checks; test success alone does not prove optimal code.

This is a documentation/architecture decision, not additional runtime coverage or a change to the active complete-suite goal. Next suite work: calibrated R2 capture, meaningful gap inventory, phase-specific comparisons and P1-P3 references/native adapters. The registered runner and exact known-failure checks already exist; the earlier checkpoint's instruction to register them is superseded.

## Current checkpoint (2026-09-30, full R1 match reference)

R1 now has a twice-identical independent MAME source capture through match award, result/title reset, one-player reselection and first advancing restarted serve. Frozen controls are in tests/cases/one-player-match.json and scripts/capture_one_player_match.lua; discovery uses source observations only and writes no source RAM. Reproduce with python scripts/capture_test_reference.py --case one-player-match. The accepted private fixture has 13,378 updates: 11,427 gameplay and 1,951 tail-only callbacks, 3,344 PSG bytes, 50 consumed refresh values and 1,002 between-callback RAM writes. Match award is update 11960/frame 13259; restarted flight is update 13378/frame 14677. All 1,566 prefix updates agree exactly with the existing frozen prefix, including inputs, refresh reads, sound and between-callback events. The capture command now enforces this agreement and the frozen physical controls before replacing the fixture.

The parser permits callback-counter clearing only at the documented source title-reset loop (PC 01E9, main-thread actor, zero write); unexplained counter writes remain errors. Milestone states and source times are validated. Recorder termination now ignores later frame callbacks after closing its output, fixing the discovery recorder's repeated closed-file errors. No erroneous discovery output is used as the accepted oracle.

python scripts/run_regression_tests.py --case one-player-match executes all 13,378 actual 68000 updates and returns a behaviour difference at callback-entry 1333/frame 2631: deferred display setup request (RAM offset 2), expected 129, actual 1; kind tail-only. It matches 1,332 updates and 250 PSG bytes before that known implementation boundary. Executable SHA256 c31a3a5b3cf091f145a679968ee1c747180553606f0d8a4abe0ca183828b6210. Full report: build/tests/one-player-match-report.json. The unchanged serve suite plus mutation self-test passes, detecting ball court X 212 versus 213 at update 1.

Added tests/known-failures.json and scripts/run_test_suite.py: the aggregate runner executes registered actual native cases, verifies exact known-red signatures, rejects unexpected passes and changed signatures, and keeps missing R2/gap/phase/presentation requirements as explicit exit-2 failures even in baseline-check mode. Self-test combines the existing native mutation with classification rejection checks. python scripts/run_test_suite.py --baseline-check --self-test completed: serve green, round-transition and one-player-match known red with matching signatures; native mutation and changed-signature/unexpected-pass rejection checks succeeded. Overall suite remains failing because six required coverage groups are explicitly missing. build/tests/suite-report.json preserves these results.

Active full-suite goal remains incomplete. Next: register exact known-failure signatures and an all-case runner with explicit missing coverage; calibrate/capture complementary R2; inventory R1/R2 observations and fill meaningful F1-F5 gaps; add phase-specific comparisons and P1-P3 source/media/native adapters. Full R1 source continuity is established, not later native behaviour or presentation correctness. Earlier next-action sections below are historical where superseded by this checkpoint.

## Current next-goal decision (2026-09-30, suite before port cleanup)

Roadmap now defines a goal-ready reference-backed red/green suite before broad Amiga port cleanup or maintained-source conversion. Complete R1/R2 and meaningful gap references plus presentation evidence; register and run all required cases in one command; use source-derived phase starts to diagnose later regimes independently of earlier continuous-replay failures. Separate green, specifically known red, unexpected red and missing coverage. Known failures retain exact first-divergence signatures; missing fixtures/adapters/entry points are not expected failures or passes.

Planned tests/known-failures.json and an explicitly named baseline-check mode must verify green cases and known-red signatures while keeping red visible. Strict mode remains failing until all required checks pass; baseline mode fails on missing cases, unexpected differences or unexpected passes pending review. The suite goal completes only with all required source data and runnable comparisons, zero missing/unexpected results, actual reports and mutation/signature-change detection. The next implementation goal then establishes maintained 68000 source with identical baseline results and resolves red cases while preserving green ones. Existing source/port proof below is unchanged. This update prepares the goal; it does not start capture, implementation or a new active goal.

## Current reference completion plan (2026-09-30)

Expanded tests/reference-spec.md into an executable work backlog: artifact destinations per case, the existing R1 input sequence and result/restart discovery task, a calibrated two-player R2 input recipe with explicit durations/outcome guards, five focused gap-case families, named graphics/audio/timing capture checkpoints, comparison criteria and separate source-data/port completion checklists. Future case filenames are explicitly proposed, not implemented commands. Exact control mappings and restart actions are bounded source discovery tasks; no unverified physical input bits or tennis outcomes are asserted. Continuous captures use frozen input schedules and finite diagnostic watchdogs, not injected gameplay state.

Next source work: generalize the exact callback capture to full match/result regimes, establish R1 restart inputs, and collect the complete R1 while preserving the accepted prefix. Then calibrate/capture R2, fill only meaningful gaps and collect presentation references. Existing source-record and port evidence below is unchanged; this documentation pass adds no runtime coverage.

## Latest checkpoint (2026-09-30, exact first-round source record)

The independent source record is ready for the regression runner: tests/reference/round-transition.json (ignored/private). Run python scripts/capture_test_reference.py --case round-transition to capture twice, or add --verify-only to validate the saved record. The fixture contains 1,566 consecutive updates after the initial callback: 1,430 gameplay and 136 tail-only callbacks, 285 ordered PSG bytes, eight actual consumed refresh-register decisions, and 50 between-callback RAM writes. Exact callback entry, common-tail entry and return snapshots preserve the main-thread actions and both callbacks in source frame 2631. Initial PRNG state and actual input-reader returns are supplied; no Python gameplay model produces the expected state.

Milestones: first game award update 1204/frame 2503, first tail-only callback 1333/frame 2631, gameplay restored 1469/frame 2768, first advancing resumed serve flight 1566/frame 2865. Two raw captures are byte-identical (SHA-256 88c2b67c299bf991b26797831bd6eb8732466976639c7fe337d997e7ca3d44ac). All 1,567 retained pre-tail states, including the initial callback, also match the older non-debugger source capture exactly. A debugger numeric-literal/register-name ambiguity in an earlier trial was corrected with explicit 0x prefixes before freezing the final record. The fixture SHA-256 is 4cfc422e23b5e2c6781056cc249cfae24eacf8a2e378f08eb082203a0aa45ac7.

Run python scripts/run_regression_tests.py --case round-transition --reference-only to validate and prepare initial state, input, entropy and harness configuration without executing the port. The validator reconstructs source continuity from between-callback writes, rejects missing effects, checks dispatch kind and tail counters, and retains ordered source event evidence. Deleting the captured display-setup write was rejected at callback 1333. Those source writes are never injected into native RAM to manufacture parity. The extended actual 68000 replay carries its own state; python scripts/run_regression_tests.py --case round-transition matches all 1,332 preceding updates and 250 PSG bytes, then returns exit 1 at callback-entry 1333: deferred display setup request expected 129, actual 1. This is the known unimplemented native main-thread round setup and tail-only routing, not a newly introduced regression. Full report includes preceding source actions in build/tests/round-transition-report.json. The default serve suite and its deliberate mutation self-test still pass; the temporary mutation is removed.

Goal achieved: a repeatable, runner-consumable continuous source record through the first game, pause and resumed serve. Full R1 match/restart, R2 two-player reference and presentation snapshots remain open. Next port work is the maintained-source/native round transition against this frozen oracle; next reference extension is complete match/restart. Roadmap, tests/README.md and tests/reference-spec.md reflect the separate capture and port statuses. No full-match or hardware phase gate is claimed.

## Current reference-test specification (2026-09-30)

Added tests/reference-spec.md: two complementary continuous match replays (one-player AI and varied two-player play), with short focused cases only for important behaviours neither replay observes. It specifies accrued state across serves/points/games, meaningful behaviour inventory, exact callback and main-thread transition boundaries, input/random fixtures, twice-identical source captures, first-divergence reporting and separate hardware acceptance. Existing 200-callback S1 is captured/passing; R1 has partial source and sampled port evidence; complete R1 and R2 remain required. No additional runtime coverage is claimed by this documentation change.

Next reference work: extend R1 through tail-only round transition and resumed serve with exact ordering and refresh-sign inputs, then match completion/restart. Capture complementary R2, assess actual observed coverage, and add focused cases for remaining meaningful gaps. The maintained-source migration and current port implementation boundary remain as recorded below. Roadmap and test instructions link the specification.

## Latest checkpoint (2026-09-30, continuous serve regression suite)

One command now runs the deterministic serve regression: python scripts/run_regression_tests.py. The Copperline harness executes the same generated 68000 gameplay routines and native audio interpreter included by the live game, initializes RAM once, and carries it across 200 callbacks. It compares 254 RAM bytes at both post-gameplay and post-tail boundaries (101,600 update-state byte comparisons), the initial tail state, and 40 ordered PSG events against an independent MAME oracle. Callback-pointer bytes C000-C001 are excluded. Reference capture runs MAME twice and requires identical state/event output; ordinary tests neither run MAME nor derive expected state from Python. Reference RAM remains ignored in tests/reference/serve.json. See tests/README.md for commands, prerequisite tools, checkpoint definitions and limits.

Verified: python scripts/capture_test_reference.py produced two identical captures; python scripts/run_regression_tests.py --self-test passed and detected a temporary one-pixel ball court X mutation at update 1 (expected 212, actual 213). A separate negative run returned exit 1 and the same named difference; the harness was restored. Temporary mutated source/executable are removed. The older run_translated_player_frame_probe.py still passes all 244 retained/controlled cases after shared source generation and test-I/O extraction. The regression executable SHA-256 is 1a3086e8af33b75be453eac4465bba9875bb7c71ce70f8a3b594e89825b214b4; frozen fixture SHA-256 is 04cab326368feb72bbfe0d45fbf122c02b60d2a1f5c6124baffa47e1d516c330. Full results and negative-run evidence are local under build/tests/.

This completes the first regression foundation, not the maintained-source migration or full-game equivalence. The fixture covers serve, launch, flight, return and a point, with fixed native refresh-sign input zero matching this captured path. It excludes actual joystick sampling, native rendering, Paula playback and real-time scheduling. Next establish the editable 68000 product source with this regression guarding changes, and extend cases to first-game award, between-game routing/pause and resumed serve. Existing live display/audio/cadence checks remain separate; no roadmap phase gate is advanced.

## Current decision and next action (2026-09-30, maintained source regression suite)

Agreed direction: keep reproducible translation as the reference baseline, then iterate on editable maintained 68000 port source. Native scheduling and direct Amiga hardware changes belong in that source. Preserve game rules, arithmetic widths, callback ordering and source cadence. Review the public-source policy before checking in ROM-derived translated source; private ROMs and extracted assets remain excluded.

The roadmap records the planned files: tests/README.md, tests/cases/*.json, tests/reference/, tests/state-fields.json, amiga/tests/simulation_harness.s, scripts/run_regression_tests.py and scripts/capture_test_reference.py. Generated results go under ignored build/tests/. MAME explicitly captures reference cases; ordinary regression runs use saved fixtures and Copperline to execute actual assembled game routines without real-time presentation waits. Compare named simulation fields and ordered sound events per source callback, control random inputs, and report the first difference with a failing exit status. Routine and gameplay cases share the harness. Normal-executable input, display, Paula DMA and real-time cadence checks remain separate.

Next action: reuse existing build/capture/replay helpers to package the established serve and first-game award as initial regression cases. Extend across gameplay versus tail-only dispatch, the between-game transition and resumed serve as that boundary is implemented. This documentation update implements no test files or harness. Existing sampled matches do not establish every-callback or full-game correctness. The measured checkpoint below remains the current executable evidence.

## Latest checkpoint (2026-09-30, independent simulation and blanking commit)

The live loop now samples player input and runs each due source update from CIA-B timer B at approximately 59.922738 Hz, independent of PAL frame presentation. Sound events still reach Paula in their simulation update. Sprite DMA data and palette/score Copper commands are prepared in inactive banks; the vertical-blank commit writes only COP1LC, then prepares the other bank outside blanking. See analysis/native-gameplay-integration.md and analysis/long-game-replay.md. The PAL-frame number at a given source update can vary by about a tick between launches because the clocks are independent; source-update state is checked against the corresponding source checkpoint.

Run python scripts/run_amiga_live_serve_probe.py and python scripts/run_amiga_long_game_probe.py --ordinary. Both passed on the unexpanded PAL A500 Copperline profile. The long replay has 34 matching state/score checkpoints, four matching score transitions, 250 ordered PSG bytes, a visible B game tally, and zero Copper-list commits finishing on visible lines; the ordinary run also awards B a game and measured zero late commits. Earlier trials with a CIA-A timer, a beam-wrap clock, and too much work inside blanking failed cadence or display checks and were replaced. Correction to the next boundary: $06B1 is the already translated counter/audio interrupt tail. At source frame 2631 the main-thread round path installs it alone, suppressing gameplay updates; after a timed wait and round setup it restores $0699 at frame 2768. Next: add callback routing plus the main-thread between-game state transition, then measure display and sound through a complete match and verify on WinUAE.

The entries below record earlier checkpoints and may describe superseded implementation states.

## Latest checkpoint (2026-09-30, long game replay)

Run python scripts/run_amiga_long_game_probe.py --ordinary. The source capture spans 2202 callbacks and B point awards at updates 134, 469, 807, then a game award at 1204. The native replay uses private source Z80-refresh sign choices and matches 34 sampled state/score/scoreboard checkpoints through update 1318 with no mismatches, including 250 ordered PSG bytes across 155 event updates. A screenshot confirms the awarded game tally. The ordinary executable, without the source refresh fixture, also awards B a game. See analysis/long-game-replay.md and ignored build/amiga/long-game/report.json, GIF, WAV and PNGs.

Timing remains open: 113 replay source updates through 1318 and 103 ordinary updates through the last sampled update 1617 completed during visible scanlines. A once-per-PAL-frame presentation commit made the count worse and was reverted. The source switches callback $0699 to $06B1 after the game at frame 2631; the live executable still lacks that between-game transition. Next: translate the $06B1 callback, then buffer/schedule presentation so visible-line work is eliminated, and remeasure audio continuity.

The entries below record earlier checkpoints and may describe superseded implementation states.

## Latest checkpoint (2026-09-30, Paula tones)

The live game now sends the three ordered source PSG tone/volume streams to native Paula DMA channels through a looping four-sample square wave and per-channel period/volume registers. Run python scripts/run_amiga_live_serve_probe.py on the exact PAL A500 profile. It captures build/amiga/gameplay-integration/serve-audio.wav and verifies that source serve note PSG period $0D5 (525.17 Hz) is present strongly in the native WAV. The same run preserves sampled gameplay, score selection, and 59/119 update cadence. Native executable: 213188 bytes, SHA-256 24d1d6fa499b4aa55a5dc47e004336fc6d55577f672c3b8aa2ab3c916f650e30. See analysis/paula-tone-output.md for hardware mapping, proof and limitations. Next: longer rallies and scoring/game transitions, then sustained frame/audio continuity and full-match measurements.

The entries below record earlier checkpoints and may describe superseded implementation states.

## Latest checkpoint (2026-09-30)

The native live game now selects all six scoreboard graphics fields through prepared Amiga bitplane banks and Copper pointer patches. The display selection follows the source scoreboard draw events: point/game/mode updates consume the pending redraw flag, status text appears on its pending event, and expiry restores blank text despite retained low status bits. Shadow VDP writes remain verification data, not display input. The scripted serve changes B point from 0 to 1 at the source draw boundary; captured screenshots show only that score cell changed among the six fields after the status message has expired. PAL/source cadence and sprite state still match sampled source checkpoints. Run python scripts/run_amiga_live_serve_probe.py and python scripts/run_amiga_score_copper_probe.py; details and limits are in nalysis/native-gameplay-integration.md. The live executable is 212404 bytes, SHA-256 49332452784e71c2283f4914d40e29103cac1027a5382baef0e6245e2250f643. Next: native Paula audio from ordered PSG events, then longer rallies and score/game coverage.

The entries below record earlier checkpoints and may describe a superseded implementation state.

# Champion Tennis Amiga port worklog

Current status and next action, 2026-09-29. The full investigation history is preserved in [the pre-cleanup worklog](analysis/history/WORKLOG-pre-port-cleanup-2026-09-29.md); its older progress figures and next-action notes are historical.

## Current result

The source of record is the generated, annotated Z80 assembly at `build/analysis/champion-tennis-classified.asm`. `python scripts/roundtrip_rom.py` regenerates it from the locally configured 8 KB G-1009 cartridge and the tracked block, symbol, literal-operand, and comment inputs in `analysis/`. The listing covers every byte, has 393 operationally named address labels and 147 address-keyed comments, and rebuilds the original 8,192 bytes exactly (SHA-256 `19bb6647f14ef50f976e8d0a06d389f06b2e700d54a54fb1734d3140f9745ad1`). The partition is 5,765 instruction bytes and 2,427 byte-emitted bytes; 14 emitted bytes have no proved reader. Byte equality proves preservation, not complete gameplay interpretation. The assembly, ROM and rebuilt image stay ignored; the annotation inputs are the reviewable source.

[Whole-ROM review](analysis/static-rom-review.md), [annotation audit](analysis/annotation-audit.md), [frame-update contract](analysis/frame-update-contract.md), [ball translation notes](analysis/ball-math-translation.md), and [sprite-rendering assessment](analysis/sprite-rendering.md) state the current evidence and uncertainty. The Python source model checks instruction-level behaviour but is not the port or the authoritative disassembly. `python scripts/check_source_ball_update.py` passes. No emulator was run during the final static annotation and comment passes.

Earlier Gearsystem and MAME captures established deterministic samples, title/keyboard mode selection, movement, one returned ball and a scored point. The new [source timing baseline](analysis/source-timing-baseline.md) measures 60 gameplay updates in 60 consecutive MAME SC-3000 video intervals at 59.922738 Hz, with controller reads, normalized input, movement, and post-gameplay RAM snapshots. A 20-interval left hold alternates two- and one-pixel moves, taking lower X from `$C0` to `$A2`; two complete captures are byte-identical. This is a bounded active-play result, not a claim about all modes or SG-1000/Gearsystem timing. `python scripts/smoke_amiga_run.py` now copies the working vasm 2.0e binary from sibling `amiga-reversing2` into ignored `.tools/vasm/`, assembles a 64-byte Kickstart 1.x hunk executable, and launches it with Copperline `--run --exit-on-return`. It returned zero on the exact unexpanded PAL A500/Kickstart 1.3 profile; executable SHA-256 `2679fb883a0b4dc9b040f6fe0a6cdf2ee1d8e6aeeb75f7a5412c9a93ce538e2a`. This proves the direct native build/launch loop, but only for a return-code smoke program. The return-code smoke test alone does not establish gameplay, while the bounded sprite probe below now proves one input/movement replay. The Phase 1 infrastructure gate has not passed.

The [sprite hardware-fit test](analysis/sprite-rendering.md) checks 111 retained source RAM snapshots and a controlled MAME gameplay VRAM frame. It finds at most eight visible sprite records, at most three overlapping 16-line spans, and at most two colours within each proposed Amiga sprite-channel pair. The controlled frame's VDP attribute bytes equal the RAM buffer, and pattern zero is the two-by-two ball shadow mark. A native Copperline prototype now displays the converted court and all eight sprite channels on the exact target profile; `python scripts/run_amiga_sprite_probe.py` produces a 10-second, 250-frame GIF at `build/amiga/sprite-probe/gameplay-sprites.gif` with source-driven lower-player motion. Its first 40 updates match all 40 MAME checkpoint tuples for normalized input, lower X, source tick, hold count, update ordinal, attached-ball Y/X and serve step. The first release ends at `$A2`; 50 and 100 PAL frames contain 59 and 119 simulation updates respectively. `python scripts/check_translated_timing_replay.py` also matches all 256 source RAM bytes over those 40 intervals with the Python full-update translation. That path stays in lower `serve_wait`, upper `ai_wait` and ball-dispatch `idle`. A separate controlled source serve capture now has 201 byte-identical checkpoints across two runs; the Python full-update translation matches all 256 RAM bytes for the 200 following updates, including serve, flight, return and point. Native gameplay beyond the serve-wait slice and exact visual parity remain open. The sibling `amiga-reversing2` repository provides `knowledge/amiga_hw_reference.md`, `knowledge/amiga_hw_registers.json`, and `ext/amiga_includes/ndk_2.0/include/hardware/custom.i` for later hardware work.

## Next action

The joined native replay now covers generated gameplay and the complete interrupt tail for 240 retained and four controlled cases: 62,464 post-tail RAM bytes, 40 ordered PSG bytes, 43 scoreboard VRAM writes, and 16 deferred VDP bytes match the source model (`python scripts/run_translated_player_frame_probe.py`; executable SHA-256 `bbb19074a64d3bdcbbab8fdbc4b16c86755e8bb0851a2bea5eea18783d664477`). The audio tick is a separate source-semantic 68000 routine because generated audio still has unresolved indirect dispatch, stack, flag and port instructions. The explicit Z80 refresh-register fixture is zero, and uncaptured sound commands remain unproved.

The [live integration probe](analysis/native-gameplay-integration.md) boots from retained in-progress source RAM, samples Amiga joystick/fire, runs the joined native update at source cadence, and renders the previous source sprite buffer through a dynamic eight-channel bridge. It packs active records in source priority order, selects their patterns from a converted 64-pattern atlas, and patches pair colours. On the exact PAL A500 profile it reaches 59 and 119 updates by PAL frames 50 and 100; a scripted left hold moves lower X and sprite-buffer X from C0 to A3 hexadecimal. Running scripts/run_amiga_gameplay_integration_probe.py produced a 10-second GIF and screenshot under ignored build/amiga/gameplay-integration/ (137576-byte executable SHA-256 c20f91da0b29c2af6136ae896eae80391c252df0e7a5381a3d2f4b0014802cd2). Native logs report no sprite bridge fit errors and ball slot 4 in this captured wait-state. Running scripts/check_sprite_hardware_fit.py passes 312 snapshots, including a serve sequence with ball slot 0, with at most eight active records and two colours per Amiga channel pair; it verifies converted rows for every observed pattern. The court remains static, scoreboard writes only update shadow VRAM, PSG bytes are not played, and there is no title boot or ADF.  The live serve runner scripts/run_amiga_live_serve_probe.py now captures port-2 fire and verifies native checkpoints at updates 59, 119 and 179 against source frames 1358, 1418 and 1478. Lower-player X, sprite-buffer X, ball Y/X, both player phases and ball slots match; the ball moves from slot 4 to slot 0 and the native bridge reports no errors. The serve screenshot and GIF are under ignored build/amiga/gameplay-integration/; the 137740-byte executable has SHA-256 9b7eef04a37467659fb7db781d200b7ac64c970915c24c139fff18214ad54576. This is sampled state parity, not pixel parity. Next integrate native Copper score selection, then map PSG output to Paula and test later rallies and scoring. The [native Copper scoreboard probe](analysis/score-copper-probe.md) now prepares all 38 variants for both point fields, both game tallies, centre status and mode text. One 100940-byte PAL A500 executable switches all six fields from a baseline to alternate values through 224 patched Copper pointer pairs. Copperline confirms the original capture matches in every field, the alternate changes every field, and no pixels change outside those six regions. A source-colour check passes every prepared variant. This remains an isolated display prototype: the live game has not yet selected banks from game score/status state. The ordinary sprite and live gameplay probes still pass; WinUAE visual confirmation remains open.

The [original-cartridge ball/shadow comparison](analysis/ball-shadow-comparison.md) confirms the conspicuous gap in the pre-serve bob: source frame 1320 has ball/shadow Y 145/180 at the same X, visible as a 36-pixel gap in its MAME screenshot. The Amiga capture shows about 70 output pixels at 2x scale. During actual serve flight, the original ball and shadow reach matching Y at frames 1361-1362 and 1411. No positional correction is indicated by these samples.

## Repository boundary

Keep `analysis/` annotations, `scripts/` reproduction and translation tools, and `tooling/` MSVC compatibility shims. The preliminary [ROM evidence map](analysis/rom-map.md) and archived worklog retain historical captures and older figures; use the current reviews above for present classifications. `build/` contains generated listings, reports, and retained local emulator output. `.tools/`, `config.local.ini`, the cartridge and Amiga ROM are private local inputs and must stay ignored. Autogenerated MAME `cfg/` and `snap/` output formerly at the repository root is retained under ignored `build/local/`. Do not commit private ROMs or unmodified extracted assets.

Cleanup kept the historical trace/check scripts because they reproduce evidence cited in the archive. This repository has no commits yet; before an initial commit, review the Python analogue's embedded ROM table constants against the public-source policy. The private cartridge, ROMs, generated assembly and emulator outputs are already excluded by `.gitignore`.

The preliminary Ghidra import/export path, label-audit prototype, and block-suggestion script are retired. Their generated project, candidate map, intermediate listings and stale run snapshots were removed; the current `rom-blocks.def` and annotated round-trip do not depend on them. The initial [ROM map](analysis/rom-map.md) retains the historical findings and marks its retired commands. Generated Gearsystem captures were reduced to the samples read by the evidence checkers and two representative sound runs, saving about 107 MB. Current source checks, title/VDP/sound capture checks, and MAME movement/score/ball checks passed after cleanup. The retained raw captures are local evidence, not commit candidates.

## Recheck

- `python scripts/roundtrip_rom.py` — exact cartridge rebuild and label/comment input validation.
- `python scripts/check_source_ball_update.py` — static translated-source checks.
- `python scripts/source_timing_baseline.py` — repeat the MAME SC-3000 active-play timing and input capture; `--verify-only` checks local captures.
- `python scripts/smoke_amiga_run.py` — copy the adjacent vasm binary locally, build the minimal hunk executable, and verify Copperline direct run on the target profile.
- `python scripts/check_sprite_hardware_fit.py` — check source snapshot channel, overlap and paired-palette bounds against controlled gameplay VRAM.
- `python scripts/run_amiga_sprite_probe.py` — regenerate private Amiga-ready assets, build the native display prototype, and capture its screenshot and 10-second GIF in Copperline.
- `git status --short` — review only intended source and documentation before a first commit.
