"""Verify packed title masks against ordered VDP name-table writes."""

import configparser
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
WRITE = re.compile(r"DATA WRITE VRAM\[\$([0-9A-F]{4})\] <- \$([0-9A-F]{2})")


def main():
    config = configparser.ConfigParser(interpolation=None)
    config.read(ROOT / "config.local.ini", encoding="utf-8")
    rom = Path(config["inputs"]["cartridge"]).read_bytes()
    trace = json.loads((ROOT / "build/smoke/hardware-trace-reset-105.json").read_text())
    writes = [(int(m[1], 16), int(m[2], 16), index)
              for index, line in enumerate(trace["lines"])
              if (m := WRITE.search(line))]
    # A is the tile index; B is row count, C is mask bytes per row.
    groups = [
        (0x0376, 0x3C42, 0x69, 5, 4),
        (0x038A, 0x3D26, 0x69, 5, 3),
        (0x0399, 0x3C42, 0x62, 1, 3),
        (0x039C, 0x3C4C, 0x64, 10, 3),
    ]
    matches = []
    for source, destination, tile, rows, bytes_per_row in groups:
        expected = []
        for row in range(rows):
            for column in range(bytes_per_row):
                mask = rom[source + row * bytes_per_row + column]
                for bit in range(8):
                    if mask & (0x80 >> bit):
                        expected.append((destination + row * 32 + column * 8 + bit, tile))
        positions = [i for i, write in enumerate(writes)
                     if [(a, b) for a, b, _ in writes[i:i + len(expected)]] == expected]
        assert positions, f"no ordered VDP sequence for ROM {source:04X}"
        first = writes[positions[0]]
        matches.append({"rom_start": f"{source:04X}", "rom_bytes": rows * bytes_per_row,
                        "vram_start": f"{destination:04X}", "tile": f"{tile:02X}",
                        "rows": rows, "mask_bytes_per_row": bytes_per_row,
                        "set_bits_written": len(expected), "first_trace_index": first[2]})
    report = {"trace_count": trace["count"], "groups": matches}
    out = ROOT / "build/analysis/title-bitmap-report.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
