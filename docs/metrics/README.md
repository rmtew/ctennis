# Resource report workflow

Every native build regenerates ignored `build/metrics/static.json` cheaply from
actual executable hunks, active retained incbins, generated UI pages and the
assembled replay packet table. It never launches an emulator. Size includes
executable symbols/relocations; loaded code/data/BSS excludes that metadata.
Asset byte totals overlap the hunks and are not extra RAM allocations.

The displayed BUILD revision now names the latest commit touching product inputs
(amiga/assets, native generators/tools.lock), with LOCAL only for changes to those
paths. Report, observer and documentation commits no longer change executable
bytes through their version label. Exact executable SHA256 and all compiled input
hashes are the evidence; the display label is not a freshness certificate.

The finite `native_acceptance.py` gate collects metrics during its existing cold
one-player/two-player cadence, UI setup and canonical demo checks, then generates
`build/metrics/current.json` and `.md` with `--require-runtime`. No extra full
campaign is added. A failed check still stops the gate. No optimisation is part
of this change; observers watch native stack bus accesses and existing counters.

After a product change, commit implementation first (as required by the native
gate), run affected validation, then explicitly record the reviewable summary:

```sh
RUST_LOG=info python scripts/native_acceptance.py
python scripts/native_metrics.py --require-runtime --record
```

For this observer-only change, the bounded affected checks are sufficient:

```sh
RUST_LOG=info python scripts/native_metrics.py --refresh --require-runtime --record
```

`--refresh` runs four existing checks, not a new framework or independent oracle.
Individual affected checks can be run directly. `--record` creates no commit,
PR or publication; review and commit `docs/metrics/current.json` and `.md` together.
Deltas use the previous complete report on local `master`, the last accepted
baseline; until a report lands on master, the explicitly preserved latest reviewed snapshot supplies historical deltas. They compare
runtime only when target, tool versions and measurement boundaries agree.

Report-only/docs-only work reuses proven identical products/configuration:

```sh
python scripts/native_metrics.py --check
```

This does not emulate. It checks the built executable/compile manifest, recorded
source/config hashes, ROM and tool hashes, and any latest local receipts. If a
later run exists, including failed/interrupted runs, regenerate the summary;
never fall back to an older passing measurement. Missing files/config/tools
cannot certify reuse. Restore the private tool cache and build before checking
in a new checkout; a docs/report-only build keeps the same displayed revision.
Raw captures need not be retained for reuse; recorded bounded summaries remain
explicitly reused, not fresh runs. Timestamps and report commit hashes are not
identity. Generated report files are excluded from product dependencies.

Default generation writes ignored output; missing/stale/failed case metrics
produce an incomplete summary. `--require-runtime` fails that invocation.
`--record` also replaces a tracked summary with failure/incomplete state if the
requested generation fails, so a failed refresh cannot leave a green report.
The gate receipt remains authoritative for acceptance; resource completion does
not mean a full gate was run.

Profiles are callback-entry title/help, one/two-player ball-in-flight, demo,
physical user pause and match end. Input-transition callbacks are retained and
phase sample counts expose skipped calls. UI construction samples cover actual
redraws; idle title callbacks do not render sprites. The dispatcher measurement
includes its service/logic, not all input sampling. Per-phase elapsed intervals
include emulated contention, with bus-boundary prefix/suffix excluded. They do
not claim a CPU busy/wait split. Simulation-tick deadline headroom includes entry
lateness; work-budget headroom subtracts work alone. PAL display-frame budget is
separate. Nearest-rank p95 and median are descriptive for the recorded finite
scene extent, not a statistical model of all play.

Cold loading starts after measured cold reset of a read-only ADF, at fixed100%
floppy speed. A prior calibration boot only discovers actual Exec header
addresses; it is outside the measured reset-to-input interval. The pinned API
exposes LoadSeg completion/entry, not file-read vs relocation subphases or boot
script start. Those stay null. Assets/control readiness is the actual CIA timer
start after native initialization; successful first normal selection establishes
input responsiveness, including the existing workflow's input-delivery wait.
The first complete displayed title is the second completed frame notification
after a verified title Copper publication, allowing the first to be partial.
The observer requires the actual title Copper pointer, logical title flag and
menu page to remain selected throughout that window; switching away invalidates
the window. Completion requires reset, LoadSeg completion, executable entry,
assets readiness, this scanout proof and successful input milestones. Unsupported
boot-script/LoadSeg-start milestones may remain null. Disk
read/seek counters and host launch time remain unavailable.

RAM is whole initialized machine chip usage including resident OS/stack, with
free/largest block verified against Exec free lists. Cold peak covers observed
free-count mutations from initialized pools; pre-Exec bootstrap remains
unmeasured. Zero other RAM describes the measured unexpanded target. Allocation
failure results are not instrumented and stay null. Celebration is measured in
the current merged product; future feature changes require affected profile
refreshes. Do not inspect another worker's unfinished files.

Input responsiveness may precede full scanout. Milestone differences are signed
offsets; explicit loader/init/display intervals and the total until both input
and a complete title are ready preserve that overlap. Initialized-pool boot RAM
samples are recorded at their actual positions, without extrapolating peaks.

The build's Python import closure also reaches the report writer. A change only
to `scripts/native_metrics.py` may reuse completed native observations if the
exact executable and every observer, product, tool, config and raw artifact
remain hash-identical. The report marks that reuse and binds its current writer
hash separately. An observer edit, missing artifact or later failed receipt
never receives this exception. This prevents report-format fixes from creating
a duplicate emulator campaign.

Report identity binds product, measured extents/statistics, observer/config/ROM/
tool dependencies and the current report writer, excluding generated reports
and timestamps. Product identity remains separate. No executable-size cap is
configured, so executable headroom remains null rather than borrowing the RAM
budget.

`--check` verifies the report's content identity as well as its dependencies, so
changed numeric summaries cannot keep a previous identity. New lifecycle features require their actual native state in `MetricsObserver.profile()`
and a measured availability declaration in `generate()` before refreshing. A
baseline report does not certify a future feature.

UI construction distributions group actual redraws by page: the title row shows
menu-page construction, and help includes controls/credits. This grouping is
independent of callback-entry profiles and can include redraws during pause or
input transitions. Pause-only UI construction is unmeasured; sprite rendering
and dispatcher distributions retain their observed callback-entry profiles.

`--check` also compares the current report-writer SHA256 explicitly. Writer
changes require regeneration, even when the raw observations qualify for reuse.

Static generation now reconciles every executable file byte into exclusive
listing-backed instruction, asset, reserve, table, alignment and hunk metadata
categories. Unknown gaps, overlaps or mismatched embedded assets fail generation.
The hunk CODE label includes embedded data and reserves; it is not an instruction
byte count. Identical asset copies are informational, not validated optimization
savings. See [the measured size attribution](executable-size.md).

Release ADFs remove only HUNK_SYMBOL records from the already-built development
executable. Development builds and listing sidecars retain symbols. Packaging
records both hashes, verifies the embedded release bytes, and preserves loaded
payloads, memory flags and relocations. Cold ADF observers compare actual loaded
bytes against the release executable while resolving symbols from the matching
development listing. Other native checks keep the development executable.
The report binds both products separately. The earlier symbol-rich baseline is
retained in `baselines/development-symbols.json` with its original historical
identity; it does not certify current observer changes.

For cold boot measurement the input harness waits for the continuously selected
initial title scanout proof before pressing its physical mode key. This adds
only an observation wait, not a product change. A scanout window beginning
after initial successful selection is rejected as a returned title, so later
match/title transitions cannot masquerade as the boot milestone.

The reviewed symbol-removal comparison is in
[release-loading-comparison.md](release-loading-comparison.md) and its JSON,
bound to both report/ADF/executable hashes. The historical title scanout point
was checked by bounded offline replay; its proof is retained in
`baselines/title-proof-review.json`. The release run is newly measured; later
report assembly/`--check` conservatively labels receipt reuse. Full native-gate
acceptance is separate from completion of these four affected checks.

Cold menu receipts also bind the packaged release executable (including its
compiled-executable entry and ADF hash); debug executable/listing hashes are
recorded separately. For focused variant validation, use
`RUST_LOG=info python scripts/run_enhanced_menu_tests.py --adf --boot-only`.
Its separate `enhanced-menu-cold-boot-binding/report.json` explicitly excludes
full menu lifecycle acceptance. A failed full menu receipt is not replaced by
this bounded check.

The PR19 integration measures the committed merged product, including the Mac
menu font, classic/robot poses, five UI cache assets and Battle Hymn celebration.
`celebration` means observed result lifecycle with the celebration pose active;
the earlier result entry remains `match-end`. Both profiles retain their actual
sample counts. Celebration is now required when its code is compiled.
The former release report is retained in `baselines/pre-pr19-release.json`; it
does not certify the merged product. Failed menu receipts remain outside Git.
The menu takeover check waits at most twelve actual UI samples for the physical
button2 sample, then requires the same demo exit and frozen-state preservation;
a missing sample or incorrect takeover still fails.

Current merged-product byte attribution is regenerated in executable-size.json
and .md; integration-comparison.json/.md compare the historical stripped product
with the freshly measured merged product. The older release-loading-comparison
is explicitly historical and names its retained baseline report. Native report
deltas require matching observer definitions for runtime statistics; a profile
split cannot silently be compared as the same scene. If master has no metrics
report yet, the preserved reviewed baseline supplies labeled historical static
deltas. `--check` verifies that baseline hash as well as current product inputs.

The frozen PR21/PR22 integration preserves the selected LED masks and title geometry. Point banks occupy startup-generated chip BSS, not embedded file bytes; listing-backed BSS extents are reported separately and reconcile with HUNK_BSS. The previous measured product is preserved in baselines/pre-title-score-current.json/.md and its size snapshot. Refresh all four affected metric collectors plus the full cold menu after this product change.

The focused native LED startup check supplies square-startup.json/.md, bound to its exact development executable and frozen-preview contract. Its emulated constructor interval is an ordinary-startup observation; it does not split the cold-ADF entry-to-ready interval. Current metrics cover frozen master f82780dcf9f4be154d912db0b306598a729afe24. Later help wording/title-ball changes require exact-product validation before reuse or remeasurement; these measurements do not certify those changes.

Direct score/WIN strips replace full variant banks and horizontal per-row switches.
The accepted pre-change report is retained in `baselines/pre-direct-hud-current.json`
and `.md`. `direct-hud-comparison.json`/`.md` bind measured instruction, data/BSS,
relocation and runtime changes; bounded baseline probes add previously unavailable
ISR/handover/dirty-HUD metrics without rerunning the old acceptance campaign.
