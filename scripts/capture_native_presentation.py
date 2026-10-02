"""Associate native presentation observations with exact live simulation callbacks.

Diagnostic capture, not a P1 pass: screenshots at CPU stops can contain partial
rasters. This records actual state and beam position without changing game RAM
or bypassing the application's input, scheduling, or hardware paths.
"""
import configparser
import argparse
import json
import re
from pathlib import Path

from copperline_test_session import CopperlineSession, NativeControlSession
from run_presentation_tests import ROOT, build_native, digest


def code_symbols(listing):
    return {name: int(offset, 16) for name, offset in
            re.findall(r'^([A-Za-z_][\w]*)\s+00:([0-9A-Fa-f]{8})\s*$', listing, re.M)}


def capture(targets=(0, 17, 18, 63, 134, 135, 136, 166), recorded_entropy=False, track_commits=False, completed_rasters=False, observe_audio=False, executable_mutator=None, initial_source_update=0, initial_phase_reference=None, capture_label=None, source_mutator=None, observe_fields=False, source_case='one-player-match', native_inputs=None, observe_state=False, observe_initial_fields=False, strict_source_events=True, presentation_reference_directory='tests/reference/presentation', native_input_schedule=None, interface_flavor="original", required_raster_generations=()):
    config = configparser.ConfigParser(interpolation=None)
    config.read(ROOT / 'config.local.ini', encoding='utf-8')
    directory = ROOT / ('build/tests/native-presentation-recorded' if recorded_entropy else 'build/tests/native-presentation-alignment')
    if capture_label:
        if not re.fullmatch(r'[a-z0-9-]+', capture_label):
            raise ValueError('Invalid private capture label')
        directory = directory.with_name(directory.name + '-' + capture_label)
    directory.mkdir(parents=True, exist_ok=True)
    report_path = directory / 'report.json'
    report_path.unlink(missing_ok=True)
    case = json.loads((ROOT / 'tests/cases/p1-title.json').read_text())
    if source_case not in ('one-player-match', 'two-player-match', 'one-player-restart-complete', 'two-player-restart-complete'):
        raise ValueError('Unsupported source parent')
    case['source_case'] = source_case
    case['interface_flavor']=interface_flavor
    if native_inputs is None:
        native_inputs = [{'port': 2, 'red': True}]
    if (not native_inputs or len({row.get('port') for row in native_inputs}) != len(native_inputs)
            or any(row.get('port') not in (1, 2)
                   or set(row) - {'port', 'up', 'down', 'left', 'right', 'red', 'blue'}
                   or any(type(value) is not bool for key, value in row.items() if key != 'port')
                   for row in native_inputs)):
        raise ValueError('Invalid physical joystick inputs')
    if initial_source_update:
        if not recorded_entropy or not initial_phase_reference:
            raise ValueError('Later graphics start requires a verified phase and recorded entropy')
        case['initial_phase_reference'] = initial_phase_reference
        phase = json.loads((ROOT / initial_phase_reference).read_text())
        if targets and targets[-1] > initial_source_update + len(phase['updates']):
            raise ValueError('Graphics targets extend beyond the independently verified phase')
    schedule = native_input_schedule or []
    if schedule and (not observe_state or any(row['after_callback'] < initial_source_update for row in schedule)):
        raise ValueError('Physical schedules require consecutive callback observation and valid epochs')
    applied_inputs = []
    source_path = ROOT / f'tests/reference/{source_case}.json'
    source = json.loads(source_path.read_text())
    frozen = json.loads((ROOT / f'{presentation_reference_directory}/{source_case}/manifest.json').read_text())
    if digest(source_path) != frozen['parent_reference_sha256']:
        raise ValueError('Source simulation reference changed relative to frozen presentation capture')
    if (not set(required_raster_generations) <= set(targets)
            or required_raster_generations and not completed_rasters):
        raise ValueError('Exact raster generations require declared completed-raster targets')
    if list(targets) != sorted(set(targets)) or not targets or targets[0] < initial_source_update or targets[-1] > len(source['updates']):
        raise ValueError('Callback targets must be unique, increasing and inside the source replay')
    executable = build_native(case, directory, recorded_refresh=recorded_entropy, initial_source_update=initial_source_update, source_mutator=source_mutator)
    if executable_mutator:
        executable_mutator(executable)
    symbols = code_symbols((directory / 'native.lst').read_text())
    observations = []
    commits = []
    prepared_scenes = []
    entropy_reads = []
    audio_events = []
    audio_ticks = []
    field_events = []
    state_events = []
    initial_fields = []
    source_event_differences = []
    ctl = Path(config['tools']['copperline']).with_name('copperline-ctl.exe')
    with (CopperlineSession(ctl, ROOT) if ctl.exists() else NativeControlSession(directory)) as session:
        launch = session.inspect('session_launch', {'factory': True, 'model': 'A500',
            'binary': config['tools']['copperline'], 'run': str(executable),
            'args': ['--chipset', 'OCS', '--video', 'PAL', '--cpu', '68000',
                     '--chip', '512K', '--slow', '0', '--fast', '0', '--noaudio',
                     *(['--audio-wav', str(directory / 'native.wav')] if observe_audio else []),
                     config['inputs']['amiga_rom']]})
        stop = session.inspect('run_until', {'seconds': 30, 'wait_ms': 50000})
        if stop['reason'] != 'loadseg':
            raise RuntimeError(f'Application not loaded: {stop}')
        base = int(re.search(r'first hunk \$([0-9A-Fa-f]+)', stop['detail']).group(1), 16)
        # Static title data lives in the chip-data hunk. Resolve its compiled
        # symbol against actual LoadSeg segments, never against the code base.
        segments = session.inspect('segments.list')['current']
        located = {name: (int(h), int(offset, 16)) for name, h, offset in re.findall(
            r'^([A-Za-z_][\w]*)\s+(\d\d):([0-9A-Fa-f]{8})\s*$',
            (directory / 'native.lst').read_text(), re.M)}
        title_hunk, title_offset = located['title_copper']
        if segments[0]['start'] != base or title_offset >= segments[title_hunk]['size']:
            raise ValueError('Static title symbol differs from actual loaded hunks')
        title_bank = f"{segments[title_hunk]['start'] + title_offset:08x}"
        for inputs in native_inputs:
            session.inspect('input_set_port', {'port': inputs['port'], 'device': 'joystick'})
            session.inspect('input_joy', inputs)
        if track_commits:
            session.inspect('break_add', {'kind': 'pc', 'addr': base + symbols['game_scene_prepared']})
            session.inspect('break_add', {'kind': 'pc', 'addr': base + symbols['presentation_commit_in_blank']})
        if recorded_entropy:
            session.inspect('break_add', {'kind': 'pc', 'addr': base + symbols['refresh_replay_done']})
        if observe_audio:
            session.inspect('break_add', {'kind': 'pc', 'addr': base + symbols['paula_events_done']})
        if observe_fields:
            session.inspect('break_add', {'kind': 'pc', 'addr': base + symbols['scoreboard_selection_done']})
        initial_break = None
        if observe_initial_fields:
            if not observe_fields or targets[0] <= initial_source_update:
                raise ValueError('Initial field observation requires later targets and field tracking')
            initial_break = session.inspect('break_add', {'kind': 'pc',
                'addr': base + symbols['simulation_update'],
                'cond': {'lhs': {'mem': base + symbols['simulation_updates']},
                         'op': 'eq', 'rhs': initial_source_update}})
        if observe_state:
            if not recorded_entropy:
                raise ValueError('Consecutive state observation requires the private replay build')
            session.inspect('break_add', {'kind': 'pc', 'addr': base + symbols['log_replay_transition']})
        def observe_stop(stop):
            if stop['reason'] != 'breakpoint':
                return False
            generation = int(session.inspect('mem_read', {'addr': base + symbols['simulation_updates'], 'len': 2})['data'], 16)
            if initial_break and stop['pc'] == base + symbols['simulation_update'] and generation == initial_source_update:
                initial_fields.append({'update': generation,
                    'field_values': session.inspect('mem_read', {'addr': base + symbols['field_values'], 'len': 6})['data'],
                    'stop': stop})
                session.inspect('break_remove', {'id': initial_break['id']})
                return True
            if observe_state and stop['pc'] == base + symbols['log_replay_transition']:
                registers = session.inspect('regs_get')
                state_events.append({'update': generation, 'stop': stop,
                    'post_tail_ram': session.inspect('mem_read', {'addr': registers['a'][5], 'len': 256})['data']})
                for event in schedule:
                    if event['after_callback'] == generation:
                        tool = 'input_key' if 'rawkey' in event['arguments'] else 'input_joy'
                        applied_inputs.append({'after_callback': generation, 'source_control': event['source_control'],
                            'tool': tool, 'arguments': event['arguments'], 'stop': stop,
                            'response': session.inspect(tool, event['arguments'])})
                return True
            if observe_fields and stop['pc'] == base + symbols['scoreboard_selection_done']:
                field_events.append({'update': generation + 1,
                    'field_values': session.inspect('mem_read', {'addr': base + symbols['field_values'], 'len': 6})['data'],
                    'score_flags_before': int(session.inspect('mem_read', {'addr': base + symbols['score_flags_before'], 'len': 1})['data'], 16),
                    'status_timer_before': int(session.inspect('mem_read', {'addr': base + symbols['status_timer_before'], 'len': 1})['data'], 16),
                    'stop': stop})
                return True
            if observe_audio and stop['pc'] == base + symbols['paula_events_done']:
                count = int(session.inspect('mem_read', {'addr': base + symbols['psg_count'], 'len': 1})['data'], 16)
                data = session.inspect('mem_read', {'addr': base + symbols['psg_log'], 'len': count})['data'] if count else ''
                if list(bytes.fromhex(data)) != source['updates'][generation]['psg']:
                    if strict_source_events:
                        raise ValueError(f'Native PSG bytes differ at update {generation + 1}')
                    source_event_differences.append({'update': generation + 1,
                        'boundary': 'native-sound-events', 'field': 'ordered PSG writes',
                        'expected': source['updates'][generation]['psg'], 'actual': list(bytes.fromhex(data))})
                audio_ticks.append({'update': generation + 1, 'due': int(session.inspect('mem_read', {'addr': base + symbols['game_audio_due'], 'len': 1})['data'], 16),
                    'wait': int(session.inspect('mem_read', {'addr': base + symbols['game_audio_wait'], 'len': 1})['data'], 16),
                    'rate': int(session.inspect('mem_read', {'addr': base + symbols['game_audio_rate'], 'len': 1})['data'], 16),
                    'voices': session.inspect('mem_read', {'addr': base + symbols['game_audio_voices'], 'len': 96})['data'], 'stop': stop})
                if count or source['updates'][generation]['psg']:
                    audio_events.append({'update': generation + 1, 'psg': data,
                                         'registers': session.inspect('custom_dump')['regs'], 'stop': stop})
                return True
            if recorded_entropy and stop['pc'] == base + symbols['refresh_replay_done']:
                value = session.inspect('regs_get')['d'][0] & 255
                expected_reads = source['updates'][generation]['refresh_reads']
                if strict_source_events and (not expected_reads or any(event['bit'] != value for event in expected_reads)):
                    raise ValueError(f'Native refresh consumption diverged at update {generation + 1}')
                entropy_reads.append({'update': generation + 1, 'bit': value, 'stop': stop})
                return True
            if track_commits and stop['pc'] == base + symbols['game_scene_prepared']:
                bank = session.inspect('mem_read', {'addr': base + symbols['back_copper'], 'len': 4})['data']
                started = int(session.inspect('mem_read', {'addr': base + symbols['simulation_started_updates'], 'len': 2})['data'], 16)
                prepared_scenes.append({'generation': initial_source_update + started, 'bank': bank,
                    'field_values': session.inspect('mem_read', {'addr': base + symbols['prepared_field_values'], 'len': 6})['data'],
                    'objects': session.inspect('mem_read', {'addr': base + symbols['game_scene_objects'], 'len': 64})['data'],
                    'stop': stop})
                return True
            if track_commits and stop['pc'] == base + symbols['presentation_commit_in_blank']:
                front = session.inspect('mem_read', {'addr': base + symbols['presentation_copper'], 'len': 4})['data']
                prepared = prepared_scenes[-1] if prepared_scenes else None
                title = bool(int(session.inspect('mem_read', {'addr': base + symbols['game_title_display'], 'len': 1})['data'], 16))
                expected_bank = title_bank if title else prepared['bank'] if prepared else None
                if not prepared or prepared['generation'] > generation or expected_bank != front:
                    raise ValueError('Published bank does not match the actual completed prepared scene')
                # The title is a separate static asset selected by the native
                # lifecycle. Frozen service ticks need not prepare a new court.
                commits.append({'prepared_after_callback': generation if title else prepared['generation'],
                                'completed_callback': generation, 'title_selected': title,
                                'expected_bank': expected_bank, 'prepared_scene': prepared, 'front_copper': front,
                                'field_values': prepared['field_values'],
                                'visible_frame': stop['frame'] + (1 if stop['vpos'] >= 236 else 0), 'stop': stop})
                return True
            return False
        if initial_break:
            deadline = stop['seconds'] + 10
            while not initial_fields:
                stop = session.inspect('run_until', {'seconds': deadline, 'wait_ms': 50000})
                if not observe_stop(stop):
                    raise RuntimeError(f'Initial native field boundary not reached: {stop}')
        for target in targets:
            current = int(session.inspect('mem_read', {'addr': base + symbols['simulation_updates'], 'len': 2})['data'], 16)
            if current > target:
                raise ValueError(f'Completed raster advanced past callback {target}; use more widely separated targets')
            breakpoint = session.inspect('break_add', {'kind': 'pc',
                'addr': base + symbols['simulation_update'],
                'cond': {'lhs': {'mem': base + symbols['simulation_updates']},
                         'op': 'eq', 'rhs': target}})
            deadline = stop['seconds'] + max(10, (target - current) / 30 + 2)
            while True:
                stop = session.inspect('run_until', {'seconds': deadline, 'wait_ms': 50000})
                if observe_stop(stop):
                    continue
                break
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
                'front_copper': session.inspect('mem_read', {'addr': base + symbols['presentation_copper'], 'len': 4})['data']})
            # Actual CT07 primitives and the published hardware sprite bank.
            # Observation only: no expected geometry or intermediate writes.
            def scene_snapshot():
                objects = bytes.fromhex(session.inspect('mem_read', {'addr':base+symbols['game_scene_objects'],'len':64})['data'])
                front = int(session.inspect('mem_read', {'addr':base+symbols['presentation_copper'],'len':4})['data'],16)
                hardware = []
                courts = [int(session.inspect('mem_read', {'addr':base+symbols[name],'len':4})['data'],16) for name in ('front_copper','back_copper')]
                court_selected = front in courts
                # The title has no sprite pointer commands and disables sprite DMA.
                for channel in range(8) if court_selected else ():
                    pointer = bytes.fromhex(session.inspect('mem_read', {'addr':front+68+8*channel,'len':8})['data'])
                    if int.from_bytes(pointer[:2],'big') != 0x120+4*channel or int.from_bytes(pointer[4:6],'big') != 0x122+4*channel:
                        raise ValueError('Native sprite pointer layout changed')
                    address = int.from_bytes(pointer[2:4],'big')*65536 + int.from_bytes(pointer[6:8],'big')
                    image = bytes.fromhex(session.inspect('mem_read', {'addr':address,'len':72})['data'])
                    hardware.append({'channel':channel,'address':address,'control':image[:4].hex(),
                                     'plane_words':image[4:68].hex()})
                visible = sum(bool(objects[n+5]) for n in range(0,64,8))
                error = int(session.inspect('mem_read', {'addr':base+symbols['sprite_bridge_error'],'len':1})['data'],16)
                if error or not 0 <= visible <= 8:
                    raise AssertionError('Native scene exceeds its sprite/colour capacity')
                return {'objects':objects.hex(), 'visible_primitives':visible, 'fit_error':error,
                        'selected_copper':front, 'court_bank_selected':court_selected,
                        'observation_frame':stop['frame'], 'hardware_sprites':hardware}

            observations[-1]['native_scene_at_callback'] = scene_snapshot()
            observations[-1]['latest_commit'] = commits[-1] if commits else None
            session.inspect('break_remove', {'id': breakpoint['id']})
            if completed_rasters:
                if not track_commits:
                    raise ValueError('Completed raster capture requires presentation commit tracking')
                raster_deadline = stop['frame'] + 3
                while True:
                    stop = session.inspect('run_until', {'vpos': 0, 'hpos': 0, 'wait_ms': 50000})
                    if observe_stop(stop):
                        continue
                    # A fast first phase callback can finish in the blank already
                    # observed before its scene was ready. Wait for its first
                    # actual publication AND completed scanout, not the prior frame.
                    completed = [event for event in commits if event['visible_frame'] <= stop['frame'] - 1]
                    if completed:
                        actual_generation = completed[-1]['prepared_after_callback']
                        if target not in required_raster_generations or actual_generation == target:
                            break
                        if actual_generation > target:
                            raise RuntimeError(f'Requested generation {target} missed; completed raster is {actual_generation}')
                    if stop['frame'] >= raster_deadline:
                        raise RuntimeError('No completed published scene within three frames')
                if stop['reason'] != 'target' or stop['vpos'] != 0 or stop.get('bridge'):
                    raise RuntimeError(f'Completed raster boundary not reached: {stop}')
                rendered_frame = stop['frame'] - 1
                visible = [event for event in commits if event['visible_frame'] <= rendered_frame]
                raster = session.inspect('capture_screenshot', {'path': str(directory / f'completed-{target:05d}.png')})
                observations[-1]['native_scene_at_raster'] = scene_snapshot()
                observations[-1]['completed_raster'] = {'stop': stop, 'rendered_frame': rendered_frame,
                    'generation': visible[-1] if visible else None, 'capture': raster}
                if target in required_raster_generations:
                    observations[-1]['completed_raster']['requested_generation'] = target
                    observations[-1]['completed_raster']['wait_horizon_callback'] = int(session.inspect('mem_read',
                        {'addr': base + symbols['simulation_updates'], 'len': 2})['data'], 16)
            print(f'callback {count}: {len(differences)} state differences, beam {stop["vpos"]}:{stop["hpos"]}', flush=True)
        log = Path(launch['log']).read_text(encoding='utf-8', errors='replace')
        for marker in ('cpu=M68000', 'cpu_clock=7.09MHz', 'chip_ram=512K', 'fast_ram=0K',
                       'slow_ram=0K', 'chipset=Ocs', 'video=Pal', 'Kickstart 1.3'):
            if marker not in log:
                raise ValueError(f'Native hardware profile marker missing: {marker}')
        (directory / 'copperline.log').write_text(log, encoding='utf-8')
        final_count = int(session.inspect('mem_read', {'addr': base + symbols['simulation_updates'], 'len': 2})['data'], 16)
        if recorded_entropy:
            expected_entropy = [(row['ordinal'], event['bit']) for row in source['updates'][initial_source_update:final_count]
                                for event in row['refresh_reads']]
            completed_reads = [(event['update'], event['bit']) for event in entropy_reads if event['update'] <= final_count]
            pending_reads = [(event['update'], event['bit']) for event in entropy_reads if event['update'] > final_count]
            # Beam wrap can stop inside the next callback after its refresh read,
            # before simulation_updates is incremented. Validate that partial
            # callback as a prefix, without inventing a completed callback.
            pending_expected = [(final_count + 1, event['bit']) for event in source['updates'][final_count]['refresh_reads']] if final_count < len(source['updates']) else []
            if completed_reads != expected_entropy or pending_reads != pending_expected[:len(pending_reads)]:
                if strict_source_events:
                    raise ValueError('Native entropy consumption order/count differs from the source')
                for update in range(initial_source_update + 1, final_count + 2):
                    wanted = [bit for ordinal, bit in expected_entropy if ordinal == update]
                    actual = [bit for ordinal, bit in completed_reads if ordinal == update]
                    if update == final_count + 1:
                        wanted = [bit for _, bit in pending_expected[:len(pending_reads)]]
                        actual = [bit for _, bit in pending_reads]
                    if wanted != actual:
                        source_event_differences.append({'update': update,
                            'boundary': 'native-entropy-consumption', 'field': 'refresh sign reads',
                            'expected': wanted, 'actual': actual})
    report = {'capture_report_path': str(report_path), 'scope': __doc__, 'executable_sha256': digest(executable),
              'reference_sha256': digest(source_path), 'symbols': symbols,
              'native_source': case['native_source'], 'native_source_sha256': digest(ROOT / case['native_source']),
              'private_replay_wrapper_sha256': digest(directory / 'native-recorded-refresh.s') if recorded_entropy else None,
              'emulator_sha256': digest(Path(config['tools']['copperline'])),
              'bridge_sha256': digest(ctl) if ctl.exists() else None,
        'control_transport': 'optional MCP bridge' if ctl.exists() else 'direct CCP', 'kickstart_sha256': digest(Path(config['inputs']['amiga_rom'])),
              'initial_source_update': initial_source_update,
              'initial_phase_reference': initial_phase_reference,
              'initial_phase_sha256': digest(ROOT / initial_phase_reference) if initial_phase_reference else None,
              'native_inputs': native_inputs, 'source_case': source_case,
              'native_input_schedule': schedule, 'applied_physical_events': applied_inputs,
              'presentation_reference_directory': presentation_reference_directory, 'observations': observations,
              'recorded_entropy': recorded_entropy,
              'refresh_fixture_sha256': digest(directory / 'refresh-signs.bin') if recorded_entropy else None,
              'commits': commits, 'commit_tracking': track_commits,
              'entropy_reads': entropy_reads, 'completed_rasters': completed_rasters,
              'audio_events': audio_events, 'audio_ticks': audio_ticks, 'audio_observed': observe_audio,
              'field_events': field_events, 'fields_observed': observe_fields,
              'state_events': state_events, 'state_observed': observe_state,
              'initial_fields': initial_fields,
              'source_event_differences': source_event_differences,
              'strict_source_events': strict_source_events,
              'executable_mutated': executable_mutator is not None or source_mutator is not None,
              'native_wav': str(directory / 'native.wav') if observe_audio else None,
              'final_completed_callbacks': final_count,
              'graphics_comparison_complete': False}
    report_path.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--recorded-entropy', action='store_true')
    parser.add_argument('--track-commits', action='store_true')
    parser.add_argument('--completed-rasters', action='store_true')
    args = parser.parse_args()
    targets = (0, 17, 63, 134, 166) if args.completed_rasters else (0, 17, 18, 63, 134, 135, 136, 166)
    capture(targets, recorded_entropy=args.recorded_entropy, track_commits=args.track_commits, completed_rasters=args.completed_rasters)
