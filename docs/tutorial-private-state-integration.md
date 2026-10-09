# Private-state shared-core integration

The current product adds the approved generation guard after the supplied-A5
migration. Current measurements and validation are in
[the generation follow-up](tutorial-generation-results.md). The retained measurements
below describe only the preceding `ff236692` product.

Richard approved the supplied-A5 scope in [the design](tutorial-private-state-scope.md).
Product `ff23669241d5c3c2bcbaf9afbcc112ad1ff19ac1` runs the actual shared core directly
in private prediction buffers. [PR38](https://github.com/rmtew/ctennis/pull/38) stays
draft and unmerged pending appearance review and complete acceptance.

## Implemented boundary

Public logical APIs preserve caller A5 and the body's condition-code contract,
and bind canonical state. Instrumentation preserves incoming flags before the
body; blocked calls preserve caller SR. Direct bodies receive an even 318-byte context through A5. The scorer uses
state offsets, including valid offset zero, with a negative terminator. Retained
prediction dispatches the same nine actual bodies and reads their owned state.
There is no alternate gameplay model or separate prediction implementation.

Private execution removes three recurring 318-byte transfers per worker. Full
318+72-byte external selection checks, balanced replay scratch and 72-byte history
metadata restoration remain. Checkpoint, initial-context, explicit seek and resume
copies remain. Synchronous/sliced seek retains its reviewed canonical working path.
Algorithms, RNG order, audio/scene clocks, state layout and schema are unchanged.
Native sinks retain canonical live reads and frozen-output suppression; contact
hooks, score-Copper helpers, bulk copies and the presentation IRQ preserve A5.

## Actual-core verification

Independent source review cleared wrappers, core state references, scorer pointers,
private readers/dispatch, sinks and IRQ preservation. Selected CPU campaign
`3c738fc71ae0411e90009281c5e64aab` completed successfully with full acceptance false:
`history-cpu`, `preview-cpu`, `seek-sliced-cpu`, `core-entropy`, `core-shared-bytes`
and `private-state-cpu`. History/preview ran fresh and were reused on resume after
a missing evidence-path correction; the other four cases ran fresh.

The differential executes the retained reviewed native executable, current live
native executable and current standalone private core sequentially: 2,056 operations
per one/two-player context, 4,112 total. Every boundary compares all 318 state bytes
and ordered events before recording trace/projection digests. Two poisoned private
bases alternate; CPU bus guards reject canonical, other-owner and canary accesses.
All 4,112 public A5 checks and nine blocked-operation A5/CCR checks passed. History
checks replay every retained boundary with different initial state, cursor wrap,
relocation and actual native sinks. Preview checks cache, replacement, cancellation,
resolution, lifecycle, output isolation, ownership transitions and budgets 1..4.
Sliced seek compares checkpoint 512→569 in native and relocated standalone images
while selection 835 remains public until commit.

Normalized native/standalone core bytes are identical: **17,524 bytes**, seven
relocations, fourteen sink branches, SHA256
`951935ce4ec1538f5ff2fa83898c36af7a75de60f4c0fe025e74181543f1544c`.
No absolute core-state relocations remain. The core is 496 bytes smaller.
Native loaded code is **56,412 bytes (424 fewer)**; data 112,700 and BSS 145,420
are unchanged. Loaded payload is 314,532 bytes; development executable 205,940
bytes (1,392 fewer). Native SHA256:
`3a9ea3037c70cedaf165acb7f2df01405b1849fd7abcc2a5cfb37c2244bf8237`.
Standalone SHA256: `e44ea6770300f07bc6d7bfba41f6c0c34da8250bbe566247a5ea814147788f36`.
These assembled sizes replace the scope document's encoding estimate.

## Fresh native result

Affected campaign `752010155f314f518e23eb6645039f71` passed its two selected cases.
It executed OCS/68000/512 KB chip, no slow/fast RAM and external Kickstart 1.3.
Full acceptance remains false. The previous product is `6f2828735c273258c0c0abdb577778f1e831a7ae`,
SHA256 `c543a695d9493254eb152cf34a093676c3c0c0dcd4df203d0ad105a5b97e3cb8`.

| Finite measurement | PAL before → after | NTSC before → after |
|---|---:|---:|
| Accepted fresh held request → first actual endpoint, raw CCK | 2,506,041 → 1,959,597 | 2,481,597 → 1,862,179 |
| Same interval, regional guest seconds | 0.706545 → 0.552482 | 0.693272 → 0.520228 |
| Reduction | 21.8% | 25.0% |
| Preview worker call entries in interval | 83 → 77 | 79 → 68 |
| 318-byte state-copy call entries in interval | 252 → **0** | 240 → **0** |
| Complete callbacks checked | 763 → 691 | 744 → 673 |
| Maximum complete callback work, CCK | 54,879 → 54,937 | 54,940 → 55,061 |
| Minimum absolute callback headroom, CCK | 3,626.137 → 3,573.137 | 4,116.006 → 3,988.006 |
| Initialized free chip / largest block, bytes | 70,040/69,456 → 70,464/69,880 | 79,000/78,416 → 79,424/78,840 |

Both fresh captures have zero deadline misses and dropped notifications, 320-byte
observed stack extent, invariant 318/72/318 frozen boundaries (518 PAL/500 NTSC),
exact Resume latest and no pressed edge from held resume input, with all three
native presentation banks resumed. Physical movement → player publication is
28.446/27.280 ms; held-choice → already computed endpoint is 19.713/10.119 ms.
Dense ball/shadow animation preserves the checked normal-speed cadence.

The endpoint metric starts at the accepted request store and ends at actual
native publication; it is not pixel scanout or physical-key latency. The provider
uses 3,546,895 CCK/s in both regions: its NTSC values are 0.699653→0.525017 seconds.
The table instead converts raw NTSC CCK using 3,579,545 CCK/s. These finite live
captures have different phases/sample counts; they establish no universal bound
or paired per-tick speedup. Global callback maxima increased slightly while every
observed deadline still passed. Source inspection alone does not prove timing.

Copy counts come from the unchanged write-only capture transport: actual emitted
BSR/JSR return-address stores, exact return values and the capture's verified loaded
hunks/listing. [The read-only parser](../scripts/check_private_state_copies.py) binds
executable, manifest, capture, listing and literal RPC to completed receipts. Counts
are call entries in the stated interval, not exclusive cost or matched-RTS spans.
Initial/checkpoint/commit copies outside that interval still exist.
Supplemental retained output: `build/tests/private-state-cpu/native-copy-counts.json`,
SHA256 `36de6d688e67ffce7be9668276339c016d18576c1cbf90557cfd6c75c5898fcc`.

## Commands and receipts

Commands ran with `RUST_LOG=info` and
`PYTHONPATH=/tmp/ctennis-shared-core-python/lib/python3.12/site-packages`.
The CPU command also supplied
`CTENNIS_PRIVATE_STATE_BEFORE=/tmp/ctennis-private-state-before/build/amiga/interfaces/enhanced/baseline-rally`.

```sh
python scripts/native_acceptance.py --plan --case history-cpu --case preview-cpu --case seek-sliced-cpu --case core-entropy --case core-shared-bytes --case private-state-cpu
python scripts/native_acceptance.py --start --campaign 3c738fc71ae0411e90009281c5e64aab --case history-cpu --case preview-cpu --case seek-sliced-cpu --case core-entropy --case core-shared-bytes --case private-state-cpu
python scripts/native_acceptance.py --resume --campaign 3c738fc71ae0411e90009281c5e64aab
python scripts/native_acceptance.py --plan --case tutorial-court-pal --case tutorial-court-ntsc
python scripts/native_acceptance.py --start --campaign 752010155f314f518e23eb6645039f71 --case tutorial-court-pal --case tutorial-court-ntsc
python scripts/check_private_state_copies.py --output build/tests/private-state-cpu/native-copy-counts.json /tmp/ctennis-private-state-evidence/before-tutorial-court-pal build/tests/tutorial-court-pal /tmp/ctennis-private-state-evidence/before-tutorial-court-ntsc build/tests/tutorial-court-ntsc
python scripts/native_metrics.py --require-runtime --record
```

| Receipt | SHA256 |
|---|---|
| History CPU | `45c4c5b431495c75b5fdbaac4e20c69ed0bcddc9b9a9d9137cfe6f53911ba757` |
| Preview CPU | `4b5d2109fa0271f1cf216bf0c805dbe588e50558aa7ea1d7ad25337c827c83c6` |
| Sliced-seek CPU | `2bcaa71fb7660a3e9284992cbfc9aff1c5c34a122fbaa8871cdfaafc91db43b6` |
| Entropy CPU | `f80ad770b9e6bedf2d398c4428611916410ffc4f4dfe20c78875835e1f6967f8` |
| Shared bytes | `9d3ccf85c29f8e56cb8d96246cd4e6868ba15c5c22c6e2d4fbb564e33e230b3c` |
| Private-state differential | `0efaa78845900df865b20c923782254ca02eea7ca188d24c95682e195a0aff65` |
| Native PAL | `33505b5dc27280ed2bd695e9e78c7edf4d31e41b1225d00c210b89ec43acc1f3` |
| Native NTSC | `829b8aad556fd288e6c98bfa15eb1ae6241a5be683a05a0b229ab25246139907` |

Campaigns and raw receipts/media remain ignored under `build/acceptance/campaigns`
and `build/tests`. Historical PAL/NTSC captures were moved intact to
`/tmp/ctennis-private-state-evidence/before-tutorial-court-{pal,ntsc}`, with all 79
files per region verified before/after in `preservation-audit.json`. Current output
directories link to fresh storage there to avoid the nearly full workspace disk.
No unique native input was removed.

## Retained failures and remaining gates

The first campaign accidentally omitted case flags on start and used the default
catalog. It stopped before emulator execution; package receipt validation rejected
changed dependencies. `dd8396f9870647a4a9baa90f83d2c21f` remains preserved and is not
a pass. The selected campaign's sliced-seek attempt 000001 failed before execution
because its historical input path was absent here. The original 835-operation
prefix and all five source-evidence hashes matched in the retained evidence
worktree; an unchanged campaign symlink fixed its location. Attempt 000002 passed.
`/tmp/ctennis-private-state-evidence/seek-input-location-audit.json` records this.

Earlier precheck failures remain recorded in
`/tmp/ctennis-private-state-precheck-failures.json`. The preview test now accounts
for seek generation advancing twice during a deliberate seek away and back;
only those four expected bytes change, and every other protected byte still
compares equal. The new differential executes CPU instances sequentially because
machine68k owns one machine globally. No expected intermediate gameplay state
was injected or oracle regenerated. Focused host checks passed (226 checks). The copy parser also rejected an
incomplete receipt and an intentionally changed listing; both negative controls
are retained in `build/tests/private-state-cpu/copy-parser-negative-controls.json`.

Resource record and check both exit 1 for **incomplete standard profile coverage**;
focused tutorial measurements do not fill that coverage. Full release/cold-ADF
acceptance, production retained-return navigation/publication and user appearance review
remain pending. No optional trails, retained-branch runtime or Exit work was added.
Independent reviewer `/root/native_receipt_review` cleared the exact source and
completed selected evidence: all six CPU receipts and both native receipts,
recorded inputs/products/artifacts, raw state/output/callbacks, scalar readbacks,
Exec free lists, presentation banks, media/cadence and independently recounted
copy entries and regional latencies. No material blocker exists within these
selected extents; the remaining gates above are not claimed complete.
