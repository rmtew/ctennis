# Deferred work

- [ ] After PR #25 is accepted and merged, investigate direct score/WIN bitmap
  updates as the user-selected next direction: replace per-row score/WIN pointer
  switching and full variant strips with small LED tiles at fixed positions.
  Use the building buffer as the write target; displayed and ready buffers remain
  immutable until normal atomic publication/ownership rotation. Beam distance
  alone is not permission to modify a displayed or ready buffer. Validate the
  ownership rule against native DMA before changing the renderer.

  Compare buffered full HUD bands with whole-court buffers and simple fixed
  strips, measuring actual code/data/BSS, relocation bytes, chip RAM and elapsed
  68000 CCK including chip-bus contention. Consider six unique 16x16 one-bit tiles
  (0/15/30/40/A/blank): 192 bytes of source masks by arithmetic, not a measured
  total memory saving. Reconcile the seven logical states and described 2-byte
  by 40-row strip layout with the accepted release; quantify destination buffers,
  colour planes, copying, WIN graphics and publication overhead separately.
  Preserve selected LED shapes/positions and preview any appearance changes for
  user review before implementation.

  Removing score/WIN pointer tricks does not commit to removing all three Copper
  lists: dynamic sprites and display setup still need safe publication. Retain
  those mechanisms unless a separately measured and reviewed redesign justifies
  replacing them. Preserve fixed initialization, changed-field behavior and
  per-bank cache correctness for every retained path; require all-bank visible
  score/WIN, Copper/DMA and negative-control regressions, plus unchanged/changed
  field timing checks. Do not assume a speedup.

- [ ] Acceptance criterion for direct HUD cleanup: compare worst observed spare
  time against the accepted PR #25 baseline using identical workloads, tools,
  measurement boundaries and PAL/NTSC target configurations. Bind each result to
  its exact build. Report minimum simulation-deadline headroom and minimum display
  handover margin separately, in CCK and target-correct milliseconds; do not
  conflate 50/60 Hz display frames with the approximately 59.923 Hz simulation
  cadence. Include maximum callback work, entry lateness and ISR cost alongside
  code/data/BSS and chip RAM bytes. Exercise simultaneous score/WIN/status changes,
  reset, end exchange and all banks dirty, as well as ordinary unchanged/changed
  fields. Label finite-run maxima/minima and their coverage as observed, not proven
  worst-case bounds. Preserve existing deadlines, publication/DMA checks and
  negative controls; no weakened gates to obtain a better comparison.

- [ ] If destination descriptors remain useful after that redesign, investigate
  16-bit Copper-list-relative offsets with base-indexed addressing (for example
  `0(a0,d0.w)`) instead of 32-bit destination addresses and relocations. Verify
  range, sign extension, alignment and offsets across every bank layout; test
  whether fixed high/low-word separation permits one offset per pair. Keep
  graphics lookup references separate. Measure code/data/relocation sizes and
  contended 68000 CCK while preserving fixed-pointer initialization, changed-field
  early rejection, independent per-bank caches and score/Copper/DMA regressions.

Documentation only; no runtime implementation authorized by this note. Hold this
TODO PR (#26) until PR #25 is accepted and merged to avoid release-gate base churn;
the coordinator owns merge ordering. Leave PR #25's frozen head
`1ec93d4d29e89f462efe9cdc2779b146e6346518` unchanged. This task is independent of
PR #24 and does not approve Shot Doctor implementation.
