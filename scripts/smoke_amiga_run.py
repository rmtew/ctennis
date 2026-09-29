"""Build a minimal Kickstart 1.3 hunk and run it directly in Copperline."""

import configparser
import hashlib
import json
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ASSEMBLER_SOURCE = ROOT.parent / "amiga-reversing2" / "tools" / "vasmm68k_mot.exe"
ASSEMBLER = ROOT / ".tools" / "vasm" / "vasmm68k_mot.exe"
SOURCE = ROOT / "amiga" / "smoke.s"
EXECUTABLE = ROOT / "build" / "amiga" / "smoke"


def main() -> None:
    config = configparser.ConfigParser(interpolation=None)
    if not config.read(ROOT / "config.local.ini", encoding="utf-8"):
        raise FileNotFoundError("config.local.ini")
    copperline = Path(config["tools"]["copperline"])
    rom = Path(config["inputs"]["amiga_rom"])
    for path in (ASSEMBLER_SOURCE, copperline, rom):
        if not path.is_file():
            raise FileNotFoundError(path)
    ASSEMBLER.parent.mkdir(parents=True, exist_ok=True)
    if not ASSEMBLER.exists() or ASSEMBLER.read_bytes() != ASSEMBLER_SOURCE.read_bytes():
        shutil.copy2(ASSEMBLER_SOURCE, ASSEMBLER)
    EXECUTABLE.parent.mkdir(parents=True, exist_ok=True)

    build = subprocess.run(
        [str(ASSEMBLER), "-Fhunkexe", "-kick1hunks", "-m68000", "-o", str(EXECUTABLE), str(SOURCE)],
        cwd=ROOT, capture_output=True, text=True, timeout=30,
    )
    if build.returncode:
        raise RuntimeError(f"vasm failed: {build.stdout}\n{build.stderr}")
    command = [
        str(copperline), "--factory", "--model", "A500", "--chipset", "OCS",
        "--video", "PAL", "--cpu", "68000", "--chip", "512K", "--slow", "0",
        "--fast", "0", "--noaudio", "--run", str(EXECUTABLE),
        "--exit-on-return", str(rom),
    ]
    execution = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=90)
    log = execution.stdout + execution.stderr
    (EXECUTABLE.parent / "smoke-copperline.log").write_text(log, encoding="utf-8")
    required = ("cpu=M68000", "chip_ram=512K", "fast_ram=0K", "slow_ram=0K",
                "chipset=Ocs", "video=Pal", "Kickstart 1.3")
    if execution.returncode or any(item not in log for item in required):
        raise RuntimeError(f"Copperline launch failed ({execution.returncode}); see {EXECUTABLE.parent / 'smoke-copperline.log'}")
    print(json.dumps({
        "assembler_sha256": hashlib.sha256(ASSEMBLER.read_bytes()).hexdigest(),
        "executable_sha256": hashlib.sha256(EXECUTABLE.read_bytes()).hexdigest(),
        "executable_bytes": EXECUTABLE.stat().st_size,
        "copperline_exit_code": execution.returncode,
        "profile": "PAL A500, OCS, 68000, 512K chip, 0 slow, 0 fast, Kickstart 1.3",
    }, indent=2))


if __name__ == "__main__":
    main()
