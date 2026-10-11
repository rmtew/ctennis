# Tutorial exploration loop

This increment follows draft PR54. Short G/B2 executes the currently placed shot
inside the tutorial. The gesture captures a complete edited origin and literal
F/B1 action on press; releasing either button cannot change that captured shot.
The initial human serve executes the prospective held serve shown by autoplay.
G/B2 plus a direction consumes the gesture. No retained-shot navigation is added.
A hold lasting 24 nominal simulation intervals (about 400ms elapsed timer time)
opens options; its release is consumed and confirmation requires a fresh press.

Execution uses actual full-core nominal callbacks with ordinary poll, logical
pad/result sampling, render-before-dispatch and the complete dispatcher tail.
Physical input, keyboard ACK and publication retain their existing priorities.
The tutorial remains logically active. During flight the ordinary native court
is displayed and audio stays muted. After the opponent launches a return, the
first complete simulation boundary pauses, allowing legal human position edits
before the ball reaches the player. A miss/net/out, lifecycle transition, explicit
long-hold stop or the finite 512-update limit stops coherently. Terminal context
is unavailable; automatic retry of a missed shot is not implemented.

Exploratory updates do not append history records or change the interrupted
backup, history72 or incoming cache. The paused canonical state is complete318,
not a reduced predictor continuation or an animation sample. A full-current
preview request supplies that complete origin to the existing guarded projected
worker; staged serves use their existing qualified route. Seek/replay/pending
owners reject competing starts and requests before canonical mutation.

**Play From Here** exits the tutorial, applies current legal position/action and
builds native player objects, then installs a complete branch checkpoint at the
interrupted live cursor. Older operations remain; incomplete old attempt metadata
is retired. Logical edges and RNG are part of the checkpoint. Physical menu input
is reconciled before normal recording resumes. The actual branch's audio state
is synchronized on exit. **Resume Original** restores the exact interrupted state
and history, then performs the existing physical-input reconciliation and restores
saved sound levels. Original audio periods remain untouched during muted flight.

Every native scene source switch retires ready prediction ownership and clears
reusable neutral-bank tags. An unavailable preview invalidates and rebases its
generation instead of retaining old prediction-bearing banks. The last completed
actual scene may remain displayed until a new neutral tutorial scene publishes.
An accepted press snapshot remains independent of action-only preview refreshes;
chords, long holds, fresh presses and exit consume it. Concurrent seek/preview
owners refuse the release-time start.

## Qualification plan

Independent source review cleared focused execution after correcting simultaneous
F+G capture, projected full-origin routing, pending seek fences, stale-generation
retirement and neutral-bank tag reuse. This is source review, not a native pass.

Stable diagnostic cases: `tutorial-exploration-cpu`, `tutorial-exploration-pal`,
`tutorial-exploration-ntsc`. Package the committed product first. The CPU case
compares complete states and ordered semantic outputs with another execution of
actual ordinary full-core APIs from the same genuine accepted origins. It checks
both incoming action literals, Original318/history72/records/incoming preservation,
commit checkpoint seek and logical gesture consumption. Its presentation sinks
are observational traps; cycles do not establish Amiga elapsed-time bounds.

The PAL/NTSC controller cold-loads the exact stripped ADF, observes scalar bus
writes, supplies only physical keys, and retains selected complete state reads
and native-resolution screenshots. It checks gesture/serve/return/reentry/Original
and Play exit boundaries, all observed complete callback deadlines and ACK pulses.
The raw transport has a 128MiB uncompressed cap per attempt and omits bulk bitmap,
stack and DMA tracing. These omitted protections remain explicit release holds.
Failed attempts stay immutable alongside passing receipts.

No universal deadline guarantee, full resource campaign, human appearance approval,
WinUAE/physical-hardware result, broad cancellation/fairness proof or full release
acceptance is inferred. Unaffected historical receipts remain historical and are
not relabelled as passes for this increment. No merge is authorized.

## Focused results

Runtime product: `1e3dbb356b9e061201d4c7c31b94282dd193baa7`. Development SHA256
`51118ed46f219035cc70cdd846762bf9f3ba67f355165ad8711f9cf394cead89`;
stripped release `f4e10d0784302c739b73f335ffbdc68d018713178379e3e63c10fceaa997c8b5`.
The 901,120-byte ADF is `da25745e978bd48acf4e933960aa5d656d02961e91a56b4f21a2a28307c2d13a`.
Observer and documentation commits do not change that product. Exact private
receipt paths and hashes are in [summary.json](evidence/tutorial-exploration/summary.json).

CPU campaign `3af8114e884e474bb0e7c6d153d1fb58`, attempt3, passed 372 complete318
and ordered-output comparisons: initial serve69 updates, then held131 or
released103. Native-origin prospective launch uses the separately bound captured
initial318; only the ordinary logical `continue_held` byte differs at launch.
A separate missed-shot comparison passed64 updates, actual stop3/no human launch,
unavailable preview context, and exact Original318/history72/records/incoming
restoration. Movement reaches the actual legal left edge X40 through controls;
no intermediate canonical state is supplied. Presentation remains trapped in
these CPU proofs, so their results do not establish physical/native timing.

Native campaign `688060ab910b4624922b88b81e13e846` passed PAL attempt4 and NTSC
attempt1. Both cold-load the same stripped ADF and pass all nine named checks:
initial serve, consumed direction chord, actual moving scanout, pause after
opponent return, literal held/released capture, consumed menu hold/release,
exact Original restoration and complete Play branch checkpoint. Small white ball
movement is independently visible in both native-resolution flight photographs;
sprite-header changes alone are insufficient to identify the moving object.
Readback and screenshot may refer to different completed frame epochs.

| Measured finite extent | PAL | NTSC |
|---|---:|---:|
| Complete callbacks | 1,382 | 1,376 |
| Maximum complete callback work | 15.408ms | 15.303ms |
| Minimum absolute simulation headroom | 1.059ms | 1.148ms |
| Complete keyboard ACK pulses | 38 | 38 |
| Minimum ACK duration | 216.245µs | 213.156µs |
| Dropped notifications / unfinished callbacks | 0 / 0 | 0 / 0 |
| Uncompressed scalar raw capture | 5,925,821 bytes | 5,858,430 bytes |

These are elapsed emulated colour clocks, including contention and entry
lateness; they are neither host latency nor a universal deadline guarantee.
Physical input schedules are identical across standards, while CIA-seeded native
states need not match. Causal gameplay equality uses matched deterministic CPU
origins and input schedules, rather than subtracting unrelated native timings.
The released native return hits the net, stops coherently and invalidates preview
context. Automatic point retry remains absent; independent point-end and out
trajectories are not separately claimed by this focused extent.

Initial native captions in both the interrupted and final PAL photographs say
**LANDING**. The earlier NET description was mistaken. The captured-origin
diagnosis compares47 ball-field samples through predicted landing without a
difference, followed by five additional actual samples before accepted opponent
contact. No serve physics or caption correction was justified. The diagnostic
uses actual preview and gameplay APIs; it does not infer ball-only prediction
and opponent-intercepted gameplay have identical terminal timelines.

Two clean package builds are byte-identical, and the fresh `--adf --boot-only`
check passes all four loaded-byte/initial-title checks. The earlier product's
boot report is preserved before replacing the canonical receipt. Independent
review verifies source ownership fences, native/CPU receipt bindings, actual
scanout and callback arithmetic. Full resource recording deliberately remains
incomplete: `native_metrics.py --require-runtime --record` exits1 with all eight
broad profiles unmeasured. Both tracked metric files record that limitation.

Failures remain immutable: initial CPU legal-placement coverage failure;
interrupted PAL attempt1; inverse-raster assertion failure in attempt2; past
absolute breakpoint target in attempt3; and a missed-shot observer that assumed
X32 was always legal. The latter three observer assumptions were corrected
without changing runtime physics or weakening output equality. All native
captures are capped at128MiB uncompressed; bulk bitmap, stack and DMA tracing
was deliberately omitted. No giant archive or wider collector was generated.

No current matched prediction-endpoint latency rerun was performed. Earlier
non-overlapping physical-input→COPJMP accounting remains historical in
[coherent scheduler results](tutorial-coherent-scheduler-results.md) and the
subsequent matched reports. Declined owners are included in scheduler overhead;
outside-callback time and support work are not automatically recoverable idle
time. This increment changes the exploration workflow, not that latency claim.
