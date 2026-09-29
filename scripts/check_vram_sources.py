"""Verify identified ROM-to-VRAM transfers in a Gearsystem reset/title capture."""

import configparser
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
EXPECTED_SHA256 = "19bb6647f14ef50f976e8d0a06d389f06b2e700d54a54fb1734d3140f9745ad1"


def main() -> None:
    config = configparser.ConfigParser(interpolation=None)
    config.read(ROOT / "config.local.ini", encoding="utf-8")
    rom = Path(config["inputs"]["cartridge"]).read_bytes()
    if len(rom) != 0x2000 or hashlib.sha256(rom).hexdigest() != EXPECTED_SHA256:
        raise ValueError("Configured cartridge is not the identified 8 KB image")

    capture = ROOT / "build" / "smoke"
    state = json.loads((capture / "hardware-state-reset-120.json").read_text(encoding="utf-8"))
    trace = json.loads((capture / "hardware-trace-reset-120.json").read_text(encoding="utf-8"))
    vram = (capture / "vram-reset-120.bin").read_bytes()
    if (state["frames"] != 120 or state["cartridge_sha256"] != EXPECTED_SHA256
            or not state["media"]["is_sg1000"] or len(vram) != 0x4000
            or hashlib.sha256(vram).hexdigest() != state["vram_sha256"]
            or trace["count"] != state["trace_count"]):
        raise ValueError("Hardware capture files do not describe one valid SG-1000 run")

    registers = {int(row[0]): int(row[1], 16) for row in state["vdp_registers"]["registers"]}
    required = {0: 0x02, 2: 0x0F, 3: 0x7F, 4: 0x07, 5: 0x76, 6: 0x03}
    if any(registers[index] != value for index, value in required.items()):
        raise ValueError(f"Unexpected title VDP register layout: {registers}")
    if not any("[VDP] REG R02 NAME TABLE <- $0E" in line for line in trace["lines"]):
        raise ValueError("Initial $3800 name-table selection missing from trace")
    if not any("[VDP] REG R02 NAME TABLE <- $0F" in line for line in trace["lines"]):
        raise ValueError("Title $3C00 name-table selection missing from trace")

    transfers = [
        ("sprite_pattern", 0x19CC, 0x1DCC, 0x1800),
        ("background_pattern_top", 0x1C4C, 0x1F94, 0x2098),
        ("background_pattern_middle", 0x1C4C, 0x1F94, 0x2898),
        ("background_pattern_bottom", 0x1C4C, 0x1F94, 0x3098),
    ]
    rows = []
    for name, start, end, destination in transfers:
        actual = vram[destination:destination + end - start]
        expected = rom[start:end]
        if actual != expected:
            first = next(i for i, pair in enumerate(zip(actual, expected)) if pair[0] != pair[1])
            raise ValueError(f"{name} mismatch at VRAM {destination + first:04X}")
        rows.append({"name": name, "rom_start": f"{start:04X}", "rom_end_exclusive": f"{end:04X}",
                     "vram_start": f"{destination:04X}", "length": len(expected),
                     "sha256": hashlib.sha256(expected).hexdigest()})

    encoded = rom[0x01C3:0x01D3]
    if len(encoded) != 16 or encoded[-1] != 0 or any(value == 0 for value in encoded[:-1]):
        raise ValueError("Unexpected background color-run encoding")
    expanded = bytes(color for value in encoded[:-1]
                     for color in [value & 0xF0] * ((value & 0x0F) * 8))
    if len(expanded) != 0x0350:
        raise ValueError(f"Unexpected color-run expansion length: {len(expanded)}")
    for destination in (0x0000, 0x0800, 0x1000):
        if vram[destination:destination + len(expanded)] != expanded:
            raise ValueError(f"Color-run expansion differs at VRAM {destination:04X}")
        rows.append({"name": "background_color_runs", "rom_start": "01C3",
                     "rom_end_exclusive": "01D3", "vram_start": f"{destination:04X}",
                     "length": len(expanded), "sha256": hashlib.sha256(expanded).hexdigest()})

    result = {"cartridge_sha256": EXPECTED_SHA256, "vram_sha256": state["vram_sha256"],
              "trace_count": trace["count"], "title_vdp_registers": required,
              "verified_transfers": rows}
    (ROOT / "build" / "analysis" / "vram-source-report.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
