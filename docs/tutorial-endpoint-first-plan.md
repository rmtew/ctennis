# Endpoint-first integration decision and first proof

The approved priorities are player placement first, normal ball sprite motion,
and optional incremental path filling. Dense samples are not a reason to delay
an independently exact endpoint. This proposal changes readiness/publication;
it does not change real incoming contact, create contact at the recorded tick,
or permit a future opponent response. No significant runtime rewrite has begun.

## Current measured cost boundary

Independent source/receipt review of PR41's fresh-D intervals gives:

| Nested measurement | PAL CCK | NTSC CCK |
|---|---:|---:|
| Request to actual human contact hook | 2,014,960 | 1,675,264 |
| Contact hook to first endpoint publication | 631,282 | 611,302 |
| 69 original ball calls, including launch and 68 outgoing phases | 52,000 | 51,890 |

The first two intervals partition the measured 0.746/0.639-second request to
publication. Ball calls are nested within those intervals; do not add them to
wall time. On PAL, 126 public steps consume 668,036 CCK; 52 active ticks consume
300,944, 123 appends 21,650, 129 owner restores 42,771 and 127 progress-returned
calls 70,328. These are nested observations, not mutually exclusive totals.
Contact resolution dominates the delay (~0.568/0.468 s); outgoing arithmetic
costs ~15 ms while its admitted slices/publication occupy ~0.178/0.171 s.
These are one combined incoming/edit sequence, not directly comparable to
earlier serve-only timing. Native entropy runs are not paired RNG experiments.

## Source-grounded plan

1. Keep immediate player placement publication in `tutorial_tick` and renderer.
   Continue the exact recorded incoming dispatcher through actual human contact,
   including clocks, player phases, held/edge inputs, AI/RNG and service tails.
   A miss publishes its actual terminal projection with no outgoing marker.
2. At the complete human launch boundary retain an immutable private launch
   state per alternative. Query a separate private endpoint scratch. PR40's
   `landing_query` is currently test-only and performs synchronous fallback up
   to 256 phases; a measured rejected fixture costs about 110,000 CCK, exceeding
   a normal callback budget. It cannot enter the tutorial unchanged.
3. First add/prove a bounded try-fast interface: accepted produces original
   event-applied terminal full state, endpoint eight bytes, phase count and
   outcome; rejected supplies a diagnostic reason and leaves all 318 input
   bytes unchanged. Both shipping and standalone must use that same helper.
   Keep the existing exact diagnostic query/reference proof. Measure the real
   human launch corpus before selecting admission/dispatch policy. A cheap
   short scan must avoid paying query overhead on short/rejected flights and
   must count any scanned prefix in the 256 cap with no repeated prefix.
4. Separate endpoint readiness from dense-count readiness. Current
   `tutorial_progress_qualify`/mode-one marker rendering uses `paths[count-1]`
   and interprets an outcome as a stopped complete alternative. Do not inflate
   count or mark a partially filled path complete. Add generation-bound endpoint
   data/readiness, keep actual terminal state isolated, and publish the exact
   marker while subsequent worker slices fill dense samples with original ball
   ticks. Renderer remains a reader; generation change discards both products.
5. Normal sprite playback consumes only actual available samples at the normal
   cadence; it must never outrun readiness or jump to a fabricated point. Event
   sample/dwell/repeat semantics remain exact. Incremental original ticks are
   the first integration: they save endpoint publication delay, not total dense
   CPU cost. Rejected/net/out/wrap cases remain sequential exact workers.
6. A later accepted-interval point-at-time proof can restore the immutable launch
   seed, set actual `G_STEP=n-1`, and invoke original `game_advance_ball` for
   `1 <= n < terminal_phase`. Conservative guard must prove no earlier intrinsic
   event. Sample zero remains complete actual launch projection; terminal uses
   the actual query post-event state (bounce resets/damping), not a polynomial
   extrapolation. This reuses the original routine rather than a separate model.

## Gates and ownership

Integrator owns the bounded helper/corpus proof, readiness protocol and native
measurements. Parent coordinates independent source and evidence review before
merge. First small proof is try-fast success/rejection neutrality on actual
post-human-launch states, including maximum guard cost, full state, terminal
priority, cap accounting and stale generations. Record state/code bytes.

Measure on the same controlled incoming recording/actions: request to contact,
contact to endpoint publication, placement publication, time to required normal
sprite sample, eventual dense-fill completion, largest complete fresh-input and
transition callbacks, minimum headroom and whole-machine RAM. Report short,
accepted long and every rejection reason separately, including dispatch/guard
costs and prefix scans. Existing serve-only receipts do not certify this flow.

Appearance, affected mandatory preview proofs, standard metrics, cold stripped
ADF and full release holds remain. No uploads, merges, scheduling changes or
optional trail/sprite experiments are included. This concrete plan precedes a
larger runtime rewrite; correctness migration proceeds independently.
