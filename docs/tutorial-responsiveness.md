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

- [x] Batch path segments under one aggregate pixel quota and one bounded header
  quota, including invisible and stationary samples.
- [ ] Measure each work class including callback tail, presentation IRQ and timer
  margin before changing its admission reserve. Keep original deadlines.
- [ ] Give latest-position simulation priority; cancel idle refinement on edits.
- [ ] Separate placement-ready, animation-ready and fully refined-trail times.
- [ ] Publish a truthful actual prefix where useful; do not extrapolate an endpoint.
- [ ] Refine completed trajectories by midpoint subdivision on free private
  backgrounds, erasing previous coarse chords on each pass. Preserve contact,
  flight and visibility changes as mandatory boundaries.
- [ ] Keep ball/shadow on native sprites indexed through dense time samples.
- [ ] Verify complete canonical/history/backup preservation, input edges, actual
  publication ownership, PAL/NTSC deadlines and fresh-input/transition cases.
- [ ] Report fresh first-result latency and derive a concrete interaction target
  from the measured workload; do not claim a target has passed before evidence.

Root owns integration, scheduling changes, the sole native controller and result
reporting. The presentation author supplies isolated source changes; an
independent reviewer clears exact source before execution and checks original
completed evidence afterward. Existing screenshots and PR38's earlier selective
PAL pass describe the starting prototype, not this unfinished repair.

## First repair

Product `44d9c86` batches at most eight segment/header attempts under one shared
32-pixel quota. Its fresh selective PAL campaign
`6982ce508ce741afab62e651d81df269` passed: 2,507 complete callbacks, zero drops,
minimum absolute headroom 3,594.137 CCK. Cold complete-view latency fell to
13.400 seconds; warm variant changes took 2.200–3.000 seconds. These remain
complete-view measurements, not separate placement readiness or full acceptance.
Independent evidence review is pending.

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
