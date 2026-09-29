# Native Copper scoreboard selection

The source scoreboard routine can change six regions in its 256-by-192 picture. The addresses are offsets in the 32-tile-wide name table at `$3800`:

| Field | Tile destination | Source pixel rectangle | Values prepared |
| --- | --- | --- | --- |
| A point | `$38A2`, two rows | x=16-31, y=40-55 | 0-6 |
| B point | `$38BC`, two rows | x=224-239, y=40-55 | 0-6 |
| A game tally | `$3922`, six rows | x=16-31, y=72-119 | 0-6 |
| B game tally | `$393C`, six rows | x=224-239, y=72-119 | 0-6 |
| Centre status | `$398E`, one row | x=112-135, y=96-103 | 0-6 |
| Mode text | `$3A5A`, one row | x=208-247, y=144-151 | 0-2 |

`python scripts/run_amiga_score_copper_probe.py` prepares all 38 variants as Amiga bitplane banks from the captured tile graphics and assembles a separate PAL A500 OCS executable. Every prepared pixel is checked against its source colour. The runtime selects banks by patching Copper bitplane-pointer value words; it does not interpret VDP writes. Port-2 fire switches a demonstration state from points 0/0, games 0/0, status 0, mode 1 to points 1/2, games 1/2, status 1, mode 2. These are demonstration values, not a simulated scoring event.

The point glyphs use SG colour 5 on black. Fixing plane 0 to one inside the two point rectangles lets the Copper select plane 2 alone: palette index 1 is black and index 5 is the original violet. The game tallies similarly fix plane 3 and select plane 1, using black index 8 and the source's index-10 colour. The mode text fixes planes 0-2 and selects plane 3, using black index 7 and white index 15. These masks are confined to black-margin rectangles, and the baseline image proves they do not change visible pixels.

The centre status lies across the court and needs all four planes, including its original gray-and-black background. Switching four pointers at its horizontal edge produced a staggered fetch and damaged the net. The working Copper list instead selects a pre-rendered eight-scanline, full-width bank for all four planes at the start of status row 96, then restores the court planes at row 104. The left game tally changes plane 1 at x=16; a second plane-1 pointer change at x=64 resumes the selected status bank before its text at x=112. The right game tally changes plane 1 at x=224. This keeps the three fields independently selectable on the shared rows.

The calibrated horizontal waits are `$3D` for x=16, `$A1` for x=224, `$51` for the status plane-1 resumption at x=64, and `$99` for mode x=208. The Copper list has 224 patched pointer pairs. The 68000 changes those value words during vertical blank when the selected field state changes.

On Copperline's exact PAL A500, OCS, 68000, 512 KB chip, no slow/fast RAM, Kickstart 1.3 profile, the [original screenshot](../build/amiga/score-copper-probe/score-original.png) matches the existing static capture in all six fields. The [alternate screenshot](../build/amiga/score-copper-probe/score-alternate.png) changes pixels in all six regions and nowhere outside them. The [toggle GIF](../build/amiga/score-copper-probe/score-toggle.gif) shows both states from the same 100,940-byte executable. All 38 prepared variants passed the source-colour check. The ordinary sprite and live gameplay probes still pass with the shared display include.

This is a display prototype. Its source tile artwork comes from the controlled frame-1310 VRAM capture; later changes to pattern or colour tables have not been established. The live game still has a static scoreboard and shadow VDP writes; it does not yet choose these banks from game score/status state. The generated ADF is available under `build/amiga/score-copper-probe/`, but WinUAE visual validation has not been performed. The next integration step is to derive the six selectors directly from native game state and confirm a scored point changes the visible fields at the source update boundary.
