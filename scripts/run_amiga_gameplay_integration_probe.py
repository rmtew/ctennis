"""Check live input/display in an explicit captured diagnostic phase."""

import hashlib
import json
import re
from pathlib import Path

from run_translated_prng_probe import ROOT, run


DISPLAY = ROOT / "build" / "amiga" / "gameplay-integration"


def main():
    from build_native_game import build
    config, executable = build(phase_start=True)
    copperline = Path(config["tools"]["copperline"])
    amiga_rom = Path(config["inputs"]["amiga_rom"])
    png = DISPLAY / "gameplay-integration.png"
    gif = DISPLAY / "gameplay-integration.gif"
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
    if (len(states) < 3 or [state[0] for state in states[:2]] != [50, 100]
            or not 58 <= states[0][1] <= 61
            or not 59 <= states[1][1] - states[0][1] <= 61):
        raise AssertionError(f"PAL/source update cadence is wrong: {states[:3]}")
    initial_x = (ROOT / "build/translation/live-initial-ram.bin").read_bytes()[0x4a]
    if states[-1][3] >= initial_x or not any(state[3] < initial_x for state in states):
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
