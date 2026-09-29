"""Capture twice and verify a bounded source gameplay timing/input baseline."""

import argparse
import configparser
import csv
import hashlib
import json
import os
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "build" / "reference" / "source-timing"
MAME = ROOT / ".tools" / "mame-0.289" / "mame.exe"
CARTRIDGE_ZIP = ROOT / "build" / "mame" / "roms" / "sg1000" / "champtns.zip"
EXPECTED_SHA256 = "19bb6647f14ef50f976e8d0a06d389f06b2e700d54a54fb1734d3140f9745ad1"
FIRST_FRAME = 1280
LAST_UPDATE_FRAME = 1339


def run(command: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=90, **kwargs)
    if result.returncode:
        raise RuntimeError(f"{command[0]} failed ({result.returncode}): {result.stderr[-3000:]}")
    return result


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    if not rows or any(len(row.get("ram", "")) not in (0, 2048) for row in rows):
        raise ValueError(f"Malformed timing capture: {path}")
    return rows


def verify_capture(rows: list[dict[str, str]]) -> dict[str, object]:
    by_frame: dict[int, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_frame[int(row["frame"])].append(row)
    if sorted(by_frame) != list(range(FIRST_FRAME, LAST_UPDATE_FRAME + 2)):
        raise AssertionError("Unexpected frame coverage")

    snapshots = {}
    for frame in range(FIRST_FRAME, LAST_UPDATE_FRAME + 1):
        events = by_frame[frame]
        kinds = Counter(row["event"] for row in events)
        if kinds["checkpoint"] != 1 or kinds["port"] != 12 or kinds["frame_done"] != 1:
            raise AssertionError(f"Update/input count differs in frame interval {frame}: {kinds}")
        ports = [row for row in events if row["event"] == "port"]
        if {(row["pc"], row["address"]) for row in ports} != {("093A", "00DC")}:
            raise AssertionError(f"Unexpected input port/reader in interval {frame}")
        expected_first_group = "FB" if 1300 <= frame < 1320 else "FF"
        if [row["value"] for row in ports] != [expected_first_group] * 6 + ["FF"] * 6:
            raise AssertionError(f"Input read values differ in interval {frame}")

        writes = [row for row in events if row["event"] == "write"]
        expected_writes = [("084E", "C053", "04" if 1300 <= frame < 1320 else "00"),
                           ("0858", "C056", "00")]
        if 1300 <= frame < 1320:
            expected_writes.append(("143B", "C04A", None))
        if [(row["pc"], row["address"], row["value"] if expected[2] is not None else None)
            for row, expected in zip(writes, expected_writes)] != expected_writes or len(writes) != len(expected_writes):
            raise AssertionError(f"Normalized input/movement writes differ in interval {frame}")
        if [row["event"] for row in events[:13]] != ["frame_done"] + ["port"] * 12:
            raise AssertionError(f"Input reads do not precede state writes in interval {frame}")
        if events[-1]["event"] != "checkpoint":
            raise AssertionError(f"Checkpoint is not after gameplay writes in interval {frame}")

        checkpoint = next(row for row in events if row["event"] == "checkpoint")
        if checkpoint["pc"] != "06B5" or checkpoint["address"] != "C06B":
            raise AssertionError(f"Wrong gameplay checkpoint in interval {frame}")
        ram = bytes.fromhex(checkpoint["ram"])
        if ram[:2] != bytes((0x99, 0x06)) or (ram[0x6B] + 1) & 0xFF != int(checkpoint["value"], 16):
            raise AssertionError(f"Callback pointer/tick mismatch in interval {frame}")
        snapshots[frame] = {"sha256": hashlib.sha256(ram).hexdigest(),
                            "lower_x": f"{ram[0x4A]:02X}",
                            "input_a": f"{ram[0x53]:02X}",
                            "input_b": f"{ram[0x56]:02X}",
                            "tick_before_write": f"{ram[0x6B]:02X}"}

    if Counter(row["event"] for row in rows) != {
        "frame_done": 61, "port": 720, "write": 140, "checkpoint": 60,
    }:
        raise AssertionError("Unexpected total event counts")
    if snapshots[1299]["lower_x"] != "C0" or snapshots[1300]["lower_x"] != "BE" or snapshots[1320]["lower_x"] != "A2":
        raise AssertionError("Movement response differs from the observed baseline")
    expected_x = 0xC0
    for frame in range(1300, 1320):
        expected_x -= 2 if (frame - 1300) % 2 == 0 else 1
        if snapshots[frame]["lower_x"] != f"{expected_x:02X}":
            raise AssertionError(f"Alternating movement step differs in interval {frame}")
    return {"intervals": 60, "updates": 60, "port_reads": 720,
            "normalized_input_writes": 120, "movement_writes": 20,
            "selected_post_gameplay_ram": {str(frame): snapshots[frame]
                                           for frame in (1299, 1300, 1319, 1320, 1339)}}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true", help="Use existing ignored captures")
    args = parser.parse_args()
    config = configparser.ConfigParser(interpolation=None)
    if not config.read(ROOT / "config.local.ini", encoding="utf-8"):
        raise FileNotFoundError("config.local.ini")
    cartridge = Path(config["inputs"]["cartridge"]).read_bytes()
    cartridge_hash = hashlib.sha256(cartridge).hexdigest()
    if len(cartridge) != 8192 or cartridge_hash != EXPECTED_SHA256:
        raise ValueError("Configured cartridge differs from the identified G-1009 image")
    with zipfile.ZipFile(CARTRIDGE_ZIP) as archive:
        names = archive.namelist()
        if len(names) != 1 or archive.read(names[0]) != cartridge:
            raise ValueError("MAME cartridge archive does not contain the configured cartridge")
    version = run([str(MAME), "-version"]).stdout.strip()
    xml = run([str(MAME), "-listxml", "sc3000"]).stdout
    machine = ET.fromstring(xml).find("machine")
    if machine is None or machine.attrib["name"] != "sc3000":
        raise ValueError("MAME did not describe the expected SC-3000 machine")
    refresh = float(machine.find("display").attrib["refresh"])

    OUTPUT.mkdir(parents=True, exist_ok=True)
    if not args.verify_only:
        for run_name in ("run_a", "run_b"):
            environment = os.environ.copy()
            environment["CT_RUN"] = run_name
            command = [str(MAME), "sc3000", "-noreadconfig", "-hashpath", ".tools/mame-0.289/hash",
                       "-rompath", "build/mame/roms", "-cart", "champtns", "-video", "none",
                       "-sound", "none", "-skip_gameinfo", "-nothrottle", "-seconds_to_run", "23",
                       "-autoboot_script", "scripts/capture_source_timing.lua"]
            result = run(command, env=environment)
            if f"TIMING_CAPTURE_COMPLETE {run_name}" not in result.stdout:
                raise RuntimeError(f"Incomplete timing capture: {run_name}")

    first_file, second_file = OUTPUT / "run_a.tsv", OUTPUT / "run_b.tsv"
    first_bytes, second_bytes = first_file.read_bytes(), second_file.read_bytes()
    if first_bytes != second_bytes:
        raise AssertionError("Repeated source timing captures differ")
    details = verify_capture(load_rows(first_file))
    report = {"cartridge_sha256": cartridge_hash, "emulator": version,
              "emulator_sha256": hashlib.sha256(MAME.read_bytes()).hexdigest(),
              "machine": "sc3000", "video_refresh_hz": refresh,
              "video_frame_ms": 1000.0 / refresh,
              "emulator_options": ["-noreadconfig", "-video none", "-sound none",
                                   "-nothrottle", "-seconds_to_run 23"],
              "input_schedule": {"one_player_key_press_after_frame": 120,
                                 "one_player_key_release_after_frame": 420,
                                 "left_press_after_frame": 1300,
                                 "left_release_after_frame": 1320},
              "checkpoint": "C06B write at post-write PC 06B5; after gameplay body, before audio/VDP tail",
              "observed_interval_labels": [FIRST_FRAME, LAST_UPDATE_FRAME],
              "capture_sha256": hashlib.sha256(first_bytes).hexdigest(),
              "repeat_byte_identical": True, **details}
    (OUTPUT / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
