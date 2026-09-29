"""Replay a held-fire game through its award against the source cartridge."""

import argparse
import configparser
import csv
import hashlib
import json
import re
import sys
from pathlib import Path
from PIL import Image

from run_translated_prng_probe import ROOT, ASSEMBLER, run
from run_amiga_score_copper_probe import FIELDS, output_rectangle
from source_gameplay_slice import run_translated_frame_body
from source_irq_tail import irq_tail_06b1


OUT = ROOT / "build" / "amiga" / "long-game"
SOURCE = ROOT / "build" / "reference" / "source-long-game" / "run_a.tsv"
LIVE = ROOT / "build" / "amiga" / "gameplay-integration" / "gameplay-integration"
REPLAY_LIMIT = 1332  # second callback in source frame 2631 is outside the live game body
LOG = re.compile(
    r"DBG: LIVE F=([0-9A-F]{2}) U=([0-9A-F]{2}) I=([0-9A-F]{2}) "
    r"X=([0-9A-F]{2}) SX=([0-9A-F]{2}) E=([0-9A-F]{2}) B=([0-9A-F]{2}) "
    r"BY=([0-9A-F]{2}) BX=([0-9A-F]{2}) LP=([0-9A-F]{2}) UP=([0-9A-F]{2}) "
    r"SB=([0-9A-F]{2}) ST=([0-9A-F]{2}) UC=([0-9A-F]{4}) "
    r"PA=([0-9A-F]{2}) PB=([0-9A-F]{2}) GA=([0-9A-F]{2}) GB=([0-9A-F]{2}) "
    r"SF=([0-9A-F]{2}) M=([0-9A-F]{2}) DG=([0-9A-F]{2}) DL=([0-9A-F]{4}) "
    r"PH=([0-9A-F]{4}) PT=([0-9A-F]{4})"
)


def source_ball_slot(ram):
    slots = [slot for slot in (0, 4, 8)
             if ram[0x10 + 4 * slot] < 0xC0 and ram[0x13 + 4 * slot] & 15]
    return slots[0] if len(slots) == 1 else 0xFF


def make_refresh_fixture(source, cartridge):
    ram = bytearray(bytes.fromhex(source[0]["ram"]))
    irq_tail_06b1(ram, rom=cartridge)
    vram = bytearray(16384)
    signs = bytearray(REPLAY_LIMIT)
    constrained = []
    audio_checks = [(0, 0)]
    audio_events = [()]
    psg_hash = psg_total = 0
    for update in range(1, REPLAY_LIMIT + 1):
        expected = bytes.fromhex(source[update]["ram"])
        matches = []
        for sign in (0, 1):
            candidate_ram, candidate_vram = ram.copy(), vram.copy()
            checkpoint = []
            result = run_translated_frame_body(candidate_ram, candidate_vram, game_bits=0x10,
                                               lower_refresh_bit=0, upper_refresh_bit=sign,
                                               rom=cartridge,
                                               checkpoint=lambda state: checkpoint.append(bytes(state)))
            if checkpoint == [expected]:
                matches.append((sign, candidate_ram, candidate_vram, result))
        if not matches:
            raise AssertionError(f"Source model diverges at update {update}, frame {source[update]['frame']}")
        if len(matches) == 1:
            constrained.append({"update": update, "source_frame": int(source[update]["frame"]),
                                "refresh_bit": matches[0][0]})
        sign, ram, vram, result = matches[0]
        signs[update - 1] = sign
        for value in result.psg_bytes:
            psg_hash = (psg_hash * 33 + value) & 0xFFFF
            psg_total += 1
        audio_checks.append((psg_hash, psg_total))
        audio_events.append(result.psg_bytes)
    (OUT / "refresh-signs.bin").write_bytes(signs)
    (OUT / "refresh-signs.i").write_text(
        f'REFRESH_SIGN_COUNT equ {REPLAY_LIMIT}\n'
        'refresh_signs: incbin "build/amiga/long-game/refresh-signs.bin"\n', encoding="ascii")
    return constrained, audio_checks, audio_events


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ordinary", action="store_true",
                        help="also capture the native-timer live build without source refresh fixtures")
    args = parser.parse_args()
    if not SOURCE.is_file():
        run([sys.executable, "scripts/capture_source_long_game.py"], timeout=120)
    run([sys.executable, "scripts/run_amiga_gameplay_integration_probe.py"], timeout=120)
    config = configparser.ConfigParser(interpolation=None)
    if not config.read(ROOT / "config.local.ini", encoding="utf-8"):
        raise FileNotFoundError("config.local.ini")
    copperline = Path(config["tools"]["copperline"])
    amiga_rom = Path(config["inputs"]["amiga_rom"])
    OUT.mkdir(parents=True, exist_ok=True)
    with SOURCE.open(newline="", encoding="utf-8") as handle:
        source = list(csv.DictReader(handle, delimiter="\t"))
    constrained, audio_checks, audio_events = make_refresh_fixture(
        source, Path(config["inputs"]["cartridge"]).read_bytes())
    replay = OUT / "replay-game"
    run([str(ASSEMBLER), "-Fhunkexe", "-kick1hunks", "-m68000", "-DLONG_GAME_REPLAY=1",
         "-o", str(replay), "amiga/gameplay_integration_probe.s"])
    png = OUT / "after-game-award.png"
    gif = OUT / "game-award.gif"
    wav = OUT / "game-award.wav"
    log = run([str(copperline), "--factory", "--model", "A500", "--chipset", "OCS",
               "--video", "PAL", "--cpu", "68000", "--chip", "512K", "--slow", "0",
               "--fast", "0", "--noaudio", "--audio-wav", str(wav), "--run", str(replay),
               "--joy-after", "5", "fire", "30000", "2",
               "--screenshot-after", "28", str(png), "--gif-after", "24", str(gif),
               "--gif-seconds", "5", str(amiga_rom)], timeout=120)
    (OUT / "copperline.log").write_text(log, encoding="utf-8")
    records = [tuple(int(value, 16) for value in match) for match in LOG.findall(log)]
    native_audio_events = {int(update, 16): bytes.fromhex(data)
                           for update, count, data in re.findall(
                               r"DBG: PSG U=([0-9A-F]{4}) N=([0-9A-F]{2}) D=([0-9A-F]*)", log)}
    mismatches = []
    compared = []
    for record in records:
        (frame, low_update, input_bits, player_x, sprite_x, bridge_error, ball_slot,
         ball_y, ball_x, lower_phase, upper_phase, selected_b, selected_status,
         update, point_a, point_b, games_a, games_b, score_flags, mode, selected_game_b,
         deadline_misses,
         psg_hash, psg_total) = record
        if update & 255 != low_update or not 0 < update < len(source):
            mismatches.append({"update": update, "error": "update ordinal invalid"})
            continue
        if update > REPLAY_LIMIT:
            continue
        row = source[update]
        ram = bytes.fromhex(row["ram"])
        actual = (player_x, sprite_x, ball_slot, ball_y, ball_x, lower_phase,
                  upper_phase, point_a, point_b, games_a, games_b, score_flags, mode)
        expected = (ram[0x4A], ram[0x15], source_ball_slot(ram), ram[0x34], ram[0x35],
                    ram[0x49], ram[0x45], ram[0x3E], ram[0x3F], ram[0x40],
                    ram[0x41], ram[0x42], ram[0x3D])
        compared.append({"pal_frame_low": frame, "source_update": update,
                         "source_frame": int(row["frame"]),
                         "score": [point_a, point_b, games_a, games_b],
                         "display_b_status_game_b": [selected_b, selected_status, selected_game_b],
                         "deadline_misses": deadline_misses})
        if actual != expected or bridge_error:
            mismatches.append({"update": update, "source_frame": int(row["frame"]),
                               "native": actual, "source": expected,
                               "sprite_bridge_error": bridge_error})
        if (psg_hash, psg_total) != audio_checks[update]:
            mismatches.append({"update": update, "error": "ordered PSG event stream differs",
                               "native_hash_count": [psg_hash, psg_total],
                               "source_hash_count": audio_checks[update]})
    last_compared_update = compared[-1]["source_update"]
    expected_audio_events = {update: bytes(values)
                             for update, values in enumerate(audio_events[:last_compared_update + 1])
                             if values}
    observed_audio_events = {update: values for update, values in native_audio_events.items()
                             if update <= last_compared_update}
    if observed_audio_events != expected_audio_events:
        first = next((update for update in sorted(set(observed_audio_events) | set(expected_audio_events))
                      if observed_audio_events.get(update) != expected_audio_events.get(update)), None)
        mismatches.append({"update": first, "error": "ordered PSG bytes differ",
                           "native": list(observed_audio_events.get(first, b"")),
                           "source": list(expected_audio_events.get(first, b""))})
    transition_updates = (134, 469, 807, 1204)
    for update in transition_updates:
        match = next((item for item in compared if item["source_update"] == update), None)
        if match is None:
            mismatches.append({"update": update, "error": "score transition was not logged"})
            continue
        ram = bytes.fromhex(source[update]["ram"])
        expected_score = [ram[index] for index in (0x3E, 0x3F, 0x40, 0x41)]
        if match["score"] != expected_score:
            mismatches.append({"update": update, "error": "score transition differs"})
        drawn = next((item for item in compared if item["source_update"] == update + 1), None)
        if drawn is None or drawn["display_b_status_game_b"][0] != expected_score[1] or drawn["display_b_status_game_b"][2] != expected_score[3]:
            mismatches.append({"update": update + 1, "error": "score graphics did not change on next source update"})
    if not png.read_bytes().startswith(b"\x89PNG") or not gif.read_bytes().startswith(b"GIF8"):
        mismatches.append({"update": 1205, "error": "native game-award capture missing"})
        yellow_pixels = 0
    else:
        scored_image = Image.open(png).convert("RGB")
        tally = next(field for field in FIELDS if field.name == "games_b")
        yellow_pixels = sum(pixel == (221, 204, 85)
                            for pixel in scored_image.crop(output_rectangle(tally)).get_flattened_data())
        if yellow_pixels == 0:
            mismatches.append({"update": 1205, "error": "awarded game tally not visible"})
    report = {"ordinary_executable_sha256": hashlib.sha256(LIVE.read_bytes()).hexdigest(),
              "replay_executable_sha256": hashlib.sha256(replay.read_bytes()).hexdigest(),
              "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
              "replay_source_refresh_choices": constrained,
              "replay_source_update_limit": REPLAY_LIMIT,
              "score_transition_updates_checked": list(transition_updates),
              "ordered_psg_events_through_last_compared_update": audio_checks[compared[-1]["source_update"]][1],
              "source_native_psg_event_updates_compared": len(expected_audio_events),
              "visible_line_update_completions": compared[-1]["deadline_misses"],
              "visible_awarded_game_tally_pixels": yellow_pixels,
              "native_checkpoints": len(records), "compared": compared,
              "mismatches": mismatches[:20], "screenshot": str(png), "gif": str(gif),
              "wav": str(wav), "machine": "PAL A500 OCS 68000, 512K chip, 0 slow/fast, Kickstart 1.3"}
    if args.ordinary:
        ordinary_png = OUT / "ordinary-long.png"
        ordinary_log = run([str(copperline), "--factory", "--model", "A500", "--chipset", "OCS",
                            "--video", "PAL", "--cpu", "68000", "--chip", "512K", "--slow", "0",
                            "--fast", "0", "--noaudio", "--run", str(LIVE),
                            "--joy-after", "5", "fire", "35000", "2",
                            "--screenshot-after", "34", str(ordinary_png), str(amiga_rom)], timeout=120)
        (OUT / "ordinary-long.log").write_text(ordinary_log, encoding="utf-8")
        ordinary_scores = [tuple(int(value, 16) for value in match)
                           for match in re.findall(r"UC=([0-9A-F]{4}) PA=([0-9A-F]{2}) "
                                                   r"PB=([0-9A-F]{2}) GA=([0-9A-F]{2}) "
                                                   r"GB=([0-9A-F]{2})", ordinary_log)]
        if not ordinary_png.read_bytes().startswith(b"\x89PNG") or not ordinary_scores:
            raise AssertionError("Ordinary live long run was not captured")
        report["ordinary_run"] = {"screenshot": str(ordinary_png),
                                  "last_score_sample": ordinary_scores[-1],
                                  "awarded_game_seen": any(a or b for _, _, _, a, b in ordinary_scores),
                                  "visible_line_update_completions": int(re.findall(r"DL=([0-9A-F]{4})", ordinary_log)[-1], 16),
                                  "source_refresh_fixture": False}
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in
                      ("source_sha256", "replay_executable_sha256", "native_checkpoints",
                       "score_transition_updates_checked", "ordered_psg_events_through_last_compared_update",
                       "visible_awarded_game_tally_pixels", "visible_line_update_completions",
                       "mismatches", "screenshot", "gif", "wav")},
                     indent=2))
    if args.ordinary:
        print(json.dumps({"ordinary_run": report["ordinary_run"]}, indent=2))
    if mismatches:
        raise AssertionError(f"Native long game differs at update {mismatches[0]['update']}")


if __name__ == "__main__":
    main()
