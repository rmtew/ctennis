# Startup video standard selection

The game reads Kickstart's `ExecBase.VBlankFrequency` once before Forbid,
Disable, SuperState or custom-chip takeover. The named offset `$212` is the
readable byte in [exec/execbase.i](https://d0.se/include/exec/execbase.i), before
its V36 additions; unlike EClockFrequency, it is available on Kickstart1.3.
For the supported fixed OCS A500 display,50 selects PAL and60 selects NTSC.

PAL installs the existing CIA interval11838+14906/65536 and zero-based last
line311; NTSC installs11947+13180/65536 and last line261. These are conservative
bounds for the shortest312/262-line fields. The existing four-line guard gives
cutoffs307/257, both later than publication start253. Startup no longer samples
beam movement or waits for a field. An unexpected OS value returns DOS
RETURN_FAIL(20) before takeover, with timing state untouched. There is no guessed
fallback. This supports the fixed PAL/NTSC target, not arbitrary programmed modes.

Live nine-bit beam reads, publication IRQ handling, three-bank ownership, HUD,
gameplay and audio are unchanged. The earlier measurement-hardening proposal is
superseded by this simpler selection; its commits remain historical evidence.

## Historical failure evidence

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

The same capture has ExecBase at `$c00276`, Exec version34 revision2, and
VBlankFrequency at ExecBase+$212 equal to50. Reading that byte selects PAL
without interpreting the captured invalid beam measurement. The private USS is
retained outside Git; neither an emulator restore nor a WinUAE execution pass
is claimed by its read-only inspection.

## Focused protection

- `python scripts/run_video_standard_tests.py` assembles the actual selector and
  constants. All256 possible OS byte values execute against poisoned timing
  state:50/60 must replace every bound/interval/phase correctly; all254 other
  values must return20 and preserve the state exactly. This includes the50 read
  from the actual failed USS.
- `python scripts/run_startup_publication_tests.py` cold-boots the exact packaged
  release on Copperline PAL/NTSC with zero and512KB slow RAM. Physical Enter
  must produce matching hardware/software court pointers and positive raster
  evidence for both controller-role labels, in addition to title disappearance.
  The report is marked incomplete before work; failures/interruption supersede
  any previous pass, with a host unit check covering both failure paths.
- `python scripts/run_native_video_clock_tests.py` checks the exact standard's
  bounds and every observed CIA callback deadline in CCK on unexpanded PAL/NTSC.

These checks are in the finite acceptance command. Fresh Copperline results do
not claim WinUAE or physical-hardware validation. No unrelated full campaign is
required for this focused change; outstanding resource coverage remains explicit.

## Validation status

Pending fresh candidate validation after replacing startup measurement. Earlier
measurement-candidate receipts and hashes are superseded; see Git history for
those results. The private candidate must pass independent review before merge
or any Library replacement.
