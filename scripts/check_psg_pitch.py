"""Verify the first audible pitch table lookup against CPU and PSG traces."""

import configparser
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def main():
    config = configparser.ConfigParser(interpolation=None)
    config.read(ROOT / "config.local.ini", encoding="utf-8")
    rom = Path(config["inputs"]["cartridge"]).read_bytes()
    cpu = json.loads((ROOT / "build/smoke/cpu-window-reset-356.json").read_text())
    hardware = json.loads((ROOT / "build/smoke/hardware-trace-reset-400.json").read_text())
    assert len(rom) == 0x2000
    assert len(rom[0x18DA:0x18F2]) == 24
    table_index = 4
    source = 0x18DA + 2 * table_index
    value = int.from_bytes(rom[source:source + 2], "big")
    shift = 3
    shifted = value >> shift
    period = shifted >> 4
    assert source == 0x18E2 and value == 0x2A70
    assert shifted == 0x054E and period == 0x054
    cpu_lines = cpu["lines"]
    for fragments in [
        ("000:1958", "HL:18E2", "LD D,(HL)"),
        ("000:195B", "DE:2A70", "BC:0203"),
        ("000:196C", "DE:054E"),
        ("000:198A", "AF:C480", "OUT ($7F),A"),
        ("000:198A", "AF:0580", "OUT ($7F),A"),
    ]:
        assert any(all(fragment in line for fragment in fragments) for line in cpu_lines), fragments
    psg = [line for line in hardware["lines"] if "[PSG]" in line]
    assert any("TONE Ch:2 LATCH:$C4" in line for line in psg)
    assert any("TONE Ch:2 DATA:$05 Period:$054" in line for line in psg)
    assert any("VOLUME Ch:2 Data:$D0" in line for line in psg)
    report = {"table_start": "18DA", "table_bytes": 24,
              "first_observed_source": f"{source:04X}", "table_word": f"{value:04X}",
              "shift": shift, "shifted": f"{shifted:04X}", "psg_period": f"{period:03X}",
              "channel": 2}
    out = ROOT / "build/analysis/psg-pitch-report.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
