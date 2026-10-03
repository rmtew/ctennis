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
        if status not in (1, 2, 3, 4, 5, 6):
            raise ValueError('Unknown native contract')
        init += f'        move.b #{128 | status},game_display\n        move.b #224,game_status_clock\n'
    fixture = directory / 'fixture.s'
    source = source.replace(startup, init)
    if mutant:
        if mutant == 'pointer':
            marker = '        include "assets/native/court/score-patch-tables.i"'
            tables = (ROOT/'assets/native/court/score-patch-tables.i').read_text()
            for plane in range(4): tables = tables.replace(f'score_bank_status_{status}_p{plane}',f'score_bank_status_0_p{plane}')
            fault_path = directory/'fault-score-tables.i'; fault_path.write_text(tables)
            source = source.replace(marker,f'        include "{fault_path}"')
        elif case == 'audio-hit':
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
    assemble([str(ASSEMBLER), '-Fhunkexe', '-kick1hunks', '-m68000', '-DENHANCED_INTERFACE=1', '-L', str(listing),
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
        from native_hunk import loaded_hunks
        loaded=loaded_hunks(executable,session.inspect('segments.list')['current'],lambda a,n: bytes.fromhex(session.inspect('mem_read',{'addr':a,'len':n})['data']))
        if not loaded or not all(row['matched'] for row in loaded): raise AssertionError('Native contract loaded bytes differ')
        def read(name, size=1):
            return list(bytes.fromhex(session.inspect('mem_read', {'addr': base+symbols[name], 'len': size})['data']))
        def check(label, actual, expected):
            checks.append({'label': label, 'actual': actual, 'expected': expected})
            if actual != expected:
                raise AssertionError(checks[-1])
        session.inspect('run_until', {'pc': base + symbols['main_loop']})
        raster_checks = []
        association = {'fields':bytearray(read('prepared_field_values',6)), 'started':0, 'completed':0,
                       'back':bytearray(read('back_copper',4)), 'cop':bytearray(4), 'ready':None, 'published':None, 'publications':[]}
        if case.startswith('status-'):
            def observe(message):
                if message.get('method') != 'event.mmio': return
                row=message['params']; address=row['addr']; size=row['size']; value=row['value']
                if row.get('dropped_events',0) or row.get('dropped_notifications',0): raise AssertionError('Status publication telemetry lost')
                for name,buffer in [('prepared_field_values','fields'),('back_copper','back')]:
                    begin=base+symbols[name]
                    if begin<=address and address+size<=begin+len(association[buffer]):
                        association[buffer][address-begin:address-begin+size]=value.to_bytes(size,'big')
                if address==base+symbols['simulation_started_updates']: association['started']=value
                if address==base+symbols['display_ready'] and value:
                    association['ready']={'bank':int.from_bytes(association['back'],'big'),'generation':association['started'],
                        'fields':list(association['fields']),'completed':False}
                if address==base+symbols['simulation_updates']:
                    association['completed']=value
                    if association['ready'] and association['ready']['generation']==value: association['ready']['completed']=True
                if 0xdff080<=address and address+size<=0xdff084:
                    association['cop'][address-0xdff080:address-0xdff080+size]=value.to_bytes(size,'big')
                if address==0xdff088 and association['started']:
                    prepared=association['ready']; pointer=int.from_bytes(association['cop'],'big')
                    check('status published bank belongs to completed prepared scene',bool(prepared and prepared['completed'] and prepared['bank']==pointer),True)
                    check('status publication stays in retired bottom window',row['position']['vpos']>=253,True)
                    association['published']=dict(prepared,position=row['position'],actual_pointer=pointer,visible_frame=row['position']['frame']+(1 if row['position']['vpos']>=252 else 0))
                    association['publications'].append(association['published'])
            session.notification_handler=observe
            session.inspect('events.subscribe',{'events':['mmio'],'mmio':[
                {'addr':base+symbols[name],'len':length,'access':'write'} for name,length in
                [('prepared_field_values',6),('back_copper',4),('simulation_started_updates',2),('simulation_updates',2),('display_ready',1)]]+
                [{'addr':0xdff080,'len':4,'access':'write'},{'addr':0xdff088,'len':2,'access':'write'}]})
        pc = base + symbols['game_scene_service' if case=='audio-hit' else 'game_observe_pre_tail']
        session.inspect('break_add', {'kind': 'pc', 'addr': pc})
        seen = []
        for tick in range(38 if case.startswith('status-') else 20 if case=='audio-hit' else 3):
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
                if tick in (13,37):
                    variant=status if tick==13 else 0
                    completed=[row for row in association['publications'] if row['visible_frame']<=stop['frame']-1]
                    published=completed[-1] if completed else None
                    current=association['published']
                    check('visible status selection belongs to published completed scene',published['fields'][4] if published else None,variant)
                    regs=session.inspect('custom_dump')['regs']
                    check('status screenshot uses actual published physical Copper bank',regs['COP1LCH']*65536+regs['COP1LCL'],current['actual_pointer'])
                    check('current and completed status frames select same stable bank content',current['fields'][4],variant)
                    photo=directory/('visible.png' if variant else 'expired.png')
                    session.inspect('capture_screenshot',{'path':str(photo)})
                    locations={name:(int(h),int(o,16)) for name,h,o in re.findall(r'^([A-Za-z_][\w]*)\s+(\d\d):([0-9A-Fa-f]{8})\s*$',listing.read_text(),re.M)}
                    segments=session.inspect('segments.list')['current']
                    def located(name):
                        h,o=locations[name]; return segments[h]['start']+o
                    delta=current['actual_pointer']-located('copperlist')
                    pointers={}
                    for plane in (0,2,3):
                        hi=located(f'score_cop_{120+plane}_hi')+2+delta
                        lo=located(f'score_cop_{120+plane}_lo')+2+delta
                        words=bytes.fromhex(session.inspect('mem_read',{'addr':hi,'len':2})['data'])+bytes.fromhex(session.inspect('mem_read',{'addr':lo,'len':2})['data'])
                        pointers[str(plane)]={'actual':int.from_bytes(words,'big'),'expected':located(f'score_bank_status_{variant}_p{plane}')}
                    from native_square_scores import assert_hud_bank
                    bank_index=[located(n) for n in ('copperlist','copperlist_back','copperlist_third')].index(current['actual_pointer'])
                    assert_hud_bank(lambda a,n: bytes.fromhex(session.inspect('mem_read',{'addr':a,'len':n})['data']),
                                    located,bank_index,current['fields'])
                    atomic_json(photo.with_suffix('.json'),{'completed_scene':published,'current_published':current,'rendered_frame':stop['frame']-1,'status_plane_pointers':pointers})
                    from native_status_raster import assert_status_raster
                    raster_checks.append(dict(assert_status_raster(photo,variant),published_scene=published,rendered_frame=stop['frame']-1,screenshot=str(photo.relative_to(ROOT))))
                    for plane,pointer in pointers.items():check('actual net status plane '+plane+' pointer',pointer['actual'],pointer['expected'])
            session.inspect('step', {'count': 1})
        session.inspect('capture_screenshot', {'path': str(directory / 'final.png')})
    target_log(directory)
    if case == 'audio-hit':
        from native_audio_checks import pcm16_window
        audible = pcm16_window(directory/'native.wav', seen[1]['seconds'] + .002, .005)
        check('native hit emitted audible signal', any(row['nonzero_pcm16_samples'] for row in audible['channels']), True)
    report = {'passed': True, 'case': case, 'checks': checks, 'observations': seen,
              'executable_sha256': hashlib.sha256(executable.read_bytes()).hexdigest(),
              'status_raster':raster_checks,'loaded_hunks':loaded,
              'fixture_initialization': 'once at native startup; subsequent actual dispatcher ticks, no state writes',
              'scope': 'Local native scoring/status/render-field contracts, not uninterrupted ordinary play'}
    atomic_json(directory / 'report.json', report)
    print(case, 'PASS', len(checks), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=(*SCORING, 'status-1', 'status-2', 'status-3', 'status-4', 'status-5', 'status-6', 'audio-hit'), required=True)
    parser.add_argument('--self-test', action='store_true', help='One compiled late field fault at unchanged normal checkpoints')
    args = parser.parse_args()
    path = ROOT / 'build/tests/native-contracts' / args.case / 'report.json'
    def action():
        run(args.case)
        if args.self_test:
            report = json.loads(path.read_text())
            controls = []
            for mutation in ('pitch','envelope') if args.case=='audio-hit' else (True,'pointer') if args.case.startswith('status-') else (True,):
                try:
                    run(args.case, mutant=mutation)
                except AssertionError as error:
                    detail = error.args[0]
                    wanted = 'visible native status raster matches committed bank' if mutation=='pointer' else ('native hit pitch at actual Paula channel3' if mutation=='pitch' else
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
