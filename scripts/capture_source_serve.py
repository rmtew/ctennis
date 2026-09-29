"""Capture and compare two deterministic SC-3000 serve trajectories."""

import configparser
import csv
import hashlib
import json
import os
import subprocess
import zipfile
from pathlib import Path

from source_gameplay_slice import run_translated_frame_body
from source_irq_tail import irq_tail_06b1


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "build" / "reference" / "source-serve"
MAME = ROOT / ".tools" / "mame-0.289" / "mame.exe"
CARTRIDGE_ZIP = ROOT / "build" / "mame" / "roms" / "sg1000" / "champtns.zip"
EXPECTED_ROM_SHA256 = "19bb6647f14ef50f976e8d0a06d389f06b2e700d54a54fb1734d3140f9745ad1"


def read_capture(path):
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    if [int(row["frame"]) for row in rows] != list(range(1299, 1500)):
        raise AssertionError("Serve checkpoint sequence is incomplete")
    for row in rows:
        ram = bytes.fromhex(row["ram"])
        if len(ram) != 256 or (ram[0x6B] + 1) & 255 != int(row["tick_written"], 16):
            raise AssertionError(f"Invalid pre-write RAM checkpoint at {row['frame']}")
    return rows


def main():
    config = configparser.ConfigParser(interpolation=None)
    if not config.read(ROOT / "config.local.ini", encoding="utf-8"):
        raise FileNotFoundError("config.local.ini")
    rom = Path(config["inputs"]["cartridge"]).read_bytes()
    if hashlib.sha256(rom).hexdigest() != EXPECTED_ROM_SHA256:
        raise AssertionError("Unexpected cartridge")
    with zipfile.ZipFile(CARTRIDGE_ZIP) as archive:
        if len(archive.namelist()) != 1 or archive.read(archive.namelist()[0]) != rom:
            raise AssertionError("MAME cartridge archive differs from configured cartridge")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for name in ("run_a", "run_b"):
        env = os.environ.copy()
        env["CT_SERVE_RUN"] = name
        command = [str(MAME), "sc3000", "-noreadconfig", "-hashpath", ".tools/mame-0.289/hash",
                   "-rompath", "build/mame/roms", "-cart", "champtns", "-video", "none",
                   "-sound", "none", "-skip_gameinfo", "-nothrottle", "-seconds_to_run", "26",
                   "-autoboot_script", "scripts/capture_source_serve.lua"]
        result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, timeout=120)
        if result.returncode or f"SERVE_CAPTURE_COMPLETE {name}" not in result.stdout:
            raise RuntimeError(f"Incomplete {name}: {result.stdout[-1000:]} {result.stderr[-1000:]}")
    first, second = (OUTPUT / "run_a.tsv"), (OUTPUT / "run_b.tsv")
    if first.read_bytes() != second.read_bytes():
        raise AssertionError("Serve captures are not byte-identical")
    rows = read_capture(first)
    ram = bytearray(bytes.fromhex(rows[0]["ram"]))
    irq_tail_06b1(ram, rom=rom)  # checkpoint 1299 precedes its tail write
    vram = bytearray(16384)
    path_counts = {}
    for row in rows[1:]:
        frame = int(row["frame"])
        checkpoint = []
        result = run_translated_frame_body(
            ram, vram, game_bits=0x10 if frame < 1450 else 0,
            lower_refresh_bit=0, upper_refresh_bit=0, rom=rom,
            checkpoint=lambda state: checkpoint.append(bytes(state)),
        )
        for path in (result.lower_path, result.upper_path, result.ball_path):
            path_counts[path] = path_counts.get(path, 0) + 1
        expected = bytes.fromhex(row["ram"])
        if checkpoint != [expected]:
            differences = [(f"{i:02X}", f"{checkpoint[0][i]:02X}", f"{expected[i]:02X}")
                           for i in range(256) if checkpoint[0][i] != expected[i]]
            raise AssertionError(f"Translation mismatch at {frame}: {differences[:16]}")
    fields = {"lower_phase": 0x3A, "ball_phase": 0x38, "point_flags": 0x39,
              "ball_y": 0x4D, "ball_x": 0x4E, "serve_counter": 0x6C}
    transitions = []
    prior = None
    for row in rows:
        ram = bytes.fromhex(row["ram"])
        current = {name: ram[offset] for name, offset in fields.items()}
        if prior is None or any(current[name] != prior[name] for name in ("lower_phase", "ball_phase", "point_flags")):
            transitions.append({"frame": int(row["frame"]), **{name: f"{value:02X}" for name, value in current.items()}})
        prior = current
    report = {"emulator": "MAME 0.289 sc3000", "rom_sha256": EXPECTED_ROM_SHA256,
              "capture_sha256": hashlib.sha256(first.read_bytes()).hexdigest(),
              "repeat_byte_identical": True, "checkpoints": len(rows),
              "translated_updates_matched": len(rows) - 1,
              "translated_bytes_per_update": 256,
              "translated_path_counts": path_counts,
              "button_press_after_frame": 1300, "button_release_after_frame": 1450,
              "transitions": transitions}
    (OUTPUT / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
