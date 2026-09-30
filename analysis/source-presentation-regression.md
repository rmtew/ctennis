# Original-game presentation references and native comparison

The retained P1 source record is private under
`tests/reference/presentation/manifest.json`. Tracked recipes, capture code and
validators reproduce it from the user's cartridge. Source collection and native
parity are separate: the native title test is registered; other native P1 cases
and P2/P3 remain open.

## Capture and source checks

The observer wraps each frozen R1/R2 physical-input policy, without CPU/game-state
writes. Both runs must retain the exact accepted callback capture hash. Every
selected frame retains 1KB RAM, 16KB VRAM, eight actual VDP register values, PC,
host-endian RGB bitmap words, whole-raster PNG and active-area PNG. Repeated
decoded pixels and hardware bytes must agree. Artifact hashes are checked again
before freezing; a deliberately changed raw raster was rejected and restored.

The TMS observer follows control-write pairs, treats a second byte's bit 7 as a
register command, applies the device's register masks, and cancels the control
latch on status or VRAM-data transfers. MAME's pinned device configuration adds
12 border pixels on each side of its 256x192 active picture. These details come
from [MAME mame0289 TMS source](https://github.com/mamedev/mame/blob/mame0289/src/devices/video/tms9928a.cpp).
The bitmap is read using [MAME's screen pixel API](https://docs.mamedev.org/luascript/ref-devices.html#screen-device)
and encoded losslessly; it is not resampled through a snapshot layout.

An earlier preview suggested alternating nearly blank title pictures. That
diagnosis is withdrawn: retained frame-119 and frame-299-to-302 PNGs contain
complete title pixels, with RGB hash prefix `956da2404512` and nonblack bounds
(28,28)-(260,187). Reading the original-size image and inspecting the bytes
resolved the misleading preview. There is no demonstrated source-output or
snapshot-renderer defect.

The current record has 263 R1 and 312 R2 rasters. It covers the required named
title/mode, both-end serve wait/action/launch/first-flight, first lower/upper
contact, bounce/net/out, distinct point pairs, all status messages, and
game/match/result/title-return/restart windows. Neighbouring frames are retained.
There are 57 R1 and 65 R2 field observations, each with captured display pixels
matching the ROM glyph record selected by observed source state. No requested
field is missing from its window. Point-code aliases remain separate logical
observations even where their glyphs are identical.

`presentation_reference.py` is a test-only static hardware decoder, following
the pinned MAME implementation. It cross-checks captured pixels against captured
VRAM/registers; it does not generate the reference image or run game physics.
Every named checkpoint matches a captured hardware state. Some moving frames
match earlier states; some neighbouring boundary frames have no complete static
match. All associations and unmatched frames are retained in
`raster-validation.json`, rather than assuming the current RAM, current VRAM and
captured bitmap share a generation. Field reports record the first captured
display of the selected glyph and whether it was already visible before the
trigger. Whole-match display integrity and target scheduling remain P3 work.

## Actual native graphics test

The installed `copperline-ctl --mcp` exposes a headless control bridge. The small
stdlib client launches its own exact A500/OCS/PAL/68000/512K-chip/zero-fast/slow
session, waits through the `LoadSeg` stop, runs the application for the declared
interval, and captures a completed frame. It closes only its own session. A
request observation timeout continues waiting on the same live request.

The native capture is 716x285, rather than the GUI screenshot's vertically
rescaled 716x540. An exhaustive exact court-region match established a unique
viewport origin (62,16). Every horizontal pixel pair in the full viewport is
identical, proving the 2:1 horizontal and 1:1 vertical extraction; no interpolation
or approximate scale is used. The source-to-Amiga palette is fixed in the test
contract independently of the production palette table.

The title case compiles `amiga/gameplay_integration_probe.s` and uses its existing
initial serve data, verified identical to the frozen R1 initial post-tail image.
It sends no native controls and compares actual hardware pixels with the stable
original title. The current application starts at the court; title/menu startup
is absent. Its first observed difference is logical pixel (74,12), black expected
and native `cc55bb` observed. The comparator detects a changed first pixel; the
suite policy rejects changed signatures and unexpected passes. This case does
not claim coverage of other native scenes or fix the startup implementation.


## Live callback alignment and upper-player placement

The shared native builder emits an assembler listing without changing executable
bytes (SHA256 remains d974224c00c1c27b60cb5eda75009b21bfbede9d8b50a0376c9dd78a7c38a1ed).
Copperline's LoadSeg event identifies the relocated first code hunk. A conditional
PC breakpoint at simulation_update reads the actual simulation_updates word.
The diagnostic capture reaches exactly 0,17,18,63,134,135,136,166 completed updates,
without writing game memory or replacing its scheduling/input/hardware paths.
All 254 bytes match at 0,17,18,63. Later captures differ only at AI target C076
(source 212/native 172 in this run), following an uncontrolled refresh-sign
choice; this must not be treated as a presentation-only mismatch or ignored.

The registered p1-upper-player-placement comparison uses completed update 17.
Its source crop is byte-identical across frames 1314-1320; beam line 166 is past
that crop. All simulation bytes match. The expected pink pixel set spans X88-103,
the actual set X68-83, both Y12-39, with 254 pixels each. Translating every source
pixel by (-20,0) yields the exact actual set. The source/native differences thus
identify an origin error rather than physics or animation drift: native sprite
coordinates add $6c, 20 short of $80 for this viewport. The first differing crop
pixel is logical (74,12), source black/native cc55bb. No product correction is
made while establishing the red/green baseline.

A five-second initial-serve comparison was rejected: gameplay continues during
that interval, so its positions are not comparable to the initial source frame.
No case or known failure from that experiment was registered. Moving regions
still require explicit presentation generation and controlled entropy; this
invariant-region comparison does not complete the rest of P1.
