"""Assemble the maintained native game from explicitly prepared private assets."""

import hashlib
import json
import sys
import subprocess
from pathlib import Path

from native_tools import ROOT, ASSEMBLER, run, verify_build_tools
from native_evidence import tracked_call, compile_manifest


DISPLAY = ROOT / "build" / "amiga" / "gameplay-integration"


def module_hashes():
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(p for p in (ROOT / "amiga/game").iterdir() if p.suffix in (".s", ".i"))}


def _build(flavor="enhanced"):
    if flavor != "enhanced":
        raise ValueError("Only the maintained enhanced interface is supported")
    display = ROOT / "build/amiga/interfaces" / flavor
    verify_build_tools()
    defines=["-DENHANCED_INTERFACE=1"] if flavor == "enhanced" else []
    from native_assets import prepare
    prepare()
    if flavor == "enhanced":
        revision = run(["git", "rev-parse", "--short=7", "HEAD"]).strip()
        dirty = subprocess.run(["git", "diff", "--quiet", "HEAD"], cwd=ROOT).returncode != 0
        version = ROOT / 'build/native/version.bin'
        version.parent.mkdir(parents=True, exist_ok=True)
        version.write_bytes((f"BUILD {revision}" + (" + LOCAL" if dirty else "")).encode('ascii') + b"\0")
    from native_ui_pages import prepare as prepare_ui_pages
    prepare_ui_pages(version.read_bytes())
    display.mkdir(parents=True, exist_ok=True)
    executable = display / f"ctennis-{flavor}"
    run([str(ASSEMBLER), "-Fhunkexe", "-kick1hunks", "-m68000", *defines, "-L", str(display / "native.lst"), "-o",
         str(executable), "amiga/main.s"])
    compile_manifest(executable, display / "native.lst")
    report = {"subject": "maintained-native", "interface_flavor": flavor, "entry_point": "game_tick_dispatch",
              "startup": "native title",
              "native_modules": module_hashes(),
              "executable_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
              "executable": str(executable)}
    (display / "build-report.json").write_text(json.dumps(report, indent=2) + "\n")
    return None, executable


def build(flavor="enhanced"):
    display = ROOT / "build/amiga/interfaces" / flavor
    return tracked_call([display / 'build-report.json'], 'build', 'maintained-native',
                        'ordinary title',
                        'scripts/build_native_game.py', None, lambda: _build(flavor),
                        lambda path, report: [Path(report['executable'])])


if __name__ == "__main__":
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interface", choices=("enhanced",), default="enhanced")
    args = parser.parse_args()
    build(args.interface)
    print((ROOT / "build/amiga/interfaces" / args.interface / "build-report.json").read_text())
