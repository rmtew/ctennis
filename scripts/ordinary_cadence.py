from native_tools import emulator_config
"""CT09's finite non-stopping ordinary play measurement, not a reference model."""
from fractions import Fraction
import json
import re
import shutil
from native_tools import ASSEMBLER, run as assemble
from native_clock import clock_contract, INTERVAL_CCK
from native_setup_observation import SetupObserver
from native_longword_observer import LongwordObserver

from native_state_observation import field_addresses, read_native_state
from native_hunk import loaded_hunks
from build_native_game import build
from native_observation import code_symbols, target_log
from copperline_test_session import NativeControlSession
from native_evidence import ROOT, atomic_json, compile_manifest

CCK_HZ = 3546895
ECLK_HZ = 709379
CHIP_BYTES = 524288


def chip_memory(read):
    execbase = int.from_bytes(read(4, 4), 'big')
    node = int.from_bytes(read(execbase+0x142, 4), 'big')
    regions = []
    while node:
        h = read(node, 32)
        successor = int.from_bytes(h[:4], 'big')
        if not successor:
            break  # Exec list tail sentinel
        if len(regions) >= 20 or any(r['header'] == node for r in regions):
            raise ValueError('Invalid Exec MemList')
        lower, upper, free = [int.from_bytes(h[i:i+4], 'big') for i in (20, 24, 28)]
        chunk, previous, chunks = int.from_bytes(h[16:20], 'big'), 0, []
        while chunk:
            if not lower <= chunk < upper or chunk <= previous or len(chunks) >= 4096:
                raise ValueError('Invalid Exec free chunk chain')
            b = read(chunk, 8)
            size = int.from_bytes(b[4:], 'big')
            if size < 8 or chunk+size > upper:
                raise ValueError('Invalid Exec free chunk size')
            chunks.append({'addr': chunk, 'bytes': size})
            previous, chunk = chunk, int.from_bytes(b[:4], 'big')
        if sum(c['bytes'] for c in chunks) != free:
            raise ValueError('Exec free-list sum differs from mh_Free')
        regions.append({'header': node, 'attributes': int.from_bytes(h[14:16], 'big'),
                        'lower': lower, 'upper': upper, 'free': free, 'chunks': chunks})
        node = successor
    if not regions or any(r['upper'] > CHIP_BYTES or not r['attributes'] & 2 for r in regions):
        raise ValueError('Target has unexpected non-chip memory region')
    return {'execbase': execbase, 'regions': regions,
            'used_chip_bytes': CHIP_BYTES-sum(r['free'] for r in regions)}


def run(mode, bank_control=False, boot_adf=None, flavor="enhanced", keyboard=False):
    config, ordinary = build(flavor=flavor); config = emulator_config()
    adf_sha=__import__('hashlib').sha256(boot_adf.read_bytes()).hexdigest() if boot_adf else None
    name = f'ct10-adf-{mode}-cadence' if boot_adf else 'ct09-published-bank-control' if bank_control else f'ct09-ordinary-{mode}-cadence'
    name += '-' + flavor + ('-keyboard' if keyboard else '')
    directory = ROOT / f'build/tests/{name}'
    directory.mkdir(parents=True, exist_ok=True)
    exe, listing = directory/'native-application', directory/'native.lst'
    shutil.copy2(ordinary, exe)
    shutil.copy2(ordinary.parent/'native.lst', listing)
    if bank_control:
        source = (ROOT/'amiga/main.s').read_text()
        marker = '        move.l  d0,$dff080'
        if source.count(marker)!=1:
            raise ValueError('Ordinary Copper publication instruction changed')
        # The previous front is now back_copper. Publish that stale physical
        # bank after update200, leaving readiness/counters/gameplay unchanged.
        wrapper = directory/'wrong-bank.s'
        wrapper.write_text(source.replace(marker,
            '        cmpi.w  #200,simulation_updates\n        bcs.s   bank_control_unchanged\n'
            '        move.l  back_copper,d0\nbank_control_unchanged:\n'+marker))
        assemble([str(ASSEMBLER),'-Fhunkexe','-kick1hunks','-m68000',*(['-DENHANCED_INTERFACE=1'] if flavor=='enhanced' else []),'-L',str(listing),'-o',str(exe),str(wrapper)])
    compile_manifest(exe, listing)
    symbols = code_symbols(listing.read_text())
    if 'refresh_signs' in symbols or 'initial_ram' in symbols:
        raise ValueError('Ordinary cadence subject contains captured initialization/entropy')
    contract = clock_contract()
    atomic_json(directory/'clock-contract.json', contract)  # before execution
    failures, checkpoints, inputs, replies, changes = [], {}, [], {}, []
    callbacks, commits, memory_writes = [], [], []
    preparations = []
    view_selections = []
    native_state, controls = {}, bytearray(8)
    state = {'lifecycle': 0, 'started': 0, 'completed': 0, 'ready': None,
             'released': False, 'initial_selected': None, 'restart_selected': None,
             'last_commit': 0, 'start': None, 'origin': None, 'pause_pose': None}
    pointer_bytes = {n: bytearray(4) for n in ('front_copper','back_copper','copper_write_delta','sprite_write_delta','cop1lc')}
    state.update(title=0, prepared=None, bank_fault_pause=False)
    restarted = 'two' if mode == 'one' else 'one'
    with NativeControlSession(directory) as s, (directory/'events.jsonl').open('w') as raw:
        args=['--chipset','OCS','--video','PAL','--cpu','68000','--chip','512K',
              '--slow','0','--fast','0','--noaudio','--audio-wav',str(directory/'native.wav'),
              '--record-input',str(directory/'inputs.record'),config['inputs']['amiga_rom']]
        launch={'binary':config['tools']['copperline'],'args':args}
        boot_samples=[]
        boot_allocations=[]
        boot_calibration=None
        if boot_adf:
            args += ['--floppy-drives','1','--floppy-speed','100']
        else:
            launch['run']=str(exe)
        s.inspect('session_launch',launch)
        if boot_adf:
            s.inspect('media.floppy.insert',{'drive':0,'path':str(boot_adf),'write_protected':True})
            catch=s.inspect('break.add',{'kind':'loadseg','name':'baseline-rally'})
            calibrated_stop=s.inspect('run_until',{'seconds':120})
            if calibrated_stop['reason']!='loadseg':raise RuntimeError('ADF calibration did not load product')
            def boot_read(a,n):return bytes.fromhex(s.inspect('mem_read',{'addr':a,'len':n})['data'])
            boot_calibration=chip_memory(boot_read)
            s.inspect('break.remove',{'id':catch['id']})
            s.inspect('machine.reset',{'kind':'cold'})
            headers={r['header']:bytearray(32) for r in boot_calibration['regions']}
            free_counts={}
            free_stores={h:LongwordObserver() for h in headers}
            def boot_event(message, log=True):
                if log:raw.write(json.dumps(message)+'\n')
                if message.get('method')!='event.mmio':return
                row=message['params'];a,v,n=row['addr'],row['value'],row['size']
                if row.get('dropped_events',0) or row.get('dropped_notifications',0):
                    failures.append({'field':'boot allocation telemetry drop'})
                for region in boot_calibration['regions']:
                    h=region['header']
                    if h<=a and a+n<=h+32:
                        headers[h][a-h:a-h+n]=v.to_bytes(n,'big')
                        data=headers[h]
                        # Exec's long RMW stores may write low word FIRST. A
                        # sample needs both words from the same instruction;
                        # mixed old/new halves invent64KB allocation changes.
                        if (h+28<=a and a+n<=h+32 and int.from_bytes(data[14:16],'big')&2
                                and int.from_bytes(data[20:24],'big')==region['lower']
                                and int.from_bytes(data[24:28],'big')==region['upper']):
                            free=free_stores[h].write(a-h-28,v,n,row['pc'])
                            if free is None:continue
                            if free>region['upper']-region['lower']:
                                failures.append({'field':'invalid boot free-count update'})
                            free_counts[h]=free
                            if len(free_counts)==len(headers):
                                boot_allocations.append({'position':row['position'],'pc':row['pc'],
                                    'free_counts':dict(free_counts),'used_chip_bytes':CHIP_BYTES-sum(free_counts.values())})
            s.notification_handler=boot_event
            s.inspect('events.subscribe',{'events':['mmio'],'mmio':[
                {'addr':h,'len':32,'access':'write'} for h in headers]})
            catch=s.inspect('break.add',{'kind':'loadseg','name':'baseline-rally'})
            # Read-only samples during boot are lower-bound observations, not
            # an unobserved transient allocation peak. Play is uninterrupted.
            for frame in range(1,6000):
                stop=s.inspect('run_until',{'frame':frame})
                if stop['reason']=='loadseg':break
                if stop['reason']!='target':raise RuntimeError(stop)
                if frame%50==0:
                    try:
                        def boot_read(a,n):return bytes.fromhex(s.inspect('mem_read',{'addr':a,'len':n})['data'])
                        boot_samples.append({'position':stop,'memory':chip_memory(boot_read)})
                    except ValueError:pass # Exec free list not initialized yet
            s.inspect('break.remove',{'id':catch['id']})
        else:
            stop=s.inspect('run_until',{'seconds':30})
        if stop['reason']!='loadseg':raise RuntimeError(stop)
        base = int(re.search(r'first hunk \$([0-9A-Fa-f]+)', stop['detail'])[1], 16)
        address = {n: base+symbols[n] for n in ('simulation_updates', 'simulation_started_updates',
            'simulation_timer_origin', 'game_lifecycle', 'game_input_bits', 'display_ready',
            'front_copper','back_copper','copper_write_delta','sprite_write_delta','game_title_display')}
        # These buffers are in the chip-data hunk, not hunk0. Resolve the
        # compiled section offsets against the actual LoadSeg hunk addresses.
        segments = s.inspect('segments.list')['current']
        if segments[0]['start']!=base:
            raise ValueError('LoadSeg code base differs from actual hunk list')
        located = {n:(int(h),int(o,16)) for n,h,o in re.findall(
            r'^([A-Za-z_][\w]*)\s+(\d\d):([0-9A-Fa-f]{8})\s*$',listing.read_text(),re.M)}
        banks = {}
        for n in ('copperlist','copperlist_back','title_copper','sprite0','sprite_back'):
            h,offset=located[n]
            if offset>=segments[h]['size']: raise ValueError('Buffer symbol outside loaded hunk')
            banks[n]=segments[h]['start']+offset
        pointer_addresses = {n:address[n] for n in pointer_bytes if n!='cop1lc'}
        pointer_addresses['cop1lc']=0xdff080
        native_fields=field_addresses(base,symbols)
        address_fields={address:name for name,address in native_fields.items()}
        def read(a, n):
            return bytes.fromhex(s.inspect('mem_read', {'addr': a, 'len': n})['data'])
        loaded_checks=loaded_hunks(exe,segments,read)
        initial_memory = chip_memory(read)
        if boot_adf and [r['header'] for r in initial_memory['regions']]!=list(headers):
            raise ValueError('Cold-reset memory pool differs from actual calibration')

        setup_observer=SetupObserver(base,symbols,listing.read_text())
        entry_stop=s.inspect('run_until',{'pc':base+symbols['start']})
        entry_regs=s.inspect('regs.get')
        task=int.from_bytes(read(initial_memory['execbase']+0x114,4),'big')
        cli=4*int.from_bytes(read(task+0xac,4),'big')
        entry_stack={'sp':entry_regs['a'][7],'cli_default_bytes':4*int.from_bytes(read(cli+0x34,4),'big'),
                     'native_lower':base+symbols['game_stack_bottom'],'native_upper':base+symbols['game_stack_top']}

        title_initial = read(address['game_title_display'],1)[0]
        state['title']=title_initial
        native_state.update(read_native_state(s,base,symbols))
        for port in (1, 2):
            s.inspect('input_set_port', {'port': port, 'device': 'joystick'})
        def send(method, params):
            ident = s.send_async(method, params)
            inputs.append({'id': ident, 'method': method, 'params': params,
                           'observed_callback': state['completed']})
        def action_buttons(held):
            if keyboard:
                for key in (0x23,0x39):send('input.key',{'rawkey':key,'action':'press' if held else 'release'})
            else:
                for port in (1,2):send('input.joy',{'port':port,'red':held})
        def selection_key(chosen):
            return (0x01 if chosen=='one' else 0x02) if keyboard else (0x46 if chosen=='one' else 0x42)
        def milestone(label, position):
            if label in checkpoints:
                return
            checkpoints[label] = {'callback': state['completed'], 'position': position,
                                  'lifecycle': state['lifecycle'], 'state': dict(native_state),
                                  'controls': controls.hex()}
            send('capture.screenshot', {'path': str(directory/(label+'.png'))})
            send('custom.dump', {})
        def fault(field, **details):
            if len(failures) < 20:
                failures.append({'field': field, 'callback': state['completed'], **details})
        def on_callback(position):
            n, lifecycle = state['completed'], state['lifecycle']
            callbacks[-1].update(lifecycle=lifecycle, score=list(bytes([native_state['game_point_a'], native_state['game_point_b'], native_state['game_games_a'], native_state['game_games_b']])),
                                 flight=native_state['game_flight'], controls=controls.hex())
            if lifecycle == 2 and state['initial_selected'] is None:
                milestone('initial_title', position)
                send('input.key', {'rawkey': selection_key(mode), 'action': 'press'})
                state['initial_selected'] = n
            if lifecycle == 3 and 'first_selection' not in checkpoints:
                milestone('first_selection', position)
            if 'first_selection' in checkpoints and 'first_release' not in checkpoints and n-checkpoints['first_selection']['callback'] >= 80:
                milestone('first_release', position)
                send('input.key', {'rawkey': selection_key(mode), 'action': 'release'})
            if lifecycle == 1 and 'first_play' not in checkpoints:
                milestone('first_play', position)
                action_buttons(True)
            if lifecycle == 1 and native_state['game_flight'] and native_state['game_step']:
                milestone('restarted_flight' if 'restart_play' in checkpoints else 'first_flight', position)
            if any(bytes([native_state['game_point_a'], native_state['game_point_b']])): milestone('point', position)
            if any(bytes([native_state['game_games_a'], native_state['game_games_b']])): milestone('game', position)
            if lifecycle in (4, 5):
                milestone('pause', position)
                pose = bytes([native_state['game_upper_y'], native_state['game_upper_x'], native_state['game_upper_image'], native_state['game_upper_colour'], native_state['game_lower_y'], native_state['game_lower_x'], native_state['game_lower_image'], native_state['game_lower_colour']]).hex()
                if state['pause_pose'] is None: state['pause_pose'] = pose
                elif state['pause_pose'] != pose: fault('movement during round pause')
            else:
                if state['pause_pose'] is not None and lifecycle == 1: milestone('resume', position)
                state['pause_pose'] = None
            if lifecycle == 6:
                milestone('result', position)
                if max(bytes([native_state['game_games_a'], native_state['game_games_b']])) != 6 or any(bytes([native_state['game_point_a'], native_state['game_point_b']])): fault('result before six-game completion')
            if lifecycle == 7: milestone('returned_title', position)
            if lifecycle == 2 and 'result' in checkpoints and state['restart_selected'] is None:
                milestone('restart_title_ready', position)
                send('input.key', {'rawkey': selection_key(restarted), 'action': 'press'})
                state['restart_selected'] = n
            if state['restart_selected'] is not None and lifecycle == 3:
                milestone('restart_selection', position)
                if bool(native_state['game_mode']&128) != (restarted == 'two') or any(bytes([native_state['game_point_a'], native_state['game_point_b'], native_state['game_games_a'], native_state['game_games_b']])): fault('restart mode/score')
                if n-checkpoints['restart_selection']['callback'] >= 80 and 'restart_release' not in checkpoints:
                    milestone('restart_release', position)
                    send('input.key', {'rawkey': selection_key(restarted), 'action': 'release'})
            if state['restart_selected'] is not None and lifecycle == 1:
                milestone('restart_play', position)
                if 'held_blocked' not in checkpoints and n-checkpoints['restart_play']['callback'] >= 80:
                    if native_state['game_flight'] or any(bytes([native_state['game_point_a'], native_state['game_point_b'], native_state['game_games_a'], native_state['game_games_b']])) or any(v&0x30 for v in controls[6:8]): fault('held old action escaped')
                    milestone('held_blocked', position)
                    action_buttons(False)
                if 'held_blocked' in checkpoints and n-checkpoints['held_blocked']['callback'] >= 80 and 'fresh_action' not in checkpoints:
                    milestone('fresh_action', position)
                    action_buttons(True)
            if 'restarted_flight' in checkpoints and 'finished' not in checkpoints:
                milestone('finished', position)
                send('pause', {})  # the only stop after entry, at completed acceptance
        def event(message):
            raw.write(json.dumps(message, separators=(',', ':'))+'\n')
            if 'id' in message:
                replies[str(message['id'])] = message
                if 'error' in message: fault('asynchronous control error', error=message['error'])
                return
            if message.get('method') != 'event.mmio': return
            if boot_adf:boot_event(message,log=False)
            r = message['params']; a, value, size = r['addr'], r['value'], r['size']
            position = r['position']
            setup_observer.observe(r)
            if r.get('dropped_events', 0) or r.get('dropped_notifications', 0): fault('telemetry drop')
            for field, start in pointer_addresses.items():
                if start<=a and a+size<=start+4:
                    pointer_bytes[field][a-start:a-start+size]=value.to_bytes(size,'big')
            if a==address['game_title_display']:
                state['title']=value
                view_selections.append({'title':bool(value),'position':position})
            if any(a+i in address_fields for i in range(size)):
                for i,v in enumerate(value.to_bytes(size,'big')):
                    if a+i in address_fields:native_state[address_fields[a+i]]=v
            elif address['game_input_bits'] <= a < address['game_input_bits']+8:
                controls[a-address['game_input_bits']:a-address['game_input_bits']+size] = value.to_bytes(size, 'big')
            elif a == address['game_lifecycle']:
                state['lifecycle'] = value
                changes.append(r)
            elif a == 0xbfde00 and value == 1: state['start'] = position['cck']
            elif a == address['simulation_timer_origin']: state['origin'] = value
            elif a == address['simulation_started_updates']:
                if value != state['started']+1 or state['completed'] != state['started']: fault('start sequence')
                state['started'] = value
                callbacks.append({'callback': value, 'entry': position})
            elif a == address['simulation_updates']:
                if value != state['completed']+1 or value != state['started']: fault('completion sequence')
                state['completed'] = value
                callbacks[-1]['completion'] = position
                on_callback(position)
            elif a == address['display_ready']:
                state['ready'] = state['started'] if value else None
                if value:
                    pointer = int.from_bytes(pointer_bytes['back_copper'],'big')
                    delta = int.from_bytes(pointer_bytes['copper_write_delta'],'big')
                    sprite_delta = int.from_bytes(pointer_bytes['sprite_write_delta'],'big')
                    expected_sprite_delta = banks['sprite_back']-banks['sprite0'] if pointer==banks['copperlist_back'] else 0
                    if pointer not in (banks['copperlist'],banks['copperlist_back']) or delta!=pointer-banks['copperlist'] or sprite_delta!=expected_sprite_delta:
                        fault('prepared bank/delta mismatch',pointer=pointer,delta=delta,sprite_delta=sprite_delta)
                    state['prepared']={'generation':state['started'],'bank':pointer,
                        'title_at_prepare':bool(state['title']),'position':position}
                    preparations.append(dict(state['prepared']))
            elif a == 0xdff088 and state['start'] is not None:
                generation = state['ready']
                # A frozen menu tick advances simulation but prepares no new
                # scene. Publish the latest prepared completed scene, not an
                # invented scene for the latest menu service callback.
                if generation is None or generation > state['completed'] or generation <= state['last_commit']: fault('stale/unprepared presentation', generation=generation)
                if generation is not None: state['last_commit'] = generation
                pointer = int.from_bytes(pointer_bytes['cop1lc'],'big')
                prepared = state['prepared']
                # The main lifecycle can explicitly select the permanently
                # prepared title or the completed court between callbacks.
                # Observe that page selection independently of scene readiness.
                expected = banks['title_copper'] if state['title'] else prepared['bank'] if prepared else None
                if pointer != expected:
                    fault('published Copper bank',generation=generation,expected_pointer=expected,actual_pointer=pointer)
                    if bank_control and not state['bank_fault_pause']:
                        state['bank_fault_pause']=True
                        send('pause',{})
                commits.append({'generation': generation, 'position': position,'pointer':pointer,
                                'prepared':dict(prepared) if prepared else None,
                                'title_selected':bool(state['title']),'expected_pointer':expected})
            if a in (0xdff080, 0xdff082, 0xdff088) and state['start'] is not None and 44 <= position['vpos'] < 252:
                fault('visible-line Copper commit', position=position)
            if (a in (0xdff080, 0xdff082, 0xdff088) and state['start'] is not None
                    and not state['title'] and 25 <= position['vpos'] < 252):
                fault('court bank publication after sprite header DMA starts', position=position)
            if any(h['header'] <= a < h['header']+32 for h in initial_memory['regions']) or initial_memory['execbase']+0x142 <= a < initial_memory['execbase']+0x14e:
                memory_writes.append(r)
        if boot_adf:s.inspect('events.unsubscribe')
        s.notification_handler = event
        watches = [{'addr': a, 'len': 4 if n in pointer_bytes else 1 if n in ('display_ready','game_title_display') else 2, 'access': 'write'} for n, a in address.items()]
        watches += [{'addr': address['game_input_bits'], 'len': 8, 'access': 'write'},
                    *[{'addr':a,'len':1,'access':'write'} for name,a in native_fields.items() if name in ('game_flight','game_contact','game_lower_phase','game_upper_phase','game_score_flags','game_mode','game_point_a','game_point_b','game_games_a','game_games_b','game_display','game_lower_animation','game_upper_animation','game_upper_y','game_upper_x','game_upper_image','game_upper_colour','game_lower_y','game_lower_x','game_lower_image','game_lower_colour','game_step')],
                    {'addr': 0xdff080, 'len': 4, 'access': 'write'},
                    {'addr': 0xdff088, 'len': 2, 'access': 'write'},
                    {'addr': 0xbfde00, 'len': 1, 'access': 'write'},
                    {'addr': initial_memory['execbase']+0x142, 'len': 12, 'access': 'write'}]
        watches += [{'addr': h['header'], 'len': 32, 'access': 'write'} for h in initial_memory['regions']]
        watches += setup_observer.watches()
        s.inspect('events.subscribe', {'events': ['mmio'], 'mmio': watches})
        stop = s.inspect('run_until', {'seconds': stop['seconds']+(20 if bank_control else 1000)})
        s.inspect('events.unsubscribe')
        final_memory = chip_memory(read)
        s.notification_handler = None
    target_log(directory)
    # Live commands are serviced at an emulator boundary. Our final pause may
    # arrive after the next update entered. Preserve that unfinished suffix,
    # never call it a completed update or accept a gap inside the checked run.
    pending_callback = None
    if callbacks and 'completion' not in callbacks[-1]:
        if (callbacks[-1]['callback'] == state['completed']+1 and stop['reason']=='pause'
                and (checkpoints.get('finished',{}).get('callback') == state['completed'] or state['bank_fault_pause'])):
            pending_callback = callbacks.pop()
        else:
            fault('unexpected incomplete callback')
    required = ('initial_title', 'first_selection', 'first_release', 'first_play', 'first_flight',
                'point', 'game', 'pause', 'resume', 'result', 'returned_title', 'restart_title_ready',
                'restart_selection', 'restart_release', 'restart_play', 'held_blocked', 'fresh_action', 'restarted_flight', 'finished')
    for label in (() if bank_control else required):
        if label not in checkpoints: fault('missing milestone', milestone=label)
    origin = state['start']+(65535-state['origin'])*5 if state['start'] is not None and state['origin'] is not None else None
    maximum_late, maximum_work, minimum_phase = 0, 0, None
    for row in callbacks:
        n = row['callback']
        ideal = (n-1) * INTERVAL_CCK
        allowance = 5+5+Fraction((n-1)*5, 2*65536)  # origin + fractional tick quantization + rounding
        if origin is None or 'completion' not in row:
            fault('missing clock origin/completion'); continue
        phase = row['entry']['cck']-origin-ideal
        completion = row['completion']['cck']-origin-ideal
        interval = INTERVAL_CCK
        if phase < -allowance or phase >= interval+allowance or completion >= interval+allowance:
            fault('native deadline', measured_callback=n, entry_phase_cck=float(phase), completion_phase_cck=float(completion))
        minimum_phase = float(phase) if minimum_phase is None else min(minimum_phase, float(phase))
        maximum_late = max(maximum_late, float(phase))
        maximum_work = max(maximum_work, row['completion']['cck']-row['entry']['cck'])
    active_memory_writes = [r for r in memory_writes if state['start'] is not None and r['position']['cck'] >= state['start']]
    if active_memory_writes: fault('ordinary allocation/topology changed; peak not established')
    if final_memory['used_chip_bytes'] >= CHIP_BYTES: fault('chip RAM exhausted')
    for row in inputs:
        if str(row['id']) not in replies: fault('missing asynchronous reply', id=row['id'])
    capture = directory/'measurement.json'
    atomic_json(capture, {'clock_contract': contract, 'clock_origin_cck': origin, 'callbacks': callbacks,
                         'base': base, 'addresses': address, 'native_fields':native_fields, 'watch_ranges': watches,
                         'timer_start_cck': state['start'], 'timer_origin_count': state['origin'],
                         'bank_addresses':banks,'prepared_scenes':preparations,
                         'title_initial':bool(title_initial),'view_selections':view_selections,
                         'loaded_hunks':segments,'loaded_executable_checks':loaded_checks,'launch':launch,'entry_stack':entry_stack,'entry_stop':entry_stop,'boot_samples':boot_samples,'boot_allocations':boot_allocations,'boot_calibration':boot_calibration,
                         'pending_final_callback': pending_callback,
                         'commits': commits, 'lifecycle_changes': changes, 'memory_initial': initial_memory,
                         'memory_final': final_memory, 'memory_writes': memory_writes,
                         'inputs': inputs, 'replies': replies, 'stop': stop, 'checkpoints': checkpoints,'explicit_setup_regions':setup_observer.regions})
    if boot_adf:
        if any(store.seen for store in free_stores.values()):
            fault('cold boot allocator incomplete final long store')
        if not boot_allocations or boot_allocations[0]['position']['cck']>=state['start']:
            fault('cold boot allocator observation absent')
        elif boot_allocations[-1]['used_chip_bytes']!=final_memory['used_chip_bytes']:
            fault('cold boot allocator final count differs from actual free list')
    if boot_adf and __import__('hashlib').sha256(boot_adf.read_bytes()).hexdigest()!=adf_sha:
        fault('ADF changed during execution')
    report = {'case': name, 'subject': 'maintained-native', 'passed': not failures,
              'first_difference': failures[0] if failures else None, 'differences': failures,
              'start_mode': mode, 'restart_mode': restarted, 'startup': 'cold ADF' if boot_adf else 'ordinary title',
              'entropy': 'ordinary native timer', 'uninterrupted': True, 'callback_breakpoints': 0,
              'observed_callbacks': len(callbacks), 'checkpoints': checkpoints,
              'started_callbacks': state['started'], 'pending_final_callback': pending_callback,
              'cadence': {'minimum_phase_cck': minimum_phase, 'maximum_entry_late_cck': maximum_late,
                          'maximum_update_work_cck': maximum_work, 'clock_contract': contract},
              'presentation': {'commits': len(commits), 'latest_prepared_completed_epoch':
                               not any(f['field'] in ('stale/unprepared presentation','published Copper bank','prepared bank/delta mismatch') for f in failures),
                               'actual_pointer_checked':True},
              'memory': {'peak_chip_bytes': final_memory['used_chip_bytes'] if not active_memory_writes else None,
                         'scope': 'CIA timer start through restarted flight, including resident OS/application/allocated stack; pre-timer peak not claimed',
                         'continuous_allocation_watch': not active_memory_writes, 'cold_disk_boot': 'observed' if boot_adf else 'unverified','cold_boot_peak':max((r['used_chip_bytes'] for r in boot_allocations),default=None),
                         'cold_boot_peak_scope':'first initialized Exec chip pool through restarted flight; pre-pool bootstrap transient usage unverified'},
              'phase_contract_proposal':setup_observer.proposal(callbacks,origin) if origin is not None else {'diagnostic_passed':False,'issues':['missing clock origin']},
              'capture': str(capture.relative_to(ROOT)), 'audio_wav': str((directory/'native.wav').relative_to(ROOT)),
              'loaded_executable_verified':all(c['matched'] for c in loaded_checks),
              'adf':str(boot_adf.relative_to(ROOT)) if boot_adf else None,'adf_sha256':adf_sha,
              'scope': 'Uninterrupted native ordinary lifecycle/cadence; boot samples do not establish cold-boot transient peak; no original full-match/pixel/waveform parity'}
    atomic_json(ROOT/f'build/tests/{name}-report.json', report)
    if bank_control:
        wrong = [f for f in failures if f['field']=='published Copper bank']
        detected = bool(wrong and wrong[0]['generation']>=200 and any(c['generation']<200 for c in commits))
        report.update(passed=detected, first_difference=None if detected else {'field':'wrong bank control escaped'},
                      subject='maintained-native-mutant',detected_failure=wrong[0] if wrong else None,
                      normal_executable_sha256=__import__('hashlib').sha256(ordinary.read_bytes()).hexdigest(),
                      scope='Delayed actual stale COP1LC bank; readiness/callback/gameplay counters unchanged. Not complete ordinary acceptance.')
        atomic_json(ROOT/f'build/tests/{name}-report.json',report)
    print(json.dumps({k: v for k, v in report.items() if k not in ('checkpoints', 'differences')}), flush=True)
    return 0 if report['passed'] else 1
