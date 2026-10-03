# Three-bank publication design

The released ADF can restart Copper at line24 after a scene finishes at line22.
The subsequent sprite pointer MOVEs overlap header DMA; captured channels fetch
POS/CTL words again as DATA/DATB. CPU COPJMP timing alone missed this fault.

Keep three complete Copper/sprite banks with explicit ownership:

- `front_copper`: displayed and immutable.
- `ready_copper`: latest completed scene, immutable until consumed or superseded.
- `back_copper`: the producer's writable bank.
- `spare_copper`: the free bank when no completed scene is waiting.

There is exactly one displayed bank and one writable bank. The third bank is
either ready or spare, never both. Completing the writable bank replaces the
ready scene; its superseded ready bank becomes writable. If none was waiting,
the spare becomes writable. Completion records its generation and title/court
selection before advertising readiness. Rendering never writes the front or
ready bank. Simulation continues at its existing fixed E-clock cadence.

Publication uses the first main-loop poll from line253, after the footer's last
line251 and the latest sprite terminator reads on252. Read the full nine-bit
physical beam position with high/low/high sampling; retry a changed high bit. Once per bottom interval it
installs the latest completed scene, or repeats the front if none is ready.
The existing Disable/Forbid ownership and polling remain; no interrupt handler
or OS input path is introduced. An update spanning the boundary delays that
poll. It can publish later in the guarded bottom window; if it misses the entire
window, repeat the front. This polling design does not promise an exact line253
interrupt. New completion after the interval's first poll waits for the next
interval. Reset the once-per-bottom latch on any observed visible line, so a
main-loop poll need not hit line0 to recognize a new interval.

Use COP1LC plus COPJMP in this bottom-only window. This avoids a queued-but-not-
active fourth ownership state. The old front becomes spare only at this safe
handover, after its bitplane/footer and sprite consumers have finished. Measure the physical field's last beam line at initialization before the
simulation clock starts, and close the bottom acceptance window four lines
before that measured last line. This allows for alternating field lengths and
keeps COP1LCH/L plus COPJMP comfortably before automatic restart. A late
or inconsistent sample retains the displayed bank; never let the CPU pointer
write straddle automatic restart. The bounded sequence must finish every sprite
pointer pair before the next field's header DMA. No early-
field publication is allowed. A repeat never recycles the displayed bank.

Each Copper bank retains an independent six-byte score-selection cache. Court
bitplanes and prebuilt score/status banks remain shared and immutable. The third
bank adds3064 Copper bytes and576 sprite bytes before any implementation size
change, plus its cache and ownership metadata. Actual RAM remains measured.

Verification binds all eight channels to the installed generation and bank;
checks all pointer pairs complete before header DMA; follows actual header,
image-data and terminator addresses; and rejects headers fetched as pixels.
Sweep publication phase, include PAL wrap and all three bank roles, and require
the released implementation to fail as a negative control. Preserve canonical
trajectory, physical input isolation, UI transitions, cadence and512KB metrics.

The accepted target remains PAL. Line253 is the layout's conservative retirement boundary, not a
PAL field-length assumption:208 rows beginning at44 end before252, with sprite terminators through252. The new beam
reader also handles NTSC field wrap. Audit the released and candidate NTSC
targets separately; the pinned model begins NTSC sprite header DMA at20 rather
than PAL25. NTSC E-clock frequency differs, so the current PAL interval is not
proof of equivalent simulation timing. Do not claim NTSC acceptance or change
its cadence without reporting the required scope.
