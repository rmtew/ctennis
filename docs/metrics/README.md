# Resource report workflow

Every native build regenerates ignored `build/metrics/static.json` from the
executable hunks, listing, retained assets, generated UI caches and replay table.
It does not start an emulator. File size includes symbols and relocations.
Loaded code, data and BSS exclude that metadata. Asset totals overlap the hunks;
they are not additional RAM allocations.

The product label uses the latest commit that touches product inputs. The LOCAL
suffix marks changes to those inputs. Exact executable and input SHA256 values
establish identity; the displayed label alone does not establish freshness.
Documentation under product-input directories can affect that label.

## Commands

The finite acceptance gate collects resource measurements during its existing
cold one-player, two-player, setup and demo checks. Record the reviewed result:

```sh
RUST_LOG=info python scripts/native_acceptance.py
python scripts/native_metrics.py --require-runtime --record
```

For an affected measurement refresh, run:

```sh
RUST_LOG=info python scripts/native_metrics.py --refresh --require-runtime --record
```

`--refresh` runs four existing collectors. It does not replace full acceptance.
Run individual affected checks when their narrower scope is sufficient.
`--record` writes docs/metrics/current.json and .md but makes no commit.
Review both files together.

For documentation-only changes, build the matching product and run:

```sh
python scripts/native_metrics.py --check
```

This check does not emulate. It verifies report content, the report writer,
compiled inputs, tools, configuration, ROM and latest local receipts. Missing
tools or inputs cannot establish reuse. A later failed or interrupted run
supersedes an older pass. Generated reports and timestamps are not product
identity. Report-writer changes require regeneration; unchanged observations
can qualify for explicitly labeled reuse under the existing identity rules.

Default generation writes ignored outputs. Missing, stale or failed case metrics
produce an incomplete summary. `--require-runtime` then fails. With `--record`,
that incomplete state replaces the tracked summary. Never leave an older green
summary in place after a failed refresh. The gate receipt remains authoritative
for acceptance.

## Measurement boundaries

Profiles describe actual callback-entry states: title, help, one-player rally,
two-player rally, demo, pause, match end and celebration. Sample counts show each
profile's extent. Input transitions remain in callback accounting. UI redraw
distributions group menu work under title and Controls/Credits under help.
Pause-only UI construction remains unmeasured.

Elapsed CCK includes emulated bus contention. Dispatcher measurements exclude
some input sampling and bus-boundary tails. They do not separate CPU work from
wait time. Simulation deadline headroom includes entry lateness. Work-budget
headroom subtracts work alone. Display-frame and simulation budgets are separate.
Median and nearest-rank p95 describe finite samples, not all possible play.

Cold loading starts at measured reset with a read-only ADF and 100% floppy speed.
An earlier calibration boot finds Exec header addresses outside that interval.
The API exposes LoadSeg completion and executable entry. File-read, relocation
subphases, boot-script start, disk counters and host launch time remain unavailable.
Assets are ready when the native CIA timer starts.

The first complete title is the second frame notification after verified title
Copper publication. The title pointer, logical flag and menu page must stay
selected throughout that window. Input selection follows this proof. A later
returned title cannot substitute for initial boot. Input and display milestones
remain separate; signed offsets preserve their possible overlap.

RAM means whole initialized-machine chip usage, including OS and stack. Exec
free lists verify free bytes and the largest block. Pre-pool bootstrap use and
allocation failure instrumentation remain unmeasured. Executable bytes are not
whole-machine RAM. No executable-size cap is configured, so its headroom is null.

Release packaging strips only HUNK_SYMBOL records. It preserves loaded bytes,
memory flags and relocations. Cold-ADF observers compare actual loaded bytes
with the release executable and use the matching development listing for symbols.
Both products have separate hashes. For a bounded boot check, run
`RUST_LOG=info python scripts/run_enhanced_menu_tests.py --adf --boot-only`.
That receipt does not replace full menu lifecycle validation.

## Retained evidence

`current.json` and `current.md` describe the recorded product and its limits.
At this cleanup baseline, runtime resource coverage is incomplete. Historical
measurements do not certify the PR #28 startup or PR #29 title changes.

The current delta chain uses `baselines/pre-title-score-current.json`, which in
turn binds `baselines/pre-pr19-release.json`. Keep these exact JSON bytes.
`native_metrics.py` also uses the first file as its historical fallback.

[The direct HUD comparison](direct-hud-comparison.md) and its JSON retain the
measured PR #25 to PR #27 result. Its source baseline is
`baselines/pre-direct-hud-current.json`. [Validation](direct-hud-validation.md)
records that older product's finite gate. Later failed or unmeasured products
must not inherit those passes.

Older integration, symbol-removal and startup summaries remain in Git history.
Their former filenames did not guarantee that they described the current build.
Use regenerated ignored static metrics for current size attribution.
