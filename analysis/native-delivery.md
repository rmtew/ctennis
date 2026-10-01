# Private native A500 delivery

CT10 targets PAL A500 / 68000 / OCS / 512 KB chip / zero slow, fast or Z3 RAM /
Kickstart 1.3 (34.5). No attract mode or tutorial is part of this item.

The ordinary product shares subsystem-owned named state in `amiga/game/state.i`
and the native frame order in `integration.s`: display events, logical input,
scoring, players/ball/movement, scene animation, wrapping primary clock,
six saturating clocks, audio and presentation service. It embeds no source
address space or whole cartridge and uses no generated register/flag routines.
Only diagnostic builds import captured initial conditions and serialize actual
native outcomes to the established source-byte contract. The four existing
arithmetic scratch omissions remain unchanged; raw diagnostics remain separate.

DOS entry records its incoming SP, calls Exec Forbid/Disable on that DOS stack,
then uses an explicitly allocated 4 KB application stack for this nonreturning
hardware owner. The ordinary executable never calls Copperline's `$f0ff60`
debug trap; debug logging requires the explicit `COPPERLINE_LOG` define.

## Prepare and build

Configure legitimate private inputs and previously verified reference captures
as described by `config.example.ini` and setup instructions. Keep all originals,
extracted assets and generated delivery output ignored/private. This ADF contains
original-derived assets and is not a public redistribution artifact.

Pin vasm1.9d (68000 backend2.6a, motorola3.17a, hunk2.14c), Python and Pillow as
recorded by the local evidence manifest. Install the packaging library locally:

```sh
python -m pip install --target .tools/python amitools==0.8.1
RUST_LOG=info python scripts/prepare_native_assets.py
RUST_LOG=info python scripts/build_native_game.py
RUST_LOG=info python scripts/build_native_adf.py --self-test
```

Asset preparation is an explicit offline conversion of the legitimate local
cartridge and verified original captures. It does not run translation or an
emulator. After preparation the ordinary native assembly/packaging steps do not
require that cartridge, translation output, emulator or local input config.
Diagnostic phase builds and reference checks remain separate and require their
original inputs. The assembler uses `-Fhunkexe -kick1hunks -m68000`.

Outputs: ignored `build/amiga/gameplay-integration/gameplay-integration` and
`build/amiga/ctennis-delivery/ctennis.adf`. The OFS DD disk has `S/startup-sequence`
containing `ctennis`, and the amitools `boot1x` boot block. Filesystem timestamps
are fixed through the filesystem API (amitools0.8.1's CLI `time` command has a
success-return bug). `--self-test` builds twice from clean disks and requires
byte-identical executable and ADF hashes. Reports atomically record latest
run-start/completion, actual sources/assets, tools, executable and disk hashes.

## Observe actual delivery

```sh
RUST_LOG=info python scripts/run_ordinary_round_tests.py --mode=one --match --cadence --adf
RUST_LOG=info python scripts/run_ordinary_round_tests.py --mode=one --match --cadence
RUST_LOG=info python scripts/run_ordinary_round_tests.py --mode=two --match --cadence
RUST_LOG=info python scripts/progress.py
```

The disk command starts at machine reset with only Kickstart and read-only DF0
at real floppy speed100. It does not use host `--run`. DOS loads the disk's
executable; all actual loaded hunk bytes are compared after relocation against
the maintained build. Thereafter the existing full ordinary lifecycle check
uses physical inputs and nonstopping bus observations, actual Copper-bank
association and native timer entropy. Source captured-phase replays are not
substituted for this ordinary path. WAV, input record, milestone captures,
raw events and measurement JSON remain private and provenance-bound.

Boot free-list samples are retained lower-bound observations. A cold calibration
locates actual Exec pool headers; a second cold reset continuously observes their
initialization and every free-count update through DOS entry and restarted flight.
The scoped allocation peak begins at the initialized Exec chip pool; pre-pool
bootstrap transient usage stays unmeasured. No executable-size-as-RAM claim.
Copperline is the user-approved sufficient validation target (2026-10-01 20:00 UTC). Independent exact-head code/runtime review remains required; other emulator/real-hardware validation was not performed.
The complete registered delivery aggregate keeps translator diagnostics,
known-red prefixes, stale/error rows and unresolved coverage distinct; its case
counts do not certify product behaviours or full original equivalence.

## Current local delivery evidence

The final native executable SHA256 is
`be7e6cdcc4e07201a1c6dca705ffb52eb5911070cdfc31070f82aff100219bfa`;
the private ADF SHA256 is
`6ca21da17f70bafedb48805879ad419ba5932078f19060febf13f57406562f9d`.
Two clean package builds were identical. Read-only cold DF0 completed 11,890
native updates and 9,766 checked Copper publications through match and physical
restart. Actual relocated loaded bytes matched the executable, with no observed
deadline, visible-line publication or event drop. Peak occupied chip allocation
was 237,088 bytes from initialized Exec pools onward (233,464 during play);
pre-pool bootstrap transient usage is unmeasured. Final recorded-entropy
maintained replays matched 13,378 and 27,037 complete updates under the existing
250-byte semantic contract, keeping the four legacy scratch bytes separate.

The previous cold run failed at callback 5,101 when a Copper write reached line44.
Publication now leaves one full line for the register writes; the unchanged
assertion passes. Failed raw events and the original receipt are retained in
ignored `build/ct10/failed-visible-line44`. Linker symbol metadata is explicitly
parsed rather than mistaken for loaded data; wrong loaded bytes and unsupported
hunk blocks remain errors.

The one complete 99-case aggregate is **not passed**: 43 green, 25 tool errors,
15 unexpected red, 11 known-red prefixes, four unexpected green and one stale.
Focused fixes address the stale physical observer and actual first two-player
mode-label preparation. Missing historical phase references, obsolete diagnostic
bridge wrappers, unrelated baseline promotions and coverage backlog remain
separate from maintained runtime evidence. No broad oracle recapture, automatic
rebaselining or second aggregate was performed. Current focused receipts and
provenance determine acceptance, not that retained aggregate's counts.

Local Copperline disk audio also includes synthesized floppy-drive sound; WAV
existence or nonzero samples alone cannot certify native Paula output. Ordinary
audio checks and actual Paula registers are distinct evidence. The installed
MAME driver list has no `a500`, and fs-uae/amiberry are absent. These tools remain unavailable, but the user-approved Copperline scope no longer
requires them. Final accepted-target receipts and exact-head review still govern
CT10 completion.
See the latest WORKLOG entry and ignored `build/ct10` reports for final guard status.

Final focused direct runs complete 11,891/23,836 native-entropy callbacks and
9,765/19,717 checked publications, with 267,208 occupied chip bytes from timer
start onward in both modes. Serve mutation/restoration, round/result compiled
faults, four input timing edges, all thirteen physical windows plus ownership,
both mode selections, delayed bank fault and emitted mute/disconnect pass.
Ordinary physical result/title/restart additionally verifies returned-title
Paula volumes/emitted samples are zero and restart-intro signal is present on
both channels. These debug audio observations remain distinct from uninterrupted
cadence. All 40 unit checks pass. The current progress command reports local
delivery evidence and requires current accepted-target receipts and independent exact-head review.

Review follow-up: phase-only build now explicitly defines COPPERLINE_LOG, as
does the long-game diagnostic assembler command. Live integration, live serve
and long-game diagnostic probes pass; this fixes a genuine new omission, not
a historical diagnostic error. Ordinary assembly defines neither flag and the
executable/ADF hashes above remain unchanged. Common-helper provenance properly
invalidates earlier receipts; they are not edited or silently promoted. Fresh
accepted-target reruns are required after this build-helper change.
