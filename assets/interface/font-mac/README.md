# Font-Mac private native UI asset

**Font-Mac — creator unknown.** Exact public archive PNG retained for the
user-approved private Baseline Rally prototype. Archive maintainer ianhan is
not credited as the font's creator. No ownership, license, or public
redistribution clearance is claimed. This font has no cartridge/ROM dependency;
its provenance is separate from the game's other retained assets.

Source archive: [ianhan/BitmapFonts, fonts/Font-Mac.png](https://github.com/ianhan/BitmapFonts/blob/main/fonts/Font-Mac.png).
Pinned source: [c13d9c452f0bb0f7449ceda44ea2b69f591c9acf](https://github.com/ianhan/BitmapFonts/blob/c13d9c452f0bb0f7449ceda44ea2b69f591c9acf/fonts/Font-Mac.png).
Fetched through the supported GitHub file tool; pinned and main responses
contained the same blob. Retrieved 2026-10-02.

- Source Git blob SHA1: `fa26bc065dbb933759778fadf8fe7ed2485512d8`.
- Source PNG SHA256: `b21998e5bc6d8227486a121f5d1fb0b1f62b13a7b6e70ba3129c967fd5fb4616`.
- Native binary SHA256: `0cac150a456a400258d9e065b947331bfea451bac4aa26547c5a4ddcfaebcac7`.

## Pixel mapping and provenance

The actual image is 320×256 pixels, with only black background and white ink
(2,310 white pixels). Glyphs use fixed 8×8 cells, eight-pixel horizontal advance,
at x=8×column. The rows start at y=104,114,124; there are two blank scanlines
between rows. No scaling, trimming, shifting, smoothing or redraw is applied.
Some glyphs (X, slash and asterisk) occupy all eight columns; Q and lowercase
descenders use row 7. Preserve these pixels and the full eight-row cell.

| Source row | Columns | Inspected characters in source order |
| --- | --- | --- |
| y=104 | 0–31 | `ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef` |
| y=114 | 0–31 | `ghijklmnopqrstuvwxyz0123456789,.` |
| y=124 | 0–14 | `-+*#!"%&/()=?;:` |
| y=124 | 15–21 | Seven non-ASCII forms; retained as unbound cells in JSON |

The last seven forms visually resemble accented letters and a beta/sharp-s
form. The PNG supplies no authoritative encoding labels, so they are not
assigned guessed codepoints or used as ASCII punctuation. All 86 ink-bearing
source cells are accounted for, including these unbound cells.

`character-map.json` gives explicit ASCII slot, byte offset, source coordinate,
and all eight row bytes for each mapped character. It separates blank space
and the independently authored apostrophe from source glyphs. The apostrophe
(ASCII39) is a tiny original punctuation addition authored by Codex for this
prototype, rows `18 18 10 20 00 00 00 00` in hex. It was not copied from another
font or derived by editing a Font-Mac glyph. No existing Font-Mac glyph was
redrawn. Space is an explicitly blank eight-pixel advance.

Supported: uppercase/lowercase A–Z/a–z, digits 0–9, space, and
`, . - + * # ! " % & / ( ) = ? ; : '`. Required menu/help set in the map has no
missing characters after the apostrophe addition. Unavailable printable ASCII:
`$ < > @ [ \ ] ^ _ ` followed by backtick and `{ | } ~`.
Unsupported slots are zero-filled storage, **not valid blank substitutions**.
Validate final UI/version strings and report unavailable characters before
integration. Unicode en/em dashes and typographic quotes are unavailable.

## Integration contract and cost

`font.bin` is exactly 1,024 bytes: 128 ASCII slots × eight row bytes. For ASCII
character c, read bytes `[8*c, 8*c+8)`, bit7 leftmost and bit0 rightmost;
1=ink and 0=background. Advance eight pixels; draw all eight rows. There are
81 supported glyphs: 79 extracted, blank space, and authored apostrophe.
Their rows use 648 bytes; 47 unavailable slots use 376 zero-padding bytes.

This matches the existing `ui_text` byte-at-a-time 68000 layout and the existing
1,024-byte UI table size. Replacement therefore adds zero font-table RAM;
keeping both tables adds 1,024 bytes (chip RAM if placed with existing chip
data). Character lookup costs zero extra runtime bytes: ASCII×8 is the lookup.
JSON, source PNG, proof and extraction script are authoring inputs and need no
runtime memory. No additional pointers, widths, font engine or decompression.

The runtime font is installed at `assets/native/title/font-mac.bin` and registered
in the native manifest. `amiga/game/interface.s` loads it. The offline UI page
builder uses the same installed binary. This directory retains the source PNG,
explicit character map, extraction script and verified authoring binary.

The 28-character, 224-pixel UI width remains valid. The renderer controls line
origins, stride and palette. Extraction checks do not certify native readability.

Ready-to-use final help-page credit lines, 26 and 27 ASCII characters:

```text
Font-Mac - creator unknown
Archive: ianhan/BitmapFonts
```

The exact descriptive credit for prose/metadata is
`Font-Mac — creator unknown`.

## Focused validation

From repository root:

```sh
python assets/interface/font-mac/extract.py
python assets/interface/font-mac/extract.py --text "Start game" --text "Font-Mac - creator unknown"
```

The offline validator checks exact source hash, dimensions, colors and ink rows;
accounts for all source ink; regenerates and compares the committed binary/map;
and independently decodes every bit in all 86 cells against source pixels
(5,504 pixel comparisons). It checks required character coverage and rejects
unavailable characters supplied by `--text`. This is focused extraction
validation, not the native acceptance gate.

Explicit authoring only: `--write` regenerates binary/map; `--proof /tmp/proof.png`
creates an optional nearest-neighbor glyph/text proof from the native bytes.
Neither extraction nor PNG loading occurs during a game build.
