"""Assemble the maintained native game from explicitly prepared private assets."""

import configparser
import hashlib
import json
import sys
from pathlib import Path

from native_tools import ROOT, ASSEMBLER, run
OUT = ROOT / "build/translation"
from evidence import tracked_call, compile_manifest


DISPLAY = ROOT / "build" / "amiga" / "gameplay-integration"


def module_hashes():
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(p for p in (ROOT / "amiga/game").iterdir() if p.suffix in (".s", ".i"))}


def _build(phase_start=False):
    config = configparser.ConfigParser(interpolation=None)
    config.read(ROOT / 'config.local.ini', encoding='utf-8')
    if not ASSEMBLER.is_file():
        raise FileNotFoundError(ASSEMBLER)
    defines=[]
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
        defines=['-DLIVE_PHASE_START=1']
    DISPLAY.mkdir(parents=True, exist_ok=True)
    executable = DISPLAY / "gameplay-integration"
    run([str(ASSEMBLER), "-Fhunkexe", "-kick1hunks", "-m68000", *defines, "-L", str(DISPLAY / "native.lst"), "-o",
         str(executable), "amiga/gameplay_integration_probe.s"])
    compile_manifest(executable, DISPLAY / "native.lst")
    report = {"subject": "maintained-native", "entry_point": "game_source_tick",
              "startup": "captured diagnostic phase" if phase_start else "native title",
              "native_modules": module_hashes(),
              "executable_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
              "executable": str(executable)}
    (DISPLAY / "build-report.json").write_text(json.dumps(report, indent=2) + "\n")
    return config, executable


def build(phase_start=False):
    return tracked_call([DISPLAY / 'build-report.json'], 'phase-build' if phase_start else 'build', 'maintained-native',
                        'captured phase' if phase_start else 'ordinary title',
                        'scripts/build_native_game.py', None, lambda: _build(phase_start),
                        lambda path, report: [Path(report['executable'])])


if __name__ == "__main__":
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase-start", action="store_true", help="Explicit captured diagnostic phase; ordinary builds start at title")
    build(parser.parse_args().phase_start)
    print((DISPLAY / "build-report.json").read_text())
