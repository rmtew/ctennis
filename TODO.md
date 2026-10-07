# Deferred work

- Implement the authorized [tutorial roadmap](docs/tutorial-mode-design.md),
  starting with the shared deterministic core. It replaces conflicting proposals
  in draft PR #24. Keep one increment active and review before merge.
- Investigate 16-bit Copper-list-relative destination offsets only if they are
  useful after the direct HUD change. Check range, sign extension, alignment and
  each bank layout. Measure code, relocation bytes and contended 68000 time.
  Preserve fixed initialization, per-bank caches and DMA tests.
- Full-match files, disk flushing and portable saves remain later work.
  Bounded rolling history and seek are part of the tutorial roadmap.

Exit-game work was cancelled; reboot remains the intended behavior.
