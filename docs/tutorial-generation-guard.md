# Prediction generation and ownership guard

Richard selected an incrementing generation guard after the supplied-A5 change.
This bounded change replaces the three preview byte comparisons (warm-cache
request, worker entry, completed result), using the existing 32-bit
`game_preview_generation`. It adds no state bytes and changes no core algorithm,
seek identity comparison, worker admission or rendering ratio.

The old helper compared selected simulation318 and history metadata72. Those
checks detected unversioned writes as well as stale selections. The replacement
rejects a mismatched generation and requires frozen history mode2, no active
preview/seek body and no history replay. Main-loop entry points are the only
writers of prediction validity. The presentation IRQ preserves A5 and writes
presentation/hardware fields only; it does not change selection or generation.
An IRQ cannot run a preview/history API. No worker owner survives a public yield.

## Mutation audit

| Change | Controlled entry and existing invalidation |
|---|---|
| Recording initialization/reattach, including failed attach | `history.s:game_history_attach` invalidates preview and seek job; records/checkpoint/attempt eviction only run in recording mode1. |
| Tutorial or physical pause entry | `game_history_freeze` saves live state, enters mode2 and invalidates both jobs before any request. |
| Selected moment | Successful synchronous seek invalidates both jobs; sliced seek begin retires the preview before working, commit retires again. Failed seeks are atomic and preserve existing ready results. |
| Seek cancellation | Begin has already retired previews. Cancel retires the seek job and cannot restore old selection. |
| Edited X/Y, selected attempt or action alternatives | Accepted `game_preview_request` increments generation before preparing new contexts. Warm reuse still checks ordinal/kind/end/origin. Both held/released variants belong to this generation; switching the displayed variant consumes a precomputed alternative and does not mutate prediction inputs. |
| Cancel | `game_preview_cancel` increments generation, clears published counts/cache and retires active ownership. |
| Resume/tutorial exit | `game_history_resume_latest` restores live state and invalidates both jobs before physical input reconciliation or dispatch. Menu close is presentation only. |
| Live logical state, scene/audio clocks, held/edge input | Nine public wrappers reject live calls while frozen unless the history replay owner is set. Private preview bodies write their A5 context; sliced seek restores selected state before returning. Physical sampler/presentation mutate separate adapter fields. |

The existing active3 exception is request-owned oldest-checkpoint restoration:
it executes zero logical operations, temporarily replaces canonical state within
one synchronous request and restores selected318/history72 before returning.
It neither publishes nor yields. No new untracked selection writer was found;
source and bus-write audits in the supplied-A5 proof remain applicable.

Generation is never reset by a new match/attach/resume. Request rejects values
at or above `0xfffffffe`; cancel may advance to `0xffffffff`; invalidation
saturates there, clears status/counts/cache, and requests remain disabled until
process restart. There is no wrap or reuse of an old token. Invalid requests do
not increment it. The last accepted request uses input `0xfffffffd` and issues token
`0xfffffffe`, which can still complete and publish. Worker/result guards reject
only terminal `0xffffffff`.

## Validation and scope

Keep the complete byte comparison as an explicitly called PREVIEW_DEBUG diagnostic,
without calls from shipping worker/request/result paths. Test deliberate
canonical/history corruption against that diagnostic and full preserved-image
assertions; a generation counter does not detect arbitrary memory corruption.
Keep poisoned contexts, full318/ordered outputs/cursors, stale/cancel/edit/seek/
resume/exhaustion (including last-issued token) controls and per-write isolation audits. Add owned/replay entry
rejection controls. Re-run affected CPU and current-serve PAL/NTSC; complete the
already planned retained cold4/cached2 PAL/NTSC fixture at the same product head.
Compare finite callback and endpoint costs with the preserved supplied-A5 product;
no universal timing bound or production retained-navigation claim follows.

Root owns implementation/integration. `/root/native_receipt_review` independently
reviews this design and exact source before execution, then completed evidence.
PR38 remains draft/unmerged pending appearance review and later release gates.
