# Complete later-regime diagnostic coverage

The baseline now classifies 63 cases: 39 green and 24 exact known red. The
aggregate self-test completed without unexplained differences or tool failures.
Four required groups remain open: focused F2/F4/F5 behaviour, P1 graphics,
P2 audio and P3 ordinary executable input/cadence/deadlines. The suite therefore
still fails. Known-red cases are not independent defect counts.

## Source evidence and finite endpoint

`one-player-restart-complete` and `two-player-restart-complete` repeat the
original full-match input schedules, extending only their stop frames. Each
source capture was independently repeated. Their entire old callback prefixes
(13,378 and 27,037 updates) remain identical, including initial state. Original
full-match fixtures remain unchanged. New lengths are 13,413 and 27,072 updates.
The extra callbacks prove row-two handoff and serve animation release, rather
than stopping at the first advancing flight.

| Extension | Raw capture SHA256 | Fixture SHA256 |
|---|---|---|
| One player | `2061dedb1a84d52ca323292ae529e219a07cd55f25624707729e4b7505962505` | `5f2b217242b654e1d964cfa9aa8e32a8b53ada28e42da8d9c93bf0669bbf7480` |
| Two players | `0e12179dbaa87d52e35306c13e7f47f77a8ff980e5b6d2b754d933dc1f5b760d` | `4ed7b21b75a25429d8862dd3d56bac5f89f5ddd3e773d660ef583a952b0c6014` |

`scripts/regime_reference.py` validates reachable starts, source milestones,
server/receiver identity, human versus AI handoff and animation release. Six
shortened full-interval recipes were rejected. Historical short snapshot
prefixes and initial states were also preserved when expanding their ends.

## Full intervals and measured failures

Each phase initializes once from the source start, then runs the actual assembled
native routines through the entire interval. Expected main-thread writes are
observations only; they are never injected into native state. Full standalone
runs completed before registering signatures. Aggregate baseline runs stop at
the exact known first failure; they do not claim matching later callbacks.

| Phase | Initial source update | Compared callbacks | Complete endpoint | First divergent source update |
|---|---:|---:|---:|---:|
| One-player lower round | 1203 | 395 | 1598 | 1333 |
| One-player upper round | 3844 | 316 | 4160 | 3974 |
| Two-player lower round | 2406 | 316 | 2722 | 2536 |
| Two-player upper round | 4271 | 316 | 4587 | 4401 |
| One-player match/restart | 11959 | 1451 | 13410 | 12089 |
| Two-player match/restart | 25618 | 1451 | 27069 | 25748 |

All six first fail at local callback 130, after 129 matching callbacks, on
entry to a tail-only callback. Round cases differ in the deferred display setup
request (expected 129, actual 1). Match cases differ in the first audio channel's
stream pointer low byte (expected 150, actual 4): the source main thread queues
result music. The live native main-thread transition is not implemented.
The two complete extension replays retain their original first round failures
at source 1333/2536. Longer references do not turn those failures into passes.

## Independent later comparisons

| Case | Callbacks | Result |
|---|---:|---|
| round-tail-phase | 136 | Known red at local 1: input direction B, 1 versus 0 |
| match-tail-phase | 448 | 192 match; local 193 misses title/menu display request, 131 versus 1 |
| resumed-play-phase | 200 | 95 match; local 96 AI launch trajectory, 199 versus 200 |
| restart-play-phase | 50 | Green, 20 ordered PSG events |
| two-player-resumed-serve-complete-phase | 50 | Green, 20 PSG events |
| one-player-upper-resumed-serve-complete-phase | 50 | Green, 20 PSG events |
| two-player-upper-resumed-serve-complete-phase | 50 | Green, 20 PSG events |
| two-player-restarted-serve-complete-phase | 50 | Green, 20 PSG events |
| one-player-ai-launched-serve-complete-phase | 32 | Green, 15 PSG events |

The result-tail case was previously green over 40 callbacks. Extending it to
menu selection reveals an existing missing stage after 192 matches, not a new
product regression. The independent AI case starts just after the known faulty
launch and protects subsequent flight/handoff/release. Independent starts prove
local behaviour only. They do not prove the port naturally reached that state.

All green later cases have mutation sensitivity checks. The post-launch case
corrupts the active flight vector and detects it at its first callback; other
serve cases detect a changed ball coordinate at their first callback. Exact
known-failure policies reject altered signatures and unexpected passes.

The upper contact timing validator now compares the actual active flight vector
instead of a range including input scratch. Before/at contact select
`8c257e1b612d00`; after selects `914e521b612d00`. Keeping action scratch different
while restoring the normal vector is rejected. Existing source fixtures remain
unchanged; all three native contact cases and targeted mutations still pass.

## Reproduction and stopping boundary

Use `python scripts/capture_test_reference.py --help` for explicit source capture
or verification; normal regression never recaptures the oracle. Run an individual
case with `python scripts/run_regression_tests.py --case <case-id> --self-test`.
Run the aggregate with
`python scripts/run_test_suite.py --baseline-check --self-test`.
Source-derived fixtures, logs and media remain private ignored artifacts;
maintained scripts, recipes, policies and conclusions are public.

The later-phases diagnostic group is complete. Stop equivalent window expansion.
Next compare distinct retained graphics/audio checkpoints through actual Amiga
hardware paths, then finish remaining focused behaviours and ordinary execution
checks. Fixing the registered transition/launch/menu defects belongs to the port
implementation phase. Current RAM/PSG diagnostics may later be retired only
when their required observable behaviour is protected by native tests; they do
not require retaining translated registers or original hardware interfaces.
