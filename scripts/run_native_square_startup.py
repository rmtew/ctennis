"""Measure the actual one-time LED startup and verify all generated strip bytes.

Uses the ordinary product entry, not a rewritten game or injected RAM state.
A second compiled executable moves the advantage glyph one pixel and must be
rejected by the frozen, user-selected preview contract.
"""
import argparse
import hashlib
import re
from pathlib import Path
from build_native_game import build
from copperline_test_session import NativeControlSession
from native_evidence import atomic_json, compile_manifest, tracked_call
from native_hunk import loaded_hunks
from native_observation import target_log
from native_square_scores import assert_generated_point_banks
from native_tools import ROOT, ASSEMBLER, emulator_config, run as assemble


def inspect_startup(executable, listing, directory):
    locations = {name: (int(hunk), int(offset, 16)) for name,hunk,offset in
                 re.findall(r'^([A-Za-z_][\w]*)\s+(\d\d):([0-9A-Fa-f]{8})\s*$', listing.read_text(), re.M)}
    config = emulator_config()
    with NativeControlSession(directory) as session:
        session.inspect('session_launch', {'binary': config['tools']['copperline'], 'run': str(executable),
            'args': ['--chipset', 'OCS', '--video', 'PAL', '--cpu', '68000', '--chip', '512K',
                     '--slow', '0', '--fast', '0', '--noaudio', config['inputs']['amiga_rom']]})
        stop = session.inspect('run_until', {'seconds': 30})
        if stop['reason'] != 'loadseg':
            raise RuntimeError(stop)
        segments = session.inspect('segments.list')['current']
        def raw(address, length):
            return bytes.fromhex(session.inspect('mem_read', {'addr': address, 'len': length})['data'])
        def located(name):
            hunk,offset = locations[name]
            return segments[hunk]['start']+offset
        loaded = loaded_hunks(executable, segments, raw)
        begin = session.inspect('run_until', {'pc': located('init_square_score_banks')})
        finish = session.inspect('run_until', {'pc': located('init_square_score_banks_end')})
        checks = assert_generated_point_banks(raw, located)
        expected = b''.join((ROOT/f'assets/native/court/plane{p}.bin').read_bytes()[48*32:64*32]
                            for p in (0,2,3)) + (ROOT/'assets/native/court/plane1.bin').read_bytes()[72*32:120*32]
        for bank in range(3):
            if raw(located(f'hud_bank{bank}'),len(expected)) != expected:
                raise AssertionError('Initial HUD strip copy differs from unchanged court')
        if raw(located('simulation_timer_running'), 1) != b'\0':
            raise AssertionError('Score construction must precede the game timer')
        # The ordinary initialized title must still be reached after construction.
        session.inspect('run_until', {'pc': located('main_loop')})
        if raw(located('simulation_timer_running'), 1) != b'\xff':
            raise AssertionError('Ordinary startup failed to start the timer')
        photo = directory/'ordinary-title.png'
        session.inspect('run_until', {'seconds': finish['seconds']+.25})
        session.inspect('capture_screenshot', {'path': str(photo)})
    target_log(directory)
    return {'passed': True, 'generated_banks': checks, 'loaded_hunks': loaded,
            'constructor_seconds': finish['seconds']-begin['seconds'],
            'timing_scope': 'init_square_score_banks entry through end label before RTS; emulated elapsed time, including active OS display DMA',
            'constructor_entry': begin, 'constructor_end': finish,
            'hunk_payload_bytes': sum(row['bytes'] for row in loaded),
            'executable_bytes': executable.stat().st_size,
            'executable_sha256': hashlib.sha256(executable.read_bytes()).hexdigest(),
            'title_capture': str(photo.relative_to(ROOT))}


def run(self_test):
    _, executable = build(flavor='enhanced')
    directory = ROOT/'build/tests/native-square-startup'
    directory.mkdir(parents=True, exist_ok=True)
    report = inspect_startup(executable, executable.with_name('native.lst'), directory)
    if self_test:
        fault_dir = directory/'wrong-advantage-position'
        fault_dir.mkdir(exist_ok=True)
        source = (ROOT/'amiga/square_score_banks.i').read_text()
        marker = 'moveq   #4,d4 ; one centred A, not Ad'
        if source.count(marker) != 1:
            raise ValueError('Advantage position fault marker changed')
        fault_include = fault_dir/'square_score_banks.i'
        fault_include.write_text(source.replace(marker, 'moveq   #5,d4 ; deliberately wrong position'))
        source = (ROOT/'amiga/main.s').read_text()
        source = source.replace('include "amiga/square_score_banks.i"', f'include "{fault_include}"')
        fault_source = fault_dir/'fixture.s'
        fault_source.write_text(source)
        fault_exe, fault_listing = fault_dir/'native-mutant', fault_dir/'native.lst'
        assemble([str(ASSEMBLER), '-Fhunkexe', '-kick1hunks', '-m68000', '-DENHANCED_INTERFACE=1',
                  '-L', str(fault_listing), '-o', str(fault_exe), str(fault_source)])
        compile_manifest(fault_exe, fault_listing)
        try:
            inspect_startup(fault_exe, fault_listing, fault_dir)
        except AssertionError as error:
            detail = error.args[0]
            if not isinstance(detail, dict) or detail.get('label') != 'startup banks match selected square preview':
                raise
            report['compiled_fault_control'] = {'detected': True, 'failure': detail,
                'executable_sha256': hashlib.sha256(fault_exe.read_bytes()).hexdigest()}
        else:
            raise AssertionError('Wrong advantage position escaped independent preview comparison')
    atomic_json(directory/'report.json', report)
    print(f"All6 LED tiles match selected preview; startup {report['constructor_seconds']*1000:.3f}ms", flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    path = ROOT/'build/tests/native-square-startup/report.json'
    tracked_call([path], 'native-square-startup', 'maintained-native', 'ordinary startup',
                 'scripts/run_native_square_startup.py', None, lambda: run(args.self_test),
                 lambda path, report: [ROOT/'build/amiga/interfaces/enhanced/baseline-rally'])
