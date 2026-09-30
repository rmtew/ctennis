"""Associate native presentation observations with exact live simulation callbacks.

Diagnostic capture, not a P1 pass: screenshots at CPU stops can contain partial
rasters. This records actual state and beam position without changing game RAM
or bypassing the application's input, scheduling, or hardware paths.
"""
import configparser
import json
import re
from pathlib import Path

from copperline_test_session import CopperlineSession
from run_presentation_tests import ROOT, build_native, digest


def code_symbols(listing):
    return {name: int(offset, 16) for name, offset in
            re.findall(r'^([A-Za-z_][\w]*)\s+00:([0-9A-Fa-f]{8})\s*$', listing, re.M)}


def capture(targets=(0, 17, 18, 63, 134, 135, 136, 166)):
    config = configparser.ConfigParser(interpolation=None)
    config.read(ROOT / 'config.local.ini', encoding='utf-8')
    directory = ROOT / 'build/tests/native-presentation-alignment'
    directory.mkdir(parents=True, exist_ok=True)
    report_path = directory / 'report.json'
    report_path.unlink(missing_ok=True)
    case = json.loads((ROOT / 'tests/cases/p1-title.json').read_text())
    source_path = ROOT / 'tests/reference/one-player-match.json'
    source = json.loads(source_path.read_text())
    if list(targets) != sorted(set(targets)) or not targets or targets[0] < 0 or targets[-1] > len(source['updates']):
        raise ValueError('Callback targets must be unique, increasing and inside the source replay')
    executable = build_native(case, directory)
    symbols = code_symbols((directory / 'native.lst').read_text())
    observations = []
    ctl = Path(config['tools']['copperline']).with_name('copperline-ctl.exe')
    with CopperlineSession(ctl, ROOT) as session:
        launch = session.inspect('session_launch', {'factory': True, 'model': 'A500',
            'binary': config['tools']['copperline'], 'run': str(executable),
            'args': ['--chipset', 'OCS', '--video', 'PAL', '--cpu', '68000',
                     '--chip', '512K', '--slow', '0', '--fast', '0', '--noaudio',
                     config['inputs']['amiga_rom']]})
        stop = session.inspect('run_until', {'seconds': 30, 'wait_ms': 50000})
        if stop['reason'] != 'loadseg':
            raise RuntimeError(f'Application not loaded: {stop}')
        base = int(re.search(r'first hunk \$([0-9A-Fa-f]+)', stop['detail']).group(1), 16)
        session.inspect('input_set_port', {'port': 2, 'device': 'joystick'})
        session.inspect('input_joy', {'port': 2, 'red': True})
        for target in targets:
            breakpoint = session.inspect('break_add', {'kind': 'pc',
                'addr': base + symbols['simulation_update'],
                'cond': {'lhs': {'mem': base + symbols['simulation_updates']},
                         'op': 'eq', 'rhs': target}})
            stop = session.inspect('run_until', {'seconds': stop['seconds'] + 10, 'wait_ms': 50000})
            if stop['reason'] != 'breakpoint' or stop['pc'] != base + symbols['simulation_update']:
                raise RuntimeError(f'Callback target not reached: {target}: {stop}')
            count = int(session.inspect('mem_read', {'addr': base + symbols['simulation_updates'], 'len': 2})['data'], 16)
            if count != target:
                raise ValueError(f'Wrong completed callback count: {count} versus {target}')
            registers = session.inspect('regs_get')
            actual = bytes.fromhex(session.inspect('mem_read', {'addr': registers['a'][5], 'len': 256})['data'])
            expected = bytes.fromhex(source['initial_post_tail'] if target == 0 else source['updates'][target - 1]['post_tail_ram'])
            differences = [{'offset': offset, 'expected': expected[offset], 'actual': actual[offset]}
                           for offset in range(2, 256) if actual[offset] != expected[offset]]
            capture = session.inspect('capture_screenshot', {'path': str(directory / f'callback-{target:05d}.png')})
            observations.append({'completed_callbacks': count, 'stop': stop,
                'ram': actual.hex(), 'state_differences': differences, 'capture': capture,
                'display_ready': session.inspect('mem_read', {'addr': base + symbols['display_ready'], 'len': 1})['data'],
                'front_copper': session.inspect('mem_read', {'addr': base + symbols['front_copper'], 'len': 4})['data']})
            session.inspect('break_remove', {'id': breakpoint['id']})
            print(f'callback {count}: {len(differences)} state differences, beam {stop["vpos"]}:{stop["hpos"]}', flush=True)
        log = Path(launch['log']).read_text(encoding='utf-8', errors='replace')
        for marker in ('cpu=M68000', 'cpu_clock=7.09MHz', 'chip_ram=512K', 'fast_ram=0K',
                       'slow_ram=0K', 'chipset=Ocs', 'video=Pal', 'Kickstart 1.3'):
            if marker not in log:
                raise ValueError(f'Native hardware profile marker missing: {marker}')
        (directory / 'copperline.log').write_text(log, encoding='utf-8')
    report = {'scope': __doc__, 'executable_sha256': digest(executable),
              'reference_sha256': digest(source_path), 'symbols': symbols,
              'native_source': case['native_source'], 'native_source_sha256': digest(ROOT / case['native_source']),
              'emulator_sha256': digest(Path(config['tools']['copperline'])),
              'bridge_sha256': digest(ctl), 'kickstart_sha256': digest(Path(config['inputs']['amiga_rom'])),
              'native_inputs': {'port': 2, 'red': True}, 'observations': observations,
              'graphics_comparison_complete': False}
    report_path.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    capture()
