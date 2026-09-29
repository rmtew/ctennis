"""Explicitly record and freeze independent MAME regression oracles."""
import argparse
import configparser
import hashlib
import json
import os
import subprocess
import zipfile
from pathlib import Path
from run_translated_prng_probe import ROOT
from run_translated_player_frame_probe import ROM_SHA256
from round_reference import build_fixture, validate_fixture


def capture_round(config):
    out = ROOT / 'build/tests/round-reference-capture'
    out.mkdir(parents=True, exist_ok=True)
    mame = ROOT / '.tools/mame-0.289/mame.exe'
    captures = []
    for name in ('a', 'b'):
        path = out / (name + '.tsv')
        env = os.environ.copy()
        env['CT_TEST_CAPTURE'] = str(path)
        command = [str(mame), 'sc3000', '-noreadconfig', '-hashpath', '.tools/mame-0.289/hash',
                   '-rompath', 'build/mame/roms', '-cart', 'champtns', '-video', 'none', '-sound', 'none',
                   '-debug', '-debugger', 'none', '-skip_gameinfo', '-nothrottle', '-seconds_to_run', '51',
                   '-autoboot_script', 'scripts/capture_round_reference.lua']
        result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, timeout=120)
        (out / (name + '.log')).write_text(result.stdout + result.stderr, encoding='utf-8')
        if result.returncode or 'ROUND_REFERENCE_COMPLETE' not in result.stdout:
            raise RuntimeError(result.stdout + result.stderr)
        captures.append(path.read_bytes())
    if captures[0] != captures[1]:
        raise AssertionError('Round source captures differ; reference not replaced')
    fixture = build_fixture(captures[0], {
        'rom_sha256': ROM_SHA256, 'emulator': 'MAME 0.289 sc3000',
        'emulator_sha256': hashlib.sha256(mame.read_bytes()).hexdigest(),
        'capture_sha256': hashlib.sha256(captures[0]).hexdigest(), 'repeat_identical': True,
        'capture_script_sha256': hashlib.sha256((ROOT / 'scripts/capture_round_reference.lua').read_bytes()).hexdigest(),
        'parser_sha256': hashlib.sha256((ROOT / 'scripts/round_reference.py').read_bytes()).hexdigest(),
        'case_sha256': hashlib.sha256((ROOT / 'tests/cases/round-transition.json').read_bytes()).hexdigest(),
        'machine': 'SC-3000 NTSC, SK-1100 keyboard, cartridge champtns',
        'setup_inputs': [{'frame': 120, 'control': 'SK1100 PA3 key 0x10', 'pressed': True},
                         {'frame': 420, 'control': 'SK1100 PA3 key 0x10', 'pressed': False},
                         {'frame': 1300, 'control': 'port-1 fire', 'pressed': True}],
        'capture_bounds': {'begin_frame': 1298, 'last_begin_frame': 3000},
        'source_command': command,
    })
    target = ROOT / 'tests/reference/round-transition.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(fixture, indent=2) + '\n', encoding='utf-8')
    report = validate_fixture(fixture)
    report.update(reference_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                  capture_sha256=fixture['capture_sha256'], repeat_identical=True)
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=('serve', 'round-transition'), default='serve')
    parser.add_argument('--verify-only', action='store_true', help='Validate an existing round-transition reference without MAME')
    args = parser.parse_args()
    if args.verify_only:
        if args.case != 'round-transition':
            parser.error('--verify-only currently applies to round-transition')
        fixture = json.loads((ROOT / 'tests/reference/round-transition.json').read_text())
        print(json.dumps(validate_fixture(fixture), indent=2))
        return
    config = configparser.ConfigParser(interpolation=None)
    config.read(ROOT / "config.local.ini", encoding="utf-8")
    cartridge = Path(config['inputs']['cartridge']).read_bytes()
    if hashlib.sha256(cartridge).hexdigest() != ROM_SHA256:
        raise ValueError('Unexpected cartridge')
    with zipfile.ZipFile(ROOT / 'build/mame/roms/sg1000/champtns.zip') as archive:
        if len(archive.namelist()) != 1 or archive.read(archive.namelist()[0]) != cartridge:
            raise ValueError('MAME archive differs from the supplied cartridge')
    if args.case == 'round-transition':
        capture_round(config)
        return
    out = ROOT / 'build/tests/reference-capture'
    out.mkdir(parents=True, exist_ok=True)
    captures = []
    for name in ('a', 'b'):
        path = out / (name + '.tsv')
        env = os.environ.copy()
        env['CT_TEST_CAPTURE'] = str(path)
        command = [str(ROOT / '.tools/mame-0.289/mame.exe'), 'sc3000', '-noreadconfig',
                   '-hashpath', '.tools/mame-0.289/hash', '-rompath', 'build/mame/roms',
                   '-cart', 'champtns', '-video', 'none', '-sound', 'none', '-skip_gameinfo',
                   '-nothrottle', '-seconds_to_run', '26', '-autoboot_script', 'scripts/capture_test_reference.lua']
        result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, timeout=120)
        (out / (name + '.log')).write_text(result.stdout + result.stderr, encoding='utf-8')
        if result.returncode or 'TEST_REFERENCE_COMPLETE' not in result.stdout:
            raise RuntimeError(result.stdout + result.stderr)
        captures.append(path.read_bytes())
    if captures[0] != captures[1]:
        raise AssertionError('Source captures differ')
    states, tails, events = {}, {}, {}
    for line in captures[0].decode().splitlines():
        kind, frame, value = line.split('\t')
        frame = int(frame)
        if kind == 'S':
            if frame in states:
                raise AssertionError('Duplicate source callback')
            states[frame] = value
        elif kind == 'T':
            tails[frame] = value
        else:
            events.setdefault(frame, []).append(int(value, 16))
    if sorted(states) != list(range(1299, 1500)) or sorted(tails) != sorted(states) or not events:
        raise AssertionError('Incomplete RAM or PSG capture')
    fixture = {'rom_sha256': ROM_SHA256, 'emulator': 'MAME 0.289 sc3000',
               'capture_sha256': hashlib.sha256(captures[0]).hexdigest(), 'repeat_identical': True,
               'initial_pre_tail': states[1299], 'initial_psg': events.get(1299, []),
               'initial_post_tail': tails[1299],
               'updates': [{'frame': frame, 'ram': states[frame], 'post_tail_ram': tails[frame], 'psg': events.get(frame, [])}
                           for frame in range(1300, 1500)]}
    target = ROOT / 'tests/reference/serve.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(fixture, indent=2) + '\n', encoding='utf-8')
    print(f'Frozen 200 source callbacks in {target}; two captures identical')


if __name__ == '__main__':
    main()
