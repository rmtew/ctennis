"""CT09's finite non-stopping ordinary play measurement, not a reference model."""
import csv
from fractions import Fraction
import json
import re
import shutil

from build_native_game import build
from capture_native_presentation import code_symbols
from copperline_test_session import NativeControlSession
from evidence import ROOT, atomic_json, compile_manifest

CCK_HZ = 3546895
ECLK_HZ = 709379
CHIP_BYTES = 524288


def clock_contract():
    periods, extents = [], {}
    for mode in ('one', 'two'):
        path = ROOT / f'tests/reference/audio/{mode}-player-match/a/frame-times.tsv'
        with path.open() as handle:
            rows = list(csv.DictReader(handle, delimiter='\t'))
        times = [int(r['seconds']) * 10**18 + int(r['attoseconds']) for r in rows]
        deltas = set(b-a for a, b in zip(times, times[1:]))
        if len(deltas) != 1:
            raise ValueError('Source frame period is not constant')
        periods.append(deltas.pop())
        reference = json.loads((ROOT/f'tests/reference/{mode}-player-match.json').read_text())
        # Start-of-callback frames establish cadence. A pre-tail checkpoint
        # can cross a video boundary during a long source callback; its frame
        # label is not a second invocation or a skipped source tick.
        frames = [reference['initial_callback']['begin_frame']] + [r['begin_frame'] for r in reference['updates']]
        if any(b-a != 1 for a, b in zip(frames, frames[1:])):
            raise ValueError('Full source callback cadence is not one update per frame')
        extents[mode] = {'updates': len(reference['updates']), 'first_frame': frames[0], 'last_frame': frames[-1]}
    if periods[0] != periods[1]:
        raise ValueError('Source modes have different frame periods')
    ticks = Fraction(periods[0] * ECLK_HZ, 10**18)
    fixed = round(ticks * 65536)
    return {'source_period_attoseconds': periods[0], 'eclock_hz': ECLK_HZ,
            'cck_hz': CCK_HZ, 'cck_per_eclock': 5, 'interval_16_16': fixed,
            'resolution_cck': 1, 'origin_uncertainty_cck': 5,
            'source_callback_extents': extents,
            'interval_rounding_error_eclock': '<= N/(2*65536)',
            'rules': {'entry': 'not before source deadline minus quantization; before next deadline',
                      'completion': 'before next deadline',
                      'publication': 'physical beam outside visible rows 44..235; latest completed prepared epoch',
                      'telemetry': 'zero missing, duplicate or dropped events',
                      'memory': 'validated Exec chip free list; continuously observe topology/free mutations',
                      'entropy': 'ordinary native timer; no captured-phase or recorded entropy initialization'}}


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


def run(mode):
    config, ordinary = build()
    name = f'ct09-ordinary-{mode}-cadence'
    directory = ROOT / f'build/tests/{name}'
    directory.mkdir(parents=True, exist_ok=True)
    exe, listing = directory/'native-application', directory/'native.lst'
    shutil.copy2(ordinary, exe)
    shutil.copy2(ordinary.parent/'native.lst', listing)
    compile_manifest(exe, listing)
    symbols = code_symbols(listing.read_text())
    if 'refresh_signs' in symbols or 'initial_ram' in symbols:
        raise ValueError('Ordinary cadence subject contains captured initialization/entropy')
    contract = clock_contract()
    atomic_json(directory/'clock-contract.json', contract)  # before execution
    failures, checkpoints, inputs, replies, changes = [], {}, [], {}, []
    callbacks, commits, memory_writes = [], [], []
    ram, controls = bytearray(256), bytearray(8)
    state = {'lifecycle': 0, 'started': 0, 'completed': 0, 'ready': None,
             'released': False, 'initial_selected': None, 'restart_selected': None,
             'last_commit': 0, 'start': None, 'origin': None, 'pause_pose': None}
    restarted = 'two' if mode == 'one' else 'one'
    with NativeControlSession(directory) as s, (directory/'events.jsonl').open('w') as raw:
        s.inspect('session_launch', {'binary': config['tools']['copperline'], 'run': str(exe),
            'args': ['--chipset', 'OCS', '--video', 'PAL', '--cpu', '68000', '--chip', '512K',
                     '--slow', '0', '--fast', '0', '--noaudio', '--audio-wav',
                     str(directory/'native.wav'), '--record-input', str(directory/'inputs.record'),
                     config['inputs']['amiga_rom']]})
        stop = s.inspect('run_until', {'seconds': 30})
        if stop['reason'] != 'loadseg':
            raise RuntimeError(stop)
        base = int(re.search(r'first hunk \$([0-9A-Fa-f]+)', stop['detail'])[1], 16)
        address = {n: base+symbols[n] for n in ('simulation_updates', 'simulation_started_updates',
            'simulation_timer_origin', 'game_lifecycle', 'game_input_bits', 'display_ready')}
        virtual = base+symbols['virtual_memory']+0xc000
        def read(a, n):
            return bytes.fromhex(s.inspect('mem_read', {'addr': a, 'len': n})['data'])
        initial_memory = chip_memory(read)
        ram[:] = read(virtual, 256)
        for port in (1, 2):
            s.inspect('input_set_port', {'port': port, 'device': 'joystick'})
        def send(method, params):
            ident = s.send_async(method, params)
            inputs.append({'id': ident, 'method': method, 'params': params,
                           'observed_callback': state['completed']})
        def milestone(label, position):
            if label in checkpoints:
                return
            checkpoints[label] = {'callback': state['completed'], 'position': position,
                                  'lifecycle': state['lifecycle'], 'ram': ram.hex(),
                                  'controls': controls.hex()}
            send('capture.screenshot', {'path': str(directory/(label+'.png'))})
            send('custom.dump', {})
        def fault(field, **details):
            if len(failures) < 20:
                failures.append({'field': field, 'callback': state['completed'], **details})
        def on_callback(position):
            n, lifecycle = state['completed'], state['lifecycle']
            callbacks[-1].update(lifecycle=lifecycle, score=list(ram[0x3e:0x42]),
                                 flight=ram[0x38], controls=controls.hex())
            if lifecycle == 2 and state['initial_selected'] is None:
                milestone('initial_title', position)
                send('input.key', {'rawkey': 0x46 if mode == 'one' else 0x42, 'action': 'press'})
                state['initial_selected'] = n
            if lifecycle == 3 and 'first_selection' not in checkpoints:
                milestone('first_selection', position)
            if 'first_selection' in checkpoints and 'first_release' not in checkpoints and n-checkpoints['first_selection']['callback'] >= 80:
                milestone('first_release', position)
                send('input.key', {'rawkey': 0x46 if mode == 'one' else 0x42, 'action': 'release'})
            if lifecycle == 1 and 'first_play' not in checkpoints:
                milestone('first_play', position)
                for port in (1, 2): send('input.joy', {'port': port, 'red': True})
            if lifecycle == 1 and ram[0x38] and ram[0x66]:
                milestone('restarted_flight' if 'restart_play' in checkpoints else 'first_flight', position)
            if any(ram[0x3e:0x40]): milestone('point', position)
            if any(ram[0x40:0x42]): milestone('game', position)
            if lifecycle in (4, 5):
                milestone('pause', position)
                pose = ram[0x45:0x4d].hex()
                if state['pause_pose'] is None: state['pause_pose'] = pose
                elif state['pause_pose'] != pose: fault('movement during round pause')
            else:
                if state['pause_pose'] is not None and lifecycle == 1: milestone('resume', position)
                state['pause_pose'] = None
            if lifecycle == 6:
                milestone('result', position)
                if max(ram[0x40:0x42]) != 6 or any(ram[0x3e:0x40]): fault('result before six-game completion')
            if lifecycle == 7: milestone('returned_title', position)
            if lifecycle == 2 and 'result' in checkpoints and state['restart_selected'] is None:
                milestone('restart_title_ready', position)
                send('input.key', {'rawkey': 0x42 if restarted == 'two' else 0x46, 'action': 'press'})
                state['restart_selected'] = n
            if state['restart_selected'] is not None and lifecycle == 3:
                milestone('restart_selection', position)
                if bool(ram[0x3d]&128) != (restarted == 'two') or any(ram[0x3e:0x42]): fault('restart mode/score')
                if n-checkpoints['restart_selection']['callback'] >= 80 and 'restart_release' not in checkpoints:
                    milestone('restart_release', position)
                    send('input.key', {'rawkey': 0x42 if restarted == 'two' else 0x46, 'action': 'release'})
            if state['restart_selected'] is not None and lifecycle == 1:
                milestone('restart_play', position)
                if 'held_blocked' not in checkpoints and n-checkpoints['restart_play']['callback'] >= 80:
                    if ram[0x38] or any(ram[0x3e:0x42]) or any(v&0x30 for v in controls[6:8]): fault('held old action escaped')
                    milestone('held_blocked', position)
                    for port in (1, 2): send('input.joy', {'port': port, 'red': False})
                if 'held_blocked' in checkpoints and n-checkpoints['held_blocked']['callback'] >= 80 and 'fresh_action' not in checkpoints:
                    milestone('fresh_action', position)
                    for port in (1, 2): send('input.joy', {'port': port, 'red': True})
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
            r = message['params']; a, value, size = r['addr'], r['value'], r['size']
            position = r['position']
            if r.get('dropped_events', 0) or r.get('dropped_notifications', 0): fault('telemetry drop')
            if virtual <= a < virtual+256:
                ram[a-virtual:a-virtual+size] = value.to_bytes(size, 'big')
            elif address['game_input_bits'] <= a < address['game_input_bits']+8:
                controls[a-address['game_input_bits']:a-address['game_input_bits']+size] = value.to_bytes(size, 'big')
            elif a == address['game_lifecycle']:
                state['lifecycle'] = value
                changes.append(r)
            elif a == 0xbfdf00 and value == 1: state['start'] = position['cck']
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
            elif a == 0xdff088 and state['start'] is not None:
                generation = state['ready']
                # A frozen menu tick advances simulation but prepares no new
                # scene. Publish the latest prepared completed scene, not an
                # invented scene for the latest menu service callback.
                if generation is None or generation > state['completed'] or generation <= state['last_commit']: fault('stale/unprepared presentation', generation=generation)
                if generation is not None: state['last_commit'] = generation
                commits.append({'generation': generation, 'position': position})
            if a in (0xdff080, 0xdff082, 0xdff088) and state['start'] is not None and 44 <= position['vpos'] < 236:
                fault('visible-line Copper commit', position=position)
            if any(h['header'] <= a < h['header']+32 for h in initial_memory['regions']) or initial_memory['execbase']+0x142 <= a < initial_memory['execbase']+0x14e:
                memory_writes.append(r)
        s.notification_handler = event
        watches = [{'addr': a, 'len': 2 if n != 'display_ready' else 1, 'access': 'write'} for n, a in address.items()]
        watches += [{'addr': address['game_input_bits'], 'len': 8, 'access': 'write'},
                    {'addr': virtual+0x38, 'len': 0x4d-0x38, 'access': 'write'},
                    {'addr': virtual+0x66, 'len': 1, 'access': 'write'},
                    {'addr': 0xdff080, 'len': 4, 'access': 'write'},
                    {'addr': 0xdff088, 'len': 2, 'access': 'write'},
                    {'addr': 0xbfdf00, 'len': 1, 'access': 'write'},
                    {'addr': initial_memory['execbase']+0x142, 'len': 12, 'access': 'write'}]
        watches += [{'addr': h['header'], 'len': 32, 'access': 'write'} for h in initial_memory['regions']]
        s.inspect('events.subscribe', {'events': ['mmio'], 'mmio': watches})
        stop = s.inspect('run_until', {'seconds': stop['seconds']+1000})
        s.inspect('events.unsubscribe')
        final_memory = chip_memory(read)
        s.notification_handler = None
    # Live commands are serviced at an emulator boundary. Our final pause may
    # arrive after the next update entered. Preserve that unfinished suffix,
    # never call it a completed update or accept a gap inside the checked run.
    pending_callback = None
    if callbacks and 'completion' not in callbacks[-1]:
        if (callbacks[-1]['callback'] == state['completed']+1 and stop['reason']=='pause'
                and checkpoints.get('finished',{}).get('callback') == state['completed']):
            pending_callback = callbacks.pop()
        else:
            fault('unexpected incomplete callback')
    required = ('initial_title', 'first_selection', 'first_release', 'first_play', 'first_flight',
                'point', 'game', 'pause', 'resume', 'result', 'returned_title', 'restart_title_ready',
                'restart_selection', 'restart_release', 'restart_play', 'held_blocked', 'fresh_action', 'restarted_flight', 'finished')
    for label in required:
        if label not in checkpoints: fault('missing milestone', milestone=label)
    origin = state['start']+(65535-state['origin'])*5 if state['start'] is not None and state['origin'] is not None else None
    maximum_late, maximum_work, minimum_phase = 0, 0, None
    for row in callbacks:
        n = row['callback']
        ideal = Fraction((n-1)*contract['source_period_attoseconds']*CCK_HZ, 10**18)
        allowance = 5+5+Fraction((n-1)*5, 2*65536)  # origin + fractional tick quantization + rounding
        if origin is None or 'completion' not in row:
            fault('missing clock origin/completion'); continue
        phase = row['entry']['cck']-origin-ideal
        completion = row['completion']['cck']-origin-ideal
        interval = Fraction(contract['source_period_attoseconds']*CCK_HZ, 10**18)
        if phase < -allowance or phase >= interval+allowance or completion >= interval+allowance:
            fault('source deadline', measured_callback=n, entry_phase_cck=float(phase), completion_phase_cck=float(completion))
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
                         'base': base, 'addresses': address, 'virtual_state': virtual, 'watch_ranges': watches,
                         'timer_start_cck': state['start'], 'timer_origin_count': state['origin'],
                         'pending_final_callback': pending_callback,
                         'commits': commits, 'lifecycle_changes': changes, 'memory_initial': initial_memory,
                         'memory_final': final_memory, 'memory_writes': memory_writes,
                         'inputs': inputs, 'replies': replies, 'stop': stop, 'checkpoints': checkpoints})
    report = {'case': name, 'subject': 'maintained-native', 'passed': not failures,
              'first_difference': failures[0] if failures else None, 'differences': failures,
              'start_mode': mode, 'restart_mode': restarted, 'startup': 'ordinary title',
              'entropy': 'ordinary native timer', 'uninterrupted': True, 'callback_breakpoints': 0,
              'observed_callbacks': len(callbacks), 'checkpoints': checkpoints,
              'started_callbacks': state['started'], 'pending_final_callback': pending_callback,
              'cadence': {'minimum_phase_cck': minimum_phase, 'maximum_entry_late_cck': maximum_late,
                          'maximum_update_work_cck': maximum_work, 'clock_contract': contract},
              'presentation': {'commits': len(commits), 'latest_prepared_completed_epoch':
                               not any(f['field']=='stale/unprepared presentation' for f in failures)},
              'memory': {'peak_chip_bytes': final_memory['used_chip_bytes'] if not active_memory_writes else None,
                         'scope': 'ordinary executable entry through restarted flight, including OS allocation',
                         'continuous_allocation_watch': not active_memory_writes, 'cold_disk_boot': 'unverified'},
              'capture': str(capture.relative_to(ROOT)), 'audio_wav': str((directory/'native.wav').relative_to(ROOT)),
              'scope': 'Uninterrupted native ordinary lifecycle/cadence; no original full-match/pixel/waveform parity or ADF gate'}
    atomic_json(ROOT/f'build/tests/{name}-report.json', report)
    print(json.dumps({k: v for k, v in report.items() if k not in ('checkpoints', 'differences')}), flush=True)
    return 0 if report['passed'] else 1
