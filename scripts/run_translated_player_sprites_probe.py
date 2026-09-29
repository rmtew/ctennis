"""Compare generated player sprite records with source-derived RAM behavior."""

import configparser
import hashlib
import json
import random
import re
import sys
from pathlib import Path

from run_translated_prng_probe import ROOT, OUT, ASSEMBLER, run
from source_input_movement import build_player_sprites_10e9


CASE_COUNT = 2048
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
    match = re.search(r"(?ms)^build_player_sprites:\n(.*?)^ball_flight_update:", generated)
    if not match:
        raise AssertionError("Generated sprite-construction boundaries are missing")
    routine = "build_player_sprites:\n" + match.group(1)
    routine, count = re.subn(r"(?m)^player_sprite_descriptors:\n(?:dc\.b [^\n]*\n)+", "", routine)
    if count != 1 or "ERROR" in routine:
        raise AssertionError("Generated sprite-construction body changed or has a diagnostic")
    (OUT / "player-sprites-routine.s").write_text(routine, encoding="utf-8")
    memory = bytearray(65536)
    memory[:len(cartridge)] = cartridge
    (OUT / "player-sprites-memory.bin").write_bytes(memory)
    rng = random.Random(20260930)
    cases = bytearray()
    for case in range(CASE_COUNT):
        ram = bytearray(256)
        for offset in (0x45, 0x46, 0x48, 0x49, 0x4A, 0x4C):
            ram[offset] = rng.randrange(256)
        ram[0x47] = case % 14
        ram[0x4B] = (case // 14) % 14
        cases.extend(ram[0x45:0x4D])
        build_player_sprites_10e9(ram)
        cases.extend(ram[0x14:0x20])
        cases.extend(ram[0x24:0x30])
    (OUT / "player-sprites-cases.bin").write_bytes(cases)
    executable = OUT / "translated-player-sprites-probe"
    run([str(ASSEMBLER), "-Fhunkexe", "-kick1hunks", "-m68000", "-o",
         str(executable), "amiga/translated_player_sprites_probe.s"])
    log = run([str(copperline), "--factory", "--model", "A500", "--chipset", "OCS",
               "--video", "PAL", "--cpu", "68000", "--chip", "512K", "--slow", "0",
               "--fast", "0", "--noaudio", "--run", str(executable),
               "--exit-on-return", str(amiga_rom)], timeout=120)
    (OUT / "player-sprites-copperline.log").write_text(log, encoding="utf-8")
    for expected in ("cpu=M68000", "chip_ram=512K", "fast_ram=0K", "slow_ram=0K",
                     "chipset=Ocs", "video=Pal", "Kickstart 1.3", "program returned 0"):
        if expected not in log:
            raise AssertionError(f"Native sprite proof missing {expected}: {log[-500:]}")
    report = {"cases_checked": CASE_COUNT, "bytes_compared_per_case": 24,
              "result": "both 12-byte player sprite records match source model",
              "routine_sha256": hashlib.sha256(routine.encode()).hexdigest(),
              "executable_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
              "machine": "PAL A500 OCS 68000, 512K chip, 0 slow/fast, Kickstart 1.3"}
    (OUT / "player-sprites-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
