"""Focused CT05 ordinary physical-input proof: first game, pause, next serve."""
import argparse
import json
import re
import shutil
from pathlib import Path
from build_native_game import build
from capture_native_presentation import code_symbols
from copperline_test_session import NativeControlSession
from evidence import ROOT, atomic_json, compile_manifest, tracked_call


def run(mode):
    config, ordinary = build()
    directory = ROOT / f'build/tests/ct05-ordinary-{mode}-round'
    directory.mkdir(parents=True, exist_ok=True)
    exe = directory / 'native-application'
    shutil.copy2(ordinary, exe)
    listing = directory / 'native.lst'
    shutil.copy2(ordinary.parent / 'native.lst', listing)
    compile_manifest(exe, listing)
    symbols = code_symbols(listing.read_text())
    rows, differences = [], []
    award = paused = resumed = completed = None
    frozen = None
    previous_games = 0
    last_callback = None
    with NativeControlSession(directory) as s:
        s.inspect('session_launch', {'binary': config['tools']['copperline'], 'run': str(exe),
            'args': ['--chipset', 'OCS', '--video', 'PAL', '--cpu', '68000', '--chip', '512K',
                     '--slow', '0', '--fast', '0', '--noaudio', config['inputs']['amiga_rom']]})
        stop = s.inspect('run_until', {'seconds': 30})
        if stop['reason'] != 'loadseg': raise RuntimeError(stop)
        base = int(re.search(r'first hunk \$([0-9A-Fa-f]+)', stop['detail'])[1], 16)
        def mem(name, count):
            return bytes.fromhex(s.inspect('mem_read', {'addr': base + symbols[name], 'len': count})['data'])
        s.inspect('run_until', {'seconds': stop['seconds'] + 2})
        if int.from_bytes(mem('game_lifecycle', 2), 'big') != 2:
            raise AssertionError('Ordinary title not reached')
        key = 0x46 if mode == 'one' else 0x42
        s.inspect('input_key', {'rawkey': key, 'action': 'press'})
        stop = s.inspect('run_until', {'seconds': stop['seconds'] + 5})
        s.inspect('input_key', {'rawkey': key, 'action': 'release'})
        for port in (1, 2):
            s.inspect('input_set_port', {'port': port, 'device': 'joystick'})
            s.inspect('input_joy', {'port': port, 'red': True})
        pc = base + symbols['game_observe_pre_tail']
        s.inspect('break_add', {'kind': 'pc', 'addr': pc})
        deadline = stop['seconds'] + 150
        for index in range(6000):
            stop = s.inspect('run_until', {'seconds': deadline})
            if stop['pc'] != pc or stop['reason'] not in ('target', 'breakpoint'): raise RuntimeError(stop)
            ram = bytes.fromhex(s.inspect('mem_read', {'addr': base + symbols['virtual_memory'] + 0xc000, 'len': 256})['data'])
            lifecycle = int.from_bytes(mem('game_lifecycle', 2), 'big')
            stage = mem('game_score_state', 1)[0]
            games = sum(ram[0x40:0x42])
            row = {'callback': int.from_bytes(mem('simulation_updates', 2), 'big') + 1,
                   'lifecycle': lifecycle, 'scoring_stage': stage, 'ram': ram.hex()}
            if last_callback is not None and row['callback'] != last_callback + 1:
                raise AssertionError('Ordinary callback observation is not consecutive')
            last_callback = row['callback']
            if bool(ram[0x3d] & 0x80) != (mode == 'two'):
                differences.append({'field': 'physical mode selection', 'callback': row['callback']})
            rows.append(row)
            if games != previous_games:
                if games != previous_games + 1 or award is not None:
                    differences.append({'field': 'exactly one first-game award', 'callback': row['callback']})
                award = row['callback']
                previous_games = games
            if lifecycle in (4, 5):
                if award is None: differences.append({'field': 'pause before game award'})
                if paused is None: paused = row['callback']
                pose = ram[0x45:0x4d]
                if frozen is None: frozen = pose
                if pose != frozen: differences.append({'field': 'player moved during round pause', 'callback': row['callback']})
                if games != 1 or any(ram[0x3e:0x40]):
                    differences.append({'field': 'score changed during round pause', 'callback': row['callback']})
            elif paused is not None and lifecycle == 1:
                if resumed is None: resumed = row['callback']
                if stage == 1 and ram[0x38] and ram[0x66]:
                    completed = row['callback']
                    break
        if not all((award, paused, resumed, completed)):
            differences.append({'field': 'ordinary first game and subsequent advancing serve not completed'})
    path = ROOT / f'build/tests/ct05-ordinary-{mode}-round-report.json'
    capture = directory / 'observations.json'
    atomic_json(capture, rows)
    report = {'case': f'ct05-ordinary-{mode}-round', 'passed': not differences,
              'first_difference': differences[0] if differences else None, 'differences': differences,
              'award_callback': award, 'pause_callback': paused, 'resume_callback': resumed,
              'next_serve_callback': completed, 'observed_callbacks': len(rows),
              'capture': str(capture.relative_to(ROOT)), 'physical_inputs': 'held red on both physical ports',
              'scope': 'Ordinary first game and next serve; no match parity or raster equivalence'}
    atomic_json(path, report)
    print(json.dumps({k:v for k,v in report.items() if k not in ('capture','differences')}))
    return 0 if report['passed'] else 1


def run_match(mode, early_release=False):
    """Ordinary physical play through award/title/reselection and fresh serve."""
    config, ordinary = build()
    name = f'ct06-ordinary-{mode}-' + ('early-release' if early_release else 'restart')
    directory = ROOT / f'build/tests/{name}'
    directory.mkdir(parents=True, exist_ok=True)
    exe = directory / 'native-application'
    shutil.copy2(ordinary, exe)
    listing = directory / 'native.lst'
    shutil.copy2(ordinary.parent / 'native.lst', listing)
    compile_manifest(exe, listing)
    symbols = code_symbols(listing.read_text())
    checkpoints, differences = {}, []
    observations = 0
    previous_callback = None
    previous = None
    snapshots = []
    restarted_mode = 'two' if mode == 'one' else 'one'
    selection_pressed = False
    released_callback = None
    waiting_callback = None
    action_samples = {}
    with NativeControlSession(directory) as session:
        session.inspect('session_launch', {'binary': config['tools']['copperline'], 'run': str(exe),
            'args': ['--chipset','OCS','--video','PAL','--cpu','68000','--chip','512K',
                     '--slow','0','--fast','0','--noaudio',config['inputs']['amiga_rom']]})
        stop = session.inspect('run_until', {'seconds':30})
        if stop['reason'] != 'loadseg': raise RuntimeError(stop)
        base = int(re.search(r'first hunk \$([0-9A-Fa-f]+)', stop['detail'])[1],16)
        def mem(name,count):
            return bytes.fromhex(session.inspect('mem_read',{'addr':base+symbols[name],'len':count})['data'])
        stop = session.inspect('run_until', {'seconds':stop['seconds']+2})
        if int.from_bytes(mem('game_lifecycle',2),'big') != 2: raise AssertionError('Ordinary title missing')
        key = 0x46 if mode == 'one' else 0x42
        session.inspect('input_key',{'rawkey':key,'action':'press'})
        stop = session.inspect('run_until',{'seconds':stop['seconds']+5})
        session.inspect('input_key',{'rawkey':key,'action':'release'})
        for port in (1,2):
            session.inspect('input_set_port',{'port':port,'device':'joystick'})
            session.inspect('input_joy',{'port':port,'red':True})
        pc = base+symbols['game_observe_pre_tail']
        session.inspect('break_add',{'kind':'pc','addr':pc})
        deadline = stop['seconds']+1000
        for index in range(40000):
            stop = session.inspect('run_until',{'seconds':deadline})
            if stop['pc'] != pc or stop['reason'] not in ('target','breakpoint'): raise RuntimeError(stop)
            ram = bytes.fromhex(session.inspect('mem_read',{'addr':base+symbols['virtual_memory']+0xc000,'len':256})['data'])
            lifecycle = int.from_bytes(mem('game_lifecycle',2),'big')
            callback = int.from_bytes(mem('simulation_updates',2),'big')+1
            if previous_callback is not None and callback != previous_callback+1:
                raise AssertionError('Ordinary callback continuity lost')
            previous_callback=callback;observations+=1
            state=(lifecycle,tuple(ram[0x40:0x42]))
            if state != previous:
                snapshots.append({'callback':callback,'lifecycle':lifecycle,'ram':ram.hex()})
                previous=state
            if lifecycle == 6 and 'match_award' not in checkpoints:
                if max(ram[0x40:0x42]) != 6 or any(ram[0x3e:0x40]):
                    raise AssertionError('Result before six-game award / nonzero points')
                checkpoints['match_award']=callback
                # Deliberately keep both old action buttons held across the menu.
            if lifecycle == 7 and 'returned_title_display' not in checkpoints:
                if any(ram[0x3d:0x42]): raise AssertionError('Old mode/score leaked into title reset')
                checkpoints['returned_title_display']=callback
            if lifecycle == 2 and 'match_award' in checkpoints and not selection_pressed:
                checkpoints['title_ready']=callback
                session.inspect('input_key',{'rawkey':0x42 if restarted_mode=='two' else 0x46,'action':'press'})
                selection_pressed=True
            if selection_pressed and lifecycle == 3:
                if 'restart_selected' not in checkpoints:
                    checkpoints['restart_selected']=callback
                    if bool(ram[0x3d]&128) != (restarted_mode=='two') or any(ram[0x3e:0x42]):
                        raise AssertionError('Chosen restart mode/score not fresh')
                if released_callback is None and callback-checkpoints['restart_selected'] >= 80:
                    session.inspect('input_key',{'rawkey':0x42 if restarted_mode=='two' else 0x46,'action':'release'})
                    released_callback=callback
            if early_release and 'restart_selected' in checkpoints:
                elapsed = callback-checkpoints['restart_selected']
                def action_sample():
                    return {'callback':callback,'lifecycle':lifecycle,
                            'raw':list(mem('game_input_bits',2)),
                            'pressed':list(mem('game_input_pressed',2)),
                            'released':list(mem('game_input_released',2)),
                            'latches':list(mem('game_old_action_latches',2)),
                            'controls':list(mem('game_player_controls',2))}
                if elapsed == 100:
                    sample=action_sample()
                    if lifecycle != 9 or sample['raw'] != [16,16] or sample['latches'] != [16,16]:
                        raise AssertionError('Early release must start with both old actions held in restart sound')
                    action_samples['before_release']=sample
                    checkpoints['early_release']=callback
                    session.inspect('input_joy',{'port':2,'red':False})
                elif elapsed == 101:
                    sample=action_sample()
                    if lifecycle != 9 or sample['raw'] != [0,16] or sample['released'] != [16,0] or sample['latches'] != [0,16]:
                        raise AssertionError('Sampled release during restart sound did not retire only P1 latch')
                    action_samples['sampled_release']=sample
                    checkpoints['sampled_release']=callback
                elif elapsed == 140:
                    if 'sampled_release' not in checkpoints:raise AssertionError('Release was not observed before repress')
                    checkpoints['early_repress']=callback
                    session.inspect('input_joy',{'port':2,'red':True})
                elif elapsed == 141:
                    sample=action_sample()
                    if lifecycle != 9 or sample['raw'] != [16,16] or sample['pressed'] != [16,0] or sample['latches'] != [0,16]:
                        raise AssertionError('Fresh press before play re-latched P1 or released continuously held P2')
                    action_samples['sampled_repress']=sample
                    checkpoints['sampled_repress']=callback
            if released_callback is not None and lifecycle == 1:
                if 'restart_playing' not in checkpoints:
                    checkpoints['restart_playing']=callback
                    if bool(ram[0x3d]&128) != (restarted_mode=='two') or any(ram[0x3e:0x42]) or ram[0x3d]&0x70:
                        raise AssertionError('Old mode/end/score leaked into restarted match')
                    if mem('game_lower_owner',2) != bytes([0,1]):
                        raise AssertionError('Old player ownership survived reset')
                if early_release:
                    if callback > checkpoints['restart_playing']:
                        sample=action_sample()
                        if sample['raw'] != [16,16] or sample['latches'] != [0,16] or sample['controls'] != [16,0]:
                            raise AssertionError('Fresh P1 action masked or continuously held P2 action escaped')
                        if 'fresh_action_eligible' not in checkpoints:
                            checkpoints['fresh_action_eligible']=callback
                            action_samples['playable']=sample
                        if ram[0x38] and ram[0x66]:
                            checkpoints['restarted_flight']=callback
                            snapshots.append({'callback':callback,'lifecycle':lifecycle,'ram':ram.hex()})
                            break
                        if callback-checkpoints['restart_playing'] >= 60:
                            raise AssertionError('Fresh early repress did not launch without a second release')
                    continue
                if waiting_callback is None and ram[0x3a]&0x40:
                    waiting_callback=callback
                if waiting_callback is not None and 'restart_action' not in checkpoints:
                    if ram[0x38] or any(ram[0x3e:0x42]): raise AssertionError('Restart launched without fresh action')
                    if 'old_action_blocked' not in checkpoints and callback-waiting_callback >= 80:
                        if mem('game_input_bits',2) != bytes([16,16]):
                            raise AssertionError('Old physical actions were not still held')
                        if any(v&0x30 for v in mem('game_player_controls',2)):
                            raise AssertionError('Old physical action leaked into player controls')
                        checkpoints['old_action_blocked']=callback
                        for port in (1,2):session.inspect('input_joy',{'port':port,'red':False,'blue':False})
                    elif 'old_action_blocked' in checkpoints and callback-checkpoints['old_action_blocked'] >= 80:
                        checkpoints['restart_action']=callback
                        session.inspect('input_joy',{'port':2,'red':True})
                elif 'restart_action' in checkpoints and ram[0x38] and ram[0x66]:
                    checkpoints['restarted_flight']=callback
                    snapshots.append({'callback':callback,'lifecycle':lifecycle,'ram':ram.hex()})
                    break
        required=(('match_award','returned_title_display','title_ready','restart_selected','early_release','sampled_release','early_repress','sampled_repress','restart_playing','fresh_action_eligible','restarted_flight') if early_release else
                  ('match_award','returned_title_display','title_ready','restart_selected','restart_playing','old_action_blocked','restart_action','restarted_flight'))
        if any(k not in checkpoints for k in required):differences.append({'field':'Ordinary match/title/restarted serve incomplete','checkpoints':checkpoints})
    capture=directory/'checkpoints.json';atomic_json(capture,snapshots)
    report={'case':name,'subject':'maintained-native','passed':not differences,
            'first_difference':differences[0] if differences else None,'checkpoints':checkpoints,
            'observed_callbacks':observations,'consecutive_callbacks':True,'start_mode':mode,'restart_mode':restarted_mode,'held_old_actions_verified': 'old_action_blocked' in checkpoints,
            'capture':str(capture.relative_to(ROOT)),
            'early_release_verified':early_release and 'fresh_action_eligible' in checkpoints,
            'action_samples':action_samples,
            'scope':'Ordinary uninterrupted physical play through result/title/opposite mode/restarted advancing serve; no reference full-match/cadence/pixel parity'}
    path=ROOT/f'build/tests/{name}-report.json';atomic_json(path,report)
    print(json.dumps(report),flush=True)
    return 0 if report['passed'] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('one','two'), required=True)
    parser.add_argument('--match',action='store_true',help='CT06 ordinary result/title/restarted serve')
    parser.add_argument('--early-release',action='store_true',help='Focused CT06 one→two restart-sound release/repress edge')
    args=parser.parse_args()
    if args.early_release and (not args.match or args.mode != 'one'):
        parser.error('--early-release requires --match --mode=one')
    mode=args.mode
    if args.match:
        name=f'ct06-ordinary-{mode}-' + ('early-release' if args.early_release else 'restart')
        path=ROOT/f'build/tests/{name}-report.json'
        return tracked_call([path],'ordinary-round','maintained-native','ordinary title',
                            'scripts/run_ordinary_round_tests.py',None,lambda:run_match(mode,args.early_release),
                            lambda path,report:[ROOT/f'build/tests/{name}/native-application'])
    path = ROOT / f'build/tests/ct05-ordinary-{mode}-round-report.json'
    return tracked_call([path], 'ordinary-round', 'maintained-native', 'ordinary title',
                        'scripts/run_ordinary_round_tests.py', None, lambda: run(mode),
                        lambda path, report: [ROOT / f'build/tests/ct05-ordinary-{mode}-round/native-application'])

if __name__ == '__main__':
    raise SystemExit(main())
