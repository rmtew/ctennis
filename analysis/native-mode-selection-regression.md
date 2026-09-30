# CT-02 native title and physical selection (2026-09-30 UTC)

The historical failures below are preserved as provenance. The three existing
`p1-title`, `p1-accept-one-player`, and `p1-accept-two-player` cases now pass on
the maintained ordinary executable. Only these three known-red policies are
removed; no aggregate or later presentation family is promoted.

Native title/selection state owns mode acceptance. CIA-A serial input decodes
Delete/Tab, acknowledges the keyboard, latches one choice during a hold, and
waits for release plus the existing 64-tick minimum before active play. Native
runtime initialization fills the temporary legacy gameplay fields; it does not
load either mode's captured RAM. A repeated selection press during play cannot
restart it. Both choices wait in serve state until physical port-2 fire.

This environment retained the cartridge, Kickstart and source timing/serve
captures, but neither full-match presentation fixtures nor `copperline-ctl`.
The bounded source-media restoration samples only frames 119/300/1299 for both
choices, repeated identically. It validates the configured cartridge against
the MAME archive, captures original raster/VRAM/register/RAM observations and
keeps them ignored. The title raster exactly matches decoded static VRAM. The
moving ball's accepted-frame VRAM can follow its scanout, so the independently
rendered raster remains the pixel oracle. No target output generates expected
pixels. Copperline's existing CCP server supplies physical input, memory reads,
execution stops and completed-raster screenshots without installing a bridge.

Each mode run verifies title gating, one acceptance during five seconds held,
release before gameplay, first completed mode-label generation, and an exact
whole accepted viewport. The moving serve ball is aligned using only its
observed vertical pose; unrelated pixel differences still fail. The required
sprite-origin correction `$6c` → `$80` is a one-line CT-02 acceptance prerequisite
from the documented CT-07 defect, not a renderer migration. The first ordinary
DMA display is the title list, with sprite DMA disabled until court commit.

The existing two-player sprite/mode negative controls both fail as required.
A wrong mode fails the first accepted-generation ownership assertion; shifted
sprites fail the full viewport even after the ball pose aligns. The original
expectations are unchanged. Local reports and captures are under
`build/tests/p1-*-normal/` and `build/tests/p1-*-report.json`; detailed commands,
hashes, failed development attempts and unrun checks are in WORKLOG.md.

This establishes CT-02 startup/choice only. It does not complete physical upper
controls, scoring/round/result lifecycles, native gameplay/render/audio migration,
full matches, original audio fidelity, ADF delivery, or real-hardware validation.

---

# Native physical mode-selection failure tests

Both choices start the same fresh ordinary native executable and current R1 initialization. Neither initializes selected R2 state nor writes expected mode flags through the emulator. Source keys are independently documented in MAME's retained SK-1100 source: PA3/$10 is Del/Ins (one player); PB5/$08 is Func (two players). Native policy maps these to Delete rawkey$46 and Tab rawkey$42 respectively. Copperline input_key schema was queried live before use.

Each run observes a complete raster before the key press at two emulated seconds, after a five-second hold and release, and after22 seconds. These deadlines establish bounded observation, not source/native timing equivalence. Original accepted-mode frame1299 pixels and RAM hashes are verified; expected mode flags are0/$80. No new original capture was needed.

Actual ordinary behaviour:120 source-rate callbacks have completed before either key is pressed, with lower serve-wait and upper receive phases already active outside waiting mode. Counts include tail/menu work and are diagnostic; active player phases and mode state determine premature gameplay. Hash-verified original frame119 has no active player phases. At the final observation1318 source-rate callbacks have completed. Delete retains one-player flags0; Tab also retains0 instead of$80. Both completed pictures differ from the source. Matching the default one-player flags does not establish acceptance: both cases fail the requirement that gameplay await a choice.

The accepted-mode path is absent. The timed final viewport is therefore diagnostic and is not claimed as a generation-aligned accepted-mode observation. That comparison remains an explicit requirement when the acceptance path exists. These tests establish missing choice gating and two-player response, rather than closing all mode presentation work.

Both ordinary cases repeat with identical compared outputs. Each rejects two actual compiled variants behind the unchanged first failure: one-pixel sprite-origin shift and startup mode-bit change. Eight native launches total (two normals, four mutants, two repeated normals). No product source was changed. Complete stage output hashes, mode flags, field values and pixel differences are pinned; scheduler-dependent callback counts and stop metadata remain evidence without being treated as exact timing expectations. Changes to later outputs cannot hide behind the early missing-choice error.

Run:

```powershell
python scripts/run_mode_selection_tests.py --case p1-accept-one-player --self-test
python scripts/run_mode_selection_tests.py --case p1-accept-two-player --self-test
```

Both currently return1, with exact known-red reports. The97-case aggregate is52 green/45 known red. These two cases were executed;95 previous reports are reused with incremental provenance, not a claimed full97-case run. Four coverage groups remain incomplete. Stop repeating missing-mode variants. Next protect distinct match/result/menu/restart outputs using the existing independently captured scene generations, then remaining court outcomes/audio/ordinary execution requirements.


Correction verified after the initial milestone: the gating assertion now uses active player phases/waiting mode, not callback count. Both normal runs repeated identically and all four compiled mutants were rejected again. The97-case figure above is historical; current aggregate is99 cases,52 green,47 known red.
