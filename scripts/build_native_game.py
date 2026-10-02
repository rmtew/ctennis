"""Assemble the maintained native game from explicitly prepared private assets."""

import configparser
import hashlib
import json
import sys
import subprocess
from pathlib import Path

from native_tools import ROOT, ASSEMBLER, run
OUT = ROOT / "build/translation"
from evidence import tracked_call, compile_manifest


DISPLAY = ROOT / "build" / "amiga" / "gameplay-integration"


def module_hashes():
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(p for p in (ROOT / "amiga/game").iterdir() if p.suffix in (".s", ".i"))}


def _build(phase_start=False, flavor="enhanced"):
    if flavor not in ("original", "enhanced"):
        raise ValueError("Unknown interface flavor")
    display = ROOT / "build/amiga/interfaces" / flavor
    config = configparser.ConfigParser(interpolation=None)
    config.read(ROOT / 'config.local.ini', encoding='utf-8')
    if not ASSEMBLER.is_file():
        raise FileNotFoundError(ASSEMBLER)
    defines=["-DENHANCED_INTERFACE=1"] if flavor == "enhanced" else []
    if flavor == "enhanced":
        revision = run(["git", "rev-parse", "--short=7", "HEAD"]).strip()
        dirty = subprocess.run(["git", "diff", "--quiet", "HEAD"], cwd=ROOT).returncode != 0
        version = ROOT / 'build/amiga/title/enhanced/version.bin'
        version.parent.mkdir(parents=True, exist_ok=True)
        version.write_bytes((f"BUILD {revision}" + (" + LOCAL" if dirty else "")).encode('ascii') + b"\0")
    if phase_start:
        cartridge = Path(config["inputs"]["cartridge"]).read_bytes()
        # Explicit diagnostic phase, never the ordinary application's startup.
        import csv
        from source_irq_tail import irq_tail_06b1
        with (ROOT/'build/reference/source-timing/run_a.tsv').open() as handle:
            initial=next(bytes.fromhex(row['ram'])[:256] for row in csv.DictReader(handle,delimiter='\t')
                         if row['event']=='checkpoint' and int(row['frame'])==1299)
        ram=bytearray(initial);irq_tail_06b1(ram,rom=cartridge)
        (OUT/'live-initial-ram.bin').write_bytes(ram)
        defines += ['-DLIVE_PHASE_START=1','-DCOPPERLINE_LOG=1']
    display.mkdir(parents=True, exist_ok=True)
    executable = display / f"ctennis-{flavor}"
    run([str(ASSEMBLER), "-Fhunkexe", "-kick1hunks", "-m68000", *defines, "-L", str(display / "native.lst"), "-o",
         str(executable), "amiga/gameplay_integration_probe.s"])
    compile_manifest(executable, display / "native.lst")
    report = {"subject": "maintained-native", "interface_flavor": flavor, "entry_point": "game_source_tick",
              "startup": "captured diagnostic phase" if phase_start else "native title",
              "native_modules": module_hashes(),
              "executable_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
              "executable": str(executable)}
    (display / "build-report.json").write_text(json.dumps(report, indent=2) + "\n")
    return config, executable


def build(phase_start=False, flavor="enhanced"):
    display = ROOT / "build/amiga/interfaces" / flavor
    return tracked_call([display / 'build-report.json'], 'phase-build' if phase_start else 'build', 'maintained-native',
                        'captured phase' if phase_start else 'ordinary title',
                        'scripts/build_native_game.py', None, lambda: _build(phase_start, flavor),
                        lambda path, report: [Path(report['executable'])])


if __name__ == "__main__":
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase-start", action="store_true", help="Explicit captured diagnostic phase; ordinary builds start at title")
    parser.add_argument("--interface", choices=("original", "enhanced"), default="enhanced")
    args = parser.parse_args()
    build(args.phase_start, args.interface)
    print((ROOT / "build/amiga/interfaces" / args.interface / "build-report.json").read_text())
