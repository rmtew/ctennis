# CT11 native independence cutover

Execution is authorized after merged release `50ef76227a72e137c37efe29502cf60b1d4590d4`. The Library specification `libfile_4418e95b71388191ab3e9857bf2927b3`, version 1, was read in full; its older draft-status text is superseded by this task's authorization. CT12–16 remain outside scope. No master merge or history rewrite.

CT11 is blocked at baseline/inventory. No product removals have occurred and no acceptance gate is claimed complete. This branch is isolated from release packaging at `/workspace/ctennis-ct11`.

## Baseline and ledger

[ledger.json](ledger.json) enumerates all 422 tracked paths at the merged baseline, with exact Git blobs and proposed keep/replace/remove dispositions: 39 keep, 54 replace, 329 remove. The family decisions below explain prerequisites. The ledger is a cutover checklist, not proof that retained dependencies are clean. [baseline.json](baseline.json) freezes the baseline tree, representative rollback verification, recorded release hashes, available native asset hashes, tools and fresh check outcomes. Release executable/ADF hashes are recorded WORKLOG evidence at product840e3ff, not newly observed artifacts at the merge commit. Enhanced version text embeds the commit, so complete executable equality needs an explicit stable version-input contract during behavior-neutral comparison.

`git show 50ef76227a72e137c37efe29502cf60b1d4590d4:amiga/game/interface_demo.s` reproduces the current tracked bytes exactly. Git history is the rollback location for eventual tracked deletions; no archive directory is proposed.

| Family | Disposition and finite prerequisite |
| --- | --- |
| `amiga/game/`, native application and hardware includes | Keep native game and assets. Remove captured-state ABI, diagnostic conditionals and obsolete probe naming after native contracts execute the real dispatcher. |
| Original interface flavor | Recommend retiring it as a delivered flavor. Current code offers native comparison layout, not distinct gameplay. It duplicates title/layout/assets and acceptance burden. Preserve its useful assertions in enhanced contracts and use merged Git history for comparison. Final disposition needs parent/user decision; unchanged in this draft. |
| Native build/package/tool/hunk helpers | Keep responsibilities, pinned tools and deterministic packaging. Replace phase-start/config/source-memory path with explicit native assets and missing-input validation. |
| Asset generators and source models | Remove after native input pack is preserved, versioned, validated and build-tested. Move pose/animation, glyph, score-bank and audio definitions into native contracts. |
| Original capture/translation/emulator machinery and Z80 tooling | Remove after useful independent protection transfers. No MAME/Gearsystem/cartridge test/build requirement remains at cutover. |
| Original recipes, references, adapters and historical gate units | Replace useful assertions with native initialization/controls/entropy and frozen independent expectations. Never derive new expected state from the implementation under test. |
| PR15 native recording and canonical10958 fixture | Keep. Verified 10958 digest lines and payload SHA256 `17dd5ddba0499a70956b2d588f084786a00c294672510f69ef991858734d79e6`. Native capture provenance is distinct from original-platform media. |
| Historical analyses/roadmaps/plans/worklog/archive | Transfer current constraints, asset provenance and risks into concise docs, then remove active historical documents. Historical AGENTS preservation rules are superseded by the explicit whole-repository CT11 authorization. |
| Hidden config/manifests/ignore policy | Preserve private exclusions. Replace cartridge/source-system/Gearsystem setup with native tools/assets plus separately configured legitimate Kickstart for Copperline only. |

## Concrete blockers and asset decision

The supplied existing checkout has native score/sprite outputs but lacks `build/amiga/native-scene`, `build/amiga/native-audio` and `build/amiga/title`; the isolated branch has no native asset set. A fresh enhanced build with copied vasm1.9d fails first on `build/amiga/native-scene/poses.bin`. Required poses, animations, sprite images, native sound data and both relevant title/font include closures therefore cannot be frozen or validated. Do not rebuild them from cartridge or original captures to conceal this missing transfer.

Request the existing approved merged-release native inputs through a supported transfer into this executor. No presumed parent filesystem or failed-transfer bypass. The native pack must contain only required native binary/include/authoring inputs, not executable/ADF/cartridge/Kickstart/source captures, with recursive include closure, dimensions, planes/palettes, schema, sizes, hashes and provenance. A manifest without its bytes is insufficient.

Recommended durable storage: a versioned private Library native-input pack, addressed by immutable version and SHA256, materialized explicitly into an ignored native-assets directory. Approve that destination before creating or uploading it. No change to current exclusions and no native asset commit is authorized by this draft. A separately approved private storage alternative is acceptable. Converted graphics/fonts/music remain Sega-derived; conversion does not grant ownership or public redistribution rights. Current native graphics/audio are retained, not redesigned.

No untracked input was deleted, moved or committed. Original input/reference/tool directories in the supplied checkout are untouched and may contain irreplaceable untracked files. Their provenance/retention decision must precede any later physical cleanup; Git covers tracked files only.

## Finite remaining execution

1. Obtain/approve and freeze native asset pack; verify every required input and tool, preserved provenance and missing/incompatible-input failure. Freeze actual merged-baseline executable/ADF/symbol hashes with explicit version-text treatment.
2. Transfer finite native controls, launch/rally/bounds, scoring/deuce/advantage, lifecycle/restart, render/status/tally, audio and timing protection. Keep exact completed scene/bank association, sprite-header publication deadline and tally DMA-slot reasoning. Preserve canonical10958 protection. Native cadence is `11838 + 14906/65536` PAL E-clock ticks with established rounding/deadline rules.
3. Perform ledger removals in reviewable commits; update imports/includes/docs/manifests/config and current issue/provenance ledger. No active archive, original-format data, source emulator or Z80 reconstruction remains.
4. New checkout, empty outputs/cache, only native pack and pinned tools, original inputs absent/inaccessible: build/package twice with byte/hash equality and embedded executable equality; native host checks; bounded Copperline PAL A500/68000/OCS/512KB/no expansion lifecycle/menu/pause/fullmatch-demo/takeover plus retained controls/scoring/render/audio/timing guards and read-only cold ADF. Record exact head/commands/tools/assets/checked extents and pass/fail/notrun. Stop for independent review and merge by parent.

Fresh checks so far: 43 host units PASS without config/ROM; fixture integrity PASS; enhanced build FAIL missing poses; deterministic packaging and Copperline NOT RUN. Progress invocation completes but reports missing/unverified evidence; it does not certify CT11. Existing units still encode historical contracts and are not a transferred native acceptance suite.

Known limits to carry forward: pre-Exec-pool bootstrap RAM unmeasured; whole-game source pixel/waveform/filter/phase/stereo parity unverified; old 99-case aggregate failed and remains historical, not an endless current gate. User WinUAE6.0.2 tally confirmation included512KB slow RAM and is separate from unexpanded Copperline target acceptance. Current baseline WORKLOG reports missing original presentation/audio fixtures; no substitute oracle is synthesized here.

## Approved follow-up

On2026-10-02 at07:02:50UTC the user explicitly approved storing retained native graphics/audio directly in private `rmtew/ctennis` and retiring the original comparison build. This supersedes the pending storage/flavor decisions above and the prior asset-input exclusions for that native set only. Cartridge, Kickstart, source media, executable and ADF exclusions remain. The release worker is preparing a supported Library transfer; wait for its exact ID before importing bytes. No original-input regeneration.

Independent preparation extracts native listing/target validators from historical presentation runners and directly declares the accepted PAL clock in `scripts/native_clock.py`. Menu/demo/feedback and ordinary-cadence imports no longer load translated PRNG or original presentation runners. Current asset absence still blocks assembly, runtime and protection-transfer completion.
