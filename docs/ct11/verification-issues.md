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

## Representative UI setup measurement exposes timer-wrap debt

The targeted observer identifies only the actual `ui_render` dirty-clear instruction through its ready write, with exact CCK boundaries and gameplay/score write watches. Menu navigation, player-count changes, Help, Controls, Credits, page wrapping and page exit are measured separately. No general title-lifecycle exemption exists.

The review-only candidate bounds are four native ticks for a menu rebuild and eight for a page rebuild, with at most six/ten subsequent non-advancing recovery callbacks. These are explicit responsiveness envelopes, not exact observed durations or adopted acceptance. Measured menu regions are about190000CCK; Help about359000, Controls324000, Credits291000. The proposal preserves all raw deadline failures and applies the existing clock/publication rules to every other callback and all advancing gameplay.

The proposal itself FAILS bounded recovery for the longer page changes. The 16-bit free-running timer spans327680CCK; Help's complete update exceeds that sampling range. Subsequent callbacks retain a whole-wrap wall-time deficit rather than draining it. After the tested sequence the deficit is approximately three wraps. Rebasing the observer would conceal this loss. A separate setup clock domain or product timer fix requires explicit review; neither is implemented, and no phase diagnostic is promoted to aggregate acceptance.

The same bounded menu/help sequence on the frozen merged baseline artifact also
fails recovery at callbacks223,277,331,391,446 and506 and ends about three timer
wraps behind. Baseline comparison is a native executable diagnostic, not an
original-system oracle. No baseline assets or source media are added to the
maintained tree. Final measured bounds/cases are attached to PR16.

The enhanced restart audio contract distinguishes cleanup silence from sound
caused by a fresh serve. Native enhanced reselection calls `game_new_match`,
which resets voices and does not queue the legacy startup pair. Returned-title
and restart-cleanup windows remain strictly silent; the fresh-serve window must
emit native sound. All intervening update counters remain consecutive, including
six post-serve capture updates. No product audio change is made.

## Final independent review and follow-on timing repair

Independent final review cleared the behavior-neutral CT11 cleanup at `7a9f5f2ac4e87f55cba796f34ac74512f85a30ff`; the parent accepted cleanup with the inherited timing limitation retained. Cadence acceptance remains failed. Raw failed receipts are preserved, and no proposed setup contract, setup exemption or observer-origin switch is adopted. Final focused verification completed 17 commands (16 passed); the setup measurement command passed collection, while its recovery proposal failed.

The reviewer independently confirmed status-2 visible and expired rasters against 384 native asset pixels, the wrong-pointer fault with 266 differing pixels, 20 host tests, and the corrected restart observer source. The Help sequence measured 564 callbacks and ten construction regions: 354 raw timing errors, 280 outside setup and six recovery failures. Help construction took 359305 CCK, about 0.1 seconds, crossing the 327680 CCK modulo timer range and losing elapsed time. Later gameplay resumes normal tick spacing: 67 later active callbacks were observed, with the last 50 gaps spanning 58733–59697 CCK and maximum work 24355 CCK. Approximately one million CCK of absolute epoch debt remains. Normal-rate recovery does not erase that debt or turn the strict cadence receipt into a pass. Unchanged product timing/source, the merged-baseline reproduction and these recovery observations support the scoped cleanup disposition only.

The parent will manage a finite follow-on timing repair before cosmetic polish:

1. Make elapsed accounting wrap-safe so long UI updates cannot discard whole timer wraps. Preserve the continuous observation epoch and raw callback accounting.
2. Bound UI construction work between timer and input samples, starting with menu/Help/Controls/Credits transitions. Preserve exact completed scene/bank association, publication windows, input packets and audio cleanup.
3. Repeat the bounded menu/help sequence and then the relevant gameplay cadence checks, demonstrating accounted elapsed time and bounded recovery without changing observer origins or hiding failures. Reuse existing fixtures and observers rather than introducing a large framework.

This is follow-on scope, not an implemented CT11 fix or an adopted timing budget. The documentation-only disposition commit does not rerun runtime tests or promote earlier evidence to a new-head runtime pass.
