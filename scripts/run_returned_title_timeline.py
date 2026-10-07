"""Initial-once retained match award, then actual native title scanout timeline."""
import hashlib
import json
import re
import argparse

from build_native_game import build
from copperline_test_session import NativeControlSession
from native_evidence import atomic_json, compile_manifest
from native_hunk import loaded_hunks
from native_identity_raster import assert_menu_selection_raster
from native_tools import ASSEMBLER, ROOT, emulator_config, run
from run_native_contracts import SCORING


def main(phase=None, control=False):
    directory = ROOT / 'build/tests' / ('returned-title-timeline' + ('' if phase is None else '-' + str(phase)) + ('-delayed-control' if control else ''))
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / 'report.json'
    atomic_json(path, {'passed': False, 'state': 'incomplete'})
    _, ordinary = build()
    points, games, contact, _, _ = SCORING['match-award']
    initialization = '        moveq #0,d0\n        bsr game_new_match\n        bsr game_begin_active\n        move.b #$40,game_score_flags\n        st ui_demo\n        clr.b ui_player_count\n'
    for name, value in zip(('game_point_a', 'game_point_b', 'game_games_a', 'game_games_b', 'game_contact'), (*points, *games, contact)):
        initialization += f'        move.b #{value},{name}\n'
    source = (ROOT / 'amiga/main.s').read_text()
    if control:
        render = (ROOT / 'amiga/game/interface_render.s').read_text()
        gate = '        cmp.w   ui_title_request_epoch,d0\n        beq     .done'
        assert render.count(gate) == 1
        altered = directory / 'interface-render.s'
        altered.write_text(render.replace(gate, '        sub.w   ui_title_request_epoch,d0\n        cmpi.w  #1,d0\n        bls     .done'))
        interface = directory / 'interface.s'
        interface.write_text((ROOT / 'amiga/game/interface.s').read_text().replace('"amiga/game/interface_render.s"', '"' + str(altered) + '"'))
        source = source.replace('"amiga/game/interface.s"', '"' + str(interface) + '"')
    if phase is not None:
        timer = '        bsr     read_sim_timer\n        move.l  d0,last_timer_count'
        assert source.count(timer) == 1
        source = source.replace(timer, f'fixture_startup_phase:\n        bsr read_presentation_line\n        cmpi.w #{phase},d0\n        bne.s fixture_startup_phase\n' + timer)
    marker = '        bsr     game_begin_title'
    assert source.count(marker) == 1
    fixture = directory / 'fixture.s'
    fixture.write_text(source.replace(marker, initialization))
    executable, listing = directory / 'native-fixture', directory / 'native.lst'
    run([str(ASSEMBLER), '-Fhunkexe', '-kick1hunks', '-m68000', '-DENHANCED_INTERFACE=1',
         '-L', str(listing), '-o', str(executable), str(fixture)])
    compiled = compile_manifest(executable, listing)
    located = {name: (int(hunk), int(offset, 16)) for name, hunk, offset in
               re.findall(r'^([A-Za-z_]\w*)\s+(\d\d):([0-9A-Fa-f]{8})\s*$', listing.read_text(), re.M)}
    config = emulator_config()
    events, photos, replies = [], {}, {}
    state = {'started': 0, 'completed': 0, 'returned': None, 'publication': None,
             'pointer': bytearray(4), 'life': 1, 'title': False, 'title_ready': None}
    with NativeControlSession(directory) as session:
        session.inspect('session_launch', {'binary': config['tools']['copperline'], 'run': str(executable),
            'args': ['--chipset', 'OCS', '--video', 'PAL', '--cpu', '68000', '--chip', '512K',
                     '--slow', '0', '--fast', '0', '--noaudio', config['inputs']['amiga_rom']]})
        stop = session.inspect('run_until', {'seconds': 30})
        assert stop['reason'] == 'loadseg'
        segments = session.inspect('segments.list')['current']
        def address(name):
            hunk, offset = located[name]
            return segments[hunk]['start'] + offset
        def read(address, size):
            return bytes.fromhex(session.inspect('mem_read', {'addr': address, 'len': size})['data'])
        loaded = loaded_hunks(executable, segments, read)
        assert all(row['matched'] for row in loaded)
        breakpoint = session.inspect('break_add', {'kind': 'pc', 'addr': address('main_loop')})
        stop = session.inspect('run_until', {'seconds': stop['seconds'] + 2})
        session.inspect('break_remove', {'id': breakpoint['id']})
        assert stop['pc'] == address('main_loop')
        assert int.from_bytes(read(address('game_lifecycle'), 2), 'big') == 1
        regs = session.inspect('custom_dump')['regs']
        state['pointer'] = bytearray(((regs['COP1LCH'] << 16) | regs['COP1LCL']).to_bytes(4, 'big'))
        watch = {'simulation_started_updates': 2, 'simulation_updates': 2, 'game_lifecycle': 2,
                 'ui_title_deferred': 1, 'ui_dirty': 1, 'game_title_display': 1,
                 'ready_generation': 2, 'ready_completed': 1, 'display_ready': 1}
        names = {address(name): name for name in watch}
        def photo(label, position):
            if label in photos:
                return
            identifier = session.send_async('capture.screenshot', {'path': str(directory / (label + '.png'))})
            photos[label] = {'id': identifier, 'request_position': position}
            replies[identifier] = label
        def observe(message):
            if message.get('id') in replies:
                photos[replies[message['id']]]['reply'] = message
                return
            if message.get('method') == 'event.frame':
                row = message['params']
                assert not row.get('dropped_notifications', 0)
                if state['returned']:
                    frame = row['position']['frame']
                    offset = frame - state['returned']['position']['frame']
                    if 0 <= offset <= 6:
                        photo('frame-' + str(offset), row)
                return
            if message.get('method') != 'event.mmio':
                return
            row = message['params']
            assert not row.get('dropped_events', 0) and not row.get('dropped_notifications', 0)
            name, value = names.get(row['addr']), row['value']
            if name == 'simulation_started_updates':
                state['started'] = value
            if name == 'simulation_updates':
                state['completed'] = value
                if state['returned'] and value - state['returned']['completed'] == 4:
                    photo('callback-4', row['position'])
            if name == 'game_lifecycle':
                state['life'] = value
                if value == 2 and state['returned'] is None:
                    state['returned'] = {'position': row['position'], 'started': state['started'], 'completed': state['completed']}
            if name == 'game_title_display':
                state['title'] = bool(value)
            if name == 'ready_completed' and value and state['title'] and state['returned'] and state['title_ready'] is None:
                state['title_ready'] = {'position': row['position'], 'started': state['started'], 'completed': state['completed']}
            if 0xdff080 <= row['addr'] and row['addr'] + row['size'] <= 0xdff084:
                offset = row['addr'] - 0xdff080
                state['pointer'][offset:offset + row['size']] = value.to_bytes(row['size'], 'big')
            if row['addr'] == 0xdff088 and state['returned']:
                pointer = int.from_bytes(state['pointer'], 'big')
                if pointer == address('title_copper') and state['publication'] is None:
                    state['publication'] = {'position': row['position'], 'started': state['started'], 'completed': state['completed']}
                if state['publication']:
                    assert pointer == address('title_copper'), ('Court published after actual title publication', row)
            events.append(dict(row, name=name))
        session.notification_handler = observe
        watches = [{'addr': address(name), 'len': size, 'access': 'write'} for name, size in watch.items()]
        watches += [{'addr': 0xdff080, 'len': 4, 'access': 'write'}, {'addr': 0xdff088, 'len': 2, 'access': 'write'}]
        session.inspect('events.subscribe', {'events': ['mmio', 'frame'], 'mmio': watches})
        session.inspect('run_until', {'seconds': stop['seconds'] + 30})
        session.inspect('events.unsubscribe')
        # Flush terminal asynchronous capture replies before inspecting pixels.
        session.inspect('status')
    state['pointer'] = state['pointer'].hex()
    report = {'passed': False, 'state': 'complete', 'timeline': state, 'photos': photos,
              'events': events, 'initialization': 'Retained match-award fixture once after actual product init; no later state/regime injection',
              'executable_sha256': hashlib.sha256(executable.read_bytes()).hexdigest(),
              'ordinary_sha256': hashlib.sha256(ordinary.read_bytes()).hexdigest(), 'compiled': compiled,
              'startup_phase': phase,
              'control': 'one-extra-deferred-callback' if control else None,
              'loaded_hunks': loaded, 'scope': 'Observed actual publication/scanout timing; no arbitrary complete-state or deadline claim'}
    atomic_json(path, report)
    assert state['returned'] and state['publication'], state
    for label, row in photos.items():
        try:
            assert_menu_selection_raster(directory / (label + '.png'), 0, 1)
            row['full_title_pixels'] = True
        except AssertionError as error:
            row['full_title_pixels'] = False
            row['pixel_difference'] = str(error)
    assert any(row['full_title_pixels'] for row in photos.values()), photos
    # Bound the intended one-callback deferral and actual publication. Raster
    # ownership follows physical publication, not a scalar callback offset.
    next_callback = state['title_ready']['started'] == (state['returned']['started'] + 1) & 0xffff
    if control:
        assert not next_callback, 'Delayed-construction control was not detected'
        report['control_detected'] = 'constructed ready did not finish next callback'
        atomic_json(path, report)
        print(json.dumps({'control_detected': report['control_detected'], 'timeline': state}))
        return
    assert next_callback, 'Constructed ready did not finish next callback'
    assert 0 <= state['publication']['position']['cck'] - state['title_ready']['position']['cck'] <= 313 * 227
    complete_frame = state['publication']['position']['frame'] + 2
    required = [row for label, row in photos.items() if label.startswith('frame-') and row['request_position']['position']['frame'] >= complete_frame]
    assert any(row['request_position']['position']['frame'] == complete_frame for row in required), 'First complete title frame telemetry missing'
    assert required and all(row['full_title_pixels'] for row in required), photos
    report['diagnostic_completed'] = True
    report['passed'] = True
    atomic_json(path, report)
    print(json.dumps({'timeline': state, 'photos': photos}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', type=int, choices=(0, 22, 253, 255, 256, 308))
    parser.add_argument('--delayed-control', action='store_true')
    args = parser.parse_args()
    main(args.phase, args.delayed_control)
