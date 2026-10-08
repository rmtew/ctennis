"""Finite PAL court prototype capture through real one-player keyboard controls.

This is a prototype review case, not tutorial release acceptance. It observes
complete callback boundaries and retains literal RPC/notifications, source PNGs
and the exact same pixels in a native-resolution review view and animation.
"""
import hashlib
import json
import re

from build_native_game import build
from check_shared_core_bytes import normalized
from native_evidence import ReportRun, TARGET, atomic_json, inputs_for, snapshot
from native_hunk import loaded_hunks
from native_metrics import memory_summary
from native_observation import target_log
from native_tools import ROOT, emulator_config
from ordinary_cadence import chip_memory
from tutorial_capture import CaptureSession, CallbackObserver, SurfaceObserver, native_view, animation

FIELDS = dict(tutorial_active=1, tutorial_pending=1, tutorial_menu=1,
              tutorial_x=1, tutorial_y=1, tutorial_end=1, tutorial_active_variant=1,
              tutorial_input_source=1, tutorial_status=2, tutorial_animation_index=2,
              tutorial_progress_operations=2, tutorial_render_generation=2,
              tutorial_published_generation=2, tutorial_resume_count=2,
              tutorial_generation=4, tutorial_build_generation=2,
              tutorial_render_phase=2, tutorial_render_surface=4,
              front_copper=4, back_copper=4, ready_copper=4, spare_copper=4,
              presentation_copper=4, display_ready=1, ready_completed=1,
              ready_generation=2, ready_game_generation=2,
              game_presented_generation=2, ready_title_display=1,
              missed_presentation_deadlines=2,
              tutorial_work_pending=1, tutorial_render_path=2, tutorial_render_point=2,
              tutorial_line_active=1, tutorial_line_x=2, tutorial_line_y=2,
              tutorial_line_end_x=2, tutorial_line_end_y=2,
              tutorial_line_dx=2, tutorial_line_dy=2, tutorial_line_error=2,
              tutorial_line_sx=2, tutorial_line_sy=2,
              tutorial_counts=4)


def run():
    directory = ROOT/'build/tests/tutorial-court-pal'
    directory.mkdir(parents=True, exist_ok=True)
    output = directory/'report.json'
    transaction = ReportRun([output], 'native-feedback', 'maintained-native',
                            'ordinary title; real one-player physical controls')
    try:
        paths, tools = inputs_for('native-feedback', 'scripts/run_tutorial_capture.py')
        transaction.meta.update(files=snapshot(paths), tools=tools,
                                runner='scripts/run_tutorial_capture.py', actual_target=TARGET)
        import subprocess
        transaction.meta['commit'] = subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
        _, executable = build()
        listing = (executable.parent/'native.lst').read_text()
        shared, relocations, sinks = normalized(executable, executable.parent/'native.lst')
        assert (len(shared), relocations, sinks,
                hashlib.sha256(shared).hexdigest()) == (
            18020, 257, 14,
            '9a457929bc223b843132bb53af7d604ed574441e32c4651eb69897aa0b48689d')
        config = emulator_config()
        screenshots, boundaries, actions, waits = [], [], [], []
        selected = metadata = live_backup = None
        resume_readback = None
        awaiting_resumed_boundary = False
        first_resumed_boundary_matches = False
        held_resume_samples = 0
        with CaptureSession(directory) as session:
            session.inspect('session_launch', dict(binary=config['tools']['copperline'],
                run=str(executable), args=['--chipset','OCS','--video','PAL',
                '--cpu','68000','--chip','512K','--slow','0','--fast','0',
                '--noaudio',config['inputs']['amiga_rom']]))
            stop = session.inspect('run_until', dict(seconds=30))
            assert stop['reason'] == 'loadseg', stop
            segments = session.inspect('segments.list')['current']
            symbols = {name: segments[int(hunk)]['start']+int(offset, 16)
                for name, hunk, offset in re.findall(
                r'^([A-Za-z_]\w*)\s+(\d\d):([0-9a-fA-F]{8})\s*$', listing, re.M)}
            def read(address, size):
                return bytes.fromhex(session.inspect('mem_read',
                    dict(addr=address, len=size))['data'])
            def block(name, size): return read(symbols[name], size)
            def number(name, size=None):
                return int.from_bytes(block(name, FIELDS.get(name, 2) if size is None else size), 'big')
            loaded = loaded_hunks(executable, segments, read)
            observer = CallbackObserver(0, symbols)
            observer.surfaces = SurfaceObserver(symbols, read)
            session.observer = observer
            subscription = session.inspect('events.subscribe',
                dict(events=['mmio','frame'], mmio=(observer.watches(FIELDS, read)+
                                                  observer.surfaces.watches())))
            assert not subscription.get('dropped_notifications', 0)
            session.inspect('break_add', dict(kind='pc', addr=symbols['simulation_update']))
            session.inspect('break_add', dict(kind='pc', addr=symbols['tutorial_resume_restored']))
            start_seconds = stop['seconds']
            time = start_seconds
            def advance(seconds):
                nonlocal stop, time, selected, metadata, live_backup
                nonlocal resume_readback, awaiting_resumed_boundary
                nonlocal first_resumed_boundary_matches, held_resume_samples
                target = time+seconds
                assert target-start_seconds <= 120, 'Finite native tutorial seconds cap'
                for _ in range(8192):
                    stop = session.inspect('run_until', dict(seconds=target))
                    time = stop['seconds']
                    if stop.get('pc') == symbols['tutorial_resume_restored']:
                        assert resume_readback is None and live_backup is not None
                        restored = block('game_core_state', 318)
                        history = block('game_history_state', 72)
                        backup = block('tutorial_interrupted_state', 318)
                        expected_history = bytearray(metadata)
                        origin = symbols['game_history_state']
                        mode_offset = symbols['game_history_mode']-origin
                        position_offset = symbols['game_history_position']-origin
                        cursor_offset = symbols['game_history_cursor']-origin
                        assert 0 <= mode_offset < 72 and 0 <= position_offset <= 64 and 0 <= cursor_offset <= 64
                        expected_history[mode_offset] = 1
                        expected_history[position_offset:position_offset+8] = metadata[cursor_offset:cursor_offset+8]
                        assert restored == backup == live_backup, 'Resume did not publish exact interrupted state'
                        assert history == expected_history, 'Resume changed unrelated history metadata'
                        resume_readback = dict(state=restored.hex(), expected_state=live_backup.hex(),
                            backup=backup.hex(), history=history.hex(), expected_history=expected_history.hex(),
                            position={k:stop[k] for k in ('pc','cck','frame','seconds')})
                        awaiting_resumed_boundary = True
                    if stop.get('pc') == symbols['simulation_update']:
                        assert observer.pending is None
                        current = block('game_core_state', 318)
                        history = block('game_history_state', 72)
                        backup = block('tutorial_interrupted_state', 318)
                        active = number('tutorial_active')
                        row = dict(position={k:stop[k] for k in ('cck','frame','vpos','hpos','seconds')},
                                   state=current.hex(), history=history.hex(),
                                   backup=backup.hex(), fields={n:number(n) for n in FIELDS})
                        boundaries.append(row)
                        if active:
                            if selected is None:
                                selected, metadata, live_backup = current, history, backup
                            assert current == selected, 'Tutorial changes selected complete state'
                            assert history == metadata, 'Tutorial changes public history metadata'
                            assert backup == live_backup, 'Tutorial changes interrupted live backup'
                        elif awaiting_resumed_boundary:
                            assert current == live_backup, 'Resume callback dispatched before restored boundary'
                            first_resumed_boundary_matches = True
                            awaiting_resumed_boundary = False
                        elif first_resumed_boundary_matches:
                            assert not (block('game_input_pressed', 2)[0] & 0x10), 'Held menu action creates an invented shot edge'
                            held_resume_samples += 1
                    if time >= target:
                        break
                else:
                    raise AssertionError('Finite complete-boundary observation cap')
            def key(rawkey, held, seconds=.06):
                session.inspect('input_key', dict(rawkey=rawkey, action='press' if held else 'release'))
                actions.append(dict(rawkey=rawkey, held=held, at_seconds=time))
                advance(seconds)
            def ready():
                wait_start = time
                for _ in range(200):
                    advance(.2)
                    if (number('tutorial_active') and number('tutorial_status') == 4
                            and not number('tutorial_pending')
                            and number('tutorial_published_generation') == number('tutorial_render_generation')
                            and observer.surfaces.current(number('tutorial_published_generation'))):
                        waits.append(dict(start_seconds=wait_start, ready_seconds=time,
                                          elapsed_seconds=time-wait_start,
                                          generation=number('tutorial_published_generation')))
                        return
                atomic_json(directory/'readiness-failure.json', dict(
                    waits=waits, boundaries=boundaries, stop=stop,
                    fields={n:number(n) for n in FIELDS},
                    surface_publications=observer.surfaces.publications))
                raise AssertionError('No current complete tutorial scene within finite wait')
            def photo(name):
                source = directory/(name+'-viewport.png')
                native = directory/(name+'.png')
                session.inspect('capture_screenshot', dict(path=str(source)))
                native_view(source, native)
                surface = None
                if number('tutorial_active') and not number('tutorial_pending'):
                    surface = observer.surfaces.completed_surface(number('tutorial_published_generation'))
                screenshots.append(dict(name=name, source=str(source.relative_to(ROOT)),
                                        native=str(native.relative_to(ROOT)),
                                        source_geometry=[716,285], native_geometry=[256,208],
                                        stop=dict(stop), fields={n:number(n) for n in FIELDS},
                                        observed_surface=surface))
                return native
            advance(.7)
            photo('title')
            key(0x01, True, .1); key(0x01, False, 1.4)
            assert number('game_lifecycle', 2) == 1
            key(0x24, True); key(0x24, False, .08)
            key(0x24, True); key(0x24, False)
            ready(); photo('released-serve')
            old_xy = (number('tutorial_x'), number('tutorial_y'))
            key(0x22, True, .15); key(0x22, False)
            assert (number('tutorial_x'), number('tutorial_y')) != old_xy
            ready(); photo('edited-serve')
            key(0x23, True); ready(); photo('held-serve')
            frames = []
            for index in range(24):
                advance(1/12)
                frames.append(photo(f'animation-{index:02d}'))
            movie = directory/'held-serve-animation.gif'
            movie_info = animation(frames, movie, 83)
            key(0x23, False); ready(); photo('released-edited-serve')
            # Restore while physical F is held but interrupted logical F was not.
            key(0x23, True); ready()
            # Modifier use must consume its release instead of opening a menu.
            key(0x24, True); key(0x22, True); key(0x22, False); key(0x24, False)
            assert not number('tutorial_menu')
            key(0x24, True); key(0x24, False)
            advance(.2); assert number('tutorial_menu'); ready(); photo('options')
            # Resume latest is the enabled action after disabled Play from here.
            key(0x4d, True); key(0x4d, False)
            key(0x44, True); key(0x44, False)
            advance(.2)
            assert not number('tutorial_active') and number('tutorial_resume_count') == 1
            assert first_resumed_boundary_matches and held_resume_samples >= 2
            photo('resumed')
            # Finish at a real outer-callback boundary, retaining no partial one.
            stop = session.inspect('run_until', dict(seconds=time+.1))
            assert stop.get('pc') == symbols['simulation_update'] and observer.pending is None
            memory = chip_memory(read)
            interval = (number('simulation_interval_whole', 4)*65536+
                        number('simulation_interval_fraction', 2))
            video = dict(presentation_last_line=number('presentation_last_line', 2),
                         simulation_interval_whole=number('simulation_interval_whole', 4),
                         simulation_interval_fraction=number('simulation_interval_fraction', 2))
            assert video == dict(presentation_last_line=311, simulation_interval_whole=11838,
                                 simulation_interval_fraction=14906), 'Actual PAL selector/deadline contract differs'
            timing = observer.result(interval)
            missed_publications = number('missed_presentation_deadlines')
            assert missed_publications == 0
            raw = dict(records=session.records, uncompressed_bytes=session.raw_bytes,
                       cap_uncompressed_bytes=session.MAX_RAW_BYTES)
            surfaces = observer.surfaces.result()
        target_log(directory)
        capture = directory/'capture.json'
        atomic_json(capture, dict(boundaries=boundaries, actions=actions, waits=waits, timing=timing,
                                 memory=memory, loaded_hunks=loaded, surfaces=surfaces))
        report = dict(passed=True, subject='maintained-native', interface_flavor='enhanced',
            target=TARGET, native_video=video, waits=waits,
            missed_presentation_deadlines=missed_publications,
            executable_sha256=hashlib.sha256(executable.read_bytes()).hexdigest(),
            capture=str(capture.relative_to(ROOT)), screenshots=screenshots,
            animation=str(movie.relative_to(ROOT)), literal_rpc=raw,
            literal_rpc_path=str((directory/'literal-rpc.jsonl.gz').relative_to(ROOT)),
            animation_frames=movie_info['frames'], animation_geometry=movie_info['geometry'],
            animation_source_frames=movie_info['source_frames'],
            shared_core=dict(bytes=len(shared), relocations=relocations, sink_branches=sinks,
                             normalized_sha256=hashlib.sha256(shared).hexdigest()), loaded_hunks=loaded,
            resume_readback=resume_readback, first_resumed_boundary_matches=first_resumed_boundary_matches,
            held_resume_no_pressed_edge=held_resume_samples >= 2,
            surface_ownership=dict(surface_write_count=surfaces['surface_write_count'],
                bank_write_count=surfaces['bank_write_count'],
                protected_surface_writes=0, protected_bank_writes=0,
                exact_queued_image_published=True,
                queued_images=len(surfaces['queues']), actual_publications=len(surfaces['publications'])),
            complete_state_bytes=318, public_history_bytes=72,
            native_memory=memory_summary(memory), timing=timing,
            frozen_boundaries=sum(bool(r['fields']['tutorial_active']) for r in boundaries),
            scope='Finite PAL current-human-serve court prototype; physical double-tap/edit/hold/release/modifier/menu/resume. No retained-shot navigation, live branching, full native gate or release claim.')
        manifest = json.loads((executable.parent/'baseline-rally.compile.json').read_text())
        artifacts = [p for p in directory.iterdir() if p.is_file() and p != output]
        transaction.finalize(output, report, [manifest], artifacts)
        print('tutorial-court-pal prototype capture PASS', flush=True)
    except BaseException as error:
        transaction.abort(error)
        raise


if __name__ == '__main__':
    run()
