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
