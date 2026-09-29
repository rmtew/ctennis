"""Verify title name-table and transformed sprite transfers against ROM and VRAM."""

import configparser
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def main():
    config = configparser.ConfigParser(interpolation=None)
    config.read(ROOT / "config.local.ini", encoding="utf-8")
    rom = Path(config["inputs"]["cartridge"]).read_bytes()
    vram = (ROOT / "build/smoke/vram-reset-120.bin").read_bytes()
    state = json.loads((ROOT / "build/smoke/hardware-state-reset-120.json").read_text())
    assert len(rom) == 0x2000 and len(vram) == 0x4000
    assert hashlib.sha256(vram).hexdigest() == state["vram_sha256"]

    # 055F interleaves two 16-byte halves of each 32-byte ROM block in RAM,
    # swapping their order. 00D1 then bit-reverses the 0x340-byte result.
    interleaved = b"".join(
        rom[0x19CC + block * 32 + 16:0x19CC + block * 32 + 32]
        + rom[0x19CC + block * 32:0x19CC + block * 32 + 16]
        for block in range(26)
    )
    reversed_bits = bytes(int(f"{value:08b}"[::-1], 2) for value in interleaved)
    sprite_mismatches = [
        (f"{i:03X}", f"{a:02X}", f"{b:02X}")
        for i, (a, b) in enumerate(zip(vram[0x1C00:0x1F40], reversed_bits)) if a != b
    ]
    assert sprite_mismatches == [("003", "FB", "00")], sprite_mismatches[:16]

    # 040D-045E calls 0542 to copy fixed-width rows with a 32-byte VRAM stride.
    row_groups = [
        (0x0482, 0x38C6, 4, 0x11),
        (0x04C6, 0x38D6, 4, 0x11),
        (0x050A, 0x3842, 2, 2),
        (0x050E, 0x385C, 2, 2),
        (0x0512, 0x38A1, 4, 10),
        (0x0512, 0x38BB, 4, 10),
        (0x053A, 0x3A21, 4, 2),
    ]
    initial_row_matches = 0
    initial_row_bytes = 0
    for source, destination, width, rows in row_groups:
        for row in range(rows):
            start = source + row * width
            target = destination + row * 0x20
            initial_row_matches += sum(
                a == b for a, b in zip(vram[target:target + width], rom[start:start + width])
            )
            initial_row_bytes += width
    assert initial_row_bytes == 232 and initial_row_matches == 232

    # 0357-0373 copies three literal title strings directly to consecutive
    # portions of title name-table VRAM.
    title_strings = [
        (0x03BA, 0x3E03, 0x1B),
        (0x03D5, 0x3E64, 0x19),
        (0x03EE, 0x3EA4, 0x19),
    ]
    for source, destination, length in title_strings:
        assert vram[destination:destination + length] == rom[source:source + length]

    report = {
        "rom_sha256": hashlib.sha256(rom).hexdigest(),
        "vram_sha256": state["vram_sha256"],
        "verified_transformed_sprite_bytes": len(reversed_bits) - len(sprite_mismatches),
        "sprite_runtime_differences": sprite_mismatches,
        "initial_name_table_row_groups_from_code": len(row_groups),
        "initial_row_bytes_still_matching_at_title": initial_row_matches,
        "initial_row_bytes_total": initial_row_bytes,
        "verified_title_strings": len(title_strings),
        "sprite_attribute_first_40": vram[0x3B00:0x3B28].hex(),
        "title_name_nonzero_count": sum(bool(x) for x in vram[0x3C00:0x3F00]),
    }
    out = ROOT / "build/analysis/title-layout-report.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
