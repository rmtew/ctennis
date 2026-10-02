"""Bounded one-time native starts through the application's actual dispatcher.

Independent retained scoring tuples and status durations, no source memory,
intermediate state writes or expected values computed by another game model.
These local fixtures are separate from ordinary lifecycle/cadence acceptance.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
from build_native_game import build
from native_tools import ROOT, ASSEMBLER, run as assemble, emulator_config
from native_observation import code_symbols, target_log
from copperline_test_session import NativeControlSession
from native_evidence import atomic_json, compile_manifest, tracked_call

# Native scoring encodes deuce5/5 and advantage4/6. These tuples were retained
# from accepted deuce/advantage contracts before deletion, not replay output.
SCORING = {
    'deuce': ([2, 3], [1, 2], 0x82, [5, 5], [1, 2]),
    'advantage': ([5, 5], [1, 2], 0x82, [4, 6], [1, 2]),
    'return-deuce': ([4, 6], [1, 2], 0xc2, [5, 5], [1, 2]),
    'advantage-game': ([4, 6], [1, 2], 0x82, [0, 0], [2, 2]),
    'match-award': ([3, 0], [5, 2], 0x82, [0, 0], [6, 2]),
}


def run(case, mutant=False):
    config = emulator_config()
    _, normal = build()
    directory = ROOT / 'build/tests/native-contracts' / case
    if mutant:
        directory = directory / ('mutant-' + str(mutant))
    directory.mkdir(parents=True, exist_ok=True)
    source = (ROOT / 'amiga/main.s').read_text()
    startup = '        bsr     game_begin_title'
    if source.count(startup) != 1:
        raise ValueError('Native fixture startup marker changed')
    init = '        moveq #1,d0\n        bsr game_new_match\n        bsr game_begin_active\n        move.b #$40,game_score_flags\n'
    if case in SCORING:
        points, games, outcome, expected_points, expected_games = SCORING[case]
        init += ''.join(f'        move.b #{v},{name}\n' for name, v in zip(
            ('game_point_a', 'game_point_b', 'game_games_a', 'game_games_b', 'game_contact'),
            (*points, *games, outcome)))
    elif case == 'audio-hit':
        init += '        bsr game_audio_request_hit\n'
    else:
        status = int(case.removeprefix('status-'))
        if status not in (2, 3, 4, 5):
            raise ValueError('Unknown native contract')
        init += f'        move.b #{128 | status},game_display\n        move.b #224,game_status_clock\n'
    fixture = directory / 'fixture.s'
    source = source.replace(startup, init)
    if mutant:
        if case == 'audio-hit':
            marker = '        include "amiga/game/paula_output.s"'
            fault = (ROOT / 'amiga/game/paula_output.s').read_text()
            if mutant == 'pitch':
                fault = fault.replace('game_audio_write_period:', 'game_audio_write_period:\n        addq.w #1,d0')
            else:
                fault = fault.replace('game_audio_write_level:', 'game_audio_write_level:\n        moveq #0,d0')
            fault_path = directory / 'fault-paula.s'; fault_path.write_text(fault)
            source = source.replace(marker, f'        include "{fault_path}"')
        else:
            marker = 'game_scene_present_fields:\n'
            if source.count(marker) != 1:
                raise ValueError('Native renderer control marker changed')
            threshold = 31 if case.startswith('status-') else 1
            field = 'field_values+4' if case.startswith('status-') else 'field_values'
            value = 2 if case.startswith('status-') else 0
            source = source.replace(marker, marker + f'        cmpi.w #{threshold},simulation_updates\n        bcs.s contract_fault_wait\n        move.b #{value},{field}\ncontract_fault_wait:\n')
    fixture.write_text(source)
    executable, listing = directory / 'native-fixture', directory / 'native.lst'
    assemble([str(ASSEMBLER), '-Fhunkexe', '-kick1hunks', '-m68000', '-L', str(listing),
              '-o', str(executable), str(fixture)])
    compile_manifest(executable, listing)
    symbols = code_symbols(listing.read_text())
    checks = []
    with NativeControlSession(directory) as session:
        session.inspect('session_launch', {'binary': config['tools']['copperline'], 'run': str(executable),
            'args': ['--chipset', 'OCS', '--video', 'PAL', '--cpu', '68000', '--chip', '512K',
                     '--slow', '0', '--fast', '0', '--noaudio', *(['--audio-wav', str(directory/'native.wav')] if case=='audio-hit' else []), config['inputs']['amiga_rom']]})
        stop = session.inspect('run_until', {'seconds': 30})
        if stop['reason'] != 'loadseg':
            raise RuntimeError(stop)
        base = int(re.search(r'first hunk \$([0-9a-fA-F]+)', stop['detail'])[1], 16)
        def read(name, size=1):
            return list(bytes.fromhex(session.inspect('mem_read', {'addr': base+symbols[name], 'len': size})['data']))
        def check(label, actual, expected):
            checks.append({'label': label, 'actual': actual, 'expected': expected})
            if actual != expected:
                raise AssertionError(checks[-1])
        session.inspect('run_until', {'pc': base + symbols['main_loop']})
        pc = base + symbols['game_scene_service' if case=='audio-hit' else 'game_observe_pre_tail']
        session.inspect('break_add', {'kind': 'pc', 'addr': pc})
        seen = []
        for tick in range(34 if case.startswith('status-') else 20 if case=='audio-hit' else 3):
            stop = session.inspect('run_until', {'seconds': 60})
            if stop['pc'] != pc:
                raise RuntimeError(stop)
            points = read('game_point_a', 2)
            games = read('game_games_a', 2)
            field = read('field_values', 6)
            seen.append({'tick': tick+1, 'points': points, 'games': games, 'fields': field,
                         'status_clock': read('game_status_clock')[0]})
            if case in SCORING:
                check('native points at actual dispatcher boundary', points, expected_points)
                check('native games at actual dispatcher boundary', games, expected_games)
                if tick >= 1:
                    check('render point/game fields follow scorer', field[:4], expected_points+expected_games)
                if case == 'match-award':
                    check('match bit follows sixth logical game', read('game_mode')[0] & 64, 64)
            elif case == 'audio-hit':
                regs = session.inspect('custom_dump')['regs']
                if tick >= 1:
                    check('native hit pitch at actual Paula channel3', regs['AUD3PER'], 1688)
                if tick in (1,2):
                    check('native hit envelope at actual Paula channel3', regs['AUD3VOL'], 64 if tick==1 else 51)
                seen[-1].update(seconds=stop['seconds'], period=regs['AUD3PER'], volume=regs['AUD3VOL'])
            else:
                check('status visible until native saturation expiry', field[4], status if tick < 31 else 0)
            session.inspect('step', {'count': 1})
        session.inspect('capture_screenshot', {'path': str(directory / 'final.png')})
    target_log(directory)
    if case == 'audio-hit':
        from native_audio_checks import pcm16_window
        audible = pcm16_window(directory/'native.wav', seen[1]['seconds'] + .002, .005)
        check('native hit emitted audible signal', any(row['nonzero_pcm16_samples'] for row in audible['channels']), True)
    report = {'passed': True, 'case': case, 'checks': checks, 'observations': seen,
              'executable_sha256': hashlib.sha256(executable.read_bytes()).hexdigest(),
              'fixture_initialization': 'once at native startup; subsequent actual dispatcher ticks, no state writes',
              'scope': 'Local native scoring/status/render-field contracts, not uninterrupted ordinary play'}
    atomic_json(directory / 'report.json', report)
    print(case, 'PASS', len(checks), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=(*SCORING, 'status-2', 'status-3', 'status-4', 'status-5', 'audio-hit'), required=True)
    parser.add_argument('--self-test', action='store_true', help='One compiled late field fault at unchanged normal checkpoints')
    args = parser.parse_args()
    path = ROOT / 'build/tests/native-contracts' / args.case / 'report.json'
    def action():
        run(args.case)
        if args.self_test:
            report = json.loads(path.read_text())
            controls = []
            for mutation in ('pitch','envelope') if args.case=='audio-hit' else (True,):
                try:
                    run(args.case, mutant=mutation)
                except AssertionError as error:
                    detail = error.args[0]
                    wanted = ('native hit pitch at actual Paula channel3' if mutation=='pitch' else
                              'native hit envelope at actual Paula channel3') if args.case=='audio-hit' else (
                              'status visible until native saturation expiry' if args.case.startswith('status-') else
                              'render point/game fields follow scorer')
                    if not isinstance(detail, dict) or detail.get('label') != wanted:
                        raise
                    controls.append({'detected': True, 'failure': detail,
                        'artifact_directory': str((path.parent / ('mutant-'+str(mutation))).relative_to(ROOT)),
                        'executable_sha256': hashlib.sha256((path.parent / ('mutant-'+str(mutation)) / 'native-fixture').read_bytes()).hexdigest()})
                else:
                    raise AssertionError('Compiled native fault escaped')
            report['compiled_fault_controls'] = controls
            atomic_json(path, report)
    tracked_call([path], 'native-contract', 'maintained-native', 'one-time native fixture',
                 'scripts/run_native_contracts.py', None, action,
                 lambda path, report: [path.parent / 'native-fixture'])
