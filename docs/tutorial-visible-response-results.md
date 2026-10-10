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
out of scope. Landing visibility, complete owner costs, continued edits,
close/resume, both routes and both standards still require current-product proof.

Campaign `1801d21b56ec4ce2990d5f876230d416` preserves all stronger capture
failures. Transport overflow, buffered profile metadata, unsupported profile
frame emission under run_until and canonical subregion-boundary observer errors
are collection failures, never product passes. Fixes and the resumed attempt
remain under qualification. Independent review is ongoing.

PAL native visible cadence is 50 fields/s; NTSC is approximately 60. A nominal
60 Hz simulation does not create 60 distinct PAL display frames. No corrected
disk, universal deadline bound, resource clearance, full acceptance, WinUAE
pass, merge or release is established by this investigation checkpoint.
