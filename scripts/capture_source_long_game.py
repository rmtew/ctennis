"""Repeatably capture the source cartridge through a four-point game award."""

import configparser
import csv
import hashlib
import json
import os
import subprocess
import zipfile
from collections import Counter
from pathlib import Path

from capture_source_serve import ROOT, MAME, CARTRIDGE_ZIP, EXPECTED_ROM_SHA256


OUT = ROOT / "build" / "reference" / "source-long-game"
LAST = 3500


def read_rows(path):
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    if not rows or int(rows[0]["frame"]) != 1299 or int(rows[-1]["frame"]) != LAST:
        raise AssertionError("Long source capture bounds are wrong")
    frames = [int(row["frame"]) for row in rows]
    if frames != sorted(frames):
        raise AssertionError("Long source checkpoints are out of order")
    for row in rows:
        ram = bytes.fromhex(row["ram"])
        if len(ram) != 256 or (ram[0x6B] + 1) & 255 != int(row["tick_written"], 16):
            raise AssertionError(f"Invalid RAM/tick at frame {row['frame']}")
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
            raise AssertionError("MAME archive differs from the configured cartridge")
    OUT.mkdir(parents=True, exist_ok=True)
    for name in ("run_a", "run_b"):
        env = os.environ.copy()
        env["CT_LONG_RUN"] = name
        env["CT_LONG_LAST"] = str(LAST)
        command = [str(MAME), "sc3000", "-noreadconfig", "-hashpath", ".tools/mame-0.289/hash",
                   "-rompath", "build/mame/roms", "-cart", "champtns", "-video", "none",
                   "-sound", "none", "-skip_gameinfo", "-nothrottle", "-seconds_to_run", "60",
                   "-snapshot_directory", str(OUT),
                   "-autoboot_script", "scripts/capture_source_long_game.lua"]
        result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, timeout=120)
        if result.returncode or f"LONG_GAME_CAPTURE_COMPLETE {name}" not in result.stdout:
            raise RuntimeError(f"Incomplete {name}: {result.stdout[-1000:]} {result.stderr[-1000:]}")
    first, second = OUT / "run_a.tsv", OUT / "run_b.tsv"
    if first.read_bytes() != second.read_bytes():
        raise AssertionError("Long source captures differ")
    rows = read_rows(first)
    changed = []
    previous = None
    for ordinal, row in enumerate(rows):
        ram = bytes.fromhex(row["ram"])
        scores = tuple(ram[index] for index in (0x3E, 0x3F, 0x40, 0x41))
        if scores != previous:
            changed.append({"source_update": ordinal, "frame": int(row["frame"]),
                            "points_a_b_games_a_b": scores})
        previous = scores
    expected = [(1299, (0, 0, 0, 0)), (1433, (0, 1, 0, 0)),
                (1768, (0, 2, 0, 0)), (2106, (0, 3, 0, 0)),
                (2503, (0, 0, 0, 1))]
    if [(item["frame"], item["points_a_b_games_a_b"]) for item in changed[:5]] != expected:
        raise AssertionError(f"Expected four-point game award missing: {changed[:5]}")
    counts = Counter(int(row["frame"]) for row in rows)
    report = {"emulator": "MAME 0.289 sc3000", "rom_sha256": EXPECTED_ROM_SHA256,
              "repeat_byte_identical": True, "capture_sha256": hashlib.sha256(first.read_bytes()).hexdigest(),
              "checkpoints": len(rows), "first_last_frame": [1299, LAST],
              "non_single_checkpoint_frames": {str(frame): count for frame, count in counts.items() if count != 1},
              "score_transitions": changed,
              "input": "port-1 fire held from source frame 1300 through capture end"}
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
