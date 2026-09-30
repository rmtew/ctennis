# Game-driven native status lifecycles

Four cases cover the remaining one-player messages (selectors 2, 3, 4 and 5).
Each starts once from original captured state two callbacks before the message
draw, runs the existing native gameplay, and follows the message through expiry.
There are no intermediate expected-state writes, direct field-selector writes,
or source-VDP writes supplied to the renderer. The existing first-game prefix
separately covers selector 1. Two-player selector 6 remains open.

## Independent source expectations

`scripts/status_reference.py` pins the accepted presentation recipe, original
media/association manifest hashes and the continuous original callback parent.
It rebuilds each ignored local phase from that parent and validates it against
the public phase recipe. An already pending or displayed earlier message at
the start is rejected. The phase begins before the point event, rather than
seeding a pending status request after the game has generated it.

The original drawn-message latch supplies the expected requested status at each
callback. These isolated intervals have exactly one message appearance and
clear; the retained original state must show that complete sequence. The
appearance's pending-not-drawn flags and expiry's drawn flags/saturated timer
are checked. This is a projection of observed source state, not a Python game
simulation. The selector survives in the low bits after expiry; the drawn latch
determines whether text should remain visible.

Physical source pixels remain separate evidence. Three stable checkpoints per
case select independently captured original rasters using callback/VDP/raster
associations. Their status crops must agree with captured original glyphs and
the expected latch state. At the exact draw callback the original scanout can
still show the prior text, so the callback latch is not presented as an exact
physical pixel timing oracle. No new MAME captures or dependencies were needed.

| Selector | Initial completed callbacks | Appearance | Expiry | Raster targets |
|---|---:|---:|---:|---|
| 2 | 2233 | 2235 | 2266 | 2234, 2237, 2268 |
| 3 | 4922 | 4924 | 4955 | 4923, 4926, 4957 |
| 4 | 1648 | 1650 | 1681 | 1649, 1652, 1683 |
| 5 | 7071 | 7073 | 7104 | 7072, 7075, 7106 |

## Actual native observations and mutations

`scripts/run_status_tests.py` uses the actual application's sampler, source-rate
simulation, native scoreboard selection and shared Copper backend. Original
refresh choices are supplied through the existing replay adapter. Held fire is
an actual Amiga joystick input. All 35 consecutive scoreboard selections per
case are observed at the existing routine's return boundary, including the
callbacks immediately before and after expiry. The native input flags and timer
are compared with original observations. Full meaningful RAM agrees at each of
the three raster checkpoints.

Completed native rasters are associated with their actual committed display
generation and visible frame, not with an assumed one-callback-per-PAL-frame
mapping. The existing exact palette/viewport mapping is applied. Capture reports,
private replay wrappers, executables and screenshots retain hashes. Selection
or state differences are product failures; missing/invalid evidence and failed
capture commands remain tool errors.

Two private compiled mutations run in every case:

- Replace the native expiry clear with `nop`: first failure is the exact expiry
  callback, and the completed later raster retains unwanted text.
- Compare the native timer with 254 instead of 255: first failure is one callback
  before expiry. The later cleared raster is correct, so the consecutive request
  checks are necessary to detect this regression.

All four normal cases are green: 140 consecutive requests and 12 completed
raster crops. Both mutations are detected in all four cases; their simulation
state remains unchanged at the raster checkpoints. Stop equivalent one-player
status-window expansion.

Run `python scripts/run_status_tests.py --all --self-test`, or select a registered
`--case p1-status-2-lifecycle` (selectors 3, 4 and 5 have equivalent case names).
The aggregate suite registers four independent cases and clears stale reports.

These are local lifecycle tests, not continuous round/match parity, ordinary
unpaused timing, or complete P1 acceptance. Two-player status 6, game-driven
point/mode/reset/result/restart output and other scene classes remain required.
The source-state/field observations are diagnostic adapters: they may change or
retire when a redesigned Amiga implementation preserves equivalent behavior
through an independent observable-output test.

The remaining status-6 original interval is already retained in
`tests/reference/two-player-match.json`: appearance20925, expiry20956, with both
source buttons held and both input readers returning16. Its frozen physical
windows are22224/22255. A future local start at20923 precedes the point request.
The current live adapter lacks the second reader, already protected by P3
known-red cases. Extend the capture adapter to the correct source parent and
both physical ports; do not write the expected second input, pending message
or selector into the native game to hide that omission.

Full aggregate baseline/self-test verified:87 cases,52 green,35 exact known red,
no unexplained failures or tool errors. All new capture-report, private wrapper,
executable and PNG hashes verified after that run. Four missing groups still
cause the completion gate to fail.
