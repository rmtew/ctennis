# Two-player physical input calibration

Recorded 2026-09-30 using pinned MAME 0.289 SC-3000 and the verified cartridge.
Reproduce with `python scripts/capture_input_map.py`. Two raw captures agree
byte-for-byte (SHA256 `e6fa3b7fb4b5862eb7b4dac70e0a1b74a297764fcc840b2882b6eb58bffbb3da`).
The private `tests/reference/input-map.json` retains 562 complete callbacks,
14 press observations, raw control events, exact input-reader returns and
all entry/pre-tail/return states. It records ROM, emulator and script hashes.

Select two-player mode with SK-1100 `:sgexp:sk1100:PB5`, mask `$08` (Func):
set_value(1) at frame 120, clear_value() at 420. The retained initial state has
mode flags `$80`. One-player selection remains PA3 mask `$10` (Del/Ins).
Every gamepad test presses with set_value(1), releases with clear_value(),
and retains a 24-source-frame hold followed by 16 neutral frames. Callback
IDs and consumed inputs are recorded; frame durations are not assumed to be
callback durations.

| Physical control | JOYPAD field mask | Normalized input-reader value |
|---|---:|---:|
| Up | $01 | $02 |
| Down | $02 | $08 |
| Left | $04 | $04 |
| Right | $08 | $01 |
| Button 1 | $10 | $10 |
| Button 2 | $20 | $20 |

The table applies to both `:ctrl1:mspad:JOYPAD` and
`:ctrl2:mspad:JOYPAD`. Pad 1 appears in input-reader group 0; pad 2 appears in
group 1. In separate-input mode, source input_direction_a combines pad 1's
low direction nibble with pad 2's direction nibble shifted left four bits;
input_direction_b combines pad 1 actions shifted right four with pad 2 actions
in bits 4/5. These are diagnostic source fields, not a required native state ABI.

Pad 1 controls the lower player; pad 2 controls the upper player in the retained
mode. The simultaneous interval at frames 1820-1844 holds pad 1 Right and pad 2
Left: readers return 1 and 4, normalized direction is $41, lower player X moves
59 to 92 and upper X moves 157 to 128 in the retained comparison interval.
The players respond independently. Earlier lower Left moves X 189 to 156,
and Right moves 159 to 192; upper Down moves Y 10 to 43. Positions are source
observations, not prescribed movement distances. Some individual holds encounter
bounds or phase blocks; identical endpoints do not imply a broken input.

Button values are confirmed at both input readers and normalized fields.
Button 1 on the lower player starts actual play during this sequence; later
upper buttons are exercised in the resulting phases. This establishes the
physical mapping, not successful returns for both players, all reachable
movement rows, or complete mode/side-transition coverage. The R2 varied match
must still retain those behaviours and a full result/restart. A separate
both-buttons-held discovery is diagnostic only until its outcomes and variety
are inspected and a final schedule is frozen twice.

Side ownership changes are explicit in the annotated source:
normalize_input_for_player_side rotates the combined control nibbles when
mode_status_flags bit 4 differs from the requested court end. Thus pad 1 is
lower and pad 2 upper only with that side bit clear; the assignments exchange
when it is set. The initial and simultaneous calibration intervals exercise
the clear-bit mapping. The full R2 observes both side modes, while further
focused movement checks across a side change remain to be indexed. A first
normal-return discovery mistakenly pulsed actions by court end without this
exchange and stalled waiting for serve; it is rejected diagnostic data.
