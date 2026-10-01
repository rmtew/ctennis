from native_state_observation import read_native_state
"""Four CT09 physical edges; paused boundary probes are separate from cadence."""
import json
import re
import shutil

from build_native_game import build
from capture_native_presentation import code_symbols
from copperline_test_session import NativeControlSession
from evidence import ROOT, atomic_json, compile_manifest


def run():
    config, ordinary = build()
    directory = ROOT/'build/tests/ct09-input-timing-edges'
    directory.mkdir(parents=True, exist_ok=True)
    exe, listing = directory/'native-application', directory/'native.lst'
    shutil.copy2(ordinary, exe)
    shutil.copy2(ordinary.parent/'native.lst', listing)
    compile_manifest(exe, listing)
    symbols = code_symbols(listing.read_text())
    checks, failures = [], []
    for kind in ('direction', 'action'):
        for boundary in ('before', 'after'):
            case = directory/f'{kind}-{boundary}'
            with NativeControlSession(case) as s:
                s.inspect('session_launch', {'binary': config['tools']['copperline'], 'run': str(exe),
                    'args': ['--chipset','OCS','--video','PAL','--cpu','68000','--chip','512K',
                             '--slow','0','--fast','0','--noaudio',config['inputs']['amiga_rom']]})
                stop = s.inspect('run_until', {'seconds':30})
                if stop['reason'] != 'loadseg': raise RuntimeError(stop)
                base = int(re.search(r'first hunk \$([0-9A-Fa-f]+)', stop['detail'])[1],16)
                def mem(name, n):
                    return bytes.fromhex(s.inspect('mem_read', {'addr':base+symbols[name],'len':n})['data'])
                def snapshot():
                    ram = read_native_state(s,base,symbols)
                    return {'ram':ram.hex(), 'lower_x':ram[0x4a], 'lower_phase':ram[0x3a],
                            'tick':ram[0x6b], 'raw':mem('game_input_bits',2).hex(),
                            'started':int.from_bytes(mem('simulation_started_updates',2),'big'),
                            'completed':int.from_bytes(mem('simulation_updates',2),'big')}
                stop = s.inspect('run_until', {'seconds':stop['seconds']+2})
                s.inspect('input_set_port', {'port':2,'device':'joystick'})
                s.inspect('input_joy', {'port':2})
                s.inspect('input_key', {'rawkey':0x46,'action':'press'})
                stop = s.inspect('run_until', {'seconds':stop['seconds']+2})
                s.inspect('input_key', {'rawkey':0x46,'action':'release'})
                stop = s.inspect('run_until', {'seconds':stop['seconds']+2})
                pc_sample = base+symbols['sample_amiga_joystick']
                pc_observe = base+symbols['game_observe_pre_tail']
                # Establish the actual neutral serving pose, never inject RAM.
                for _ in range(100):
                    stop = s.inspect('run_until', {'pc':pc_sample})
                    before = snapshot()
                    if int.from_bytes(mem('game_lifecycle',2),'big') == 1 and before['lower_phase'] & 0x40: break
                    s.inspect('step', {'count':1})
                else: raise AssertionError('Ordinary neutral serve wait absent')
                if before['raw'] != '0000': raise AssertionError('Precondition is not physically neutral')
                if boundary == 'after':
                    stop = s.inspect('run_until', {'pc':pc_observe})
                    neutral = snapshot()
                    if neutral['lower_x'] != before['lower_x'] or neutral['lower_phase'] != before['lower_phase']:
                        raise AssertionError('Neutral pre-tail changed pose')
                else: neutral = None
                injection = stop
                accepted = s.inspect('input_joy', {'port':2, 'left':kind=='direction', 'red':kind=='action'})
                if boundary == 'after':
                    s.inspect('step', {'count':1})
                    sample = s.inspect('run_until', {'pc':pc_sample})
                    next_before = snapshot()
                else: sample, next_before = stop, before
                observed = s.inspect('run_until', {'pc':pc_observe})
                actual = snapshot()
                expected_x = next_before['lower_x']-(1+(next_before['tick']&1)) if kind == 'direction' else next_before['lower_x']
                expected_phase = 0x20 if kind == 'action' else next_before['lower_phase']
                expected_callback = before['started']+(boundary=='after')
                passed = (actual['lower_x']==expected_x and actual['lower_phase']==expected_phase
                          and actual['raw']==('0400' if kind=='direction' else '1000')
                          and actual['started']==expected_callback
                          and actual['completed']==expected_callback-1)
                check = {'kind':kind, 'boundary':boundary, 'before':before, 'neutral_same_callback':neutral,
                         'physical_injection':injection, 'input_reply':accepted, 'sampler':sample,
                         'observed':observed, 'actual':actual, 'expected_x':expected_x,
                         'expected_phase':expected_phase, 'expected_callback':expected_callback,
                         'guest_latency_cck':observed['cck']-injection['cck'], 'passed':passed}
                checks.append(check)
                if not passed: failures.append({'field':kind+' '+boundary+' source-tick edge','actual':actual})
    # Preserve the four exact target logs in the existing physical runner's
    # fingerprinted log location, without copying any private input contents.
    (directory/'copperline.log').write_bytes(b''.join((directory/f'{kind}-{boundary}'/'emulator.log').read_bytes()
        for kind in ('direction','action') for boundary in ('before','after')))
    capture=directory/'edges.json';atomic_json(capture,checks)
    report={'case':'ct09-input-timing-edges','subject':'maintained-native','passed':not failures,
            'first_difference':failures[0] if failures else None,'checks':checks,
            'capture':str(capture.relative_to(ROOT)), 'scope':'Four physical input edges at actual ordinary sampler/pre-tail boundaries; debug stops do not certify ordinary cadence'}
    atomic_json(ROOT/'build/tests/ct09-input-timing-edges-report.json',report)
    print(json.dumps({'case':report['case'],'passed':report['passed'],'first_difference':report['first_difference']}),flush=True)
    return 0 if report['passed'] else 1
