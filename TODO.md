# Deferred work

- [PR #24](https://github.com/rmtew/ctennis/pull/24) remains an active Shot Doctor design. Implementation is not approved.
  Keep that draft independent of repository cleanup.
- Investigate 16-bit Copper-list-relative destination offsets only if they are
  useful after the direct HUD change. Check range, sign extension, alignment and
  each bank layout. Measure code, relocation bytes and contended 68000 time.
  Preserve fixed initialization, per-bank caches and DMA tests.
- Recording, save and seek extensions remain later work.

Exit-game work was cancelled; reboot remains the intended behavior.
