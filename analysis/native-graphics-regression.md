# CT07 native presentation boundary

The application renders eight maintained scene primitives: three parts per
actor, ball and shadow. Native animation and pose geometry prepare the next
scene at tick end; the next update uploads it. Round resets can refresh actors
immediately. Native ordering preserves the ball's three depth positions.
Prepared private Amiga sprite images replace runtime VDP pattern decoding.
Logical white, blue, purple and black roles select hardware pair palettes.

The maintained field selector consumes a typed logical score/mode/status
packet. It preserves delayed status draw, expiry and forced score redraw
boundaries, then patches inactive Copper pointers to prepared native bitplane
banks. Product builds exclude generated animation, sprite, scoreboard and VDP
routines and remove the 16 KB VRAM shadow and write/register helpers.
Temporary scalar game-state adapters and translated audio remain CT10/CT08 debt.

Captured-phase builds alone import the previous captured scene once and
serialize actual primitives for retained raw diagnostics. The ordinary product
never renders source sprite records. Diagnostic display flags are observational
and are excluded from ordinary builds. The exact C067–C06A semantic scratch
contract is unchanged; all raw differences remain recorded. Pixels have no
waiver or tolerance.

The existing placement runner now observes a completed published raster rather
than requiring the CPU breakpoint to occur after its viewport. Source geometry
must still be invariant across the declared original frames. Existing moving,
score/status, round and result comparisons retain their original images and
check every requested observation. Presentation reports now use the existing
run-start invalidation, provenance and atomic-finalization mechanism.

Concrete findings: the first native shadow blink mismatch at serve update47
was repaired from actual gameplay visibility flags. After field retirement,
whole-view comparison exposed 50 missing right tally pixels starting at
update17 / (219,73). Its Copper pointer switch now precedes the fetch, using
switch byte26 / wait$9d for plane1. The earlier $99 and $91 trials exposed partial pointer fetches in the two-player phase and were rejected; the $9d gap preserves the right field and preceding court pixels. The right point field retains its existing plane2 timing. Unused
hardware channels are hidden in the inactive sprite bank, preserving publication
isolation. A late sprite fault's diagnostic label is local so it does not break
native renderer local branch resolution.

The restarted-flight check exposed a four-pixel missing ball at callback13381.
An early-blank commit at scanline4 updated COP1LC after the Copper had already
started its previous list. A blank-time COPJMP1 reload now makes the published
bank drive that frame. Expected source images/generation association are
unchanged. Existing capture observations record actual native primitives,
selected hardware bank/control/planes and fit flags, with pointer-layout and
eight-channel/colour-capacity assertions. Bank snapshots describe their
observation frame; completed raster pictures retain their separate generation.
Each captured executable owns its private initial-state file, so later phase
builds cannot stale a placement receipt by replacing a shared build scratch
file. This changes capture ownership, not initial-state contents or product logic.

Final results, exact commands, source/executable/reference/tool/target receipts
and failed reproductions are recorded in WORKLOG.md and ignored build/ct07.
This bounded graphics acceptance does not prove full original-match equivalence,
cadence, peak chip RAM, audio waveform parity, cold ADF boot or independent
hardware validation. Compiled symbols describe bridge integration/retirement;
only actual comparisons establish runtime acceptance.
