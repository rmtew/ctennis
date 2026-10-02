# Framed square-score layout

The follow-up user request closes the WIN boxes, separates HUMAN/AI from A/B,
and places the selected square LED scores in a framed upper compartment. The
existing native y68 WIN top line is the shared divider. No scoring rules or
palette entries change.

Authored native geometry (inclusive borders):

| Element | A | B |
| --- | --- | --- |
| Role-label row | y34–41 | y34–41 |
| 16x16 score cell | x16–31, y48–63 | x224–239, y48–63 |
| Frame sides | x11,36 | x219,244 |
| Top / divider / bottom | y43 /68 /123 | y43 /68 /123 |
| WIN word cells | x17–31, y72–119 | x225–239, y72–119 |

There are two blank native rows between the A/B header cells and the role row.
Every score cell has four blank native pixels between its edges and its frame.
The old left border moves one pixel outward because a16-pixel cell cannot have
equal integer padding inside the previous23-pixel interior. WIN glyph pixels and
row pitch stay unchanged. The zero and other narrower numbers are centred inside
the cell using horizontal translations only; odd-width ink necessarily leaves a
one-pixel remainder. No selected segment pixel is redrawn, scaled or clipped.

`score-layout-contract.json` specifies the new geometry and translations; the
original selected masks in `square-led-contract.json` remain frozen. All seven
states still mean0,15,30,40,A,40,blank. The original48-byte segment definition is
unchanged; a seven-byte signed alignment table plus alignment padding is added.

The existing16-row point banks move down eight rows. Role banks move down two
rows, retaining court pixels in their full-width strips. Two fixed plane0/3
restores are added after the role row because there is now a gap before the point
bank begins. Horizontal Copper fetch slots and all WIN/status scheduling remain
unchanged. Startup still creates the same28 point banks; gameplay still switches
pointers. The WIN and status strips change only the moved frame-edge pixels.
No bitmap size, score-bank allocation or colour is added.

Reference: user screenshot Library
`libfile_24aa2b5c5a188191b3d6220223b9a180`. Local supported materialization failed
with `library file transfer failed: download failed`; authorized-file fallback
also could not resolve it. The parent worker inspected the actual screenshot
and reported its open WIN bottoms, high unframed zeros and crowded role labels.
This implementation uses that inspection plus the actual native assets. Local
visual verification uses fresh native emulator captures, not an inferred copy
of the user screenshot.

Focused checks are the37 host tests, explicit native-input validation, the startup
pixel-equivalence/fault test, all28 scoreboard mode/end/state fixtures, and a
DOUBLE FAULT status fixture that checks frame pixels while status strips are
active. The scoreboard comparisons include both published physical Copper banks,
all selected/restore pointers, all score/tally variants, both role-label variants
and the A/B-to-role blank gap. No broad full native campaign is claimed.

## Focused result

All listed checks passed on product `0ce30f56f15f0f7fd39ad57d2a003f795e03ce9d`:
37 host tests,94 input checks,28 generated banks,28 native scoreboard fixtures
with56 panel/role captures, and the DOUBLE FAULT fixture with112 native checks.
The deliberate wrong advantage position, wrong WIN pointer, late status field
and wrong status-pointer controls were rejected. Both physical Copper banks and
all236 pointer descriptors were checked; no publication deadline misses occurred
in the scoreboard fixtures. Ordinary physical-keyboard one- and two-player starts
also passed the full panel and role-label comparisons. The first ordinary preview
attempt captured the still-visible outgoing title too early; waiting through the
normal start transition produced the verified serve captures. No product change
was made to hide that intermediate capture.

Construction measured21.232ms before the game clock starts. Against current
master21c370f, the clean executable is248480 ->235412 bytes (-13068); loaded hunk
payload is202104 ->202504 bytes (+400, excluding loader bookkeeping). The point
banks remain14336 bytes. The extra two fixed-plane restores enlarge the two
Copper lists by16 bytes each; there is no additional bitmap plane or score bank.
The unchanged48-byte segment table gains a separate seven-byte alignment table
and one alignment byte. Gameplay still performs pointer selection, not drawing.

The visually inspected1500x1030 comparison is saved as
`baseline-rally-framed-square-scores.png`, Library
`libfile_7a650b8165548191bd91c5bb5a03dcef`, version0. Its main court is an ordinary
native capture displayed at716x537 from the716x285 field; the labelled state
samples are native fixtures. [The compact receipt](score-layout-verification.json)
records hashes and controls. Raw captures, reports and executables remain ignored.
A subsequent documentation-only commit adds this receipt without product changes.
