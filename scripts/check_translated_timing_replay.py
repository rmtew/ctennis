"""Compare the translated full update with 40 captured source RAM checkpoints."""

import configparser
import csv
import hashlib
import json
from pathlib import Path

from source_gameplay_slice import run_translated_frame_body


ROOT = Path(__file__).resolve().parent.parent
CAPTURE = ROOT / "build" / "reference" / "source-timing" / "run_a.tsv"
EXPECTED_ROM_SHA256 = "19bb6647f14ef50f976e8d0a06d389f06b2e700d54a54fb1734d3140f9745ad1"


def main():
    config = configparser.ConfigParser(interpolation=None)
    if not config.read(ROOT / "config.local.ini", encoding="utf-8"):
        raise FileNotFoundError("config.local.ini")
    rom = Path(config["inputs"]["cartridge"]).read_bytes()
    if hashlib.sha256(rom).hexdigest() != EXPECTED_ROM_SHA256:
        raise AssertionError("Unexpected cartridge")
    with CAPTURE.open(newline="", encoding="utf-8") as handle:
        checkpoints = {int(row["frame"]): bytes.fromhex(row["ram"])
                       for row in csv.DictReader(handle, delimiter="\t")
                       if row["event"] == "checkpoint" and 1299 <= int(row["frame"]) <= 1339}
    if sorted(checkpoints) != list(range(1299, 1340)):
        raise AssertionError("Missing source checkpoints")

    # The tap runs immediately before the C06B write. Resume the following
    # update with the counter value written at the end of interval 1299.
    ram = bytearray(checkpoints[1299][:256])
    ram[0x6B] = (ram[0x6B] + 1) & 0xFF
    vram = bytearray(16384)
    paths = {}
    for frame in range(1300, 1340):
        result = run_translated_frame_body(
            ram, vram, game_bits=4 if frame < 1320 else 0,
            lower_refresh_bit=0, upper_refresh_bit=0, rom=rom,
        )
        paths[result.ball_path] = paths.get(result.ball_path, 0) + 1
        expected = bytearray(checkpoints[frame][:256])
        expected[0x6B] = (expected[0x6B] + 1) & 0xFF
        if ram != expected:
            differences = [(f"{i:02X}", f"{ram[i]:02X}", f"{expected[i]:02X}")
                           for i in range(256) if ram[i] != expected[i]]
            raise AssertionError(f"RAM mismatch at interval {frame}: {differences[:16]}")
    print(json.dumps({"compared_updates": 40, "bytes_per_checkpoint": 256,
                      "ball_paths": paths, "final_ram_sha256": hashlib.sha256(ram).hexdigest()}, indent=2))


if __name__ == "__main__":
    main()
