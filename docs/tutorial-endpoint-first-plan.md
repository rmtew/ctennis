# Endpoint-first integration decision and first proof

The approved priorities are player placement first, normal ball sprite motion,
and optional incremental path filling. Dense samples are not a reason to delay
an independently exact endpoint. This integration changes readiness/publication;
it does not change real incoming contact, create contact at the recorded tick,
or permit a future opponent response. Bounded endpoint readiness is in focused validation; existing scheduling reserves remain.

## Current measured cost boundary

The completed focused correctness campaign `9070c56648064349926818a8e21a16f0`
measured product source `350eabb`. Its retained fresh-D matched intervals are:

| Measurement | PAL CCK | NTSC CCK |
|---|---:|---:|
| Request to actual human contact hook | 1,910,303 | 1,674,866 |
| Contact hook to actual COPJMP endpoint publication | 595,197 | 613,125 |
| Whole request to publication | 2,505,500 | 2,287,991 |
| Public worker interval union, nested | 666,662 | 662,978 |
| Original logical-entry/ball subtree union within workers, nested | 411,941 | 415,889 |
| Original post-contact ball subtree, nested | 51,506 | 51,939 |

Total elapsed is 706.4/639.2 ms; request-to-contact is 538.6/467.9 ms.
Workers account for 26.61%/28.98% of elapsed; original logical-entry subtrees
account for 16.44%/18.18%. The latter includes recorded indirect entry wrappers,
not just arithmetic. Worker residual is 10.17%/10.80%. Post-contact ball work
is only 14.5 ms, or 8.65%/8.47% of the post-contact interval. The contact hook
precedes the remaining original dispatcher tail: this interval is not purely
outgoing work. Nested costs must not be added to elapsed time.

Simulation-update callback spans occupy 48.27%/50.25% of elapsed. Outside those
spans, 1,296,034/1,138,301 CCK remains unassigned polling, IRQ, bus, idle or
admission time; the trace does not establish that it is scheduler waste.
Last completed worker to COPJMP is 76,130/91,699 CCK (21.5/25.6 ms), likewise
not wholly attributable to rendering. Competing released-flight work is minimal
before the first held marker (zero released outgoing phases). This is one live
entropy run per region, not a paired experiment or a universal timing bound.

Source policy in `tutorial_tick` admits at most **four** public slices per
callback (`D6=3` plus `DBRA`), each with four operations or fallback two.
Every yield rechecks remaining time. All nonserve continuation statuses, including historical/current incoming
PRIME/RESOLVE, require 10,000 E-ticks for four or 7,000 for two; resolved current-serve
HELD/RELEASED requires 7,000 or 5,000. READY/footer/general work reserves 10,000;
pure presentation and render phases 1/4/5 reserve 5,000. Placement/menu drawing
exits without worker continuation, and a newly qualified endpoint makes placement
dirty and leaves publication for a separately admitted pass. Animation/footer can
consume headroom before admission. These are artificial policy ceilings, not
measured safe replacement budgets. Observed 120/107 worker steps across 42/38
callbacks do not prove the four-slice ceiling binds.

The bounded-helper proof below first establishes cost and correctness without
changing these policies. Before changing admission or readiness, distinguish
actual incoming work, guard/copy overhead, reserve refusals, placement exits,
variant readiness and publication with contextual matched traces. Arithmetic
alone cannot remove the measured incoming delay; no unrelated scheduler rewrite
or 110,000-CCK synchronous fallback is authorized by this cost split.

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

## Bounded-helper preflight (not callback acceptance)

The linked helper has no shipping caller yet. A finite CPU preflight exercised
42 complete seeds (20 actual post-dispatch launches, including edited and
exchanged-end cases, and 22 declared initial ball domains), in standalone,
relocated standalone and emitted native code. Declared cases used all 32 incoming
CCRs; natural cases used 0 and 31. Accepted full318/point/phase/outcome matched
uninterrupted original ball instructions; rejection preserved full318, source
and canonical state, and executed zero original ball fallback calls. Eight
excluded edited cases require an actual no-contact terminal flag, rather than
merely reaching a cap or exhausting the recording.

Actual shared helper is 884 code bytes, zero static state bytes, with two verified
external PC-relative calls; normalized SHA256 is
`8e0925f3122ad2a8ca8ce9bca7f5d2a47379720a041e72d3387080a641e3fbc0`.
The original 17,606-byte normalized core is unchanged. Maximum observed copy318
plus helper cost is 11,918 CPU cycles; maximum observed stack use is 118 bytes.
These CPU measurements exclude native chip-bus waits and IRQs and do not justify
a callback reserve. Guards 5 (phase-wrap) and 12 (defensive bracket miss) were not
observed; no intermediate state was injected to manufacture their reachability.
The diagnostic wrapper's 21 declared cases also matched, but nesting adds another
48-byte frame and 44-byte register save: its old stack/cost figures are historical
and require fresh reporting. Native timing and endpoint/readiness integration
remain pending. `scripts/run_landing_try_proof.py` provides manifest-bound evidence;
unreceipted preflight alone does not certify a committed product.

## Native diagnostic costs and minimal admission proposal

At source `afd8eda93aff77c9ec99dcfc1dafe401196803b5`, isolated PAL/NTSC
helper-plus-copy probes passed 84 jobs each (42 initial seeds, two samples each).
PAL receipt `0c443ce48ed143ac9b5ae21fd8182303` and NTSC receipt
`a5dfc8c88e11480ea28dd07ef0d548a0` retain original raw evidence; no drops were
reported. Maximum copied-helper span was 6,062/6,141 CCK, both accepted-short.
PAL natural long cost at most 4,865 CCK against 52,698 for its original scan;
edited held long at most 4,968 against 52,003. Accepted-short query cost 6,062
against only 3,094 for its scan. The fixture deliberately does not preserve
production cadence, and two samples do not establish a worst-case bound.

The minimal integration therefore retains the actual complete launch per
alternative and permits the ordinary dense worker to run its first four original
ball phases. A flight that stops in that prefix never pays query overhead.
For a still-running flight, a separate generation-checked public attempt copies
that immutable phase-zero launch into shared private scratch and invokes only
the bounded helper. The dense continuation is neither rewound nor advanced by
this attempt, so its four phases remain counted once within the original 256
cap. Rejected attempts leave the dense worker sequential. Accepted endpoint
readiness/point/phase/outcome does not imply dense completion or increase count.

Admit one such attempt alone with the existing general 10,000-E-tick reserve,
then yield; publish on the existing separately admitted presentation pass.
This is a hypothesis to validate on complete fresh-input callbacks, including
launch-copy and publication transitions, not a reduction of existing reserves
or an unrelated scheduler rewrite. Two immutable318 launches plus one318 scratch
and generation-cleared metadata are proposed; measure emitted storage/code after
integration. Normal playback waits for actual available samples, and terminal
dwell/repeat requires the real dense stopping outcome.

## Implemented readiness protocol (validation in progress)

`game_preview_endpoint_pending` checks generation, variant, frozen selection,
seek inactivity, valid immutable launch, unfinished outcome, no prior attempt,
and four through255 actual outgoing phases. `game_preview_endpoint_try` repeats
those guards, makes one bounded copy/query, and publishes separate eight-byte
point, outgoing phase and outcome. Accepted query with an inconsistent terminal
phase is discarded with distinct reason15; proof requires that branch to be
unreachable under intact seed/dense state. Neither API changes dense318, counts,
status, stream cursors, original events or phase accounting. Cancellation/history
mutation clears seed-valid, attempted and endpoint-ready flags. Shared terminal
scratch can be reused; later APIs must reconstruct from the immutable launch if
they need full terminal318 after another query.

The actual standalone/native endpoint module matches482 normalized code bytes
(32 relocations, six verified external branches), SHA256
`2c2ada68494407db11a2c7cf2eca5ac981a0d975b85a9e472b5389a3ad10f6c7`.
Measured preview storage is10,974bytes, metadata150:988bytes added, consisting of
954private state bytes and34metadata bytes. Complete core remains318 and history
metadata72; no checkpoint/input format change is introduced. Renderer marker mode
reads the separate endpoint; dense sprite mode reads only available samples.
Dwell/repeat requires actual dense stopping outcome. Full API/callback/native RAM
acceptance is pending; prior helper-only costs do not certify this integration.
