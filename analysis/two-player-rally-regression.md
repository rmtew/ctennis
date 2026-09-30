# Continuous two-player rally regression

The original-game requirement is now established by the independent
`two-player-rally` case: six alternating accepted returns, followed by an
actual point award. The existing full R2 match remains unchanged and retains
its known round-transition failure. This supplementary case closes its
missing longer-rally observation; it does not establish complete P1/P2/P3 or
the other focused behaviours.

## Source discovery and frozen reference

Read the contact gates before choosing controls. Both use court-plane ball
position, require Y separation below four and X separation below seventeen,
and reject contact height at or above twenty-nine. The lower contact point
is player Y plus twenty-seven; the upper is player Y plus thirty-five. Both
use player X plus eight. A contact below eight height units chooses the
source's special short-trajectory path.

Physical steering with lower Y target 128 and upper target 31 produced only
single returns. In the first, upper contact height six selected the short
path and the ball failed at the net. Keeping the upper player at Y eight
allowed a two-return rally, but the lower player was still catching up in X:
its return landed beyond the sloping left court boundary, setting the source
out-of-court flag. These are diagnostic observations, not failed port tests.

Keeping both players deeper (lower Y 152, upper Y eight) gave the lower player
enough incoming flight time to align horizontally. Source-only steering then
produced 56 alternating returns before the diagnostic stop. It changed only
physical controller fields, never cartridge state. That discovery controller
is not the regression policy or an expected-result calculator.

The accepted reference freezes its actual controller changes through six
returns. At frame 2289 both controllers move right to miss the next contact.
The original awards the point at frame 2349. The frozen Lua policy contains
only scheduled physical presses/releases and a finite stop at frame 2689;
there is no state-dependent input or RAM injection. Two independent captures
agree byte-for-byte across 1,390 callbacks and 290 ordered PSG bytes. There
are no refresh reads or between-callback RAM writes in this case.

| Accepted return | Source callback | Source frame |
|---|---:|---:|
| Upper | 707 | 2006 |
| Lower | 762 | 2061 |
| Upper | 816 | 2115 |
| Lower | 870 | 2169 |
| Upper | 925 | 2224 |
| Lower | 979 | 2278 |
| Point award; point codes 2/0 become 3/0 | 1050 | 2349 |

Return evidence is the source's accepted-launch entry marker, followed by
captured flight and contact-animation state. `scripts/rally_reference.py`
groups these by actual score transitions, requires both players and at least
four returns within one completed rally, and checks the deliberate miss ends
that rally. The resulting report retains each actual court/display ball
position, active flight vector and player coordinates. Removing all lower
return markers is rejected; returns accumulated across separate points do
not satisfy the requirement.

## Actual native comparison

All 1,390 callbacks match the actual assembled gameplay routines shared with
the application: 254 state bytes at entry, pre-tail and callback return, plus
all 290 PSG bytes. State carries continuously from the initial capture; the
harness does not inject expected intermediate writes or compute expected game
results. A temporary native ball-X increment is detected at callback one,
pre-tail, court X expected 212 and actual 213. Mutated source and executable
are removed afterward.

This is a simulation/control-reader replay. Ordinary native physical input,
rendered contact/rally frames, audible output and real-time cadence remain
separate requirements. The actual game executable still has the known
between-game and hardware-output defects recorded by the rest of the suite.

Reproduce with:

```text
python scripts/capture_test_reference.py --case two-player-rally
python scripts/run_regression_tests.py --case two-player-rally --self-test
python scripts/inventory_match_references.py
python scripts/run_test_suite.py --baseline-check --self-test
```

Raw capture SHA256:
`01edaffe41ef371983620330729ac7a692e3f76108fd95f465c046b11b4f8208`.
Fixture SHA256:
`2ebf77b07faa0af4e7504094f5395b38b49cb5ddbdc173ccdb0728aeff1cbcbf`.
Private evidence remains in `build/tests/two-player-rally-capture/` and
`tests/reference/two-player-rally.json`. Diagnostic steering captures stay in
the ignored `build/tests/rally-discovery/`; only the frozen policy, case,
validator and conclusions belong in Git.
