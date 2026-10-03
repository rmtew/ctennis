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

## Startup PAL/NTSC cadence

The measured full field also selects the simulation cadence once (last line below300 means NTSC). PAL retains11838+14906/65536 E-clock ticks. NTSC uses11947+13180/65536, the nearest16-bit fractional interval to the PAL interval multiplied by715909/709379. Shared dispatcher code reads selected whole/fraction words; there is no per-update standard branch.

Source: Amiga Inc. Exec include, https://d0.se/include/exec/execbase.i lines189–199: E-clock frequencies709379 PAL and715909 NTSC, and ex_EClockFrequency only added inV36 (unavailable onKick1.3). Exact scaled fraction277711866223633/23244931072 is11947.201106487884; selected interval11947.201110839844. Rates are59.922737854578195 PAL and59.92273783275037 NTSC updates/second. Existing PAL interval on real NTSC would run0.9205234437444582% faster.

Copperline's current hardcoded PAL timebase means NTSC geometry/DMA checks alone do not validate simulation timing through its reported seconds. The native clock check instead validates CIA cadence in actual CCK and converts using the documented NTSC E-clock frequency, as described below. This avoids an emulator clock patch; audio pacing and real hardware behavior remain outside that claim.

The third bank's236 score descriptors/cache are initialized before the CIA timer starts, alongside the existing banks. The first uninitialized third-bank selection failed a strict callback deadline (76335CCK versus59191CCK); initializing all banks removed that runtime setup cost. The focused unchanged-dispatcher clock check then passed235 PAL and236 NTSC callbacks, including the first update. No callback deadline was relaxed. The final finite gate checks every callback in its ordinary lifecycle/setup campaigns as well.

NTSC timing validation uses actual CCK positions and native CIA timer writes, not Copperline's PAL-derived seconds. Pinned Copperline e65a9584ccd0c86e678661ed5d2c18622da63fd4 src/bus.rs cia_ticks_for_cck divides accumulated CCK by5 for both standards; therefore applying the documented NTSC E-clock frequency to this domain validates native interval selection/deadlines without changing the emulator. It does not certify emulator audio pacing or real hardware behavior. No emulator patch was made.

## Publication while a producer is active

Fresh NTSC phase22 testing found a genuine polling starvation: a nearly field-locked simulation update repeatedly spanned the six-line bottom guard, leaving all23 captured full fields on title despite live gameplay. Merely selecting the NTSC timer is insufficient.

Both title and court Copper lists now request COPER at line253. A dedicated level3 handler saves all working registers, acknowledges COPER and calls the same guarded presenter; main-loop polling remains available. Startup uses Kick1.3 Exec SuperState before owning the level3 vector and enabling only the Copper interrupt. Scene freeze and ready-discard ownership changes mask interrupts only for their short metadata transactions; next-bank pointer/cache work runs after restoring SR. A scene-specific ready_completed latch is set atomically with completion, or immediately for a complete scene built between callbacks. It stays valid across frozen ticks until consumption or supersession. The presenter accepts this latch while the next update is active. No simulation interval, event timer or deadline changes.

The direct NTSC phase22 smoke now has23 complete fields,368 control-header words, all three banks/eight channels,13 independently matched whole-bank snapshots and23 full-field publications.24 of25 observed strobes occur while a producer update is active; all select an already completed frozen generation. A compiled interrupt-disabled NTSC control retains the starvation mechanism. Setup/demo/attract observers bind publication to the actual ready generation rather than requiring the CPU producer to be idle.

Independent review found two interrupt-boundary defects in the first candidate: tick equality rejected valid older frozen scenes, and a main-loop line252 sample could resume after IRQ publication and clear blank_seen. The scene-completion latch repairs the first; the whole beam/latch/strobe transaction now saves SR and masks interrupts, repairing the second. The mask covers only beam reads, metadata and hardware publication; it never wraps gameplay or bank-cache preparation. The DMA oracle rejects more than one strobe per physical field.

Targeted proof: delayed title consumes generation234 after completed tick237; delayed paused court consumes generation181 after completed tick184. Both remain immutable through the delay and then install normally. A beam252 boundary fixture generated14 real pending Copper requests and passed with at most one strobe per physical field. Removing only the presenter transaction mask reproduces the exact latch reopening after an IRQ strobe (observed atphysical line255), and the oracle rejects it. Cold menu/return checks now pass132 checks. These are focused pre-freeze results; the final gate reruns them at the committed review head.
