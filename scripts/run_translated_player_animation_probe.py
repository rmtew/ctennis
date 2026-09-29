"""Compare generated player animation RAM with the source model on A500."""

import configparser
import hashlib
import json
import random
import re
import sys
from pathlib import Path

from run_translated_prng_probe import ROOT, OUT, ASSEMBLER, run
from source_input_movement import animate_player_14a7_14b3


CASE_COUNT = 2048
ROM_SHA256 = "19bb6647f14ef50f976e8d0a06d389f06b2e700d54a54fb1734d3140f9745ad1"
OFFSETS = (0x43, 0x44, 0x6D, 0x6E, 0x4B, 0x47)


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
    match = re.search(r"(?ms)^animate_lower_player:\n(.*?)^unsigned_multiply_byte:", generated)
    if not match:
        raise AssertionError("Generated animation boundaries are missing")
    routine = "animate_lower_player:\n" + match.group(1)
    routine, count = re.subn(r"(?m)^animation_records:\n(?:dc\.b [^\n]*\n)+", "", routine)
    if count != 1 or "ERROR" in routine:
        raise AssertionError("Generated animation body changed or has a diagnostic")
    (OUT / "player-animation-routine.s").write_text(routine, encoding="utf-8")
    threshold = re.search(r"(?ms)^threshold_table_lookup:\n(.*?)^direction_ai:", generated)
    if not threshold or "ERROR" in threshold.group(1):
        raise AssertionError("Generated threshold lookup changed or has a diagnostic")
    (OUT / "threshold-routine.s").write_text("threshold_table_lookup:\n" + threshold.group(1), encoding="utf-8")
    memory = bytearray(65536)
    memory[:len(cartridge)] = cartridge
    (OUT / "player-animation-memory.bin").write_bytes(memory)
    rng = random.Random(20260930)
    cases = bytearray()
    for case in range(CASE_COUNT):
        ram = bytearray(256)
        for offset in (0x43, 0x44):
            phase = rng.randrange(4)
            flag = (0, 0x08, 0x10, 0x18)[rng.randrange(4)]
            ram[offset] = phase | flag
        for offset in (0x6D, 0x6E, 0x4B, 0x47):
            ram[offset] = rng.randrange(256)
        cases.extend(ram[offset] for offset in OFFSETS)
        animate_player_14a7_14b3(ram, upper=False)
        animate_player_14a7_14b3(ram, upper=True)
        cases.extend(ram[offset] for offset in OFFSETS)
    (OUT / "player-animation-cases.bin").write_bytes(cases)
    executable = OUT / "translated-player-animation-probe"
    run([str(ASSEMBLER), "-Fhunkexe", "-kick1hunks", "-m68000", "-o",
         str(executable), "amiga/translated_player_animation_probe.s"])
    log = run([str(copperline), "--factory", "--model", "A500", "--chipset", "OCS",
               "--video", "PAL", "--cpu", "68000", "--chip", "512K", "--slow", "0",
               "--fast", "0", "--noaudio", "--run", str(executable),
               "--exit-on-return", str(amiga_rom)], timeout=120)
    (OUT / "player-animation-copperline.log").write_text(log, encoding="utf-8")
    for expected in ("cpu=M68000", "chip_ram=512K", "fast_ram=0K", "slow_ram=0K",
                     "chipset=Ocs", "video=Pal", "Kickstart 1.3", "program returned 0"):
        if expected not in log:
            raise AssertionError(f"Native animation proof missing {expected}: {log[-500:]}")
    report = {"cases_checked": CASE_COUNT, "result": "both player animation states match source model",
              "routine_sha256": hashlib.sha256(routine.encode()).hexdigest(),
              "executable_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
              "machine": "PAL A500 OCS 68000, 512K chip, 0 slow/fast, Kickstart 1.3"}
    (OUT / "player-animation-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
