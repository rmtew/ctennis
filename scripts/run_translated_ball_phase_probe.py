"""Run generated ball dispatch against 200 captured serve/flight/point states."""

import configparser
import csv
import hashlib
import json
import sys
from pathlib import Path

from run_translated_prng_probe import ROOT, OUT, ASSEMBLER, run
from run_translated_player_frame_probe import ROM_SHA256, SERVE_CAPTURE, extract
from source_ball_update import ball_dispatch_11a0
from source_input_movement import input_update_0832, movement_and_sprites_13b9
from source_irq_tail import irq_tail_06b1
from source_player_update import player_state_0b29_0e54
from source_score_display import score_gate_094e, scoreboard_update_06eb


COUNT = 200


def main():
    config = configparser.ConfigParser(interpolation=None)
    if not config.read(ROOT / "config.local.ini", encoding="utf-8"):
        raise FileNotFoundError("config.local.ini")
    copperline = Path(config["tools"]["copperline"])
    amiga_rom = Path(config["inputs"]["amiga_rom"])
    cartridge = Path(config["inputs"]["cartridge"]).read_bytes()
    if hashlib.sha256(cartridge).hexdigest() != ROM_SHA256:
        raise AssertionError("Unexpected source cartridge")
    for path in (ASSEMBLER, copperline, amiga_rom, SERVE_CAPTURE):
        if not path.is_file():
            raise FileNotFoundError(path)
    OUT.mkdir(parents=True, exist_ok=True)
    source = OUT / "champion-raw.68k"
    run([sys.executable, "-W", "ignore", "scripts/z80268k.py", "--champion-source", "-n",
         "-i", "mot", "-o", "mot", "-c", str(source), "-I", str(OUT / "z80-support.i"),
         "--report-output", str(OUT / "report.json"),
         "build/analysis/champion-tennis-classified.asm"])
    generated = source.read_text(encoding="utf-8")
    ball = extract(generated, "ball_flight_update", "player_movement_and_sprites")
    arithmetic = extract(generated, "unsigned_multiply_byte", "triangular_root_step")
    sound = extract(generated, "assign_sound_stream_5", "wait_audio_channels_0_1")
    ldir = extract(generated, "ldir", "exx")
    (OUT / "ball-phase-routines.s").write_text(ball + arithmetic + sound + ldir,
                                                encoding="utf-8")
    memory = bytearray(65536)
    memory[:len(cartridge)] = cartridge
    (OUT / "ball-phase-memory.bin").write_bytes(memory)

    with SERVE_CAPTURE.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    if len(rows) != 201 or [int(row["frame"]) for row in rows] != list(range(1299, 1500)):
        raise AssertionError("Missing or reordered serve checkpoints")
    ram = bytearray(bytes.fromhex(rows[0]["ram"]))
    irq_tail_06b1(ram, rom=cartridge)
    vram = bytearray(16384)
    cases = bytearray()
    paths = {}
    for row in rows[1:]:
        frame = int(row["frame"])
        scoreboard_update_06eb(ram, vram)
        input_update_0832(ram, game_bits=0x10 if frame < 1450 else 0)
        score_gate_094e(ram)
        player_state_0b29_0e54(ram, upper=False, refresh_bit=0)
        player_state_0b29_0e54(ram, upper=True, refresh_bit=0)
        before = bytes(ram)
        path = ball_dispatch_11a0(ram)
        paths[path] = paths.get(path, 0) + 1
        after = bytes(ram)
        cases.extend(before)
        cases.extend(after)
        movement_and_sprites_13b9(ram)
        expected = bytes.fromhex(row["ram"])
        if ram != expected:
            differences = [offset for offset in range(256) if ram[offset] != expected[offset]]
            raise AssertionError(f"Source replay mismatch at {frame}: {differences[:12]}")
        irq_tail_06b1(ram, rom=cartridge)
    if len(cases) != COUNT * 512:
        raise AssertionError("Unexpected native case count")
    (OUT / "ball-phase-cases.bin").write_bytes(cases)
    executable = OUT / "translated-ball-phase-probe"
    run([str(ASSEMBLER), "-Fhunkexe", "-kick1hunks", "-m68000", "-o",
         str(executable), "amiga/translated_ball_phase_probe.s"])
    log = run([str(copperline), "--factory", "--model", "A500", "--chipset", "OCS",
               "--video", "PAL", "--cpu", "68000", "--chip", "512K", "--slow", "0",
               "--fast", "0", "--noaudio", "--run", str(executable),
               "--exit-on-return", str(amiga_rom)], timeout=120)
    (OUT / "ball-phase-copperline.log").write_text(log, encoding="utf-8")
    for expected in ("cpu=M68000", "chip_ram=512K", "fast_ram=0K", "slow_ram=0K",
                     "chipset=Ocs", "video=Pal", "Kickstart 1.3", "program returned 0"):
        if expected not in log:
            raise AssertionError(f"Native ball phase proof missing {expected}: {log[-500:]}")
    report = {"updates_checked": COUNT, "bytes_compared_per_update": 256,
              "source_paths": paths, "result": "generated ball phase matches source model",
              "executable_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
              "machine": "PAL A500 OCS 68000, 512K chip, 0 slow/fast, Kickstart 1.3"}
    (OUT / "ball-phase-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
