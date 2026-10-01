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

Final commands and exit codes are mechanically recorded in ignored
`build/ct05/final-commands.json` and `final-summary.log`. Each runner report has
run-start/finalization provenance for actual sources, emitted assets, executable,
independent reference data, tools and target. Private captures remain ignored.
Configuration: `RUST_LOG=info`, PAL A500, 68000, OCS, 512 KB chip, no slow/fast
expansion, Kickstart 1.3. Both ordinary logs contain those target markers.

| Existing maintained replay | Executed/matched | Result |
| --- | ---: | --- |
| `serve` | 200/200 | Passed |
| `deuce-sequence-phase` | 1649/1649 | Passed |
| `round-transition` | 1566/1566 | Passed; old update 1333/frame 2631 reset failure resolved |
| Four one/two-player lower/upper round-complete phases | 316/316 each | Passed |
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

## Remaining raw comparison failures

All four existing round-scene contexts match every viewport/field crop and have
no source-event mismatch. Each covers 268 consecutive state observations.
The existing **full raw-state** checker remains unchanged and reports:

| Context | Overall result | First raw difference |
| --- | --- | --- |
| First one-player/lower round | Failed | 1469, offset 0x67, expected 43, actual 240 |
| One-player/upper round | Passed | None |
| Two-player/lower round | Failed | 2672, offset 0x67, expected 43, actual 240 |
| Two-player/upper round | Failed | 4537, offset 0x67, expected 179, actual 240 |

Across these failures the only differing offsets are `0x67–0x68`, retired contact
scratch. The source contact routine writes its temporary coordinate there;
maintained native contact computes in named state/registers. Maintained replay
already omits `0x67–0x6a` under the CT04 policy. No new exclusions, tolerance,
expected-value writes or fixture edits were added to the scene checker. Its raw
red remains visible rather than manually declared green. Whether that checker
should adopt the existing maintained-state contract is an explicit review issue.

Missing original media were restored with the existing deterministic source
capture and freeze tools (primary one/two-player media and bounded upper-round
supplements). Original callback streams and repeated source rasters were
validated; no native output was made into an expectation. Logs are under
`build/ct05/restore-*` and `freeze-*`.

## Fault protection and freshness

An actual native point-increment fault (`+1` changed to `+2`) is detected by the
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
and avoids hashing inactive conditional assets. Unit controls: 17 passed,
including changed-asset invalidation for that truncation; no broad new suite.

`RUST_LOG=info python scripts/progress.py --fresh-since
2026-10-01T02:29:30+00:00` records fresh passes for the complete CT05 replays and
ordinary runs, fresh failures for three raw scene reports, and rejects the
2800-update prefix as full-match acceptance. **CT05 remains unverified.** Old
promoted green known-failure entries were removed only for the full round replay,
four full round phases and completely passing upper one-player scene. Other
known reds remain; no shortened or weakened comparison promotes them.

No complete match, result/restart, full ordinary cadence, RAM ceiling, ADF boot
or independent-hardware parity claim is made. CT06 has not begun.
