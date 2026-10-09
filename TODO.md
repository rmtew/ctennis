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
- Optional ball sprite echoes follow the simple placement/normal-ball-animation
  baseline; see the [separate opt-in milestone](docs/tutorial-mode-design.md#optional-ball-sprite-echoes).
  Defining the milestone does not authorize implementation. Richard's future
  explicit go-ahead is required; primary objects win and clashes are skipped.
- Optional [static sprite trail fragments](docs/tutorial-mode-design.md#optional-static-sprite-trail-fragments)
  are a separate prototype requiring Richard's separate opt-in. Build over
  unchanged frames, invalidate on movement/action/context changes, preserve
  primary objects and allow gaps. Neither optional milestone gates the roadmap.

Exit-game work was cancelled; reboot remains the intended behavior.

- [ ] Review and integrate the [retained navigation/branch preparation](docs/tutorial-retained-branch.md); keep PR38 unmerged pending appearance and remaining acceptance.
