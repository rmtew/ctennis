# Incoming physics scheduling: finite results

The incoming-only extension executes actual projected operation 8 between nominal
callbacks. Selected CPU and controlled PAL/NTSC checks pass; this is an
experimental draft, not a worst-case timing bound, merge or release clearance.
The design and complete admitted partition are in
[tutorial-physics-background.md](tutorial-physics-background.md).

The shared core is unchanged: 17, 606 normalized code/table bytes, 7 relocations,
14 verified sink branches, normalized SHA 256
`99c 543c 170c 036137be 81d 07ebd 30b 522ef 3abdff 04bd 7b 1af 38f 00047bb 99d 5`.
Standalone SHA 256:
`dc 23694209c 12e 6ed 5b 76ece 946256241c 2fae 00b 859d 81dbd 457a 8bbcd 756f 4`.
Candidate/control development products have equal 212, 748-byte length and differ
only at file byte 39, 995, the read-only admission switch:

- Candidate: `8cddde 2db 3a 9de 7af 7644b 05eb 451bd 28a 16ec 5f 6949b 766489bb 9c 5afa 6ddf 2`.
- Control: `466284bcd 5329357f 41f 43962b 8ac 35cd 79e 940fc 6d 35b 95666828f 15c 36936b`.

Control includes the same new classifier/layout and disables physics admission;
it isolates the scheduling decision, rather than reproducing PR 45's exact bytes.
Product source is `f 1a 9d 543b 2b 36a 907a 595b 6b 76cd 860b 43033e 88`.

## CPU completeness and candidate selection

Four natural contact/miss pairs at both ends compare 2, 256 public yields. Forty
once-declared full-origin RNG/geometry/placement cases add 19, 632 yields: 16 byte
RNG values at each end, five boundary cases and three placements. All 21, 888
observations agree in complete private 318 states, ordered events, paths,
outcomes, launches and cursors. Different register/stack working-state poison
is used. The classifier changes no loaded memory, and every public worker
preserves the full image outside preview storage, including canonical state,
history, cache and live output. All 4, 560 admitted operation 8 witnesses execute
one projected dispatch, at most one derive/root and no original dispatcher,
endpoint query or visibility scan. Maximum admitted full worker cost is 26, 130
CPU cycles; classifier maximum is 2, 336 cycles. These are CPU-only observations,
not complete native owner bounds.

Fifty-four classifier-only fixtures challenge serve phases/clocks, court limits,
role/side/stage mismatch, capacities and released count 8/9/10 against held 10.
Released 9 is refused because its append would permit a geometry scan; both
neighbors are accepted. The receipt validator requires the selected domain
identities and per-operation witnesses. Declared fixtures are initialized once
before their tested API, not inserted into a running simulation.

Forward placement produces an actual net return; wide/near placements produce
actual landing returns. Declared incoming net, outside and out-bounce cases miss;
a declared contact/outgoing case returns out. These cover direction/contact and
termination transitions, not every possible short/long shot. Natural upper-end
contact is CPU evidence; the physical tutorial trials use the lower end.

The outgoing candidate was characterized without moving it: 114/70 observed
outgoing full API workers at lower/upper ends, maxima 5, 164/4, 394 CPU cycles.
Terminal tails can finish variants and scan up to 513 geometry points when counts
match. Separate ad hoc incoming equal-geometry workers reached 30, 126/33, 896
cycles; the new admission partition excludes that scan. Outgoing continuation
and endpoint queries remain nominal. The first useful extension is therefore
incoming dispatches with explicit costly-tail exclusions.

## Controlled native evidence

Each region pair uses the same built source, recorded seed/origin, frozen 318
state, history records/end, guided key/held sequence and endpoint placements.
All three selected outcomes have identical complete incoming, launch and terminal
states. Initial physical request positions match. Later alignment/edit times
start after each independently observed outcome, so their absolute input
timelines differ. Computational pairing is verified; these guided trials do not
establish universal speedup or identical absolute keystroke schedules.

| Finite native observation | PAL control | PAL candidate | NTSC control | NTSC candidate |
|---|---:|---:|---:|---:|
| Completed callbacks |595|596|586|592|
| Accepted background owners |257|283|355|451|
| Accepted operation 8 owners |0|8|0|33|
| Maximum operation 8 whole owner, CCK |—|8, 112|—|8, 140|
| Maximum cheap whole owner, CCK |3, 704|3, 628|3, 601|3, 692|
| Declined owners |24, 189|23, 804|22, 262|22, 050|
| Maximum declined owner, CCK |1, 618|1, 832|1, 630|2, 029|
| Maximum complete callback, CCK |54, 877|54, 877|55, 572|55, 572|
| Maximum entry lateness, CCK |1, 750.394|1, 750.394|1, 332.745|1, 332.745|
| Minimum absolute callback headroom, CCK |3, 405.137|3, 405.137|3, 249.006|3, 249.006|
| Maximum exact root service including IRQ, CCK |1, 453|1, 489|1, 467|1, 464|
| Complete exact root service sequences |25, 042|24, 684|23, 204|23, 094|
| Peak observed stack, bytes |320|320|324|324|
| Maximum input-to-matrix, CCK |38, 256|37, 752|30, 080|30, 776|
| Maximum keyboard poll gap, CCK |41, 255|41, 255|41, 779|41, 779|
| Maximum ACK hold, CCK |4, 220|4, 235|24, 365|24, 365|
| Chip free/largest block, bytes |60, 712/60, 128|60, 712/60, 128|69, 672/69, 088|69, 672/69, 088|

Every accepted whole owner completes between callbacks and has one operation
write/body. Spans include classifier/admission, public worker, owner release and
progress tail. The exact four-PC root-service reduction includes IRQ interruptions.
Finite oversized-owner measurement-record negative controls are rejected;
these are offline detector challenges, not native fault injection.

Physical controls exercise misses, accepted returns, repeated edits, early
endpoint publication, normal sprite banks/COPJMP, outgoing playback/repeat/dwell,
active-job menu cancellation and exact live resume. Complete canonical/history/
backup/cache and retained record guards, original incoming/outgoing references,
held resume without fresh edges and finite input/ACK checks pass.

| Physical gesture to outcome COPJMP, seconds | PAL control | PAL candidate | NTSC control | NTSC candidate |
|---|---:|---:|---:|---:|
| Initial held outcome |0.707186|0.687153|0.623792|0.623791|
| Guided alignment |3.102100|3.162207|3.106202|3.206507|
| Fresh D edit |0.652981|0.603029|0.537593|0.521200|

The initial PAL outcome improves by about 20ms and fresh edits by 50ms PAL/16ms
NTSC; alignment is about 60ms/100ms slower. Benefits are mixed. Background
classification/admission overhead grows, and time outside the measured preview APIs
still dominates these selected paths.

The comparison receipt records the last actual public request→accepted contact→
marker and the union of observed preview-step/endpoint API spans. Time outside
those APIs includes nominal waiting, input, presenter, rendering and other work;
it is not a measurement of idle CPU time. Gesture-based contact fields from the
native observer remain separately labelled. See the private comparison receipt
for exact CCK breakdowns and source/product binding.

## Falsified allowance, resources and holds

The first PAL control trial, with physics disabled, falsified the previous entry
hypothesis: 1, 750.394 CCK exceeds 1, 750. Its archive is
`/tmp/ctennis-physics-failures/07083b 9c 33b 84bb 39bf 899adf 366c 505-control-pal-000001`;
raw capture SHA 256:
`f 818da 957939b 5fde 97bc 81d 4619e 816ce 6130973e 16c 75fd 560de 7ca 42c 6171`.
An intermediate proposal to reduce unresolved completion uncertainty was rejected
in timing review. Policy 5 retains 1, 250 completion uncertainty, uses 2, 000 entry
and 55, 750 callback, preserving the exact 59, 000 combined gate. The observed NTSC
callback leaves only 178 CCK against that component hypothesis. Failure and
invalidated/interrupted CPU attempts remain in the campaign; none counts as a pass.

Neither region witnessed a background accepted-contact/root owner. Native contact
dispatches ran nominally, maxima 11, 250/11, 272 CCK in the candidate. CPU contact
proofs and the one-root source partition support the experiment, but they do not
close the 20, 000 CCK full background contact-owner hypothesis. This gap, independent
admission arithmetic, coherent-read/IRQ/DMA/entry-return bounds, approved ACK/input
limits, all-workload fairness and producer/publication budgets remain open. The
24, 365 CCK ACK outlier occurs in both NTSC runs. No WCET, normative G 2/S 05/S 18,
universal input/no-drop, WinUAE or physical-hardware claim follows.

Loaded code 60, 396/data 112, 700/BSS 151, 192/payload 324, 288 bytes; development 212, 748.
Relative to PR 45:code/payload +332, data/BSS +0, development +392. The new switch
word resides in code; mutable RAM, canonical 318, history 80, 318, metadata 72 and
incoming cache 344 are unchanged. Chip pool figures include the OS and stack.
Full resources, cold stripped release, appearance and mandatory acceptance remain
incomplete; both tracked resource reports are regenerated with that status.

Correctness and timing reviewers independently verified raw equality and native
spans/inputs/pairing, and clear bounded experimental draft publication only.
The integrator owns implementation integration; the parent coordinates reviewers.
First follow-up proof: obtain naturally phased admitted-contact owner witnesses in
both regions, then justify full admission/transport bounds before considering
merge. Approving those bounds and mixed-benefit tradeoffs requires review; this
work does not silently approve them or merge any draft.


## Reproduction and receipt status

Selected campaign `07083b9c33b84bb39bf899adf366c505` completes five of five
selected cases. It explicitly reports `full_native_catalog_covered=false` and
`acceptance_passed=false`. The final CPU attempt is `000006`; four native cases
reuse compatible finalized captures, with dependency/product checks, rather
than claiming another fresh execution. Their fresh attempts are PAL control
`000002`, PAL candidate `000001`, NTSC control `000001` and NTSC candidate `000001`.

The final CPU report at `build/tests/physics-cpu/report.json` has SHA256
`83cec56ea7e834a8fe0a500cc718735cd2edb6aeba338ead85557ff455d0cd2e`.
The offline four-capture comparison at
`build/tests/physics-comparison/report.json` has SHA256
`9e2bf34b5efd1be7391366c7ffbd3717cce25058ab64f624b2a4087e40c2f3b9`.
Raw reports remain private ignored build artifacts; the campaign retains failed,
interrupted and dependency-invalidated attempts. CPU attempts 3 and 5 changed
dependencies during execution and do not count. An unintended default campaign
was stopped during host units before any build or emulator execution.

Commands (Python is `/tmp/ctennis-shared-core-python/bin/python`; `RUST_LOG=info`):

```sh
python scripts/native_acceptance.py --plan --case physics-cpu --case physics-control-pal --case physics-pal --case physics-control-ntsc --case physics-ntsc
python scripts/native_acceptance.py --resume --campaign 07083b9c33b84bb39bf899adf366c505 --start
python -m unittest discover -s tests/unit -q
python scripts/native_metrics.py --require-runtime --record
```

The host command passes 256 tests. Metrics recording exits 1 and writes both
`docs/metrics/current.json` and `current.md` as incomplete, bound to the candidate
product: all eight required runtime profiles are unmeasured and cold release
coverage remains incomplete. No full native gate, appearance campaign, cold
release or physical-hardware trial was run for this increment.
