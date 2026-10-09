# Generation guard: current measurements

Richard approved replacing repeated paused-selection byte comparisons with the
existing incrementing generation and controlled ownership. Product
`b1eb145c8417a54045b80f585b475f4f1f3665e3` implements that bounded follow-up to
[the supplied-A5 migration](tutorial-private-state-integration.md).
[The mutation audit](tutorial-generation-guard.md) defines the contract.
PR [38](https://github.com/rmtew/ctennis/pull/38) remains draft and unmerged.

## Changed contract and product

Warm request, worker entry and completed result now check generation and frozen,
unowned selection admission. All legitimate selection mutations invalidate the
existing generation; it saturates rather than wrapping. The final issued token
`0xfffffffe` can complete; terminal `0xffffffff` disables new requests until
restart. No state bytes were added. The full 318/history 72 diagnostic remains
explicitly available in standalone PREVIEW_DEBUG tests, alongside poisoned
contexts and full-state/output/cursor comparisons. A generation counter does not
detect arbitrary memory corruption. Sliced seek retains its full selection check.

The actual native and standalone core remains **17,524 bytes**, seven relocations,
fourteen sinks, normalized SHA256
`951935ce4ec1538f5ff2fa83898c36af7a75de60f4c0fe025e74181543f1544c`.
Native SHA256:
`9bfd85797f8b3a997cff8fa1489be8bfdfca45a0396001935da019c3fc117454`.
Standalone SHA256:
`9cccfffd752e328cfa5f1a4a5c2c2ccd64e1d0c2c8fbc4b72cca7dbeaaabda8b`.
Loaded code is **56,388 bytes**, 24 fewer than supplied-A5; data 112,700 / BSS 145,420
are unchanged. Loaded payload 314,508; development file 205,908 (32 fewer).
The stripped release computed SHA256 is
`61f772a1452b24b2aefa1a3cff6f816332c15e84d2ffd25c82c3505dd7a17292`,
175,004 bytes. This static identity does not claim a fresh release cold boot.

## Current-serve native latency

OCS / 68000 / 512 KB chip, no slow/fast RAM, external Kickstart 1.3. These finite captures
include physical controls, rendering, audio configuration, complete transitions,
all three native presentation banks and exact live resume.

| Measurement | Supplied-A5 PAL → generation PAL | Supplied-A5 NTSC → generation NTSC |
|---|---:|---:|
| Accepted fresh held request → first actual endpoint, raw CCK | 1,959,597 → 1,603,734 | 1,862,179 → 1,558,616 |
| Same interval, regional seconds | 0.552482 → **0.452152** | 0.520228 → **0.435423** |
| Observed reduction | **18.16%** | **16.30%** |
| Complete callbacks | 691 → 655 | 673 → 613 |
| Maximum callback work, CCK | 54,937 → 54,937 | 55,061 → 55,028 |
| Minimum absolute callback headroom, CCK | 3,573.137 → 3,573.137 | 3,988.006 → 4,023.006 |
| Initialized free chip / largest block, bytes | 70,464/69,880 → 70,488/69,904 | 79,424/78,840 → 79,448/78,864 |
| Observed stack extent, bytes | 320 → 316 | 320 → 320 |

Both have zero dropped notifications and deadline misses; full 318/history 72/
backup 318 remain frozen at 481/441 complete boundaries. Resume restores the
entire selected live backup and reconciles held input without a pressed edge.
Independent raw reconstruction reproduced every callback and queue/publication,
71 sprite checks per region, 35 viewport→native image pairs and both menu drawings.
Dense animation retains normal-speed cadence. Verified current PNG/GIF are copied
to `/workspace/tutorial-visual-review/`, with exact hashes and product/receipt
identity in `generation-visual-index.json`; older files remain separately labeled.

PAL physical movement→player publication is 27.817 ms; held-choice→already computed
endpoint 19.087 ms. NTSC is 36.955/34.227 ms, worse than the preceding finite
27.280/10.119 ms observations. There is no universal responsiveness improvement
claim. Fresh endpoint begins at accepted request and ends at actual publication,
not physical input or pixel scanout. Regional conversion uses 3,546,895 CCK/s PAL
and 3,579,545 CCK/s NTSC. The provider uses the PAL clock in both regions, yielding NTSC
0.439431 s. Different phase/sample counts preclude paired per-tick speedup claims.

## Matched actual-core CPU costs

Six-case CPU campaign `b50677c9dc314e998b365c346461eb28` completed: history,
preview, sliced seek, entropy, shared bytes and private-state differential.
Every history boundary/checkpoint uses full 318/ordered events/cursors, poisoned
initial working state, relocation and native sinks. Differential runs the retained
pre-A5 native product, current native and standalone actual core sequentially:
4,112 logical operations, 4,112 public A5 checks and nine blocked A5/CCR controls.
Full memory-write guards protect canonical, other-owner and canary regions.

Preview proof tests all 390 diagnostic selection bytes individually, stale tokens,
cancel/seek/edit/resume, active/replay rejection on cold and warm jobs, saturation
and actual completion of the final issued token. These deliberate negative writes
are diagnostic controls; native gameplay receives no expected intermediate state.

| Matched job | Supplied-A5 → generation CPU cycles |
|---|---:|
| Cold, 308 worker calls | 7,421,342 → 5,751,982 (−22.494%) |
| Cached, 114 worker calls | 3,331,006 → 2,713,126 (−18.550%) |
| Maximum cold worker | 75,106 → 69,686 |
| Maximum cached worker | 57,328 → 51,908 |
| Cold request | 21,794 → 21,888 |
| Cached request | 18,296 → 12,826 |

Exactly 5,420 CPU cycles disappear per worker, with equal logical operation counts
and complete state/output comparisons. This is CPU-runner cost, not native CCK
or a promised native percentage. Independent review recounted the matched costs.
Observer-only follow-up files are absent from all four long CPU receipt closures;
these results remain compatible. Entropy/shared closure checks were run fresh
again after the observer fix.

## Current instruction/worker profile

Optional PAL campaign `645c9f6e1ee54f4a96b4483a27cda7d8` passed at the same
unchanged native product. A physical D edit to first actual held publication took
**1,645,612 CCK / 0.463958 seconds**. This different input/phase is separate from
the current-serve table. The retained pre-migration profile was 0.768514 seconds.
Actual emitted call stores and paired RTS reads isolate 78 complete worker roots,
**672,981 bus CCK**, maximum 13,234. Their exclusive categories partition exactly:

| Category | Bus CCK | Share of worker spans |
|---|---:|---:|
| Guard/admission helper | 4,704 | 0.70% |
| Copy/restore helpers | 28,630 | 4.25% |
| Core body own instructions, excluding descendants | 30,314 | 4.50% |
| Public preview own instructions | 54,840 | 8.15% |
| Other helpers, including physics/scene/score/audio descendants | 554,493 | 82.39% |

The core-body subtree union is **477,659 CCK (70.98% of worker spans)**. It overlaps
the exclusive categories and must not be added to them. No recurring
`game_history_copy_state` call appears in these workers. `game_ratio` has 147 calls,
85,731 exclusive / 85,930 inclusive CCK. Ratio is 12.74% of workers but only 5.21%
of the entire fresh endpoint interval. Eliminating its whole measured cost would
be about 24.17 ms; that is a cost comparison, not a predicted speedup.

The separate flat profile includes trailing commit frames and an old-generation
tail. All 27 committed CLSM/PC streams contain 302,971 ordinary instructions,
302,997 encoded samples, 1,814,486 charged CCK, 40,140 chip wait CCK and 572 IRQ CCK.
Every row/retired count/summary matches; 26 complete-frame DMA traces count
730,756 CPU-owned / 722,532 idle / 346,112 bitplane CCK. CPU waits attribute
29,717 to bitplanes, 6,059 refresh, 1,336 copper, 976 sprites and 545 audio.
These are bus ownership totals, not worker budgets. Timer reread lexical region
has 213,224 charged / 5,313 wait CCK; ratio has 97,792 / 2,083. Broader flat lexical
regions are not call subtrees or fresh-worker-only measurements.

All 165 complete callbacks passed (max 54,937 / min headroom 3,573.137 CCK), zero loss,
63 frozen full 318/72/318 boundaries. Stack 320 is observed during the profiling
window; startup stack is unmeasured. The fresh interval contains 27 wholly
contained callbacks: 1,030,554 CCK total work, minimum finishing margin 13,550.586.
Five callbacks hit the four-worker-call cap, eighteen ran three, two ran two and
two ran none. Raising that cap alone therefore cannot explain most stalls.
Summed finishing margins overlap time already spent waiting and are not a
transferable latency saving. This observer has no fresh CIA-return-value ledger;
flat PC samples and complete spans cannot prove why every admission declined.
The literal profiler request and loaded code both bind base 129,680 / size 56,388;
no screenshots/register/slot/memory tracing was enabled. Source provenance is
`0a008de`; pending docs and unrelated retained-observer edits meant the working
checkout was not globally clean, while every consumed hash and product stayed exact.

Independent review reproduced all streams, actual 5,863 call/RTS rows, 165
callbacks, frozen tuples, loaded-hunk checks and endpoint publications. Receipt
SHA256 `5b9a90d38011c9d12e23b8f6f2eea47131b7d1d411da2699143fad0685fa69cd`.

## Next assessment: admission before larger batching

Recommend a small read-only admission/reserve assessment before choosing another
runtime batching change. The previous guard-plus-copy justification (43.7% of
workers) is obsolete: those exclusive categories are now 4.95%. Core work remains
dominant, most callbacks stop below the existing four-call limit, and the actual
end-to-end span substantially exceeds worker time. Record coherent actual CIA
reads, branch/admission outcome and next bounded worker/publication unit for each
fresh/cancel/result transition; do not infer a spendable budget from idle slots
or aggregate headroom. This is evidence to review, not approval to lower reserves.

A later batching proposal must preserve fresh input/preemption, generation checks
at every public boundary, result/publication tails and worst callback deadlines
in both regions, including retained resolution and seek. Measure code/state/stack
and full cold/transition costs before claiming a throughput benefit.

Exact ratio arithmetic is the smaller secondary candidate if that assessment
shows little safely usable headroom. It changes less ownership/scheduling, but
its whole measured cost is only about 5.2% of this endpoint interval. First prove
an emitted original/candidate comparison over the three masked 8-bit inputs,
including zero divisor, overflow/wrap/rounding, clobbered registers and CCR/X.
Then compare full shared-core state/events and actual native timing; no `DIVU`,
lookup table or improvement percentage is approved by this report.

## Retained native jobs

The physical fixed-seed acquisition records a human return/missed contact,
pauses with the real P control, seeks once to the retained selection, completes a
cold job at budget 4, then an edited cached job at budget 2. Both variants compare
all 318 bytes, paths and ordered outputs against uninterrupted execution of the
same actual standalone core. Live selection/history/backup, caller frame, input
and other-owner state stay protected at every API yield. The fixture issues one
owned API per actual callback; it is not production retained navigation or
endpoint publication, and its request→result latency includes that scheduling.

| Finite retained measurement | PAL | NTSC |
|---|---:|---:|
| Cold worker calls / resolver operations | 329 / 805 | 329 / 805 |
| Cached worker calls / resolver operations | 254 / 0 | 254 / 0 |
| Cold request→result, regional seconds | 5.540447 | 5.540582 |
| Cached request→result, regional seconds | 4.288986 | 4.288912 |
| Cold summed worker / maximum worker, CCK | 3,206,871 / 23,403 | 3,216,246 / 23,500 |
| Cached summed worker / maximum worker, CCK | 1,620,926 / 20,380 | 1,632,372 / 20,530 |
| Complete callbacks / body frames | 900 / 1,861 | 848 / 1,870 |
| Callback median / p95 / maximum, CCK | 19,392 / 26,011 / 55,460 | 19,516 / 26,332 / 55,543 |
| Fresh-input callback samples / maximum, CCK | 6 / 22,944 | 6 / 23,874 |
| Minimum absolute headroom / stack bytes | 3,050.137 / 292 | 3,506.006 / 278 |

No drops or rejected writes occurred. Literal IRQ acknowledgements prove active=1
resolver and active=2 variant bodies were interrupted with their actual A5 owner.
NTSC's original two jobs covered only active=2: attempt 000002 correctly failed the
promised extent despite completing the jobs. A fixed-budget 3 normal-API diagnostic,
limited to 512 calls, obtained the missing active=1 pair after three steps. It records
generation 8/status 1 before cancellation and preserves the original two completed
jobs. No IRQ, timer, callback phase or intermediate state was forced. Original
2,048-callback/70-second/raw-byte caps remain; PAL needed no auxiliary work. NTSC
also proves the observer repair with one actual seek-body entry resumption.

## Evidence, failures and remaining gates

Runtime commit is `b1eb145c`; observer binding is `40f5b69d`; read-only body observer
repair is `0a008de0510249739d60dc404c79cf4c2de80001`. The repair changes no executable.
An IRQ resumed an observed entry before its first instruction; the previous
observer counted a second body and tried to add a duplicate return breakpoint.
Retained NTSC attempt 000001 remains failed. The fix requires unchanged complete
318 bytes, architectural registers, owner, return slot and no semantic intent,
plus literal completed IRQ acknowledgements in strict timestamp order. It keeps
the original IRQ-inclusive duration/body budget, caps additional resumptions 64
per API and reference-counts genuine tail frames sharing a return breakpoint.
236 host tests passed, including missing/incomplete/out-of-order IRQ and changed
state/register/owner/return-slot negatives. Source review cleared both the repair and separate auxiliary coverage ledger
before native retries. The previous PAL pass and failed NTSC originals remain hash-preserved
in separate directories; retry outputs cannot overwrite them.

Commands use `RUST_LOG=info` and
`PYTHONPATH=/tmp/ctennis-shared-core-python/lib/python3.12/site-packages`;
CPU differential also uses
`CTENNIS_PRIVATE_STATE_BEFORE=/tmp/ctennis-private-state-before/build/amiga/interfaces/enhanced/baseline-rally`.

```sh
python -m unittest discover -s tests/unit
python scripts/native_acceptance.py --plan --case history-cpu --case preview-cpu --case seek-sliced-cpu --case core-entropy --case core-shared-bytes --case private-state-cpu
python scripts/native_acceptance.py --start --campaign b50677c9dc314e998b365c346461eb28 --case history-cpu --case preview-cpu --case seek-sliced-cpu --case core-entropy --case core-shared-bytes --case private-state-cpu
python scripts/native_acceptance.py --plan --case tutorial-court-pal --case tutorial-court-ntsc --case core-entropy --case core-shared-bytes --case private-state-retained-pal --case private-state-retained-ntsc --case tutorial-hotspots-pal
python scripts/native_acceptance.py --start --campaign 5bd223ae5e594e8e80bba564843470f1 --case tutorial-court-pal --case tutorial-court-ntsc --case core-entropy --case core-shared-bytes --case private-state-retained-pal --case private-state-retained-ntsc --case tutorial-hotspots-pal
python scripts/native_acceptance.py --resume --campaign 5bd223ae5e594e8e80bba564843470f1
python scripts/native_acceptance.py --start --case tutorial-hotspots-pal
python scripts/native_metrics.py --require-runtime --record
python scripts/native_metrics.py --check
```

Current-serve PAL receipt SHA256:
`9b1be1aff9140d3c171416fad8279001f899540d0338cb8fbc1a1060a68ce690`;
NTSC `46a4351adca8fb496eeeb8afe7f5bca3fdb884b0e8f95629517155eadb239020`.
Long CPU preview/seek/private receipts are pinned in
[scripts/retained_private_extent.py](../scripts/retained_private_extent.py).
Retained PAL receipt SHA256:
`420a33168c96be145609770adaaf80147e785c698fdebc2ce3b0fdd7f1545ad7`;
NTSC `63fadae7e4be04d35d14e455e18d7253b6a1977da2f3d2ccf37ec2e3297a928d`.
Profile `5b9a90d38011c9d12e23b8f6f2eea47131b7d1d411da2699143fad0685fa69cd`.
Seven-case native campaign completed successfully with full acceptance false:
current-serve and profile reused exact compatible evidence, both retained cases and
entropy/shared closure checks ran fresh after coverage observer commit `86e5731`.

Resource record/check exit 1 for incomplete standard profile coverage; focused
checks do not fill the standard release-resource gate. Recorded static sizes and
missing/stale profiles are committed together. Raw campaign artifacts,
executable/listing/ROM/media remain outside Git.
Storage relocations verified every file before and after; no unique input removed.
The first synthetic precheck failures and older failed attempts remain retained;
none counts as a pass. No full native/release acceptance is claimed.

Independent reviewer `/root/native_receipt_review` cleared exact source and all
completed selected evidence: both native current-serve cases, both retained cases,
the profile and all six CPU proofs. It independently reconstructed literal state,
outputs, callbacks, IRQ ownership, loaded hunks, publication/media and cost streams,
and verified every consumed input/artifact binding. Root owns integration. User appearance review and full
release/cold-ADF acceptance remain gates. Production retained navigation and
publication are later work; these jobs are a bounded API fixture. No batching,
ratio arithmetic change, optional trails/sprites, Exit work or merge was performed.
