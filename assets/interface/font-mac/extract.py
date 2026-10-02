"""Offline Font-Mac authoring/validation; never invoked by a game build.

Requires the repository's pinned Pillow. No network, ROM or cartridge input.
"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
SOURCE_SHA256 = "b21998e5bc6d8227486a121f5d1fb0b1f62b13a7b6e70ba3129c967fd5fb4616"
# Visually inspected ASCII mapping: source order is NOT ASCII/codepoint order.
SOURCE_ROWS = (
    (104, "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef"),
    (114, "ghijklmnopqrstuvwxyz0123456789,."),
    (124, '-+*#!"%&/()=?;:'),
)
# Independently authored by Codex for Baseline Rally; not extracted/redrawn.
APOSTROPHE = [0x18, 0x18, 0x10, 0x20, 0, 0, 0, 0]
REQUIRED = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 ,.-+*!?/:;()'"
CREDITS = ["Font-Mac - creator unknown", "Archive: ianhan/BitmapFonts"]


def derive():
    raw = (ROOT / "Font-Mac.png").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == SOURCE_SHA256, "source hash changed"
    im = Image.open(ROOT / "Font-Mac.png").convert("RGB")
    assert im.size == (320, 256)
    assert {color for count, color in im.getcolors()} == {(0, 0, 0), (255, 255, 255)}
    ink = {(x, y) for y in range(256) for x in range(320)
           if im.getpixel((x, y)) == (255, 255, 255)}
    assert {y for x, y in ink} == set(range(104, 112)) | set(range(114, 122)) | set(range(124, 132))
    table = bytearray(128 * 8)
    entries = []
    covered = set()
    def cell(x, y):
        return [sum(1 << (7 - col) for col in range(8)
                    if (x + col, y + row) in ink) for row in range(8)]
    for y, chars in SOURCE_ROWS:
        for col, char in enumerate(chars):
            x = col * 8
            rows = cell(x, y)
            offset = ord(char) * 8
            table[offset:offset + 8] = bytes(rows)
            entries.append(dict(character=char, ascii=ord(char), offset=offset,
                                origin="Font-Mac", source_xy=[x, y], rows=rows))
            covered.update((x + dx, y + dy) for dx in range(8) for dy in range(8))
    # Seven visually inspected non-ASCII forms are retained but deliberately
    # unbound. The image has no authoritative encoding labels (last is beta/
    # sharp-s-like). They must never displace ASCII punctuation by assumption.
    unbound = []
    for col in range(15, 22):
        x, y = col * 8, 124
        unbound.append(dict(source_xy=[x, y], rows=cell(x, y)))
        covered.update((x + dx, y + dy) for dx in range(8) for dy in range(8))
    assert ink <= covered, "unaccounted source ink"
    entries.append(dict(character=" ", ascii=32, offset=256,
                        origin="blank spacing", rows=[0] * 8))
    table[39 * 8:40 * 8] = bytes(APOSTROPHE)
    entries.append(dict(character="'", ascii=39, offset=312,
                        origin="independently authored Baseline Rally punctuation",
                        rows=APOSTROPHE))
    entries.sort(key=lambda entry: entry["ascii"])
    supported = {entry["character"] for entry in entries}
    missing = sorted(set(REQUIRED) - supported)
    assert not missing, f"missing required characters: {missing}"
    for text in CREDITS:
        assert not set(text) - supported
    manifest = dict(
        name="Font-Mac — creator unknown", source_sha256=SOURCE_SHA256,
        source_git_blob_sha1="fa26bc065dbb933759778fadf8fe7ed2485512d8",
        source_url="https://github.com/ianhan/BitmapFonts/blob/c13d9c452f0bb0f7449ceda44ea2b69f591c9acf/fonts/Font-Mac.png",
        width=8, height=8, advance=8, bytes_per_glyph=8,
        encoding="ASCII slots 0..127; bit7 leftmost; rows top to bottom; 1 is ink",
        table_bytes=len(table), supported_glyphs=len(entries),
        source_glyphs=sum(len(chars) for y, chars in SOURCE_ROWS),
        required_characters=REQUIRED, missing_required_characters=missing,
        unsupported_printable_ascii="".join(chr(c) for c in range(32, 127) if chr(c) not in supported),
        unsupported_policy="zero-filled slots are unavailable, not substitutions; validate text before rendering",
        glyphs=entries, unbound_source_cells=unbound,
        binary_sha256=hashlib.sha256(table).hexdigest(), credit_lines=CREDITS,
    )
    return bytes(table), manifest


def validate_pixels(table, manifest):
    """Decode each committed bit independently and compare to the actual PNG."""
    im = Image.open(ROOT / "Font-Mac.png").convert("RGB")
    count = 0
    for entry in manifest["glyphs"]:
        if entry["origin"] != "Font-Mac":
            continue
        x, y = entry["source_xy"]
        for row in range(8):
            for col in range(8):
                actual = bool(table[entry["offset"] + row] & (0x80 >> col))
                expected = im.getpixel((x + col, y + row)) == (255, 255, 255)
                assert actual == expected, (entry["character"], row, col)
                count += 1
    for entry in manifest["unbound_source_cells"]:
        x, y = entry["source_xy"]
        for row in range(8):
            for col in range(8):
                assert bool(entry["rows"][row] & (0x80 >> col)) == (im.getpixel((x + col, y + row)) == (255, 255, 255))
                count += 1
    return count


def proof(table, destination):
    lines = ["ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz",
             "0123456789 ,.-+*!?/:;()'", '-+*#!"%&/()=?;:',
             "Start game   Players: 1", "How to play   Controls", *CREDITS]
    im = Image.new("RGB", (max(map(len, lines)) * 8, len(lines) * 10), "black")
    for line, text in enumerate(lines):
        for column, char in enumerate(text):
            for row in range(8):
                for bit in range(8):
                    if table[ord(char) * 8 + row] & (0x80 >> bit):
                        im.putpixel((column * 8 + bit, line * 10 + row), (255, 255, 255))
    im.resize((im.width * 3, im.height * 3), Image.Resampling.NEAREST).save(destination)


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--write", action="store_true", help="explicit offline regeneration")
    parser.add_argument("--proof", type=Path, help="optional proof PNG destination")
    parser.add_argument("--text", action="append", default=[], help="reject unavailable characters in integration text")
    args = parser.parse_args()
    table, manifest = derive()
    encoded = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    if args.write:
        (ROOT / "font.bin").write_bytes(table)
        (ROOT / "character-map.json").write_text(encoded, encoding="utf-8")
    assert (ROOT / "font.bin").read_bytes() == table, "committed binary differs"
    assert (ROOT / "character-map.json").read_text(encoding="utf-8") == encoded, "committed map differs"
    checked = validate_pixels((ROOT / "font.bin").read_bytes(), manifest)
    supported = {entry["character"] for entry in manifest["glyphs"]}
    for text in args.text:
        missing = sorted(set(text) - supported)
        if missing:
            parser.error(f"missing required characters in {text!r}: {missing}")
    if args.proof:
        proof(table, args.proof)
    print(f"PASS: {checked} source pixels / 86 source cells; {len(table)} native bytes; "
          f"{len(supported)} supported ASCII glyphs; missing required: []")
    print("Unavailable printable ASCII: " + manifest["unsupported_printable_ascii"])


if __name__ == "__main__":
    main()
