"""Capture a live native serve and compare its early states with source RAM."""

import configparser
import csv
import hashlib
import json
import re
import sys
from pathlib import Path
from PIL import Image, ImageChops

from run_translated_prng_probe import ROOT, run
from run_amiga_score_copper_probe import FIELDS, output_rectangle


DISPLAY = ROOT / "build" / "amiga" / "gameplay-integration"
SOURCE = ROOT / "build" / "reference" / "source-serve" / "run_a.tsv"
LOG_PATTERN = re.compile(
    r"DBG: LIVE F=([0-9A-F]{2}) U=([0-9A-F]{2}) I=([0-9A-F]{2}) "
    r"X=([0-9A-F]{2}) SX=([0-9A-F]{2}) E=([0-9A-F]{2}) "
    r"B=([0-9A-F]{2}) BY=([0-9A-F]{2}) BX=([0-9A-F]{2}) "
    r"LP=([0-9A-F]{2}) UP=([0-9A-F]{2}) SB=([0-9A-F]{2}) ST=([0-9A-F]{2})"
)


def source_ball_slot(ram):
    slots = [slot for slot in (0, 4, 8)
             if ram[0x10 + 4 * slot] < 0xC0 and ram[0x13 + 4 * slot] & 15]
    if len(slots) != 1:
        raise AssertionError(f"Expected one source ball slot, got {slots}")
    return slots[0]


def main():
    # Also builds the exact executable and checks the existing left-movement run.
    run([sys.executable, "scripts/run_amiga_gameplay_integration_probe.py"], timeout=120)
    config = configparser.ConfigParser(interpolation=None)
    if not config.read(ROOT / "config.local.ini", encoding="utf-8"):
        raise FileNotFoundError("config.local.ini")
    copperline = Path(config["tools"]["copperline"])
    amiga_rom = Path(config["inputs"]["amiga_rom"])
    executable = DISPLAY / "gameplay-integration"
    png = DISPLAY / "serve.png"
    gif = DISPLAY / "serve.gif"
    scored_png = DISPLAY / "serve-scored.png"
    log = run([str(copperline), "--factory", "--model", "A500", "--chipset", "OCS",
               "--video", "PAL", "--cpu", "68000", "--chip", "512K", "--slow", "0",
               "--fast", "0", "--noaudio", "--run", str(executable),
               "--joy-after", "5", "fire", "2500", "2",
               "--screenshot-after", "7", str(png), "--gif-after", "4", str(gif),
               "--gif-seconds", "10", str(amiga_rom)], timeout=120)
    (DISPLAY / "serve.log").write_text(log, encoding="utf-8")
    scored_log = run([str(copperline), "--factory", "--model", "A500", "--chipset", "OCS",
                      "--video", "PAL", "--cpu", "68000", "--chip", "512K", "--slow", "0",
                      "--fast", "0", "--noaudio", "--run", str(executable),
                      "--joy-after", "5", "fire", "2500", "2",
                      "--screenshot-after", "10", str(scored_png), str(amiga_rom)], timeout=120)
    (DISPLAY / "serve-scored.log").write_text(scored_log, encoding="utf-8")
    if not png.read_bytes().startswith(b"\x89PNG") or not gif.read_bytes().startswith(b"GIF8"):
        raise AssertionError("Serve display capture missing")
    records = [tuple(int(part, 16) for part in match) for match in LOG_PATTERN.findall(log)]
    if len(records) < 3:
        raise AssertionError(f"Only {len(records)} native serve checkpoints")
    with SOURCE.open(newline="", encoding="utf-8") as handle:
        source = {int(row["frame"]): bytes.fromhex(row["ram"])
                  for row in csv.DictReader(handle, delimiter="\t")}
    checked = []
    for frame, updates, input_bits, lower_x, sprite_x, error, ball_slot, ball_y, ball_x, lower_phase, upper_phase, score_b, status in records[:3]:
        source_frame = 1299 + updates
        ram = source[source_frame]
        expected = (ram[0x4A], ram[0x15], source_ball_slot(ram),
                    ram[0x34], ram[0x35], ram[0x49], ram[0x45])
        actual = (lower_x, sprite_x, ball_slot, ball_y, ball_x, lower_phase, upper_phase)
        if actual != expected or error:
            raise AssertionError(f"Native update {updates} differs from source frame {source_frame}: "
                                 f"native={actual}, source={expected}, error={error}")
        expected_score = (0, 0) if source_frame < 1434 else (ram[0x3F], 0)
        if (score_b, status) != expected_score:
            raise AssertionError(f"Visible score selection at source frame {source_frame}: "
                                 f"native={(score_b, status)}, expected={expected_score}")
        checked.append({"pal_frame": frame, "source_update": updates,
                        "source_frame": source_frame, "ball_slot": ball_slot,
                        "ball_yx": [ball_y, ball_x], "input_bits": input_bits})
    if [item["ball_slot"] for item in checked] != [4, 4, 0]:
        raise AssertionError(f"Serve did not move the ball into flight slot: {checked}")
    if any(record[5] for record in records):
        raise AssertionError("Native sprite bridge reported an error during serve capture")
    earlier = Image.open(png).convert("RGB")
    scored = Image.open(scored_png).convert("RGB")
    if earlier.size != scored.size:
        raise AssertionError("Serve screenshot dimensions differ")
    pixel_changes = {}
    for field in FIELDS:
        box = output_rectangle(field)
        pixel_changes[field.name] = ImageChops.difference(earlier.crop(box), scored.crop(box)).getbbox() is not None
    if not pixel_changes["point_b"] or any(pixel_changes[name] for name in
                                            ("point_a", "games_a", "games_b", "status", "mode")):
        raise AssertionError(f"Scored point pixels differ from expected fields: {pixel_changes}")
    report = {"executable_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
              "source_state_matches": checked, "native_log_checkpoints": len(records),
              "screenshot": str(png), "gif": str(gif),
              "scored_screenshot": str(scored_png), "score_field_pixel_changes": pixel_changes,
              "machine": "PAL A500 OCS 68000, 512K chip, 0 slow/fast, Kickstart 1.3"}
    (DISPLAY / "serve-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
