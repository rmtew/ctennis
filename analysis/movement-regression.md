# Movement boundaries and current regression evidence

The annotated source uses two four-row bounds tables at ROM `$144D` and
`$147C`. Animation bits 5–6 select the row; animation bit 7 or point-outcome
bit 2 suppresses movement. Accepted movement attempts use steps of one and two
alternately, from the interrupt counter's prior parity. Positive steps must
remain strictly below their table limit; negative steps may equal it. There is
no clamp: a rejected step leaves the coordinate unchanged.

| Player | Row | Inclusive Y range | Inclusive X range |
|---|---:|---:|---:|
| Lower | 0 | 152–153 | 128–199 |
| Lower | 1 | 152–153 | 40–111 |
| Lower | 2 | 128–153 | 40–199 |
| Lower | 3 | 98–153 | 40–199 |
| Upper | 0 | 7–9 | 80–111 |
| Upper | 1 | 7–9 | 128–159 |
| Upper | 2 | 7–31 | 64–175 |
| Upper | 3 | 7–62 | 64–175 |

These are allowed destination ranges, not proof that every destination occurs
in every phase. A two-byte Y range explains why a held direction sometimes
does nothing even though movement is enabled. Opposing direction bits are
processed sequentially; this capture deliberately uses one direction at a time.
Mode bit 4 exchanges the players' controller nibbles, as documented in
[the physical input map](two-player-input-map.md).

## Captured and compared initial row

`movement-serve-bounds` selects two-player mode from reset, leaves fire released,
and moves both players through down/up/down and right/left/right holds. The
frozen policy writes only physical controller fields. Both captures agree
exactly: 742 consecutive gameplay callbacks, no PSG writes, no refresh reads
or between-callback RAM changes. The complete case passes against the assembled
routines shared with the application: 254 bytes at entry, pre-tail and return.
This is simulation/input-reader replay evidence, not ordinary native joystick
sampling or display timing acceptance.

`scripts/movement_reference.py` verifies eight player/direction observations:
actual approach, eight stopped attempts covering both step sizes, then four
accepted reversal attempts with a coordinate response. Relevant animation,
mode, point-block and consumed direction values are checked. Narrow vertical
ranges need not move on all four reversal attempts. A neutral interval between
holds remains in the continuous replay.

| Direction | Approach/hold callbacks | Four reversal callbacks |
|---|---:|---:|
| Down | 21–124; stopped 117–124 | 141–144 |
| Up | 141–244; stopped 237–244 | 261–264 |
| Right | 381–484; stopped 477–484 | 501–504 |
| Left | 501–604; stopped 597–604 | 621–624 |

Source raw capture SHA256:
`352b2a0849c138140d92f41ab7b60253129b5ceba5bc9d514652c3f24129d22e`.
Frozen fixture SHA256:
`9741dfe015d72e6db81bff5e624431521273f4463f179669d50e048a8bd9f711`.
Private raw streams, logs and validation report remain in
`build/tests/movement-serve-bounds-capture/`; source-derived data stays ignored.

Reproduce with:

```text
python scripts/capture_test_reference.py --case movement-serve-bounds
python scripts/run_regression_tests.py --case movement-serve-bounds --self-test
python scripts/inventory_match_references.py
```

The deliberate native lower-X increment is detected at callback 1, pre-tail,
sprite record 1 X: expected 192, actual 193. Temporary mutated source and
executable are removed. An altered source held-direction observation is also
rejected by the behavioural evidence validator.

## Alternate-service row

`movement-alternate-serve-bounds` preserves the first 485 callbacks of the
frozen R2 source record exactly, through source frame 1784. Its natural first
point toggles mode bit 3; `initialize_round_state` then selects animation row 1
for both players. The following physical-input sequence keeps serve actions
released and holds down/up/down then left/right/left. Both independent source
captures agree: 1,322 callbacks and 50 ordered PSG bytes. The full native case
passes and the same native movement mutation is detected at callback 1.

| Direction | Approach/hold callbacks | Four reversal callbacks |
|---|---:|---:|
| Down | 601–704; stopped 697–704 | 721–724 |
| Up | 721–824; stopped 817–824 | 841–844 |
| Left | 961–1064; stopped 1057–1064 | 1081–1084 |
| Right | 1081–1184; stopped 1177–1184 | 1201–1204 |

The upper reset X is 160, one beyond row 1's permitted positive destination
159. The sequence moves left first, then approaches the positive limit from
inside the range. Reset positions are not automatically valid destinations
for every direction; the original movement code rejects rather than clamps.
The validator checks exact natural-prefix equality against its hashed R2
parent on every capture validation and native run.

Raw SHA256:
`b0a91d89f4472f1f4a1f0e2c2f6fc608bc44b232279dceb5d2207913dcd811ad`.
Fixture SHA256:
`592a872488874a9099767f31a56e3cf892ecef37f31ebf61e2adde4305cf15e5`.
Use the preceding capture/test commands with case
`movement-alternate-serve-bounds`. Both cases remain continuous from reset;
neither injects expected intermediate results.

## Remaining F1 work

One receiver-row limit is now independently established by
`movement-receiver-right-bound`. It preserves the first 1,320 R2 callbacks
through frame 2619, then moves the upper receiver right during the alternate
lower serve. Direct source snapshots bracket the movement calls, establishing
row 2 before movement rather than inferring it from later animation state.

| Observation | Source callbacks | Actual upper X |
|---|---:|---:|
| Approach and hold | 1321–1342 | 160 to 175 |
| Last eight enabled held attempts | 1335–1342 | 175 throughout |
| Four reversal attempts | 1343–1346 | 173, 172, 170, 169 |

The full native comparison passes 1,348 callbacks and 190 PSG bytes. Source
capture repeats exactly with the extra observations; removing them produces
exactly the independently recorded ordinary stream. Source fixture SHA256:
`5d9aabd25124f451f35014fa87e247acde56f036019674259f29e23cab596530`.
Raw observed capture SHA256:
`5895f458630c61769b3658899e64b54dcce9e4f9a45ad9c47e993caa34fc2c3f`.
The native self-test deliberately lets the row-2 receiver escape X175. It is
detected at callback 1331, pre-tail sprite record 5 X: expected 175, actual 176.
Normal source/executable remain unchanged and temporary mutation files are
removed. This targeted check passed after the full aggregate's mutation run.

The combined inventory tracks each player/row/direction separately: 21 of
32 combinations have approach/hold/reversal evidence, and 11 remain. Passing
one limit does not close its entire row. This is movement coverage, not a
percentage of overall source or port correctness.

The other upper-receiver limits now have independent cases in the first R2
serve. Each preserves the first 212 callbacks exactly, then holds the requested
direction at frames 1512–1535 and its reverse at 1536–1539. The stop at frame
1541 precedes the bounce that would change the row. All cases have direct
movement-entry/return snapshots, twice-identical observed captures, and a
separate observer-free recording with identical ordinary output.

| Case | Actual approach | Held callbacks | Four reversal coordinates |
|---|---:|---:|---|
| `movement-receiver-left-bound` | X88 to X64 | 229–236 | 66, 67, 69, 70 |
| `movement-receiver-up-bound` | Y8 to Y7 | 229–236 | 9, 10, 12, 13 |
| `movement-receiver-down-bound` | Y8 to Y31 | 229–236 | 29, 28, 26, 25 |

Each complete native case compares 242 callbacks and 20 PSG bytes, including
the approach at callbacks 213–236 and reversal at 237–240. Together with the
alternate-serve right-limit case, these establish all four upper row-2 limits.
The native mutation tests deliberately escape each tested limit only when
receiver-row flags are active; exact differences are in the case reports.
Source validation also rejects an animation-blocked held attempt instead of
counting its stationary coordinate as a bounds observation.

Fixture SHA256s are
`0538d1c317b789cba8c36ce1f6286bd355590285e76b22e1b388248e3c9e259e`
(left),
`086cb9bd6e8aa341137450a5c011863b6a1d3807fd47459c56307eef419c9640`
(up), and
`db1a21184f005da1b8f8a970b8ba9d73e4c4794083043857fb9b81b6d0f7bcd2`
(down). Reproduce with the ordinary capture/test commands and these case IDs.

Rows 2–3 for each player still need approach/hold/reversal evidence. Existing
R2 post-body observations include all four unblocked animation row selections,
but that alone does not establish their bounds, movement inputs or the exact
row used earlier within the callback. Read the phase/reset/trajectory writers
and index intervals before collecting missing sequences. Preserve the existing
continuous matches and the new independent case; do not manufacture animation
flags or substitute the old Python movement model for original-game evidence.

## Read-only movement capture

The lower receiver right limit now has a continuous source parent and a
separate native phase: `movement-lower-receiver-right-bound` and
`movement-lower-receiver-right-phase`. The parent preserves R2's first 4,569
callbacks, including ordered main-thread writes; only debugger-log sequence
numbers change with added observation records. Mode `$92` exchanges controller
ownership, so pad 2 controls the lower player.

Source callbacks 4570–4587 approach X192 to X199; 4580–4587 prove eight stopped
attempts. Reversals 4588–4591 produce X198,196,195,193. Two observed captures
agree through 4,593 callbacks, and match the independent observer-free run.
The continuous native parent retains the exact callback-2536 round-transition
failure. The independent 24-callback phase is green and detects X199-to-X200
escape at local callback 6/source 4575. It initializes once from source callback
4569 and carries actual native state; no intermediate source writes are injected.
This adds one lower row-2 limit without claiming continuous upstream parity.

`python scripts/capture_movement_observations.py --case two-player-rally`
and `--case two-player-match` each record full RAM immediately before and after
both player movement calls, twice. The tool verifies the source ROM contains
the two expected CALL instructions at `$13B9` and `$13BC`. Optional debugger
hooks snapshot at `$13B9` and `$13BF`, then immediately continue; they do not
write CPU/game state or step instructions.

After stripping only those snapshots and restoring raw sequence numbers,
each capture must equal its original raw source record byte-for-byte. This
passed for the complete rally and full R2 record. Raw R2 includes one callback
after the retained fixture endpoint; the indexed inventory excludes it and
reports raw/retained extents explicitly, including the initial callback.

Observed raw SHA256s are
`135724ae50a43355f5be4f3391908c3b63aeb01e11446eeec8d54de893db1912`
(rally) and
`8b6d22f6b409c58fae2c577d1362b26ee128e7e70c92c3ad4b4200f77d70c12a`
(full R2). Reports and raw data stay in ignored
`build/tests/<case>-movement-observations/`. The source hooks are disabled for
ordinary reference collection unless the case explicitly requests them. Such
cases additionally require an observer-free run to match exactly before the
fixture is frozen. Altering the observed receiver row is rejected by validation.

The serve handoff selects receiving-player row 2 by retaining low animation
bits and setting bit 6. The bounce path replaces bits 5–6 with both set for
both players, selecting row 3. Completed serve/contact animations also permit
row 3 movement after clearing the movement-blocking bit. In the first retained
R2 serve, upper row 2 is visible from callback 213 (frame 1512) until the bounce
at callback 243 (frame 1542). Post-body row selections identify candidate
intervals; they do not alone prove the exact row at movement entry. Investigate
whether distant row-2 limits are actually reachable during that transient
phase before requiring a hold there or proposing a documented starting-state
injection. Keep geometric limits separate from phase-blocked movement.
