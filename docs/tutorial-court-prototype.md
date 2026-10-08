# Court prototype delivery

The active increment starts from merged PR #37, `d779dacc`. The approved
[tutorial roadmap](tutorial-mode-design.md) remains the feature contract.
The first visual checkpoint is deliberately small: current human serve, legal
position edits, actual held/released alternatives, projected ball/shadow animation,
ghost position, readable court/score, progress/hints and Resume latest. Play from
here remains disabled until edited-checkpoint branching is proved; its menu
caption is pending the appearance repair. This
checkpoint does not finish retained-shot navigation or the tutorial release.

## Ownership and review

The existing history/preview author owns runtime code. The root integrator owns
the finite capture/controller, build, resource recording and delivery. Independent
source review precedes execution; an independent evidence reviewer checks the
completed native observations. The user reviews native-resolution screenshots
and a short animation before visual tuning is locked, as required by the roadmap.

## Tracked work

- [x] Integrate independently reviewed bounded preview/seek foundation, PR #37.
- [x] Add finite `tutorial-court-pal` capture/controller case and negative observer
  controls for late/partial callbacks, missing loss telemetry and unbound evidence.
- [x] Independently review the capture source at `8a3704a` for its stated scope.
- [x] Commit and independently review the current-serve runtime prototype.
- [x] Run the selected PAL case from a committed handoff; retain its campaign ID,
  literal RPC, complete boundary readbacks, original viewport PNGs and animation.
- [x] Independently review completed evidence and report actual RAM, stack,
  complete callback timing, transition costs and preview/render wait.
- [ ] Present the native court screenshots and animation for user visual review.
- [ ] Add retained attempt selection, incoming flight, previous/next and time
  navigation, including missed contact and evicted/truncated context.
- [ ] Prove two-human exclusion, controlling-player bindings, mixed devices,
  repeated enter/leave and PAL/NTSC elapsed-time gesture behavior.
- [ ] Add Play from here with an edited canonical/input/RNG branch checkpoint;
  discard the old future only on explicit commit and prove branch replay.
- [ ] Complete the full target and cold release gate in the roadmap's final increment.

## First native capture

Use the single controller after source review:

```sh
RUST_LOG=info PYTHONPATH=<pinned-provider> python scripts/native_acceptance.py --plan --case tutorial-court-pal
RUST_LOG=info PYTHONPATH=<pinned-provider> python scripts/native_acceptance.py --start --case tutorial-court-pal
RUST_LOG=info PYTHONPATH=<pinned-provider> python scripts/native_acceptance.py --campaign <printed-id>
```

The actual A500/68000/OCS/512 KB/no-expansion product boots normally. Physical
keys start one-player play and enter with a G double-tap. The case edits a legal
position, compares F held/released, captures 24 actual animation samples, checks
that a G modifier release does not open the menu, then resumes while F is held.
No world or expected-state writes are permitted after boot.

Every observed outer boundary while paused must preserve the complete 318-byte
selected state, all 72 public history bytes and the interrupted 318-byte backup.
A read-only breakpoint after Resume latest publication checks the exact restored
state before reconciliation or dispatch. The first resumed boundary must retain
it; subsequent physical-held sampling must not invent an action press.
The capture pins actual PAL 311/11838/14906 video/timer selectors, normalized
shared-core bytes and loaded hunks. Every complete callback, including entry,
fresh input, rendering and resume, retains the original deadline checks.

Source viewport PNGs are retained. The 256×208 review views select the original
low-resolution active pixels with no interpolation; the GIF uses captured native
frames. These are actual product output, not a mockup or a separate tennis model.
All artifacts and source/tool/product inputs are bound in the receipt.
The first attempt (`0d576e5814b34362930663c0a71ed313`, head `6fec023`)
failed the original 128 MiB raw-log cap at 14.68 guest seconds; its original
artifacts are preserved. The first observed event was at 6.02 seconds, so 128 MiB covered
8.66 observed guest seconds. At that measured rate, 120 seconds would need
about 1.73 GiB; the streaming capture budget is 2 GiB with margin. This is an
estimate, and the finite 120-second limit remains unchanged. No writes are
filtered, and overflow still fails the attempt and permits emulator shutdown.
The next attempt (`ac28e589b3c0464b800dbcca004ad891`, head `46287b1`)
failed the 20-second view wait. Actual writes show preview completion at 18.49
absolute guest seconds and path rendering starting at 19.92, still in progress
at 28.48. The renderer processes one segment per callback, so the capture now
allows up to 40 seconds per view while retaining the overall 120-second limit,
all callback deadlines and loss checks. Each actual view wait is recorded for
latency review; the longer capture allowance does not establish usable latency.
Screenshot metadata binds the stable background surface after two fields. Full
queued and actual Copper publications are retained separately. Animation changes
sprite banks without changing the background generation; the screenshot metadata
does not claim that its latest published sprite bank has completed scanout.

## Resource decision

The author's proposed two private four-plane court surfaces need 49,152 bytes,
plus small controller/prepared-scene state. This is a design estimate until the
actual build and initialized Exec free list are measured. The prior finite PAL
fixture had 124,608 chip bytes free; it is not a guarantee for this ordinary boot
or the new renderer. Copy/draw and simulation work must be sliced and serialized,
and only complete surfaces may be published. A displayed or queued surface must
never be written. A fifth bitplane would conflict with the current OCS sprite
palette and is not part of this proposal.

Foundation preview waits of roughly 2–6 seconds make pending feedback necessary.
Deadline compliance alone does not establish useful interaction latency. If the
actual view exceeds available memory or callback headroom, reduce rendering work
before capture approval; do not add a timing exemption. Standard runtime metrics
and cold release coverage remain incomplete until their own checks complete.

The 40-second attempt (`0fc4d3a70e5548c2a5922736de8522e7`, head
`f558be1`) also failed readiness, with preview complete but path phase unchanged
from 19.92 through 48.48 absolute guest seconds. Source review identified a
Bresenham sign bug: initializing the step direction changed the condition flags
before the signed delta branch. Upward or leftward segments could therefore
walk indefinitely. The repair explicitly tests each computed delta immediately
before selecting its sign. Passive path cursor/line telemetry and failure
readbacks are retained for the next native proof; no timing exemption is added.

The repaired renderer at `13f2771` completed the initial and edited views and
24 held-shot animation samples. Attempt `6307797e8d6041ab8fd6fde3383630b2`
then failed the observer iteration cap during menu readiness: the emulator
repeatedly returned a reached `target` at the same 83.233847 guest seconds,
slightly below the requested floating-point time. The capture now treats the
protocol's reached-target result as completion, retaining actual returned time
for subsequent requests. All original artifacts and callback guards remain.

The full visual/resume run at `aeacdc6` (campaign
`355efdb360ee474f9c149044898fdd29`) remained failed: independent reconstruction
of 4,840,070 literal records found 5,191 complete callbacks with no drops, but
the first title callback had −756.86 CCK headroom. Every later callback passed,
with minimum headroom 12,412.38 CCK. The source repair initializes gesture
thresholds before the CIA epoch, skips unused hint scanning on inactive idle
screens and returns from an inactive tutorial tick before saving registers.
Fresh physical input, active tutorial and gameplay keep their full input path.
The deadline and all observers remain unchanged; a fresh run must prove the
reduced first-callback cost.

A read-only early check of the next run at `3a1d720` found the first callback
still short by 77.86 CCK (58,589 CCK work). The verified owned observer was
interrupted and its partial evidence preserved. The next repair bakes the normal
Tutorial caption at X96/Y71 into the existing title page cache, removing its
repeated native font draw without adding allocation. The selected fourth row
retains native inversion before the three-entry selection-cache lookup. The
independent authored raster contract now includes the fourth caption.

Appearance review can use the preserved complete visual/resume run at `aeacdc6`
while timing repair continues. Its native court, held-shot view and 24 captured
animation samples are actual emulator output, but the run is timing FAILED.
Independent inspection also found that the options view lacks its three central
menu captions/highlight; that appearance is defective and remains pending.
Do not describe this visual checkpoint as accepted native gameplay or a release.

The released-shot image also reports “CALCULATION LIMIT — INCOMPLETE”; its
preview is not complete. Independent literal readbacks verify all 318 bytes
restored at resume, prescribed history changes and no invented F edge across
17 subsequent held-input boundaries. The original executable/listing for that
historical run were overwritten; this limits product identity verification.
Future capture cases retain the just-built executable, listing and compile
manifest before launching the emulator, including on failure.

The selective PAL campaign `675b4408cdbf4431adf52fcfbcb643c1` at
`13cb3e9daf754bf17445c60c0ce4e3653093dd0c` passed and was independently
reviewed by `/root/native_receipt_review`. Its retained executable SHA256 is
`680c5a1684cdf42edfed36b2f15d5e233759806a59951907b06510dd508911b6`.
All five loaded hunks and the normalized actual core matched. The literal RPC
SHA256 is `e86385ea264066f7d4782c79f32d67b8b0d3552da16f8f82ebf49fc18f14b7ee`.
All 5,287 complete callbacks met unchanged deadlines: minimum absolute
headroom 3,555.137 CCK, maximum work 54,951 CCK, zero dropped observations.
There were 5,125 complete frozen boundaries, exact resume restoration and
17 subsequent physically held F boundaries without an invented press.
All 75 private queues and 72 actual publications preserved ownership;
all 31 native images and the 24-source/16-frame GIF matched original pixels.
These image bindings cover stable background, not latest sprite-bank scanout.

Observed free chip RAM was 71,992 bytes, largest block 71,408 and stack use
320 bytes. Development/code/data/BSS/loaded sizes were respectively
203,592/54,928/112,700/145,380/313,008 bytes. Preview/render readiness took
10.20–20.20 guest seconds in this finite sequence. The recorded standard
resource report remains incomplete; full target/release coverage is unmeasured.
This selective pass does not clear the observed menu appearance defect or
turn the finite released attached-ball preview into a completed outgoing shot.
Screenshots/GIF remain local: upload/publication is not authorized.
