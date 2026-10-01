"""Build and verify native Copper selection for all changing score fields."""

import configparser
import json
import math
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageChops

from run_translated_prng_probe import ROOT, ASSEMBLER, run
from source_score_display import GAME_TILES, MODE_TILES, POINT_TILES, STATUS_TILES
from generate_amiga_sprite_probe import PALETTE


OUT = ROOT / "build" / "amiga" / "score-copper-probe"
DISPLAY = ROOT / "build" / "amiga" / "sprite-probe"
SCREEN_WIDTH = 256
BYTES_PER_ROW = SCREEN_WIDTH // 8
RASTER_TOP = 0x2C
DISPLAY_PALETTE = {0: 0x000, 1: 0x000, 5: 0x77F, 7: 0x000,
                   8: 0x000, 10: 0xDC5, 14: 0xCCC, 15: 0xFFF}


@dataclass(frozen=True)
class Field:
    name: str
    index: int
    x: int
    y: int
    columns: int
    rows: int
    count: int
    tiles: bytes
    planes: tuple[int, ...]
    fixed_planes: tuple[int, ...]
    wait: int
    switch_byte: int

    @property
    def width(self):
        return self.columns * 8

    @property
    def height(self):
        return self.rows * 8


FIELDS = (
    Field("point_a", 0, 16, 40, 2, 2, 7, POINT_TILES, (2,), (0,), 0x3D, 2),
    # Switch before the x=208 fetch, not between its high/low pointer writes.
    # Native gameplay changes bus contention; a split pointer crossing 64K
    # otherwise reads unrelated data just left of the right point glyph.
    Field("point_b", 1, 224, 40, 2, 2, 7, POINT_TILES, (2,), (0,), 0x99, 26),
    Field("games_a", 2, 16, 72, 2, 6, 7, GAME_TILES, (1,), (3,), 0x3D, 2),
    Field("games_b", 3, 224, 72, 2, 6, 7, GAME_TILES, (1,), (3,), 0xA1, 28),
    # Four planes begin switching at x=64, leaving time before status x=112.
    Field("status", 4, 112, 96, 3, 1, 7, STATUS_TILES, (0, 1, 2, 3), (), 0x51, 8),
    Field("mode", 5, 208, 144, 5, 1, 3, MODE_TILES, (3,), (0, 1, 2), 0x99, 26),
)


def source_pixel(vram, field, variant, dx, dy):
    tile = field.tiles[variant * field.columns * field.rows
                       + (dy // 8) * field.columns + dx // 8]
    y = field.y + dy
    bank = (y // 64) * 0x800
    line = dy % 8
    bits = vram[0x2000 + bank + tile * 8 + line]
    colours = vram[bank + tile * 8 + line]
    return (colours >> 4) if bits & (0x80 >> (dx % 8)) else (colours & 15)


def set_bit(buffer, x, y, plane, colour):
    offset = y * BYTES_PER_ROW + x // 8
    mask = 0x80 >> (x % 8)
    if colour & (1 << plane):
        buffer[offset] |= mask
    else:
        buffer[offset] &= ~mask


def make_banks(vram):
    planes = [bytearray((DISPLAY / f"plane{plane}.bin").read_bytes())
              for plane in range(4)]
    for field in FIELDS:
        for plane in field.fixed_planes:
            for y in range(field.y, field.y + field.height):
                for x in range(field.x, field.x + field.width):
                    set_bit(planes[plane], x, y, plane, 1 << plane)
    for plane, data in enumerate(planes):
        (OUT / f"plane{plane}.bin").write_bytes(data)

    bank_lines = []
    checked_variants = 0
    for field in FIELDS:
        for variant in range(field.count):
            variant_banks = {}
            for plane in field.planes:
                bank = bytearray(planes[plane][field.y * BYTES_PER_ROW:
                                               (field.y + field.height) * BYTES_PER_ROW])
                for dy in range(field.height):
                    for dx in range(field.width):
                        pixel = source_pixel(vram, field, variant, dx, dy)
                        set_bit(bank, field.x + dx, dy, plane, pixel)
                label = f"score_bank_{field.name}_{variant}_p{plane}"
                filename = f"{label}.bin"
                (OUT / filename).write_bytes(bank)
                variant_banks[plane] = bank
                bank_lines.append(f'{label}: incbin "build/amiga/score-copper-probe/{filename}"')
            for dy in range(field.height):
                for dx in range(field.width):
                    x = field.x + dx
                    index = 0
                    for plane in range(4):
                        data = variant_banks.get(plane, planes[plane])
                        row = dy if plane in variant_banks else field.y + dy
                        if data[row * BYTES_PER_ROW + x // 8] & (0x80 >> (x % 8)):
                            index |= 1 << plane
                    expected = PALETTE[source_pixel(vram, field, variant, dx, dy)]
                    if DISPLAY_PALETTE.get(index) != expected:
                        raise AssertionError(f"{field.name} value {variant} pixel {dx},{dy}: "
                                             f"Amiga index {index} differs from source colour {expected:03x}")
            checked_variants += 1
    (OUT / "score-bank-data.i").write_text("\n".join(bank_lines) + "\n", encoding="ascii")
    return checked_variants


def make_copper_and_patch_tables():
    commands = []
    descriptors = []
    pointer_tables = []

    def emit_pointer(plane, field=None, y=0, byte_offset=None, fixed=None):
        index = len(descriptors)
        hi = f"score_cop_{index}_hi"
        lo = f"score_cop_{index}_lo"
        table = f"score_pointer_table_{index}"
        commands.append(f"{hi}: dc.w ${0xE0 + plane * 4:04x},0")
        commands.append(f"{lo}: dc.w ${0xE2 + plane * 4:04x},0")
        descriptors.append(f"        dc.l {hi}+2,{lo}+2,{table}\n        dc.w ${0xFFFF if fixed is not None else field.index:04x}")
        if fixed is not None:
            pointer_tables.append(f"{table}: dc.l {fixed}")
        else:
            row = y - field.y
            addresses = ",".join(
                f"score_bank_{field.name}_{variant}_p{plane}+{row * BYTES_PER_ROW + byte_offset}"
                for variant in range(field.count))
            pointer_tables.append(f"{table}: dc.l {addresses}")

    rows = sorted({y for field in FIELDS for y in range(field.y, field.y + field.height)})
    status = FIELDS[4]
    for y in rows:
        if y == status.y:
            commands.append(f"        dc.w ${y + RASTER_TOP:02x}01,$fffe")
            for plane in status.planes:
                emit_pointer(plane, status, y, 0)
        if y == status.y + status.height:
            commands.append(f"        dc.w ${y + RASTER_TOP:02x}01,$fffe")
            for plane in status.planes:
                emit_pointer(plane, fixed=f"plane{plane}+{y * BYTES_PER_ROW}")
        fields = sorted((field for field in FIELDS if field.name != "status"
                         and field.y <= y < field.y + field.height), key=lambda field: field.x)
        events = [(field.x, field, field.planes, field.wait, field.switch_byte)
                  for field in fields]
        if status.y <= y < status.y + status.height:
            # Restore status plane 1 after the left game tally and before the text.
            events.append((64, status, (1,), status.wait, 8))
        for _, field, planes, wait, byte_offset in sorted(events):
            commands.append(f"        dc.w ${y + RASTER_TOP:02x}{wait:02x},$fffe")
            for plane in planes:
                emit_pointer(plane, field, y, byte_offset)
        commands.append(f"        dc.w ${y + RASTER_TOP:02x}d1,$fffe")
        for plane in sorted({plane for field in fields for plane in field.planes}):
            if plane == 1 and status.y <= y < status.y + status.height - 1:
                emit_pointer(plane, status, y + 1, 0)
            else:
                emit_pointer(plane, fixed=f"plane{plane}+{(y + 1) * BYTES_PER_ROW}")
    (OUT / "score-cop-commands.i").write_text("\n".join(commands) + "\n", encoding="ascii")
    table_text = (f"SCORE_PATCH_COUNT equ {len(descriptors)}\n"
                  "score_patch_descriptors:\n" + "\n".join(descriptors) + "\n"
                  + "\n".join(pointer_tables) + "\n")
    (OUT / "score-patch-tables.i").write_text(table_text, encoding="ascii")
    return len(descriptors)


def capture(copperline, rom, executable, alternate):
    name = "alternate" if alternate else "original"
    screenshot = OUT / f"score-{name}.png"
    args = [str(copperline), "--factory", "--model", "A500", "--chipset", "OCS",
            "--video", "PAL", "--cpu", "68000", "--chip", "512K", "--slow", "0",
            "--fast", "0", "--noaudio", "--run", str(executable)]
    if alternate:
        args += ["--joy-after", "5", "fire", "2500", "2",
                 "--gif-after", "4", str(OUT / "score-toggle.gif"), "--gif-seconds", "4"]
    args += ["--screenshot-after", "6", str(screenshot), str(rom)]
    log = run(args, timeout=90)
    (OUT / f"score-{name}.log").write_text(log, encoding="utf-8")
    return Image.open(screenshot).convert("RGB"), screenshot


def output_rectangle(field):
    # Copperline's output scales the 256-pixel image to approximately 548 pixels.
    return (math.floor(2.14 * field.x + 14) - 5,
            2 * field.y + 12,
            math.ceil(2.14 * (field.x + field.width) + 14) + 5,
            2 * (field.y + field.height) + 16)


def verify_images(original, alternate):
    baseline = Image.open(DISPLAY / "gameplay-sprites.png").convert("RGB")
    if original.size != alternate.size or original.size != baseline.size:
        raise AssertionError("Screenshot dimensions differ")
    difference = ImageChops.difference(original, alternate)
    baseline_difference = ImageChops.difference(baseline, original)
    rectangles = {field.name: output_rectangle(field) for field in FIELDS}
    changed = {field.name: 0 for field in FIELDS}
    baseline_errors = {field.name: 0 for field in FIELDS}
    outside = 0
    for y in range(original.height):
        for x in range(original.width):
            for field in FIELDS:
                left, top, right, bottom = rectangles[field.name]
                if left <= x < right and top <= y < bottom:
                    if difference.getpixel((x, y)) != (0, 0, 0):
                        changed[field.name] += 1
                    if baseline_difference.getpixel((x, y)) != (0, 0, 0):
                        baseline_errors[field.name] += 1
                    break
            else:
                if difference.getpixel((x, y)) != (0, 0, 0):
                    outside += 1
    if outside or any(baseline_errors.values()) or not all(changed.values()):
        raise AssertionError(f"Score pixels escaped fields or baseline changed: "
                             f"outside={outside}, baseline={baseline_errors}, changed={changed}")
    return {"field_changed_pixels": changed, "original_field_differences": baseline_errors,
            "outside_field_changed_pixels": outside, "field_output_rectangles": rectangles}


def main():
    run([sys.executable, "scripts/generate_amiga_sprite_probe.py"], timeout=120)
    if not (DISPLAY / "gameplay-sprites.png").is_file():
        run([sys.executable, "scripts/run_amiga_sprite_probe.py"], timeout=120)
    config = configparser.ConfigParser(interpolation=None)
    if not config.read(ROOT / "config.local.ini", encoding="utf-8"):
        raise FileNotFoundError("config.local.ini")
    copperline = Path(config["tools"]["copperline"])
    rom = Path(config["inputs"]["amiga_rom"])
    OUT.mkdir(parents=True, exist_ok=True)
    vram = (ROOT / "build/reference/source-timing/sprite-f1310.vram").read_bytes()
    checked_variants = make_banks(vram)
    patch_count = make_copper_and_patch_tables()
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
    original, original_path = capture(copperline, rom, executable, False)
    alternate, alternate_path = capture(copperline, rom, executable, True)
    proof = verify_images(original, alternate)
    if not (OUT / "score-toggle.gif").read_bytes().startswith(b"GIF8"):
        raise AssertionError("Score toggle GIF missing")
    report = {"executable_bytes": executable.stat().st_size,
              "copper_pointer_pairs": patch_count,
              "variants_color_checked": checked_variants,
              "original_screenshot": str(original_path),
              "alternate_screenshot": str(alternate_path),
              "gif": str(OUT / "score-toggle.gif"), **proof}
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
