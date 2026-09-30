# Champion Tennis (SG-1000/SC-3000) → Amiga 500: agent roadmap

This document defines the target and phase gates. [WORKLOG.md](WORKLOG.md) is the authoritative current status, evidence, decision record, and next action. Update it whenever a gate changes or an experiment changes an assumption.

Current phase boundary (2026-09-30): translated gameplay and native Amiga input, Copper/bitplane/sprite display, and Paula tone output run through one game award. Simulation is now paced independently of PAL presentation; the inactive Copper-list address is switched in blanking, with zero visible-line commits measured in the long replay and ordinary run. After a game, the source temporarily selects the existing counter/audio interrupt tail alone while its main-thread round transition runs; this callback routing and round transition, complete-match presentation/audio checks, and independent hardware verification remain open. See [the current worklog](WORKLOG.md) and [long-game replay evidence](analysis/long-game-replay.md) for measured results and the next action. No Phase 4 or Phase 5 gate is claimed.

Full R1 source capture is now reproducible through match result and restarted serve: 13,378 updates, twice-identical, with the existing 1,566-update prefix preserved exactly. Its actual 68000 comparison completes and first diverges at the known callback 1333 round-transition boundary. R2, focused gap/phase cases, presentation references/adapters, and the all-case known-failure runner remain required before the suite goal is complete. See the latest worklog checkpoint for commands and evidence.

Four source-derived phase diagnostics now supplement R1: restarted serve and a short match-tail interval pass; round-tail input handling and resumed launch calculation have independently observed known-red signatures. Phase fixtures retain exact parent provenance and are checked against the twice-captured source record. These isolate later behaviour without claiming upstream parity; longer/result-transition phases, R2 and presentation coverage remain open. See the latest worklog checkpoint.

The resumed-launch known failure is now explained by carry loss in the translated triangular-root helper. A temporary native correction matches all 200 retained phase updates and restores the baseline source; no product fix or additional coverage completion is claimed. The worklog records the reproducible diagnostic.

Two-player calibration and a twice-identical varied 27,037-update full match/result/restart reference are now retained. Native R2 matches 2,535 updates before the known round-transition failure. Source markers establish returns by both players, but not in the same rally: that R2 requirement remains explicitly missing. An indexed match inventory records observed scoring, clock and refresh evidence. See the current worklog for captures and remaining gaps.

The required deuce/advantage/back-to-deuce/game-award sequence now has a green continuous 1,649-update native phase replay (260 PSG bytes) and five green scoring-boundary cases, derived from natural R2 play. Source scoring checkpoints are enforced. This adds independent later scoring coverage without changing the full-match known failure or claiming hardware presentation parity.

Later shared/status timer boundaries now have explicit source-derived cases. Shared timer full state and the scoped seven-counter status observation pass; the full status case records an explained audio-cadence failure (unconditional native audio service versus the source two-callback countdown). Both comparisons remain registered, so focused clock evidence does not conceal the audio defect or claim whole-state parity. See the current worklog for exact signatures and aggregate verification.

Source presentation now retains 575 twice-identical rasters across both frozen full-match replays and 122 verified field observations. Named P1 windows and exact source/native viewport rules are recorded. The actual native executable has a registered title comparison: known red because title/menu presentation is not implemented. A callback-aligned upper-player placement case also exposes a 20-pixel sprite-origin error with matching simulation state. Generation-aligned moving-scene and field-sequence cases now cover an uninterrupted prefix through the first game tally: seven whole-screen comparisons retain the sprite failure, while 42 field comparisons pass. The aggregate has 21 cases: 12 green and nine exact known red; six missing requirement groups still prevent suite completion. Remaining native P1 comparisons and P2/P3 stay open. See the latest worklog and test instructions.

## Maintained source and regression suite (agreed 2026-09-30)

[The original-game reference specification](tests/reference-spec.md) defines
two complementary continuous match replays, meaningful observed coverage,
focused gap cases, fixture capture requirements and acceptance criteria.
Its execution plan specifies artifact destinations, R1 continuation/restart
discovery, two-player input calibration and R2 recipe, focused gap cases,
named presentation captures and separate data/port completion checklists.
Full-match captures and comparisons remain open; the passing serve case is the
initial foundation.

The exact one-player prefix reference is now captured twice identically through
the first game award, 136 tail-only callbacks and resumed serve flight (1,566
updates, 285 PSG bytes and eight recorded refresh decisions). The regression
runner consumes it with `--case round-transition`, matches 1,332 updates and
250 PSG bytes, then fails at the known unimplemented main-thread transition
before callback 1333. Source capture readiness and port parity are separate;
this is not a passing complete match. See [test instructions](tests/README.md).

Keep the reproducible translation as a reference baseline, then iterate on an editable, maintained 68000 port source. Native scheduling and direct Amiga hardware changes belong in that source rather than repeated generator patches. Preserve arithmetic widths, update order, rules and source cadence. Regeneration must not overwrite maintained code. Review the existing public-source policy before checking in ROM-derived translated source; private ROMs and extracted assets remain excluded.

The suite executes the actual assembled game routines, not a Python analogue. Capture reference cases explicitly in MAME, then use saved fixtures and Copperline for ordinary regression runs. Replay supplied inputs and initial state without real-time presentation waits. Compare named simulation fields and ordered sound events at each source callback. Gameplay versus tail-only dispatch remains future coverage. Control random inputs and identify nonportable state explicitly. Report the first differing callback, field, expected and actual values, and return a failing exit status.

Implemented foundation files:

| Location | Responsibility |
|---|---|
| `tests/README.md` | Run instructions, established coverage and gaps. |
| `tests/cases/*.json` | Initial-state fixture, input sequence, entry point, callback count and comparison fields. |
| `tests/reference/` | Saved source state and sound events; private ROM-derived fixtures stay local and ignored where required. |
| `tests/state-fields.json` | Field names, widths and locations for readable differences. |
| `amiga/tests/simulation_harness.s` | Call the same routines linked into the game, supply state/inputs and capture results without presentation waits. |
| `scripts/run_regression_tests.py` | Build, run Copperline and compare saved reference results. |
| `scripts/capture_test_reference.py` | Explicit MAME reference capture or extension, outside ordinary regression runs. |
| `build/tests/` | Ignored executables, captures and reports. |

The first case now passes `python scripts/run_regression_tests.py`: 200 continuous serve/flight/return/point callbacks, 254 RAM bytes at both post-gameplay and post-tail boundaries, and 40 ordered PSG bytes match an independent twice-identical MAME capture. `--self-test` detects a temporary ball-position mutation at callback 1. An independent negative run also returned exit 1 with the named difference; mutations were removed. The existing joined probe still passes after extracting shared build and test-I/O helpers. See [suite instructions and limits](tests/README.md). This does not establish complete-game correctness or change the phase gates.

The next work follows the suite-first goal below. Establish reference-backed cases and explicit known failures before broad port cleanup or implementing missing gameplay regimes. The current suite tests the generated routines shared with the live executable; it has not yet migrated the product to editable maintained gameplay source. Keep separate normal-executable checks for joystick sampling, Copper/sprite display, Paula DMA and real-time cadence.

## Intended endpoint and test migration (agreed 2026-09-30)

The final product is concise, targeted, maintained native Amiga code. The
translated 68000 implementation is a verified starting point, not a required
internal architecture. Iterate on it with regression evidence, replacing and
simplifying subsystems until translation scaffolding and original-hardware
implementation debt are removed. Optimize using measurements on the target
A500 while preserving gameplay, source cadence and presentation behaviour.
Internal state layout, routine boundaries and data structures may change.
Input, rendering and sound use the direct Amiga hardware paths; the product
must not need a Z80 machine model or an SG VDP/PSG translation layer.

Distinguish temporary translation diagnostics from lasting behavioural tests:

- Raw source RAM, emulated registers/flags, source callback pointers and PSG
  writes diagnose translation errors. They do not define the final port ABI.
- Lasting tests compare meaningful simulation state and outcomes, action
  acceptance, accumulated behaviour, logical timing, rendered content and
  audible events. They retain continuous replays and relevant edge cases.
- A small test-only observation adapter exposes named values and events from
  the actual native implementation. It translates observations and captured
  initial conditions, not gameplay or hardware operations. Keep this adapter
  out of the production update/render/audio paths.

For each subsystem replacement, define its behavioural contract from the
independent original-game evidence. Establish the new comparison alongside
existing detailed checks before removing those checks; preserve all relevant
cases, including known failures, and explicitly justify any internal fields
excluded from comparison. Map timing and random inputs to their observable
choices/effects without requiring the original registers or memory layout.
Sound comparisons move from source PSG bytes to equivalent audible events
and output, with documented acceptance criteria; graphics comparisons cover
displayed content and timing without requiring original VDP operations.
The adapter must read actual port results, never reconstruct expected results
or inject expected intermediate source writes to manufacture a match.

Retire obsolete diagnostics, macros, virtual-memory/register machinery,
generator dependencies and duplicated implementations as their replacements
are verified. Preserve independent source references and provenance as test
artifacts, not runtime dependencies. Final cleanup is complete only when the
maintained native executable builds without translation scaffolding, the
lasting suite preserves required coverage, and target hardware/performance
checks pass. Passing tests alone do not prove optimality or justify keeping
obsolete architecture. This migration follows the complete-suite baseline;
it does not narrow the current reference/test completion goal.

## Next goal: complete the reference-backed red/green suite

**Goal statement:** Build one-command regression coverage for every required
case in `tests/reference-spec.md` against the actual assembled Amiga port,
with independently captured source expectations, explicit known failures and
visible missing coverage. Establish the suite before broad port cleanup and
maintained-source conversion, so subsequent work preserves passing behaviour
and deliberately resolves recorded failures.

This goal establishes a diagnostic baseline; it does not require fixing all
port failures. It preserves observable original-game behaviour, not the
translated implementation or its memory layout. The following implementation
goal replaces those internals with concise maintained native Amiga code,
migrating diagnostic checks to behavioural contracts before retiring them.

### Work sequence

1. Extend the independent source capture to full R1 match/result/restart, then
   calibrate and capture R2. Preserve the accepted first-round prefix. Follow
   the reference specification's input recipes, stop guards, repeatability
   checks and artifact policy.
2. Index actual observed behaviours in a coverage manifest. Capture F1-F5 only
   where meaningful gaps remain. Collect the required P1-P3 original-game
   presentation/input/timing evidence. Never treat intended coverage as observed.
3. Generalize the existing runner to enumerate all registered cases in one
   invocation and execute the actual routines linked into the game. Ordinary
   runs use frozen source fixtures; reference capture remains explicit. Extend
   the harness for supported callback regimes and input/entropy streams, not
   by injecting expected source writes into port state.
4. Retain continuous R1/R2 replays for accumulated-state drift. Add source-derived
   phase cases starting before resumed serves, match completion and restart,
   where an earlier red boundary prevents independently diagnosing later code.
   Record starting-state provenance and required native entry point. A phase
   case does not replace the continuous replay or claim upstream parity.
5. Run every case and record the first divergence for each red result. Separate
   simulation comparisons from executable hardware/presentation checks. A
   missing entry point, unsupported adapter, absent reference or unimplemented
   comparison is missing coverage, not a gameplay mismatch and not a pass.
6. Register known failures and verify the suite's policy with deliberate
   gameplay mutations and altered failure signatures. Remove mutations and
   preserve the existing passing serve test. Update reports, instructions,
   coverage manifest, worklog and case status from the actual final run.

### Status and known-failure policy

| Status | Meaning | Effect on the goal |
|---|---|---|
| Green | A valid original-game reference exists and the port passes its checks. | Preserve on every subsequent change. |
| Red, known | A runnable reference-backed comparison fails with a recorded, understood first-divergence signature. | Valid baseline evidence, but remains visibly red. |
| Red, unexpected | A previous green case fails, or a known failure changes signature without an explained implementation change. | Investigate; baseline is not accepted. |
| Missing | Capture, adapter, entry point or comparison is absent/invalid/unsupported. | Goal remains incomplete for that required case. |

Plan to add `tests/known-failures.json` containing case ID, reason, relevant
implementation boundary, exact first-divergence signature (callback, boundary,
field/event and expected/actual values), and fixture/build provenance. Keep
transient tool/build/capture errors outside this register. Do not bless any
failure merely because it is reproducible. For presentation tests use a named
checkpoint and violated criterion instead of a simulation callback signature.

The all-case runner must show actual green/red/missing results and fail strict
validation while any required case is red or missing. A separate, explicitly
named baseline-check mode may succeed when all green cases stay green and all
known red signatures reproduce; its output must still show those cases red.
It must fail for unexpected differences, missing required cases and unexpected
passes. A formerly red case becoming green requires review of the passing
evidence and removal of its known-failure entry, not silent acceptance or a
stale exception. Never ignore exit codes or blanket-mark a whole family of
cases as expected failures.

### Deliverables and completion evidence

- All required source records, coverage intervals and media/checkpoint manifests
  from the reference specification, with duplicate-capture proof and reproducible
  local generation. Private inputs and ROM-derived oracles remain ignored.
- Tracked case definitions, field mappings, required native entry points, phase
  fixture provenance and `tests/known-failures.json`.
- One documented all-case command using existing runner/build helpers, with
  machine-readable per-case results and a concise coverage/status summary.
- A strict run exposing every outstanding red result and a baseline-check run
  that proves the unchanged green results and each known red signature. Missing
  coverage must be zero; source-data completion and port success stay separate.
- Demonstrated detection of a deliberate regression in a green case and a
  changed known-failure signature. No mutations remain in the accepted source.

This goal is achieved only when every required case is runnable and classified
green or specifically known red, all source-reference completion requirements
are met, no unexpected failures or missing checks remain, and the final reports
match the committed code and local frozen fixture hashes. Deferring a case
requires an explicit user scope change; difficulty is not an exemption. The
existing round-transition failure at callback 1333 is the first known-red
candidate, not evidence that this complete-suite goal is already met.

### Following goal: maintain and complete the native port

Once the baseline suite is established, freeze the generated translation as a
reference and establish editable maintained 68000 product source under the
existing repository/private-ROM policy. Link both tests and the live game to
that source; first require identical green results and known-red signatures.
Then clean up and implement native scheduling, round/match/restart transitions,
input, direct graphics and sound in reviewable changes. Each change preserves
all green cases and either preserves or deliberately resolves its related red
cases with evidence. Do not weaken reference data or broaden exclusions to
obtain green results. Finish when all required simulation and separate native
hardware/presentation checks pass; retain the existing ADF and independent
hardware verification gates.

## Goal

Produce a playable, native Amiga 500 port of the SG-1000/SC-3000 **Champion Tennis** cartridge. Preserve the original game rules and feel by translating its Z80 game logic to 68000 and replacing its video, sound, and input interfaces with Amiga implementations. Deliver a reproducible build, a bootable ADF, and evidence from automated comparisons against the original cartridge. The delivered Amiga game should not require the original cartridge at runtime.

The agent owns implementation and iteration. It should automate every repeatable operation, use investigation to discover facts and diagnose exceptions, and turn each discovery into checked-in annotations, code, or tests. Do not substitute an LLM's impression that the games “look the same” for executable comparisons.

## Starting assumptions and boundaries

- The user supplies a legitimately obtained Champion Tennis cartridge image and any required Amiga ROM through local configuration. Do not commit these files, their dumps, or unmodified extracted copyrighted assets to a public repository. Keep generated private build outputs local unless the user explicitly chooses to distribute them.
- Target an unexpanded PAL Amiga 500: 68000, OCS, 512 KB chip RAM, no slow or fast RAM, and Kickstart 1.3. Record the actual emulator and machine settings. The source cartridge's game speed and update behaviour take priority over evenly advancing every PAL video frame; measure the source cadence before choosing the Amiga presentation schedule.
- Treat SG-1000 cartridge gameplay as authoritative. Investigate SC-3000 input differences only where they affect this game. Require no unexplained reachable gameplay-state differences in the mandatory differential suite; document acceptable graphics and audio differences separately.
- Use **Gearsystem** for scripted SG-1000 checks, **MAME SC-3000** for the verified keyboard-mode and active-play source captures, and **Copperline** for scripted Amiga runs. MEKA and WinUAE can provide independent checks when an emulator-specific discrepancy arises. Do not treat Gearsystem's SG-1000 input path as definitive for SC-3000 keyboard mode selection.
- Gearsystem's installed headless build has passed an MCP connection, SG-1000 cartridge load, and synchronous two-frame stepping smoke test. Deterministic replay and the game's update cadence still need proof. An existing WinUAE configuration identifies a local Kickstart 1.3 file; its 512 KB chip plus 512 KB slow RAM setting must not be copied into the unexpanded target profile. Read the ROM path from local configuration, and verify the file and target profile independently.
- Jotd's [Moon Patrol](https://github.com/jotd666/mpatrol) and [Xevious](https://github.com/jotd666/xevious) are examples of Z80-to-68000 transcoding and asset conversion, not drop-in converters for this particular ROM.

## Repository and configuration

Keep the port in its **own local repository**. A setup script obtains pinned versions of [Gearsystem](https://github.com/drhelius/Gearsystem) and [Copperline](https://github.com/CopperlineHQ/Copperline), builds or installs them as needed, installs the 68000 assembler/linker and ADF packaging tools, and runs a capability smoke test. Keep third-party checkout directories outside the port's tracked source, or ignore them. Record exact commits and tool versions in test reports. The setup script should be rerunnable without discarding local work.

Use a local, ignored config file (with a checked-in example) for at least:

```ini
[inputs]
cartridge = C:/local/path/to/champion-tennis.sg
amiga_rom = C:/local/path/to/kickstart.rom

[machines]
source_system = sg1000
source_region = verify-from-cartridge-and-reference-run
target_model = A500
target_video = PAL

[tools]
gearsystem = C:/local/path/to/gearsystem.exe
copperline = C:/local/path/to/copperline.exe
```

Validate paths, cartridge size and hash, executable versions, and emulator capabilities up front. Store hashes and versions in results, but do not copy the user's inputs into version control. Identify the specific cartridge revision before accepting address maps or golden observations: an 8 KB image has been catalogued, but the supplied image must be checked rather than assumed identical.

Suggested project layout (names are illustrative):

```text
config.example.ini        local input/tool settings template
scripts/setup.*           pinned dependencies and smoke checks
scripts/analyse.*         ROM map, disassembly, code/data evidence
scripts/generate.*        generated 68000 and converted assets
scripts/build.*           executable and ADF generation
scripts/compare.*         coordinated two-emulator differential runs
analysis/                 annotations, symbols, hypotheses, evidence
translator/               Z80 translation rules and focused checks
amiga/                    hand-written hardware adapters and build inputs
tests/scenarios/          deterministic input sequences and edge cases
build/                    ignored generated outputs
reports/                  ignored or selectively checked-in concise results
```

Generated and hand-edited sources must remain separate. A regeneration must preserve annotations, mappings, patches, and Amiga-specific code.

## Phase 1 — Prove the test infrastructure

1. Boot the supplied cartridge in Gearsystem. Verify its hash, actual machine/region settings, title screen, inputs, and a short reproducible rally. Capture screenshots and a compact trace for a known input sequence.
   Measure the game's logical update cadence and repeat the same reset-and-input run to establish a deterministic source baseline. Define exactly when each press and release becomes visible to the game, including any repeated reads within one update.
   Gearsystem 3.9.18 misclassifies the supplied `.bin` filename as Master System. Stage a byte-identical `.sg` copy only in ignored local output, and require `is_sg1000=true` in the media report before collecting reference evidence.
2. Build a minimal Amiga executable that boots in Copperline. Prove automated launch, joystick injection, frame stepping, memory inspection, breakpoint control, and screenshots. Use direct executable launch for rapid iteration; reserve ADF testing for packaging milestones.
   Use the agreed unexpanded PAL A500 profile and decide the executable and ADF boot paths early enough to account for their memory and initialization costs.
3. Build a coordinator that can independently control each emulator and save two observations under one scenario ID. First compare **known scripted inputs and checkpoint counts**, not presumed equivalent CPU registers.
4. Record whether both interfaces can pause at a game-loop boundary, read state, inject controls, and resume deterministically. If a documented control method cannot do this reliably, make a small test adapter or use an alternative exposed interface. Keep the failure and workaround reproducible.

**Gate:** One command starts both emulators from a defined baseline, replays an input script, reaches chosen checkpoints, and writes a machine-readable report. This gate may initially compare only source-side observations against saved runs; equivalent Amiga game state becomes available later.

## Phase 2 — Understand the cartridge

- Establish the cartridge's physical and CPU-visible layout from the verified image, Gearsystem's pinned SG-1000 cartridge/memory implementation, and independent project examples. Keep original file offsets distinct from mirrored CPU addresses and RAM/IO. Record assumptions that the ROM or traces have not yet confirmed.
- Pilot a small command-line Z80 disassembler and matching assembler before adopting either. Start with `z80dasm` and `z80asm`, following the documented byte-exact Arkanoid MSX reconstruction; consider `z80-smart-disassembler` for alternative code/data and label hypotheses. Inspect source, build instructions, Windows availability, licenses, and runtime/build dependencies. Pin versions only after a local smoke test. Avoid a larger toolchain when a simpler one meets the same gate.
- Make the ROM reconstruction reproducible: a documented command consumes the locally configured original image and emits editable assembly covering every one of its 8,192 bytes exactly once. Assemble that source into an 8,192-byte image and require a byte-for-byte comparison and SHA-256 match to the input. Keep unknown regions explicitly represented as data bytes until evidence supports a stronger classification. The round trip establishes byte preservation, not correct code/data interpretation or gameplay understanding.
- Disassemble the ROM with explicit code/data classifications, labels, cross-references, and confidence/evidence notes. Use execution coverage, breakpoints, memory access traces, and VDP/PSG write traces to resolve ambiguous regions. A linear disassembly is only an initial hypothesis.
- Identify startup, main loop, interrupt handling, input sampling, game-state update, ball movement, collisions, scoring, serve handling, AI, rendering, and audio. Record entry points and stable **post-update checkpoints**.
- Map live RAM, relevant VDP RAM and registers, and persistent game state. For each candidate variable, record address, width, signedness, units, update routine, and the experiment or trace supporting it. Keep unknowns explicit.
- Extract and document tile/sprite, palette, text, and sound data. Distinguish original encoded data from Amiga-ready converted assets. Automate extraction and conversion once formats are understood.
- Capture a small set of reference gameplay scenarios from reset, including one-player and two-player controls, serves, rallies, score changes, and end-of-game transitions.

**Gate:** A reproducible analysis command rebuilds the 8,192-byte cartridge image byte-for-byte from the annotated source and produces a complete code/data/unknown map, labels, extracted-assets manifest, source-state map, checkpoint list, and example reference traces. At least one rally can be traced through the identified update path. Record separately which classifications and game-state meanings are still hypotheses.

## Phase 3 — Transcode and adapt

- Generate 68000 source from the annotated Z80 control flow and data references. Inventory reachable instructions, addressing modes, and indirect control flow; unsupported reachable cases must fail visibly. Preserve a source-address-to-target-symbol map. Make translation rules programmatic and give them small focused checks, particularly for flags, 8-bit arithmetic/wraparound, signed comparisons, stack/call behaviour, indirect control flow, and any self-modifying code discovered. Compare representative translated routines against source execution before integrating a full rally. Preserve original semantics before optimizing.
- Isolate SG-1000 hardware operations behind named interfaces. Implement Amiga joystick reading, graphics, sound, and timing on the other side. Keep game logic separately testable where possible.
- Convert original graphics to Amiga bitplanes/palette. Choose hardware sprites or blitter drawing after observing the actual sprite sizes, overlap, and colour needs. Maintain a map from source display objects to Amiga display objects.
- Implement sound events on Paula and test their triggering separately from waveform fidelity. Match game update cadence despite different source and target video regions.
- Build a native Amiga executable on every iteration. Record the build command, binary hash, memory footprint, and machine profile.
  Measure update time, missed display deadlines, and audio continuity during an unpaused run on the exact target profile. A checkpoint match does not establish real-time playability.

**Gate:** The executable boots, accepts input, runs a meaningful rally with score changes, and exposes labelled state at the same logical checkpoints as the source. Appearance and audio can still be provisional at this gate.

## Phase 4 — Differential testing and diagnosis

The coordinator drives both games with the **same logical input events**, rather than assuming identical controller bits or instruction counts. Stop each immediately after its corresponding game update, normalize only documented representation differences, and compare meaningful state. Do not compare the complete Z80 and 68000 register files or advance equal numbers of instructions.

Begin with this schema and extend it based on the discovered RAM map:

```json
{
  "checkpoint": "post_game_update",
  "game_phase": "rally",
  "ball": {"x": 0, "y": 0, "vx": 0, "vy": 0},
  "players": [{"x": 0, "y": 0}, {"x": 0, "y": 0}],
  "score": {},
  "serve_state": {},
  "ai_state": {},
  "timers": {}
}
```

The numbers above are placeholders, not presumed game fields. The map must identify each actual field's address or symbol, encoding, semantics, source evidence, and normalization rule. Missing/unidentified fields must be reported, never silently set to zero. Compare discrete state exactly when possible. For presentation, separately compare court and sprite geometry, screenshots at selected checkpoints, and ordered sound events; use explicit tolerances only where there is a justified difference.

For each mismatch, retain:

- the cartridge hash, executable hash, emulator versions/configurations, scenario and random seed if any;
- the shortest replayable input prefix and the **first divergent logical update**;
- source and Amiga state before and after that update, with field-level differences;
- the relevant execution and hardware-event traces, plus screenshots if the mismatch concerns rendering;
- a diagnosis tied to a change in translation, state mapping, hardware adapter, timing, or test assumptions.

Automate reduction of failing input sequences where feasible. Fix the underlying rule, add or update a regression scenario, regenerate, rebuild, and rerun the suite. The agent should use its judgment to investigate a mismatch, then encode what it learned so later runs no longer require the same manual reasoning.

For difficult conditions, add controlled state injection at verified checkpoint boundaries: collision edges, simultaneous input and bounce, serve/score transitions, byte overflow, AI branch boundaries, and match completion. Avoid impossible states by documenting invariants and replaying representative cases from reset when practical. Include longer seeded input runs to reveal interactions missed by hand-picked examples.

**Gate:** A documented suite passes across representative normal play and reachable edge cases with zero unexplained gameplay-state divergences. Every accepted presentation difference is listed with its scope and reason; “looks right” is not a pass criterion.

## Phase 5 — Package and verify

Build a bootable ADF from the passing executable. Test the **ADF itself** in Copperline from a clean boot with the unexpanded PAL Amiga 500 profile, real controller mapping, sound, and a complete playable match. Verify that a direct executable run and ADF run reach equivalent game behaviour at the measured source game speed. Retain the build recipe, ADF hash, test report, known limitations, and brief run instructions. State the chosen boot path's Kickstart requirement explicitly.

**Final deliverables:** source repository and reproducible scripts; ROM map and symbol/state evidence; generated source and asset-conversion pipeline; native Amiga executable; bootable ADF; replayable differential scenarios; passing report plus clearly stated remaining differences. The supplied cartridge/ROM paths stay local and are not required to play the finished ADF.

## Agent operating rule

Work autonomously through the phases. Prefer small verified increments, with the next experiment selected from the first unresolved mismatch or missing prerequisite. Use deterministic scripts for extraction, translation, builds, replay, comparison, and packaging. Keep manual annotations and decisions reviewable. Report progress in terms of demonstrated gates, failing cases, and reproducible artifacts, and avoid claiming equivalence beyond the scenarios and state fields actually tested.

## Relevant interfaces and examples

- [Gearsystem MCP documentation](https://github.com/drhelius/Gearsystem/blob/master/MCP_README.md): cartridge loading, synchronous frame stepping, breakpoints, Z80/RAM access, controller input, traces, screenshots, save states.
- [Copperline control protocol](https://copperline.dev/docs/control/): programmatic debugging, input injection, memory inspection, and MCP bridge.
- [Copperline direct executable launching](https://copperline.dev/docs/run/) and [headless/scripted execution](https://copperline.dev/docs/headless/): rapid build checks and replay.
- [Jotd Moon Patrol](https://github.com/jotd666/mpatrol) and [Xevious](https://github.com/jotd666/xevious): related transcoding and asset workflows.
