# Startup video standard selection

The game reads Kickstart's `ExecBase.VBlankFrequency` once before Forbid,
Disable, SuperState or custom-chip takeover. The named offset `$212` is the
readable byte in [exec/execbase.i](https://d0.se/include/exec/execbase.i), before
its V36 additions; unlike EClockFrequency, it is available on Kickstart 1.3.
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

WinUAE 6.0.3 user capture `baseline-rally2.uss` (SHA256
`1c510e769970523e59d2090d57efc838721feb2eaaf198cf3e4aa3513d680028`)
contains a completed court scene waiting behind the title. Its measured last line
is158 and safe line154; publication requires253 or later, so that interval is
empty. Relocated startup/publication instructions match release PR27. The capture
uses PAL/OCS/68000,512KB chip plus512KB slow, compatible CPU, both CPU cycle-exact
modes disabled. It does not establish interrupt liveness from one instant.

The previous routine treated any decrease as a wrap. WinUAE 6.0.3's beam readback
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
  constants. All 256 possible OS byte values execute against poisoned timing
  state:50/60 must replace every bound/interval/phase correctly; all 254 other
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

## Focused validation receipt

Product commit `076c5796f70288e00c3a5f57fec9ca6453ae880e`, BUILD076c579; pinned vasm 1.9d,
Copperline 1.0.0-rc.1 and external Kickstart 1.3, completed 2026-10-03:

- Actual selector:256/256 byte values passed; the verified USS byte50 selects
  last/safe lines311/307 and the PAL interval. Invalid values preserve all 18
  bytes of poisoned timing state and return20.
- Exact-release ADF cold Start:4/4 passed (PAL/NTSC × zero/512KB slow).
  Loaded hunks, bounds, cadence, title, hardware/software Copper pointers and
  positive controller-label raster checks (1,920 pixels each) passed.
- `RUST_LOG=info python scripts/run_native_video_clock_tests.py`:PAL239 and
  NTSC239 completed callbacks, each within its strict deadline. The first
  invocation failed because inherited logging suppressed the required target
  marker; its failed receipt is retained outside Git. This successful rerun
  supersedes it, without weakening target or timing assertions.
- `python -m unittest discover -s tests/unit -q`:67 tests passed, including
  failed/interrupted startup receipt replacement. `git diff --check` passed.

Receipt SHA256s (raw reports retained outside Git):

- selector: `2b2110c4d9d04f44b23b425285826ef840a04b4542e1f0c403b60e11086d1ea8`.
- cold-start: `ea24aea8c747ce268f1c32e0a76a7ff9d9a6ad51185c7d76caf88e95748215b3`.
- cadence: `e41c03498f427e4bea61d43e37ee7dd37ff46bf3dac5b4f7738555a335ab5fa8`.
- saved-state: `c63e423b3e5a3e0e2eec2390f8a364fb3a1ca36cc8e6d51c12c64248a3d41589`.

Development SHA256 `6a15f93a4fc45539cc008dc1ac8848d596684b7c4844dfc7d888043f4a763a4c`;
release `e7c777de556980d8e1c1aa7bcd9a2fd3dcfd8d3086b6c9d8e4422986c31c42fc`;
ADF `59d3fc5dbb0621997cf38ff713346543137863ad8b1cef5bba4d09bc5e2f69e8`.
Release 158,928 bytes; loaded code43,792 (+16 versus PR27), data112,188 and
BSS9,424 unchanged; total loaded165,404. No new writable state. Compared with
the abandoned hardened-measurement candidate, loaded code shrinks 24 bytes.

`python scripts/native_metrics.py --require-runtime --record` exited1 and
records explicit incomplete resource coverage for the changed executable.
Fresh full-game loading/stack/resource measurements and the full gate were not
run; earlier PR27 results remain historical at16679feb and are not claimed as
reused. No fresh WinUAE or physical-hardware execution is claimed. PR #28 is merged. This evidence does not authorize a Library replacement.
