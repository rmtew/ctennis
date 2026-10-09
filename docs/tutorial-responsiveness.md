# Tutorial responsiveness work

The latest approved private-state increment is recorded in
[the integration result](tutorial-private-state-integration.md): fresh PAL/NTSC
endpoint times are 0.552482/0.520228 regional guest seconds, with zero recurring
state-copy calls in each measured fresh prediction interval. Older observations
below retain their original product identities.

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
Dense playback advanced 60/30 nominal ticks. PAL aggregate drift is
0.315/0.150 ms. The original NTSC report mixed provider seconds with regional
nominal seconds; raw-CCK normalization below corrects this to 1.617/0.809 ms
in regional units, still within the field-plus-tick bounds. Endpoint samples
hold without wrapping. Original receipts remain unchanged.

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

### Public worker span reconstruction

Independent read-only reconstruction binds generation 10/variant 0 in the
fresh-held-edit interval to the first actual marker publication, using literal
CCK timestamps rather than converting reported seconds. Call starts are the
native `game_preview_step` BSR/JSR stack stores; ends are the matching caller
progress stores. Every counted call belongs wholly to one selected complete
callback; duplicate, crossing and unmatched calls reject the analysis.

| Exact preserved-product observation | PAL | NTSC |
| --- | ---: | ---: |
| Request→marker raw CCK bounds | 56,164,191→59,953,786 | 55,540,575→59,172,428 |
| Public worker calls | 105 | 69 |
| Enclosing worker span total | 1,282,367 CCK | 1,063,222 CCK |
| Median / maximum enclosing worker span | 12,772 / 18,867 CCK | 16,379 / 21,194 CCK |
| Whole callbacks contained in that raw interval | 64 | 60 |
| Selected complete-callback work | 1,964,306 CCK | 1,679,620 CCK |
| Selected callback complement outside worker spans | 681,939 CCK | 616,398 CCK |
| Sum of observed absolute headroom | 1,791,903 CCK | 1,873,124 CCK |

These worker spans include call return, caller bookkeeping, IRQ and contention;
they are not exclusive simulation-body costs. The callback complement applies
only to those complete contained callbacks, not all work in the request interval.
In particular, the initial request callback is only partially in the interval,
and a publication can occur before its containing callback finishes. The earlier
61-entry NTSC interval included that final callback; the table uses 60 fully
contained callbacks instead. Headroom sums are observations, not budgets that
can simply be transferred to additional work. The four-public-call cap is not
established as the bottleneck. Source thresholds and repeated restore costs
are plausible constraints requiring measured separation.

Nothing here establishes a one-second unavoidable target-hardware lower bound.
A focused separate read/write-stack observation is being prepared to pair actual
call/RTS accesses and split simulation bodies, selection guards and copy/restore
spans. It must measure declined admissions/finishing tails without altering the
actual physics or live state and without overwriting these baseline captures.
Only a separately reviewed admission change and fresh affected-case proof can
establish a speedup. No smaller reserve or larger public API budget is approved
by these measurements alone.

### Corrected NTSC timebase interpretation

The provider's saved `position.seconds` uses a fixed 3,546,895 CCK/s timebase even
in NTSC mode, while the observer's original nominal/tolerance calculation used
3,579,545 CCK/s. The old 10.849/5.425-ms NTSC values therefore include a clock-unit
conversion difference and must not be called pure playback drift. Reconstructing
the same 60/30-tick epochs entirely in raw CCK gives elapsed 3,589,948/1,794,975 and
nominal 3,584,160.333/1,792,080.167 CCK. Drift is 5,787.667/2,894.833 CCK: regional
NTSC conversion 1.617/0.809 ms, or provider conversion 1.632/0.816 ms. Both remain
within the same-unit field-plus-tick allowance, and producer ticks remain 60/30.
No emulator rerun is needed for this arithmetic correction; the original report,
executable, input trace and receipt are preserved. Reported latencies elsewhere
are provider guest seconds unless a regional conversion is explicitly named.
New timing observations must retain raw CCK and label the seconds timebase.

### Completed PAL latency separation

The separate read/write-stack diagnostic used the unchanged product
`3d755826cc70536d92a9b33dca382df0b4d60a40`, executable SHA256
`7c6a89d70efa2689c78767f56febbd9dea2b66f33e552e447ff83af2353ae849`.
Observer source `7a27bb6` measured 235 complete callbacks, zero notification
loss and minimum absolute headroom 3,657.137 CCK. Independent review reconstructed
all literal calls, callbacks, endpoints and 133 frozen 318/72/318 boundaries.
Initial held-shot and fresh-D-edit endpoints took 1.058566 and 1.080232 PAL
seconds. The fresh physical-input window was 31,609,720→35,441,189 CCK.

| Fresh edit, wholly contained measured spans | CCK |
| --- | ---: |
| 89 public preview calls, inclusive | 1,180,598 |
| Actual core-body subtree union, including nested helpers | 473,079 |
| Copy/restore subtree union | 284,600 |
| Exclusive guard/admission category inside workers | 255,594 |
| Exclusive copy/restore category inside workers | 281,258 |
| Exclusive core-body own instructions inside workers | 31,988 |
| Exclusive API own instructions inside workers | 59,077 |
| Exclusive other helpers inside workers | 552,681 |

The five exclusive categories partition public-worker spans exactly. Subtree
unions overlap those categories and must not be added to them. The core-body
subtree took approximately 0.133 PAL seconds; 31,988 CCK is only its own-instruction
category, not the total simulation cost. Stack markers retain IRQ and contention;
instruction tails outside the first call store and last RTS read are not isolated.

Stable literal CIA read bytes and the saved timer globals reconstruct all 154
`tutorial_work_remaining` returns in the fresh window. Of 149 preview-loop
decisions, 38 admitted budget 4, 51 admitted budget 2 and 60 declined. Every
admitted decision has an actual following worker in the same callback; every
decline has none. Declines retained 3,118–6,990 E ticks. Their finishing tails
were 166–563 CCK and final absolute headroom was 15,280.389–34,649.879 CCK.
The existing 7,000-E minimum therefore leaves substantial unused time in this
specific current-serve observation. Maximum observed fresh public-worker span
was 18,583 CCK. These observations support investigating a class-specific
current-serve admission reserve; they do not bound unseen operations or justify
lowering retained-navigation admission globally. Keep the existing public cap,
sequential operations, actual core and complete restore guards. Review a reserve
and its worst-case worker plus finishing tail, then prove affected PAL/NTSC
deadlines and physical-input endpoint timing on the new product before claiming
a speedup. No scheduling or physics change is included in this diagnostic.

Campaign `0144dc18e4d440a6b4a5573e1d73b5e2` remains **incomplete/passedfalse**:
the controller hit ENOSPC in `preserve_artifacts` after the completed child
report. Original report and attempt receipt both have SHA256
`5085ecc066237d0349fe955497c3ce97d6785f1e3165a8379e58a5627542ea72`.
The separate `scripts/validate_preserved_latency.py` binds those originals,
controller failure, all consumed inputs/tools/products and retained artifacts
without running the emulator or changing campaign state. It establishes only
the completed measurement extent. `child.json` contains command identity, not
an independently recorded exit status. The earlier diagnostic parser failure
`d123f2e465f14387890f991bee0d506f` is also retained. Neither diagnostic establishes
full acceptance. NTSC exclusive-body/admission measurement and any improved
runtime remain pending.

### Resolved current-serve scheduling correction

Product `6f28287` applies the measured reserve only when `game_preview_kind==3`
and phase is `PREVIEW_HELD` or `PREVIEW_RELEASED`: budget 4 requires 7,000 E ticks,
budget 2 requires 5,000. Resolution, priming and other kinds retain 10,000/7,000.
Every public yield rechecks remaining time, with the same four-call cap. Physical
sampling and placement keep priority; result preparation and post-worker
animation retain separate 10,000-E checks, and publication retains its 5,000-E
check. Actual sequential core operations, RNG calls and complete restoration
are unchanged. Independent source review preceded the two affected native cases.

Fresh campaign `c758f56a66a74791aa54e23f07f452c0` completed with both selected
cases passing and `acceptance_passed=false`. Both execute native SHA256
`c543a695d9493254eb152cf34a093676c3c0c0dcd4df203d0ad105a5b97e3cb8`.

| Focused unchanged observer measurement | PAL | NTSC |
| --- | ---: | ---: |
| Fresh held edit→actual endpoint, provider seconds | 0.706545 | 0.699653 |
| Previous product, same metric | 1.068426 | 1.023953 |
| Fresh prediction latency reduction | 33.9% | 31.7% |
| Physical movement→actual player publication | 23.703 ms | 41.587 ms |
| Already computed held-choice→endpoint publication | 35.321 ms | 26.833 ms |
| Complete callbacks | 763 | 744 |
| Maximum callback work | 54,879 CCK | 54,940 CCK |
| Minimum absolute deadline headroom | 3,626.137 CCK | 4,116.006 CCK |
| Frozen complete canonical/history/backup boundaries | 589 | 572 |
| Dropped observations | 0 | 0 |
| Stack usage | 320 B | 320 B |
| Initialized chip free / largest free block | 70,040 / 69,456 B | 79,000 / 78,416 B |

Fresh prediction improves; individual movement/choice publication samples vary
with callback/display phase and do not establish an improvement for those paths.
The existing physical-input/publication guards pass. Times denote actual native
publication, not exact pixel scanout. The same observer checks actual player and
ball/shadow banks, complete freeze/resume boundaries, held control edges, menu
construction and dense normal-speed animation. The normalized actual core remains
18,020 B, 257 relocations, 14 sinks, SHA256
`9a457929bc223b843132bb53af7d604ed574441e32c4651eb69897aa0b48689d`.

PAL immutable attempt receipt SHA256:
`398ea92423dadf32275bd009e2bbe3579d0a3055a2e44841b7834c9b9e97b717`.
NTSC immutable attempt receipt SHA256:
`18362c9a66c03d1f6b1ab4e6e5e116d90903b57a60d6183e8e4ab454fd9bc9e2`.
The original pre-adjustment baselines were copied and hash-checked before these
affected reruns. Independent completed-evidence review cleared both exact
receipts, raw callback/publication reconstruction, input/state isolation,
native pixel selections and unchanged actual-core bytes. These publication
latencies are finite samples, not enforced general latency upper bounds.

Development executable is 207,332 B; code 56,836 B (+52), data 112,700 B and BSS
145,420 B unchanged; loaded payload 314,956 B. These complete callback maxima
include fresh input and transitions in this finite case, not all possible serve
positions or a universal worker bound. Resource collection explicitly remains
incomplete for standard runtime profile coverage (`--require-runtime --record`
returns 1). No unaffected native case was rerun. Full native/cold release
acceptance and appearance review remain pending; PR38 stays unmerged.
