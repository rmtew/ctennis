"""Replay captured VDP writes and verify short-lived ROM-to-name-table copies."""

import configparser
import hashlib
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
    final_vram = (ROOT / "build/smoke/vram-reset-105.bin").read_bytes()
    assert len(rom) == 0x2000 and len(final_vram) == 0x4000
    assert len(trace["lines"]) == trace["count"]
    rows = [
        (0x0482, 0x38C6, 4, 0x11), (0x04C6, 0x38D6, 4, 0x11),
        (0x050A, 0x3842, 2, 2), (0x050E, 0x385C, 2, 2),
        (0x0512, 0x38A1, 4, 10), (0x0512, 0x38BB, 4, 10),
        (0x053A, 0x3A21, 4, 2),
    ]
    expected_rows = []
    expected_total = 0
    for source, destination, width, count in rows:
        for row in range(count):
            expected_rows.append([(destination + row * 32 + column,
                                   rom[source + row * width + column])
                                  for column in range(width)])
            expected_total += width

    vram = bytearray(0x4000)
    writes = []
    sprite_writes = []
    sprite_attribute_writes = []
    name_events = []
    last_90 = None
    vint = 0
    for index, line in enumerate(trace["lines"]):
        if "VINT FLAG" in line:
            vint += 1
            if vint == 90:
                last_90 = bytes(vram)
        match = WRITE.search(line)
        if match is None:
            continue
        address = int(match[1], 16)
        value = int(match[2], 16)
        vram[address] = value
        writes.append((address, value, vint, index))
        if address == 0x1C03:
            sprite_writes.append({"vint": vint, "trace_index": index, "value": f"{value:02X}", "line": line})
        if 0x3B00 <= address < 0x3B80:
            sprite_attribute_writes.append((vint, address, value, index))
        if 0x3800 <= address < 0x3F00:
            if not name_events or name_events[-1]["vint"] != vint:
                name_events.append({"vint": vint, "writes": 0, "nonzero_writes": 0,
                                    "first_address": f"{address:04X}"})
            name_events[-1]["writes"] += 1
            name_events[-1]["nonzero_writes"] += bool(value)

    # The first 90 VINTs precede the title-table draw. Replaying the whole
    # reset trace from zero must reproduce its final state exactly.
    assert bytes(vram) == final_vram, "VDP trace replay differs from captured VRAM"
    assert final_vram == (ROOT / "build/smoke/vram-reset-120.bin").read_bytes()
    assert last_90 is not None
    assert all(value == 0 for value in last_90[0x3800:0x3F00])
    assert expected_total == 232
    matched_rows = []
    for expected_row in expected_rows:
        matches = [write for i, write in enumerate(writes)
                   if [pair[:2] for pair in writes[i:i + len(expected_row)]] == expected_row]
        assert matches, f"no VDP write sequence for row starting {expected_row[0]}"
        matched_rows.append(matches[0])

    report = {
        "trace_count": trace["count"],
        "vint_count": vint,
        "vram_sha256": hashlib.sha256(vram).hexdigest(),
        "verified_initial_rows": len(matched_rows),
        "initial_row_write_count_from_code": expected_total,
        "first_initial_row_match": {"vint": matched_rows[0][2], "address": f"{matched_rows[0][0]:04X}",
                                    "trace_index": matched_rows[0][3]},
        "name_table_write_phases": name_events,
        "sprite_1c03_writes": sprite_writes,
        "sprite_attribute_write_count": len(sprite_attribute_writes),
        "sprite_attribute_nonzero_writes": [
            {"vint": frame, "address": f"{address:04X}", "value": f"{value:02X}",
             "trace_index": index}
            for frame, address, value, index in sprite_attribute_writes if value
        ],
    }
    out = ROOT / "build/analysis/title-vdp-replay.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
