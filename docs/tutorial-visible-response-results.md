# Tutorial physical visibility and response investigation

The exact privately delivered `4baa6da` disk failed the reported PAL title-entry
UX. These are Copperline observations, not a WinUAE or hardware pass. The exact
ADF SHA256 is `5f117929c19360e9ed5ed3441c596f6626930ee780bf900bfe1c1636154e65c6`.
The frozen delivery and every failed collection remain outside Git.

## Delivered disk reproduction

The probe cold-boots the actual read-only disk, catches its LoadSeg before
entry, compares the loaded stripped hunks, then uses physical title navigation
or physical in-match controls. It writes no guest state and does not select a
callback regime. Native 256×208 images select the existing pixels from the
original viewport without interpolation. Font checks use the authored font.

| PAL title route observation | Physical input to first observed matching pixels |
|---|---:|
| D movement | 64.684745 ms / 3 field transitions |
| G release to open menu | 2211.988514 ms / 110 field transitions |
| Down press to selected second row | 1469.047153 ms / 74 field transitions |

These are screenshot observation timestamps. The original coarse frame stop
can be partway through the following field; they are not exact completed-field
edges or normative response bounds. The pinned renderer replays the most
recently completed field. Later captures use at most 1 ms CCK transport batches;
this bounds stop overshoot, not the field's display-completion delay. Post-field
memory reads remain distinct from the queued state actually published.

Title reproduction campaign `4e36f504063743a69a55e1947f6aef8a` retained
`build/tests/tutorial-ux-delivered-title-pal/5c07e614ee8e42c59a934de77ee06a42/`:
538 native frames plus original viewport images and scanout GIF. The banner font
check fails. The initial frozen native ball and shadow objects are hidden;
ball mode stays zero throughout the held-F sequence. Menu checks pass only
after long settlement, which is evidence of the menu pixels, not responsiveness.

In-match reproduction campaign `488f64e35daa4198888a0188de30ab66` retained
`build/tests/tutorial-ux-delivered-match-pal/1d1279df00c64bebba124d4b18486108/`:
612 native frames plus viewport images and GIF. The banner also fails. Its
original frozen ball/shadow are visible native objects, but the old renderer
hides them while waiting. Held preview produces native samples in this route.
This distinguishes the title initialization failure from the presentation gaps.

## Causal findings and correction

Source inspection shows title selection enters PLAYING before score and serve
initialization. The old tutorial immediately freezes this incomplete snapshot.
The in-match capture measures initialized score, serve-wait phase and visible
original ball/shadow. Title initialization is therefore a separate liveness
cause; the original title capture did not watch all those fields and does not
by itself prove every intermediate phase.

The old fast placement path skips the banner, hides ball/shadow when no preview
sample is ready, and schedules footer hints downstream of prediction. Menu work
copies the full 24 KiB court in repeated slices, reserves a large owner for each
slice and renders labels synchronously. These are source-supported mechanisms;
only the visible timings above are measured user-facing costs. Outside-callback
time is not assumed idle or recoverable.

The current correction prepares banner, three menu ROIs and control
lines before the timer starts; uses two paired private footers with the existing
free-canvas ownership; retains actual original ball/shadow while prediction is
pending; waits for the actual initialized visible serve boundary on title entry;
and keeps actual prefix playback from consuming accumulated unavailable time.
Generation retirement, original resume and selected/other-branch fairness remain
requirements. Optional trails and deferred navigation/edited branching remain
out of scope. Both routes and both standards now have the finite current-product proof below.

## Placement publication and bounded neutral retention

The stronger PAL motion checks rejected `44c09eb`: first motion took five field
transitions (100.185937 ms observation time), and only 18 of 30 fields changed
pose. Actual root producers nevertheless ran 36 times over that 30-field window,
with borrowed-canvas owners around 9,300 CCK. Input sampling and canvas ownership
were therefore insufficient explanations for the missed visible fields.
The literal trace shows COPJMP publication on three fields out of each five.
Source inspection identifies repeated `discard_ready_scene` calls on accepted
movement requests as the mechanism: a 60 Hz simulation can retire a completed
pose just before a 50 Hz PAL publication opportunity.

The correction retains an already completed **neutral** sampled pose until its
replacement is complete. It does not retain prediction-bearing scenes. A native
Copper-bank pointer records neutrality only after fresh object/sprite construction
and validation of that bank's canvas: closed menu, actual control identity,
calculating caption, no landing metadata, mode 0 frozen original ball/shadow.
Every animation, legacy publication and original-court restoration clears that
descriptor, preventing bank-address reuse from treating a later prediction as
neutral. Entry also clears it. Admission and execution recheck immutable-canvas
eligibility; requests require the actual queued Copper pointer to match the
descriptor. There is no elapsed-time refusal cache or arbitrary waiting period.

Refusal is reconsidered on every root attempt. Changes to input source, menu or
selection, caption identity, canvas ownership, ball mode, marker readiness or
generation/variant can invalidate eligibility or select a larger work class.
Deadline admission continues to sample the live timer/beam. Prediction, cue,
menu and variant changes still retire obsolete completed banks immediately.
Retained poses keep their sampled generation identity; they are not relabeled
as a current prediction. Actual COPJMP auditing separately compares current
and queued identities and positively checks native frozen ball/shadow bytes,
the immutable calculating footer and control source, and absence of a cue.

Independent review found and corrected both a descriptor lifetime gap and a
pre-startup observer-cache snapshot error. The observer now replays the actual
startup cache writes and rejects later cache mutation. All interrupted captures
and review revisions remain preserved. Source review at `feaad05`, runtime
`b8b04f8`, found no remaining blocking runtime/observer coherence flaw:
`build/tests/tutorial-playable-review/ux-current-source-review.json`, SHA256
`acdc71e85914a198493c54f1d46b0c1899f80e8bab58534b042a46e327c74ba2`.

## Closed PAL title-entry evidence

Campaign `066e29453f5c4403ac1d33d5c36bbcb7` preserves the failed stronger checks,
review interruptions and fresh attempts. The closed PAL title capture is
`build/tests/tutorial-ux-candidate-title-pal/89f15fcbeaa74070ae47d257bae86692/report.json`.
It cold-boots the exact stripped ADF and uses physical title navigation.

| Current PAL title observation | Result |
|---|---:|
| First movement | 40.061237 ms / 2 field transitions |
| Continuous left movement | 28 changed poses / 30 fields; maximum gap 1 field |
| Menu open | 60.110604 ms / 3 transitions |
| Select second menu row | 60.119908 ms / 3 transitions |
| Menu close | 60.119062 ms / 3 transitions |
| Keyboard ACK | 22 complete pairs; maximum hold 2.845587 ms |
| Retained neutral publications | 13, all positively audited |
| Callback deadline headroom | minimum 3,821.409 CCK; no dropped events |
| Whole-machine chip pool | 449,920 B used; 74,368 B free; 73,168 B largest block |

The banner, keyboard hints, original frozen ball, actual landing cross, menu
labels and exact original resume all pass. An additional pixel reduction finds
81 mode 2 ball observations at 20 distinct positions before any landing cue,
using actual queued native headers/sample bytes and white image pixels rather
than animation counters. The landing cue becomes visible at terminal sample 63
in these schedules. This proves a displayed computed landing point, not a cue
that precedes the animated ball throughout its flight. Native sprite X equals the cropped pixel X; Y is
native object Y+1. An inherited 31-pixel X assumption failed and remains in the
earlier receipts; the current cue and frozen-ball checks use the measured origin.

The first-movement accounting is non-overlapping: physical key to actual XY
write 5.539775 ms, XY write to COPJMP 9.864121 ms, COPJMP to first completed-field
replay observation 24.657341 ms, sum 40.061237 ms. The last interval includes
display completion and observation overshoot; it is not all scheduler delay.
Outside-callback time is not assumed idle or recoverable.

The measured largest complete root producer owners are 10,032 CCK borrowed,
12,429 CCK without ROI/cue work and 22,650 CCK full. Their work allowances are
12,500, 15,000 and 25,000 CCK respectively; an additional 5,000 CCK service/margin
reservation remains separate. Entry through the following keyboard-service
entry measures 10,279, 12,684 and 22,898 CCK respectively. Every accepted owner
class in this capture fits its work allowance. These are finite maxima, not
universal WCET. Earlier measured 22,467 CCK work exceeding the old 20,000-CCK
allowance remains a failure; it is not rescued by the service reserve.

The initial NTSC observation failed at 60 fields while the original game remained
in score initialization with hidden native ball objects. Probe `7030ce6` uses 72
NTSC fields, matching 60 PAL fields' approximately 1.2-second observation duration.
This changes observation coverage, not runtime eligibility or gameplay timing.
The four closed current-product routes pass; the failed shorter observation remains preserved.

## Scope and retained latency accounting

These physical cold-boot runs do not establish matched deterministic starting
states: native boot entropy differs. Do not interpret their timing differences
as a matched causal prediction-latency comparison. The previously matched
incoming accounting remains in `docs/tutorial-next-operation-results.md`:
PAL 491.500312 ms and NTSC 484.965547 ms after the earlier scheduler correction,
including endpoint-known to COPJMP 14.200590/12.089805 ms. Its repeated-decline
cost is included in scheduler overhead, never an additional bucket. That
historical campaign proves its own product and is not fresh current-UX latency
proof. New matched prediction-latency qualification remains a limitation.

Campaign `1801d21b56ec4ce2990d5f876230d416` preserves all stronger capture
failures. Transport overflow, buffered profile metadata, unsupported profile
frame emission under run_until and canonical subregion-boundary observer errors
are collection failures, never product passes. The four closed captures and focused checks have independent review; collection failures remain failures.

PAL native visible cadence is 50 fields/s; NTSC is approximately 60. A nominal
60 Hz simulation does not create 60 distinct PAL display frames. A corrected private disk candidate is qualified for these finite routes. Universal deadline bounds, full resource clearance, full acceptance, WinUAE, merge and release remain held.

## Four-route qualification and focused resource checks

Runtime `b8b04f8`, probe `7030ce6`, campaign
`066e29453f5c4403ac1d33d5c36bbcb7` passed all four physical routes:

| Route | First visible movement | Changed poses / 30 fields | Menu open / select / close (ms) |
|---|---:|---:|---:|
| PAL title | 40.061237 ms / 2 fields | 28 | 60.110604 / 60.119908 / 60.119062 |
| NTSC title | 50.073124 ms / 3 fields | 28 | 33.040512 / 34.054328 / 34.078074 |
| PAL in-match | 60.096225 ms / 3 fields | 28 | 60.096789 / 40.070541 / 60.126956 |
| NTSC in-match | 34.042595 ms / 2 fields | 29 | 34.072766 / 50.096032 / 50.074241 |

Every continuous-motion maximum gap is one field. The non-overlapping first
movement intervals (physical input to XY, XY to the first displayed pose's
COPJMP, COPJMP to completed-field observation) are:

| Route | Input → XY | XY → COPJMP | COPJMP → observation | Total (ms) |
|---|---:|---:|---:|---:|
| PAL title | 5.539775 | 9.864121 | 24.657341 | 40.061237 |
| NTSC title | 9.376611 | 22.949565 | 17.746948 | 50.073124 |
| PAL in-match | 8.961923 | 27.044499 | 24.089802 | 60.096225 |
| NTSC in-match | 7.850439 | 7.999341 | 18.192815 | 34.042595 |

These are measured finite observation bounds, not exact scanout-edge latency.
All four verify actual banner/hint/menu fonts, frozen ball/shadow, computed
landing pixels, unchanged 318-byte original state and 72-byte history state,
unchanged history records, and physical original resume back to ordinary pixels.
There are 444 actual mode 2 ball photographs before any landing cue. The cue
appears at terminal sample 63 in these schedules; an advance landing cue is not
established. No edited-position commit or optional trajectory trail is added.

The four runs total 2,268 complete callbacks, 678 publications, 61 positively
qualified retained neutral publications, 92 complete keyboard ACK pairs and
four exact original restores. There are no dropped events or measured callback
deadline misses. The largest measured full root owner is 23,083 CCK; every class
and its following keyboard-entry bracket fit the 12,500/15,000/25,000 CCK work
allowances without consuming the separate 5,000 CCK service/margin reserve.
PAL uses 449,920 B of the chip pool (74,368 B free); NTSC uses 440,960 B
(83,328 B free), with no expansion pool. Finite measurements do not prove
universal bounds or full workload acceptance.

Campaign `02c9d008ad8c4256932327603e10a32d` independently passes 11 input checks,
four exact-release PAL/NTSC cold boots with zero/512 KiB slow RAM, and package
reproducibility. Only 36,396 bytes of HUNK_SYMBOL records are removed; the five
loaded hunks match the development image. The current product has 344,364 B
loaded payload, 15,412 B more than the delivered baseline. The fresh normalized
shared-core check independently matches 17,606 bytes, seven relocations and 14
sinks. The previously executed host suite passed 339 tests; its retained receipt
explicitly identifies parent-recorded tool-output provenance.

Independent receipts are `build/tests/tutorial-playable-review/ux-four-route-independent-review.json`
and `ux-focused-independent-review.json`. The source review's clearance covers
the qualified initialized lower-human routes. Outside that scope, rejected
`tutorial_request .missing` requests can leave a previous queued bank; broader
rejected-request retirement remains a hold, not a globally cleared invariant.

`native_metrics.py --require-runtime --record` truthfully records incomplete
current-product coverage in both `docs/metrics/current.json` and `current.md`:
all eight full named resource profiles remain unmeasured. Human appearance and
playability, WinUAE, matched deterministic current prediction latency, broad
fairness/cancellation, universal WCET and all resume/full-release holds remain.
No merge or public binary upload is authorized by these focused passes.

The curated machine-readable record is
`docs/evidence/tutorial-latency/visible-response-summary.json`; raw frames,
transport traces, failed attempts, reviews and private delivery artifacts remain
outside Git. Controls: WASD/pad move; hold F/button 1 for prediction; G/button 2
opens the menu; choose Close to return, or Resume Original to restore the actual
interrupted game. PAL presents 50 fields/s and NTSC approximately 60.
