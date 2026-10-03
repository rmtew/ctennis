# Direct score/WIN bitmap update plan

For review before runtime edits. Audit base: accepted PR #25 merge
`d4c9be71364225a663897acf2664e14ca7e2865c`; no runtime changes in this plan.
Keep appearance, simulation timing, PAL/NTSC selection, COPER ISR and the three
front/ready/building roles unchanged. This does not authorize Shot Doctor work.

## Chosen minimal layout

Use three sets of fixed, full-width, plane-selective strips, permanently paired
with the existing Copper/sprite bank indices:

| Region (native coordinates) | Planes | Bytes per bank | Three banks |
| --- | --- | ---: | ---: |
| Points, y48..63, stride32 | 0, 2, 3 | 1,536 | 4,608 |
| WIN, y72..119, stride32 | 1 | 1,536 | 4,608 |
| **Total mutable bitmap storage** | | **3,072** | **9,216** |

Initialize strips once from the retained court planes. Stamp A's point at byte2
in plane2 and B's at byte28 in planes0/2/3. Stamp each WIN row's plane1 word at
byte2/28 to choose earned versus grey, preserving other planes and frame pixels.
Six unique16x16 masks cost192 bytes; the existing seven point states map
`0,1,2,3,4,3,5` (state5 is another40, final state is blank). Preserve the original
fixed tens/units and A placement; no appearance change or new preview is needed.
An8-row WIN word mask needs16 bytes. These are proposed tile storage sizes, not
measured executable deltas; retain the existing immutable font/definitions and
provenance. Generate masks once from existing product definitions, never from the
independent frozen test masks. Compare with those masks during validation.

Status occupies y96..103, within WIN. Compose its existing full-width plane1
256-byte variant into this bank's WIN strip, then restore current A/B WIN words
for those eight rows. Retain immutable status banks and their ordinary start/end
switches for planes0/2/3, and existing mode banks at y34..41. This removes all
per-row point/WIN/status-overlap switches without extending the work to a new
status/mode renderer. Static court is still shared elsewhere.

Replace236 score pointer descriptors with explicit region boundary setup: six
point pointer pairs (enter/restore three planes), two WIN pairs, six status pairs
(enter/restore three planes), eight mode pairs:22 pairs total. Bind fixed strip
and restore addresses at initialization for each bank. During preparation only
three status and four mode pairs can change; point/WIN changes write bitmap words.
Retain three shortened Copper lists: sprite pointers/colours, display setup,
footer and COPER publication still need the existing ownership protocol.

## Static audit and alternatives

Counts below come from merged source declarations and actual retained file sizes,
not a new executable build or emulated timing run. Court planes are256x192,
32 bytes/row, four planes; the proposed destination sizes follow these dimensions.
Copy counts exclude tile generation and initial field stamping.
The earlier described2x40 strip geometry does not match this merged source:
point masks are2x16 bytes and WIN has six8-row labels (48 rows).

| Layout candidate | Three mutable copies | Initial destination-copy word writes | Assessment |
| --- | ---: | ---: | --- |
| Whole four-plane court | 73,728 B | 36,864 | Duplicates192 rows despite static court. |
| Four-plane HUD band y48..119 | 27,648 B | 13,824 | Simple contiguous band, but copies unchanged planes/rows. |
| **Selected fixed plane strips** | **9,216 B** | **4,608** | Three bounded regions; no per-row beam choreography. |

Existing point storage is28*512 =14,336 B chip BSS; games storage is14*1,536 =
21,504 B retained data. Replacing these35,840 B with9,216 B strips plus208 B tiles
reduces this bitmap-storage subtotal by26,416 B. This excludes code, Copper,
relocation and metadata changes, which require an actual build. Retain7,168 B
status and3,072 B mode assets initially. Existing236 descriptors occupy3,304 B;
with their pointer tables the current reported category is8,008 B. Do not claim
all of it as savings until the shortened implementation is assembled.

Deterministic destination write counts for one building bank, excluding caches,
address setup and instruction fetches:

- Both points changed:64 word stores (A16; B48),128 B.
- Both game counts changed:96 word stores,192 B; redraw six rows per player for
  simplicity, including reset/decrement, avoiding another incremental mechanism.
- Status changed alone:128 word stores to its plane1 strip plus16 WIN repair
  stores,288 B; three pointer pairs add6 Copper word stores.
- All fields changed: status copy first, then both complete WIN/point stamps:
  288 bitmap word stores (576 B), plus14 status/mode Copper word stores (28 B).
  Do not duplicate the WIN repair when complete WIN redraws already cover it.
- No fields changed for that bank:zero bitmap/pointer stores beyond comparisons.
  If all three banks are stale, each is refreshed only when it becomes building;
  never update all three concurrently. At most3*604 =1,812 destination bytes
  across their successive all-dirty preparations (excluding caches/init).

These are planned store counts, not CCK estimates. Full HUD/court alternatives
can also stamp only changed words after initialization; do not pretend their
larger allocations require full copies every callback.

## Implementation sequence after specific approval

1. Add fixed strip storage/tile initialization and exact per-bank field caches.
   Replace only score field preparation and score Copper commands/tables; preserve
   game/scoring fields and `prepared_field_values` generation binding. Use the
   existing build-bank selection, including invalidated ready-bank reuse. Update
   caches only after pixels/pointers are complete; mark readiness afterward.
2. Keep CPU writes restricted to the current building bank. Front/ready strips,
   Copper lists and sprite headers are immutable. Retain native freeze, atomic
   ready publication and ISR bank rotation unchanged; no beam-distance heuristic.
   Status and WIN changes compose in the fixed order above, including stale banks,
   reset and end exchange. Remove obsolete variant banks/descriptors and startup
   expansion only when their consumers have been replaced.
3. Extend existing native scoreboard/status checks for actual fetched strips in
   all three banks, all0..6 values, modes/ends and simultaneous score/WIN/status.
   Keep independent pixel contracts, frame borders and negative controls; adapt
   an obsolete wrong-pointer mutant to an actual wrong strip/stamp mutation,
   preserving its purpose. Verify writes never touch ready/front and preserve
   PAL/NTSC DMA, atomic generation publication and reset/dirty-all-bank cases.
4. Build once for listing-backed code/data/BSS/relocation deltas, then run only
   affected native checks and required final acceptance. No redundant old-baseline
   campaign and no unrelated broad framework. Review actual costs and pixel/DMA
   evidence before merge. Any appearance deviation returns for user preview.

## Before/after timing evidence

Reuse accepted PR #25 evidence for the old product; do not rerun it wholesale.
The committed `docs/metrics/current.json` binds development SHA256
`1a5286650df54e65d4a3339557b1b54f5a0a7c398fcd552b3c7537e14d547e72`
and release SHA256
`4ee3c2b2c2e2e67e418c372997609cb21c05afb8f06508d74b4e8371e7993911`.
Its report identity is
`e7b80a5ea695782e5a5375802d94a02ab596a0b69c33fddd09528be20d1f2b6d`.
Observed old cold-one maximum callback work is55,192 CCK and entry lateness
2,734.905 CCK; two-player values are56,673 and2,690.580 CCK. These maxima can
occur on different callbacks; do not subtract their sum as a measured margin.
The named setup pause profile has observed minimum simulation headroom791.005 CCK;
that is a scoped observation, not the whole-game worst-case bound.

Preserve receipt hashes and workload/target/observer definitions. Compare old/new
minimum simulation deadline headroom, display handover margin, callback maxima,
entry lateness and ISR cost separately in CCK and target-correct ms. Include
simultaneous score/WIN/status, reset/end exchange/all banks dirty plus ordinary
unchanged/changed fields on PAL/NTSC. Display50/60Hz and simulation~59.923Hz are
separate budgets; do not weaken deadlines, DMA assertions or compiled controls.
Report sample counts and observed extrema, not proven bounds or predicted gains.

This executor is available, but its clean worktree has no private build/tool cache
or raw accepted receipts. The committed metrics summary is available; raw receipt
bindings, NTSC/handover/ISR detail and any newly requested stress-case coverage
must come from the coordinator's accepted PR #25 artifacts. Obtain and verify
those before runtime comparison; if a metric was not observed, mark it unavailable
or add only a specifically justified bounded baseline observation. No emulator
campaign was started for this plan.
