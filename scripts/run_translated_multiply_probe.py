"""Check generated Z80 multiply code for every operand pair on a PAL A500."""

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
    match = re.search(r"(?ms)^unsigned_multiply_byte:\n(.*?)^restoring_divide_byte:", generated)
    if not match:
        raise AssertionError("Translated multiply routine labels are missing")
    routine = "unsigned_multiply_byte:\n" + match.group(1)
    required = ("MAKE_HL_NO_AR", "MAKE_DE_NO_AR", "MAKE_H", "PUSH_SR", "POP_SR")
    if "ERROR" in routine or any(name not in routine for name in required):
        raise AssertionError("Multiply routine changed or has a translation error")
    (OUT / "multiply-routine.s").write_text(routine, encoding="utf-8")
    expected = bytearray()
    for h in range(256):
        for l in range(256):
            expected.extend((h * l).to_bytes(2, "big"))
    (OUT / "multiply-expected.bin").write_bytes(expected)
    executable = OUT / "translated-multiply-probe"
    run([str(ASSEMBLER), "-Fhunkexe", "-kick1hunks", "-m68000", "-o",
         str(executable), "amiga/translated_multiply_probe.s"])
    log = run([str(copperline), "--factory", "--model", "A500", "--chipset", "OCS",
               "--video", "PAL", "--cpu", "68000", "--chip", "512K", "--slow", "0",
               "--fast", "0", "--noaudio", "--run", str(executable),
               "--exit-on-return", str(rom)], timeout=120)
    (OUT / "multiply-copperline.log").write_text(log, encoding="utf-8")
    for expected_log in ("cpu=M68000", "chip_ram=512K", "fast_ram=0K", "slow_ram=0K",
                         "chipset=Ocs", "video=Pal", "Kickstart 1.3", "program returned 0"):
        if expected_log not in log:
            raise AssertionError(f"Native multiply proof missing {expected_log}")
    report = {"operand_pairs_checked": 65536, "result": "all native 16-bit products match",
              "routine_sha256": hashlib.sha256(routine.encode()).hexdigest(),
              "executable_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
              "machine": "PAL A500 OCS 68000, 512K chip, 0 slow/fast, Kickstart 1.3"}
    (OUT / "multiply-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
