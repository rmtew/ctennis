# Native Amiga development

Maintain Baseline Rally for A500, 68000, OCS and 512 KB chip RAM with no expansion.
Use legitimate external Kickstart 1.3 for emulator tests. Read README.md,
tests/README.md and docs/limits.md before changing the project.
Keep one concrete work item active. Independent review must precede merge.
Do not change master directly or rewrite history.

Branding, Classic human/robot sprites, Font-Mac, Battle Hymn and match celebration
are integrated. Replacement music needs user selection. The authorized tutorial scope and implementation
roadmap are in docs/tutorial-mode-design.md. That document replaces conflicting
proposals in draft PR #24; it does not approve the old draft wholesale.
Bounded recording and seek are in scope; persistent saves remain later work. Exit-game work was cancelled; reboot is intentional.

Runtime code is in amiga/main.s and amiga/game/. Preserve the assembly style.
Tests must exercise the actual native dispatcher, controls, rendering and audio.
A fixture can initialize native state once. After that, use controls and entropy,
and read actual outputs. Do not inject intermediate expected state, select a
callback regime, duplicate the game as an oracle or regenerate expected results
from the implementation. Keep the independent 10,958-tick trajectory bound to
its recording and seed.

Builds use explicit versioned native inputs and tools.lock.json. Missing or
corrupt inputs must fail. Do not recover them through extraction or archives.
assets/native is approved private storage; retain Sega-derived provenance.
Keep cartridges, Kickstart, original captures, executables, ADFs and raw runtime
reports outside Git. Do not destroy irreplaceable untracked inputs. Recover
tracked removals through Git history, not archive directories. Public publication
needs separate authorization.

Run focused checks after a change. The finite full native gate is
`RUST_LOG=info python scripts/native_acceptance.py`. Do not recreate the retired
aggregate or repeat manual playthroughs without need. For neutral changes, prefer
byte/symbol equality and relevant checks. Receipts must name the exact commit,
inputs, tools, target and checked extent. Distinguish fresh, reused and stale
results. A failed or interrupted rerun supersedes earlier passes.

Check actual completed banks and epochs, sprite-header publication timing and
visible tally output. Counters alone do not prove correct output. Report exact
commands, hashes, failed checks and checks not run. Source inspection or host
unit tests do not establish a native gate pass.

Builds regenerate ignored static metrics. Existing cadence, setup and demo checks
collect runtime and loading metrics. After affected resource validation, run
`python scripts/native_metrics.py --require-runtime --record`. Review and commit
both docs/metrics/current.json and .md. For documentation-only work, use
`--check`; do not start another emulator campaign. Follow docs/metrics/README.md.
Product labels exclude report and documentation commits outside product inputs.
Do not inspect another worker's unfinished branches.

Release packaging removes only HUNK_SYMBOL records. Keep the development
executable and listing for debug observers. Check the exact stripped release
bytes on cold boot. Report development and release hashes separately.
