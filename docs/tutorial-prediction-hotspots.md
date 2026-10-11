# Prediction cost assessment

The supplied-A5 migration was subsequently approved and implemented. See
[the private-state integration result](tutorial-private-state-integration.md).
Measurements below describe the retained pre-migration product. The current
measurement and next-step recommendation are in
[the generation follow-up](tutorial-generation-results.md).

This is a measured proposal, not authorization for another runtime rewrite.
PR [38](https://github.com/rmtew/ctennis/pull/38) remains a draft pending appearance
review. The native product is `6f2828735c273258c0c0abdb577778f1e831a7ae`, executable
SHA256 `c543a695d9493254eb152cf34a093676c3c0c0dcd4df203d0ad105a5b97e3cb8`.
The already reviewed scheduler change reduced the fresh held endpoint from
1.068426 to 0.706545 provider seconds in PAL and 1.023953 to 0.699653 in NTSC.
Those are finite observations, not latency guarantees. No new gameplay change
was made for this assessment.

## Fresh measurement and its limits

Optional campaign `837fef4076ce47178827eefe734ece32`, observer commit
`52d87c18f3a044bfa5f9b4f5c3b2f660e2680a8f`, completed with the selected diagnostic
passing. It is **not full acceptance**. It used the actual unchanged executable,
OCS, 68000, PAL, 512 KB chip RAM, no slow/fast RAM and external Kickstart 1.3.
Retained evidence is under `build/tests/tutorial-hotspots-pal/`; campaign report
is under `build/acceptance/campaigns/837fef4076ce47178827eefe734ece32/`.

The runner uses real title/start/pause controls, initial held prediction, then a
physical D edit. It compares all 318 canonical bytes, 72 history metadata bytes
and 318 backup bytes at complete update boundaries; publication checks use the
actual completed native path, bank, sprites and prediction generation. Fresh D
to first actual held endpoint took **2,725,839 CCK / 0.768514 PAL seconds** in
this capture. Its phase and input differ from the earlier 0.706545 capture;
neither supersedes the other as a universal bound.

Actual emitted call-stack writes and matched RTS reads isolate **83 workers**
wholly contained in that fresh generation's request-to-endpoint window. Their
inclusive cost is **1,141,185 CCK**; maximum worker is **18,839 CCK**. These bus
spans include IRQ/contention and exclude pre-store/post-read instruction tails.
Exclusive categories partition that total exactly:

| Category | Bus CCK | Meaning |
|---|---:|---|
| Selection guard/admission | 236,836 | Full paused selection comparison |
| Copy/restore | 261,576 | State transfer and history metadata restoration |
| Core body own instructions | 31,989 | Body cost excluding descendants |
| Public preview own instructions | 57,427 | API/control bookkeeping |
| Other helpers | 553,357 | Includes physics, scene, score and audio descendants |

The **actual core-body subtree union is 475,365 CCK**, not 31,989. Inclusive
subtrees must not be added to the exclusive partition. There are 63 dispatch
bodies, 63 round polls, 63 result samples and 65 pad samples (two primes plus
63 continuation samples): 254 logical operations to the first held endpoint.
That endpoint computes one alternative; released prediction continues later.

| Function | Calls | Exclusive bus CCK | Inclusive bus CCK |
|---|---:|---:|---:|
| `game_preview_selection_unchanged` | 83 | 236,836 | 236,836 |
| `game_history_copy_state` | 252 | 224,966 | 225,363 |
| `game_ratio` | 147 | 85,669 | 85,868 |
| `game_preview_continue_one` | 252 | 48,853 | 562,180 |
| `game_scene_actor` | 126 | 33,778 | 44,938 |
| `score_export_fields` | 63 | 30,696 | 30,696 |
| `score_import_fields` | 63 | 30,645 | 30,645 |
| `game_audio_tick` | 63 | 23,192 | 24,460 |

The independent flat instruction profile covers the bounded capture plus commit
frames, including an old-generation tail and trailing work. It is deliberately
**not** labeled a fresh-worker-only profile or an inclusive call graph. It has
40 committed frames, 448,277 ordinary retired instructions, 448,316 encoded
samples, 2,818,734 charged CCK, 60,709 ChipRAM wait CCK and 859 IRQ CCK.
Every cost row is paired with its PC row; ordinary counts agree with every
frame's retirement count and totals with the profiler summary. The pinned
sampler has no explicit sample-drop counter. Legal maximum/split instruction
chunks fail closed as unsupported scope. Stop discards an uncommitted tail;
the last written frame is 469, four frames after the endpoint.

Some useful flat lexical regions (local labels stay in their enclosing region):

| Region | Instructions | Charged CCK | Chip wait CCK |
|---|---:|---:|---:|
| Selection comparison | 46,354 | 237,962 | 7,350 |
| State copy | 9,576 | 235,144 | 1,890 |
| Ratio arithmetic | 17,309 | 86,947 | 1,755 |
| Launch root | 397 | 1,460 | 73 |
| Timer reread/poll region | 59,580 | 357,882 | 9,220 |

The state comparison `CMPM.W`, branch and `DBRA` each execute 13,674 times in
that broader profile. Charged CCK per instruction is respectively 6, 4 and
5–7. The two bulk-copy `MOVEM.L` instructions execute 1,596 times each at
54 and 52 charged CCK. Some `top_pcs.source_mnemonic` fields contain the inline
local label rather than the opcode mnemonic; the instruction descriptions above
were checked against emitted opcodes and the native listing. Bus waits are
separately retained. These are emulator
measurements; operand-dependent physical 68000 timing has not been independently
audited against the pinned CPU model.

Written frame IDs skip 435 and 460: instruction retirement counts remain complete
across profiler poll intervals, but DMA totals cover the 39 nonpartial recorded
frame traces, not every physical field from 427 through 469.
Complete-frame bus ownership records CPU 1,094,947, idle 1,085,492 and bitplane
519,168 CCK. CPU waits attributed to bitplanes are 42,473, refresh 9,637, copper
1,968, sprites 1,367 and audio 794 CCK. Ownership is not instruction execution
time: a CPU instruction can execute internally without owning a bus slot.
Idle ownership and timer polling identify scheduling opportunity, but are not
automatically transferable worker budget. The capture has 198 complete callbacks,
maximum 54,879 CCK, minimum observed headroom 3,626.137 CCK, zero dropped
notifications. Fresh-window stack usage is 244 bytes; startup stack is unmeasured.

Independent source/evidence review reproduced all raw callback and worker
aggregates, both endpoint publications and every state readback; 96 frozen
state/metadata/backup tuples are invariant. All 400 evidence and 99 completion
hashes match. The immutable receipt SHA256 is
`4e918a2cec6b558cc44b0b9f4adac0bb8f81854a431da8affb6724550af428ea`.

Capture caps are 64 profile frames, 32 MiB profile files, 64 MiB uncompressed
RPC, 30 seconds of emulated PAL time, 1,024 callbacks and 4,096 boundary stops. Raw RPC used
39,371,599 bytes. Earlier campaign `f89b605c6f184d219f568a5b4ba61642` failed its
raw cap and remains preserved separately; it is not a game-check failure or a
pass. The successful observer omitted unnecessary startup stack logging and
restricted fresh stack reads to actual worker return coverage, with root-slot
and LIFO checks. Caps were not increased.

## Current architecture

[preview.s](../amiga/game/preview.s) advances the same deterministic native
core as live play and the isolated CPU runner. Absolute state symbols currently
give those routines one working core address. Each public step validates the
paused selection, loads the appropriate private 318-byte working state, advances
one to four logical operations, saves it and restores the paused canonical state
and 72-byte metadata before yielding. It does not copy the recorded history.
It **already keeps the working state loaded across operations within a call**;
saves occur at yield or owner transition. Copies reflect the present interface,
not an inherent requirement of prediction.

Held and released contexts start from the actual action context. Retained future
operations preserve recorded envelopes and logical arguments while overriding
human B1; after retained future ends the genuine core/AI continues with synthetic
round/pads/result/tick operations. AI is reactive. Same seed does not guarantee
paired randomness when alternatives change random-call order.

Existing incoming-prefix reuse, fully-ready cache reuse, edit coalescing and
held-first endpoint publication are already implemented. Paths stop at an actual
landing/net/out/contact/lifecycle outcome or the 256-point/dispatch horizon.
They do not simulate an unbounded future match.

Hardware audio/display sinks are isolated already. Their state dependencies are
still real: [result_audio.s](../amiga/game/result_audio.s) gates round progress
on `AV_DONE`; core service advances clocks and audio; [scene.s](../amiga/game/scene.s)
updates controls/animation clocks and `courtY`. The projected path also uses
actual visibility/contact/flight state. Removing these entire routines as cosmetic
would change results. Their dependencies can be separated through a deliberate
shared-core refactor.

## Ranked proposals requiring review

The subsequent [private-state scope review](tutorial-private-state-scope.md)
finds a practical A5 strategy and recommends supplied private addressing as the
next structural candidate. Its concrete scope supersedes automatic deferment
behind the smaller changes in this initial ranking. Implementation still requires
user approval.

| Rank | New candidate | Gain evidence / complexity | Correctness requirement |
|---|---|---|---|
| 1 | Compare 79 longwords plus final word instead of 159 words | Directly targets the largest guard; small change, gain unmeasured | Compare all 318 bytes and all 72 metadata bytes; preserve equality result and early rejection; even alignment, no overread |
| 2 | Larger owned jobs or one validation/swap per callback job | Guard plus copy are 498,412 CCK, 43.7% of measured worker cost; medium change | Preserve fresh input/preemption, cancellation/generation checks and restoration at every external boundary; measure worst operation plus publication tail |
| 3 | Core accepts a private state address base | Removes global swaps structurally; larger interface change | Audit every writable global, alias, sink and register use; same actual core for live and standalone execution; full differential proof |
| 4 | Exact ratio arithmetic improvement | Ratio is a measured 85,669 CCK worker hotspot; moderate proof burden | Preserve byte overflow, zero divisor, rounding, clobbers and live flags; exhaustive input-domain comparison before proposing `DIVU` or other replacement |
| 5 | Extend existing action/prefix cache to a verified partially completed base | Likely useful for repeated historical-return edits; this serve has little incoming prefix | Cache all dependencies and RNG position; reject invalid history, action, controls and generation; no seed-only equivalence claim |
| 6 | Factor shared ball/contact kernel and a lighter predictor wrapper | Potential architectural saving; high dependency/proof cost | Live and prediction call the same kernel; retain necessary AI, lifecycle, audio-completion and projection state |
| 7 | Exact analytic segments / small tables | Speculative, highest equivalence risk | Prove discrete rounding, overflow, contact order and RNG call order; retain event termination already present |

No percentage or end-to-end gain is promised. Deleting all measured guard/copy
cost would remove about 0.1405 PAL seconds of worker bus spans, not necessarily
that much wall latency. Admission, callback cadence, DMA and publication can
quantize the outcome. Four public calls per callback is a cap, not an established
bottleneck. Larger jobs must be measured against the actual remaining timer and
worst transition, not typical rally cost or aggregate headroom.

Private addressing needs an explicit register/access strategy: no assumption that
A6 or another register is available across current routines/library calls. Existing
selected/edited/held/released buffers already occupy four 318-byte contexts;
additional code, context, stack and cycles must be measured. Full ratio tables
over three byte inputs would exceed 512 KB by themselves. The launch-root loop
is only 1,533 total CCK in this broader capture; optimizing it first is low value.

## Tooling and first proof

The build pins vasm 1.9d with `-m68000`, hunk output and a native listing. It
already emits some short BSR forms. Global speed peepholes are not a proof:
vasm options can change flags or read/modify/write behavior. Current output does
not use `-linedebug`; line information alone would not supply valid unwind CFI.
Pinned Copperline source `e65a958` supports instruction samples, cost metadata
and frame DMA ownership, used here without invented stack unwinding. See official
[profiling](https://copperline.dev/docs/profiling/) and
[debugger](https://copperline.dev/docs/vscode/) documentation; newer advertised
features must be checked against the installed pin. External m68k-lint/68kcounter
are possible static reviewers, not installed or relied on for these measurements.

The recommended first small proof, after user review, is the complete longword
selection comparison. Require mutation rejection at every byte of the 390-byte
state/metadata selection, different/poisoned working state, and unchanged complete
state, events, cursors, preview paths and RNG positions through actual CPU runs.
Then compare bounded PAL/NTSC fresh input, cancellation, ownership transitions,
worst callbacks and publication tails. Record code bytes, state bytes and worst
cycles alongside typical rally observations. No narrow hash substitutes for
completeness. Larger job amortization follows only if this leaves meaningful cost.

The integration owner implements only the reviewed choice; the parent coordinates
an independent source/evidence reviewer before merge. Private-address/core-kernel
architecture and changes to cache/branch semantics require explicit user review.
PR38 appearance, broader resource coverage and the full release gate remain
separate outstanding work. No sprite opt-ins or branch runtime were added here.
