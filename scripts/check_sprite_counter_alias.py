"""Verify that the interrupt countdown aliases the sprite upload buffer."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SMOKE = ROOT / "build/smoke"


def main():
    windows = {
        frame: json.loads((SMOKE / f"cpu-window-reset-{frame}.json").read_text())
        for frame in range(34, 40)
    }
    expected_before = [0xFC, 0x00, 0xFF, 0xFE, 0xFD, 0xFC]
    expected_after = [0x00, 0xFF, 0xFE, 0xFD, 0xFC, 0xFB]
    for frame, before, after in zip(windows, expected_before, expected_after):
        window = windows[frame]
        assert window["frame"] == frame
        assert int(window["ram_c080_before"].split()[3], 16) == before
        assert int(window["ram_c080_after"].split()[3], 16) == after

    def has(frame, *fragments):
        return any(all(fragment in line for fragment in fragments)
                   for line in windows[frame]["lines"])

    assert has(34, "000:00DA", "AF:0044", "HL:C083", "LD (HL),A")
    for frame in range(35, 40):
        assert has(frame, "000:06C2", "HL:C083", "DEC (HL)")
    assert has(39, "000:02A5", "DE:1C03", "HL:C083", "LD A,(HL)")
    assert has(39, "000:02A6", "AF:FBAC", "DE:1C03", "OUT ($BE),A")

    trace = json.loads((SMOKE / "hardware-trace-reset-105.json").read_text())
    matching_writes = [line for line in trace["lines"]
                       if "DATA WRITE VRAM[$1C03] <- $FB" in line]
    assert len(matching_writes) == 1
    report = {
        "source_ram": "C083",
        "destination_vram": "1C03",
        "initial_transformed_byte": "00",
        "frame_35_to_39_ram_after": [f"{value:02X}" for value in expected_after[1:]],
        "uploaded_byte": "FB",
        "vdp_write": matching_writes[0],
    }
    out = ROOT / "build/analysis/sprite-counter-alias-report.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
