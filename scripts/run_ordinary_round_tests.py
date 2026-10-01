"""Focused CT05 ordinary physical-input proof: first game, pause, next serve."""
import argparse
import json
import re
import shutil
from pathlib import Path
from build_native_game import build
from capture_native_presentation import code_symbols
from copperline_test_session import NativeControlSession
from evidence import ROOT, atomic_json, compile_manifest, tracked_call


def run(mode):
    config, ordinary = build()
    directory = ROOT / f'build/tests/ct05-ordinary-{mode}-round'
    directory.mkdir(parents=True, exist_ok=True)
    exe = directory / 'native-application'
    shutil.copy2(ordinary, exe)
    listing = directory / 'native.lst'
    shutil.copy2(ordinary.parent / 'native.lst', listing)
    compile_manifest(exe, listing)
    symbols = code_symbols(listing.read_text())
    rows, differences = [], []
    award = paused = resumed = completed = None
    frozen = None
    previous_games = 0
    last_callback = None
    with NativeControlSession(directory) as s:
        s.inspect('session_launch', {'binary': config['tools']['copperline'], 'run': str(exe),
            'args': ['--chipset', 'OCS', '--video', 'PAL', '--cpu', '68000', '--chip', '512K',
                     '--slow', '0', '--fast', '0', '--noaudio', config['inputs']['amiga_rom']]})
        stop = s.inspect('run_until', {'seconds': 30})
        if stop['reason'] != 'loadseg': raise RuntimeError(stop)
        base = int(re.search(r'first hunk \$([0-9A-Fa-f]+)', stop['detail'])[1], 16)
        def mem(name, count):
            return bytes.fromhex(s.inspect('mem_read', {'addr': base + symbols[name], 'len': count})['data'])
        s.inspect('run_until', {'seconds': stop['seconds'] + 2})
        if int.from_bytes(mem('game_lifecycle', 2), 'big') != 2:
            raise AssertionError('Ordinary title not reached')
        key = 0x46 if mode == 'one' else 0x42
        s.inspect('input_key', {'rawkey': key, 'action': 'press'})
        stop = s.inspect('run_until', {'seconds': stop['seconds'] + 5})
        s.inspect('input_key', {'rawkey': key, 'action': 'release'})
        for port in (1, 2):
            s.inspect('input_set_port', {'port': port, 'device': 'joystick'})
            s.inspect('input_joy', {'port': port, 'red': True})
        pc = base + symbols['game_observe_pre_tail']
        s.inspect('break_add', {'kind': 'pc', 'addr': pc})
        deadline = stop['seconds'] + 150
        for index in range(6000):
            stop = s.inspect('run_until', {'seconds': deadline})
            if stop['pc'] != pc or stop['reason'] not in ('target', 'breakpoint'): raise RuntimeError(stop)
            ram = bytes.fromhex(s.inspect('mem_read', {'addr': base + symbols['virtual_memory'] + 0xc000, 'len': 256})['data'])
            lifecycle = int.from_bytes(mem('game_lifecycle', 2), 'big')
            stage = mem('game_score_state', 1)[0]
            games = sum(ram[0x40:0x42])
            row = {'callback': int.from_bytes(mem('simulation_updates', 2), 'big') + 1,
                   'lifecycle': lifecycle, 'scoring_stage': stage, 'ram': ram.hex()}
            if last_callback is not None and row['callback'] != last_callback + 1:
                raise AssertionError('Ordinary callback observation is not consecutive')
            last_callback = row['callback']
            if bool(ram[0x3d] & 0x80) != (mode == 'two'):
                differences.append({'field': 'physical mode selection', 'callback': row['callback']})
            rows.append(row)
            if games != previous_games:
                if games != previous_games + 1 or award is not None:
                    differences.append({'field': 'exactly one first-game award', 'callback': row['callback']})
                award = row['callback']
                previous_games = games
            if lifecycle in (4, 5):
                if award is None: differences.append({'field': 'pause before game award'})
                if paused is None: paused = row['callback']
                pose = ram[0x45:0x4d]
                if frozen is None: frozen = pose
                if pose != frozen: differences.append({'field': 'player moved during round pause', 'callback': row['callback']})
                if games != 1 or any(ram[0x3e:0x40]):
                    differences.append({'field': 'score changed during round pause', 'callback': row['callback']})
            elif paused is not None and lifecycle == 1:
                if resumed is None: resumed = row['callback']
                if stage == 1 and ram[0x38] and ram[0x66]:
                    completed = row['callback']
                    break
        if not all((award, paused, resumed, completed)):
            differences.append({'field': 'ordinary first game and subsequent advancing serve not completed'})
    path = ROOT / f'build/tests/ct05-ordinary-{mode}-round-report.json'
    capture = directory / 'observations.json'
    atomic_json(capture, rows)
    report = {'case': f'ct05-ordinary-{mode}-round', 'passed': not differences,
              'first_difference': differences[0] if differences else None, 'differences': differences,
              'award_callback': award, 'pause_callback': paused, 'resume_callback': resumed,
              'next_serve_callback': completed, 'observed_callbacks': len(rows),
              'capture': str(capture.relative_to(ROOT)), 'physical_inputs': 'held red on both physical ports',
              'scope': 'Ordinary first game and next serve; no match parity or raster equivalence'}
    atomic_json(path, report)
    print(json.dumps({k:v for k,v in report.items() if k not in ('capture','differences')}))
    return 0 if report['passed'] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('one','two'), required=True)
    mode = parser.parse_args().mode
    path = ROOT / f'build/tests/ct05-ordinary-{mode}-round-report.json'
    return tracked_call([path], 'ordinary-round', 'maintained-native', 'ordinary title',
                        'scripts/run_ordinary_round_tests.py', None, lambda: run(mode),
                        lambda path, report: [ROOT / f'build/tests/ct05-ordinary-{mode}-round/native-application'])

if __name__ == '__main__':
    raise SystemExit(main())
