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

## Causal findings and correction under qualification

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

The current unqualified correction prepares banner, three menu ROIs and control
lines before the timer starts; uses two paired private footers with the existing
free-canvas ownership; retains actual original ball/shadow while prediction is
pending; waits for the actual initialized visible serve boundary on title entry;
and keeps actual prefix playback from consuming accumulated unavailable time.
Generation retirement, original resume and selected/other-branch fairness remain
requirements. Optional trails and deferred navigation/edited branching remain
out of scope. Both routes and both standards require current-product proof.

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
than animation counters. The landing cue becomes visible at terminal sample63
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
Both-standard and in-match qualification is still pending at this checkpoint.

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
are collection failures, never product passes. Fixes and the resumed attempt
remain under qualification. Independent review is ongoing.

PAL native visible cadence is 50 fields/s; NTSC is approximately 60. A nominal
60 Hz simulation does not create 60 distinct PAL display frames. No corrected
disk, universal deadline bound, resource clearance, full acceptance, WinUAE
pass, merge or release is established by this investigation checkpoint.
