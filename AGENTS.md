# Agent instructions

## Current goal and precedence

Read [PLAYABLE-PLAN.md](PLAYABLE-PLAN.md), then the newest [WORKLOG.md](WORKLOG.md) entry before choosing work. The finite CT-01–CT-10 queue is the current implementation order. It supersedes historical instructions to finish the entire reference-backed test suite before fixing or maintaining the port. The roadmap still defines the original target and final gates; historical worklog entries remain evidence, not competing current next actions.

This documentation change defines the queue. It does not itself perform or claim product implementation. When asked to implement or continue the port, take the first uncompleted, unblocked item. Keep **one work item active**; do not start parallel implementation or a separate coverage campaign.

## Product architecture

Build a concise maintained native 68000 game for PAL A500 / OCS / 512 KB chip / no expansion / Kickstart 1.3. Preserve observable rules, order, cadence and feel. Direct native input, rendering and sound are the endpoint.

Keep the reconstructed Z80, generated 68000 and original captures as reference oracles. Regeneration must never overwrite maintained game code. New logic belongs in the maintained product, not generator patch chains. Temporary adapters are explicit debt owned by a queue item; remove them after the native replacement is verified. Final runtime must not need emulated Z80 registers/flags, virtual source memory or SG VDP/PSG compatibility layers.

Product tests must execute the same maintained gameplay/dispatcher as the application. A test-only adapter may translate captured initial conditions and read named actual outcomes; it must not reconstruct expected gameplay or inject intermediate source resets/writes. Preserve raw-state translator checks separately while migrating relevant behavioural protection alongside each subsystem.

## Session discipline

1. Inspect current branch/worktree and applicable instructions; preserve other work. Confirm the queue item's dependencies and current evidence.
2. State the concrete product change or specific blocker to isolate, its acceptance check and finite stopping point.
3. Make the smallest useful implementation slice. Reuse the existing original reference and relevant tests.
4. Build the actual native executable. Run the focused reproduction and affected green guardrails after the final change. Check the ordinary hardware path when the item requires it.
5. Record the result and one next action in WORKLOG.md. Update queue status only when its observable acceptance has evidence.

A useful session changes the product toward the milestone, isolates an exact actionable blocker, or verifies a milestone. New tests, captures, scripts, case counts and unchanged baseline reruns alone are not implementation progress. If environment setup blocks a product check, record the exact missing input/tool and the unexecuted check; do not report it as passing.

## Test budget and integrity

- Preserve existing tests, independent source references, provenance and known failures.
- Add/extend a test only for the selected item's concrete fix or a demonstrated missing observable behaviour. First name the plausible fault, independent expectation, existing coverage gap and finite stop. Prefer extending an existing case.
- No exhaustive input/branch suite, duplicate scene permutations or new fidelity requirement without a distinct need.
- Relevant later observations must affect acceptance; an unchanged first known failure cannot certify a later output. Use one targeted late fault where necessary, not a whole new mutation campaign.
- Separate fresh execution, retained reports, local phase starts and full continuous play. Report matched/executed/reference extent when it matters.
- Never weaken an expectation or silently rebaseline a known red to make a fix appear green. Review changed outcomes against the original and explain promotions/remaining differences.
- Focused checks are normal per change. Run a complete aggregate at a meaningful delivery checkpoint or when a shared change invalidates broad evidence, not after every unchanged variant.
- Unrelated historical known reds/open coverage groups are not a reason to delay a product fix. Unexpected affected regressions must be resolved or explicitly block its acceptance.

## Repository hygiene and publication

Use ignored config.local.ini for legitimate cartridge/Kickstart paths. Never commit ROM images, full generated listings, private captures or unmodified extracted assets. Inspect the existing source/asset policy before introducing ROM-derived source. Record pinned tool versions and actual machine profile in verification reports.

Preserve all historical WORKLOG.md content. Prepend new entries; do not rewrite earlier results into current claims. Honour the user's publication scope, avoid overwriting concurrent edits, and verify the exact remote commit after an authorized push. A plan-only request does not authorize product implementation.

## Evidence freshness and progress

Run `RUST_LOG=info python scripts/progress.py` at session start and after the
selected item's checks. Use `--fresh-since <ISO timestamp with timezone>` to
identify executions in this session; compatible older evidence is **reused**,
not fresh. The command writes ignored `build/progress-report.json` and does not
run tests. See [report integrity](analysis/evidence-freshness.md).

Use the generated status and actual runner results in progress records. Missing,
legacy, stale, interrupted or partial evidence must not be manually declared
passed. A historical milestone's merged implementation may remain recorded as
verified while its current local evidence is unverified; explain that distinction.
An ordinary build's compiled symbols describe integration/dependencies, not
runtime acceptance. Translated diagnostics and known-red prefixes cannot certify
native product gates. RAM, cadence, uninterrupted play, ADF and independent target
validation stay unverified until their own measurements exist. Choose only the
focused checks needed for the active change; do not rerun a broad suite merely to
populate the progress report. Do not run builds/mutations concurrently.

## WORKLOG session template

### <actual date/time and timezone> — CT-XX: <concrete outcome>
- Status: ready / active / blocked / verified
- Before → after: observable capability, or the precise blocker isolated
- Product change: files and behaviour; explicitly say none when applicable
- Evidence: command, final executable/commit hash, machine profile, actual result and artifact/report path
- Guardrails: newly run / reused with provenance / not run; unexpected regressions and known failures
- Acceptance: which CT-XX criteria are verified, and which remain open
- Next action: one concrete step on this item, or the next ready item
- Blocker/decision needed: exact missing input, authority or unresolved question, if any

Do not mark an item verified merely because a test was written, a local phase passed or the documentation was committed.

CT05 focused ordinary acceptance uses
`RUST_LOG=info python scripts/run_ordinary_round_tests.py --mode=one` and
`--mode=two`: physical title choice, first game award, stationary round pause
and next advancing serve. It records consecutive actual callbacks; no phase
initialization or expected RAM writes. The existing four round-scene checks
remain full raw-state/pixel comparisons, including any obsolete scratch
differences. Report their raw failure separately from matched crops; do not
quietly remove fields or count that partial result as a passing gate.
