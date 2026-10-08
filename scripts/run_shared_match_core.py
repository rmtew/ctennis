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
from native_evidence import snapshot, assembly_inputs, python_inputs, changed, ReportRun, compile_manifest
import os
from match_core_state import inventory, validate_record, SCHEMA_VERSION, SIMULATION_VERSION
from collections import Counter

READONLY = {
    'game_height_choices':9, 'game_lower_depth':9, 'game_lower_width':9,
    'game_upper_limits':16, 'game_lower_limits':16,
    'game_upper_depth':9, 'game_upper_width':9, 'game_scene_poses':112,
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


def replay_and_negatives(image, symbols, rows, executable):
    """Restore only once, then use recorded API arguments; no state injection."""
    for poison in (0xa5, 0x5a):
        with Core(image,symbols,poison=poison,readonly=READONLY) as cpu:
            for row in rows:
                cpu.clear_events()
                cpu.call_logical(row['operation'],row['arguments'])
                assert cpu.state().hex() == row['state'], ('poison replay',poison,row['index'])
                assert cpu.events == row['events'], ('poison outputs',poison,row['index'])
            cpu.audit_reads()
    relocated, relocated_symbols = load_image(executable,base=0x30000)
    with Core(relocated,relocated_symbols,poison=0x96,readonly=READONLY) as cpu:
        # Relocate the complete stream, including selection, play and return.
        # A fixed prefix can cover only TITLE in an attract recording.
        relocated_lifecycles = Counter()
        for row in rows:
            cpu.clear_events()
            cpu.call_logical(row['operation'],row['arguments'])
            assert cpu.state().hex() == row['state'], ('relocated state',row['index'])
            assert cpu.events == row['events'], ('relocated outputs',row['index'])
            relocated_lifecycles[int.from_bytes(cpu.state()[216:218],'big')] += 1
        expected_lifecycles = Counter(int.from_bytes(bytes.fromhex(row['state'])[216:218],'big')
                                     for row in rows)
        assert relocated_lifecycles == expected_lifecycles, 'Incomplete relocated lifecycle coverage'
        cpu.audit_reads()
    negatives = {}
    for fault in ('omitted-init','hardware-read','out-of-state-write','undeclared-read'):
        with Core(image,symbols,poison=0x3c,readonly=READONLY) as cpu:
            try:
                if fault == 'omitted-init':
                    row = rows[0]
                    assert cpu.state().hex() == row['state'], 'Poisoned state mismatch'
                else:
                    address = symbols['game_core_sample_pads']
                    if fault == 'hardware-read':
                        code = bytes.fromhex('103900bfe4014e75')
                    elif fault == 'out-of-state-write':
                        code = bytes.fromhex('13fc0000001000024e75')
                    else:
                        target = symbols['game_entropy']
                        code = bytes.fromhex('1039')+target.to_bytes(4,'big')+bytes.fromhex('4e75')
                    cpu.mem.w_block(address,code)
                    cpu.call('game_core_sample_pads')
                    cpu.audit_reads()
                raise RuntimeError('Negative control escaped: '+fault)
            except AssertionError as error:
                message = str(error)
                expected = {'omitted-init':'Poisoned state mismatch',
                    'hardware-read':'0xbfe401','out-of-state-write':'Out-of-state write',
                    'undeclared-read':'Undeclared data read'}[fault]
                assert expected in message, (fault,message)
                negatives[fault] = message
    return negatives


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seconds', type=float, default=8)
    parser.add_argument('--demo', action='store_true')
    parser.add_argument('--history', action='store_true', help='Fresh native rolling-store equality and exhaustive actual CPU seek')
    parser.add_argument('--ntsc', action='store_true')
    parser.add_argument('--two', action='store_true',help='Select and sample both human players')
    parser.add_argument('--restart', action='store_true',help='Physically pause, return to title and select the other mode')
    args = parser.parse_args()
    if args.demo and (args.two or args.restart):
        parser.error('Demo is separate from physical mode/restart cases')
    if not 0 < args.seconds <= 300:
        parser.error('Use a finite extent of at most 300 emulated seconds')
    standard = 'NTSC' if args.ntsc else 'PAL'
    case = standard.lower() + ('-history' if args.history else '-demo' if args.demo else '-two' if args.two else '-physical')
    if args.restart:
        case += '-restart'
    directory = ROOT/'build/tests'/('shared-match-core-'+case)
    directory.mkdir(parents=True, exist_ok=True)
    report_path = directory/'report.json'
    transaction = ReportRun([report_path], 'history-native', 'maintained-native', 'native title') if args.history else None
    if not transaction:
        report_path.write_text(json.dumps({'passed':False, 'state':'incomplete'})+'\n')
    _, ordinary = build()
    standalone, _ = build_core()
    image, core_symbols = load_image(standalone)
    layout = inventory(core_symbols)
    rules_sha256 = hashlib.sha256(standalone.read_bytes()).hexdigest()
    executable, listing = directory/'native-trace', directory/'native-trace.lst'
    run([str(ASSEMBLER), '-Fhunkexe', '-kick1hunks', '-m68000',
         '-DENHANCED_INTERFACE=1', '-DDEMO_RECORDING=1', '-DCORE_TRACE=1',
         '-L',str(listing), '-o',str(executable), 'amiga/main.s'])
    locations = {name:(int(hunk),int(offset,16)) for name,hunk,offset in
                 re.findall(r'^([A-Za-z_]\w*)\s+(\d\d):([0-9a-fA-F]{8})\s*$',
                            listing.read_text(),re.M)}
    config = emulator_config()
    files = snapshot(assembly_inputs(ROOT/'amiga/main.s') |
        assembly_inputs(ROOT/'amiga/standalone.s') | python_inputs(Path(__file__)) |
        set((ROOT/'assets/native').rglob('*.*')) |
        {ROOT/'tools.lock.json',ROOT/'config.local.ini',Path(ASSEMBLER),
         Path(config['tools']['copperline']),Path(config['inputs']['amiga_rom'])})
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
                cpu.call_logical(row['operation'], row['arguments'])
                assert cpu.state().hex() == row['state'], ('state',row['index'],row['operation'])
                assert cpu.events == row['events'], ('outputs',row['index'],row['operation'],
                                                      cpu.events,row['events'])
                if args.history and row['operation']=='game_core_init':
                    from history_proof import attach
                    attach(cpu)
                if row['index'] % 1000 == 0:
                    print('Compared operation',row['index'],row['operation'],flush=True)
            collector = TraceCollector(symbols,initial,symbols['core_trace_marker'],
                symbols['core_trace_arguments'],on_row=compare,initial_callback=0)
            session.notification_handler = collector.observe
            session.inspect('events.subscribe',{'events':['mmio'],'mmio':collector.watches()})
            start_seconds = stopped['seconds']
            if not args.demo:
                breakpoint = session.inspect('break_add',{'kind':'pc','addr':symbols['game_native_menu_tick']})
                stopped = session.inspect('run_until',{'seconds':start_seconds+2})
                session.inspect('break_remove',{'id':breakpoint['id']})
                assert stopped['pc'] == symbols['game_native_menu_tick'], stopped
                selection_key = 0x42 if args.two else 0x46
                session.inspect('input_key',{'rawkey':selection_key,'action':'press'})
                stopped = session.inspect('run_until',{'seconds':stopped['seconds']+2})
                session.inspect('input_key',{'rawkey':selection_key,'action':'release'})
                session.inspect('input_set_port',{'port':2,'device':'joystick'})
                session.inspect('input_joy',{'port':2,'red':True})
                if args.two:
                    session.inspect('input_set_port',{'port':1,'device':'joystick'})
                    session.inspect('input_joy',{'port':1,'blue':True})
            stopped = session.inspect('run_until',{'seconds':start_seconds+args.seconds})
            if args.restart:
                for port in (1,2):
                    session.inspect('input_set_port',{'port':port,'device':'joystick'})
                    session.inspect('input_joy',{'port':port,'red':False,'blue':False})
                def pulse(rawkey):
                    nonlocal stopped
                    session.inspect('input_key',{'rawkey':rawkey,'action':'press'})
                    stopped = session.inspect('run_until',{'seconds':stopped['seconds']+.25})
                    session.inspect('input_key',{'rawkey':rawkey,'action':'release'})
                    stopped = session.inspect('run_until',{'seconds':stopped['seconds']+.25})
                for key in (0x19,0x4d,0x44,0x4e,0x44):
                    pulse(key)
                pulse(0x46 if args.two else 0x42)
                stopped = session.inspect('run_until',{'seconds':stopped['seconds']+2})
            # Finish at an actual completed logical boundary; never inject state.
            breakpoint = session.inspect('break_add',{'kind':'pc','addr':symbols['simulation_update']})
            stopped = session.inspect('run_until',{'seconds':stopped['seconds']+1})
            session.inspect('break_remove',{'id':breakpoint['id']})
            assert stopped['pc'] == symbols['simulation_update'], stopped
            summary = collector.finish(read(symbols['game_core_state'],len(initial)))
            session.inspect('events.unsubscribe')
            cpu.audit_reads()
            history_validation = None
            if args.history:
                from history_proof import exercise, cursor, attempts
                length = symbols['game_history_buffer_end']-symbols['game_history_buffer']
                native_store = read(symbols['game_history_buffer'],length-318)
                cpu_store = bytes(cpu.mem.r_block(core_symbols['game_history_buffer'],length-318))
                assert native_store == cpu_store, 'Native recorder bytes differ from actual CPU recorder'
                for name,width in [('game_history_cursor',8),('game_history_oldest',8),
                                   ('game_history_checkpoint_count',2),('game_history_attempt_count',2)]:
                    assert read(symbols[name],width)==bytes(cpu.mem.r_block(core_symbols[name],width)), name
                retained = cursor(cpu)-cursor(cpu,'game_history_oldest')
                old = cursor(cpu,'game_history_oldest')
                relevant = collector.rows[old+1:] # startup init isn't recorded
                first = relevant[0]['start']['seconds'] if relevant else stopped['seconds']
                history_validation = dict(passed=True, native_buffer_equal=True,
                    retained_operations=retained, retained_seconds=stopped['seconds']-first,
                    retained_callbacks=len({row['start'].get('frame') for row in relevant}),
                    native_attempts=attempts(cpu),
                    seek=exercise(standalone,rows=collector.rows))
            negatives = replay_and_negatives(image,core_symbols,collector.rows,standalone)
            if not args.demo:
                selections = [row['arguments'][0] & 255 for row in collector.rows
                              if row['operation']=='game_core_select']
                expected = [int(args.two)] + ([int(not args.two)] if args.restart else [])
                assert selections == expected, ('Physical selection scope',selections)
                if args.restart:
                    assert int.from_bytes(cpu.state()[216:218],'big') == 1, 'Restart did not reach play'
            for row in collector.rows:
                validate_record({'schema_version':SCHEMA_VERSION,
                    'simulation_version':SIMULATION_VERSION,'rules_sha256':rules_sha256,
                    'state':row['state']},core_symbols,rules_sha256)
            assert not changed(files), ('Inputs changed during comparison',changed(files))
            report = {'schema':1,'passed':True,'commit':run(['git','rev-parse','HEAD']).strip(),
                'target':{'video':standard,'cpu':'68000','chipset':'OCS','chip_kib':512,
                'slow_kib':0,'fast_kib':0},'seconds':args.seconds,'elapsed_seconds':stopped['seconds']-start_seconds,
                'demo':args.demo,'restart':args.restart,'two':args.two,
                'state_bytes':len(initial),'summary':summary,'readonly':READONLY,'files':files,
                'canonical_layout':layout,
                'coverage':{'operation_counts':dict(Counter(row['operation'] for row in collector.rows)),
                    'lifecycle_counts':dict(Counter(int.from_bytes(bytes.fromhex(row['state'])[216:218],'big')
                                                   for row in collector.rows)),
                    'title_outputs':sum(['title'] in row['events'] for row in collector.rows),
                    'selection_commands':[row['arguments'] for row in collector.rows
                                          if row['operation']=='game_core_select']},
                'poisoned_replay':[165,90], 'negative_controls':negatives,
                'relocated_replay':{'base':0x30000,'poison':0x96,'operations':len(collector.rows),
                    'lifecycle_counts':dict(Counter(int.from_bytes(bytes.fromhex(row['state'])[216:218],'big')
                                                   for row in collector.rows))},
                'code_and_immutable_tables_bytes':core_symbols['game_core_code_end']-core_symbols['game_core_code_begin'],
                'stack_bytes':cpu.stack_bytes,'cycles':cpu.total_cycles,'loaded_hunks':checks,
                'sha256':{str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest()
                          for path in (ordinary,standalone,executable,Path(ASSEMBLER))},
                'rows':collector.rows, 'history':args.history, 'history_validation':history_validation}
            if transaction:
                transaction.meta['files'] = files
                transaction.meta['environment']['PYTHONPATH'] = os.environ.get('PYTHONPATH')
                transaction.finalize(report_path,dict(report,executable_sha256=hashlib.sha256(executable.read_bytes()).hexdigest()),
                    compiled=[compile_manifest(executable,listing),compile_manifest(standalone,standalone.parent/'match-core.lst')])
            else:
                report_path.write_text(json.dumps(report,indent=2)+'\n')
            print(json.dumps({key:value for key,value in report.items()
                              if key not in ('rows','loaded_hunks','readonly','files','canonical_layout')},indent=2))


if __name__ == '__main__':
    main()
