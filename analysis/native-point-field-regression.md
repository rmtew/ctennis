# Native point-field transition regression

The tests protect when live gameplay requests a new score, in addition to the
existing font-bank renderer checks. They execute the actual assembled native
game and its inactive Copper-list preparation, blanking commit and scanout.
No intermediate score, selector, input-reader result or expected source write
is injected.

| Case | Source award | Source draw | Native start | Stable raster targets | Point codes |
| --- | ---: | ---: | ---: | --- | --- |
| `p1-deuce-fields` | 9134 | 9135 | 9130 | 9136, 9139 | 5 / 5 |
| `p1-advantage-fields` | 9588 | 9589 | 9584 | 9590, 9593 | 4 / 6 |
| `p1-return-deuce-fields` | 9869 | 9870 | 9865 | 9871, 9874 | 5 / 5 |

Each phase is reconstructed from the pinned, independently repeated original
two-player match. Both physical Amiga joystick fire buttons are held, matching
the original reader observations. Each native run starts once, four callbacks
before the award, and carries its own state throughout the nine-callback window.
The continuous deuce/advantage/game simulation replay remains separate evidence
for accumulated state; these local starts expose presentation beyond upstream
known failures.

The first original callback awards the point and requests a redraw. The next
callback consumes that request and draws the score. Before that draw, native
field selections must retain the actual native bootstrap values observed at the
first simulation entry. These are read from the executable, not supplied by the
test and not claimed to reproduce the preceding source screen. From the draw
onward, compare both points, both game counts and mode with the original request.

Supplemental original media is retained separately under ignored
`tests/reference/presentation-point-fields`. Thirty rasters repeated identically
and preserved the original callback record. Captured VDP state independently
validates the source pixels. At each stable target, all five field rectangles
have unambiguous original pixels associated with the source generation. Region
association does not fabricate expected graphics or discard differences inside
the region; it avoids requiring unrelated moving actors to have identical pixels.
Native completed rasters are associated with actual committed generations, not
with an assumed one-callback-per-video-frame mapping.

All three normal cases have nine matching request observations and ten matching
completed field crops. The sole meaningful state difference in every callback
is the existing combined control byte C056: original17, native1. The native
second input reader remains a zero stub. First failures are9131,9585 and9866;
these are three contexts of that defect, not three new defects.

Known-red acceptance requires exactly this mismatch in every callback, all nine
request checks and all ten raster checks green. A different or additional later
state/pixel failure is unexpected red even when the overall first failure is
unchanged. Partial repair also changes the baseline rather than silently passing.

Two temporary compiled changes test detection: move the native score consumer
after the award routine, making selection one callback early; omit the second
point copy, leaving that field at its native bootstrap value. Neither change
alters game RAM. The finite stopping condition is rejection at the award for
the early update and at the original draw for the frozen field, in all three
contexts, with strict classification rejecting both behind the input failure.

All six compiled checks pass that stopping condition: early copies are detected
at9134/9588/9869 and frozen second-point copies at9135/9589/9870. Every mutant
classifies as unexpected red while retaining the same earlier input mismatch.
Normal and mutant state streams are identical. There are27 request/state checks
and30 completed field crops across the three normal cases. No equivalent
regained-advantage case is needed to test the same update boundary again.

Reproduce source preparation and native comparisons:

```powershell
python scripts/capture_presentation_reference.py --case two-player-match --recipe tests/cases/point-fields.json
python scripts/freeze_point_reference.py
python scripts/run_point_tests.py --all --self-test
python scripts/run_test_suite.py --baseline-check --self-test
```

The point runner returns1 for the measured state failure. The aggregate remains
incomplete until the separate F2/F4/F5, P1, P2 and P3 backlog requirements have
reference-backed comparisons. These cases protect point changes and preservation
of games/mode; they do not establish mode transitions, game resets, later scenes,
audio or ordinary real-time acceptance. Stop equivalent scoring permutations
after the detection checks pass.

Full aggregate verification completed with91 cases:52 green,39 exact known red,
all self-tests passing, and no unexplained differences or tool failures. The
three new red classifications retain the same input defect. Four open coverage
groups still make the aggregate fail; the complete-suite goal is not achieved.
