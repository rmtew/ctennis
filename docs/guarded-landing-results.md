# Guarded landing query: isolated prototype and integration decision

The test-only 68000 prototype computes the first **intrinsic ball event** from a
caller-owned private state. It preserves net reflection and outside outcomes;
it does not ignore them to force a landing. Shipping gameplay, renderer, input,
audio, history and reactive preview source are unchanged. No match tick is
skipped. PR38's appearance/merge hold and the separate reviewed PR39 increment
remain intact.

Prototype source commit `18675d343a086ad1e44487c9e51607b73cda5ce8`;
native observer correction `2483f833919d92b3556cbb39e277d28de7c1eae5`.
The [reviewed proof](ball-query-math-proof.md) supplies conservative guards,
exact integer bounds and event priority. This prototype is a measured geometry
primitive, not approval to replace the interactive preview.

## Interface and algorithm

`scripts/fixtures/guarded_landing.s` is assembled beside the actual shared core,
and into a generated diagnostic native overlay. It is absent from shipping
includes. A5 points at a complete caller-owned private 318-byte state; the query
derives its private A4. D4–D7 and A0–A6, including caller A4/A5, are preserved;
D0–D3 and CCR are scratch, and the stack balances.

| Return | Meaning |
| --- | --- |
| D0 | 0: capped/no event; 1: launch; 2: inactive (including inactive-out); 3: bounce; 4: net reflection; 5: outside |
| D1 | Actual ball phases consumed, 1–256; this is not a match-history tick count |
| D2 | 0: accepted fast path; otherwise the named conservative guard rejection |
| D3 | Exact candidate point checks, at most six |

The fast path requires phase zero, nonnegative initial height, active flight
without pending launch, Y magnitude at least four, no unresolved special-net
reflection, ordinary displacement/height products, no height-factor wrap,
no screen clamp/wrap and court coordinates inside the rectangle for the whole
bracket. Both signed directions are supported. It validates the entire interval
before mutating the private packet. Exact endpoint/vertex-neighbour extrema
check the height quadratic; monotone endpoint checks bound court coordinates.

Two eight-decision integer searches find the same ascending roots as the
reviewed corrected-square-root formula. Positive thresholds make the predicate
monotone even though the earlier quadratic arm can descend below zero. The
inclusive root bracket contains at most six phases. The prototype calls the
actual `game_advance_ball` at those points and applies the first bounce through
the actual `game_bounce`, without a redundant seventh advance. It preserves
court classification, base resets, damping and player animation bytes.
A defensive bracket miss restores all seven bytes an advance can write before
falling back. Phase overflow and bracket-miss guards are defensive and were not
observed; the valid byte height/Z domain already bounds the root below 256.

Every rejection uses the original `game_ball_tick` once per phase, stopping at
the first launch/inactive/bounce/net/outside event or the 256-phase cap. Outside
is recognized before reflection classification; net reflection flips the Y sign,
whereas bounce preserves it. At byte phase wrap, exact base geometry classifies
low speed → bounce → net → bounds priority before applying the actual tick.
The capped status does not authorize advancing an entire match by 256 ticks.

## Completed proof and useful domain

Selected resumable campaign `7587a49538744c76ba01794dbb5123c9` completed PASS:
236 host tests, `guarded-landing-cpu`, `guarded-landing-pal` and
`guarded-landing-ntsc`. Full release acceptance is not established.

The CPU proof compares all 318 bytes against uninterrupted calls to the emitted
ball routine, event kind, phase count, guard reason, returned registers and owner
isolation. It is a ball-only arithmetic/packet proof, not a separate match model.
It checks 131,072 root calls over every byte H/Z pair and both thresholds;
62,496 isolated flights; 997,128 wrap/boundary cases; 21 declared native fixtures;
and 672 fixture calls spanning every incoming CCR value with poisoned D0–D3.
There are 21 explicitly traced fixture probes plus the CCR and retained queries;
exhaustive loops do not claim exhaustive memory-access tracing.

The isolated grid has 23,309 accepted cases (37.30%) and 39,187 fallbacks (62.70%):

| Grid guard outcome | Cases |
| --- | ---: |
| accepted | 23,309 |
| court-y-bound | 4,204 |
| screen-clamp-or-wrap | 11,672 |
| height-quotient-overflow | 752 |
| displacement-overflow | 12,512 |
| height-factor-wrap | 2,304 |
| court-x-bound | 7,743 |

These selected parameter frequencies are not gameplay probabilities. Genuine
retained PAL and NTSC streams each replay 818 logical operations unchanged,
including the selected native snapshot at operation 552. Each yielded five
unique phase-zero parameter tuples seen by the advance hook: two accepted,
one inactive, one screen-clamp/wrap rejection and one court-Y rejection.
Each captured complete state was independently copied and compared through the
query. The native benchmark also includes phase-zero unresolved net reflection,
already-contacted net, pending launch, inactive, low speed, negative zero,
nonzero phase and wrap event-priority cases.

Across all 23,321 accepted cases in the selected CPU sets, 21,044 were faster and
2,277 slower. Savings range from **−5,280 to +139,534 CPU cycles**, including
all guards/root work. Accepted query costs were 7,268–14,194 cycles; the largest
query cost across the entire selected mix was 241,478 cycles, versus a largest
reference cost of 211,674. Independent maxima are not a paired cost delta.
These CPU figures exclude Amiga contention and are not whole-domain worst bounds.

## Actual PAL/NTSC costs, including fallback

A generated test-only callback hook runs eight samples of each declared fixture:
168 query/reference pairs per region. Each pair starts from identical declared
initial private states. The reference phase count is obtained from an
uninterrupted emitted CPU scan before fixture assembly; the native reference
then executes that many original ticks, with no intermediate state injection.
Both native endpoints must equal each other and the complete CPU endpoint.
The hook preserves the interrupted registers/SR and protects canonical state,
history metadata/buffer, preview/seek storage and canaries before/after every job.
Actual loaded hunks and PAL/NTSC video/cadence selectors are verified.

The observer measures emitted call-address stack stores through matching RTS
stack reads. These elapsed CCK include contention/IRQs and exclude pre-store and
post-read CPU tails. Reference and query run sequentially at different bus phases;
medians describe finite samples. The diagnostic can exceed a normal callback's
budget while scanning; it does not demonstrate ordinary gameplay cadence,
interactive input latency or a production endpoint-publication improvement.

| Fixture | PAL reference → query median CCK | NTSC reference → query median CCK |
| --- | ---: | ---: |
| accepted-short | 2,736.0 → 5,191.0 | 2,716.0 → 5,200.0 |
| accepted-long | 59,240.5 → 3,887.0 | 59,508.5 → 3,886.5 |
| court-y-bound | 4,808.0 → 7,927.0 | 4,801.0 → 7,935.0 |
| screen-clamp-or-wrap | 31,193.0 → 36,925.0 | 31,326.0 → 37,082.0 |
| height-quotient-overflow | 15,773.5 → 19,867.0 | 15,792.5 → 19,902.0 |
| displacement-overflow | 65,661.0 → 74,476.0 | 65,922.5 → 74,775.5 |
| height-factor-wrap | 97,767.0 → 109,814.5 | 98,183.5 → 110,364.0 |
| court-x-bound | 3,998.5 → 6,893.0 | 4,011.5 → 6,923.0 |
| negative-height | 25,218.5 → 27,713.5 | 25,123.5 → 27,960.0 |
| special-net-reflection | 1,114.0 → 1,532.5 | 1,116.0 → 1,536.0 |
| net-already-contacted | 28,648.0 → 3,866.0 | 28,768.0 → 3,873.5 |
| low-speed | 769.0 → 1,111.0 | 775.5 → 1,116.0 |
| negative-zero | 778.5 → 1,117.5 | 780.0 → 1,121.5 |
| nonzero-phase | 24,904.5 → 27,748.0 | 25,088.5 → 27,816.0 |
| pending-launch | 201.0 → 420.0 | 203.0 → 421.5 |
| inactive | 110.5 → 330.0 | 110.0 → 329.5 |
| inactive-out | 116.0 → 336.5 | 116.0 → 335.0 |
| wrap-bounce-before-net | 1,138.5 → 1,407.0 | 1,133.0 → 1,408.5 |
| wrap-net-before-bounds | 1,102.5 → 1,478.5 | 1,091.0 → 1,475.0 |
| wrap-low-speed-before-bounce | 741.5 → 1,002.5 | 740.0 → 992.5 |
| wrap-none | 4,234.0 → 5,033.5 | 4,249.0 → 5,378.5 |

The accepted long-flight example consumes 78 actual ball phases. Its measured
median query duration is about 1.096 ms PAL and 1.086 ms NTSC, compared with
16.702 ms and 16.625 ms for the native scan, using 3,546,895/3,579,545 Hz.
The three-phase example is slower: approximately 0.771 → 1.464 ms PAL and
0.759 → 1.453 ms NTSC. All representative rejected flights pay overhead; this
prototype is not a universal flight acceleration and should not automatically
replace the existing scan. Complete min/p95/max and paired saved ranges remain
in the local receipts; a few interrupt-phase samples differ from median trends.

## Resources and compatibility

Pure query code is **1,140 bytes**, with no static table/BSS allocation. Its local
frame is 48 bytes plus 44 bytes of saved registers. A separately traced declared
fixture audit observed a maximum 122-byte query stack span (including call/helper
frames, excluding native IRQ frame growth). The caller supplies a complete
318-byte private state; canonical storage cannot be used for a production query.

The diagnostic adds 140 bytes of hook/reference code, a 6,720-byte declared input
fixture table and 668 bytes of BSS (two private states, results, counters and
canaries). Relative to the PR39 product, native CODE is 56,472 → 64,472 (+8,000),
DATA stays 112,700, BSS is 145,420 → 146,088 (+668), and loaded payload grows
314,592 → 323,260 (+8,668). Development file size grows 206,012 → 214,852.
These HUNK sizes are exact loaded payload costs, not measured whole-machine
free RAM. Whole-machine pool/IRQ stack worst cases for a shipping integration
remain unmeasured. There is no production allocation in this prototype.

The normalized shipping core remains byte-identical to PR39: 17,606 bytes,
seven relocations, fourteen sink branches, SHA256
`99c543c170c036137be81d07ebd30b522ef3abdff04bd7b1af38f00047bb99d5`.
The standalone fixture and diagnostic native executable have distinct hashes;
no raw image, executable, ROM or runtime capture was published.
`native_metrics.py --require-runtime --record` and `native_metrics.py --check`
both exited 1 for unchanged incomplete
standard resource coverage; both tracked current reports remain byte-identical
and still identify the unchanged PR39 shipping product. The diagnostic resource
measurements do not fill those standard profiles.

## Failures, review and integration hold

Retained failures include an early unsupported relative relocation between
fixture hunks (external actual-core calls now use JSR), the prototype root's
uncleared upper-word return, and the first native observer's missing stack-write
watch. The reviewer identified the negative-height guard's overwritten CCR; the author
corrected it before the complete proof. The native read/write observer correction keeps
the strict emitted entry/RTS pairing. Every failed/interrupted invocation remains
non-passing; the latest selected campaign completed successfully.

An independent reviewer reran all roots and the 672 CCR/private-state fixtures
with a different initial CPU working poison, checked source/guards/event order,
and independently verified both literal native RPC streams: every initial and
endpoint read, all protected-owner comparisons, loaded hunks, zero dropped
notifications and all 168 query/reference timing pairs per region. Source and
completed evidence are approved; the final report review is recorded separately.

The pending user decision is whether a tutorial placement marker means the
uninterrupted intrinsic landing or the existing reactive-opponent outcome.
Keeping the actual preview and adding a separate ball-only explanation avoids
changing existing endpoint semantics. Replacing the marker's endpoint requires
an explicit semantics decision and further integration/acceptance: a ball query
cannot reconstruct player movement, missed contacts, AI actions, RNG call order,
scoring, scene/audio or lifecycle. Recorded seek, reactive alternatives and live
play must continue to use the actual shared match core. No production semantics
change, optional sprites, scheduler redesign, upload or merge is included here.

PR39 currently targets PR38's `feature/tutorial-court-prototype` branch, not master.
PR38 still needs user appearance review and full release/cold-ADF acceptance with
complete standard resource coverage; later production retained navigation is not
claimed by its API fixtures. PR39's focused approval does not release that base
hold. The arithmetic's two runtime files can be ported independently to master
(the pre-change files match), but the resulting master product requires its own
build/hash, exhaustive arithmetic/full-state/shared-byte checks, focused native
checks and release packaging/cold boot; stacked receipts cannot certify it.
No duplicate master-based validation was started.

## Reproduction and receipt identity

Use the existing pinned tools, legitimate ROM, PR39 product and retained recordings;
missing or different inputs fail closed. The completed selective commands were:

```sh
CTENNIS_LANDING_BASELINE_ROOT=/workspace/ctennis-ratio32-shortcut \
CTENNIS_LANDING_RECORDING_ROOT=/workspace/ctennis-tutorial-court \
PYTHONPATH=/tmp/ctennis-shared-core-python/lib/python3.12/site-packages \
RUST_LOG=info python scripts/native_acceptance.py --plan \
  --case host-unit --case guarded-landing-cpu --case guarded-landing-pal --case guarded-landing-ntsc
```

Then use the same environment with `--start --campaign ID` or
`--resume --campaign ID`, retaining all four case flags. The completed ID above
records original source commit/diff provenance, receipt hashes and failed attempts.
The native watch fix was a recorded working diff during the completed captures;
its exact bytes are now committed in the observer correction above. The shipping
core and query executable bytes were unchanged by that observer fix.

## Local completed receipt identities

| Receipt | SHA256 |
| --- | --- |
| `guarded-landing-cpu` | `4d3cb853a26273a32bf31604bd652fde6dab6d906e068c8802a49bb351de1726` |
| `guarded-landing-native-pal` | `30654159d1de132c55278bfd90f809b9720ea714e2593ccd20f23af184f92c69` |
| `guarded-landing-native-ntsc` | `d5fde7fda12401798f2802cf859d77672a742f49a341c70addc39048e382e687` |
