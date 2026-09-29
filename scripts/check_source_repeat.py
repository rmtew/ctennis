"""Repeat the reset-to-title Gearsystem run and compare captured observations."""

import hashlib
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SMOKE = ROOT / "scripts" / "smoke_gearsystem.py"


def run_once(number, output, button, hold_frames, after_frames):
    command = [sys.executable, str(SMOKE)]
    if button:
        command += ["--button", button, "--hold-frames", str(hold_frames), "--after-frames", str(after_frames)]
    result = subprocess.run(
        command, capture_output=True, text=True, timeout=90,
        cwd=ROOT,
    )
    if result.returncode:
        raise RuntimeError(f"Run {number} failed: {result.stderr.strip()}")
    data = json.loads(result.stdout)
    screenshot = ROOT / "build" / "smoke" / (f"gearsystem-after-{button}.png" if button else "gearsystem-120.png")
    image = output / f"run-{number}.png"
    shutil.copyfile(screenshot, image)
    observation = {
        "cartridge_sha256": data["cartridge_sha256"],
        "emulator_version": data["server"]["version"],
        "media_is_sg1000": data["media"]["is_sg1000"],
        "frames_executed": data["stepped"]["frames_executed"],
        "ram_first_32_bytes": json.loads(data["ram_preview"][0]["text"])["data"],
        "after_ram_sha256": data["after_ram_sha256"],
        "screenshot_sha256": hashlib.sha256(image.read_bytes()).hexdigest(),
    }
    (output / f"run-{number}.json").write_text(json.dumps(observation, indent=2) + "\n", encoding="utf-8")
    return observation


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--button", choices=("start", "1", "2"))
    parser.add_argument("--hold-frames", type=int, default=300)
    parser.add_argument("--after-frames", type=int, default=30)
    args = parser.parse_args()
    output = ROOT / "build" / "reference" / (f"button-{args.button}" if args.button else "no-input")
    output.mkdir(parents=True, exist_ok=True)
    first = run_once(1, output, args.button, args.hold_frames, args.after_frames)
    second = run_once(2, output, args.button, args.hold_frames, args.after_frames)
    equal = first == second
    report = {"scenario": f"reset; 120 frames; button {args.button or 'none'} held {args.hold_frames if args.button else 0} frames; {args.after_frames if args.button else 0} more frames", "matches": equal, "observations": [first, second]}
    (output / "comparison.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not equal:
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Source repeat check failed: {error}", file=sys.stderr)
        sys.exit(1)
