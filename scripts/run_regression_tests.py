"""Run actual 68000 routines against a frozen, independent source oracle."""
import argparse
import configparser
import hashlib
import json
import re
import sys
from run_translated_prng_probe import ROOT, ASSEMBLER, run
from run_translated_player_frame_probe import prepare_gameplay, ROM_SHA256
from round_reference import validate_fixture, FOCUSED_CASES, MOVEMENT_CASES, CONTACT_CASES, EXTENSION_CASES
from phase_reference import CASES as PHASE_CASES, validate_phase
from evidence import tracked_call, compile_manifest

OUT = ROOT / 'build/tests'
SCORING_REPLAY_CASES = ('round-transition', 'deuce-sequence-phase',
    'one-player-round-lower-complete-phase', 'one-player-round-upper-complete-phase',
    'two-player-round-lower-complete-phase', 'two-player-round-upper-complete-phase',
    'two-player-resumed-serve-complete-phase', 'two-player-upper-resumed-serve-complete-phase')


def compare(records, fixture, case, fields):
    selected = case.get('compared_ram_offsets', list(range(256)))
    if not selected or len(selected) != len(set(selected)) or any(type(offset) is not int or not 0 <= offset < 256 for offset in selected):
        raise ValueError('Invalid RAM observation fields')
    offsets = set(case.get('compared_ram_offsets', range(256))) - set(case['excluded_ram_offsets'])
    if not offsets:
        raise ValueError('RAM observation excludes every selected field')
    exact = fixture.get('schema_version') == 2
    stride = 5 if exact else 3
    expected_records = 2 + stride * case['updates']
    if len(records) != expected_records:
        raise ValueError(f'Expected {expected_records} native records, received {len(records)}')
    if len(records[0]) != 256 or len(bytes.fromhex(fixture['initial_post_tail'])) != 256:
        raise ValueError('Incomplete initial state record')
    for offset, (actual, expected) in enumerate(zip(records[0], bytes.fromhex(fixture['initial_post_tail']))):
        if offset in offsets and actual != expected:
            return {'update': 0, 'boundary': 'initial-post-tail', 'ram_offset': offset,
                    'field': fields[str(offset)], 'expected': expected, 'actual': actual}
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
                if offset not in offsets:
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


def execute(config, case_name='serve', mutation=False, subject='translated'):
    executable = OUT / (case_name + ('-mutated' if mutation else ''))
    command = [str(ASSEMBLER), '-Fhunkexe', '-kick1hunks', '-m68000']
    if subject == 'maintained':
        command.append('-DPRODUCT_REPLAY=1')
    if mutation:
        command.append('-DREGRESSION_MUTATION=1')
    # Case-owned fixture paths keep another replay from invalidating this executable.
    harness = ROOT / 'amiga/tests/simulation_harness.s'
    source = harness.read_text()
    directory = OUT / (case_name + '-inputs')
    for name in ('harness-config.i', 'initial-ram.bin', 'inputs.bin', 'refresh-values.bin'):
        source = source.replace('build/tests/' + name, str((directory / name).relative_to(ROOT)))
    wrapper = directory / 'simulation_harness.s'
    wrapper.write_text(source)
    run(command + ['-L', str(executable) + '.lst', '-o', str(executable), str(wrapper)])
    compile_manifest(executable, str(executable) + '.lst')
    log = run([config['tools']['copperline'], '--factory', '--model', 'A500', '--chipset', 'OCS',
               '--video', 'PAL', '--cpu', '68000', '--chip', '512K', '--slow', '0', '--fast', '0',
               '--noaudio', '--run', str(executable), '--exit-on-return', config['inputs']['amiga_rom']], timeout=360)
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
    if not 0 < count <= 65535:
        raise ValueError('Replay exceeds this harness input-index range')
    initial = bytes.fromhex(fixture['initial_pre_tail'])
    if len(initial) != 256:
        raise ValueError('Invalid initial RAM extent')
    directory = OUT / (case['name'] + '-inputs')
    directory.mkdir(parents=True, exist_ok=True)
    (directory / 'initial-ram.bin').write_bytes(initial)
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
        (directory / 'refresh-values.bin').write_bytes(refresh)
    else:
        for segment in case['input']:
            for update in range(segment['from'], min(segment['through'], count) + 1):
                inputs[2 * (update - 1)] = segment['game_bits']
    (directory / 'inputs.bin').write_bytes(inputs)
    (directory / 'harness-config.i').write_text(
        f'CASE_UPDATE_COUNT equ {count}\nCASE_CAPTURE_REFRESH equ {int(exact)}\n')


def _main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--subject', choices=('maintained', 'translated'),
                        help='Default: maintained for migrated CT-04 cases, translated for lifecycle diagnostics')
    parser.add_argument('--self-test', action='store_true', help='Also verify detection of a temporary gameplay mutation')
    parser.add_argument('--case', choices=('serve', 'round-transition', 'one-player-match', 'two-player-match') + PHASE_CASES + FOCUSED_CASES, default='serve')
    parser.add_argument('--reference-only', action='store_true', help='Validate and prepare the round reference without running the port')
    parser.add_argument('--through-update', type=int,
                        help='Run a declared prefix through this update; report that the full replay was not executed')
    args = parser.parse_args()
    from movement_reference import MOVEMENT_PHASES
    product_cases = ('serve', 'resumed-play-phase', 'two-player-rally',
                     'one-player-upper-resumed-serve-complete-phase') + MOVEMENT_CASES + tuple(MOVEMENT_PHASES) + CONTACT_CASES
    # Continuous lower-receiver prefixes still cross the CT-05 round boundary.
    # Keep those raw translator diagnostics separately selectable and unchanged.
    migrated_cases = tuple(name for name in product_cases
                           if not name.startswith('movement-lower-receiver-') or name.endswith('-phase'))
    subject = args.subject or ('maintained' if args.case in migrated_cases + SCORING_REPLAY_CASES else 'translated')
    if subject == 'maintained' and args.case not in product_cases + ('round-transition', 'deuce-sequence-phase', 'one-player-match', 'two-player-match', 'one-player-round-lower-complete-phase', 'one-player-round-upper-complete-phase', 'two-player-round-lower-complete-phase', 'two-player-round-upper-complete-phase', 'two-player-resumed-serve-complete-phase', 'two-player-upper-resumed-serve-complete-phase'):
        parser.error('This lifecycle case is not yet migrated to maintained replay')
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
        from movement_reference import MOVEMENT_PHASES
        if args.case in MOVEMENT_CASES or args.case in MOVEMENT_PHASES:
            from movement_reference import validate_movement
            reference_summary.update(validate_movement(fixture, case))
        if args.case == 'two-player-rally':
            from rally_reference import validate_rally
            reference_summary.update(validate_rally(fixture, case))
        if args.case in CONTACT_CASES:
            from contact_reference import validate_contact
            reference_summary.update(validate_contact(fixture, case))
        if args.case in EXTENSION_CASES:
            from regime_reference import validate_extension
            reference_summary.update(validate_extension(fixture, case))
        case['updates'] = len(fixture['updates'])
    elif args.reference_only:
        parser.error('--reference-only applies to the round-transition case')
    elif case['refresh_bit'] != 0:
        raise ValueError('The serve reference assumes refresh bit zero')
    if fixture['rom_sha256'] != ROM_SHA256 or len(fixture['updates']) != case['updates']:
        raise ValueError('Wrong reference revision or callback count')
    reference_count = case['updates']
    if not exact and [row['frame'] for row in fixture['updates']] != list(range(case['first_frame'], case['first_frame'] + case['updates'])):
        raise ValueError('Reference callback sequence is incomplete')
    if args.through_update is not None:
        if not 1 <= args.through_update <= reference_count:
            raise ValueError('Requested prefix is outside the retained reference')
        case['updates'] = args.through_update
        fixture = {**fixture, 'updates': fixture['updates'][:args.through_update]}
    fields = json.loads((ROOT / 'tests/state-fields.json').read_text())['bytes']
    if subject == 'maintained':
        # Temporary arithmetic scratch is not native game state. Keep raw
        # translator diagnostics exact; product observations omit only scratch.
        case['excluded_ram_offsets'] = sorted(set(case['excluded_ram_offsets']) | set(range(0x67,0x6b)))
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
    from build_native_game import module_hashes
    maintained_before = module_hashes()
    # Regeneration must only write ignored oracle outputs.
    prepare_gameplay()
    if module_hashes() != maintained_before:
        raise AssertionError('Reference regeneration changed maintained source')
    records, digest = execute(config, case['name'], subject=subject)
    difference = compare(records, fixture, case, fields)
    report = {'subject': subject,
              'entry_point': 'game_source_tick' if subject == 'maintained' else 'fixed translated sequence',
              'native_modules': maintained_before if subject == 'maintained' else {},
              'regeneration_preserved_native_modules': True,
              'case': case['name'], 'updates': case['updates'],
              'reference_updates': reference_count,
              'full_replay_executed': case['updates'] == reference_count,
              'omitted_legacy_scratch_offsets': list(range(0x67,0x6b)) if subject == 'maintained' else [],
              'bytes_compared_per_boundary': len(set(case.get('compared_ram_offsets', range(256))) - set(case['excluded_ram_offsets'])),
              'boundaries_per_update': 3 if exact else 2,
              'reference_psg_bytes': sum(len(row['psg']) for row in fixture['updates']),
              'reference_sha256': hashlib.sha256(reference.read_bytes()).hexdigest(),
              'executable_sha256': digest, 'first_difference': difference, 'passed': difference is None}
    matched = case['updates'] if difference is None else max(0, difference['update'] - 1)
    report['updates_matched'] = matched
    report['psg_bytes_compared_in_matched_updates'] = sum(len(row['psg']) for row in fixture['updates'][:matched])
    if args.self_test and difference is None and subject == 'maintained':
        # The resumed case must detect the repaired late launch, not only an
        # earlier dispatcher failure. Other cases retain the CT-01 smoke fault.
        late_launch = args.case == 'resumed-play-phase'
        path = ROOT / ('amiga/game/gameplay_math.s' if late_launch else 'amiga/game/tick.s')
        original = path.read_bytes()
        anchor = (b'        move.w  d1,d0\n        rts' if late_launch
                  else b'        bsr     legacy_active_tick')
        if original.count(anchor) != 1:
            raise ValueError('Maintained dispatcher mutation anchor is ambiguous')
        try:
            replacement = (b'        move.w  d1,d0\n        addq.w  #1,d0\n        rts'
                           if late_launch else b'        nop')
            path.write_bytes(original.replace(anchor, replacement))
            mutated, mutant_digest = execute(config, case['name'], mutation=True, subject=subject)
            detected = compare(mutated, fixture, case, fields)
            report['mutation_kind'] = ('increment native launch root' if late_launch
                                       else 'skip maintained active dispatcher')
            report['mutation_executable_sha256'] = mutant_digest
            report['mutation_first_difference'] = detected
            if detected is None or mutant_digest == digest:
                raise AssertionError('Maintained gameplay fault was not detected')
            if late_launch and detected['update'] != 96:
                raise AssertionError('Native launch fault did not expose the repaired update 96')
        finally:
            path.write_bytes(original)
            restored, restored_digest = execute(config, case['name'], subject=subject)
            if restored_digest != digest or compare(restored, fixture, case, fields) is not None:
                raise AssertionError('Restored maintained replay did not pass identically')
            report['restored_replay_passed'] = True
    elif args.self_test and difference is None:
        from movement_reference import OBSERVED_BOUNDS, MOVEMENT_PHASES, DIRECTIONS
        mutation_case = MOVEMENT_PHASES.get(args.case, args.case)
        source = (ROOT / 'build/translation/player-frame-routines.s').read_text()
        mutation_player = OBSERVED_BOUNDS.get(mutation_case, {}).get('player', 'upper')
        anchor = (('lower_player_motion_update:\n' if mutation_player == 'lower' else 'upper_player_movement:\n')
                  if mutation_case in OBSERVED_BOUNDS else
                  'lower_player_motion_update:\n' if args.case in MOVEMENT_CASES else 'ball_flight_update:\n')
        if source.count(anchor) != 1:
            raise ValueError('Mutation entry point missing')
        mutation_path = OUT / 'mutated-routines.s'
        if mutation_case in OBSERVED_BOUNDS:
            contract = OBSERVED_BOUNDS[mutation_case]
            coordinate, limit = contract['coordinate'], contract['limit']
            operator = 'addq' if DIRECTIONS[contract['direction']][2] > 0 else 'subq'
            animation = 0x43 if mutation_player == 'lower' else 0x44
            row_start = contract.get('row', 2) << 5
            direction_shift = 4 if (contract['mode'] ^ (16 if mutation_player == 'upper' else 0)) & 16 else 0
            direction_bit = DIRECTIONS[contract['direction']][0].bit_length() - 1 + direction_shift
            mutation = (f'\tcmpi.b #{row_start},${animation:x}(a5)\n\tblo.s regression_receiver_mutation_skip\n'
                        f'\tcmpi.b #{row_start + 32},${animation:x}(a5)\n\tbhs.s regression_receiver_mutation_skip\n'
                        f'\tbtst #{direction_bit},$53(a5)\n\tbeq.s regression_receiver_mutation_skip\n'
                        f'\tcmpi.b #{limit},${coordinate:x}(a5)\n\tbne.s regression_receiver_mutation_skip\n'
                        f'\t{operator}.b #1,${coordinate:x}(a5)\nregression_receiver_mutation_skip:\n')
        else:
            coordinate = ('$60' if case.get('regime') == 'launched-serve' else
                          '$4a' if args.case in MOVEMENT_CASES else '$35')
            mutation = f'\taddq.b #1,{coordinate}(a5)\n'
        if args.case in CONTACT_CASES:
            # Change the action choice only at the captured contact geometry;
            # preserve the original CCR and stack on every other path.
            gate = '\tbeq\tupper_contact_finish_launch\t\t; [jr z,upper_contact_finish_launch]'
            if source.count(gate) != 1:
                raise ValueError('Upper contact action gate missing or ambiguous')
            player_y, player_x = reference_summary['contact_entry_player_yx']
            ball_y = reference_summary['contact_entry_ball_yx'][0]
            replacement = ('\tmove.w sr,-(sp)\n'
                           f'\tcmpi.b #{ball_y},$34(a5)\n\tbne.s regression_contact_original_gate\n'
                           f'\tcmpi.b #{player_y},$45(a5)\n\tbne.s regression_contact_original_gate\n'
                           f'\tcmpi.b #{player_x},$46(a5)\n\tbne.s regression_contact_original_gate\n'
                           '\tmove.w (sp)+,ccr\n\tbne upper_contact_finish_launch\n'
                           '\tbra upper_contact_apply_action_trajectory\n'
                           'regression_contact_original_gate:\n'
                           '\tmove.w (sp)+,ccr\n\tbeq upper_contact_finish_launch')
            mutated_source = source.replace(gate, replacement)
            report['mutation_kind'] = 'invert upper contact action trajectory gate'
        else:
            mutated_source = source.replace(anchor, anchor + mutation)
        mutation_path.write_text(mutated_source)
        try:
            mutated, _ = execute(config, case['name'], mutation=True)
            detected = compare(mutated, fixture, case, fields)
            report['mutation_first_difference'] = detected
            if detected is None:
                raise AssertionError('Gameplay mutation was not detected')
            if args.case in CONTACT_CASES and detected['update'] != case['contact_timing']['contact_update']:
                raise AssertionError('Action mutation did not first diverge at the intended contact')
        finally:
            mutation_path.unlink(missing_ok=True)
            (OUT / (case['name'] + '-mutated')).unlink(missing_ok=True)
    if exact:
        report['reference_coverage'] = reference_summary
        report['port_limit'] = ('Native scoring/round lifecycle; presentation/audio adapters and result/restart remain'
                                if subject == 'maintained' else
                                'Translated diagnostic executes gameplay every tick; no native round main path')
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


def native_replay_cases():
    from movement_reference import MOVEMENT_PHASES
    cases = ('serve', 'resumed-play-phase', 'two-player-rally',
             'one-player-upper-resumed-serve-complete-phase') + MOVEMENT_CASES + tuple(MOVEMENT_PHASES) + CONTACT_CASES
    return tuple(n for n in cases if not n.startswith('movement-lower-receiver-') or n.endswith('-phase'))


def main():
    if '--help' in sys.argv or '--reference-only' in sys.argv:
        return _main()
    probe = argparse.ArgumentParser(add_help=False)
    probe.add_argument('--case', default='serve')
    probe.add_argument('--subject')
    selected, _ = probe.parse_known_args()
    case = selected.case
    if not re.fullmatch(r'[a-z0-9-]+', case):
        return _main()
    subject = selected.subject or ('maintained' if case in native_replay_cases() + SCORING_REPLAY_CASES else 'translated')
    path = OUT / ('report.json' if case == 'serve' else case + '-report.json')
    return tracked_call([path], 'replay', subject, 'captured phase',
                        'scripts/run_regression_tests.py', case, _main,
                        lambda path, report: [OUT / case])


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, RuntimeError, FileNotFoundError, AssertionError) as error:
        print(f'REGRESSION ERROR: {error}', file=sys.stderr)
        sys.exit(2)
