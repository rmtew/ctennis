# Side-player title menu

Local implementation based on master `21c370f0a614a4ea58f3efdb5c9fea41a5959b0e`.
The approved side-player layout and native B adaptation are implemented. The
user attached the selected three-concept image directly after Library transfer
failed; the actual B pixels were visually inspected before adaptation. Its
paired blue/red rackets, white BASELINE, blue RALLY with a white edge, and central
ball are preserved. Hand-authored block lettering and simplified racket strings
fit the native header; the ball uses the existing gold-yellow palette slot.
This is an intentional pixel adaptation, not a claim of exact artwork resampling.
The native preview was displayed before committing the adaptation.

`author_title_logo_b.py` documents the reproducible native authoring. Only the
first76 rows of the existing four6144-byte planes change; all lower pixels and
the complete title palette remain byte-identical. Logo artwork ends at y75,
leaving16 blank rows before labels at y92. There is no extra bitmap allocation.

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
  states of the previously approved standalone layout preview. The full native B
  title region also matched its versioned planes in the host preview. These are host/static checks, not emulator scanout.
- The ordinary physical-input suite now visits all eight states, captures each
  complete menu, checks wraparound, Mode action toggling, and an irrelevant right
  press outside Mode. Run `RUST_LOG=info python3 scripts/run_enhanced_menu_tests.py
  --help-only` and the focused native setup timing check when tools are available.

Pinned tools were recovered through the procedure in ../ct12/checkpoint.md:
vasm commit685a87e reproduced the locked SHA256, and the official Copperline
AppImage matched e69e732f...89ce5. Native assembly now passes. The earlier
missing-tool blocker is resolved. Focused native input/scanout and setup timing
results are recorded separately under ignored build/tests; consult their exact
commit/input hashes. No full native acceptance claim is made.

Preview display follows the project's PAL presentation: constructed raw field
716x285 with title origin (126,16), native X doubled, then nearest-neighbour
display at 716x537 (4:3). This is not a square-pixel enlargement of the 256x192
active title crop. The preview identifies the fitted B artwork and distinguishes host cache renders
from actual emulator scanout.
