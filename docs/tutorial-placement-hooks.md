# Static court placement presentation

This source increment keeps the existing four-plane court, native actor/sprite
renderer, palette and triple-bank publisher. It adds no canvas and leaves the
physics, preview bodies, action alternatives and limits unchanged. Trail passes
are not scheduled; `tutorial_trails_enabled` is a reserved
byte initialized to zero. The earlier bounded optional trail renderer remains
dormant. The reviewed three-choice menu and highlight still use their existing
private canvas; that exceptional UI construction never gates player placement.
Movement repeats at one selected simulation interval rather than seven; the
15-interval double-tap threshold is unchanged. Focused PAL/NTSC evidence is recorded in
[the responsiveness report](tutorial-responsiveness.md); appearance review remains pending.

`tutorial_progress_reset` retires old observations
when an accepted position request changes generation. The next separately
admitted publication uses immutable original `plane0`, selected native player
poses and the latest edited XY. Old ball/shadow payload is hidden until an actual
current-generation alternative provides it. No bitmap copy precedes placement.

After each returned `game_preview_step` or successful READY-result read,
`tutorial_progress_returned` copies only
current-generation counts/outcomes and qualifies observed availability. It does
not render, call a core body or modify admission timers; D5/D6 are preserved.
Latest-placement readiness and continued `tutorial_work_pending` are independent,
so a held result can publish while the released continuation still runs. Dense
ball/shadow animation uses actual samples at the existing two-points per two-ticks
cadence, then holds the last actual sample and its actual visibility without
wrapping. No ninth sprite or separate constant endpoint marker is introduced.
Due animation precedes preview workers and gets fresh admission. Pure placement
and animation publication use a 5000-Eclock finishing reserve; caption
raster work retains the separate 10000-Eclock reserve. Unchanged caption pointers
skip all raster writes. The lower reserve passed the focused PAL/NTSC complete-callback checks. It is not
a universal bound. Bounded menu copy/text/publication also use this reserve and
repeat with a fresh remaining-time check after each unit; optional ghost/path
work retains 10000 E-clock ticks.

The native source exposes these presentation fields:

- `tutorial_placement_dirty`, `tutorial_placement_ready`, `tutorial_marker_ready`,
  `tutorial_animation_ready`, `tutorial_waiting_ready`, `tutorial_trails_enabled`:
  bytes.
- `tutorial_presentation_generation`, `tutorial_marker_generation`,
  `tutorial_animation_generation`, `tutorial_visible_surface`: longs.
- `tutorial_available_counts`, `tutorial_available_outcomes`: two words each.

The added declared storage is 38 bytes, including two caption-pointer cache longs
and narrowing the old timer to a word callback cursor;
actual alignment increases layout by 40 bytes versus `8e66edc`. Current loaded
code/data/BSS and whole initialized free chip measurements are in the linked report.
READY (status 4) describes published stopped-alternative presentation, not backend
pair completion. Marker-ready additionally requires an actual accepted launch,
nonempty samples and a landing/net/out/interception outcome. WAITING (status 6)
is distinct: actual released current-serve continuation has dispatched, remains
in human phase 0x40, and has no accepted launch. It displays the hold-F/B1 hint,
without inventing a landing or changing backend outcome 6/256-point horizon.
UNAVAILABLE remains status 5. Footer text explicitly identifies an unfinished
other alternative. F and joystick B1 still choose held/released presentation.

The source-only checks cover local branch references, tutorial symbol references,
32-character footer widths and diff whitespace.
No builder, emulator or actual-CPU proof ran in the author worktree. Integration
must compare actual complete publication banks and native sprites, latest-XY
supersession, held endpoint versus released waiting, ongoing other-alternative
work, dense animation, full318/all72/live-backup preservation and Resume latest.
Integration has completed focused PAL/NTSC callback, ownership, loaded-byte and
initialized-RAM checks. Root owns that execution; the author-only checks above
do not establish those results.

The focused observer binds placement readiness to the actual published render
epoch and marker/playback mode. Literal writes reconstruct immutable queued and
displayed sprite bytes; native headers and retained frame payloads must match the
prepared latest actor and actual sampled ball/shadow positions. It records request
to player/endpoint/waiting publication latency and dense animation step intervals.
PNG metadata proves a stable background; it does not identify an exact current
animation sample. Host rejection checks do not establish a native pass.

The first static PAL proof found entry-timer quantization made playback about
21.5% slower than game time. The narrow repair schedules two samples per two
native callbacks using a wrapping word cursor. Advancing that nominal cursor
instead of resetting it to a late entry preserves cadence without accumulating
delay. The focused complete-callback and aggregate timing checks now pass; broader
workloads and full acceptance remain outstanding.
