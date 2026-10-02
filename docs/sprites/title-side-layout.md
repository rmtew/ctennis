# Side-player title menu

Local implementation based on master `21c370f0a614a4ea58f3efdb5c9fea41a5959b0e`.
The approved side-player layout is implemented. Selected racket-framed logo B
remains pending: Library reference `libfile_438da231867481919e64be545e2c3253`
could not be materialized in this executor, and image read returned no pixels.
The existing BASELINE RALLY title and title palette are retained unchanged.
No substitute artwork is included.

## Native geometry and ownership

The title bitmap is 256x192. Font-Mac uses 8x8 cells. Menu rows start at x96,
y114/125/136/147: Start (40px), Mode (32px), Help (32px), Controls (64px).
The Help page itself retains its existing How to play heading and navigation.
Only the selected word's cells are inverted, as before.

A/B labels are centred on x48/x208 at y92, Human/AI beneath at y102. A stays
blue/human; B stays red and switches between human and robot with the remembered
mode. Human occupies [28,68) or [188,228), leaving 28px horizontal clearance
from the central menu [96,160). AI is centred in the same right-hand lane.
The two retained Classic ready composites start at (40,114)/(200,114), in
16x32 envelopes, leaving 40px horizontal clearance to the menu. Pose7's racket
mask is empty; pose0's retained white racket fits within its body envelope.
The normal title VS label remains at (120,92).

Normal rows and figures now share scanlines. `ui_title_row_copy` updates only
the eight central bytes per row across the four planes, avoiding erasure or
recolouring of the figures. Help-page selection retains the existing full-row
copy routine. The input dispatcher, title menu tick and UI state layout remain
byte-identical to the base commit; no gameplay role state is used to bake art.

## Footprint and validation

- Title caches: unchanged 29,696 bytes (two modes, four 256x116 planes).
- Selected menu caches: 1,024 bytes, down from 1,280; 256 chip-data bytes saved.
- A selected-row copy writes 256 bytes rather than 1,024. This is a static byte
  count, not a target timing measurement. Executable/code footprint is unmeasured.
- `python3 -m unittest discover -s tests/unit -p test_title_side_layout.py -v`
  passed: all eight static cache mode/selection states match the independently
  authored full-region font/pose/palette specification.
- `python3 -m unittest discover -s tests/unit -p test_identity_assets.py -q`
  passed all three existing identity-asset checks.
- `python3 scripts/native_assets.py` validated all 121 immutable inputs.
- The implementation-cache preview matched every native pixel in all eight
  states of the previously approved standalone layout preview. The existing
  title raster also matched. These are host/static checks, not emulator scanout.
- The ordinary physical-input suite now visits all eight states, captures each
  complete menu, checks wraparound, Mode action toggling, and an irrelevant right
  press outside Mode. Run `RUST_LOG=info python3 scripts/run_enhanced_menu_tests.py
  --help-only` and the focused native setup timing check when tools are available.

Native build attempted but blocked before assembly by missing pinned
`.tools/vasm/vasmm68k_mot.exe`. Copperline/configuration are also absent here.
Physical input, native raster, executable footprint and target timing tests were
therefore not run. No full native acceptance claim is made.

Preview display follows the project's PAL presentation: constructed raw field
716x285 with title origin (126,16), native X doubled, then nearest-neighbour
display at 716x537 (4:3). This is not a square-pixel enlargement of the 256x192
active title crop. The preview explicitly labels the B artwork as pending.
