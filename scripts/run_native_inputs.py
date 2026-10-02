"""Retained physical raw input packets/aliases, using the actual native sampler."""
import argparse, json, hashlib, re
from build_native_game import build
from native_tools import ROOT, ASSEMBLER, run as assemble, emulator_config
from native_observation import code_symbols, target_log
from native_evidence import atomic_json, compile_manifest, tracked_call
from copperline_test_session import NativeControlSession


def run():
    _, normal = build()
    config = emulator_config()
    directory = ROOT / 'build/tests/native-inputs'
    directory.mkdir(parents=True, exist_ok=True)
    executable = normal
    symbols = code_symbols((normal.parent / 'native.lst').read_text()); checks = []
    def check(label, actual, expected):
        checks.append({'label': label, 'actual': actual, 'expected': expected})
        if actual != expected: raise AssertionError(checks[-1])
    with NativeControlSession(directory) as s:
        s.inspect('session_launch', {'binary': config['tools']['copperline'], 'run': str(executable), 'args':
          ['--chipset','OCS','--video','PAL','--cpu','68000','--chip','512K','--slow','0','--fast','0','--noaudio',config['inputs']['amiga_rom']]})
        stop = s.inspect('run_until', {'seconds': 30})
        if stop['reason'] != 'loadseg': raise RuntimeError(stop)
        base = int(re.search(r'first hunk \$([0-9a-fA-F]+)', stop['detail'])[1], 16); time = stop['seconds']
        def advance(seconds=.08):
            nonlocal time
            time += seconds; s.inspect('run_until', {'seconds': time})
        def mem(name,n=1):
            return bytes.fromhex(s.inspect('mem_read',{'addr':base+symbols[name],'len':n})['data'])
        def keys(events):
            for key,held in events:
                s.inspect('input_key',{'rawkey':key,'action':'press' if held else 'release'}); advance(.025)
        def pads(): return list(mem('game_input_bits',2))
        advance(1)
        s.inspect('input_key', {'rawkey': 0x02, 'action': 'press'}); advance(.1)
        s.inspect('input_key', {'rawkey': 0x02, 'action': 'release'}); advance(1.4)
        check('ordinary physical two-player selection plays', int.from_bytes(mem('game_lifecycle',2),'big'), 1)
        keys([(0x11,True),(0x22,True),(0x23,True),(0x4f,True),(0x3c,True)])
        check('simultaneous diagonal/actions',pads(),[19,36])
        keys([(0x2d,True),(0x4f,False)])
        check('alias release retains other held key',pads(),[19,36])
        keys([(k,False) for k in (0x11,0x22,0x23,0x2d,0x3c)])
        check('all released',pads(),[0,0])
        aliases=(0x3e,0x2d,0x1e,0x2f,0x0f,0x3c)
        keys([(k,True) for k in aliases]);check('all six keypad aliases',pads(),[0,63])
        keys([(k,False) for k in aliases]);check('keypad released',pads(),[0,0])
        # Real A500 matrix suppresses ambiguous multi-key rectangles. Test
        # each opposing pair without synthesizing impossible key rollover.
        keys([(0x20,True),(0x22,True)]);check('opposing horizontal packet',pads(),[5,0])
        keys([(0x20,False),(0x22,False)])
        keys([(0x11,True),(0x21,True)]);check('opposing vertical packet',pads(),[10,0])
        keys([(0x11,False),(0x21,False)])
        s.inspect('input_set_port',{'port':2,'device':'joystick'})
        keys([(0x23,True)])
        s.inspect('input_joy',{'port':2,'red':True});advance()
        keys([(0x23,False)]);check('keyboard release retains joystick action',pads(),[16,0])
        s.inspect('input_joy',{'port':2,'red':False});advance();check('combined action released',pads(),[0,0])
        keys([(0x24,True),(0x39,True),(0x3a,True)]);check('other action buttons',pads(),[32,48])
        keys([(k,False) for k in (0x24,0x39,0x3a)])
    target_log(directory)
    atomic_json(directory/'report.json', {'passed': True, 'checks': checks,
        'executable_sha256': hashlib.sha256(executable.read_bytes()).hexdigest(),
        'scope': 'Ordinary boot and physical raw input sampler/aliases/releases; no world writes or full-match claim'})
    print('native-inputs PASS', len(checks), flush=True)


if __name__ == '__main__':
    path = ROOT/'build/tests/native-inputs/report.json'
    tracked_call([path], 'native-inputs', 'maintained-native', 'ordinary title',
        'scripts/run_native_inputs.py', None, run, lambda path,report:[ROOT/'build/amiga/interfaces/enhanced/ctennis-enhanced'])
