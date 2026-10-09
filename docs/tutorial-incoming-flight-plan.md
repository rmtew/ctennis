# Incoming/contact/outgoing integration

Approved behavior: normal ball sprites repeat the opponent's incoming shot,
the edited human contact (or visible miss), and the outgoing shot through its
first landing, flagged net collision, or out. Placement and action remain
responsive. Moving the player can change contact time. The next opponent
response is omitted. PR38's appearance/release hold remains in force.

## Source decisions

Cache the complete 318-byte state only after the recorded incoming-launch
dispatcher returns, including scene, audio and service tails. The launch hook
marks the operation; it cannot supply a complete checkpoint. Retain its actual
initial projection, including scene overrides. Restart each edited trial at
the following logical operation, sampling the chosen human action with actual
held/edge rules. Run the actual private dispatcher through contact; preserve
player phases, clocks, eligibility and RNG. No fixed interception tick and no
forced contact. Current receiving context need not have a completed human shot.

After human launch, use the original ball tick on private state for geometric
flight, omitting future players/AI, scoring, audio and scene work. Samples use
the actual event-applied state. Court-Y crossing alone is not a net collision.
Preserve outside/bounce/flagged-net/bounds priority and classify court-out
bounce as out. Match tick stays a match tick; word counters bound each segment.
513 samples allow an initial sample and up to 256 incoming plus 256 outgoing
phases. A cap remains an explicit incomplete result.

Validate placement against the incoming phase's actual movement limits and
continue actual movement eligibility checks. Renderer/player coordinates must agree with the
trial; phase-dependent limits require an explicit check in the proof.

The first integration uses dense original ball ticks. PR40's guarded endpoint
query cannot provide dense samples by itself. Integrate it only after a measured
endpoint/publication benefit includes dispatch, guards, rejected paths and
dense-fill costs. Short/rejected flights require an exact cheap scan with no
repeated prefix. Measured results and remaining coverage are in [the delivery report](tutorial-incoming-flight-results.md).

## Delivery checklist

- [x] Cache post-dispatch incoming state and support current receiving context.
- [x] Restart variants at incoming+1 and prove earlier/later contact and miss.
- [x] Switch accepted outgoing flight to original ball-only ticks.
- [x] Publish normal sprite sequence with terminal dwell and repeat.
- [x] Actual CPU differential: complete private state, samples, contact timing,
  events and canonical/history isolation; alternate initial scratch state.
- [ ] Measure complete fresh edit/publication latency in PAL and NTSC; short,
  rejected and long flights, transition and held input cases.
- [x] Record code/state bytes, stack, callback headroom and chip RAM; regenerate
  both resource reports, keeping missing standard coverage explicit.
- [x] Independent source/evidence review, followed by source-only draft PR.

Integrator owns implementation and evidence; the parent coordinates independent
review. No merge or release approval is implied by focused acceptance. Public
raw captures, binaries and private inputs remain excluded.

Focused PAL/NTSC fresh-edit and held-input measurements are complete; the broader
short/rejected/transition matrix remains open. Independent review and draft status
are recorded in the delivery report. No guarded-query shipping integration or
cold-cache cursor hint is included in this slice.
