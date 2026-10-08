# Production shared match core

This is increment 1 of the authorized tutorial roadmap. History, seek, shot
previews and tutorial controls are not implemented. The historical PR #32
[362-update proof](match-core-proof.md) remains separate evidence; its 307-byte
inventory and copied native executable are not this production boundary.

## Code and ownership

`amiga/game/core.s` includes the actual controls, dispatcher, gameplay, scoring,
scene and audio routines in both `amiga/main.s` and `amiga/standalone.s`.
The standalone executable does not include physical input, UI construction,
graphics banks, hardware output or hardware clocks. It has synchronous output
sinks. All simulation rules and lifecycle decisions execute on the 68000.

The canonical block is 318 contiguous bytes, including reserved packet bytes.
The machine-checked ownership and checkpoint-envelope contract is
`scripts/match_core_state.py`; packet interiors retain the assembly G_, S_, AV_,
D_ and O_ definitions. Schema version 2 and simulation version 3 bind the current
layout and seeded-entropy policy. The previous 314-byte block is historical;
old checkpoint envelopes are rejected. A checkpoint envelope binds the exact compiled
standalone rules hash as well as both versions and complete byte length.
The validator checks audio clip IDs and aligned offsets, including completion
at the exclusive clip boundary. It does not certify arbitrary corrupt state:
other table-index validation remains a requirement for a future restore API.

`game_core_init` clears the complete block and enters TITLE. A new match gets
one explicit 16-bit seed; zero maps to `$ace1`. Live play samples a hardware seed
only at native selection. Fresh live play uses corrected Galois16-b400-v2,
alongside the unchanged game PRNG. Historical playback explicitly retains its
original shift-only entropy rule while advancing a corrected shadow stream;
logical takeover selects that already advanced stream without another seed.
Both words and the policy are canonical. Audio AV_NEXT stores an offset
from the immutable audio-table base; no relocated pointer is checkpointed.

## Logical boundary

The public boundary comprises init, select(mode, seed, entropy policy), sample_pads(A, B),
sample_result(continue held/pressed, automatic continuation, playback active/
mask, selection held), clear_inputs, latch_actions, return_title, round_poll
and tick_dispatch. Selection and title requests are commands, not direct
adapter writes to lifecycle state. Native physical aliases, UI gestures, demo
packet cursors and presentation timers remain outside canonical state.

An unpaused native callback polls the previous logical input once, samples the
physical controls into logical pads, processes UI actions and result metadata,
accepts any selection command, then dispatches. The dispatcher decides its own
lifecycle path from canonical state. Native rendering and publication surround
these calls. The operation recording captures API arguments and order; it never
chooses a callback regime or supplies an intermediate expected state.

Paused ordinary play still samples logical pads and metadata without dispatch.
This retains existing release and action-latch behavior. Ordered logical
operations, including these samples, are required for exact replay; recording
only the final held mask at dispatched ticks would lose a release/repress.
Tutorial interruption isolation is later work and is not established here.
Button 2 retains existing shot behavior until the tutorial UI increment.

The ordered semantic output comparison covers calls inside logical operations:
scene objects/ball layer and display fields at render, field/status publication,
title requests, and each logical voice period/level. Physical pre-dispatch
render calls and native bank publication are presentation work outside these
semantic operation traces; existing native raster/publication checks protect
that integration. Shot/no-contact explanations are not added in this increment.

## Validation

Use the normal pinned native tools, legitimate external Kickstart 1.3 and the
hash-pinned CPU dependency in `tests/match-core-proof-requirements.txt`:

```sh
CC=gcc CXX=g++ python -m pip install --require-hashes --no-binary=machine68k \
  -r tests/match-core-proof-requirements.txt
RUST_LOG=info python scripts/run_shared_match_core.py --seconds 8
RUST_LOG=info python scripts/run_shared_match_core.py --ntsc --seconds 8
RUST_LOG=info python scripts/run_shared_match_core.py --two --seconds 8
RUST_LOG=info python scripts/run_shared_match_core.py --two --restart --seconds 8
RUST_LOG=info python scripts/run_shared_match_core.py --demo --seconds 300
RUST_LOG=info python scripts/run_shared_match_core_fixtures.py --case all
python scripts/check_shared_core_poll.py build/tests/shared-match-core-pal-demo/report.json
python scripts/check_core_entropy.py
RUST_LOG=info python scripts/run_demo_match_tests.py
```

The native trace is compiled only with CORE_TRACE. Production emits neither
mailbox storage nor trace instructions. Trace wrappers preserve registers and
SR; internal calls remain inside the root operation. A native write observer
rejects dropped events, non-core writers and canonical writes outside a logical
API, reconstructs all state bytes, and checks one final direct native read.
LoadSeg hunks are verified against the compiled fixture before running.

The isolated CPU starts with poisoned memory/registers, executes actual 68000
calls, compares complete state and ordered outputs after every operation, and
audits reads against narrow immutable-table declarations. Independent replays
start from the initializer with two poison patterns and consume only recorded
arguments. Negative controls must detect omitted initialization, hardware reads,
out-of-state writes and undeclared data reads. Relocated replay consumes the
complete captured stream and verifies its lifecycle coverage, rather than a
prefix that could finish before match selection. These are safety and determinism
checks, not a second implementation of the game.

Case-specific receipts under ignored `build/tests/shared-match-core-*` identify
source/input/tool/ROM hashes, exact executable hashes, target, operation extent,
observed lifecycle coverage, stack high-water and isolated CPU cycles. A rerun
invalidates that case's prior pass before building. CPU cycles exclude Amiga
contention and physical presentation work. They do not prove native deadlines
or a worst-case budget. Native acceptance, resource reports and independent
review remain required before calling the increment complete.

## Focused evidence at the reviewed boundaries

The 314-byte receipts below describe earlier source boundaries. They do not
establish complete-state equivalence for the new 318-byte schema.

Production assembly boundary: `228c31ecbdc27c32a34c08d5da7588dfa48ad4ad`.
Validation/schema boundary: `3ba1babc0396421ca36743a502cfc5f7340b91ee`.
The development executable remained byte-identical across those boundaries:
`e9420c22893b0c6e1abf5ad1fac2437ef2e8018ff78211f95bf9503c294752cc`.
The isolated executable is
`462becbdabc101841ba880dec980a2250a77a467289cbe3744a44a3c148ea482`.
These identities describe local focused evidence, not a completed native gate.

The 300-second PAL native/standalone comparison at `3ba1bab` passed 71,907
operations and 17,976 completed callbacks. It covered title, selection, play,
round pause, round sound, result sound, one completed title request and a second
demo selection. All 314 state bytes were written and compared; ordered semantic
outputs, both complete poison replays, the relocated 2,000-operation replay and
all four forbidden-access/initialization controls passed. The 240-second earlier
extent ended in result sound and is superseded by this longer case.

The PAL two-human physical selection, pause, confirmed title return and opposite
one-human selection passed 2,876 operations across 778 callbacks, including 120
paused sampling callbacks without dispatch. Both selections and final play were
asserted. The early two-human harness attempt pressed its key before native
startup sampling was installed and selected one-player mode through joystick
fire; it did not establish two-human coverage. The corrected harness waits for
the initialized native menu and asserts the actual mode commands.

Each of the five retained scoring starts passed 1,920 operation comparisons over
480 callbacks, with one native initial fixture state and no later state writes.
They retained deuce 5/5, advantage 4/6, return to deuce 5/5, advantage game award
0/0 with games 2/2, and match award 0/0 with games 6/2. Whole-fixture poisoned and
relocated replays passed. These fixtures are separate from ordinary match play.

The frozen independent trajectory passed all 10,958 ticks, with 31 flight-side
changes and zero missed publications, at production boundary `228c31e`.
Its executable hash is the same `e9420c...` product checked above; this is explicit
byte-identity reuse, not a fresh full-trajectory rerun at `3ba1bab`. Native input
sampling passed 11 checks. The host suite passed 70 tests. The early NTSC
eight-second differential passed 1,894 operations/473 callbacks, both complete
poison replays and four negative controls; its receipt binds the then-current
validation source hashes and is a bounded smoke extent, not full NTSC lifecycle
coverage. Final current-head NTSC validation remains required.

The existing emitted-byte classifier verified the standalone file against its
listing and assets. Loaded bytes reconcile as follows:

| Component | Bytes |
| --- | ---: |
| Actual shared CPU instructions | 7,538 |
| Immutable simulation tables | 10,396 |
| Shared source alignment | 2 |
| Complete canonical state | 314 |
| Eight standalone RTS sinks | 16 |
| Hunk alignment | 2 |
| Total standalone loaded bytes | 18,268 |

The native development file is 181,016 bytes; the stripped release file is
159,864 bytes with SHA256
`d70d1a0b1b5208b3798a054a64fea28d6ad775528bc3508a147b8ca9b97ab1f4`.
Native loaded code/data/BSS totals 166,228 bytes. Release stripping removes only
symbols. These sizes are not a whole-machine RAM measurement or a release cold
boot pass. The maximum observed isolated stack extent is 128 bytes; the PAL
300-second core execution accumulated 170,572,718 CPU cycles. This accumulated
total is not worst-frame cost, native contention timing or a hardware budget.

The first smoke attempt failed because its final observer call supplied both a
PC and seconds target to `run_until`; the corrected bounded breakpoint call
passed. The initial CPU dependency build failed because the environment's
default compiler was missing `clang`; the successful recovery used GCC and then
reinstalled with the existing hash-pinned requirements. Receipts and raw private
runtime state stay outside Git. Ordinary cadence, sprite publication, resource
coverage, the finite native gate and independent review remain outstanding at
this document boundary. No history buffers have been allocated.

The first ordinary one-player cadence rerun then failed on returned-title
callback 11,787: 63,480 CCK work plus 586.518 CCK entry lateness exceeded the
59,191.137 CCK callback interval. The completed ordinary match/restart had
12,049 callbacks, zero missed publications and a measured initialized-chip peak
of 305,496 bytes, but the missed deadline invalidates that native case. The
pre-fix two-player diagnostic was intentionally interrupted at observed guest
time 333.838 seconds to apply this known deadline fix; its interrupted receipt
establishes no pass.

The native presentation adapter now resets title UI state immediately and marks
the requesting callback's epoch. `ui_render` retains the previous complete
presentation throughout that callback; the next callback builds and publishes
the complete title bitmap. This spreads match cleanup and the four-plane menu
copy across separate unchanged-deadline callbacks. Physical keyboard polling and
elapsed accounting between construction planes remain in place. Fresh deliberate
menu shortcuts retain their existing acceptance, including a selection before a
deferred title bitmap is visible; held continuation controls do not become fresh
menu edges. Core state and semantic title requests remain at their original
fixed boundary. This is a presentation timing fix, not a timing exemption.

Before that fix, the full native menu passed 132 checks and PAL sprite DMA passed
all startup phases, two-player, serve, pause, return, title, alternating fields,
delayed construction and boundary-preemption cases. Stale-bank, unknown-bank,
malformed-height and unmasked-preemption controls were rejected. Native setup
passed raw deadlines and elapsed accounting; lost-wrap and delayed UI controls
were rejected. These bind the pre-fix executable and must not be presented as
fresh passes for the modified presentation adapter.

The updated demo takeover check passed 5,480 trajectory ticks, 18 flight-side
changes and zero missed publications. It retained complete game/score/audio/
clock/entropy state at takeover, then observed an actual shared-entropy call
during ordinary live execution within a finite horizon and checked consumption
at the next native input boundary. It never invokes entropy manually or injects
state. The old assertion that the demo LFSR stops in live play was deliberately
replaced because live play now consumes that same seeded generator. The frozen
10,958 expected digests remain unchanged.

The first deferred-construction cadence rerun still failed: callback11,788
spent60,327 CCK and completed60,690.381 CCK after its deadline origin, exceeding
the59,191.137 CCK interval by1,499.244 CCK. Its diagnostic setup proposal passed,
but that is not a product deadline pass. The cached-plane copy now uses register
bursts to reduce instruction overhead while copying the same3,712 bytes per
plane and retaining between-plane keyboard/timer sampling. A first dirty-source
attempt placed the helper inside a footer fallthrough and failed the menu test;
that placement was corrected before acceptance or any deadline pass claim.

`check_native_title_copy.py` executes the assembled68000 plane helper and checks
all bytes, surrounding sentinels, pointer advances and preserved registers. It
also executes the native callback counter increment across65,535->0 and checks
that the deferred flag skips only the requesting callback, then retires even
if a fresh shortcut already entered play. This bounded CPU regression does not
establish Amiga deadlines or DMA correctness; fresh integration reruns remain
required for the modified copy.

### Returned-title validation boundary

At committed head `0e994e9`, the ordinary executable was
`48f2ca13a10fc4432b1e9871aa1c9dd49a8ca3837b4e028db7ee4215dd940ae8`.
One-player match/restart completed 12,047 observed callbacks and two-player
match/restart completed 23,795. Both completed receipts have zero raw deadline
misses, zero missed publications, verified loaded executable identity and no
changed inputs. Their tightest observed title headrooms were 1,272.756 and
1,022.886 CCK respectively; these are finite observations, not worst-case
bounds. Both measured initialized-chip peaks were 305,568 bytes, not a claim
about pre-pool cold boot. The setup self-test passed all raw deadlines and
rejected lost-wrap accounting and UI-overwork controls. The menu passed all
132 checks. PAL DMA passed 15 cases and rejected four compiled controls; NTSC
passed its six startup phases. Those fixture binaries are distinct from the
ordinary executable and cover the explicitly recorded physical-bank cases.
Takeover passed 5,480 frozen ticks, 18 side changes and zero missed publications.

The fresh full frozen run reproduced all 10,958 expected trajectory ticks but
failed its earliest returned-title pixel check: the old four-callback screenshot
still showed the previous complete court. It is a failed receipt, not a full
demo acceptance pass. A bounded initial-once retained match-award fixture then
measured actual semantic TITLE, complete bitmap/ready epoch, Copper publication
and captured scanout without inserting state or selecting a callback regime
after initialization. Startup phases 0, 253 and 308 completed title construction
in exactly the following callback; ready-to-publication times were 23,338,
36,811 and 24,392 CCK, each below one physical PAL field (71,051 CCK). Phase 253
reproduced the old four-callback pixel failure, while the other phases did not.
All captured fields from the first title publication's frame plus two had the
full independently checked title pixels. This is the existing completed-scan
convention used by the continuous attract digest observer, not a software frame
model or an increased callback budget.

The frozen and attract harnesses now require that exact first completed physical
scan, construction in the next callback and publication within one PAL field
of completed ready. The old four-callback capture remains a diagnostic. Later
600/1,200/1,790-callback pixels, continuous attract digests, bank/blank/ready
guards and all trajectory digests remain strict. An actual compiled extra-
deferred-callback control is rejected by the next-callback construction bound.
These test changes require fresh full acceptance; they do not retroactively
turn the failed frozen receipt green. Current tail timelines are persisted even
when an assertion fails, and a new run replaces stale tail metadata immediately.

`check_shared_core_bytes.py` compares 17,936 actual uninstrumented native and
standalone code/table/alignment bytes. Only 250 actual HUNK_RELOC32 references
and 11 verified named synchronous-sink branch destinations per image are
normalized; all remaining bytes must match. At this boundary the normalized
SHA256 is `83679f6d9b538584f387f144f143231293753348a83092aead1ed7dcb6330601`.
Canonical mutable state is excluded from that byte comparison and validated by
the separate complete-state replay guards. The current PAL eight-second smoke
passed 1,914 operations/478 callbacks, poisoned and relocated replays and all
four forbidden-access/omitted-init controls. The current NTSC two-human pause/
return/opposite-mode smoke passed 2,850 operations/771 callbacks with the same
guards, including 119 paused logical samples and the actual title request.
Short smoke is not full-lifecycle
coverage; the earlier full core replay remains explicitly tied to its unchanged
standalone byte identity.

The honest `native_metrics.py --require-runtime --record` refresh exited 1 and
recorded incomplete current coverage: cold-one ADF was not run, two/setup
receipts were conservatively stale after harness changes, and full demo failed.
The current ordinary file is 181,192 bytes; release-symbol stripping yields
159,952 bytes and loaded code/data/BSS total 166,300 bytes. Those static sizes
do not establish whole-machine RAM headroom. The clean-head finite native gate,
fresh resource coverage and independent review are still required. No merge,
readiness or history/tutorial UI claim is implied by this boundary.

### Celebration observer and CPU-context guards

The clean `1f16910` native campaign stopped at its blue celebration check;
commands 0–22 completed, but this is a failed gate, not acceptance. The old
entry breakpoint observed RESULT only after its first sequencer callback had
completed. Actual semantic writes show RESULT beginning with completed counter
130 / started counter 131, and first-play completion flagged inside callback
1056 with completed counter 1055. The first subsequent entry observes completed
1056: the authored phrase remains exactly 926 callbacks from semantic start.
Subtracting the late entry observation 131 instead gave the erroneous age 925.
The corrected observer uses the semantic transition, retains the 926 minimum
and 924 loop interval, and checks all three voices DONE with zero duration at
the actual first-play flag. Held-input, last-loaded and audio/pixel checks remain.

The corrected working-harness blue self-test completed and rejected an actual
compiled premature-completion control with terminal durations `[1, 1, 1]`
instead of `[0, 0, 0]`. The old mutation targeted a removed direct integration
include and therefore changed nothing; the corrected route asserts each unique
main/core/integration/audio include and verifies distinct assembled identities.
The original failed gate and command log are archived privately. Its original
blue case metadata was overwritten during diagnosis; that missing case receipt
is not represented as preserved. Fresh committed celebration cases and a fresh
full frozen run are still required before another complete clean-head gate.

Logical replay now freshly poisons D0–D7, A0–A6 and CCR before every operation.
Only declared word arguments replace their low halves; unused upper halves
remain poisoned. Instance memory poison also seeds CPU context so identical
logical sequences run with distinct working registers. The collector already
recorded the declared arity correctly; this is additional hidden-context
coverage, not a correction to argument counts. Complete-state and ordered-output
comparisons plus narrow immutable-read auditing remain mandatory. These finite
replays do not establish arbitrary checkpoint restoration or corrupt-state
safety, which remain later-increment requirements.

### Entropy review correction: schema 2 / simulation 3

Independent review of `d702414` found that the old shared entropy routine put
MOVEQ between LSR and BCC. MOVEQ clears carry, so the conditional feedback never
ran: `$ace1` became `$5670`, returned zero and decayed to zero after 16 draws.
The same error exists in the immutable
[original demo routine](https://github.com/rmtew/ctennis/blob/17d6d050c07fac6ead6202bec2d1bf5a0db38079/amiga/game/interface_demo.s#L33).
The condition-code behavior is specified in the
[M68000 reference manual, MOVEQ](https://www.nxp.com/docs/en/reference-manual/M68000PRM.pdf#page=238).
Native/standalone equality could reproduce that shared mistake; independent
known answers are required in addition to differential replay.

Modern `galois16-b400-v2` moves MOVEQ before LSR. Both entropy words are seeded
once from the same nonzero match seed. Every request advances the correct
modern stream. Only explicit `legacy-shift16-v1` playback also shifts the
historical observer word and returns zero to preserve its recorded physics.
`assets/interface/demo-entropy-compat.json` permits that policy only for the exact
immutable recording checksum. Neither the original recording JSON, fixture
manifest nor 10,958 digest payload was rewritten. New recordings name the
correct generator and digest the modern word; they require separate provenance.

The falling edge of logical automatic playback selects modern entropy without
changing either stored word or seeding again. It applies during selection,
play and round tails: the UI can accept takeover in those phases. Pausing keeps
automatic playback true even when active input playback is false. A title
command clears the old automatic value before the subsequent metadata sample,
so that exit is distinct from takeover. Unsupported selection policies are
rejected by the host logical interface and cause no owned writes in the core.

The old 314-byte offsets remain intact. Offset 218 is now explicitly named
`game_legacy_entropy_state` (with historical `ui_entropy_state` alias); policy
is appended at 314, owned alignment at 315, and modern `game_entropy_state` at
316. The block grows by four bytes to 318; it had no spare old alignment byte.
Schema 2 / simulation 3 reject incompatible old checkpoint envelopes.

`check_core_entropy.py` executed both actual candidate images against authored
mathematical answers (`1 -> $b400/1`, `2 -> 1/0`, `$ace1 -> $e270/1`), a 16-draw
sequence and all 65,535 distinct nonzero states returning to `$ace1`. It also
checked zero-seed mapping, historical shadow behavior, initial-once logical
takeover fixtures in states 1/3/4/5, pause, and actual title-command exclusion.
Observed isolated entropy costs were 96/106 CPU cycles for modern low bits 0/1
and 134/144 for the legacy policy; zero-seed selection was 108 and takeover
sampling 196. These include the harness return trap and establish no Amiga
contention or deadline bound. Fresh physical takeover checks now cover PLAY,
ROUND_PAUSE and ROUND_SOUND (lifecycles 1/4/5). Mid-play takeover observes an
actual live entropy request. Both 1,608-tick tail cases preserve seed and both
stream words, select modern policy without reseeding, consume menu controls,
accept fresh human input and return naturally to PLAY. Their bounded quiet
observation makes no claim of an entropy request; that request is unnecessary
while the AI is serving rather than tracking a return.

### Current complete-state and integration evidence

The production native SHA256 is
`82225743796c9e35476daa71fc291e03dc4a62c07473113361352ca2848d7e6f`;
the standalone SHA256 is
`eea5e3d068866057cc2d1b3e046358504e456057f1714647293e02a6408caded`.
Earlier 314-byte receipts cannot establish 318-byte acceptance.

Current PAL 300-second capture compares 71,907 logical operations / 17,976
callbacks through TITLE, selection, PLAY, ROUND_PAUSE, ROUND_SOUND, result and
the next selection. NTSC two-player/pause/title/one-player restart compares
2,850 operations / 771 callbacks. Both compare all 318 state bytes and ordered
outputs with differently poisoned working state and complete relocated replay;
all owned bytes are written. Five scoring fixtures each compare 1,920 operations
/ 480 callbacks. Two extra polls after every recorded PAL poll are state/event
inert. Omitted-init, hardware-read, out-of-state-write and undeclared-read
controls reject. These receipts are retained under
`build/tests/history/690bf54-current-proofs` and
`build/tests/history/5906997-before-full-gate`; later observer-only commits
preserve these exact product bytes.

The byte audit matches 18,006 shared code/table/alignment bytes, 257 relocations
and 11 named sink fixups. Loaded standalone bytes reconcile without duplication:

| Component | Bytes |
| --- | ---: |
| Actual shared CPU instructions | 7,608 |
| Immutable simulation tables | 10,396 |
| Shared alignment | 2 |
| Complete canonical state | 318 |
| Eight standalone RTS sinks | 16 |
| Total loaded standalone | 18,340 |

Observed isolated stack maximum is 128 bytes. Maximum observed isolated cycles
in the PAL proof are init 7,176; poll 13,724; pads 248; result sample 178;
dispatch 24,446; selection 102. The separate zero-seed/entropy tests above cover
additional branches. These finite CPU observations exclude Amiga contention,
input sampling and presentation; they are not universal worst-case bounds.

The clean `2085982c5066c56578bcc5c65105669e5a0e59d0` campaign completed all 41
commands with EXIT 0. It covers cold stripped-release menu, physical inputs,
PAL/NTSC publication/DMA, scoring/status/audio, all celebration orientations,
the unchanged 10,958-tick demo and next demo, three physical takeover phases,
two unattended attract cycles, feedback, ordinary match/restart cadence,
early-release/audio, setup and packaging. Demo has 31 flight-side changes and
zero missed publications. Cold-release one-player has 12,399 callbacks;
two-player has 23,796; both have zero deadline/publication misses.

The original aggregate still records EXIT 1: its attract summary expected eight
captures while the actual test independently checked ten, including both first
complete title fields. `b34ab6f` corrects the summary to require all ten named
captures and first-complete replies, retaining the other conditions. Checker
negatives and all 86 host tests pass. Existing native receipt provenance and
coverage were revalidated without emulation; original false aggregate and logs
remain in `build/tests/history/2085982-complete-campaign-summary-mismatch`.
`build/acceptance/completed-revalidation.json` binds that original receipt,
validator source, artifacts and fresh/compatible passing case receipts; SHA256
`757b8bfddea14dd8b6f22d48415aa7496d10513898c28d0a7cf8f34b5a9d9910`.

Earlier PAL DMA failures also remain archived. A snapshot between physical
COPJMP and software front-role cleanup caused the decoder to inherit the wrong
court bank. It now binds the inherited bank from actual Copper pointer source
addresses, requires physical evidence for ambiguous court pointers and keeps
the separate title list distinct. Fresh PAL/NTSC suites and compiled negative
controls pass. Independent review cleared product and decoder at `2085982`;
the summary-only delta requires review before merge.

[Current resource reports](metrics/current.md) are recorded from the completed
workloads. Native loaded payload is 166,388 bytes; stripped release is 160,072
bytes with SHA256
`0adeee75a6ca79719f279a5e15266b7a03dee3831271ae13094e8496106b17d8`.
Cold one-player initialized chip peak is 271,920 bytes, largest free block
251,176; direct two-player peak is 305,656, largest free block 218,056. Different
startup environments are not paired memory comparisons. Minimum observed title
deadline margins are 2,020.064 CCK (cold one-player) and 1,387.160 CCK
(two-player). Future history work must budget against measured available memory
and transition margins, not a 512 KB history allowance. Pause-only UI
construction, allocation-failure instrumentation, pre-Exec bootstrap peak and
physical-board coverage remain unmeasured. No history buffer or tutorial UI is
implemented. PR #34 remains a reviewed draft pending final summary review and
integration; no merge or next tutorial increment is implied.
