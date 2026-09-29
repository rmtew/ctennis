"""Boot Kickstart on the exact target A500 profile and capture a headless frame."""

import configparser
import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def main():
    config = configparser.ConfigParser(interpolation=None)
    config.read(ROOT / "config.local.ini", encoding="utf-8")
    emulator = Path(config["tools"]["copperline"])
    rom = Path(config["inputs"]["amiga_rom"])
    for file in (emulator, rom):
        if not file.is_file():
            raise FileNotFoundError(file)

    output = ROOT / "build" / "smoke"
    output.mkdir(parents=True, exist_ok=True)
    screenshot = output / "a500-kick13.png"
    command = [
        str(emulator), "--factory", "--model", "A500", "--chipset", "OCS",
        "--video", "PAL", "--cpu", "68000", "--chip", "512K",
        "--slow", "0", "--fast", "0", "--noaudio",
        "--screenshot-after", "5", str(screenshot), str(rom),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, timeout=60)
    log = completed.stdout + completed.stderr
    (output / "copperline.log").write_text(log, encoding="utf-8")
    if completed.returncode:
        raise RuntimeError(f"Copperline returned {completed.returncode}; see build/smoke/copperline.log")
    for expected in ("cpu=M68000", "chip_ram=512K", "fast_ram=0K", "slow_ram=0K", "chipset=Ocs", "video=Pal", "Kickstart 1.3"):
        if expected not in log:
            raise RuntimeError(f"Expected {expected!r} in Copperline log")
    if screenshot.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
        raise RuntimeError("Copperline did not write a PNG screenshot")
    print(json.dumps({
        "emulator": "Copperline 1.0.0-rc.1",
        "machine": "PAL A500, OCS, 68000, 512K chip, 0 slow, 0 fast, Kickstart 1.3",
        "rom_sha256": hashlib.sha256(rom.read_bytes()).hexdigest(),
        "screenshot": str(screenshot),
        "screenshot_sha256": hashlib.sha256(screenshot.read_bytes()).hexdigest(),
    }, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Copperline smoke test failed: {error}", file=sys.stderr)
        sys.exit(1)
