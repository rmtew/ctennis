"""Assemble JOTD-generated PRNG code and test every seed on a PAL A500."""

import configparser
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "translation"
ASSEMBLER = ROOT / ".tools" / "vasm" / "vasmm68k_mot.exe"


def run(command, timeout=90):
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(f"{command[0]} failed ({result.returncode}): {result.stdout[-1000:]} {result.stderr[-1000:]}")
    return result.stdout + result.stderr


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
    match = re.search(r"(?ms)^prng_step:\n(.*?)^copy_serve_vector:", generated)
    if not match:
        raise AssertionError("Translated PRNG routine labels are missing")
    routine = "prng_step:\n" + match.group(1)
    address_load = "\tGET_ADDRESS\tprng_seed,a0"
    if routine.count(address_load) != 1 or "ERROR" in routine:
        raise AssertionError("PRNG routine has changed or contains a translation error")
    routine = routine.replace(address_load, "\tlea\tprng_seed,a0")
    (OUT / "prng-routine.s").write_text(routine, encoding="utf-8")
    (OUT / "prng-expected.bin").write_bytes(bytes((5 * seed + 1) & 255 for seed in range(256)))
    executable = OUT / "translated-prng-probe"
    run([str(ASSEMBLER), "-Fhunkexe", "-kick1hunks", "-m68000", "-o",
         str(executable), "amiga/translated_prng_probe.s"])
    log = run([str(copperline), "--factory", "--model", "A500", "--chipset", "OCS",
               "--video", "PAL", "--cpu", "68000", "--chip", "512K", "--slow", "0",
               "--fast", "0", "--noaudio", "--run", str(executable),
               "--exit-on-return", str(rom)])
    (OUT / "prng-copperline.log").write_text(log, encoding="utf-8")
    for expected in ("cpu=M68000", "chip_ram=512K", "fast_ram=0K", "slow_ram=0K",
                     "chipset=Ocs", "video=Pal", "Kickstart 1.3", "program returned 0"):
        if expected not in log:
            raise AssertionError(f"Native PRNG proof missing {expected}")
    report = {"seeds_checked": 256, "result": "all native results and RAM bytes match",
              "routine_sha256": hashlib.sha256(routine.encode()).hexdigest(),
              "executable_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
              "machine": "PAL A500 OCS 68000, 512K chip, 0 slow/fast, Kickstart 1.3"}
    (OUT / "prng-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
