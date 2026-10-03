# Deferred work

- [ ] Investigate compact score Copper patch descriptors after the current
  release: replace 32-bit destination addresses and their relocation records with
  16-bit offsets relative to each Copper-list base, using 68000 base-indexed
  addressing where appropriate (for example `0(a0,d0.w)`). Verify offset range,
  sign extension, alignment and identical destination offsets across every bank
  layout; do not assume the lists match. Check whether a fixed high/low-word
  separation permits one offset per pointer pair instead of two. Keep graphics
  lookup references separate from destination descriptors. Compare emitted code
  and data bytes, relocation count/bytes and actual 68000 elapsed CCK including
  chip-bus contention, for both unchanged and changed fields; do not assume a
  speedup. Preserve fixed-pointer initialization, changed-field early rejection,
  independent per-bank caches and all score/Copper/DMA regressions, including
  all-bank visible scoreboard checks and negative controls. Record measurements
  and obtain independent review before adopting any change.

This is an investigation note only, with no implementation authorized here.
Keep PR #25's frozen release head `1ec93d4d29e89f462efe9cdc2779b146e6346518`
unchanged; the coordinator handles merge ordering after release work. This task
is independent of PR #24 and does not approve the Shot Doctor implementation.
