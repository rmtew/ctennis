"""Drive real Amiga pads and compare live input readers with original calibration."""
import argparse
import configparser
import json
import re
from pathlib import Path

from copperline_test_session import CopperlineSession
from capture_native_presentation import code_symbols
from physical_input_reference import ROOT, CASES, load_reference, window, compare_row, sha
from run_presentation_tests import build_native
from run_translated_prng_probe import ASSEMBLER, run


def capture(policy, source, rows, mutation=False):
    directory = ROOT / ('build/tests/native-physical-input' + ('-mutation' if mutation else ''))
    directory.mkdir(parents=True, exist_ok=True)
    (directory / 'capture.json').unlink(missing_ok=True)
    build_native({'native_source': policy['native_source']}, directory)
    initial = directory / 'initial-ram.bin'
    initial.write_bytes(bytes.fromhex(source['callbacks'][0]['post_tail_ram']))
    original = (ROOT / policy['native_source']).read_text(encoding='utf-8')
    marker = 'initial_ram: incbin "build/translation/live-initial-ram.bin"'
    if original.count(marker) != 1:
        raise ValueError('Native initial state include changed')
    adapted = original.replace(marker, f'initial_ram: incbin "{initial.as_posix()}"')
    if mutation:
        marker = 'input_ready:\n        rts'
        if adapted.count(marker) != 1:
            raise ValueError('Native sampler return changed')
        adapted = adapted.replace(marker, 'input_ready:\n        eori.b  #1,game_input_bits\n        rts')
    wrapper = directory / 'native-input.s'
    wrapper.write_text(adapted, encoding='utf-8')
    executable = directory / 'native-application'
    listing = directory / 'native.lst'
    run([str(ASSEMBLER), '-Fhunkexe', '-kick1hunks', '-m68000', '-L', str(listing),
         '-o', str(executable), str(wrapper)])
    symbols = code_symbols(listing.read_text())
    config = configparser.ConfigParser(interpolation=None)
    config.read(ROOT / 'config.local.ini', encoding='utf-8')
    ctl = Path(config['tools']['copperline']).with_name('copperline-ctl.exe')
    observations, changes = [], []
    previous_ports = None
    with CopperlineSession(ctl, ROOT) as session:
        launch = session.inspect('session_launch', {'factory': True, 'model': 'A500',
            'binary': config['tools']['copperline'], 'run': str(executable),
            'args': ['--chipset', 'OCS', '--video', 'PAL', '--cpu', '68000',
                     '--chip', '512K', '--slow', '0', '--fast', '0', '--noaudio',
                     config['inputs']['amiga_rom']]})
        stop = session.inspect('run_until', {'seconds': 30, 'wait_ms': 50000})
        if stop['reason'] != 'loadseg':
            raise RuntimeError(f'Native input executable not loaded: {stop}')
        base = int(re.search(r'first hunk \$([0-9A-Fa-f]+)', stop['detail']).group(1), 16)
        for port in policy['amiga_ports'].values():
            session.inspect('input_set_port', {'port': port, 'device': 'joystick'})
        entries = {base + symbols['read_game_input']: 0, base + symbols['sample_second_input_group']: 1}
        for address in entries:
            session.inspect('break_add', {'kind': 'pc', 'addr': address})
        for row in rows[1:]:
            stop = session.inspect('run_until', {'pc': base + symbols['simulation_update'], 'wait_ms': 50000})
            if stop['reason'] != 'target' or stop.get('bridge'):
                raise RuntimeError(f'Native input sampling boundary not reached: {stop}')
            native_count = int(session.inspect('mem_read', {
                'addr': base + symbols['simulation_updates'], 'len': 2})['data'], 16)
            if native_count != row['update'] - 1:
                raise ValueError('Physical input capture skipped or repeated a native callback')
            if row['ports'] != previous_ports:
                for state in row['ports']:
                    session.inspect('input_joy', state)
                changes.append({'source_update': row['update'], 'source_frame': row['source_frame'],
                                'ports': row['ports'], 'native_sample_boundary': stop})
                previous_ports = row['ports']
            values, reader_stops = {}, []
            for _ in range(2):
                entry = session.inspect('run_until', {'seconds': stop['seconds'] + 1, 'wait_ms': 50000})
                if entry['reason'] != 'breakpoint' or entry['pc'] not in entries:
                    raise RuntimeError(f'Native input reader not reached: {entry}')
                group = entries[entry['pc']]
                if group in values:
                    raise ValueError('Duplicate native input reader invocation')
                regs = session.inspect('regs_get')
                return_pc = int(session.inspect('mem_read', {'addr': regs['a'][7], 'len': 4})['data'], 16)
                returned = session.inspect('run_until', {'pc': return_pc, 'wait_ms': 50000})
                if returned['reason'] != 'target' or returned.get('bridge'):
                    raise RuntimeError(f'Native reader return not reached: {returned}')
                values[group] = session.inspect('regs_get')['d'][0] & 255
                reader_stops.append({'group': group, 'entry': entry, 'return': returned, 'value': values[group]})
            normalized = session.inspect('run_until', {'pc': base + symbols['score_gate'], 'wait_ms': 50000})
            if normalized['reason'] != 'target' or normalized.get('bridge'):
                raise RuntimeError(f'Native normalization not reached: {normalized}')
            regs = session.inspect('regs_get')
            data = bytes.fromhex(session.inspect('mem_read', {'addr': regs['a'][5], 'len': 256})['data'])
            actual = {'update': row['update'], 'readers': [values[0], values[1]],
                      'native_completed_before_sample': native_count,
                      'normalized': [data[0x53], data[0x56]], 'mode_side': data[0x3d] & 0x94,
                      'reader_stops': reader_stops, 'normalized_stop': normalized}
            actual['first_difference'] = compare_row(row, actual)
            observations.append(actual)
            if row['update'] % 80 == 0:
                print(f'Physical inputs: {row["update"]}/{len(rows) - 1} original callbacks', flush=True)
        stop = session.inspect('run_until', {'pc': base + symbols['simulation_update'], 'wait_ms': 50000})
        if stop['reason'] != 'target' or stop.get('bridge'):
            raise RuntimeError('Last physical-input callback did not complete')
        completed = int(session.inspect('mem_read', {
            'addr': base + symbols['simulation_updates'], 'len': 2})['data'], 16)
        if completed != len(rows) - 1:
            raise ValueError('Physical input capture endpoint differs')
        log = Path(launch['log']).read_text(encoding='utf-8', errors='replace')
        for marker in ('cpu=M68000', 'cpu_clock=7.09MHz', 'chip_ram=512K', 'fast_ram=0K',
                       'slow_ram=0K', 'chipset=Ocs', 'video=Pal', 'Kickstart 1.3'):
            if marker not in log:
                raise ValueError(f'Native hardware profile missing: {marker}')
        (directory / 'copperline.log').write_text(log, encoding='utf-8')
    report = {'initial_source_callback': 0, 'initial_ram_sha256': sha(initial),
              'reference_sha256': policy['reference_sha256'], 'executable_sha256': sha(executable),
              'native_source_sha256': sha(ROOT / policy['native_source']), 'adapter_sha256': sha(wrapper),
              'emulator_sha256': sha(Path(config['tools']['copperline'])), 'bridge_sha256': sha(ctl),
              'kickstart_sha256': sha(Path(config['inputs']['amiga_rom'])),
              'mutation': mutation, 'changes': changes, 'observations': observations,
              'completed_native_callbacks': completed, 'endpoint': stop,
              'scope': 'Actual live input readers and normalized controls; source callbacks retime physical edges to native sampling boundaries. No expected intermediate RAM writes. UI selection, game-state parity, side exchange and real-time input latency remain separate.'}
    path = directory / 'capture.json'
    path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return path, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=CASES)
    parser.add_argument('--all', action='store_true')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.all == bool(args.case):
        parser.error('Choose --all or --case')
    names = CASES if args.all else (args.case,)
    for name in names:
        (ROOT / f'build/tests/{name}-report.json').unlink(missing_ok=True)
    policy, source, rows = load_reference()
    recipes = {name: json.loads((ROOT / f'tests/cases/{name}.json').read_text()) for name in names}
    for case in recipes.values():
        window(case, rows)
    normal_path, normal = capture(policy, source, rows)
    changed_path, changed = capture(policy, source, rows, True) if args.self_test else (None, None)
    normal_rows = {row['update']: row for row in normal['observations']}
    changed_rows = {row['update']: row for row in changed['observations']} if changed else {}
    passed = True
    for name, case in recipes.items():
        checks = [{'source': row, 'native': normal_rows[row['update']],
                   'first_difference': compare_row(row, normal_rows[row['update']])} for row in window(case, rows)]
        first = next((row['first_difference'] for row in checks if row['first_difference']), None)
        mutation = None
        if args.self_test:
            changed_checks = [compare_row(row['source'], changed_rows[row['source']['update']]) for row in checks]
            changed_first = next((row for row in changed_checks if row), None)
            if changed_first is None or changed_first == first:
                raise AssertionError(f'Actual native sampler mutation not detected: {name}')
            # All windows include a neutral/released boundary. A spurious other-player
            # direction must fail there even when the intended held control already fails.
            neutral = checks[0]['source']
            if compare_row(neutral, normal_rows[neutral['update']]) is not None:
                raise AssertionError('Calibration window does not start with matching neutral controls')
            if compare_row(neutral, changed_rows[neutral['update']]) is None:
                raise AssertionError('Native sampler mutation accepted at neutral boundary')
            mutation = {'instruction': 'Toggle sampled pad-1 Right in temporary executable',
                        'capture': str(changed_path), 'capture_sha256': sha(changed_path),
                        'first_difference': changed_first, 'neutral_boundary_rejected': True}
        report = {'case': name, 'passed': first is None, 'first_difference': first,
                  'checks': checks, 'self_test': args.self_test, 'mutation': mutation,
                  'reference_sha256': policy['reference_sha256'], 'case_sha256': sha(ROOT / f'tests/cases/{name}.json'),
                  'capture': str(normal_path), 'capture_sha256': sha(normal_path),
                  'full_native_capture_callbacks': len(normal_rows), 'scope': case['contract']}
        (ROOT / f'build/tests/{name}-report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        passed &= report['passed']
        print(json.dumps({'case': name, 'passed': report['passed'], 'first_difference': first}), flush=True)
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
