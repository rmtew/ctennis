"""Run actual 68000 routines against a frozen, independent source oracle."""
import argparse
import configparser
import hashlib
import json
import re
import sys
from run_translated_prng_probe import ROOT, ASSEMBLER, run
from run_translated_player_frame_probe import prepare_gameplay, ROM_SHA256

OUT = ROOT / 'build/tests'


def compare(records, fixture, case, fields):
    if len(records) != 2 + 3 * case['updates']:
        raise ValueError(f'Expected 602 native records, received {len(records)}')
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
        actual_ram, actual_tail, actual_psg = records[3 * index - 1:3 * index + 2]
        expected_ram = bytes.fromhex(expected['ram'])
        if len(actual_ram) != 256 or len(expected_ram) != 256:
            raise ValueError('Incomplete state record')
        for boundary, actual, wanted in (('post-gameplay', actual_ram, expected_ram),
                                         ('post-tail', actual_tail, bytes.fromhex(expected['post_tail_ram']))):
            if len(actual) != 256 or len(wanted) != 256:
                raise ValueError('Incomplete state record')
            for offset in range(256):
                if offset in case['excluded_ram_offsets']:
                    continue
                if actual[offset] != wanted[offset]:
                    return {'update': index, 'source_frame': expected['frame'], 'boundary': boundary,
                            'field': fields[str(offset)], 'ram_offset': offset,
                            'expected': wanted[offset], 'actual': actual[offset]}
        expected_psg = bytes(expected['psg'])
        if actual_psg != expected_psg:
            return {'update': index, 'source_frame': expected['frame'], 'field': 'ordered PSG events',
                    'expected': expected_psg.hex(), 'actual': actual_psg.hex()}
    return None


def execute(config, mutation=False):
    executable = OUT / ('serve-mutated' if mutation else 'serve')
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', action='store_true', help='Also verify detection of a temporary gameplay mutation')
    args = parser.parse_args()
    case = json.loads((ROOT / 'tests/cases/serve.json').read_text())
    if case['updates'] != 200:
        raise ValueError('This serve harness currently runs exactly 200 updates')
    if case['refresh_bit'] != 0:
        raise ValueError('This harness currently supports only refresh bit zero')
    reference = ROOT / case['reference']
    if not reference.exists():
        raise FileNotFoundError(f'{reference}: run python scripts/capture_test_reference.py once')
    fixture = json.loads(reference.read_text())
    if not fixture['repeat_identical']:
        raise ValueError('Reference determinism has not been established')
    if fixture['rom_sha256'] != ROM_SHA256 or len(fixture['updates']) != case['updates']:
        raise ValueError('Wrong reference revision or callback count')
    if [row['frame'] for row in fixture['updates']] != list(range(case['first_frame'], case['first_frame'] + case['updates'])):
        raise ValueError('Reference callback sequence is incomplete')
    fields = json.loads((ROOT / 'tests/state-fields.json').read_text())['bytes']
    config = configparser.ConfigParser(interpolation=None)
    config.read(ROOT / 'config.local.ini', encoding='utf-8')
    OUT.mkdir(parents=True, exist_ok=True)
    # Translation/extraction is shared with the live executable build. No Python
    # simulation runs here, and expected state is never generated from target code.
    run([sys.executable, 'scripts/roundtrip_rom.py'])
    prepare_gameplay()
    (OUT / 'initial-ram.bin').write_bytes(bytes.fromhex(fixture['initial_pre_tail']))
    inputs = bytearray(case['updates'])
    for segment in case['input']:
        for update in range(segment['from'], segment['through'] + 1):
            inputs[update - 1] = segment['game_bits']
    (OUT / 'inputs.bin').write_bytes(inputs)
    records, digest = execute(config)
    difference = compare(records, fixture, case, fields)
    report = {'case': case['name'], 'updates': case['updates'], 'bytes_compared_per_boundary': 254,
              'boundaries_per_update': 2,
              'psg_bytes_compared': sum(len(row['psg']) for row in fixture['updates']),
              'reference_sha256': hashlib.sha256(reference.read_bytes()).hexdigest(),
              'executable_sha256': digest, 'first_difference': difference, 'passed': difference is None}
    if args.self_test and difference is None:
        source = (ROOT / 'build/translation/player-frame-routines.s').read_text()
        anchor = 'ball_flight_update:\n'
        if source.count(anchor) != 1:
            raise ValueError('Mutation entry point missing')
        mutation_path = OUT / 'mutated-routines.s'
        mutation_path.write_text(source.replace(anchor, anchor + '\taddq.b #1,$35(a5)\n'))
        try:
            mutated, _ = execute(config, mutation=True)
            detected = compare(mutated, fixture, case, fields)
            report['mutation_first_difference'] = detected
            if detected is None:
                raise AssertionError('Gameplay mutation was not detected')
        finally:
            mutation_path.unlink(missing_ok=True)
            (OUT / 'serve-mutated').unlink(missing_ok=True)
    (OUT / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 1 if difference else 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, RuntimeError, FileNotFoundError, AssertionError) as error:
        print(f'REGRESSION ERROR: {error}', file=sys.stderr)
        sys.exit(2)
