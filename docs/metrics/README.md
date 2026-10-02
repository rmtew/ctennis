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
baseline; fetch/update that baseline by the normal review process. They compare
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
after its initial Copper publication, allowing the first to be partial. Disk
read/seek counters and host launch time remain unavailable.

RAM is whole initialized machine chip usage including resident OS/stack, with
free/largest block verified against Exec free lists. Cold peak covers observed
free-count mutations from initialized pools; pre-Exec bootstrap remains
unmeasured. Zero other RAM describes the measured unexpanded target. Allocation
failure results are not instrumented and stay null. Celebration is unavailable
on this baseline: after its independent polish implementation lands, rebuild and
refresh affected profiles. Do not inspect another worker's unfinished files.

Input responsiveness may precede full scanout. Milestone differences are signed
offsets; explicit loader/init/display intervals and the total until both input
and a complete title are ready preserve that overlap. Initialized-pool boot RAM
samples are recorded at their actual positions, without extrapolating peaks.
