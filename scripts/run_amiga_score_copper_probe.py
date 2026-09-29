"""Test a horizontal Copper bitplane-pointer switch over the left point field."""

import configparser
import json
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageChops

from run_translated_prng_probe import ROOT, ASSEMBLER, run
from source_score_display import POINT_TILES


OUT = ROOT / "build" / "amiga" / "score-copper-probe"
DISPLAY = ROOT / "build" / "amiga" / "sprite-probe"
START_Y = 40
HEIGHT = 16


def commands(horizontal):
    lines = []
    for y in range(START_Y, START_Y + HEIGHT):
        raster = y + 0x2C
        lines.append(f"        dc.w ${raster:02x}{horizontal | 1:02x},$fffe,$00e8,0,$00ea,0")
        lines.append(f"        dc.w ${raster:02x}d1,$fffe,$00e8,0,$00ea,0")
    return "\n".join(lines) + "\n"


def main():
    run([sys.executable, "scripts/generate_amiga_sprite_probe.py"], timeout=120)
    if not (DISPLAY / "gameplay-sprites.png").is_file():
        run([sys.executable, "scripts/run_amiga_sprite_probe.py"], timeout=120)
    config = configparser.ConfigParser(interpolation=None)
    if not config.read(ROOT / "config.local.ini", encoding="utf-8"):
        raise FileNotFoundError("config.local.ini")
    copperline = Path(config["tools"]["copperline"])
    amiga_rom = Path(config["inputs"]["amiga_rom"])
    OUT.mkdir(parents=True, exist_ok=True)
    plane0 = bytearray((DISPLAY / "plane0.bin").read_bytes())
    for row in range(HEIGHT):
        plane0[(START_Y + row) * 32 + 2:(START_Y + row) * 32 + 4] = b"\xff\xff"
    (OUT / "plane0.bin").write_bytes(plane0)
    vram = (ROOT / "build" / "reference" / "source-timing" / "sprite-f1310.vram").read_bytes()
    plane2 = (DISPLAY / "plane2.bin").read_bytes()
    results = []
    for point in (0, 1):
        overlay = bytearray(plane2[START_Y * 32:(START_Y + HEIGHT) * 32])
        tiles = POINT_TILES[point * 4:point * 4 + 4]
        for row in range(HEIGHT):
            tile_row = row // 8
            pixel_row = row % 8
            overlay[row * 32 + 2:row * 32 + 4] = bytes(
                vram[0x2000 + tiles[tile_row * 2 + column] * 8 + pixel_row]
                for column in range(2))
        (OUT / f"overlay-point-{point}.bin").write_bytes(overlay)
    (OUT / "score-cop-commands.i").write_text(commands(0x3C), encoding="ascii")
    executable = OUT / "score-copper-probe"
    run([str(ASSEMBLER), "-Fhunkexe", "-kick1hunks", "-m68000", "-o",
         str(executable), "amiga/score_copper_probe.s"])
    xdftool = shutil.which("xdftool")
    if xdftool:
        startup = OUT / "startup-sequence"
        startup.write_bytes(b"score-copper-probe\n")
        run([xdftool, "-f", str(OUT / "score-copper-probe.adf"),
             "format", "SCORECOPPER", "+", "makedir", "S", "+",
             "write", str(startup), "S/startup-sequence", "+",
             "write", str(executable), "score-copper-probe", "+",
             "boot", "install", "boot1x"])
    captures = []
    for point in (0, 1):
        screenshot = OUT / f"score-point-{point}.png"
        args = [str(copperline), "--factory", "--model", "A500", "--chipset", "OCS",
                "--video", "PAL", "--cpu", "68000", "--chip", "512K", "--slow", "0",
                "--fast", "0", "--noaudio", "--run", str(executable)]
        if point:
            args += ["--joy-after", "5", "fire", "2500", "2"]
            args += ["--gif-after", "4", str(OUT / "score-toggle.gif"),
                     "--gif-seconds", "4"]
        args += ["--screenshot-after", "6", str(screenshot), str(amiga_rom)]
        log = run(args, timeout=60)
        (OUT / f"score-point-{point}.log").write_text(log, encoding="utf-8")
        current = Image.open(screenshot).convert("RGB")
        captures.append(current)
        results.append({"point": point, "screenshot": str(screenshot)})
    changed = ImageChops.difference(*captures)
    if not (OUT / "score-toggle.gif").read_bytes().startswith(b"GIF8"):
        raise AssertionError("Score toggle GIF is missing")
    bbox = changed.getbbox()
    if bbox is None or not (49 <= bbox[0] <= bbox[2] <= 84 and 94 <= bbox[1] <= bbox[3] <= 126):
        raise AssertionError(f"Point glyph changed pixels outside the intended rectangle: {bbox}")
    baseline = Image.open(DISPLAY / "gameplay-sprites.png").convert("RGB")
    if ImageChops.difference(baseline, captures[0]).crop((0, 80, 120, 140)).getbbox():
        raise AssertionError("Selected zero differs from the original score pixels")
    results.append({"score_change_bbox": bbox, "horizontal_wait": 0x3D})
    (OUT / "report.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
