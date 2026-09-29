"""Check generated player-side input normalization on the PAL A500."""

import configparser
import hashlib
import json
import re
import sys
from pathlib import Path

from run_translated_prng_probe import ROOT, OUT, ASSEMBLER, run


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
    generated = source.read_text(encoding="utf-8")
    match = re.search(r"(?ms)^normalize_input_for_player_side:\n(.*?)^animate_lower_player:", generated)
    if not match:
        raise AssertionError("Translated input-side routine labels are missing")
    # The entry ends before the next routine; only its two return paths belong here.
    routine = "normalize_input_for_player_side:\n" + match.group(1)
    if "ERROR" in routine or "PUSH_SR" not in routine or "POP_SR" not in routine:
        raise AssertionError("Input-side routine changed or contains an unresolved diagnostic")
    (OUT / "input-side-routine.s").write_text(routine, encoding="utf-8")
    cases = bytearray()
    for side in (0, 0x10):
        for mode in (0, 0x10):
            for direction in range(256):
                selected = ((direction << 4) | (direction >> 4)) & 255 if (mode ^ side) & 0x10 else direction
                cases.extend((direction, mode, side, selected))
    (OUT / "input-side-cases.bin").write_bytes(cases)
    executable = OUT / "translated-input-side-probe"
    run([str(ASSEMBLER), "-Fhunkexe", "-kick1hunks", "-m68000", "-o",
         str(executable), "amiga/translated_input_side_probe.s"])
    log = run([str(copperline), "--factory", "--model", "A500", "--chipset", "OCS",
               "--video", "PAL", "--cpu", "68000", "--chip", "512K", "--slow", "0",
               "--fast", "0", "--noaudio", "--run", str(executable),
               "--exit-on-return", str(rom)], timeout=120)
    (OUT / "input-side-copperline.log").write_text(log, encoding="utf-8")
    for expected in ("cpu=M68000", "chip_ram=512K", "fast_ram=0K", "slow_ram=0K",
                     "chipset=Ocs", "video=Pal", "Kickstart 1.3", "program returned 0"):
        if expected not in log:
            raise AssertionError(f"Native input-side proof missing {expected}")
    report = {"cases_checked": 1024, "result": "all selected directions match",
              "routine_sha256": hashlib.sha256(routine.encode()).hexdigest(),
              "executable_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
              "machine": "PAL A500 OCS 68000, 512K chip, 0 slow/fast, Kickstart 1.3"}
    (OUT / "input-side-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
