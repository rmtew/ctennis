# Reduced preview call-graph experiment

This is a test-only comparison against the actual emitted original dispatcher.
The reduced `play` call graph preserves the compared observations in the retained
cases. Removing the opponent update changes wide-contact RNG results and
serve-handoff diagnostics. Removing scene processing fails the declared clamp
boundary. These results support a guarded shared-helper kernel as the next small
proof; they do not approve production migration or scheduler changes.

## Compared contract

Each execution starts independently from one immutable origin and the same
logical operation stream. The candidate receives no oracle intermediate state,
RNG, phase, launch parameters or trajectory. It calls the existing emitted
`input_update`, player/gameplay, scene, clock and ball helpers. The reference calls
the emitted original bodies, including round polling, scoring and audio service.
The original dispatcher supplies the complete incoming/contact reference; both
paths then use the actual ball-only continuation through the first outgoing
geometric outcome, matching the existing preview horizon.

The compared semantic event ledger is the receiving human's actual contact
attempts (phase, player phase, XY and ball/shadow projection) and accepted contact
or serve (phase, launch six-byte packet, target/height and contact/flight flags).
Every exact eight-byte ball/shadow sample is compared, including colours,
visibility representation and tick byte. Sample zero is the immutable origin;
the launch sample is captured after the dispatcher/helper tail, so it includes
actual launch initialization and clock advancement. Terminal flags and explicit
termination classification are also compared. The host projects the ordered
net/out/landing flag policy from `preview.s`; it computes no geometry.

Audio-period/volume, scoreboard and renderer sink ledgers are incidental to this
preview contract and are not equality requirements. Any live sink output fails
the experiment. This does not establish future explanatory reason-event coverage,
reactive actor rendering, exact full318 equality, or a playable branch. Recorder,
seek and committed playable branches retain their full-state/output proofs.

## Candidates and state

All variants keep a private318-byte scratch allocation. The reduced paths retain
210 initial bytes: gameplay60, mode1 at offset63 (`S_MODE` aliases `game_mode`),
audio100, input/control26, and tail fields23. The other108 bytes are independently
initialized with `$a5` and `$96`. No omitted initial byte may be read before it is
written; the bus audit checks that property for every run. This is an audited
conservative input set for these cases, not a minimal packed snapshot schema.

| Variant | Incoming/contact calls |
|---|---|
| `original` | Original logical bodies and dispatcher. |
| `play` | Logical samplers; input update, both players/gameplay, scene finish and clocks. Omits round poll, score, display update and audio service. |
| `human-only` | Replaces both-player gameplay with prepare controls, receiving human tick and ball tick. Omits movement and opponent updates. |
| `no-scene` | `play` without scene finish, including its animation and courtY effects. |
| `play-rng-negative` | `play` with one extra actual `game_random` draw before its first tick. |

Different final private hashes are permitted when observations agree. The
experiment rejects every CPU store outside private state/stack, every CPU read
of paused canonical318, and any change to the remaining initialized loaded
image after a helper/body call. The paused canonical state is independently the
last fixture state, not the origin. History preservation here covers initialized
history storage, not a populated production recorder or resume operation.

The retained originals begin in playing lifecycle1 and active scorer stage1.
This is a scope condition, not an implemented production admission guard.
General score/audio/lifecycle transitions require the original full replay.
The seed is `$ace1`; native reactive AI consumes its own RNG sequence. Matching
the seed alone is insufficient when a variant changes RNG call order.

## Cases and causal checks

Origins come from a single actual512-dispatch fixture. Lower cases start after
the first upper return (operation cursor564). Upper cases start after the first
lower serve (cursor356), with a declared initial role exchange: mode, scorer AI,
score flags and logical owners are initialized consistently once. They are
not evidence of an ordinary complete native end exchange. Player XY is edited
once per immutable origin; action is held or released, movement is overridden
through the simulation-level logical packet, and there is one prime sample per
variant as in production.

The ten cases include lower central, width13 and16 contacts, an earlier contact,
lower miss; upper central, wide, handoff and miss; and a declared clamp boundary.
Central/wide status comes from accepted native return-vector distance, not the
case names. Wide cases assert distance13..16 and accepted launch. Upper cases
assert actual serve-clock32 handoff and receiver-phase observations. Miss cases
assert no accepted launch and incoming-no-contact termination. The clamp fixture
initializes its ball state once at screenY/courtY193; the actual scene entry and
result witness the clamp to194. It is a boundary discriminator, not natural-match
coverage. Caps and stream exhaustion are explicitly recorded and cannot pass
the retained case checks.

The assertions require `play` equality under both poisons and actions. They also
require the deliberate extra RNG draw to change every named wide case, omitted
opponent work to fail lower wide and upper diagnostic comparisons, and omitted
scene work to fail the clamp case. Equality under both omitted-byte poisons is
required even for intentionally non-equivalent negative variants.

Retained failures matter:

- Initial v1 omitted mode along with the score packet. The read audit exposed
  offset63; held action changed the launch. The corrected210-byte set retains it.
- Lower width13, held: original targetX93; human-only89; extra RNG91. Both negative
  paths change the launch packet. Thus the comparator detects RNG-sensitive
  disagreement rather than accepting coincidental trajectory agreement.
- The clamp negative has courtY193 rather than194 in its phase2 attempt
  projection. Scene work is causal even where actor presentation is incidental.
- Upper human-only loses phase/handoff diagnostics. A coincidentally matching
  accepted shot is insufficient for the selected event contract.

## Evidence and cost limits

The executable is reused unchanged from runtime product
`a936ebac16c977cfc6c39a4426de1cbfdf62170e`; experiment base is
`bb86b3ce72dfb45db45a5a280205a29468b470a7` (draft PR41).
Standalone SHA256:
`ecd1086947ee316e713770b3548f8b19528cf2cec627713657a6bea12348eb5a`.
No runtime source, executable, scheduling policy or native input was changed.

Run with the pinned machine68k0.4.1 Python environment and existing standalone:

```sh
/tmp/ctennis-shared-core-python/bin/python tests/experiments/preview_kernel.py \
  --executable /workspace/ctennis-incoming-flight/build/standalone/match-core \
  --output /tmp/ctennis-preview-kernel-experiment-v5
```

Manifest identity:
`8a42e7c296125dbcb65fea05d2a0c7bbc424f6939751afddd61a7852c0a84895`.
Harness SHA256:
`dc57b743ad9d30934f0a3cdf4d58218ded2fd82217ec272ca49571caf83ec6e6`.
The manifest binds executable, harness, game source, shared Python helpers and
CPU module/tool metadata. Raw reports and earlier failures remain private under
`/tmp/ctennis-preview-kernel-experiment-v1` through `v5`; none are uploaded.
Completed attempts cannot be overwritten. `--resume` reuses only a complete
case with identical bindings; it never treats partial evidence as a pass.

Fresh v5 completed all ten cases and160 comparisons: `play` matched40/40,
`human-only`12/40, `no-scene`36/40, and the RNG negative24/40. The asserted
wide, upper handoff and clamp failures all occurred. Every candidate had zero
omitted initial reads and zero live outputs. Observed candidate stack maximum was
120 bytes; reference maximum was124 bytes. Both poisons gave identical preview
observations per candidate/action.
These are selective CPU proofs with declared fixtures, not full acceptance.

The measured work is emitted68000 CPU work in this experimental call graph.
For the held lower width13 case, original788,466 cycles versus `play`533,488;
lower central787,684 versus532,706; lower miss829,986 versus518,608. These finite
observations do not establish worst-case cycles or native elapsed latency.
Each candidate helper is entered directly by the host; an integrated kernel's
call overhead, bus contention, interrupts, renderer and scheduler costs remain
unmeasured. Do not use these ratios to change reserve/admission limits.
The scratch allocation is still318 bytes, and no new native kernel code bytes
have been emitted. Reducing retained initial inputs alone does not reduce the
allocated preview buffers or prove a compact production implementation.

`python scripts/native_metrics.py --check` fails with the existing
`Accepted metrics are incomplete` condition. No resource record is replaced.
No native campaign, release gate, WinUAE or physical-hardware check is claimed.

## Next review gate

Before production work, agree the exact preview observation contract and a
stable-active admission/fallback policy. The first small implementation proof
should retain318-byte scratch, call the actual shared helpers, preserve both
players/RNG and scene mutations, and compare against full original replay under
more seeds, real end exchanges and transition challenges. Full replay remains
the fallback for unproven cases and the source for on-demand playable-branch
reconstruction. Packing and renderer-only extraction require separate evidence.

The author owns a later approved implementation and integration; the parent
coordinates independent reviewers. This increment needs independent harness/
evidence review before any merge. It authorizes no production migration.

Independent review by `ratio32_review` approved test-only draft publication:
all169 manifest dependencies and identities checked, ten completed cases and160
comparisons independently reduced, poison pairs and documented counterexamples/
costs verified. The reviewer executed no Core/build/emulator. Approval excludes
production migration, timing bounds, native validation, merge and release.
