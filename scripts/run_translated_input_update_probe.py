"""Verify both decoded-input selection paths in generated 68000 code."""

import configparser
import hashlib
import json
import sys
from pathlib import Path

from run_translated_prng_probe import ROOT, OUT, ASSEMBLER, run
from run_translated_player_frame_probe import extract
from source_input_movement import input_update_0832


CASE_COUNT = 16896


def main():
    config = configparser.ConfigParser(interpolation=None)
    if not config.read(ROOT / "config.local.ini", encoding="utf-8"):
        raise FileNotFoundError("config.local.ini")
    copperline = Path(config["tools"]["copperline"])
    rom = Path(config["inputs"]["amiga_rom"])
    for path in (ASSEMBLER, copperline, rom):
        if not path.is_file():
            raise FileNotFoundError(path)
    OUT.mkdir(parents=True, exist_ok=True)
    source = OUT / "champion-raw.68k"
    run([sys.executable, "-W", "ignore", "scripts/z80268k.py", "--champion-source", "-n",
         "-i", "mot", "-o", "mot", "-c", str(source), "-I", str(OUT / "z80-support.i"),
         "--report-output", str(OUT / "report.json"),
         "build/analysis/champion-tennis-classified.asm"])
    routine = extract(source.read_text(encoding="utf-8"), "input_update", "read_game_input")
    (OUT / "input-update-routine.s").write_text(routine, encoding="utf-8")
    cases = bytearray()
    for mode in (0, 0x04, 0x80):
        keyboards = range(64) if mode == 0x80 else (0,)
        for keyboard_bits in keyboards:
            for game_bits in range(256):
                ram = bytearray(256)
                ram[0x3D] = mode
                input_update_0832(ram, game_bits=game_bits, keyboard_bits=keyboard_bits)
                cases.extend((mode, game_bits, keyboard_bits, ram[0x53], ram[0x56]))
    if len(cases) != CASE_COUNT * 5:
        raise AssertionError("Unexpected input-selection case count")
    (OUT / "input-update-cases.bin").write_bytes(cases)
    executable = OUT / "translated-input-update-probe"
    run([str(ASSEMBLER), "-Fhunkexe", "-kick1hunks", "-m68000", "-o",
         str(executable), "amiga/translated_input_update_probe.s"])
    log = run([str(copperline), "--factory", "--model", "A500", "--chipset", "OCS",
               "--video", "PAL", "--cpu", "68000", "--chip", "512K", "--slow", "0",
               "--fast", "0", "--noaudio", "--run", str(executable),
               "--exit-on-return", str(rom)], timeout=120)
    (OUT / "input-update-copperline.log").write_text(log, encoding="utf-8")
    for expected in ("cpu=M68000", "chip_ram=512K", "fast_ram=0K", "slow_ram=0K",
                     "chipset=Ocs", "video=Pal", "Kickstart 1.3", "program returned 0"):
        if expected not in log:
            raise AssertionError(f"Native input-update proof missing {expected}: {log[-500:]}")
    report = {"cases_checked": CASE_COUNT, "two_group_cases": 16384,
              "result": "both decoded input fields match source model",
              "routine_sha256": hashlib.sha256(routine.encode()).hexdigest(),
              "executable_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
              "machine": "PAL A500 OCS 68000, 512K chip, 0 slow/fast, Kickstart 1.3"}
    (OUT / "input-update-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
