"""Build and capture the native eight-sprite Copperline display prototype."""

import configparser
import csv
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "build" / "amiga" / "sprite-probe"
ASSEMBLER = ROOT / ".tools" / "vasm" / "vasmm68k_mot.exe"
EXECUTABLE = OUTPUT / "sprite-probe"
GIF = OUTPUT / "gameplay-sprites.gif"
PNG = OUTPUT / "gameplay-sprites.png"
SOURCE_TIMING = ROOT / "build" / "reference" / "source-timing" / "run_a.tsv"
MOVE_RE = re.compile(r"DBG: MOVE I=([0-9A-F]{2}) X=([0-9A-F]{2}) T=([0-9A-F]{2}) H=([0-9A-F]{2}) U=([0-9A-F]{2}) BY=([0-9A-F]{2}) BX=([0-9A-F]{2}) BS=([0-9A-F]{2})")
CLOCK_RE = re.compile(r"DBG: CLOCK F=([0-9A-F]{2}) U=([0-9A-F]{2})")


def verify_movement_replay(log):
    observed = [tuple(int(part, 16) for part in match.groups())
                for match in MOVE_RE.finditer(log)]
    with SOURCE_TIMING.open(newline="", encoding="utf-8") as handle:
        checkpoints = {int(row["frame"]): row for row in csv.DictReader(handle, delimiter="\t")
                       if row["event"] == "checkpoint" and 1300 <= int(row["frame"]) <= 1339}
    if sorted(checkpoints) != list(range(1300, 1340)):
        raise AssertionError("Source replay checkpoints 1300-1339 are missing")
    expected = []
    for frame in range(1300, 1340):
        row = checkpoints[frame]
        ram = bytes.fromhex(row["ram"])
        expected.append((ram[0x53], ram[0x4A], ram[0x6B], min(frame - 1299, 20),
                         frame - 1299, ram[0x4D], ram[0x4E], ram[0x66]))
    if observed != expected:
        mismatch = next(((index, source, native) for index, (source, native) in
                         enumerate(zip(expected, observed)) if source != native), None)
        raise AssertionError(f"Movement replay mismatch: {mismatch}; observed {len(observed)} records")
    clocks = [tuple(int(part, 16) for part in match.groups()) for match in CLOCK_RE.finditer(log)]
    if clocks != [(50, 59), (100, 119)]:
        raise AssertionError(f"PAL/source clock checkpoints differ: {clocks}")
    return {"source_replay_match": True, "compared_updates": len(expected),
            "held_updates": 20, "release_x": f"{observed[20][1]:02X}",
            "clock_checkpoints_pal_frames_to_sim_updates": clocks,
            "attached_ball_fields_match": True}


def run(command, timeout=90):
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(f"{command[0]} returned {result.returncode}: {result.stdout[-1500:]} {result.stderr[-1500:]}")
    return result


def main():
    config = configparser.ConfigParser(interpolation=None)
    if not config.read(ROOT / "config.local.ini", encoding="utf-8"):
        raise FileNotFoundError("config.local.ini")
    copperline = Path(config["tools"]["copperline"])
    rom = Path(config["inputs"]["amiga_rom"])
    for path in (ASSEMBLER, copperline, rom):
        if not path.is_file():
            raise FileNotFoundError(path)
    run([sys.executable, "scripts/generate_amiga_sprite_probe.py"])
    run([str(ASSEMBLER), "-Fhunkexe", "-kick1hunks", "-m68000", "-o",
         str(EXECUTABLE), "amiga/sprite_probe.s"])
    command = [
        str(copperline), "--factory", "--model", "A500", "--chipset", "OCS",
        "--video", "PAL", "--cpu", "68000", "--chip", "512K", "--slow", "0",
        "--fast", "0", "--noaudio", "--run", str(EXECUTABLE),
        "--joy-after", "5", "left", "334", "2",
        "--screenshot-after", "10", str(PNG),
        "--gif-after", "4", str(GIF), "--gif-seconds", "10", str(rom),
    ]
    result = run(command, timeout=120)
    log = result.stdout + result.stderr
    (OUTPUT / "copperline.log").write_text(log, encoding="utf-8")
    for expected in ("cpu=M68000", "chip_ram=512K", "fast_ram=0K", "slow_ram=0K",
                     "chipset=Ocs", "video=Pal", "Kickstart 1.3"):
        if expected not in log:
            raise AssertionError(f"Copperline profile missing {expected}")
    if not GIF.read_bytes().startswith(b"GIF8") or not PNG.read_bytes().startswith(b"\x89PNG"):
        raise AssertionError("Copperline captures missing or malformed")
    replay = verify_movement_replay(log)
    report = {"executable_bytes": EXECUTABLE.stat().st_size,
              "executable_sha256": hashlib.sha256(EXECUTABLE.read_bytes()).hexdigest(),
              "gif": str(GIF), "gif_bytes": GIF.stat().st_size,
              "png": str(PNG), "png_bytes": PNG.stat().st_size,
              "machine": "PAL A500 OCS 68000, 512K chip, 0 slow/fast, Kickstart 1.3",
              "replay": replay}
    (OUTPUT / "capture-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
