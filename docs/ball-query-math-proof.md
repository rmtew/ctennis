# Exact ball queries: derivation and bounded proof

Independently reviewed proof against `5623420afbbcb347b823c09b0f8e94d601516e34`.
This work changes no runtime source, executable, recording or expected trajectory.
The test programs call the unchanged emitted 68000 arithmetic and ball routines.
It establishes exact scalar queries and a restricted landing shortcut; it does
not authorize replacing the shared match core or claim measured native speed.

## Result

The divisor-32 routine has an exact table-free form for every 16-bit product:

```python
def ratio32(P):                 # 0 <= P <= 65535
    N = P >> 5
    if N < 256:
        return N
    W = N - 256
    R = W & (W >> 1) & (W >> 2)
    R |= R >> 1
    R |= R >> 2
    R |= R >> 4
    return (N | ~R) & 255
```

This computes the legacy result, including overflow. It is not ordinary division
followed by byte truncation or saturation. For example, emitted
`game_ratio(96, 90, 32)` returns **254**; the ordinary quotient is 270, its byte
is 14, and saturation would give 255. The formula has no table allocation.
Native instruction count, code bytes, register effects and worst cycles require
an assembled prototype and comparison before selecting an implementation.

A fixed ball segment can be evaluated directly at any byte phase. With the
ordinary-arithmetic guards below, its first intrinsic bounce from phase zero
can be located by checking at most **six** exact integer points. Without those
guards, scan up to 256 phases, stopping at the first intrinsic event. Neither
query reconstructs the rest of a match.

## Byte division and the divisor-32 reduction

The source is [gameplay_math.s](../amiga/game/gameplay_math.s). Inputs are masked
to bytes, `P = a*b`, and the quotient uses eight iterations. An exact recurrence
for the returned quotient is:

```text
r = P >> 8; q = 0
for i = 7 down to 0:
    u = 2*r + ((P >> i) & 1)
    b = int(u >= d)
    r = (u - d*b) & 255
    q = 2*q + b
```

For `d=0`, all quotient bits are one, including `P=0`. For `d>0` and `P<256*d`,
this is ordinary floor division. Outside that domain, the wrapped byte remainder
changes later quotient decisions. `game_ratio(64,128,32)=255`, whereas ordinary
division gives 256. Overflow is not uniformly saturating:
`game_ratio(127,255,32)=244`.

For `d=32`, write the remainder as `32*h+l`, with `0<=h<8`, `0<=l<32`.
The next carry is the old bit 4 of `l`. Those eight carries are bits 12 through
5 of `P`; the lowest five product bits never affect the quotient. With carry `b`,
the quotient decision is `h!=0 or b`, and
`h'=(2*h+b-decision)&7`. Zero is absorbing. While `h!=0`,
`h'=(2*h-1+b)&7` and the quotient bit is one.

Let `N=P>>5`, `h=N>>8`, `L=N&255`. For nonzero initial `h`, putting `j=h-1`
turns that recurrence into shifting the incoming bits through three-bit `j`:
`j'=(2*j+b)&7`, until `j'=7` makes `h'=0`. Thus the first three consecutive
ones in the rolling stream seeded by `h-1` terminate the leading quotient ones;
later quotient bits copy `L`. That stream is exactly `W=(h-1)*256+L=N-256`.
`W & (W>>1) & (W>>2)` marks the ends of its runs of three ones. Its highest
set bit determines the leading-one prefix. Smearing that bit down and
complementing yields that prefix; the boundary bit is already set in `L`.
This proves the formula above. With no such run, the result is 255. The highest
run marker is at most bit 7, so shifts by 1, 2 and 4 suffice.

The proof also checks a 2,048-byte direct table, a 256-byte piecewise fallback
and a 32-byte mask table. Their sizes are exact table payload sizes, not native
code or whole-machine RAM estimates. The rolling-seed form removes the
piecewise high-bit exceptions and all table data.

## Exact point and event semantics

The source is [gameplay_ball.s](../amiga/game/gameplay_ball.s). Use
`n=(old_step+1)&255` for an advance, and let `R(P)` be the exact divisor-32 form.
Signed-magnitude displacement is
`D(v,n)=sign(v)*R((v&127)*n)`, with all coordinate additions reduced to bytes.
Therefore `X=(baseX+D(vx,n))&255` and `courtY=(baseY+D(vy,n))&255`.

The height's signed velocity `s` is the magnitude for a positive byte and the
negated magnitude for a negative byte, except **`vy=0x80` gives `s=-256`**.
That follows from `NEG.B 0` followed by `ORI.W $ff00`. Negative zero has zero
court displacement but is not zero in the height equation. Define
`A=s+2*n-vz`, then `q=R((abs(A)&255)*n)`. These word operations have no signed
overflow over the input domain. If `A<0` and `q>baseScreenY`, ballY and ball
colour become zero and the routine returns before net colours. Otherwise use
`baseScreenY-q` for negative `A` with nonzero `q`, or
`(baseScreenY+q)&255` for the remaining cases. Defaults are ball colour 15,
shadow colour 1; courtY in 94..109 clears the shadow, and ballY in 94..109 then
clears the ball colour. The proof compares all 318 canonical state bytes.

Intrinsic `game_ball_tick` priority is:

1. Flight bit 7 copies the pending six-byte launch, clears step, emits launch
   sound and activates flight; it performs no advance.
2. Inactive flight returns, setting courtY to 194 if flight bit 5 is set.
3. Active flight advances; Y magnitude below 4 then ends flight as outside.
4. Unsigned `courtY < ballY` bounces, before net or rectangular bounds.
5. Flight bit 3, clear contact bit 0 and distance from courtY 110 below 3
   reflect off the net, before rectangular bounds.
6. X outside 32..231 or courtY outside 4..203 ends flight as outside.

First-bounce court classification additionally uses Y 39..183, a strict left
edge `X > 79-floor((Y-39)/4)` and inclusive right edge
`X <= 175+floor((Y-39)/4)`. First/second bounce, damping, base resets and animation
changes are checked against actual emitted ball calls. An earlier event ends
the fixed segment; querying its old parameters afterward is invalid.

## Six-candidate landing query

Let `H=baseY-baseScreenY>=0`, `m=vy&127>=4`, `s=+m` or `-m`, and exclude negative
zero. In the ordinary domain, with no coordinate wrap or screen clamp, define
`T(x)=trunc_toward_zero(x/32)`, `F(n)=2*n*n-vz*n`, and
`E=T((s+2*n-vz)*n)-T(s*n)`. Bounce means `E>H`.
The two truncation remainders differ by less than 2:

- `F <= 32*H` guarantees no bounce.
- `F >= 32*H+63` guarantees a bounce.

For positive threshold `K`, the first nonnegative integer on the ascending arm
with `F(n)>=K` is the exact corrected integer root:

```python
k = (vz + isqrt(vz*vz + 8*K)) // 4
n = k + int(2*k*k-vz*k < K)
```

Set `lo=root(32*H+1)` and `hi=root(32*H+63)`. Check the exact point predicate
in that inclusive interval. The root gap is at most
`(sqrt(126)-sqrt(2))/2 < 5`, attained at H=0, vz=0, so the interval has at most
six integers. The checker also exhausts every H/vz byte pair. A floating
parabola alone does not give the event tick: with vy=5, vz=0, both Y bases 100
and X base 128, the actual first bounce is tick **3**, not tick 1.

For an exact signed landing predicate, put `r=(m*n)%32` and `A=s+2*n-vz`:

| Case | Bounce condition for H>=0 |
|---|---|
| Positive Y, A<0 | Never |
| Positive Y, A>=0 | `F+r >= 32*(H+1)` |
| Negative Y, A<0 | `F-r >= 32*H+1` |
| Negative Y, A>=0 | `F-r >= 32*(H+1)` |

The implemented **test-only** guard is conservative. Over every phase 0..hi it
requires both displacement products below 8,192, `abs(A)<=255`,
`abs(A*n)<8192`, both screen extrema in 0..255, and court coordinate extrema
inside the rectangular bounds. The quadratic height extrema are its endpoints
and integer neighbours of its vertex. It also requires active flight, no pending
launch, hi<=255 and no pending special-net reflection. Parameters must remain
fixed, with no intervening player contact. These restrictions exclude earlier
intrinsic preemption and all arithmetic wrap/clamp. Relaxing the screen guard
to allow upward clamp is possible but is not needed for this proof. General
wrapped flight is not a monotone predicate suitable for binary search.

## What cannot be skipped

[game_play_tick](../amiga/game/gameplay.s) prepares controls, ticks the lower and
upper players, and only then ticks the ball; player movement follows. A contact
can replace the segment before that ball advance, using previous geometry and
player phase/action state. AI targets, RNG calls, scoring, scene transitions,
audio and lifecycle also contribute to a complete tick. A ball point or landing
query cannot recover their resulting state. The same actual core remains the
authority for live play, recorded seek and reactive alternatives. Equal seeds
alone do not guarantee paired randomness after different actions.

The first small prototype after review should be the divisor-32 scalar query,
then guarded geometry/landing queries for explanations. Compare actual assembled
variants, including the normal-domain path, against the existing routine's
results and caller-visible register/CCR effects. Measure code bytes and worst
68000 cycles across ordinary, overflow and boundary cases before integration.
No whole-match fast-forward should be inferred from this result. The integrator
owns any later runtime change; the coordinating reviewer owns independent
algebra and scope review before that work starts. Independent artifact review is
complete; production implementation and native timing remain a proposed next step.

## Reproducible evidence and limits

The unchanged standalone image SHA256 is
`9cccfffd752e328cfa5f1a4a5c2c2ccd64e1d0c2c8fbc4b72cca7dbeaaabda8b`.
The pinned machine68k tool is 0.4.1. Run from the repository root with the
existing pinned tool path available:

```sh
PYTHONPATH=/tmp/ctennis-shared-core-python/lib/python3.12/site-packages python scripts/prove_ball_queries.py
PYTHONPATH=/tmp/ctennis-shared-core-python/lib/python3.12/site-packages python scripts/prove_ball_query_forms.py
PYTHONPATH=/tmp/ctennis-shared-core-python/lib/python3.12/site-packages python scripts/prove_ball_query_seed.py
```

All three completed successfully. They write ignored local receipts under
`build/tests/ball-query-math/`; retained native input observations must already
exist for the first two programs. No package installation, new native build or
emulator campaign was performed for these proofs.

| Checked extent | Result |
|---|---|
| Every 16,777,216 byte a/b/divisor triple at emitted full entry | Exact recurrence; full D0, CCR and D2/D3/D4, poisoned input upper bits |
| Every 65,536 word product at the emitted divider suffix | Exact divisor-32 piecewise, compact and rolling-seed forms |
| Every 65,536 byte factor pair at full emitted entry | Compact and rolling-seed forms, including input masks/MULU |
| Every 65,536 signed-magnitude displacement/phase pair | Exact returned displacement |
| 691,561 point/height boundary cases | Full canonical 318-byte equality |
| 786,432 flight/contact/geometry cases plus 2,048 low-speed cases | Event priority and complete ball-packet effects |
| 5,521,679 ordinary signed height triples | Landing bounds and exact signed predicates, all H=0..255 by monotonic truth sets |
| Every 65,536 H/vz pair | Exact bracket, at most six candidate ticks |
| 23,309 guarded isolated flights; 615,969 uninterrupted emitted ball calls | Candidate query equals first actual event; full 318 bytes each return |
| Retained PAL and NTSC actual control streams, 818 logical operations each | 116 advances each, full state equality; native selected boundary 552 retained |

For the word-product proof, the actual 24-byte masking/multiply prefix is
verified before entering its unchanged divider suffix; full factor-pair calls
separately check that prefix. Exhaustive value loops disable per-access tracing
for speed. Separate 4,096 ratio and 1,000 ball cases retain instruction and memory
guards; recorded replays also retain those guards. This is not an assertion that
all exhaustive accesses were traced. The scalar specification is restricted to
arithmetic and ball-packet effects, not a second whole-match oracle.

The retained recordings observed maximum phase 46, no divisor-32 displacement
overflow and no negative-zero Y. Each recording contained five unique phase-zero
parameter tuples, of which two satisfied the conservative landing guard. These
are finite observations, not a proof about every reachable launch or a measured
acceptance rate. In each region, the other tuples were one court-Y-bound
rejection, one inactive flight and one screen-clamp/wrap rejection. Such tuples
must use an exact intrinsic scan for ball-only analysis, or actual shared-core
replay when complete match state is needed. No shipping fallback or skip path is
implemented by these proof programs.

The selected isolated-flight grid contained 62,496 tuples:

| Guard outcome | Tuples |
|---|---:|
| Accepted | 23,309 |
| Court X bound | 7,743 |
| Court Y bound | 4,204 |
| Displacement overflow | 12,512 |
| Height factor wrap | 2,304 |
| Height quotient overflow | 752 |
| Screen clamp/wrap | 11,672 |

Rejected tuples do not receive a six-candidate guarantee. Other guard exclusions
(negative initial height, low Y speed, negative zero, pending launch, inactive
flight, phase wrap and pending special-net reflection) are explicit in the
guard, though this selected grid does not exercise all of them. Raw observations,
images and runtime receipts stay outside Git.
Report host durations (about 71 and 15 seconds for the first two proofs) measure
test execution, not native performance. The full release/native resource gate
remains outside this arithmetic task. An interrupted precheck was replaced by
the completed fresh proof; it did not count as passing evidence.

Local receipt SHA256 values for this completed run:

| Receipt under `build/tests/ball-query-math/` | SHA256 |
|---|---|
| `report.json` | `cf5fad1f5f4f36cdd19c2165aa1b4506828b34260e7c211fe9464bbe8536bbdf` |
| `forms-report.json` | `9a334209727a3d0b6783a3631d29f1f5f9959ab71550e91b6a739780988bf7ed` |
| `seed-report.json` | `80b4da17580576d3ac1ab62e87056f67d65ac6eda471c4d68f6c4e8cced75263` |
| `counterexamples.json` | `7c27acbf9cb8d6efae1a6888b3877b31200271c0b6ce09ea835e6affc16327e9` |

The primitive receipt records its source/input/tool hashes, and the final
rolling-seed checker pins both prerequisite proof programs. Runtime input hashes
were rechecked after the proofs and still match. Python compilation and whitespace
checks passed. The required documentation resource check
`python scripts/native_metrics.py --check` exited 1 with
`Accepted metrics are incomplete`, consistent with the existing resource limit;
no new resource report or native acceptance claim was produced. The runtime
source diff is empty. This proof is published separately on
`proof/ball-query-math`, without changing PR38. See the
[independent review receipt](ball-query-math-review.md). Approval covers the
proof artifacts, not a runtime replacement or full-match skip path.
