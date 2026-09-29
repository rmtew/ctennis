"""Replay generated movement, animation and sprites at captured update states."""

import configparser
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

from run_translated_prng_probe import ROOT, OUT, ASSEMBLER, run
from source_ball_update import ball_dispatch_11a0
from source_input_movement import input_update_0832, movement_and_sprites_13b9
from source_player_update import player_state_0b29_0e54
from source_score_display import score_gate_094e, scoreboard_update_06eb
from source_irq_tail import irq_tail_06b1


ROM_SHA256 = "19bb6647f14ef50f976e8d0a06d389f06b2e700d54a54fb1734d3140f9745ad1"
CAPTURE = ROOT / "build" / "reference" / "source-timing" / "run_a.tsv"
SERVE_CAPTURE = ROOT / "build" / "reference" / "source-serve" / "run_a.tsv"
COUNT = 240


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
    for path in (ASSEMBLER, copperline, amiga_rom, CAPTURE, SERVE_CAPTURE):
        if not path.is_file():
            raise FileNotFoundError(path)
    OUT.mkdir(parents=True, exist_ok=True)
    source = OUT / "champion-raw.68k"
    run([sys.executable, "-W", "ignore", "scripts/z80268k.py", "--champion-source", "-n",
         "-i", "mot", "-o", "mot", "-c", str(source), "-I", str(OUT / "z80-support.i"),
         "--report-output", str(OUT / "report.json"),
         "build/analysis/champion-tennis-classified.asm"])
    generated = source.read_text(encoding="utf-8")
    tail_match = re.search(r"(?ms)^irq_counter_update:\n(.*?)^\s*bne\s+\.lb_13\s+; \[call z,audio_tick_three_channels\]", generated)
    if not tail_match or "ERROR" in tail_match.group(1):
        raise AssertionError("Generated IRQ counter prefix is unavailable")
    irq_prefix = "irq_counter_prefix:\n" + tail_match.group(1) + "\trts\n"
    scoreboard = extract(generated, "scoreboard_update", "input_update")
    for label in ("scoreboard_status_tiles", "mode_tile_strings", "game_tally_tiles", "point_value_tiles"):
        scoreboard, count = re.subn(rf"(?m)^{label}:\n(?:dc\.b [^\n]*\n)+", "", scoreboard)
        if count != 1:
            raise AssertionError(f"Expected one {label} table")
    input_selection = extract(generated, "input_update", "read_game_input")
    score = extract(generated, "score_gate", "lower_player_state")
    motion = extract(generated, "lower_player_motion_update", "animate_lower_player")
    for label in ("lower_movement_bounds", "upper_movement_bounds"):
        motion, count = re.subn(rf"(?m)^{label}:\ndc\.b [^\n]*\n", "", motion)
        if count != 1:
            raise AssertionError(f"Expected one {label} table")
    animation = extract(generated, "animate_lower_player", "unsigned_multiply_byte", "animation_records")
    sprites = extract(generated, "build_player_sprites", "ball_flight_update", "player_sprite_descriptors")
    ball = extract(generated, "ball_flight_update", "player_movement_and_sprites")
    ball_slots = extract(generated, "player_movement_and_sprites", "lower_player_motion_update")
    arithmetic = extract(generated, "unsigned_multiply_byte", "triangular_root_step")
    player_state = extract(generated, "lower_player_state", "build_player_sprites")
    for label in ("lower_serve_vector", "lower_trajectory_records",
                  "lower_trajectory_record_two", "lower_trajectory_record_three",
                  "upper_serve_vector", "upper_trajectory_records",
                  "upper_trajectory_record_two"):
        player_state, count = re.subn(
            rf"(?m)^{label}:\n(?:;[^\n]*\n)?(?:dc\.b [^\n]*\n)+", "", player_state)
        if count != 1:
            raise AssertionError(f"Expected one {label} table")
    helpers = extract(generated, "triangular_root_step", "initialize_audio_records")
    sound = extract(generated, "assign_sound_stream_4", "wait_audio_channels_0_1")
    ldir = extract(generated, "ldir", "exx")
    routines = (irq_prefix + scoreboard + input_selection + score + player_state + ball + ball_slots + motion + animation +
                sprites + arithmetic + helpers + sound + ldir)
    (OUT / "player-frame-routines.s").write_text(routines, encoding="utf-8")
    defined = set(re.findall(r"(?m)^([A-Za-z_]\w*):", routines))
    defined.update(("read_game_input", "sample_second_input_group",
                    "upload_sprite_attributes", "copy_cpu_bytes_to_vram_b_count", "l_0008"))
    symbol_lines = []
    for name, value in re.findall(r"(?m)^([A-Za-z_]\w*): equ 0x([0-9a-fA-F]+)$",
                                  (ROOT / "analysis" / "rom-symbols.def").read_text(encoding="utf-8")):
        if name not in defined and re.search(rf"\b{re.escape(name)}\b", routines):
            symbol_lines.append(f"{name} equ ${value}\n")
    (OUT / "player-frame-symbols.i").write_text("".join(symbol_lines), encoding="utf-8")
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
    score_paths = {}
    two_group_input_updates = 0
    total_vram_writes = 0
    updates_with_vram_writes = 0
    counter_offsets = (*range(0x6B, 0x72), 0x83)
    for frame in range(1300, 1340):
        before = bytes(ram)
        writes = scoreboard_update_06eb(ram, vram)
        game_bits = 4 if frame < 1320 else 0
        two_group_input_updates += bool(ram[0x3D] & 0x80 and not ram[0x3D] & 0x04)
        input_update_0832(ram, game_bits=game_bits)
        score = score_gate_094e(ram)
        score_paths[score.name] = score_paths.get(score.name, 0) + 1
        player_state_0b29_0e54(ram, upper=False, refresh_bit=0)
        player_state_0b29_0e54(ram, upper=True, refresh_bit=0)
        ball_dispatch_11a0(ram)
        movement_and_sprites_13b9(ram)
        expected = checkpoints[frame][:256]
        differences = [offset for offset in range(256) if ram[offset] != expected[offset]]
        if differences:
            raise AssertionError(f"Source-model/capture mismatch at frame {frame}: {differences[:12]}")
        cases.extend((game_bits, 0))
        cases.extend(before)
        cases.extend(expected)
        if len(writes) > 64:
            raise AssertionError("Scoreboard write log exceeds native buffer")
        cases.append(len(writes))
        for address, value in writes:
            cases.extend((address >> 8, address & 255, value))
        total_vram_writes += len(writes)
        updates_with_vram_writes += bool(writes)
        irq_tail_06b1(ram, rom=cartridge)
        captured_after = bytearray(expected)
        captured_after[0x6B] = (captured_after[0x6B] + 1) & 255
        if ram != captured_after:
            differences = [offset for offset in range(256) if ram[offset] != captured_after[offset]]
            raise AssertionError(f"Full source replay mismatch at frame {frame}: {differences[:12]}")
        # The audio tick immediately reloads C083; compare its pre-audio decrement.
        cases.extend(ram[offset] for offset in counter_offsets[:-1])
        cases.append((expected[0x83] - 1) & 255)
    with SERVE_CAPTURE.open(newline="", encoding="utf-8") as handle:
        serve_rows = list(csv.DictReader(handle, delimiter="\t"))
    if len(serve_rows) != 201 or [int(row["frame"]) for row in serve_rows] != list(range(1299, 1500)):
        raise AssertionError("Missing or reordered source serve checkpoints")
    ram = bytearray(bytes.fromhex(serve_rows[0]["ram"]))
    irq_tail_06b1(ram, rom=cartridge)
    vram = bytearray(16384)
    for row in serve_rows[1:]:
        frame = int(row["frame"])
        before = bytes(ram)
        writes = scoreboard_update_06eb(ram, vram)
        game_bits = 0x10 if frame < 1450 else 0
        two_group_input_updates += bool(ram[0x3D] & 0x80 and not ram[0x3D] & 0x04)
        input_update_0832(ram, game_bits=game_bits)
        score = score_gate_094e(ram)
        score_paths[score.name] = score_paths.get(score.name, 0) + 1
        player_state_0b29_0e54(ram, upper=False, refresh_bit=0)
        player_state_0b29_0e54(ram, upper=True, refresh_bit=0)
        ball_dispatch_11a0(ram)
        movement_and_sprites_13b9(ram)
        expected = bytes.fromhex(row["ram"])
        differences = [offset for offset in range(256) if ram[offset] != expected[offset]]
        if differences:
            raise AssertionError(f"Serve source-model/capture mismatch at frame {frame}: {differences[:12]}")
        cases.extend((game_bits, 0))
        cases.extend(before)
        cases.extend(expected)
        if len(writes) > 64:
            raise AssertionError("Scoreboard write log exceeds native buffer")
        cases.append(len(writes))
        for address, value in writes:
            cases.extend((address >> 8, address & 255, value))
        total_vram_writes += len(writes)
        updates_with_vram_writes += bool(writes)
        irq_tail_06b1(ram, rom=cartridge)
        cases.extend(ram[offset] for offset in counter_offsets[:-1])
        cases.append((expected[0x83] - 1) & 255)
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
    report = {"movement_updates_checked": 40, "serve_updates_checked": 200,
              "native_bytes_compared_per_update": 256,
              "score_paths": score_paths,
              "two_group_input_updates": two_group_input_updates,
              "scoreboard_vram_writes_compared": total_vram_writes,
              "native_irq_counter_bytes_compared": COUNT * len(counter_offsets),
              "updates_with_scoreboard_vram_writes": updates_with_vram_writes,
              "result": "joined scoreboard-to-sprite RAM, scoreboard VRAM writes, and IRQ counter prefix match source captures",
              "executable_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
              "machine": "PAL A500 OCS 68000, 512K chip, 0 slow/fast, Kickstart 1.3"}
    (OUT / "player-frame-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
