"""Build the maintained native game; generated translation is temporary adapter debt."""

import configparser
import hashlib
import json
import sys
from pathlib import Path

from run_translated_prng_probe import ROOT, OUT, ASSEMBLER, run
from run_translated_player_frame_probe import prepare_gameplay


DISPLAY = ROOT / "build" / "amiga" / "gameplay-integration"


def module_hashes():
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((ROOT / "amiga/game").glob("*.s"))}


def build(phase_start=False):
    from run_amiga_score_copper_probe import make_banks, make_copper_and_patch_tables
    config = configparser.ConfigParser(interpolation=None)
    if not config.read(ROOT / "config.local.ini", encoding="utf-8"):
        raise FileNotFoundError("config.local.ini")
    copperline = Path(config["tools"]["copperline"])
    amiga_rom = Path(config["inputs"]["amiga_rom"])
    cartridge = Path(config["inputs"]["cartridge"]).read_bytes()
    for path in (ASSEMBLER, copperline, amiga_rom):
        if not path.is_file():
            raise FileNotFoundError(path)
    run([sys.executable, "scripts/roundtrip_rom.py"])
    prepare_gameplay()
    run([sys.executable, "scripts/generate_amiga_sprite_probe.py"], timeout=120)
    score_vram = (ROOT / "build" / "reference" / "source-timing" / "sprite-f1310.vram").read_bytes()
    score_output = ROOT / "build" / "amiga" / "score-copper-probe"
    score_output.mkdir(parents=True, exist_ok=True)
    make_banks(score_vram)
    make_copper_and_patch_tables()
    from generate_native_title import generate
    generate()
    defines=[]
    if phase_start:
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
    run([str(ASSEMBLER), "-Fhunkexe", "-kick1hunks", "-m68000", *defines, "-o",
         str(executable), "amiga/gameplay_integration_probe.s"])
    report = {"subject": "maintained-native", "entry_point": "game_source_tick",
              "startup": "captured diagnostic phase" if phase_start else "native title",
              "native_modules": module_hashes(),
              "executable_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
              "executable": str(executable)}
    (DISPLAY / "build-report.json").write_text(json.dumps(report, indent=2) + "\n")
    return config, executable


if __name__ == "__main__":
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase-start", action="store_true", help="Explicit captured diagnostic phase; ordinary builds start at title")
    build(parser.parse_args().phase_start)
    print((DISPLAY / "build-report.json").read_text())
