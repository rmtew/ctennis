"""Build a live-input/display integration probe from the verified gameplay body."""

import configparser
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

from run_translated_prng_probe import ROOT, OUT, ASSEMBLER, run
from source_irq_tail import irq_tail_06b1
from run_amiga_score_copper_probe import make_banks, make_copper_and_patch_tables


DISPLAY = ROOT / "build" / "amiga" / "gameplay-integration"


def main():
    config = configparser.ConfigParser(interpolation=None)
    if not config.read(ROOT / "config.local.ini", encoding="utf-8"):
        raise FileNotFoundError("config.local.ini")
    copperline = Path(config["tools"]["copperline"])
    amiga_rom = Path(config["inputs"]["amiga_rom"])
    cartridge = Path(config["inputs"]["cartridge"]).read_bytes()
    for path in (ASSEMBLER, copperline, amiga_rom):
        if not path.is_file():
            raise FileNotFoundError(path)
    run([sys.executable, "scripts/run_translated_player_frame_probe.py"], timeout=120)
    run([sys.executable, "scripts/generate_amiga_sprite_probe.py"], timeout=120)
    score_vram = (ROOT / "build" / "reference" / "source-timing" / "sprite-f1310.vram").read_bytes()
    score_output = ROOT / "build" / "amiga" / "score-copper-probe"
    score_output.mkdir(parents=True, exist_ok=True)
    make_banks(score_vram)
    make_copper_and_patch_tables()
    capture = ROOT / "build" / "reference" / "source-timing" / "run_a.tsv"
    with capture.open(newline="", encoding="utf-8") as handle:
        initial = next(bytes.fromhex(row["ram"])[:256]
                       for row in csv.DictReader(handle, delimiter="\t")
                       if row["event"] == "checkpoint" and int(row["frame"]) == 1299)
    ram = bytearray(initial)
    irq_tail_06b1(ram, rom=cartridge)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "live-initial-ram.bin").write_bytes(ram)
    DISPLAY.mkdir(parents=True, exist_ok=True)
    executable = DISPLAY / "gameplay-integration"
    png = DISPLAY / "gameplay-integration.png"
    gif = DISPLAY / "gameplay-integration.gif"
    run([str(ASSEMBLER), "-Fhunkexe", "-kick1hunks", "-m68000", "-o",
         str(executable), "amiga/gameplay_integration_probe.s"])
    log = run([str(copperline), "--factory", "--model", "A500", "--chipset", "OCS",
               "--video", "PAL", "--cpu", "68000", "--chip", "512K", "--slow", "0",
               "--fast", "0", "--noaudio", "--run", str(executable),
               "--joy-after", "7", "left", "334", "2",
               "--screenshot-after", "8", str(png), "--gif-after", "4", str(gif),
               "--gif-seconds", "10", str(amiga_rom)], timeout=120)
    (DISPLAY / "copperline.log").write_text(log, encoding="utf-8")
    for expected in ("cpu=M68000", "chip_ram=512K", "fast_ram=0K", "slow_ram=0K",
                     "chipset=Ocs", "video=Pal", "Kickstart 1.3"):
        if expected not in log:
            raise AssertionError(f"Copperline profile missing {expected}")
    if not png.read_bytes().startswith(b"\x89PNG") or not gif.read_bytes().startswith(b"GIF8"):
        raise AssertionError("Native gameplay display capture missing")
    states = [tuple(int(part, 16) for part in match)
              for match in re.findall(
                  r"DBG: LIVE F=([0-9A-F]{2}) U=([0-9A-F]{2}) I=([0-9A-F]{2}) "
                  r"X=([0-9A-F]{2}) SX=([0-9A-F]{2}) E=([0-9A-F]{2}) B=([0-9A-F]{2})", log)]
    if len(states) < 3 or [(frame, updates) for frame, updates, *_ in states[:2]] != [(50, 59), (100, 119)]:
        raise AssertionError(f"PAL/source update cadence is wrong: {states[:3]}")
    if states[-1][3] >= 0xC0 or not any(state[3] < 0xC0 for state in states):
        raise AssertionError(f"Scripted left input did not move source player state: {states}")
    if any(state[3] != state[4] for state in states):
        raise AssertionError(f"Visible sprite buffer diverged from player X: {states}")
    if any(state[5] for state in states):
        raise AssertionError(f"Sprite hardware-fit error in native bridge: {states}")
    if not all(state[6] in (0, 4, 8, 0xFF) for state in states):
        raise AssertionError(f"Unexpected source ball slot: {states}")
    report = {"executable_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
              "executable_bytes": executable.stat().st_size,
              "screenshot": str(png), "gif": str(gif),
              "initial_ram_from": "source frame 1299 plus its interrupt tail",
              "clock_checkpoints": [(frame, updates) for frame, updates, *_ in states[:2]],
              "lower_x_before_after_left_input": [states[0][3], states[-1][3]],
              "native_sprite_bridge_errors": sorted({state[5] for state in states}),
              "observed_ball_slots": sorted({state[6] for state in states}),
              "display_scope": "live source sprites, native Copper score selection, Paula tone output and static court",
              "machine": "PAL A500 OCS 68000, 512K chip, 0 slow/fast, Kickstart 1.3"}
    (DISPLAY / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
