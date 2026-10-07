"""Compare native logical operations with the isolated production 68000 core."""
import argparse
import hashlib
import json
import re
from pathlib import Path

from build_match_core import build as build_core, load_image
from build_native_game import build
from copperline_test_session import NativeControlSession
from match_core_capture import TraceCollector
from match_core_cpu import Core
from native_hunk import loaded_hunks
from native_tools import ROOT, ASSEMBLER, run, emulator_config

READONLY = {
    'game_height_choices':9, 'game_lower_depth':9, 'game_lower_width':9,
    'game_upper_limits':16, 'game_scene_poses':112,
    'game_scene_robot_poses':112, 'game_scene_animations':36,
    'score_stage_flags':5, 'score_sample_fields':88, 'game_audio_levels':16,
    'native_audio_scores':28,
}
AUDIO_TABLES = {
    'native_audio_score_0':'score-0.bin', 'native_audio_score_1':'score-1.bin',
    'native_audio_score_4':'score-4.bin', 'native_audio_score_5':'score-5.bin',
    'native_audio_periods':'periods.bin', 'native_audio_envelopes':'envelopes.bin',
    'native_victory_melody':'battle-hymn/melody.bin',
    'native_victory_bass':'battle-hymn/bass.bin',
    'native_victory_arpeggio':'battle-hymn/arpeggio.bin',
    'native_victory_periods':'battle-hymn/periods.bin',
}
READONLY.update({name:(ROOT/'assets/native/audio'/path).stat().st_size
                 for name,path in AUDIO_TABLES.items()})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seconds', type=float, default=8)
    parser.add_argument('--demo', action='store_true')
    parser.add_argument('--ntsc', action='store_true')
    args = parser.parse_args()
    if not 0 < args.seconds <= 300:
        parser.error('Use a finite extent of at most 300 emulated seconds')
    directory = ROOT/'build/tests/shared-match-core'
    directory.mkdir(parents=True, exist_ok=True)
    report_path = directory/'report.json'
    report_path.write_text(json.dumps({'passed':False, 'state':'incomplete'})+'\n')
    _, ordinary = build()
    standalone, _ = build_core()
    image, core_symbols = load_image(standalone)
    executable, listing = directory/'native-trace', directory/'native-trace.lst'
    run([str(ASSEMBLER), '-Fhunkexe', '-kick1hunks', '-m68000',
         '-DENHANCED_INTERFACE=1', '-DDEMO_RECORDING=1', '-DCORE_TRACE=1',
         '-L',str(listing), '-o',str(executable), 'amiga/main.s'])
    locations = {name:(int(hunk),int(offset,16)) for name,hunk,offset in
                 re.findall(r'^([A-Za-z_]\w*)\s+(\d\d):([0-9a-fA-F]{8})\s*$',
                            listing.read_text(),re.M)}
    config = emulator_config()
    standard = 'NTSC' if args.ntsc else 'PAL'
    with NativeControlSession(directory) as session:
        session.inspect('session_launch', {'binary':config['tools']['copperline'],
            'run':str(executable), 'args':['--chipset','OCS','--video',standard,
            '--cpu','68000','--chip','512K','--slow','0','--fast','0','--noaudio',
            config['inputs']['amiga_rom']]})
        stopped = session.inspect('run_until', {'seconds':30})
        assert stopped['reason'] == 'loadseg', stopped
        segments = session.inspect('segments.list')['current']
        symbols = {name:segments[hunk]['start']+offset
                   for name,(hunk,offset) in locations.items()}
        def read(address, size):
            return bytes.fromhex(session.inspect('mem_read',
                {'addr':address,'len':size})['data'])
        checks = loaded_hunks(executable, segments, read)
        initial = read(symbols['game_core_state'],
                       symbols['game_core_state_end']-symbols['game_core_state'])
        with Core(image, core_symbols, initial, readonly=READONLY) as cpu:
            def compare(row):
                cpu.clear_events()
                cpu.call(row['operation'], dict(enumerate(row['arguments'])))
                assert cpu.state().hex() == row['state'], ('state',row['index'],row['operation'])
                assert cpu.events == row['events'], ('outputs',row['index'],row['operation'],
                                                      cpu.events,row['events'])
                if row['index'] % 1000 == 0:
                    print('Compared operation',row['index'],row['operation'],flush=True)
            collector = TraceCollector(symbols,initial,symbols['core_trace_marker'],
                symbols['core_trace_arguments'],on_row=compare,initial_callback=0)
            session.notification_handler = collector.observe
            session.inspect('events.subscribe',{'events':['mmio'],'mmio':collector.watches()})
            start_seconds = stopped['seconds']
            if not args.demo:
                session.inspect('input_key',{'rawkey':0x46,'action':'press'})
                stopped = session.inspect('run_until',{'seconds':start_seconds+2})
                session.inspect('input_key',{'rawkey':0x46,'action':'release'})
                session.inspect('input_set_port',{'port':2,'device':'joystick'})
                session.inspect('input_joy',{'port':2,'red':True})
            stopped = session.inspect('run_until',{'seconds':start_seconds+args.seconds})
            # Finish at an actual completed logical boundary; never inject state.
            breakpoint = session.inspect('break_add',{'kind':'pc','addr':symbols['simulation_update']})
            stopped = session.inspect('run_until',{'seconds':stopped['seconds']+1})
            session.inspect('break_remove',{'id':breakpoint['id']})
            assert stopped['pc'] == symbols['simulation_update'], stopped
            summary = collector.finish(read(symbols['game_core_state'],len(initial)))
            session.inspect('events.unsubscribe')
            cpu.audit_reads()
            report = {'schema':1,'passed':True,'commit':run(['git','rev-parse','HEAD']).strip(),
                'target':{'video':standard,'cpu':'68000','chipset':'OCS','chip_kib':512,
                          'slow_kib':0,'fast_kib':0},'seconds':args.seconds,'demo':args.demo,
                'state_bytes':len(initial),'summary':summary,'readonly':READONLY,
                'stack_bytes':cpu.stack_bytes,'cycles':cpu.total_cycles,'loaded_hunks':checks,
                'sha256':{str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest()
                          for path in (ordinary,standalone,executable,Path(ASSEMBLER))},
                'rows':collector.rows}
            report_path.write_text(json.dumps(report,indent=2)+'\n')
            print(json.dumps({key:value for key,value in report.items()
                              if key not in ('rows','loaded_hunks','readonly')},indent=2))


if __name__ == '__main__':
    main()
