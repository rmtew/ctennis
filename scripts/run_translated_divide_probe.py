"""Check generated restoring division against the source arithmetic on A500."""

import configparser
import hashlib
import json
import re
import sys
from pathlib import Path

from ball_math import divide_152b
from run_translated_prng_probe import ROOT, OUT, ASSEMBLER, run


DIVISORS = (0, 1, 2, 3, 4, 5, 7, 8, 15, 16, 31, 32, 63, 64, 65, 79,
            80, 95, 96, 112, 127, 128, 129, 160, 191, 192, 193, 224,
            240, 252, 254, 255)
CASES_PER_DIVISOR = 264


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
    match = re.search(r"(?ms)^restoring_divide_byte:\n(.*?)^triangular_root_step:", generated)
    if not match:
        raise AssertionError("Translated divider labels are missing")
    routine = "restoring_divide_byte:\n" + match.group(1)
    required = ("MAKE_HL_NO_AR", "MAKE_H", "PUSH_SR", "POP_SR", "CLR_XC_FLAGS",
                "INVERT_XC_FLAGS", "SET_X_FROM_C")
    if "ERROR" in routine or any(name not in routine for name in required):
        raise AssertionError("Divider routine changed or contains an unresolved diagnostic")
    (OUT / "divide-routine.s").write_text(routine, encoding="utf-8")
    cases = bytearray()
    for divisor in DIVISORS:
        dividends = [(i << 8) | ((i * 73 + 19) & 255) for i in range(256)]
        dividends += [0, 1, (divisor - 1) & 65535, divisor,
                      divisor + 1, 0xFFFF, 0x8000, 0xFF00]
        if len(dividends) != CASES_PER_DIVISOR:
            raise AssertionError("Divider case count changed")
        for dividend in dividends:
            quotient, remainder = divide_152b(dividend, divisor)
            cases.extend((dividend >> 8, dividend & 255, divisor, quotient, remainder))
    if len(cases) != len(DIVISORS) * CASES_PER_DIVISOR * 5:
        raise AssertionError("Divider case table size changed")
    (OUT / "divide-cases.bin").write_bytes(cases)
    executable = OUT / "translated-divide-probe"
    run([str(ASSEMBLER), "-Fhunkexe", "-kick1hunks", "-m68000", "-o",
         str(executable), "amiga/translated_divide_probe.s"])
    log = run([str(copperline), "--factory", "--model", "A500", "--chipset", "OCS",
               "--video", "PAL", "--cpu", "68000", "--chip", "512K", "--slow", "0",
               "--fast", "0", "--noaudio", "--run", str(executable),
               "--exit-on-return", str(rom)], timeout=120)
    (OUT / "divide-copperline.log").write_text(log, encoding="utf-8")
    for expected_log in ("cpu=M68000", "chip_ram=512K", "fast_ram=0K", "slow_ram=0K",
                         "chipset=Ocs", "video=Pal", "Kickstart 1.3", "program returned 0"):
        if expected_log not in log:
            raise AssertionError(f"Native divide proof missing {expected_log}")
    report = {"cases_checked": len(DIVISORS) * CASES_PER_DIVISOR,
              "divisors": list(DIVISORS), "result": "all quotient/remainder pairs match",
              "routine_sha256": hashlib.sha256(routine.encode()).hexdigest(),
              "executable_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
              "machine": "PAL A500 OCS 68000, 512K chip, 0 slow/fast, Kickstart 1.3"}
    (OUT / "divide-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
