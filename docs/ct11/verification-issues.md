# CT11 verification issues and proposed phase contract

Evidence head `c5f4767e04dc7f29d9f7864c4f68a07f644f59ee` completed all 23 planned commands: 20 passed and three failed. Raw failures remain in the private ignored fresh-checkout receipts; PR16 records their artifact/report hashes. Neither failures nor old receipt timestamps are rewritten as passes.

## Synchronous title construction: open, contract proposal not adopted

Cold one-player ordinary lifecycle completed 11372 callbacks; two-player completed 23320. The six deadline failures in each are synchronous first/returned title construction and the next two catch-up ticks. First construction took203740CCK cold and203482CCK host; the native merged50ef762 artifact took203250CCK in a bounded first-title comparison. Difference is below0.25%, with the same over-three-tick limitation. This is not a complete baseline lifecycle comparison or final binary identity claim.

The existing strict guard remains failed. Active-play maximum completion phases were56486.814CCK and56695.687CCK against interval59191.137CCK. Exact completed scene/bank association, publication windows, loaded bytes and allocation stability passed. Pre-Exec chip-pool bootstrap usage remains unmeasured.

Proposed review boundary: classify construction by actual calls to `prepare_title_display` / returned-title preparation, not by broad lifecycle values or a time threshold chosen from a failing sample. Record entry/exit CCK, construction work, number of elapsed native deadlines, backlog drain and publication epoch separately. A construction phase must freeze gameplay and score advancement, preserve audio/input policy, and publish only a completed scene within the existing sprite/Copper windows. Resume the ordinary timeline only after construction completion and backlog drain; retain uninterrupted counter/event accounting across the boundary. Do not omit the construction or catch-up callbacks.

All advancing gameplay retains the current exact fractional clock, quantization allowance, next-deadline completion, no missing/duplicate events, completed-bank association and PAL publication windows. Pausing or phase-resetting the product timer is a product change, not a test-contract adjustment. A separately bounded setup budget needs independent approval/evidence; no replacement setup budget is invented from203740CCK. If the reviewer requires one-tick completion even during setup, use a focused title preparation fix and repeat the relevant measurements. No contract change or timing rewrite is adopted in CT11.

## Enhanced restart observer transfer

The inherited `game_observe_pre_tail` hook is skipped by the enhanced title/menu path. It jumped11444→13310 and could not command reselection. Enhanced `ui_return_title` calls `game_begin_title`, clearing restart context, so legacy restart-sound lifecycle9 is not the enhanced restart contract.

The focused observer uses `simulation_update`, the uniform boundary after the previous update has completed and before the next sampler. Consecutive native counters include every menu callback. Release/repress happens during selection-held lifecycle3 while the physical selection key remains held: release at30, sample31, repress50, sample51, selection release80. Existing exact raw/pressed/released/latch packets and independent continuously-held-P2 exclusion are retained. Owner assignment is checked after the first active update, because selection itself only changes lifecycle. Audio checks retain returned-title mute and emitted ordinary new-match sound after enhanced reselection; this is not a claim about a legacy restart intro.

A private compiled control skips actual held-action retirement during selection. The unchanged release assertion must detect the stale latch. Product code/assets are not modified. Final focused outcomes and exact head are recorded in PR16; title cadence failures remain open.
