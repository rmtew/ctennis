# Court prototype delivery

The active increment starts from merged PR #37, `d779dacc`. The approved
[tutorial roadmap](tutorial-mode-design.md) remains the feature contract.
The first visual checkpoint is deliberately small: current human serve, legal
position edits, actual held/released alternatives, projected ball/shadow animation,
ghost position, readable court/score, progress/hints and Resume latest. Play from
here is visibly disabled until edited-checkpoint branching is proved. This
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
- [ ] Commit and independently review the current-serve runtime prototype.
- [ ] Run the selected PAL case from a committed handoff; retain its campaign ID,
  literal RPC, complete boundary readbacks, original viewport PNGs and animation.
- [ ] Independently review completed evidence and report actual RAM, stack,
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
