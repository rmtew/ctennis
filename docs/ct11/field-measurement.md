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

## Focused validation receipt

Product commit `4f82fec8c919ac079945f5c64284c64a616ce213`, pinned vasm1.9d and
Copperline1.0.0-rc.1, verified external Kickstart1.3; completed2026-10-03:

- Actual measurement/cadence assembly:9/9 finite streams passed; frozen pre-fix
  routine rejected by the backwards-step assertion. Receipt SHA256
  `4c2487baaaf2b2b13a3a4807d435a1f492a9f3c54880a7b8616545fee9aa6ac8`;
  negative control `3f46cfb736e58e5474c4d34ee9e5df8ad9aff0399bc4ce83b2b79d7ea01f687f`.
- Exact-release cold ADF physical Start:4/4 passed (PAL/NTSC × zero/512KB slow).
  Initial title and court raster assertions, field/cadence values, loaded hunk
  equality, and hardware/software Copper pointers passed. Receipt SHA256
  `324241fb9417ffb0207eb3ba81d92591d3ea589e64dd4a8ab5a533d14ebe357a`.
- Native video clock:PAL236 and NTSC237 strictly completed callbacks passed.
  Receipt SHA256 `cab6a20482f6af4e2d25d7ac346c472b708752ca82f225b0f68cfe6dc6001064`.
- Host unit suite:66 passed. `git diff --check` passed.

Development SHA256 `20357f0cac9b8186f19bbb63542695e83eb6c49fdfae43212c2aafa9ccef9a4d`;
release `293789313e83b112e9d99e4c1dee0fea376ca50f2eba8c38bd3871ad71956815`;
ADF `ae12d6ca1fcefe5a1b9caf19aef00128615445d646bb18a9eb1791739b6527e8`.
Loaded code grows40bytes to43,816; data112,188 and BSS9,424 are unchanged.
Loaded payload165,428 and release158,956bytes. No new writable state.

`python scripts/native_metrics.py --require-runtime --record` exited1 with an
explicit incomplete resource report: the changed executable has not received
new full-game loading/stack/resource measurements. These are not asserted as
reused or fresh. PR27's earlier measurements remain historical at16679feb in Git.
Only the focused validation above is claimed; the full gate and fresh WinUAE or
physical-hardware execution were not run. The new exact-release ADF remains a
private candidate pending independent review and merge, not a Library replacement.

Review follow-up (observer-only): the four retained court PNGs were verified
against their original receipt hashes and each passed the existing positive
`assert_mode_raster(...,1)` check for both controller-role labels (1,920pixels per
capture). This closes the weakness of the original black logo-absence crop,
which alone could accept a blank image. Supplemental receipt SHA256
`19b6b88395d479001b50ba8a7b499ca66a93bbfd1b9613e12fcb6a92321f0bdd`.
The startup checker now requires this positive assertion on future runs and
writes incomplete/failed/interrupted status so a later unsuccessful invocation
supersedes a previous pass. The focused host receipt test passed both failure
and KeyboardInterrupt paths. No native rerun: these are new assertions on the
unchanged retained captures and a host failure-path test; product bytes, prior
native cadence/assembly results, and candidate hashes above remain unchanged.
