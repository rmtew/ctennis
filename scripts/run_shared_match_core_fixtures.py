"""One-time retained scoring fixtures, then native/isolated logical-operation equality."""
import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from build_match_core import build as build_core, load_image
from build_native_game import build
from copperline_test_session import NativeControlSession
from match_core_capture import TraceCollector
from match_core_cpu import Core
from match_core_state import inventory
from native_evidence import compile_manifest, snapshot, python_inputs, changed
from native_hunk import loaded_hunks
from native_tools import ROOT, ASSEMBLER, run, emulator_config
from run_native_contracts import SCORING
from run_shared_match_core import READONLY


def check_case(case, seconds):
    directory = ROOT/'build/tests'/('shared-match-core-fixture-'+case)
    directory.mkdir(parents=True,exist_ok=True)
    report_path = directory/'report.json'
    report_path.write_text(json.dumps({'passed':False,'state':'incomplete'})+'\n')
    _,ordinary = build()
    standalone,_ = build_core()
    image,core_symbols = load_image(standalone)
    points,games,outcome,expected_points,expected_games = SCORING[case]
    initialization = '        moveq #1,d0\n        bsr game_new_match\n        bsr game_begin_active\n        move.b #$40,game_score_flags\n'
    for name,value in zip(('game_point_a','game_point_b','game_games_a','game_games_b','game_contact'),
                          (*points,*games,outcome)):
        initialization += f'        move.b #{value},{name}\n'
    source = (ROOT/'amiga/main.s').read_text()
    marker = '        bsr     game_begin_title'
    assert source.count(marker) == 1
    fixture = directory/'fixture.s'
    fixture.write_text(source.replace(marker,initialization))
    executable,listing = directory/'native-trace',directory/'native-trace.lst'
    run([str(ASSEMBLER),'-Fhunkexe','-kick1hunks','-m68000','-DENHANCED_INTERFACE=1',
         '-DDEMO_RECORDING=1','-DCORE_TRACE=1','-L',str(listing),'-o',str(executable),str(fixture)])
    compiled = compile_manifest(executable,listing)
    config = emulator_config()
    files = snapshot(python_inputs(Path(__file__)) | {ROOT/'tools.lock.json',Path(ASSEMBLER),
        Path(config['tools']['copperline']),Path(config['inputs']['amiga_rom'])})
    files.update(compiled['files'])
    locations = {name:(int(hunk),int(offset,16)) for name,hunk,offset in
        re.findall(r'^([A-Za-z_]\w*)\s+(\d\d):([0-9a-fA-F]{8})\s*$',listing.read_text(),re.M)}
    with NativeControlSession(directory) as session:
        session.inspect('session_launch',{'binary':config['tools']['copperline'],'run':str(executable),
            'args':['--chipset','OCS','--video','PAL','--cpu','68000','--chip','512K',
                    '--slow','0','--fast','0','--noaudio',config['inputs']['amiga_rom']]})
        stopped = session.inspect('run_until',{'seconds':30})
        assert stopped['reason'] == 'loadseg',stopped
        segments = session.inspect('segments.list')['current']
        symbols = {name:segments[hunk]['start']+offset for name,(hunk,offset) in locations.items()}
        def read(address,size):
            return bytes.fromhex(session.inspect('mem_read',{'addr':address,'len':size})['data'])
        checks = loaded_hunks(executable,segments,read)
        # Exactly one initial fixture image, after actual product initialization.
        breakpoint = session.inspect('break_add',{'kind':'pc','addr':symbols['main_loop']})
        stopped = session.inspect('run_until',{'seconds':stopped['seconds']+2})
        session.inspect('break_remove',{'id':breakpoint['id']})
        assert stopped['pc'] == symbols['main_loop'],stopped
        initial = read(symbols['game_core_state'],314)
        assert list(initial[66:68]) == points and list(initial[68:70]) == games
        with Core(image,core_symbols,initial=initial,readonly=READONLY) as cpu:
            def compare(row):
                cpu.clear_events()
                cpu.call_logical(row['operation'],row['arguments'])
                assert cpu.state().hex() == row['state'], ('fixture state',case,row['index'],row['operation'])
                assert cpu.events == row['events'], ('fixture outputs',case,row['index'],row['operation'])
            collector = TraceCollector(symbols,initial,symbols['core_trace_marker'],
                symbols['core_trace_arguments'],on_row=compare,initial_callback=0)
            session.notification_handler = collector.observe
            session.inspect('events.subscribe',{'events':['mmio'],'mmio':collector.watches()})
            for port in (1,2):
                session.inspect('input_set_port',{'port':port,'device':'joystick'})
                session.inspect('input_joy',{'port':port,'red':True})
            stopped = session.inspect('run_until',{'seconds':stopped['seconds']+seconds})
            breakpoint = session.inspect('break_add',{'kind':'pc','addr':symbols['simulation_update']})
            stopped = session.inspect('run_until',{'seconds':stopped['seconds']+1})
            session.inspect('break_remove',{'id':breakpoint['id']})
            assert stopped['pc'] == symbols['simulation_update'],stopped
            summary = collector.finish(read(symbols['game_core_state'],314))
            session.inspect('events.unsubscribe')
            cpu.audit_reads()
            first = next(row for row in collector.rows if row['operation']=='game_tick_dispatch')
            awarded = bytes.fromhex(first['state'])
            assert list(awarded[66:68]) == expected_points, ('Retained points',case,awarded[66:68])
            assert list(awarded[68:70]) == expected_games, ('Retained games',case,awarded[68:70])
            stack_bytes = cpu.stack_bytes
        for poison,base in ((0x5a,0x10000),(0x96,0x30000)):
            relocated,relocated_symbols = load_image(standalone,base=base)
            with Core(relocated,relocated_symbols,initial=initial,poison=poison,readonly=READONLY) as cpu:
                for row in collector.rows:
                    cpu.clear_events()
                    cpu.call_logical(row['operation'],row['arguments'])
                    assert cpu.state().hex() == row['state'], ('fixture replay',case,poison,row['index'])
                    assert cpu.events == row['events'], ('fixture replay output',case,poison,row['index'])
                cpu.audit_reads()
        assert not changed(files), ('Fixture inputs changed',changed(files))
        report = {'schema':1,'passed':True,'commit':run(['git','rev-parse','HEAD']).strip(),
            'case':case,'seconds':seconds,'target':{'video':'PAL','cpu':'68000','chipset':'OCS',
                'chip_kib':512,'slow_kib':0,'fast_kib':0},'summary':summary,
            'canonical_layout':inventory(core_symbols),'initial':initial.hex(),'rows':collector.rows,
            'initialization':'once after product init; no later state injection',
            'retained_points':expected_points,'retained_games':expected_games,
            'files':files,'loaded_hunks':checks,'stack_bytes':stack_bytes,
            'lifecycle_counts':dict(Counter(int.from_bytes(bytes.fromhex(row['state'])[216:218],'big')
                                           for row in collector.rows)),
            'sha256':{str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in (ordinary,standalone,executable)}}
        report_path.write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({key:value for key,value in report.items()
                          if key not in ('files','rows','initial','canonical_layout','loaded_hunks')},indent=2),flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case',choices=(*SCORING,'all'),required=True)
    parser.add_argument('--seconds',type=float,default=8)
    args = parser.parse_args()
    if not 0 < args.seconds <= 30:
        parser.error('Fixture extent must be finite and at most 30 seconds')
    for case in SCORING if args.case == 'all' else (args.case,):
        check_case(case,args.seconds)
