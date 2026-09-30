"""Observe exact source movement inputs and prove the frozen replay is unchanged."""
import argparse
import configparser
import hashlib
import json
import os
import subprocess
import zipfile
from collections import Counter
from pathlib import Path
from round_reference import FOCUSED_CASES, parse_capture, validate_fixture
from run_translated_player_frame_probe import ROM_SHA256

ROOT = Path(__file__).resolve().parent.parent


def remove_observations(payload):
    """Recover the ordinary raw stream exactly, including its sequence numbers."""
    lines = payload.splitlines(keepends=True)
    kept, index = [], 0
    while index < len(lines):
        body = lines[index].split(b'\t', 1)[1]
        if body.startswith((b'REF V ', b'REF U ')):
            for chunk in range(4):
                expected = f'REF D {chunk * 64} '.encode()
                if not lines[index + 1 + chunk].split(b'\t', 1)[1].startswith(expected):
                    raise ValueError('Incomplete diagnostic snapshot chunks')
            index += 5
        else:
            kept.append(str(len(kept) + 1).encode() + b'\t' + body)
            index += 1
    return b''.join(kept)


def inventory(callbacks):
    result = {}
    for side, animation, coordinate in (('lower', 0x43, 0x49), ('upper', 0x44, 0x45)):
        selections, enabled, changed = Counter(), Counter(), Counter()
        intervals, current = [], None
        for callback in callbacks:
            if callback['callback_kind'] != 'gameplay':
                if current:
                    intervals.append(current)
                    current = None
                continue
            before = bytes.fromhex(callback['movement_entry_ram'])
            after = bytes.fromhex(callback['movement_return_ram'])
            row = (before[animation] >> 5) & 3
            blocked = bool(before[animation] & 128 or before[0x39] & 4)
            shift = 4 if ((before[0x3D] ^ (16 if side == 'upper' else 0)) & 16) else 0
            direction = (before[0x53] >> shift) & 15
            selections[row] += 1
            if not blocked:
                enabled[row] += 1
                if before[coordinate:coordinate + 2] != after[coordinate:coordinate + 2]:
                    changed[row] += 1
            key = (row, blocked)
            if current is None or key != (current['bounds_row'], current['blocked']):
                if current:
                    intervals.append(current)
                current = {'bounds_row': row, 'blocked': blocked, 'first_update': callback['ordinal'],
                           'last_update': callback['ordinal'], 'start_yx': list(before[coordinate:coordinate + 2]),
                           'end_yx': list(after[coordinate:coordinate + 2]),
                           'directions_observed': []}
            current['last_update'] = callback['ordinal']
            current['end_yx'] = list(after[coordinate:coordinate + 2])
            if direction not in current['directions_observed']:
                current['directions_observed'].append(direction)
        if current:
            intervals.append(current)
        result[side] = {'selected_row_counts': dict(selections), 'enabled_row_counts': dict(enabled),
                        'callbacks_with_position_change': dict(changed), 'intervals': intervals}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=FOCUSED_CASES + ('one-player-match', 'two-player-match'),
                        default='two-player-rally')
    args = parser.parse_args()
    case_path = ROOT / f'tests/cases/{args.case}.json'
    case = json.loads(case_path.read_text())
    parent_path = ROOT / case['reference']
    parent_bytes = parent_path.read_bytes()
    parent = json.loads(parent_bytes)
    validate_fixture(parent)
    ordinary_name = 'without-observer.tsv' if parent.get('movement_observations') else 'a.tsv'
    ordinary_path = ROOT / f'build/tests/{args.case}-capture/{ordinary_name}'
    ordinary = ordinary_path.read_bytes()
    ordinary_hash = parent.get('ordinary_capture_sha256', parent['capture_sha256'])
    if hashlib.sha256(ordinary).hexdigest() != ordinary_hash:
        raise ValueError('Ordinary raw source capture no longer matches frozen provenance')
    config = configparser.ConfigParser(interpolation=None)
    config.read(ROOT / 'config.local.ini', encoding='utf-8')
    cartridge = Path(config['inputs']['cartridge']).read_bytes()
    if hashlib.sha256(cartridge).hexdigest() != ROM_SHA256 or parent['rom_sha256'] != ROM_SHA256:
        raise ValueError('Unexpected source cartridge')
    if cartridge[0x13B9:0x13BF] != bytes.fromhex('cd0414cd5d14'):
        raise ValueError('Movement observation boundaries do not bracket the two CALLs')
    with zipfile.ZipFile(ROOT / 'build/mame/roms/sg1000/champtns.zip') as archive:
        if len(archive.namelist()) != 1 or archive.read(archive.namelist()[0]) != cartridge:
            raise ValueError('MAME archive differs from source cartridge')
    mame = ROOT / '.tools/mame-0.289/mame.exe'
    if hashlib.sha256(mame.read_bytes()).hexdigest() != parent['emulator_sha256']:
        raise ValueError('Source emulator differs from parent capture')
    policy = ROOT / case['capture_policy']
    if hashlib.sha256(policy.read_bytes()).hexdigest() != parent['policy_sha256']:
        raise ValueError('Frozen physical policy changed')
    out = ROOT / f'build/tests/{args.case}-movement-observations'
    out.mkdir(parents=True, exist_ok=True)
    report_path = out / 'report.json'
    report_path.unlink(missing_ok=True)
    payloads = []
    command = parent['source_command']
    for name in ('a', 'b'):
        env = os.environ.copy()
        env.update(CT_TEST_CAPTURE=str(out / f'{name}.tsv'), CT_TEST_LAST_FRAME=str(case['last_begin_frame']),
                   CT_TEST_SELECT=case['selection'], CT_TEST_FIRE=str(int(case['default_fire'])),
                   CT_TEST_CONTACT_MARKERS='1' if case['selection'] == 'two' else '0',
                   CT_TEST_POLICY=case['capture_policy'], CT_TEST_MOVEMENT_SNAPSHOTS='1')
        process = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True)
        (out / f'{name}.log').write_text(process.stdout + process.stderr)
        if process.returncode or 'ROUND_REFERENCE_COMPLETE' not in process.stdout or 'LUA ERROR' in process.stdout + process.stderr:
            raise RuntimeError('Source movement observation capture failed; inspect log')
        payload = (out / f'{name}.tsv').read_bytes()
        if remove_observations(payload) != ordinary:
            raise ValueError('Movement instrumentation changed the ordinary source recording')
        payloads.append(payload)
    if payloads[0] != payloads[1]:
        raise ValueError('Source movement observations did not repeat exactly')
    callbacks, _ = parse_capture(payloads[0])
    raw_callback_count = len(callbacks)
    callbacks = [callback for callback in callbacks if callback['ordinal'] <= len(parent['updates'])]
    for callback in callbacks:
        if callback['callback_kind'] == 'gameplay' and 'movement_entry_ram' not in callback:
            raise ValueError('Missing gameplay movement observation')
    report = {'case': args.case, 'parent_reference_sha256': hashlib.sha256(parent_bytes).hexdigest(),
              'ordinary_capture_sha256': ordinary_hash,
              'observation_capture_sha256': hashlib.sha256(payloads[0]).hexdigest(),
              'observer_sha256': hashlib.sha256((ROOT / 'scripts/capture_round_reference.lua').read_bytes()).hexdigest(),
              'parser_sha256': hashlib.sha256((ROOT / 'scripts/round_reference.py').read_bytes()).hexdigest(),
              'repeat_identical': True, 'ordinary_raw_stream_unchanged': True,
              'initial_callback_included': True, 'raw_callbacks_observed': raw_callback_count,
              'retained_callbacks_observed': len(callbacks),
              'movement': inventory(callbacks), 'complete_F1': False}
    report_path.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: value for key, value in report.items() if key != 'movement'}, indent=2))


if __name__ == '__main__':
    main()
