# Fixed serve destination diagnosis

The user observed that the delivered `b8b04f8` potential serve lands in the same
place after moving the player. The original rules support this behavior: this
is not evidence of a stale preview or permission to change serve aiming.

`amiga/game/gameplay_players.s:169` (`game_random_launch`) samples absolute
court target X/Y and height from the server-end tables, using `G_RANDOM` and
`G_FLIP_SERVE`. It does not add player position to the target. Serve wait
attaches the ball at player X+20 for the lower end (upper X-4); derive_launch
uses this launch origin and the chosen target to calculate the velocity.
Moving within the original lower serve region, X128..199 and Y152..153,
therefore changes launch origin/vector while preserving the frozen serve's
random choices. Small endpoint changes can follow the original integer math.
Real subsequent serves can have different random choices; changing tutorial
position does not advance the frozen live RNG or request a new random serve.

A minimal actual 68000 CPU comparison uses the immutable original `6eb0bf72`
full preview and current `38c48b` projected preview. Its genuine initial-serve
fixture uses the existing initializer/select/pads/result/dispatcher/freeze APIs;
positions are passed through the legal request API, with no intermediate state
injection. Twelve executions cover three positions and both action alternatives.

| Lower player XY | Held launch X | Chosen target XY | Actual first landing XY |
|---|---:|---:|---:|
| 128,152 | 148 | 109,76 | 110,75 |
| 163,152 | 183 | 109,76 | 109,75 |
| 199,153 | 219 | 109,76 | 109,75 |

Original/current path bytes and the reported terminal fields match for every
paired case. Paths differ across positions. All released cases remain actual
phase $40 serve wait with attached ball and no launch; the bounded preview ends
with LIMIT, not a different landing. This is one deterministic lower initial
serve, not all gameplay states, complete state/output equivalence, native timing
or a fresh WinUAE measurement. No gameplay or RNG changes were made for diagnosis.

Receipt: `build/tests/tutorial-serve-target-diagnosis/70ae133f915b4d0089ce862a17123e16/report.json`,
SHA256 `58a9b121e81ae3b2b69c246e9120a255209417c78ed80f10d81087273b2ee377`.
Its probe, CPU module, executable/listings/manifests, helper sources and current
native shared-core byte-equality receipt are bound. Canonical/history/records
are unchanged at every public yield. Original full preview is the reference;
this is not a physical original-game replay.

The existing exact-product PAL title physical capture settles at player163,152.
Its current generation46 held endpoint is ground109,75; marker coordinates are
native pixels109,76 (Y+1 sprite/court origin). Released selection clears the
marker and demonstrates waiting. It does not supply multiple completed physical
placements, so it is supporting custody rather than the controlled comparison.
Read-only reduction: `existing-native-publication-reduction.json` alongside the
CPU receipt, SHA256 `4f80b392c58fe3724c390810944d25ee1a551159d29ba4bdea1cde7331199992`.

## Correction to the earlier marker observation

The earlier white-only landing check can count the terminal white ball. Exact
`held-preview-045.png` already has all nine cross pixels at109,76 in native
palette13 red, while its ball is at177,136, wholly outside that cross. The
published scene's animation index is21, before terminal63. Private palette15
becomes13 when the original games-score strip supplies plane1=0; the HUD and
score pointers are preserved. The previous statement that the cue only becomes
visible at the terminal sample is therefore withdrawn. New affected physical
checks must identify cross-shaped current endpoint pixels outside the ball,
including the native HUD colour, before terminal playback.

The subsequent explicit automatic-potential request is a separate interaction
change: demonstrate a prospective serve-button press automatically, preserve
literal held/released returns, loop a completed immutable potential, and restart
on position or action changes. It does not authorize changing serve targeting.

Independent read-only diagnosis and design review:
`build/tests/tutorial-playable-review/serve-target-final-independent-review.json`,
SHA256 `38ee10238d304e209eb06d8191748c810c2b391af185d4cd3c0fb2ea6be63b3c`.
The existing products and immutable delivered candidate remain untouched.
