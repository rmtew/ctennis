"""Finite native scoreboard starts, actual scanout and both published Copper banks.

Fixture initialization is compiled once before the normal dispatcher. No
intermediate RAM writes, injected outcomes or regenerated pixel expectations.
"""
import argparse
import hashlib
import json
import re
import struct

from build_native_game import build
from copperline_test_session import NativeControlSession
from native_evidence import atomic_json, compile_manifest, tracked_call
from native_observation import code_symbols, target_log
from native_tools import ROOT, ASSEMBLER, emulator_config, run as assemble
from native_scoreboard_raster import assert_scoreboard_raster


def run_case(variant, two, exchanged, mutant=False):
    points = [variant, 6-variant]
    games = [variant, 6-variant]
    directory = ROOT / 'build/tests/native-scoreboard' / f'{variant}-{int(two)}-{int(exchanged)}'
    if mutant:
        directory /= 'wrong-tally-pointer'
    directory.mkdir(parents=True, exist_ok=True)
    source = (ROOT/'amiga/main.s').read_text()
    marker = '        bsr     game_begin_title'
    if source.count(marker) != 1:
        raise ValueError('Native fixture startup marker changed')
    mode = (128 if two else 0) | (16 if exchanged else 0)
    ai = 0 if two else 2 if exchanged else 1
    init = f'        moveq #{int(two)},d0\n        bsr game_new_match\n        bsr game_begin_active\n'
    for name, value in zip(('game_mode', 'game_score_flags', 'game_point_a', 'game_point_b',
                            'game_games_a', 'game_games_b'), (mode, 64|ai, *points, *games)):
        init += f'        move.b #{value},{name}\n'
    init += '        bsr game_scene_build_players\n'
    source = source.replace(marker, init)
    if mutant:
        tables = (ROOT/'assets/native/court/score-patch-tables.i').read_text()
        for plane in range(4):
            tables = tables.replace(f'score_bank_games_a_6_p{plane}', f'score_bank_games_a_0_p{plane}')
        fault = directory/'wrong-tally-tables.i'
        fault.write_text(tables)
        marker = '        include "assets/native/court/score-patch-tables.i"'
        if source.count(marker) != 1:
            raise ValueError('Native scoreboard table marker changed')
        source = source.replace(marker, f'        include "{fault}"')
    fixture = directory/'fixture.s'
    fixture.write_text(source)
    executable, listing = directory/'native-fixture', directory/'native.lst'
    assemble([str(ASSEMBLER), '-Fhunkexe', '-kick1hunks', '-m68000', '-DENHANCED_INTERFACE=1',
              '-L', str(listing), '-o', str(executable), str(fixture)])
    compile_manifest(executable, listing)
    symbols = code_symbols(listing.read_text())
    locations = {name: (int(hunk), int(offset, 16)) for name, hunk, offset in
                 re.findall(r'^([A-Za-z_][\w]*)\s+(\d\d):([0-9A-Fa-f]{8})\s*$', listing.read_text(), re.M)}
    checks, raster, publications, pointer_checks = [], [], [], []
    def check(label, actual, expected):
        row = {'label': label, 'actual': actual, 'expected': expected}
        checks.append(row)
        if actual != expected:
            raise AssertionError(row)
    config = emulator_config()
    with NativeControlSession(directory) as session:
        session.inspect('session_launch', {'binary': config['tools']['copperline'], 'run': str(executable),
            'args': ['--chipset', 'OCS', '--video', 'PAL', '--cpu', '68000', '--chip', '512K',
                     '--slow', '0', '--fast', '0', '--noaudio', config['inputs']['amiga_rom']]})
        stop = session.inspect('run_until', {'seconds': 30})
        if stop['reason'] != 'loadseg':
            raise RuntimeError(stop)
        base = int(re.search(r'first hunk \$([0-9a-fA-F]+)', stop['detail'])[1], 16)
        segments = session.inspect('segments.list')['current']
        def raw(address, length):
            return bytes.fromhex(session.inspect('mem_read', {'addr': address, 'len': length})['data'])
        def located(name):
            hunk, offset = locations[name]
            return segments[hunk]['start']+offset
        def read(name, length=1):
            return raw(base+symbols[name], length)
        from native_hunk import loaded_hunks
        loaded = loaded_hunks(executable, segments, raw)
        check('fixture loaded bytes match compiled hunks', bool(loaded) and all(row['matched'] for row in loaded), True)
        stop = session.inspect('run_until', {'pc': base+symbols['main_loop']})
        start_time = stop['seconds']
        association = {'fields': bytearray(read('prepared_field_values', 6)),
                       'back': bytearray(read('back_copper', 4)), 'cop': bytearray(4),
                       'started': int.from_bytes(read('simulation_started_updates', 2), 'big'), 'ready': None}
        def observe(message):
            if message.get('method') != 'event.mmio':
                return
            row = message['params']
            address, size, value = row['addr'], row['size'], row['value']
            if row.get('dropped_events', 0) or row.get('dropped_notifications', 0):
                raise AssertionError('Scoreboard publication telemetry lost')
            for name, buffer in [('prepared_field_values', 'fields'), ('back_copper', 'back')]:
                begin = base+symbols[name]
                if begin <= address and address+size <= begin+len(association[buffer]):
                    association[buffer][address-begin:address-begin+size] = value.to_bytes(size, 'big')
            if address == base+symbols['simulation_started_updates']:
                association['started'] = value
            if address == base+symbols['display_ready'] and value:
                association['ready'] = {'bank': int.from_bytes(association['back'], 'big'),
                    'generation': association['started'], 'fields': list(association['fields']), 'completed': False}
            if address == base+symbols['simulation_updates']:
                if association['ready'] and association['ready']['generation'] == value:
                    association['ready']['completed'] = True
            if 0xdff080 <= address and address+size <= 0xdff084:
                association['cop'][address-0xdff080:address-0xdff080+size] = value.to_bytes(size, 'big')
            if address == 0xdff088 and association['started']:
                ready = association['ready']
                pointer = int.from_bytes(association['cop'], 'big')
                check('published bank belongs to completed scoreboard scene',
                      bool(ready and ready['completed'] and ready['bank'] == pointer), True)
                publications.append(dict(ready, actual_pointer=pointer, position=row['position']))
        session.notification_handler = observe
        session.inspect('events.subscribe', {'events': ['mmio'], 'mmio': [
            {'addr': base+symbols[name], 'len': length, 'access': 'write'} for name, length in
            [('prepared_field_values', 6), ('back_copper', 4), ('simulation_started_updates', 2),
             ('simulation_updates', 2), ('display_ready', 1)]] + [
            {'addr': 0xdff080, 'len': 4, 'access': 'write'}, {'addr': 0xdff088, 'len': 2, 'access': 'write'}]})
        # Less than one second: normal gameplay ticks and bank preparation run,
        # while the initial serve has no physical action to award a point.
        for checkpoint, elapsed in enumerate((.35, .65)):
            stop = session.inspect('run_until', {'seconds': start_time+elapsed})
            check('actual point scalars remain initialized', list(read('game_point_a', 2)), points)
            check('actual tally scalars remain initialized', list(read('game_games_a', 2)), games)
            check('mode/end ownership remains initialized', read('game_mode')[0], mode)
            check('prepared scoreboard fields retain native selections', list(read('prepared_field_values', 4)), points+games)
            banks = sorted({row['actual_pointer'] for row in publications if row['fields'][:4] == points+games})
            check('both physical Copper banks published requested scoreboard', len(banks), 2)
            regs = session.inspect('custom_dump')['regs']
            actual_pointer = regs['COP1LCH']*65536+regs['COP1LCL']
            check('scanout pointer is a published selected bank', actual_pointer in banks, True)
            photo = directory/f'stable-{checkpoint}.png'
            session.inspect('capture_screenshot', {'path': str(photo)})
            try:
                result = assert_scoreboard_raster(photo, points, games)
            except AssertionError as error:
                # Normalize only a raster rejection, allowing the self-test to
                # distinguish it from scalar, pointer or telemetry failures.
                raise AssertionError({'label': 'independent native scoreboard raster', 'detail': str(error)}) from error
            raster.append({'screenshot': str(photo.relative_to(ROOT)), 'checkpoint': elapsed, 'result': result})
            fields = list(read('prepared_field_values', 6))
            count = int(re.search(r'SCORE_PATCH_COUNT equ (\d+)', (ROOT/'assets/native/court/score-patch-tables.i').read_text())[1])
            descriptors = raw(located('score_patch_descriptors'), count*14)
            entries = [struct.unpack_from('>IIIH', descriptors, index*14) for index in range(count)]
            table_begin = min(table for hi, lo, table, field in entries)
            table_end = max(table+4*(1 if field == 65535 else 7) for hi, lo, table, field in entries)
            tables = raw(table_begin, table_end-table_begin)
            copper_length = located('copperlist_end')-located('copperlist')
            for bank in banks:
                delta = bank-located('copperlist')
                copper = raw(bank, copper_length)
                for hi, lo, table, field in entries:
                    selection = 0 if field == 65535 else fields[field]
                    off = table-table_begin+4*selection
                    expected = int.from_bytes(tables[off:off+4], 'big')
                    high, low = hi+delta-bank, lo+delta-bank
                    actual = int.from_bytes(copper[high:high+2]+copper[low:low+2], 'big')
                    check('bank selected/restore plane pointer', actual, expected)
                pointer_checks.append({'bank': bank, 'checkpoint': elapsed, 'descriptors_checked': count})
        check('subsequent native ticks completed', int.from_bytes(read('simulation_updates', 2), 'big') > 3, True)
        check('no missed scoreboard publications', int.from_bytes(read('missed_presentation_deadlines', 2), 'big'), 0)
    target_log(directory)
    report = {'passed': True, 'points': points, 'games': games, 'two_players': two, 'exchanged': exchanged,
              'checks': checks, 'raster': raster, 'publications': publications, 'plane_pointers': pointer_checks,
              'loaded_hunks': loaded, 'executable_sha256': hashlib.sha256(executable.read_bytes()).hexdigest(),
              'fixture_initialization': 'compiled once at startup; subsequent native ticks; no intermediate RAM writes'}
    atomic_json(directory/'report.json', report)
    print(f'scoreboard {variant}/{int(two)}/{int(exchanged)} PASS', flush=True)
    return report


def run(self_test):
    build(flavor='enhanced')
    reports = [run_case(n, two, exchanged) for n in range(7)
               for two in (False, True) for exchanged in (False, True)]
    controls = []
    if self_test:
        try:
            run_case(6, False, False, mutant=True)
        except AssertionError as error:
            detail = error.args[0]
            if not isinstance(detail, dict) or detail.get('label') != 'independent native scoreboard raster':
                raise
            control_directory = ROOT/'build/tests/native-scoreboard/6-0-0/wrong-tally-pointer'
            controls.append({'detected': True, 'failure': detail, 'unchanged_tally': [6, 0],
                             'artifact_directory': str(control_directory.relative_to(ROOT)),
                             'executable_sha256': hashlib.sha256((control_directory/'native-fixture').read_bytes()).hexdigest()})
        else:
            raise AssertionError('Compiled wrong tally-pointer escaped independent raster assertion')
    report = {'passed': True, 'cases': reports, 'compiled_fault_controls': controls,
              'executable_sha256': reports[0]['executable_sha256'],
              'scope': 'All native point/tally variants, modes and ends; stable two-bank scanout; compiled fixture starts'}
    atomic_json(ROOT/'build/tests/native-scoreboard/report.json', report)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    path = ROOT/'build/tests/native-scoreboard/report.json'
    tracked_call([path], 'native-scoreboard', 'maintained-native', 'one-time native fixture',
                 'scripts/run_native_scoreboard_tests.py', None, lambda: run(args.self_test),
                 lambda path, report: list((path.parent).glob('*/native-fixture')))
