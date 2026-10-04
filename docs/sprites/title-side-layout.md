# Side-player title menu

The title uses the approved paired-racket concept B. Its native adaptation
has white BASELINE lettering, blue RALLY lettering with a white edge, paired
Blue/Red rackets and a green tennis ball. The original concept was visually
inspected before adaptation. The native pixels are an intentional redraw,
not exact resampling of that concept.

`author_title_logo_b.py` reproduces the header in the existing four title
planes. Run it from the checkout with the pinned Pillow version. It updates
only the first 76 rows and the manifest hashes. Review its diff before use.
Pixels below row 75, plane sizes and palette entries remain unchanged.

The bitmap is 256×192. Font-Mac uses 8×8 cells. Menu rows start at x96 and
y114, 125, 136 and 147. Their labels are Start, Mode, Help and Controls.
Only the selected word's cells are inverted.

A/B labels are centred at x48/x208, y92. Human/AI labels are at y102.
A stays Blue and human. B stays Red and changes between human and robot with
the remembered mode. The figures start at (40,114) and (200,114), with 16×32
body bounds. The title renderer uses presentation state, not gameplay updates.

`ui_title_row_copy` updates the eight central bytes of each row in all four
planes. This preserves the side figures. Help-page selection uses the
full-row copy routine. Title caches occupy 29,696 bytes; selected menu caches
occupy 1,024 bytes.

Run the host layout test with:

```sh
python -m unittest discover -s tests/unit -p test_title_side_layout.py -v
```

It checks all eight mode/selection states against independent font, pose and
palette rules. The physical-input suite visits these states and checks actual
scanout. Run `RUST_LOG=info python scripts/run_enhanced_menu_tests.py --help-only`
with the configured native tools and external Kickstart. See
[native acceptance](../../tests/README.md) for setup and timing checks.

For preview display, construct a 716×285 PAL field with title origin (126,16).
Double native X, then display at 716×537 with nearest-neighbour scaling.
Identify whether a preview uses host-rendered caches or emulator scanout.
