# Deferred work

- [PR #24](https://github.com/rmtew/ctennis/pull/24) remains an active Shot Doctor design. Implementation is not approved.
  Keep that draft independent of repository cleanup.
- Investigate 16-bit Copper-list-relative destination offsets only if they are
  useful after the direct HUD change. Check range, sign extension, alignment and
  each bank layout. Measure code, relocation bytes and contended 68000 time.
  Preserve fixed initialization, per-bank caches and DMA tests.
- Recording, save and seek extensions remain later work.

PR #27 implemented direct score/WIN strips and is merged. The
[measured comparison](docs/metrics/direct-hud-comparison.md) records its scope,
observed results and missing old all-callback minima. Those historical results
do not certify a later executable. Exit-game work was cancelled; reboot remains
the intended behavior.
