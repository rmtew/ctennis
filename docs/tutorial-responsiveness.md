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

- [ ] Batch path segments under one aggregate pixel quota and one bounded header
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
