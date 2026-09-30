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
from round_reference import build_fixture, build_focused_fixture, validate_fixture, FOCUSED_CASES, MOVEMENT_CASES


def capture_round(config, case_name='round-transition'):
    full_match = case_name in ('one-player-match', 'two-player-match')
    focused = case_name in FOCUSED_CASES
    case = json.loads((ROOT / f'tests/cases/{case_name}.json').read_text())
    two_player = case.get('selection') == 'two' or case_name == 'two-player-match'
    policy_enabled = full_match or focused
    last_frame = case.get('last_begin_frame', 3000)
    out = ROOT / f'build/tests/{case_name}-capture'
    out.mkdir(parents=True, exist_ok=True)
    mame = ROOT / '.tools/mame-0.289/mame.exe'
    captures = []
    for name in ('a', 'b'):
        path = out / (name + '.tsv')
        env = os.environ.copy()
        env['CT_TEST_CAPTURE'] = str(path)
        env['CT_TEST_LAST_FRAME'] = str(last_frame)
        env['CT_TEST_SELECT'] = 'two' if two_player else 'one'
        env['CT_TEST_FIRE'] = '0' if two_player else '1'
        env['CT_TEST_CONTACT_MARKERS'] = '1' if two_player else '0'
        if policy_enabled:
            env['CT_TEST_POLICY'] = case['capture_policy']
        else:
            env.pop('CT_TEST_POLICY', None)
        command = [str(mame), 'sc3000', '-noreadconfig', '-hashpath', '.tools/mame-0.289/hash',
                   '-rompath', 'build/mame/roms', '-cart', 'champtns', '-video', 'none', '-sound', 'none',
                   '-debug', '-debugger', 'none', '-skip_gameinfo', '-nothrottle', '-seconds_to_run', str(last_frame // 60 + 2),
                   '-autoboot_script', 'scripts/capture_round_reference.lua']
        result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, timeout=120)
        (out / (name + '.log')).write_text(result.stdout + result.stderr, encoding='utf-8')
        if result.returncode or 'ROUND_REFERENCE_COMPLETE' not in result.stdout or 'LUA ERROR' in result.stdout + result.stderr:
            raise RuntimeError(result.stdout + result.stderr)
        captures.append(path.read_bytes())
    if captures[0] != captures[1]:
        raise AssertionError('Round source captures differ; reference not replaced')
    builder = build_focused_fixture if focused else build_fixture
    fixture = builder(captures[0], {
        'rom_sha256': ROM_SHA256, 'emulator': 'MAME 0.289 sc3000',
        'emulator_sha256': hashlib.sha256(mame.read_bytes()).hexdigest(),
        'capture_sha256': hashlib.sha256(captures[0]).hexdigest(), 'repeat_identical': True,
        'capture_script_sha256': hashlib.sha256((ROOT / 'scripts/capture_round_reference.lua').read_bytes()).hexdigest(),
        'parser_sha256': hashlib.sha256((ROOT / 'scripts/round_reference.py').read_bytes()).hexdigest(),
        'case_sha256': hashlib.sha256((ROOT / f'tests/cases/{case_name}.json').read_bytes()).hexdigest(),
        'policy_sha256': hashlib.sha256((ROOT / case['capture_policy']).read_bytes()).hexdigest() if policy_enabled else None,
        'control_schedule': case.get('control_schedule'),
        'selection': 'two' if two_player else 'one',
        'machine': 'SC-3000 NTSC, SK-1100 keyboard, cartridge champtns',
        'setup_inputs': [{'frame': 120, 'control': 'SK1100 PB5 key 0x08' if two_player else 'SK1100 PA3 key 0x10', 'pressed': True},
                         {'frame': 420, 'control': 'SK1100 PB5 key 0x08' if two_player else 'SK1100 PA3 key 0x10', 'pressed': False},
                         *([] if two_player else [{'frame': 1300, 'control': 'port-1 fire', 'pressed': True}])],
        'capture_bounds': {'begin_frame': 1298, 'last_begin_frame': last_frame},
        'source_command': command,
    }, **({} if focused else {'complete_match': full_match}))
    if full_match and not two_player:
        prefix = json.loads((ROOT / 'tests/reference/round-transition.json').read_text())
        for index, (actual, expected) in enumerate(zip(fixture['updates'], prefix['updates']), 1):
            for field in ('entry_ram', 'ram', 'post_tail_ram', 'psg', 'inputs', 'refresh_reads', 'before_events'):
                if actual[field] != expected[field]:
                    raise ValueError(f'Full match differs from frozen prefix at update {index}: {field}')
        if len(fixture['updates']) < len(prefix['updates']):
            raise ValueError('Full match shorter than existing prefix')
    if policy_enabled:
        controls = [{'frame': event['frame'], 'control': event['control'], 'value': event['value']}
                    for event in fixture['timeline'] if event['kind'] == 'control']
        if controls != [event for event in case['control_schedule'] if event['frame'] >= 1298]:
            raise ValueError('Observed controls differ from frozen schedule')
    if case_name in MOVEMENT_CASES:
        from movement_reference import validate_movement
        validate_movement(fixture, case)
    if case_name == 'two-player-rally':
        from rally_reference import validate_rally
        validate_rally(fixture, case)
    target = ROOT / f'tests/reference/{case_name}.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(fixture, indent=2) + '\n', encoding='utf-8')
    report = validate_fixture(fixture)
    if case_name in MOVEMENT_CASES:
        report.update(validate_movement(fixture, case))
    if case_name == 'two-player-rally':
        report.update(validate_rally(fixture, case))
    report.update(reference_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                  capture_sha256=fixture['capture_sha256'], repeat_identical=True)
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=('serve', 'round-transition', 'one-player-match', 'two-player-match') + FOCUSED_CASES, default='serve')
    parser.add_argument('--verify-only', action='store_true', help='Validate an existing round-transition reference without MAME')
    args = parser.parse_args()
    if args.verify_only:
        if args.case == 'serve':
            parser.error('--verify-only applies to callback references')
        fixture = json.loads((ROOT / f'tests/reference/{args.case}.json').read_text())
        report = validate_fixture(fixture)
        if args.case in MOVEMENT_CASES:
            from movement_reference import validate_movement
            case = json.loads((ROOT / f'tests/cases/{args.case}.json').read_text())
            report.update(validate_movement(fixture, case))
        if args.case == 'two-player-rally':
            from rally_reference import validate_rally
            case = json.loads((ROOT / f'tests/cases/{args.case}.json').read_text())
            report.update(validate_rally(fixture, case))
        print(json.dumps(report, indent=2))
        return
    config = configparser.ConfigParser(interpolation=None)
    config.read(ROOT / "config.local.ini", encoding="utf-8")
    cartridge = Path(config['inputs']['cartridge']).read_bytes()
    if hashlib.sha256(cartridge).hexdigest() != ROM_SHA256:
        raise ValueError('Unexpected cartridge')
    with zipfile.ZipFile(ROOT / 'build/mame/roms/sg1000/champtns.zip') as archive:
        if len(archive.namelist()) != 1 or archive.read(archive.namelist()[0]) != cartridge:
            raise ValueError('MAME archive differs from the supplied cartridge')
    if args.case != 'serve':
        capture_round(config, args.case)
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
