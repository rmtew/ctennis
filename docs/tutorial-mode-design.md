# Tutorial mode: design and roadmap

Status: implementation roadmap authorized on 7 October 2026. The shared core
is merged. Bounded history/seek merged in PR #36 after selective native acceptance
and independent review; see [bounded history](bounded-history.md). Isolated
previews are under implementation with partial CPU acceptance; see
[isolated previews](isolated-shot-previews.md). Tutorial UI and branching remain
later increments.

## Purpose and scope

Help the player see how position, contact time and the action button change a
shot. Remove guesswork about serves, returns and missed contact. Keep the court
visible. Let the player try alternatives and then continue from one, or return
to the interrupted game. Do not select a winning strategy for the player.

The title menu has a Tutorial option. It starts a one-player game with the
tutorial view open at the first serve. The same view is available during a
one-player match. It is not available in a two-human match. Keep these entry
paths on one implementation. No special one-button joystick interface is needed;
a player with that device can use the keyboard.

The first release includes bounded recent history, shot previews and branching
play. Full-match files, disk flushing and portable saved recordings are later
work. Reboot remains the way to exit the program.

## Current foundation

Bounded history started from master
`429cb73cb0ff4b10f86fa992e4694f89620d46b9`, after reviewed
[PR #34](https://github.com/rmtew/ctennis/pull/34) and
[PR #35](https://github.com/rmtew/ctennis/pull/35) merged the actual shared
68000 core and its behavior protection. Its complete canonical state is 318
bytes, with schema 2 and simulation version 3. Native execution and standalone
proofs use the same routines, including deterministic lifecycle and audio waits.

[PR #32](https://github.com/rmtew/ctennis/pull/32)'s earlier
[bounded proof](match-core-proof.md) covered 362 updates and 307 inventoried
bytes. Those historical limits do not describe the current complete state.
[PR #36](https://github.com/rmtew/ctennis/pull/36) adds fixed rolling history,
checkpoints and seek. Its selective evidence does not establish a complete
tutorial release or replace the final native acceptance gate. Do not restore
retired source folders.

This roadmap replaces conflicting tutorial and recording proposals in draft
[PR #24](https://github.com/rmtew/ctennis/pull/24). It does not approve that old
draft wholesale. In particular, history rolls within fixed storage; it does not
stop permanently when the recording buffer fills.

## Controls and entry

- During one-player play, double-tap button 2 to open tutorial mode. Button 2
  must no longer act as a duplicate shot button in this mode of play.
- On entry, freeze the match at a complete simulation boundary and retain that
  state as the interrupted-play state. Do not let tutorial controls reach it.
- Initially select the last relevant player shot or missed return attempt,
  with enough incoming flight visible to explain it. If there is no such event,
  use the current serve setup. A miss must remain inspectable without a contact.
  A raw retained probe index alone is insufficient: preview/navigation must
  verify its retained incoming context, distinguish truncated entries, and use
  the serve fallback when no suitable completed attempt survives eviction.
- In the tutorial view, directions without button 2 move the test player within
  the legal movement region for the selected serve or return.
- Holding button 2 makes directions adjust tutorial navigation/options instead
  of moving the player. The first prototype uses left/right for previous/next
  shot and up/down for time within the selected shot. These axes are prototype
  defaults, not a further design approval requirement.
- Button 1 selects the held-action alternative while held, and the released
  alternative while released. Both possible return paths remain visible.
- A single button-2 tap opens a small options menu. It offers Play from here,
  Resume latest and a way to close the menu without leaving the view. In a fresh
  title-menu tutorial, Resume latest returns to its saved initial serve state.

Distinguish a tap from a modifier gesture on release. Once button 2 has been
used with a direction, its release must not open the menu. Consume the entry
double-tap so it cannot also open that menu. Keep tap windows and key-repeat
delays in elapsed presentation time; they must feel the same in PAL and NTSC.
The exact thresholds and menu placement are prototype tuning values.

The existing [keyboard map](../amiga/game/keyboard.s) has separate action bits:
F/G for logical player A and period/slash for logical player B, as well as the
existing keypad aliases. Keep hints tied to the actual controlling player and
binding. The presence of B bindings does not enable tutorial access in a
two-human match. Verify these bindings through the native input sampler when
the UI is integrated. Do not infer a new keyboard layout from displayed text.

## Court view

Put an inverted TUTORIAL banner at the top, subject to measured screen space.
Keep the court and score readable. Show a ghost of the player's original
position and the editable test player. Repositioning changes the hypothetical
shot, not the stored original shot. Legal positions follow the game's serve and
return rules. Do not claim that every legal test position could have been reached
from the original position in the available time.

Show the incoming path and both outgoing alternatives computed by the game:
button 1 held and button 1 released. Use a solid active path and a dashed
inactive path as the first prototype. Test whether a slightly thicker active
path improves clarity at native resolution. Style must distinguish paths without
colour alone. Tune colours, thickness and dash spacing in the prototype.

When paths overlap, do not draw a false separation. Preserve the active path
and identify coincident alternatives with a short hint if needed. If contact is
not possible, show the incoming path and a brief no-contact reason; do not invent
an outgoing path. Net contact, first landing and out-of-court outcomes must come
from actual simulation events, not a second set of trajectory rules.

Animate a preview ball along the incoming path and the active outgoing path.
Use the game's height projection and shadow where useful so that height and
landing are clear. The animation is a display loop over a computed preview; it
does not advance the selected simulation moment. Repositioning, time selection
or changing button 1 invalidates the preview and restarts the display loop when
the new result is ready. Never show an old path as the result of a new position.

At the bottom, show `< n/m >`, where n is the selected retained shot and m is
the number available. Hide the left or right arrow when that move is not
possible. This also identifies the oldest retained shot without another warning.
Keep navigation stable while tutorial mode is open; paused play adds no history.

Use the row below for rotating short hints, annotations and current state.
Examples include the menu button, modifier navigation and no-contact feedback.
Choose keyboard labels or joystick button labels from the last deliberate input
source. Ignore idle samples and key-repeat noise for source selection. Avoid
rapid label changes when devices are mixed. Context feedback takes priority over
general hints; do not rotate away an important result before it can be read.
Hint timing is presentation state, separate from simulation time.

## Resume rules

There are two outcomes, with no extra resume interpretation:

1. **Play from here:** continue at the displayed simulation moment, using the
   displayed test position and selected action state. Discard the old future
   only when this command commits. Store a new branch checkpoint that includes
   the repositioned state, input-edge state and RNG state. Inputs alone cannot
   reproduce a position edit. Keep earlier retained history where possible.
2. **Resume latest:** restore the exact interrupted-play state. Discard all
   preview edits. Do not alter its score, clocks, RNG, input history or future.

Both commands remove the tutorial overlay and restore normal presentation/audio.
Menu confirmation and button-2 gestures must not leak into a serve or shot.
Preserve the selected button-1 state for Play from here; consume menu controls
separately. For Resume latest, restore the interrupted logical input state, then
reconcile current physical controls without inventing pressed edges. Test held,
released and mixed-device transitions explicitly.

## Simulation, history and preview design

Use the same actual 68000 match core in the game and the standalone harness.
Do not create a Python or host-language copy of the tennis rules as an oracle.
Separate physical input, rendering and hardware output from a fixed simulation
step. Supply logical actions at defined tick boundaries, including held-state
changes and their timing. Preserve the input state needed to derive edges.

Inventory all future-affecting state: player/ball motion, scoring, AI, RNG,
timers, contact state, game awards, end changes, match result/restart, and any
audio/animation sequencing that controls a lifecycle wait. Either retain such
sequencing in canonical state or replace it with equivalent deterministic
semantic state and prove the timing. Hardware timers must not provide hidden
entropy or completion decisions during a match. Seed once at match creation;
restoration requires full current RNG state, not just the original seed.

Use an explicit state/record schema and simulation version. Replace relocated
addresses with validated IDs or offsets when state refers to immutable tables.
Bind test recordings to the relevant code/rules version. Reject incompatible
state instead of interpreting it with a new layout. Persistent cross-version
save compatibility is not required for the first release.

Preallocate a fixed rolling store for logical input records, checkpoints and
shot/attempt indexes. A checkpoint contains all canonical state. Seek from the
nearest retained checkpoint and replay actions to the chosen moment. Evict an
old checkpoint and dependent records together; every visible shot must still
have a valid replay origin. Handle tick wrap and ring wrap explicitly. Do not
allocate memory per tick or per shot. Choose capacity and checkpoint spacing
from measurements, not an assumed maximum match length or a deuce limit.

Keep the interrupted state, editable state and preview scratch state separate.
Use bounded reusable storage; held and released alternatives may be computed
sequentially. Run both from the same selected starting state, changing only the
intended position/time/action variables. Never advance the live RNG during
preview. A changed path can change later RNG consumption; do not promise paired
opponent randomness or an ace from the landing point alone.

Bound preview work and path storage. If computation spans display frames, retain
a generation ID so a stale result cannot replace a newer request. Report a
truncated calculation rather than drawing an unproved complete outcome. These
limits are implementation choices to measure against the hardware budget.

## Roadmap and acceptance

Keep one implementation increment active. Each increment needs focused evidence
and independent review before merge. Start each increment from the reviewed
committed foundation. Do not build the UI on an unproved state boundary.

1. **Complete the shared deterministic core.** Inventory and isolate all match
   lifecycle paths. Compare complete state and ordered semantic outputs between
   native execution and standalone execution with the same logical inputs.
   Cover serves, held/released returns, misses, faults, deuce, awards, end changes,
   result waits and restart. Retain poisoned-state and forbidden-access negative
   controls. Exit: replay works without hardware-dependent reads or later state
   injection, and ordinary behavior remains protected by existing contracts.
2. **Add bounded history and seek.** Implement canonical checkpoints, action
   records and shot/attempt indexes. Test empty history, long play, wrap, eviction,
   both boundaries and repeated backwards/forwards seeks. Exit: seek state and
   outputs equal uninterrupted execution at each selected boundary; measured
   capacity and seek cost are recorded.
3. **Add isolated shot previews.** Reposition within legal bounds and compute
   held/released paths through the same core. Include no-contact, net, out and
   coincident-path cases. Exit: replaying a chosen alternative produces the same
   trajectory/outcome, and preview leaves live state/history unchanged.
4. **Integrate the court UI and branching.** Add title entry, one-player
   double-tap, modifier navigation, menu, banner, trails, animation and hints.
   Show native-resolution screenshots and a short animation before locking
   visual tuning. Test tap/hold discrimination, input-source switching, both
   resume commands and repeated enter/leave cycles. Exit: the committed branch
   replays from its edited checkpoint; Resume latest remains byte-equivalent at
   the canonical interruption boundary; two-human play cannot enter tutorial.
5. **Prove the target build and release.** Run the applicable existing tests and
   new tutorial checks, then the finite native acceptance gate. Exercise PAL and
   NTSC on A500, 68000, OCS, 512 KB chip RAM, no expansion. Check actual scanout,
   sprite/HUD publication and cold-loaded release bytes. Exit: reviewed evidence
   identifies the exact build, target, tools and coverage, with remaining limits
   stated. Emulator results do not establish physical-hardware coverage.

Measure executable/code/data size, total and added RAM, stack high-water use,
history capacity, checkpoint/seek work, preview cost and worst observed frame
time/spare time. Include ordinary play and the busiest tutorial view, with both
paths and animation visible. Separate standalone CPU cycles from contended
native timing. Use the existing [resource workflow](metrics/README.md); establish
budgets from the measured baseline before allocating the buffers. A large host
test or a short rally does not prove a native worst-case bound.

Keep progress short: current increment, evidence, remaining risk and next step.
This document is a plan. Its publication does not constitute a build, test pass
or tutorial release.
