"""Run actual 68000 routines against a frozen, independent source oracle."""
import argparse
import configparser
import hashlib
import json
import re
import sys
from run_translated_prng_probe import ROOT, ASSEMBLER, run
from run_translated_player_frame_probe import prepare_gameplay, ROM_SHA256
from round_reference import validate_fixture
from phase_reference import CASES as PHASE_CASES, validate_phase

OUT = ROOT / 'build/tests'


def compare(records, fixture, case, fields):
    exact = fixture.get('schema_version') == 2
    stride = 5 if exact else 3
    expected_records = 2 + stride * case['updates']
    if len(records) != expected_records:
        raise ValueError(f'Expected {expected_records} native records, received {len(records)}')
    if len(records[0]) != 256 or len(bytes.fromhex(fixture['initial_post_tail'])) != 256:
        raise ValueError('Incomplete initial state record')
    for offset, (actual, expected) in enumerate(zip(records[0], bytes.fromhex(fixture['initial_post_tail']))):
        if offset not in case['excluded_ram_offsets'] and actual != expected:
            return {'update': 0, 'field': fields[str(offset)], 'expected': expected, 'actual': actual}
    initial = bytes(fixture['initial_psg'])
    if records[1] != initial:
        return {'update': 0, 'field': 'initial ordered PSG events',
                'expected': initial.hex(), 'actual': records[1].hex()}
    for index, expected in enumerate(fixture['updates'], 1):
        start = 2 + stride * (index - 1)
        if exact:
            actual_entry, actual_ram, actual_tail, actual_psg, actual_refresh = records[start:start + stride]
        else:
            actual_ram, actual_tail, actual_psg = records[start:start + stride]
        expected_ram = bytes.fromhex(expected['ram'])
        if len(actual_ram) != 256 or len(expected_ram) != 256:
            raise ValueError('Incomplete state record')
        boundaries = [('pre-tail', actual_ram, expected_ram),
                      ('post-tail', actual_tail, bytes.fromhex(expected['post_tail_ram']))]
        if exact:
            boundaries.insert(0, ('callback-entry', actual_entry, bytes.fromhex(expected['entry_ram'])))
        for boundary, actual, wanted in boundaries:
            if len(actual) != 256 or len(wanted) != 256:
                raise ValueError('Incomplete state record')
            for offset in range(256):
                if offset in case['excluded_ram_offsets']:
                    continue
                if actual[offset] != wanted[offset]:
                    difference = {'update': index, 'source_frame': expected['frame'], 'boundary': boundary,
                            'field': fields[str(offset)], 'ram_offset': offset,
                            'expected': wanted[offset], 'actual': actual[offset]}
                    if exact:
                        difference['callback_kind'] = expected['callback_kind']
                        difference['preceding_source_events'] = expected['before_events']
                        if 'source_ordinal' in expected:
                            difference['source_update'] = expected['source_ordinal']
                    return difference
        expected_psg = bytes(expected['psg'])
        if actual_psg != expected_psg:
            return {'update': index, 'source_frame': expected['frame'], 'field': 'ordered PSG events',
                    'expected': expected_psg.hex(), 'actual': actual_psg.hex()}
        if exact:
            wanted = bytes(read['value'] for read in expected['refresh_reads'])
            if actual_refresh != wanted:
                return {'update': index, 'source_frame': expected['frame'], 'field': 'consumed refresh decisions',
                        'expected': wanted.hex(), 'actual': actual_refresh.hex()}
    return None


def execute(config, case_name='serve', mutation=False):
    executable = OUT / (case_name + ('-mutated' if mutation else ''))
    command = [str(ASSEMBLER), '-Fhunkexe', '-kick1hunks', '-m68000']
    if mutation:
        command.append('-DREGRESSION_MUTATION=1')
    run(command + ['-o', str(executable), 'amiga/tests/simulation_harness.s'])
    log = run([config['tools']['copperline'], '--factory', '--model', 'A500', '--chipset', 'OCS',
               '--video', 'PAL', '--cpu', '68000', '--chip', '512K', '--slow', '0', '--fast', '0',
               '--noaudio', '--run', str(executable), '--exit-on-return', config['inputs']['amiga_rom']], timeout=120)
    (OUT / (executable.name + '.log')).write_text(log, encoding='utf-8')
    for marker in ('cpu=M68000', 'chip_ram=512K', 'fast_ram=0K', 'slow_ram=0K',
                   'chipset=Ocs', 'video=Pal', 'Kickstart 1.3', 'program returned 0'):
        if marker not in log:
            raise ValueError(f'Run missing {marker}')
    records = [bytes.fromhex(value) for value in re.findall(r'DBG: REG ([0-9A-F]*)', log)]
    return records, hashlib.sha256(executable.read_bytes()).hexdigest()


def prepare_inputs(fixture, case):
    """Materialize inputs/entropy, never inject expected transition writes."""
    count = len(fixture['updates'])
    exact = fixture.get('schema_version') == 2
    if not 0 < count <= 16384:
        raise ValueError('Replay exceeds this harness input-index range')
    initial = bytes.fromhex(fixture['initial_pre_tail'])
    if len(initial) != 256:
        raise ValueError('Invalid initial RAM extent')
    (OUT / 'initial-ram.bin').write_bytes(initial)
    inputs = bytearray(2 * count)
    if exact:
        refresh = bytearray()
        for index, row in enumerate(fixture['updates']):
            seen = set()
            for read in row['inputs']:
                group = read['group']
                if group not in (0, 1) or group in seen:
                    raise ValueError('Harness needs an adapter for repeated input reads')
                seen.add(group)
                inputs[2 * index + group] = read['value']
            refresh.extend(read['value'] for read in row['refresh_reads'])
        (OUT / 'refresh-values.bin').write_bytes(refresh)
    else:
        for segment in case['input']:
            for update in range(segment['from'], segment['through'] + 1):
                inputs[2 * (update - 1)] = segment['game_bits']
    (OUT / 'inputs.bin').write_bytes(inputs)
    (OUT / 'harness-config.i').write_text(
        f'CASE_UPDATE_COUNT equ {count}\nCASE_CAPTURE_REFRESH equ {int(exact)}\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', action='store_true', help='Also verify detection of a temporary gameplay mutation')
    parser.add_argument('--case', choices=('serve', 'round-transition', 'one-player-match') + PHASE_CASES, default='serve')
    parser.add_argument('--reference-only', action='store_true', help='Validate and prepare the round reference without running the port')
    args = parser.parse_args()
    case = json.loads((ROOT / f'tests/cases/{args.case}.json').read_text())
    reference = ROOT / case['reference']
    if not reference.exists():
        raise FileNotFoundError(f'{reference}: run python scripts/capture_test_reference.py --case {args.case} once')
    fixture = json.loads(reference.read_text())
    if not fixture['repeat_identical']:
        raise ValueError('Reference determinism has not been established')
    exact = fixture.get('schema_version') == 2
    if exact:
        reference_summary = validate_phase(fixture, case) if fixture.get('reference_kind') == 'source-derived-phase' else validate_fixture(fixture)
        case['updates'] = len(fixture['updates'])
    elif args.reference_only:
        parser.error('--reference-only applies to the round-transition case')
    elif case['refresh_bit'] != 0:
        raise ValueError('The serve reference assumes refresh bit zero')
    if fixture['rom_sha256'] != ROM_SHA256 or len(fixture['updates']) != case['updates']:
        raise ValueError('Wrong reference revision or callback count')
    if not exact and [row['frame'] for row in fixture['updates']] != list(range(case['first_frame'], case['first_frame'] + case['updates'])):
        raise ValueError('Reference callback sequence is incomplete')
    fields = json.loads((ROOT / 'tests/state-fields.json').read_text())['bytes']
    config = configparser.ConfigParser(interpolation=None)
    config.read(ROOT / 'config.local.ini', encoding='utf-8')
    OUT.mkdir(parents=True, exist_ok=True)
    prepare_inputs(fixture, case)
    if args.reference_only:
        report = {'case': case['name'], 'reference_valid': True, 'port_executed': False,
                  'reference_sha256': hashlib.sha256(reference.read_bytes()).hexdigest(), **reference_summary}
        (OUT / f'{case["name"]}-reference-report.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report, indent=2))
        return 0
    # Translation/extraction is shared with the live executable build. No Python
    # simulation runs here, and expected state is never generated from target code.
    run([sys.executable, 'scripts/roundtrip_rom.py'])
    prepare_gameplay()
    records, digest = execute(config, case['name'])
    difference = compare(records, fixture, case, fields)
    report = {'case': case['name'], 'updates': case['updates'], 'bytes_compared_per_boundary': 254,
              'boundaries_per_update': 3 if exact else 2,
              'reference_psg_bytes': sum(len(row['psg']) for row in fixture['updates']),
              'reference_sha256': hashlib.sha256(reference.read_bytes()).hexdigest(),
              'executable_sha256': digest, 'first_difference': difference, 'passed': difference is None}
    matched = case['updates'] if difference is None else max(0, difference['update'] - 1)
    report['updates_matched'] = matched
    report['psg_bytes_compared_in_matched_updates'] = sum(len(row['psg']) for row in fixture['updates'][:matched])
    if args.self_test and difference is None:
        source = (ROOT / 'build/translation/player-frame-routines.s').read_text()
        anchor = 'ball_flight_update:\n'
        if source.count(anchor) != 1:
            raise ValueError('Mutation entry point missing')
        mutation_path = OUT / 'mutated-routines.s'
        mutation_path.write_text(source.replace(anchor, anchor + '\taddq.b #1,$35(a5)\n'))
        try:
            mutated, _ = execute(config, case['name'], mutation=True)
            detected = compare(mutated, fixture, case, fields)
            report['mutation_first_difference'] = detected
            if detected is None:
                raise AssertionError('Gameplay mutation was not detected')
        finally:
            mutation_path.unlink(missing_ok=True)
            (OUT / (case['name'] + '-mutated')).unlink(missing_ok=True)
    if exact:
        report['reference_coverage'] = reference_summary
        report['port_limit'] = 'Gameplay executes every tick; native between-game transition is not implemented'
    report_path = f'{case["name"]}-report.json' if exact else 'report.json'
    (OUT / report_path).write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    console_report = dict(report)
    if difference and 'preceding_source_events' in difference:
        events = difference['preceding_source_events']
        console_report['first_difference'] = {key: value for key, value in difference.items() if key != 'preceding_source_events'}
        console_report['first_difference']['preceding_source_event_count'] = len(events)
        console_report['full_report'] = str(OUT / report_path)
    print(json.dumps(console_report, indent=2))
    return 1 if difference else 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, RuntimeError, FileNotFoundError, AssertionError) as error:
        print(f'REGRESSION ERROR: {error}', file=sys.stderr)
        sys.exit(2)
