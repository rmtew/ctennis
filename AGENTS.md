# Native Amiga development

Maintain Baseline Rally, the enhanced native game for PAL A500,68000,OCS,512KB chip,zero slow/fast
RAM and legitimate separately configured Kickstart1.3 testing. Read README.md,
tests/README.md and docs/ct11/risks.md before choosing a change. Keep one concrete
item active. CT12 branding/palette/readability is implemented on its draft branch, preserving
CT11 independence and focused native UI timing. CT13 music/celebration requires
user audition; CT14+ recording/save/seek remains later scope. Independent review
precedes merge. Do not change master or rewrite history.

Runtime lives in amiga/main.s and amiga/game/. Tests exercise the actual native
dispatcher, input, rendering and audio. A fixture may initialize native state once;
afterward use controls/entropy and read actual outputs. Never inject intermediate
expected state, select a callback's regime, duplicate the game as an oracle or
regenerate a golden from the implementation under test. Keep the independently
frozen10958-tick trajectory bound to its recording and seed.

Build/package consume explicit versioned native inputs and tools.lock.json only.
Missing/corrupt inputs fail rather than triggering extraction or archive recovery.
Assets/native is approved private storage for retained native graphics/audio;
keep honest Sega-derived provenance. Cartridge/Kickstart, original captures,
executables, ADFs and raw runtime reports stay outside Git. Do not destroy
irreplaceable untracked files. Tracked rollback uses Git history, not active
archive directories. Public publication requires separate authorization.

Run focused checks after a change. The finite full native gate is
`RUST_LOG=info python scripts/native_acceptance.py`; do not recreate the retired
historical aggregate or repeat manual playthroughs. For neutral refactors prefer
byte/symbol equality and relevant checks. Receipts distinguish fresh/reused/stale,
name exact commit/inputs/tools/target/checked extent and replace older passes on
failed/interrupted reruns. Verify actual completed bank/epoch, sprite-header
publication timing and visible tally output; counters alone are insufficient.
Report concrete outcome, exact commands/hashes and any failed/not-run checks.
Do not mark a gate passed just because source inspection or host units passed.

Resource changes: builds regenerate ignored static metrics. Existing cadence,
setup and demo checks collect resource/loading metrics; the finite gate checks
report completion. After affected validation, run
`python scripts/native_metrics.py --require-runtime --record` and commit both
`docs/metrics/current.json` and `.md` with reviewed changes. Follow
`docs/metrics/README.md`; docs/report-only changes use `--check`, not an extra
emulator campaign. Product version labels exclude docs/report commits. Later
failed/interrupted runs supersede old passes. Remeasure new fonts/celebration
only after their implementation lands; do not read other workers' branches.
