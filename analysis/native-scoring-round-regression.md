# CT05 native scoring and round lifecycle checkpoint

The maintained application and replay now run `game_score_resolve` and shared
main-path `game_round_poll`. Point/game cells, service mode and scoring stages
are named native state. Generated `score_gate` is absent from the native build;
explicit translated diagnostics retain it. Gameplay, scoreboard/sprite and audio
compatibility adapters still exist. Match result/restart remains CT06 work.

The round poll runs between callbacks in both the application and maintained
replay. It reacts to native scoring state, not a recorded callback address or
injected expected writes. It freezes gameplay while the shared service tail
advances clocks, audio and display requests; resets players and advances service
and end ownership; waits for phase/audio completion; then resumes. The paused
application also refreshes the inactive sprite bank before swapping Copper
lists. Omitting that preparation caused a real missing-player pixel at reset;
the unchanged comparison now matches.

## Focused execution

Final revised commands and exit codes are mechanically recorded in ignored
`build/ct05/revised-commands.json` and `final-scene-commands.json`. The latter
refreshes all four complete scenes/faults after the final run-start fix. Each runner report has
run-start/finalization provenance for actual sources, emitted assets, executable,
independent reference data, tools and target. Private captures remain ignored.
Configuration: `RUST_LOG=info`, PAL A500, 68000, OCS, 512 KB chip, no slow/fast
expansion, Kickstart 1.3. Both ordinary logs contain those target markers.

| Existing maintained replay | Executed/matched | Result |
| --- | ---: | --- |
| `serve` | 200/200 | Passed |
| `deuce-sequence-phase` | 1649/1649 | Passed |
| `round-transition` | 1566/1566 | Passed; old update 1333/frame 2631 reset failure resolved |
| One-player/lower round-complete phase | 395/395 | Passed |
| Other three round-complete phases | 316/316 each | Passed |
| Two two-player resumed-serve-complete phases | 50/50 each | Passed |
| Continuous `two-player-match --through-update=2800` | 2800/2800 | Passed declared prefix beyond old 2536 failure; full 27037-update match not executed |

Commands are `RUST_LOG=info python scripts/run_regression_tests.py
--subject=maintained --case=<name>`, with the explicit prefix option only for the
last row. Complete CT05 phase cases default to maintained; full-match and other
unmigrated diagnostics keep their separate translated default. CT04's fixed
25-case gate is not enlarged.

Ordinary checks use `RUST_LOG=info python scripts/run_ordinary_round_tests.py
--mode=one` and `--mode=two`, with the same ordinary executable, physical keyboard
mode choice and held red on both physical ports. No captured phase start or RAM
write is used. Consecutive actual callbacks verify one game award, zero points
and stationary players throughout the round pause, then an advancing next serve.

| Ordinary mode | Award | Pause begins | Resume | Advancing next serve | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| One player | 1799 | 1928 | 2064 | 2161 | Passed; 1861 observed callbacks |
| Two players | 1348 | 1477 | 1613 | 1631 | Passed; 1331 observed callbacks |

These callback numbers are observations, not timing/parity expectations. They
include the ordinary selection lifecycle and normal timer-derived entropy.
Final ordinary executable SHA256:
`e77510df79d8fcdc4e9c1bdb5d75534b406c660804b8d1849b6b1479dd643d43`.

## Semantic acceptance and preserved raw diagnostics

All four existing round-scene contexts match every viewport/field crop and have
no source-event mismatch. Each covers 268 consecutive state observations.
The explicit `CT04-maintained-state-v1` contract compares 250 retained bytes per
callback, omitting exactly the existing four translated arithmetic scratch
bytes C067–C06A. All four complete scene windows pass this semantic comparison.
The separate `original-byte-page-diagnostic-v1` contract still compares all254
raw bytes from the same maintained executable and preserves these results:

| Context | Raw diagnostic result | First raw difference |
| --- | --- | --- |
| First one-player/lower round | Failed | 1469, offset 0x67, expected 43, actual 240 |
| One-player/upper round | Passed | None |
| Two-player/lower round | Failed | 2672, offset 0x67, expected 43, actual 240 |
| Two-player/upper round | Failed | 4537, offset 0x67, expected 179, actual 240 |

Across these failures the only differing offsets are `0x67–0x68`, retired contact
scratch. The source contact routine writes its temporary coordinate there;
maintained native contact computes in named state/registers. Maintained replay
already omits `0x67–0x6a` under the CT04 policy. The semantic check now applies that same exact contract; raw comparisons
remain intact and are explicitly labelled separately. Pixels and observed event
streams remain exact. No expected-value writes or fixture edits were made.
Parent reported independent consumer/poison validation at2b6c36f: altering all
four scratch bytes changed only scratch over268 callbacks, preserving pixels,
entropy and ordered sound. This supports the qualification; exact revised-head
independent review remains pending.

Missing original media were restored with the existing deterministic source
capture and freeze tools (primary one/two-player media and bounded upper-round
supplements). Original callback streams and repeated source rasters were
validated; no native output was made into an expectation. Logs are under
`build/ct05/restore-*` and `freeze-*`.

## Fault protection and freshness

The historical control on the unchanged native scorer, an actual point-increment fault (`+1` changed to `+2`) is detected by the
full round replay at update 134/frame 1433/pre-tail/offset 0x3f, expected 1,
actual 2. Source restoration reproduces the previously passing round executable
SHA256 `778812426f84b74fd5308fa698b90ca87ed0bbcae5750b5121deb86f0ff71ede`
and full 1566-update pass. The deuce phase alone does not exercise love/fifteen
increments; an initial fault probe there was undetected and was not accepted
as fault protection. Reports/logs: `score-fault-*` and final round replay.

Round-scene and ordinary-round runners use existing atomic evidence transactions.
Case-owned phase assets prevent later captures invalidating unrelated subjects.
The capture tool falls back to existing direct CCP when the optional control
bridge is absent. A targeted compilation-manifest fix resolves a truncated
emitted `incbin` from its unique actual source prefix, fingerprints the asset,
and avoids hashing inactive conditional assets. Unit controls:23 passed, including source-context resolution for truncated
assets, bounded-gate false-pass cases, and actual scene run-start retention.
Long mutant paths are resolved within their actual listing Source section;
ambiguous/missing recovery fails. No broad new suite.

`RUST_LOG=info python scripts/progress.py --fresh-since
2026-10-01T03:42:49.850470+00:00` records all required CT05 checks passed/fresh
and **CT05 evidenced within its bounded scope**, not independent-review clearance.
The R2 first-round gate requires current maintained continuous evidence through
original resumed-flight milestone2690; actual2800/27037 is explicit, with
`full_match_executed=false`. The separate full-match status rejects that prefix;
**CT09 stays unverified**. The progress output also exposes all three raw
scratch failures separately from semantic passes. Removed only now-green
product known-failure baselines; original expectations/raw diagnostics remain.

Each scene has268 consecutive state observations and28 exact crops, totaling
112 crops across four contexts. All sixteen actual compiled faults are detected:
sprite, point-field display, extra entropy consumption and retained byte0x7c,
which is outside scratch. Pixel faults use the measured completed-bank
generation; state/entropy faults use the exact reset callback. Root provenance
fingerprints every fault capture, executable, emitted source/assets and media.
A scene run keeps its atomic incomplete record until finalization; one targeted
unit control verifies setup failure cannot erase it or revive an old pass.

Ignored `build/ct05/revised-evidence-index.json` links final source/comparator
fingerprints, original references, normal/fault executable hashes, results and
raw differences. `revised-progress.json`, `revised-unit.log`, `revised-*.log` and
`final-scene-*` provide mechanically generated supporting evidence. The index
is private evidence, not committed raw data.

No complete match, result/restart, full ordinary cadence, RAM ceiling, ADF boot
or independent-hardware parity claim is made. Current CT05 revision is reviewable,
not cleared or merged. Subsequent work waits for parent exact-head clearance.
