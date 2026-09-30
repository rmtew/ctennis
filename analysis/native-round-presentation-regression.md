# First round tally, reset pause and resumed display

`p1-first-round-scenes` initializes the actual native application once at source
callback1203, before the first game award. It uses the independently validated
`one-player-round-lower-complete-phase` and the existing physical held-fire input.
It does not inject original main-thread resets or later state. The native program
runs through callback1471, including the interval where the original switches
temporarily to its counter/audio tail alone.

| Checkpoint | Source callback kind | Displayed contract |
| ---: | --- | --- |
| 1208 | Gameplay | Stable game tally after the point redraw |
| 1335 | Tail only | New round player layout after the main-thread reset |
| 1468 | Tail only | Reset layout retained at the end of the pause |
| 1471 | Gameplay | Actual resumed gameplay presentation |

The stable tally checkpoint is deliberately later than the award. At native
target1206, the displayed generation was1205; original generation1205 still
shows the previous score in the saved raster. Comparing that transition with a
new native score would conflate the original scanout lag with a port defect.
The selected1208 checkpoint has a verified stable source picture.

## Original pause association

No new original emulator capture is required. Primary source frames2632-2635
contain the reset; frames2766-2772 cover the end of the pause and resume. Their
raw hardware and rendered pixels already passed independent source validation
and identical repeated capture.

The earlier worklog description of `active_updates` was inaccurate. It does
not filter gameplay versus tail-only callbacks. Its interval is
`begin_frame < frame <= end_frame`. Short callbacks beginning and ending in the
same frame therefore have no indexed observation, while later tail callbacks
that cross a frame boundary are indexed. The maintained capture code itself
confirms this rule.

`source_generation` now requires an explicit matching callback kind. Its default
gameplay contract still rejects a tail callback. For an explicit tail contract,
it admits captured frame endpoints, then requires the independently captured
hardware sprite table to equal the original callback's entry sprite records.
It still checks captured hardware/image hashes, the validated VDP/raster
association and unique original pixels. It does not render an expected image.

The reset is in captured hardware by2632 and in completed pixels by2633.
Callback1335 associates hardware2633 with identical rasters2633/2634/2635.
Callback1468 associates hardware2766/2767 with the identical paused picture.
Callback1471 associates hardware2770 with the resumed picture at2772. Native
rasters use actual prepared/committed generations and completed scanout; the
requested callback is reported separately from the displayed generation.

## Actual native outcome

All268 consecutive post-tail states are compared. The first129 match; the
first divergence is1333, when the original main thread resets positions, roles
and transition state. The native main-thread round reset and tail-only dispatch
are absent, so old player placement persists. Checkpoint state difference counts
are0/20/30/48. These extend the existing known transition failure rather than
claiming a new implementation regression.

All24 point/game/status/mode crops match across the four checkpoints. All four
whole-viewport comparisons fail. The pre-pause first pixel is the existing sprite-origin defect
at callback1208, logical(50,36), black expected versus pink actual. Later first
differences are at(94,12), blue expected versus black actual, where the reset
scene needs a player that the native picture does not place there. Full viewport
hashes also retain all other differing pixels; the first pixel alone is not the
acceptance criterion.

No original refresh-sign consumption differs in the normal bounded run.
The capture adapter has an explicit diagnostic option to record consumption
differences as behavioural failures instead of raising a setup exception. Its
default strict checks remain in force for existing cases. Ordered audio checks
also account for a missing native write rather than skipping it when the native
event count is zero; this graphics case does not claim audio acceptance.

## Failure masking and finite detection checks

Known-red acceptance requires the first signature **and** a canonical digest of
every compared state difference, every expected/actual field and whole-viewport hash,
and source-event differences. This is a temporary exception for a measured
broken implementation, not the correct expected oracle. Correct expectations
remain the independent original state and pixels. Changing, partially repairing
or dropping a later observation changes the classification. Host stop frames,
beam positions, paths and executable addresses are excluded from the digest.

Three compiled changes activate only after the earlier tally checkpoint:

- Shift native sprites one more pixel at the reset checkpoint.
- Display the wrong second point field after the pause starts.
- Consume an extra refresh-sign input during the paused interval.

All preserve normal game RAM and the earlier first pixel failure. The first two
change actual completed reset output at1335. The third records `[]` expected
versus `[0]` actual at1335 rather than aborting the test. All classify as
unexpected red despite the unchanged overall first failure. Synthetic policy
controls also reject later pixel/state/event changes and missing observations.
Independent normal captures reproduce the complete acceptance digest.

Reproduce:

```powershell
python scripts/run_round_presentation_tests.py --case p1-first-round-scenes --self-test
python scripts/run_test_suite.py --baseline-check --self-test
```

The case remains red for the known incomplete port. Stop equivalent first-round
windows after this finite set. Complementary serving-end/two-player scenes,
accepted mode changes, match/result/menu/restart graphics and the remaining
F2/F4/F5/P2/P3 requirements remain open. Source state diagnostics may be retired
when equivalent named behavioural checks are established during native cleanup.

The full92-case runtime suite completed with52 green and40 exact known red, all
self-tests passing and no unexplained/tool failures. The round comparison then
expanded from a court ROI to the entire256x192 viewport: the smaller region
omitted115/115/119 differing reset-head pixels in the three later scenes. The
normal and all three compiled-mutant captures were rechecked, verifying pinned
capture reports, executable/source/reference hashes and unchanged prior pixel
regions. All newly included pixels now participate in acceptance. The case and
aggregate reports record this comparison followup; runtime code and captures
are unchanged. All actual reports classify under the reviewed final policy.
