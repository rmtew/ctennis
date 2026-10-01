# Local evidence freshness

This integration wraps existing JSON reports; it does not implement gameplay,
regenerate original expectations, replace their comparators or introduce a new
coverage campaign. Historical CT-01–CT-04 implementation evidence remains in the
worklog. Current local acceptance is computed independently from retained reports.

## Command and dimensions

```sh
RUST_LOG=info python scripts/progress.py
RUST_LOG=info python scripts/progress.py --fresh-since 2026-10-01T01:00:00+00:00
```

The command checks dependencies without running tests and atomically writes
ignored `build/progress-report.json`. Its own latest invocation is invalidated
before aggregation and atomically completed; the view records source/report
fingerprints and generation time. Rerun the command before trusting current gates;
a saved summary is a timestamped snapshot, not a self-updating assertion. It separates:

- Behavior: fixed CT-01–CT-10 evidence names, maintained subjects, complete replay
  extents, first mismatch and ordinary versus captured starts. CT-01 requires the
  actual dispatcher fault/restoration. CT-02/03 require ordinary mode checks;
  CT-04 requires all declared focused maintained replays and ordinary mode checks.
  A current ordinary build is additionally required for CT-01–CT-04. CT-04's actual
  compiled entry points and exclusion of replaced translated entry points are an
  integration prerequisite, never a substitute for those runtime reports.
- Runtime dependencies: symbols from the actual ordinary assembly listing identify
  native serve/contact, ball/launch, movement and AI integration and remaining
  score/lifecycle, presentation and audio adapters. Filename/module hashes do not
  prove migration. Symbols only describe compiled integration.
- Delivery: exact configured PAL A500/68000/OCS/512 KB chip/no expansion/Kickstart
  1.3 target and current ordinary mode execution. Peak RAM, uninterrupted ordinary
  cadence/play, cold ADF and independent target validation remain unverified.
  Executable file size is not RAM usage. No overall percentage is computed.

CT-05–CT-10 retain named existing evidence pointers but remain unverified in this
integration. Their direct native/continuous/delivery acceptance has not been
implemented here. Do not change that mapping merely to promote diagnostic rows.

## Transactions and provenance

`build_native_game.py`, `run_regression_tests.py`, `run_mode_selection_tests.py`,
`run_physical_input_tests.py` and `run_amiga_live_serve_probe.py` replace their latest
report with an incomplete invocation before fallible setup/build/run work. Results
are finalized with fsync and an atomic same-directory replace. Exceptions record
failed/interrupted attempts; a killed process leaves incomplete state. The inner
runner's ordinary JSON write can briefly lack provenance; it is then unverified,
never an accepted older pass. Parallel builds/mutations are unsupported.

Evidence schema 1 records run ID/timestamps, runner/command, subject/start kind,
required RUST_LOG=info, machine profile, executable, and checksums for local Python
import/generator closure, assembly/include sources, actual compiled incbin assets
and listing, original recipes/reference data/media, config/ROM inputs and tools.
Tool versions and the published Copperline wrapper's actual executable payload
are included. Media decoder modules loaded by the runner are fingerprinted.
Missing/changed dependencies invalidate the pass. Build module_hashes are retained
for regression compatibility, but are not the freshness dependency closure.
Replay fixture materialization is case-owned so another replay does not overwrite
its input provenance. Case-specific reference dependencies avoid a blanket hash
of all reference data. Source/import closure is deliberately conservative.

Original mode media can use the existing documented local restored-reference
fallback. The chosen media and recipe are hashed; an optional original reference's
absence is recorded and its later appearance invalidates that fallback evidence.
An absent required dependency is always stale. Raw logs and relevant captured
outputs are dependencies too. Private checksums/manifests/reports stay ignored;
ROMs, extracted assets and captures are never published by this command.

## Status and acceptance limits

Statuses are passed, failed, interrupted (including incomplete latest invocation),
not run, and stale. Missing schema/target/tool/input provenance is stale/unverified.
Compatible unchanged evidence is reused unless its start timestamp is at or after
`--fresh-since`, when it is fresh. Freshness is distinct from pass/fail. A pass with
an observed mismatch or inconsistent matched extent is rejected. Subject mismatch,
missing maintained dispatcher entry point, or partial replay cannot establish full
maintained acceptance. The aggregate reads the latest saved report, not a retained
caller body; deliberate known-red prefixes are labelled diagnostic-prefix evidence.
Unwrapped legacy runners remain unverified by this command.

This is local dependency integrity, not cryptographic attestation or protection
against fabricated reports. It does not independently rerun comparisons, certify
host/emulator correctness or measure unimplemented delivery requirements. Review
source changes and corroborate runtime reports independently before merging.

## Focused validation

`RUST_LOG=info python -m unittest discover -s tests/unit -v` exercises relevant
changed/missing inputs, missing/legacy reports, interrupted/failed reruns replacing
passes, compatible reused/fresh evidence, subject/extent disagreement, aggregate
retained-body rejection, target disagreement and optional reference appearance.
Real runner integration commands and exact results are recorded in WORKLOG.md;
raw reports/logs and the generated progress output remain under ignored build/.
