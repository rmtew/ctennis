"""Replay generated movement, animation and sprites at captured update states."""

import configparser
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

from run_translated_prng_probe import ROOT, OUT, ASSEMBLER, run
from source_gameplay_slice import run_gameplay_slice
from source_input_movement import input_update_0832, move_player_1404_145d, animate_player_14a7_14b3, build_player_sprites_10e9
from source_score_display import scoreboard_update_06eb
from source_irq_tail import irq_tail_06b1


ROM_SHA256 = "19bb6647f14ef50f976e8d0a06d389f06b2e700d54a54fb1734d3140f9745ad1"
CAPTURE = ROOT / "build" / "reference" / "source-timing" / "run_a.tsv"
COUNT = 40
OBSERVED = tuple([0x43, 0x44, 0x45, 0x46, 0x47, 0x49, 0x4A, 0x4B, 0x6D, 0x6E] +
                 list(range(0x14, 0x20)) + list(range(0x24, 0x30)))


def extract(generated, first, next_label, data_label=None):
    match = re.search(rf"(?ms)^{first}:\n(.*?)^{next_label}:", generated)
    if not match:
        raise AssertionError(f"Generated {first} boundary is missing")
    routine = f"{first}:\n" + match.group(1)
    if data_label:
        routine, count = re.subn(rf"(?m)^{data_label}:\n(?:dc\.b [^\n]*\n)+", "", routine)
        if count != 1:
            raise AssertionError(f"Expected one generated {data_label} table")
    if "ERROR" in routine:
        raise AssertionError(f"Unresolved translator diagnostic in {first}")
    return routine


def main():
    config = configparser.ConfigParser(interpolation=None)
    if not config.read(ROOT / "config.local.ini", encoding="utf-8"):
        raise FileNotFoundError("config.local.ini")
    copperline = Path(config["tools"]["copperline"])
    amiga_rom = Path(config["inputs"]["amiga_rom"])
    cartridge = Path(config["inputs"]["cartridge"]).read_bytes()
    if hashlib.sha256(cartridge).hexdigest() != ROM_SHA256:
        raise AssertionError("Unexpected source cartridge")
    for path in (ASSEMBLER, copperline, amiga_rom, CAPTURE):
        if not path.is_file():
            raise FileNotFoundError(path)
    OUT.mkdir(parents=True, exist_ok=True)
    source = OUT / "champion-raw.68k"
    run([sys.executable, "-W", "ignore", "scripts/z80268k.py", "--champion-source", "-n",
         "-i", "mot", "-o", "mot", "-c", str(source), "-I", str(OUT / "z80-support.i"),
         "--report-output", str(OUT / "report.json"),
         "build/analysis/champion-tennis-classified.asm"])
    generated = source.read_text(encoding="utf-8")
    motion = extract(generated, "lower_player_motion_update", "animate_lower_player")
    for label in ("lower_movement_bounds", "upper_movement_bounds"):
        motion, count = re.subn(rf"(?m)^{label}:\ndc\.b [^\n]*\n", "", motion)
        if count != 1:
            raise AssertionError(f"Expected one {label} table")
    animation = extract(generated, "animate_lower_player", "unsigned_multiply_byte", "animation_records")
    sprites = extract(generated, "build_player_sprites", "ball_flight_update", "player_sprite_descriptors")
    threshold = extract(generated, "threshold_table_lookup", "direction_ai")
    (OUT / "player-frame-routines.s").write_text(
        motion + animation + sprites + threshold, encoding="utf-8")
    memory = bytearray(65536)
    memory[:len(cartridge)] = cartridge
    (OUT / "player-frame-memory.bin").write_bytes(memory)

    with CAPTURE.open(newline="", encoding="utf-8") as handle:
        checkpoints = {int(row["frame"]): bytes.fromhex(row["ram"])
                       for row in csv.DictReader(handle, delimiter="\t")
                       if row["event"] == "checkpoint" and 1299 <= int(row["frame"]) <= 1339}
    if sorted(checkpoints) != list(range(1299, 1340)):
        raise AssertionError("Missing source update checkpoints")
    ram = bytearray(checkpoints[1299][:256])
    ram[0x6B] = (ram[0x6B] + 1) & 255
    vram = bytearray(16384)
    cases = bytearray()
    for frame in range(1300, 1340):
        scoreboard_update_06eb(ram, vram)
        input_update_0832(ram, game_bits=4 if frame < 1320 else 0)
        run_gameplay_slice(ram, lower_refresh_bit=0, upper_refresh_bit=0)
        before = bytes(ram)
        move_player_1404_145d(ram, upper=False)
        move_player_1404_145d(ram, upper=True)
        animate_player_14a7_14b3(ram, upper=False)
        animate_player_14a7_14b3(ram, upper=True)
        build_player_sprites_10e9(ram)
        expected = checkpoints[frame][:256]
        differences = [offset for offset in OBSERVED if ram[offset] != expected[offset]]
        if differences:
            raise AssertionError(f"Source-model/capture mismatch at frame {frame}: {differences[:12]}")
        cases.extend(before)
        cases.extend(ram)
        # The captured checkpoint follows ball-sprite placement. Complete
        # that source-model phase before advancing to the next frame.
        for slot in (0x10, 0x20, 0x30):
            ram[slot] = 0xC2
        ball_y = ram[0x34]
        slot = 0x30 if (ram[0x45] + 0x20) & 255 >= ball_y else (
            0x20 if (ram[0x49] + 0x24) & 255 >= ball_y else 0x10)
        ram[slot:slot + 4] = ram[0x4D:0x51]
        if ram[0x4D] >= 0xC0:
            ram[0x34] = 0xC2
            for ball_slot in (0x10, 0x20, 0x30):
                ram[ball_slot] = 0xC2
        irq_tail_06b1(ram, rom=cartridge)
        captured_after = bytearray(expected)
        captured_after[0x6B] = (captured_after[0x6B] + 1) & 255
        if ram != captured_after:
            differences = [offset for offset in range(256) if ram[offset] != captured_after[offset]]
            raise AssertionError(f"Full source replay mismatch at frame {frame}: {differences[:12]}")
    (OUT / "player-frame-cases.bin").write_bytes(cases)
    executable = OUT / "translated-player-frame-probe"
    run([str(ASSEMBLER), "-Fhunkexe", "-kick1hunks", "-m68000", "-o",
         str(executable), "amiga/translated_player_frame_probe.s"])
    log = run([str(copperline), "--factory", "--model", "A500", "--chipset", "OCS",
               "--video", "PAL", "--cpu", "68000", "--chip", "512K", "--slow", "0",
               "--fast", "0", "--noaudio", "--run", str(executable),
               "--exit-on-return", str(amiga_rom)], timeout=120)
    (OUT / "player-frame-copperline.log").write_text(log, encoding="utf-8")
    for expected in ("cpu=M68000", "chip_ram=512K", "fast_ram=0K", "slow_ram=0K",
                     "chipset=Ocs", "video=Pal", "Kickstart 1.3", "program returned 0"):
        if expected not in log:
            raise AssertionError(f"Native player-frame proof missing {expected}: {log[-500:]}")
    report = {"updates_checked": COUNT, "native_bytes_compared_per_update": 256,
              "source_capture_offsets_checked": len(OBSERVED),
              "result": "joined player motion, animation, sprite RAM matches source captures",
              "executable_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
              "machine": "PAL A500 OCS 68000, 512K chip, 0 slow/fast, Kickstart 1.3"}
    (OUT / "player-frame-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
