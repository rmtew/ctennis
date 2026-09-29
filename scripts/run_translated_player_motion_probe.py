"""Compare translated two-player motion with the source byte model on A500."""

import configparser
import hashlib
import json
import random
import re
import sys
from pathlib import Path

from run_translated_prng_probe import ROOT, OUT, ASSEMBLER, run
from source_input_movement import move_player_1404_145d


CASE_COUNT = 4096
ROM_SHA256 = "19bb6647f14ef50f976e8d0a06d389f06b2e700d54a54fb1734d3140f9745ad1"


def main():
    config = configparser.ConfigParser(interpolation=None)
    if not config.read(ROOT / "config.local.ini", encoding="utf-8"):
        raise FileNotFoundError("config.local.ini")
    copperline = Path(config["tools"]["copperline"])
    amiga_rom = Path(config["inputs"]["amiga_rom"])
    cartridge = Path(config["inputs"]["cartridge"]).read_bytes()
    if hashlib.sha256(cartridge).hexdigest() != ROM_SHA256:
        raise AssertionError("Unexpected source cartridge")
    for path in (ASSEMBLER, copperline, amiga_rom):
        if not path.is_file():
            raise FileNotFoundError(path)
    OUT.mkdir(parents=True, exist_ok=True)
    source = OUT / "champion-raw.68k"
    run([sys.executable, "-W", "ignore", "scripts/z80268k.py", "--champion-source", "-n",
         "-i", "mot", "-o", "mot", "-c", str(source), "-I", str(OUT / "z80-support.i"),
         "--report-output", str(OUT / "report.json"),
         "build/analysis/champion-tennis-classified.asm"])
    generated = source.read_text(encoding="utf-8")
    match = re.search(r"(?ms)^lower_player_motion_update:\n(.*?)^animate_lower_player:", generated)
    if not match:
        raise AssertionError("Generated movement boundaries are missing")
    routine = "lower_player_motion_update:\n" + match.group(1)
    for label in ("lower_movement_bounds", "upper_movement_bounds"):
        routine, count = re.subn(rf"(?m)^{label}:\ndc\.b [^\n]*\n", "", routine)
        if count != 1:
            raise AssertionError(f"Expected one {label} table in generated source")
    if "ERROR" in routine:
        raise AssertionError("Generated movement has an unresolved translator diagnostic")
    (OUT / "player-motion-routine.s").write_text(routine, encoding="utf-8")
    memory = bytearray(65536)
    memory[:len(cartridge)] = cartridge
    (OUT / "player-motion-memory.bin").write_bytes(memory)
    rng = random.Random(20260929)
    cases = bytearray()
    for case in range(CASE_COUNT):
        ram = bytearray(256)
        ram[0x39] = (0x04 if case % 17 == 0 else 0)
        ram[0x3D] = rng.randrange(2) << 4
        ram[0x43] = rng.randrange(4) << 5 | (0x80 if case % 19 == 0 else 0)
        ram[0x44] = rng.randrange(4) << 5 | (0x80 if case % 23 == 0 else 0)
        ram[0x6B] = rng.randrange(2)
        ram[0x53] = rng.randrange(256)
        for offset in (0x45, 0x46, 0x49, 0x4A):
            ram[offset] = rng.randrange(256)
        case_input = bytes(ram[offset] for offset in
                           (0x39, 0x3D, 0x43, 0x44, 0x6B, 0x53, 0x45, 0x46, 0x49, 0x4A))
        move_player_1404_145d(ram, upper=False)
        move_player_1404_145d(ram, upper=True)
        cases.extend(case_input)
        cases.extend(ram[offset] for offset in (0x45, 0x46, 0x49, 0x4A))
    (OUT / "player-motion-cases.bin").write_bytes(cases)
    executable = OUT / "translated-player-motion-probe"
    run([str(ASSEMBLER), "-Fhunkexe", "-kick1hunks", "-m68000", "-o",
         str(executable), "amiga/translated_player_motion_probe.s"])
    log = run([str(copperline), "--factory", "--model", "A500", "--chipset", "OCS",
               "--video", "PAL", "--cpu", "68000", "--chip", "512K", "--slow", "0",
               "--fast", "0", "--noaudio", "--run", str(executable),
               "--exit-on-return", str(amiga_rom)], timeout=120)
    (OUT / "player-motion-copperline.log").write_text(log, encoding="utf-8")
    for expected in ("cpu=M68000", "chip_ram=512K", "fast_ram=0K", "slow_ram=0K",
                     "chipset=Ocs", "video=Pal", "Kickstart 1.3", "program returned 0"):
        if expected not in log:
            raise AssertionError(f"Native movement proof missing {expected}: {log[-500:]}")
    report = {"cases_checked": CASE_COUNT, "result": "both player positions match source model",
              "routine_sha256": hashlib.sha256(routine.encode()).hexdigest(),
              "executable_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
              "machine": "PAL A500 OCS 68000, 512K chip, 0 slow/fast, Kickstart 1.3"}
    (OUT / "player-motion-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
