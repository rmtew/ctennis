"""Verify the first 22-byte sound stream against CPU reads and PSG writes."""

import configparser
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
READ = re.compile(r"\[CPU\] 000:19B8 .*?HL:([0-9A-F]{4})")


def main():
    config = configparser.ConfigParser(interpolation=None)
    config.read(ROOT / "config.local.ini", encoding="utf-8")
    rom = Path(config["inputs"]["cartridge"]).read_bytes()
    cpu = json.loads((ROOT / "build/smoke/cpu-window-reset-356-366.json").read_text())
    hardware = json.loads((ROOT / "build/smoke/hardware-trace-reset-400.json").read_text())
    read_addresses = [int(match[1], 16) for line in cpu["lines"]
                      if (match := READ.search(line))]
    assert read_addresses == list(range(0x1FDD, 0x1FF3))
    commands = rom[0x1FDD:0x1FF3]
    assert commands == bytes.fromhex(
        "40 58 70 01 60 01 3F 23 05 3E 05 3F 05 3E 05 3F 05 3E 05 3F 05 00")
    assert sum("000:190C" in line and "AF:0042" in line
               for line in cpu["lines"]) == 4
    assert sum("000:190C" in line and "AF:0113" in line
               for line in cpu["lines"]) == 3
    assert sum("000:18B0" in line and "AF:0154" in line
               for line in cpu["lines"]) == 8
    assert sum("000:18D0" in line and "HL:0002" in line
               for line in cpu["lines"]) == 8
    assert any("000:192F" in line and "AF:0818" in line for line in cpu["lines"])
    assert any("000:193F" in line and "AF:0100" in line for line in cpu["lines"])
    assert any("000:1937" in line and "AF:0100" in line for line in cpu["lines"])
    assert any("000:198A" in line and "AF:DF88" in line for line in cpu["lines"])

    psg = [line for line in hardware["lines"] if "[PSG]" in line]
    tone = [line for line in psg if "TONE Ch:2 LATCH:$C4" in line]
    volume = [line for line in psg if "VOLUME Ch:2 Data:$D" in line]
    assert len(tone) == 7
    loud = [line.split("Data:$")[1][:2] for line in volume if "Data:$D0" in line or "Data:$D1" in line]
    assert loud == ["D0", "D1", "D0", "D1", "D0", "D1", "D0"]
    report = {"rom_start": "1FDD", "rom_end_exclusive": "1FF3",
              "command_bytes": commands.hex(), "cpu_reads": len(read_addresses),
              "note_or_rest_commands": 8, "audible_pulses": len(tone),
              "attenuation_sequence": loud,
              "duration_base_ix_plus_8": 1, "duration_multiplier_ix_plus_5": 8,
              "observed_ix_plus_0d": 2,
              "final_byte": "00", "final_psg_mute": True}
    out = ROOT / "build/analysis/first-sound-stream-report.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
