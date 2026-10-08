# Static court placement presentation

This source increment keeps the existing four-plane court, native actor/sprite
renderer, palette and triple-bank publisher. It adds no canvas and leaves the
physics, preview bodies, action alternatives, limits and admission thresholds
unchanged. Trail passes are not scheduled; `tutorial_trails_enabled` is a reserved
byte initialized to zero. The earlier bounded optional renderer remains dormant.
Movement repeats at one selected simulation interval rather than seven; the
15-interval double-tap threshold is unchanged. No appearance approval or fresh
native timing pass is claimed.

`tutorial_progress_reset` retires old observations
when an accepted position request changes generation. The next separately
admitted publication uses immutable original `plane0`, selected native player
poses and the latest edited XY. Old ball/shadow payload is hidden until an actual
current-generation alternative provides it. No bitmap copy precedes placement.

After each returned `game_preview_step`, `tutorial_progress_returned` copies only
current-generation counts/outcomes and qualifies observed availability. It does
not render, call a core body or modify admission timers; D5/D6 are preserved.
Latest-placement readiness and continued `tutorial_work_pending` are independent,
so a held result can publish while the released continuation still runs. Dense
ball/shadow animation uses actual samples at the existing two-points per two-ticks
cadence. Animation after worker slices requires its own fresh 10000-Eclock
admission, including publication work.

The native source exposes these presentation fields:

- `tutorial_placement_dirty`, `tutorial_placement_ready`, `tutorial_marker_ready`,
  `tutorial_animation_ready`, `tutorial_waiting_ready`, `tutorial_trails_enabled`:
  bytes.
- `tutorial_presentation_generation`, `tutorial_marker_generation`,
  `tutorial_animation_generation`, `tutorial_visible_surface`: longs.
- `tutorial_available_counts`, `tutorial_available_outcomes`: two words each.

The added declared storage is 32 bytes, pending actual layout/resource measurement.
READY (status 4) describes published stopped-alternative presentation, not backend
pair completion. Marker-ready additionally requires an actual accepted launch,
nonempty samples and a landing/net/out/interception outcome. WAITING (status 6)
is distinct: actual released current-serve continuation has dispatched, remains
in human phase 0x40, and has no accepted launch. It displays the hold-F/B1 hint,
without inventing a landing or changing backend outcome 6/256-point horizon.
UNAVAILABLE remains status 5. Footer text explicitly identifies an unfinished
other alternative. F and joystick B1 still choose held/released presentation.

The source-only checks cover local branch references, tutorial symbol references,
32-character footer widths, unchanged root admission functions and diff whitespace.
No builder, emulator or actual-CPU proof ran in the author worktree. Integration
must compare actual complete publication banks and native sprites, latest-XY
supersession, held endpoint versus released waiting, ongoing other-alternative
work, dense animation, full318/all72/live-backup preservation and Resume latest.
Fresh PAL/NTSC callback headroom, IRQ ownership, loaded bytes and initialized RAM
remain required. Existing parent capture/controller owns that execution.
