"""Convert captured gameplay VDP state to four Amiga planes and eight sprites."""

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "build" / "reference" / "source-timing"
OUTPUT = ROOT / "build" / "amiga" / "sprite-probe"
PALETTE = {
    0: 0x000, 1: 0x000, 2: 0x2C4, 3: 0x6D7, 4: 0x55E,
    5: 0x77F, 9: 0xF77, 10: 0xDC5, 13: 0xC5B,
    14: 0xCCC, 15: 0xFFF,
}


def word(value):
    return value.to_bytes(2, "big")


def pattern_row(vram, pattern, row):
    base = 0x1800 + (pattern & 0xFC) * 8
    offset = row % 8 + (8 if row >= 8 else 0)
    return (vram[base + offset] << 8) | vram[base + 16 + offset]


def main():
    vram = (SOURCE / "sprite-f1310.vram").read_bytes()
    ram = (SOURCE / "sprite-f1310.ram").read_bytes()
    if len(vram) != 0x4000 or len(ram) != 0x400:
        raise ValueError("Missing controlled frame-1310 capture")
    if vram[0x3B00:0x3B28] != ram[0x10:0x38]:
        raise AssertionError("Sprite attribute buffers differ")
    OUTPUT.mkdir(parents=True, exist_ok=True)

    planes = [bytearray(192 * 32) for _ in range(4)]
    indices = set()
    for y in range(192):
        bank = (y // 64) * 0x800
        for x in range(256):
            tile = vram[0x3800 + (y // 8) * 32 + x // 8]
            line = y % 8
            pattern = vram[0x2000 + bank + tile * 8 + line]
            colour = vram[bank + tile * 8 + line]
            index = colour >> 4 if pattern & (0x80 >> (x % 8)) else colour & 15
            indices.add(index)
            for plane, data in enumerate(planes):
                if index & (1 << plane):
                    data[y * 32 + x // 8] |= 0x80 >> (x % 8)
    if not indices <= PALETTE.keys():
        raise ValueError(f"Unknown SG colours: {indices - PALETTE.keys()}")
    for plane, data in enumerate(planes):
        (OUTPUT / f"plane{plane}.bin").write_bytes(data)

    sprite_pattern_rows = bytearray(2048)
    for pattern in range(0, 256, 4):
        for row in range(16):
            offset = pattern * 8 + row * 2
            sprite_pattern_rows[offset:offset + 2] = word(pattern_row(vram, pattern, row))
    (OUTPUT / "sprite-pattern-rows.bin").write_bytes(sprite_pattern_rows)

    records = [(i, tuple(ram[0x10 + 4 * i:0x14 + 4 * i])) for i in range(10)]
    active = [(i, record) for i, record in records if record[0] < 0xC0 and record[3] & 15]
    if [i for i, _ in active] != [1, 2, 3, 4, 5, 6, 7, 9]:
        raise AssertionError("Controlled frame sprite order changed")
    pair_palettes = []
    for pair in range(4):
        colours = list(dict.fromkeys(record[3] & 15 for _, record in active[pair * 2:pair * 2 + 2]))
        if len(colours) > 3:
            raise AssertionError("Amiga sprite pair palette overflow")
        pair_palettes.append(colours)

    for channel, (source_index, (y, x, pattern, colour)) in enumerate(active):
        colour_code = pair_palettes[channel // 2].index(colour & 15) + 1
        # The SG attribute Y is one before the first displayed row. The Amiga
        # window begins at raster Y=$2C; HSTART=$36 is the left edge for this
        # 256-pixel fetch/window placement. Each HSTART step is two SG pixels.
        vstart = 0x2C + y + 1
        vstop = vstart + 16
        hstart = 0x36 * 2 + x
        pos = ((vstart & 0xFF) << 8) | ((hstart >> 1) & 0xFF)
        ctl = ((vstop & 0xFF) << 8) | (((vstart >> 8) & 1) << 2) | (((vstop >> 8) & 1) << 1) | (hstart & 1)
        stream = bytearray(word(pos) + word(ctl))
        for row in range(16):
            pixels = pattern_row(vram, pattern, row)
            stream += word(pixels if colour_code & 1 else 0)
            stream += word(pixels if colour_code & 2 else 0)
        stream += bytes(4)
        (OUTPUT / f"sprite{channel}.bin").write_bytes(stream)

    report = {
        "source_vram_sha256": hashlib.sha256(vram).hexdigest(),
        "background_colours": sorted(indices),
        "bitplane_bytes": sum(map(len, planes)),
        "source_sprite_slots": [i for i, _ in active],
        "pair_source_colours": pair_palettes,
        "sprite_bytes": 8 * 72,
        "sprite_pattern_rows_sha256": hashlib.sha256(sprite_pattern_rows).hexdigest(),
        "output": str(OUTPUT),
    }
    (OUTPUT / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
