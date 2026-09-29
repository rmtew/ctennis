# Horizontal Copper score selection probe

The scoreboard routine's VDP name-table destinations identify six changing regions in the source 256-by-192 picture:

| Field | Tile destination | Source pixel rectangle |
| --- | --- | --- |
| A point | `$38A2`, two rows | x=16-31, y=40-55 |
| B point | `$38BC`, two rows | x=224-239, y=40-55 |
| A game tally | `$3922`, six rows | x=16-31, y=72-119 |
| B game tally | `$393C`, six rows | x=224-239, y=72-119 |
| Centre status | `$398E`, one row | x=112-135, y=96-103 |
| Mode text | `$3A5A`, one row | x=208-247, y=144-151 |

These positions come from the source 32-tile-wide name table at `$3800` and the addresses in `scoreboard_update_06eb`. They describe the fields that the routine can change, not necessarily every visible scoreboard mark.

`python scripts/run_amiga_score_copper_probe.py` assembles a separate PAL A500 OCS executable using the current static court and sprites. It pre-renders the A point values zero and 15 into two Amiga plane-2 row banks. The point tiles' visible colour is SG index 5, mapped to Amiga palette index 5. In this black-margin rectangle, plane 0 can be set to one throughout: background then selects palette index 1 (black), and a plane-2 glyph pixel selects index 5 (violet). Planes 1 and 3 remain zero. Consequently the probe needs to redirect only the plane-2 pointer.

For each of the 16 source rows, the Copper waits at horizontal position `$3D` and loads the alternate plane-2 pointer, then waits until `$D1` to load the base pointer for the following row. The 68000 patches the 16 alternate pointer values during vertical blank according to port-2 fire. The same executable is captured once without fire and once with fire. This is direct selection between pre-rendered Amiga graphics; no runtime VDP write or tile interpretation drives the display.

On Copperline's exact PAL A500, OCS, 68000, 512 KB chip, no slow/fast RAM, Kickstart 1.3 profile, the [zero screenshot](../build/amiga/score-copper-probe/score-point-0.png) has identical score-region pixels to the original static Amiga capture. The [15 screenshot](../build/amiga/score-copper-probe/score-point-1.png) differs from zero only within screenshot rectangle x=53-81, y=104-123, inside the intended 16-by-16 source pixel field. The [toggle GIF](../build/amiga/score-copper-probe/score-toggle.gif) shows the same executable switching when fire is held. The probe's diagnostic sweep found `$3D` to be the horizontal wait that starts at source x=16; later waits advance the altered word position in 16-pixel steps. An earlier failed sweep encoded even low bytes in Copper WAIT words, making them MOVE instructions; the reproducible probe sets the instruction bit correctly.

This proves the isolated left-point selection in Copperline. It does not yet prove the right point field, the taller game counters, centre status, mode text, or concurrent changes with live gameplay. The probe's generated ADF under `build/amiga/score-copper-probe/` is prepared for WinUAE, but no WinUAE visual capture has been verified. The live game still has a static scoreboard and shadow VDP writes. The next integration should select all needed graphics from game score/status state and compare the displayed result with a source scoring capture.
