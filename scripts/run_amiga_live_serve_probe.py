"""Capture a live native serve and compare its early states with source RAM."""

import configparser
import csv
import hashlib
import json
import math
import re
import struct
import sys
from pathlib import Path
from PIL import Image, ImageChops

from run_translated_prng_probe import ROOT, run
from run_amiga_score_copper_probe import FIELDS, output_rectangle
from source_irq_tail import irq_tail_06b1
from evidence import tracked_call, compile_manifest


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


def check_serve_tone(wav, source, cartridge):
    # The source sound stream's first serve note sets PSG channel 2 to $0D5.
    _, _, emitted = irq_tail_06b1(bytearray(source[1316][:256]), rom=cartridge)
    if emitted[:2] != (0xC5, 0x0D):
        raise AssertionError(f"Unexpected source serve PSG pitch: {emitted}")
    payload = wav.read_bytes()
    if payload[:4] != b"RIFF" or payload[8:12] != b"WAVE":
        raise AssertionError("Copperline did not produce a RIFF WAV")
    offset, fmt, samples = 12, None, None
    while offset + 8 <= len(payload):
        kind, size = struct.unpack_from("<4sI", payload, offset)
        offset += 8
        if kind == b"fmt ":
            fmt = payload[offset:offset + size]
        if kind == b"data":
            samples = offset
            break
        offset += size + (size & 1)
    if fmt is None or samples is None:
        raise AssertionError("WAV format or data chunk missing")
    tag, channels, rate, _, alignment, bits = struct.unpack_from("<HHIIHH", fmt)
    if tag not in (3, 0xFFFE) or channels != 2 or bits != 32 or alignment != 8:
        raise AssertionError(f"Unexpected Copperline WAV format: {(tag, channels, bits, alignment)}")
    expected_hz = 3_579_545 / (32 * 0x0D5)

    def strength(values, frequency):
        step = 2 * math.pi * frequency / rate
        cosine, sine = math.cos(step), math.sin(step)
        real = imag = s = 0.0
        c = 1.0
        for value in values:
            real += value * c
            imag += value * s
            c, s = c * cosine - s * sine, s * cosine + c * sine
        return math.hypot(real, imag)

    window = 8192
    best = (0.0, 0.0)
    for frame in range(5 * rate, 8 * rate, rate // 4):
        start = samples + frame * alignment
        if start + window * alignment > len(payload):
            break
        stereo = struct.unpack_from(f"<{window * 2}f", payload, start)
        left = stereo[::2]  # PSG channel 2 is on Paula channel 3 (left).
        fundamental = strength(left, expected_hz)
        adjacent = max(strength(left, 450), strength(left, 600))
        if fundamental > best[0]:
            best = (fundamental, adjacent)
    if best[0] < 10 or best[0] < 10 * best[1]:
        raise AssertionError(f"Serve tone absent or wrong pitch: expected {expected_hz:.1f} Hz, {best}")
    return {"source_psg_period": 0x0D5, "expected_hz": round(expected_hz, 2),
            "measured_tone_strength": round(best[0], 2),
            "adjacent_strength": round(best[1], 2), "wav_sample_rate": rate}


def _main():
    # Also builds the exact executable and checks the existing left-movement run.
    run([sys.executable, "scripts/run_amiga_gameplay_integration_probe.py"], timeout=120)
    config = configparser.ConfigParser(interpolation=None)
    if not config.read(ROOT / "config.local.ini", encoding="utf-8"):
        raise FileNotFoundError("config.local.ini")
    copperline = Path(config["tools"]["copperline"])
    amiga_rom = Path(config["inputs"]["amiga_rom"])
    # Retain this captured-phase subject when the ordinary build is restored.
    executable = DISPLAY / "serve-gameplay-integration"
    executable.write_bytes((DISPLAY / "gameplay-integration").read_bytes())
    listing = DISPLAY / "serve-native.lst"
    listing.write_bytes((DISPLAY / "native.lst").read_bytes())
    compile_manifest(executable, listing)
    png = DISPLAY / "serve.png"
    gif = DISPLAY / "serve.gif"
    wav = DISPLAY / "serve-audio.wav"
    scored_png = DISPLAY / "serve-scored.png"
    log = run([str(copperline), "--factory", "--model", "A500", "--chipset", "OCS",
               "--video", "PAL", "--cpu", "68000", "--chip", "512K", "--slow", "0",
               "--fast", "0", "--noaudio", "--audio-wav", str(wav), "--run", str(executable),
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
    tone_proof = check_serve_tone(wav, source, Path(config["inputs"]["cartridge"]).read_bytes())
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
        if field.name == "status":
            # The field helper adds a five-pixel guard that can catch the moving ball.
            box = (box[0] + 5, box[1], box[2] - 5, box[3])
        pixel_changes[field.name] = ImageChops.difference(earlier.crop(box), scored.crop(box)).getbbox() is not None
    if not pixel_changes["point_b"] or any(pixel_changes[name] for name in
                                            ("point_a", "games_a", "games_b", "status", "mode")):
        raise AssertionError(f"Scored point pixels differ from expected fields: {pixel_changes}")
    report = {"passed": True, "first_difference": None, "executable_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
              "source_state_matches": checked, "native_log_checkpoints": len(records),
              "screenshot": str(png), "gif": str(gif), "audio_wav": str(wav),
              "scored_screenshot": str(scored_png), "score_field_pixel_changes": pixel_changes,
              "serve_audio": tone_proof,
              "machine": "PAL A500 OCS 68000, 512K chip, 0 slow/fast, Kickstart 1.3"}
    (DISPLAY / "serve-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


def main():
    return tracked_call([DISPLAY/'serve-report.json'], 'live-serve', 'maintained-native',
                        'captured phase', 'scripts/run_amiga_live_serve_probe.py', 'serve', _main,
                        lambda path,report: [DISPLAY/'serve-gameplay-integration'])


if __name__ == "__main__":
    main()
