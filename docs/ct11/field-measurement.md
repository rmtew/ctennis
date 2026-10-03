# Validated startup field measurement

WinUAE6.0.3 user capture `baseline-rally2.uss` (SHA256
`1c510e769970523e59d2090d57efc838721feb2eaaf198cf3e4aa3513d680028`)
contains a completed court scene waiting behind the title. Its measured last line
is158 and safe line154; publication requires253 or later, so that interval is
empty. Relocated startup/publication instructions match release PR27. The capture
uses PAL/OCS/68000,512KB chip plus512KB slow, compatible CPU, both CPU cycle-exact
modes disabled. It does not establish interrupt liveness from one instant.

The previous routine treated any decrease as a wrap. WinUAE6.0.3's beam readback
can transiently advance one line at horizontal position1 in its non-cycle-exact
path. A return to the current line can therefore look like158→157.
[Upstream fix5b2b253](https://github.com/tonioni/WinUAE/commit/5b2b253dcf27d24e6b183a06d2c4625d5fae0181)
restricts that adjustment to memory-cycle-exact mode. This is source-supported
causal evidence, not a traced reproduction of the user's original startup.

The game now recognizes a bottom-to-top crossing only when the previous sample
is at least256 and the next is below128. A one-line reversal, including256→255,
cannot satisfy that predicate. Two crossings delimit the measurement. Only
last-line bands260–263 (NTSC) and310–313 (PAL) are accepted; these cover short/long
fields and a one-line sampling/readback edge. The existing four-line guard remains.
The lowest accepted cutoff is256, after the publication start253. Cadence still
uses the existing PAL/NTSC constants and decision boundary300.

An invalid field retries measurement from scratch before storing timing bounds
or starting the simulation timer. There is no guessed cutoff, forced publication,
emulator-version special case, or unsafe earlier Copper restart. Unsupported or
persistently invalid timing remains in startup measurement. Runtime IRQ handling,
three-bank ownership, rendering, gameplay and audio are unchanged.

Focused protection:

- `python scripts/run_field_measurement_tests.py` assembles the actual measurement
  and cadence routines with a finite beam-reader fixture. It checks PAL/NTSC,
  backwards samples before/after wrap,256→255, and rejected short/gap/long lengths
  followed by valid fields. Exact result values and consumed sample counts are
  asserted. The frozen pre-fix assembly is a failing backwards-step control.
- `python scripts/run_startup_publication_tests.py` cold-boots the exact packaged
  release on Copperline PAL/NTSC with both zero and512KB slow RAM. Physical Enter
  must produce a court raster and matching hardware/software court pointers.
- `python scripts/run_native_video_clock_tests.py` checks actual CIA cadence and
  field bounds on the unchanged accepted unexpanded PAL/NTSC target.

Both new checks are included in the finite acceptance command. Their synthetic
beam cases are fixture evidence, not hardware measurement. Fresh Copperline
results do not claim a WinUAE or real-hardware pass.
