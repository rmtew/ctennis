# Tutorial responsiveness work

Placement from the latest player position takes priority over trails. Physical
input remains sampled every callback. Movement supersedes the old prediction and
idle refinement; an old endpoint must never appear to describe the new position.
While pending, show the latest player position and an explicit pending state.
Only the actual shared simulation may establish the next landing/contact result.

## Measured starting point

The independently reviewed PAL capture at product `21542bc7` (campaign
`d7ae21e91a354e4993936730bf46dc5a`) took 20.400 guest seconds from request
until complete background publication. The observer polls at 0.2 guest-second
intervals. This measures calculation **and presentation**, not calculation alone
or the 40-second capture timeout. Nominal A500 guest time is distinct from the
instrumented campaign's 201.838 seconds of wall time, including build and boot.
This is emulator evidence, not a physical A500 measurement.

| Phase | Observed guest span | Useful work |
| --- | ---: | --- |
| Physics opportunities | 9.128 s | 320 admitted calls in 549 opportunities; 1,278 logical operations |
| Final background path raster | 8.094 s | 486 callbacks, one segment per callback |
| Final court copy | 0.701 s | 43 callback opportunities |
| Final ghost | 0.651 s | 40 callback opportunities |

An F variant change took about 10 seconds despite doing no new physics. It copied
the court and redrew both unchanged paths; path drawing alone used 502–527
callbacks (8.36–8.78 seconds). The released serve stayed in actual human wait
phase `$40`, with zero launch, for its full 256-sample horizon. Its LIMIT result
remains incomplete; the waiting label does not invent an outgoing shot.

During the initial physics phase, median complete callback work was 24,488 CCK
and median remaining headroom 34,247.718 CCK; minimum headroom was 13,048.869.
During final path drawing, those medians were 9,794.5 and 48,939.334 CCK;
minimum headroom was 47,281.651. These finite measurements identify unused
capacity; they are not universal timing bounds.

The line walker already uses integer Bresenham additions, comparisons and shifts.
Its inner loop has no multiplication or division. One segment per callback,
including stationary samples, and a universal 10,000 E-clock admission reserve
are the demonstrated scheduling bottlenecks. Lower drawing precision alone
cannot establish the endpoint sooner: that still needs sequential simulation.

## Delivery and validation

- [x] Give latest-position simulation/publication priority and retire superseded results.
- [x] Separate placement, waiting and animation readiness; trails remain disabled.
- [x] Keep dense actual ball/shadow samples on the native sprite renderer at game time.
- [x] Repeat bounded menu construction units with fresh admission after each unit.
- [x] Check complete state, history/backup, input edges, publication ownership,
  fresh held edits, Resume latest and complete PAL/NTSC callback deadlines.
- [x] Measure finite fresh-result latency and record resource costs and limits.
- [ ] Complete user appearance review and the full native acceptance gate before merge.
- [ ] Resolve retained-shot navigation/branch integration after this baseline review.

Optional trajectory refinement is deferred. Moving sprite echoes and static sprite
trail fragments are independent opt-in design milestones in
[the roadmap](tutorial-mode-design.md); each requires Richard's explicit future
go-ahead before implementation. They do not gate placement or baseline usability.
Root owns integration and the sole native controller. Independent review clears
exact source before execution and original completed evidence afterward.

## Current responsiveness baseline

Product `3d755826cc70536d92a9b33dca382df0b4d60a40` preserves the court,
scoreboards, palette, sprites, shared physics and three-choice menu. Latest player
poses publish without copying the court; old ball/shadow samples are hidden until
the current generation provides an actual result. A nominal callback cursor fixes
playback drift. Menu copy/text units repeat while fresh remaining time admits
work, using a 5,000 E-clock finishing reserve; optional ghost/path work retains
10,000. Caption raster remains separately admitted. These reserves have finite
complete-callback evidence, not universal worst-case certification.

| Focused evidence | PAL | NTSC |
| --- | ---: | ---: |
| Physical movement to changed player publication | 26.931 ms | 30.096 ms |
| Fresh held position edit to actual endpoint publication | 1.068426 s | 1.023953 s |
| Held choice to already computed endpoint publication | 19.156 ms | 17.787 ms |
| Complete callbacks checked | 906 | 874 |
| Minimum absolute callback headroom | 3,657.137 CCK | 4,117.006 CCK |
| Maximum complete callback work | 54,849 CCK | 54,946 CCK |
| Missed presentation deadlines / dropped notifications | 0 / 0 | 0 / 0 |
| Initialized free chip / largest free block | 70,096 / 69,512 B | 79,056 / 78,472 B |
| Observed stack extent | 320 B | 320 B |

Both menu views became ready at the next 0.2-second observation, versus the
previous PAL 8.8/7.0-second delays. This is a polling bound, not a precise menu
scanout latency. Placement latencies above use physical controls and actual native
scene publication strobes, not exact pixel scanout timestamps. Full native sprite
RAM/header/sample checks establish published content; stable PNGs establish
background appearance. The fresh held metric binds generation and variant to the
held edit interval, preventing a later choice of an existing result from satisfying it.
Dense playback advanced 60/30 nominal ticks, with PAL aggregate drift
0.315/0.150 ms and NTSC 10.849/5.425 ms, within the target-derived field-plus-tick
bounds. Endpoint samples hold without wrapping.

A practical baseline is movement publication around 30 ms and a fresh current
serve endpoint around 1.1 seconds for this finite workload. A sub-second fresh
result remains an unproved goal. Retained returns and other workloads need their
own measurements; these values are emulator guest time, not physical A500 proof.

Fresh campaigns: PAL `8217599dd1bc4c6ba478f75d147435f1`, NTSC
`f6aad388f6a34958ba31f47564cb915f`. Both consume executable SHA256
`7c6a89d70efa2689c78767f56febbd9dea2b66f33e552e447ff83af2353ae849`.
Original reports/media remain under `build/tests/tutorial-court-{pal,ntsc}/`;
campaign manifests remain under `build/acceptance/campaigns/<id>/`. Each capture
checks full 318-byte canonical, 72-byte history and 318-byte live backup boundaries,
actual queued/published banks, native sprites, frozen live state and resume edges.
The shared core is unchanged (18,020 normalized bytes, 257 relocations, 14 sink
branches, SHA256 `9a457929bc223b843132bb53af7d604ed574441e32c4651eb69897aa0b48689d`).
Independent exact-source and completed-evidence review passed for both finite
extents, with no measured-scope blockers. PAL receipt SHA256
`d0b4f64be3f59e87f12e3a21c385ddbb17ae1dac3663a575f34bf44476002ac6`;
NTSC receipt SHA256
`4982c7290abfb9cca42b5327bd3498a78ee5bbc36b88cead082521955a7f88d7`.
The composed menu workloads cover 46/47 callbacks, peak 43,633/43,574 CCK
and minimum headroom 14,866.456/15,519.454 CCK (PAL/NTSC). These include
input, IRQ and tail; they are not isolated unit bounds.

Current development executable: 207,268 bytes; loaded code 56,784, data 112,700,
BSS 145,420, total loaded payload 314,904 bytes. Presentation fields add 38 declared
bytes and 40 layout bytes versus `8e66edc`. The tracked resource report was
regenerated with `native_metrics.py --require-runtime --record`; its expected
exit 1 records incomplete standard runtime-profile coverage. Focused tutorial
measurements above do not fill that coverage or establish full acceptance.
`native_metrics.py --check` also exits 1 because accepted metrics are incomplete;
no green standard resource-report check is claimed.

## First repair

Product `44d9c86` batches at most eight segment/header attempts under one shared
32-pixel quota. Its fresh selective PAL campaign
`6982ce508ce741afab62e651d81df269` passed: 2,507 complete callbacks, zero drops,
minimum absolute headroom 3,594.137 CCK. Cold complete-view latency fell to
13.400 seconds; warm variant changes took 2.200–3.000 seconds. These remain
complete-view measurements, not separate placement readiness or full acceptance.
Independent completed-evidence review passed for that finite extent.

A read-only reconstruction of the original `21542bc7` literal RPC matched each
worker JSR stack write to the caller's progress write. Across 640 calls, observed
cost was at most 20,834 CCK, median 15,981, total 10,225,192. This includes return
and caller bookkeeping but excludes admission and subsequent footer/publication.
It covers two current-serve previews, not arbitrary retained-shot resolution.
The independent reviewer reproduced every matched call and cleared the completed
batching evidence, including full state, publication, line and raster contracts.

The next reviewed source increment rechecks remaining time after every public
worker return, with at most four calls per callback. It retains the original
10,000 E-clock reserve for budget four and proposes budget two at 7,000 E-clock
ticks. The prior actual-CPU budget-two proof's finite peak is 54,884 CPU cycles;
the added native IRQ/tail margin is an estimate pending fresh native validation.
READY result/footer processing has its own original-reserve admission on the
following callback. The public core budget and canonical restore contract do
not change. This does not yet certify lower-reserve retained-return execution.

## Display recommendation

Use the existing static four-plane court and native sprite publication for the
first placement/animation proof, with trails disabled. This skips the 24,576-byte
copy and bitmap ghost/path work on each edit. Keep the shared three Copper/sprite
banks and immutable displayed/queued ownership; frozen scoreboard strips already
exist, and the prepared-sprite path does not redraw them. Removing the scoreboard
would change appearance and Copper layout without removing the measured main
cost. Native ball/shadow samples remain dense and advance at game time.

| Option | Chip storage calculation | CPU/DMA/appearance consequence |
| --- | --- | --- |
| Static court + native sprites | No additional canvas beyond current assets | Best first proof: publish current player/result without background copy; preserve existing four-plane palette and sprite path. |
| Current optional full-color trails | Two 24,576-byte private canvases = 49,152 bytes | Reuse reviewed ownership; rebuild only during idle refinement. Measured complete copy-phase callback maximum 30,406 CCK and path-phase maximum 26,450 CCK at `44d9c86`, including input/tail, not isolated worker cost. |
| Separate single-plane trail buffers | Two 6,144-byte planes = 12,288 bytes | A software-composited mask still needs backing/restore work. A fifth displayed single-playfield plane uses color indices16–31, overlapping native sprite colors; it is not a transparent overlay preserving the existing palette. |
| Dual playfield | Two one-plane trail buffers = 12,288 bytes, plus any court conversion/unused-plane storage | Can give hardware transparency and independent trail buffers, but each playfield is limited to three bitplanes. The retained court uses11 color indices, so it needs a reviewed palette conversion. Additional fetched planes change DMA/CPU contention and sprite priorities. |
| Tutorial-only reduced-color display | Depends on agreed replacement court and buffers | Could reduce DMA/storage and remove fixed HUD restores, but changes user-visible colors/layout. Evaluate only if the simple sprite proof fails measured needs. |

The storage rows are byte arithmetic at the current 256×192 court, not measured
allocations for unimplemented alternatives. Current initialized free chip RAM at
`8e66edc` is 71,632 bytes with both private canvases present. The original court
assets use indices0,2,3,4,5,6,9,10,13,14,15 (49,152 decoded pixels audited directly).
Existing Copper registers select four planes (`BPLCON0=$4200`) and put sprite
pair colors in registers17–31. Hardware dual-playfield bitplane/color restrictions
and higher-depth DMA contention follow the original
[Hardware Reference Manual](https://amigadev.elowar.com/read/ADCD_2.1/Hardware_Manual_guide/node0078.html),
its [color-register table](https://amigadev.elowar.com/read/ADCD_2.1/Hardware_Manual_guide/node007A.html)
and [DMA discussion](https://amigadev.elowar.com/read/ADCD_2.1/Hardware_Manual_guide/node012B.html).
No alternative architecture has an execution-time measurement or acceptance
claim. A broad native campaign is unnecessary for this comparison.

Idle rendering should repeat bounded work units while fresh remaining time
admits them, with a finishing reserve including IRQ/DMA and publication. Pixel
and header quotas bound each unit, not the total work allowed per callback.
Input/latest-position simulation and current placement publication take priority;
trail completion is never a usability/READY prerequisite. Record placement,
animation and trail times separately. A sub-second latest-placement target is a
candidate goal, not a demonstrated result; first-result measurements determine
the actual achievable target before further architecture changes.

## Remaining landing latency: read-only investigation

The final captures were inspected without rerunning the emulator. For the fresh
held edit (generation 10, variant 0), take callback entries from its accepted
request timestamp through its actual endpoint publication timestamp. PAL covers
64 entries, with entry progress moving 0→254 logical operations; NTSC covers 61,
0→256. These are entry observations, not exact total worker-cost accounting.
The respective maximum complete callback work is 36,912/37,181 CCK and minimum
absolute headroom 21,677.107/21,889.183 CCK within this interval. Most entries
advance four operations. This is a finite fresh-serve interval, not the global
maximum callback workload reported above.

Source inspection explains the work shape: synthetic continuation executes
round poll, logical pad sample, result sample and actual dispatch as four ordered
operations per simulated tick. `game_preview_step` accepts budgets 1..4 and
restores selected state/history at every public yield. The controller permits
up to four public calls, but a fresh remaining-time check requires 10,000 E-clock
ticks for budget 4 or7,000 for budget 2. The observed unused complete-callback
headroom is therefore not evidence that the four-call cap is the bottleneck.
Copy/guard/restore and native IRQ/tail costs remain part of admission safety.
The held endpoint is published as soon as its actual outcome qualifies; it does
not wait for the released 256-point waiting horizon or a bitmap trail.

Next narrow proof, before any scheduling change:

1. Reconstruct actual worker entry/return spans from the preserved literal RPC
   and matching caller writes. Separate public-call overhead, operation classes,
   caption/publication work and declined admissions; retain actual timestamps.
2. Compare hot current-serve execution with retained context resolution and
   fresh input/transition maxima. Existing budget 2 CPU proof is useful evidence,
   but cannot certify native contention or every retained-return path.
3. Propose a class-specific admission change only after bounding the complete
   finishing tail. Keep public budgets 1..4, full 318/72 restoration and the exact
   sequential core. Do not skip logical sampling/poll operations, extrapolate an
   endpoint or change RNG call order to achieve a latency target.
4. Review exact source, then run only affected fresh PAL/NTSC cases with full
   callback accounting and fresh-generation endpoint timing. Preserve these
   completed baseline captures and report the new product separately.

A reduced reserve or larger internal batch remains a hypothesis, not an approved
implementation or measured speedup. Navigation/catalog jobs need separate
admission accounting and must not share an unbounded callback with previews.
See [the retained navigation/branch queue](tutorial-retained-branch.md).

Independent read-only review reproduced the interval counts/progress/headroom
figures and checked the source operation order. No additional emulator execution
or baseline rerun was performed for this investigation.
