from native_state_observation import read_native_state
"""Drive real Amiga pads and compare live input readers with original calibration."""
import argparse
import configparser
import json
import re
from pathlib import Path

from copperline_test_session import NativeControlSession
from capture_native_presentation import code_symbols
from physical_input_reference import ROOT, CASES, load_reference, window, compare_row, sha, OUTCOME_FIELDS, ownership_reference
from build_native_game import build, module_hashes
from evidence import tracked_call, compile_manifest
from run_translated_prng_probe import ASSEMBLER, run


def capture(policy, source, rows, mutation=False, label="physical-input"):
    directory = ROOT / ('build/tests/native-' + label + ('-mutation' if mutation else ''))
    directory.mkdir(parents=True, exist_ok=True)
    (directory / 'capture.json').unlink(missing_ok=True)
    build()
    initial = directory / 'initial-ram.bin'
    initial.write_bytes(bytes.fromhex(source['callbacks'][0]['post_tail_ram']))
    original = (ROOT / policy['native_source']).read_text(encoding='utf-8')
    marker = 'initial_ram: incbin "build/translation/live-initial-ram.bin"'
    if original.count(marker) != 1:
        raise ValueError('Native initial state include changed')
    adapted = original.replace(marker, f'initial_ram: incbin "{initial.as_posix()}"')
    if mutation:
        controls = (ROOT / 'amiga/game/controls.s').read_text()
        adapted = adapted.replace('include "amiga/game/controls.s"', 'include "' + (directory / 'controls.s').as_posix() + '"')
        marker = 'input_ready:\n        rts'
        if controls.count(marker) != 1:
            raise ValueError('Native sampler return changed')
        (directory / 'controls.s').write_text(controls.replace(marker, 'input_ready:\n        eori.b  #1,game_input_bits\n        rts'))
    wrapper = directory / 'native-input.s'
    wrapper.write_text(adapted, encoding='utf-8')
    executable = directory / 'native-application'
    listing = directory / 'native.lst'
    run([str(ASSEMBLER), '-Fhunkexe', '-kick1hunks', '-m68000', '-DLIVE_PHASE_START=1', '-L', str(listing),
         '-o', str(executable), str(wrapper)])
    compile_manifest(executable,listing)
    symbols = code_symbols(listing.read_text())
    config = configparser.ConfigParser(interpolation=None)
    config.read(ROOT / 'config.local.ini', encoding='utf-8')
    observations, changes = [], []
    previous_ports = None
    with NativeControlSession(directory) as session:
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
            session.inspect('input.set_port', {'port': port, 'device': 'joystick'})
        entries = {base + symbols['read_game_input']: 0, base + symbols['sample_second_input_group']: 1}
        for address in entries:
            session.inspect('break.add', {'kind': 'pc', 'addr': address})
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
                regs = session.inspect('regs.get')
                return_pc = int(session.inspect('mem_read', {'addr': regs['a'][7], 'len': 4})['data'], 16)
                returned = session.inspect('run_until', {'pc': return_pc, 'wait_ms': 50000})
                if returned['reason'] != 'target' or returned.get('bridge'):
                    raise RuntimeError(f'Native reader return not reached: {returned}')
                values[group] = session.inspect('regs.get')['d'][0] & 255
                reader_stops.append({'group': group, 'entry': entry, 'return': returned, 'value': values[group]})
            # Native scoring follows completed input normalization in the
            # shared active tick; the translated score_gate no longer exists.
            normalized = session.inspect('run_until', {'pc': base + symbols['game_score_tick'], 'wait_ms': 50000})
            if normalized['reason'] != 'target' or normalized.get('bridge'):
                raise RuntimeError(f'Native normalization not reached: {normalized}')
            regs = session.inspect('regs.get')
            data = read_native_state(session,base,symbols)
            actual = {'update': row['update'], 'readers': [values[0], values[1]],
                      'native_completed_before_sample': native_count,
                      'normalized': [data[0x53], data[0x56]], 'mode_side': data[0x3d] & 0x94,
                      'reader_stops': reader_stops, 'normalized_stop': normalized}
            outcome_stop = session.inspect('run_until', {'pc': base + symbols['game_observe_pre_tail']})
            if outcome_stop['reason'] != 'target':
                raise RuntimeError(f'Native player outcome boundary not reached: {outcome_stop}')
            result = read_native_state(session,base,symbols)
            actual['outcome'] = {name: result[offset] for name, offset in OUTCOME_FIELDS.items()}
            actual['edges'] = list(bytes.fromhex(session.inspect('mem_read', {'addr': base + symbols['game_input_pressed'], 'len': 4})['data']))
            actual['owners'] = list(bytes.fromhex(session.inspect('mem_read', {'addr': base + symbols['game_lower_owner'], 'len': 2})['data']))
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
    report = {'initial_source_callback': source.get('initial_source_callback', 0), 'initial_ram_sha256': sha(initial),
              'reference_sha256': policy['reference_sha256'], 'executable_sha256': sha(executable),
              'native_source_sha256': sha(ROOT / policy['native_source']), 'adapter_sha256': sha(wrapper),
              'emulator_sha256': sha(Path(config['tools']['copperline'])), 'transport_sha256': sha(ROOT / 'scripts/copperline_test_session.py'), 'native_modules': module_hashes(),
              'kickstart_sha256': sha(Path(config['inputs']['amiga_rom'])),
              'mutation': mutation, 'compiled_controls_sha256': sha(directory/'controls.s') if mutation else sha(ROOT/'amiga/game/controls.s'), 'changes': changes, 'observations': observations,
              'completed_native_callbacks': completed, 'endpoint': stop,
              'scope': 'Maintained physical controls, edges, ownership and eight observed player fields at every callback; physical edges retimed to sampling boundaries, initial state only. Local phase evidence, not continuous round progression or real-time latency.'}
    path = directory / 'capture.json'
    path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return path, report


def _main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=CASES)
    parser.add_argument('--all', action='store_true')
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--ownership', action='store_true', help='Also check the single reachable exchanged-end window')
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
    batch_difference = next((row['first_difference'] for row in normal['observations'] if row['first_difference']), None)
    passed = batch_difference is None
    for name, case in recipes.items():
        checks = [{'source': row, 'native': normal_rows[row['update']],
                   'first_difference': compare_row(row, normal_rows[row['update']])} for row in window(case, rows)]
        first = next((row['first_difference'] for row in checks if row['first_difference']), None) or batch_difference
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
                  'full_native_capture_callbacks': len(normal_rows), 'batch_first_difference': batch_difference,
                  'scope': case['contract'] + ' CT-03 additionally compares actual positions, phases, animation, ownership and press/release edges at every observed update.'}
        (ROOT / f'build/tests/{name}-report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        passed &= report['passed']
        print(json.dumps({'case': name, 'passed': report['passed'], 'first_difference': first}), flush=True)
    if args.ownership:
        other_source, other_rows = ownership_reference()
        other_policy = dict(policy, reference_sha256=sha(ROOT/'build/reference/control-ownership/reference.json'))
        path, evidence = capture(other_policy, other_source, other_rows, label='control-ownership')
        first = next((row['first_difference'] for row in evidence['observations'] if row['first_difference']), None)
        evidence.update(passed=first is None, first_difference=first)
        path.write_text(json.dumps(evidence,indent=2)+'\n')
        print(json.dumps({'exchanged_end_ownership': first is None, 'first_difference': first}),flush=True)
        passed &= first is None
    return 0 if passed else 1


def main():
    import sys
    if '--timing-edges' in sys.argv:
        if sys.argv[1:] != ['--timing-edges']:
            raise ValueError('--timing-edges is a separate four-edge ordinary probe')
        from input_timing_edges import run as run_edges
        path=ROOT/'build/tests/ct09-input-timing-edges-report.json'
        return tracked_call([path],'physical','maintained-native','ordinary title',
                            'scripts/run_physical_input_tests.py',None,run_edges,
                            lambda path,report:[ROOT/'build/tests/ct09-input-timing-edges/native-application'])
    if '--help' in sys.argv:
        return _main()
    probe = argparse.ArgumentParser(add_help=False)
    probe.add_argument('--case', choices=CASES)
    probe.add_argument('--all', action='store_true')
    selected, _ = probe.parse_known_args()
    names = CASES if selected.all else (selected.case,) if selected.case else ()
    paths = [ROOT/f'build/tests/{name}-report.json' for name in names]
    if '--ownership' in sys.argv:
        paths.append(ROOT/'build/tests/native-control-ownership/capture.json')
    def executables(path,report):
        capture = ROOT/report['capture'] if 'capture' in report else path
        return [capture.parent/'native-application']
    return tracked_call(paths, 'physical', 'maintained-native', 'captured phase',
                        'scripts/run_physical_input_tests.py', list(names) + ['physical-input'], _main, executables)


if __name__ == '__main__':
    raise SystemExit(main())
