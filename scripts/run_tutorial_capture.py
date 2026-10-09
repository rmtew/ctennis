"""Finite PAL/NTSC court prototype capture through real physical controls.

This is a prototype review case, not tutorial release acceptance. It observes
complete callback boundaries and retains literal RPC/notifications, source PNGs
and the exact same pixels in a native-resolution review view and animation.
"""
import hashlib
import json
import re
import shutil
import argparse

from build_native_game import build
from check_shared_core_bytes import normalized
from native_evidence import ReportRun, TARGET, atomic_json, inputs_for, snapshot
from native_hunk import loaded_hunks
from native_metrics import memory_summary
from native_observation import target_log
from native_tools import ROOT, emulator_config
from ordinary_cadence import chip_memory
from tutorial_capture import (CaptureSession, CallbackObserver, SurfaceObserver,
                              native_view, animation, assert_native_text, assert_tutorial_menu,
                              assert_court_origins)

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
              tutorial_counts=4, tutorial_available_counts=4, tutorial_available_outcomes=4,
              tutorial_placement_dirty=1, tutorial_placement_ready=1,
              tutorial_marker_ready=1, tutorial_animation_ready=1, tutorial_ball_mode=1,
              tutorial_scene_layer=1,
              tutorial_waiting_ready=1, tutorial_trails_enabled=1, tutorial_footer_dirty=1,
              tutorial_presentation_generation=4, tutorial_marker_generation=4,
              tutorial_animation_generation=4, tutorial_visible_surface=4,
              tutorial_menu_selection=1, game_preview_status=2)
FIELDS['tutorial_animation_callback'] = 2
FIELDS['game_preview_endpoint_outcomes'] = 4
FIELDS['game_preview_endpoint_ready'] = 2
FIELDS['game_preview_endpoint_phases'] = 4
FIELDS['game_preview_generation'] = 4


def run(standard='PAL'):
    assert standard in ('PAL','NTSC')
    target = dict(TARGET, video=standard)
    expected_video = dict(zip(('presentation_last_line','simulation_interval_whole',
                              'simulation_interval_fraction'),
                             (311,11838,14906) if standard == 'PAL' else (261,11947,13180)))
    directory = ROOT/('build/tests/tutorial-court-'+standard.lower())
    directory.mkdir(parents=True, exist_ok=True)
    output = directory/'report.json'
    transaction = ReportRun([output], 'native-feedback', 'maintained-native',
                            'ordinary title; real one-player physical controls')
    try:
        paths, tools = inputs_for('native-feedback', 'scripts/run_tutorial_capture.py')
        transaction.meta.update(files=snapshot(paths), tools=tools,
                                runner='scripts/run_tutorial_capture.py', actual_target=target,
                                target_role='legacy-validator-reference',
                                target_scope='evidence.target is a legacy validator reference; actual_target and report.target identify the executed video standard.')
        import subprocess
        transaction.meta['commit'] = subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
        _, executable = build()
        # Keep original debug/product identity even when runtime validation fails.
        for name in ('baseline-rally','native.lst','baseline-rally.compile.json'):
            shutil.copy2(executable.parent/name, directory/name)
        listing = (directory/'native.lst').read_text()
        shared, relocations, sinks = normalized(executable, executable.parent/'native.lst')
        assert (len(shared), relocations, sinks,
                hashlib.sha256(shared).hexdigest()) == (
            17606, 7, 14,
            '99c543c170c036137be81d07ebd30b522ef3abdff04bd7b1af38f00047bb99d5')
        config = emulator_config()
        screenshots, boundaries, actions, waits = [], [], [], []
        visual_checks = {}
        selected = metadata = live_backup = None
        resume_readback = None
        awaiting_resumed_boundary = False
        first_resumed_boundary_matches = False
        held_resume_samples = 0
        with CaptureSession(directory) as session:
            session.inspect('session_launch', dict(binary=config['tools']['copperline'],
                run=str(executable), args=['--chipset','OCS','--video',standard,
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
            observer.surfaces = SurfaceObserver(symbols, read, verify_court_restores=True,
                                               last_line=expected_video['presentation_last_line'],
                                               verify_sprites=True)
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
                    # The protocol target is quantized to guest colour clocks.
                    # Its returned seconds can round below the requested float.
                    if stop.get('reason') == 'target' or time >= target:
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
                    scene = observer.surfaces.current_presentation(observer.state)
                    if (number('tutorial_active') and number('tutorial_status') in (4,6)
                            and not number('tutorial_pending')
                            and not number('tutorial_placement_dirty')
                            and not number('tutorial_footer_dirty')
                            and number('tutorial_published_generation') == number('tutorial_render_generation')
                            and scene
                            and observer.surfaces.current(number('tutorial_published_generation'))):
                        waits.append(dict(start_seconds=wait_start, ready_seconds=time,
                                          elapsed_seconds=time-wait_start,
                                          generation=number('tutorial_published_generation'),
                                          state='waiting' if number('tutorial_waiting_ready') else 'placement',
                                          first_actual_publication_seconds=scene['position']['seconds'],
                                          first_actual_ready_generation=scene['ready_generation']))
                        return
                atomic_json(directory/'readiness-failure.json', dict(
                    waits=waits, boundaries=boundaries, stop=stop,
                    fields={n:number(n) for n in FIELDS},
                    surface_publications=observer.surfaces.publications))
                raise AssertionError('No current complete tutorial scene within finite wait')
            def prediction_complete():
                # Pair completion is an evidence check, never the UI READY gate.
                for _ in range(200):
                    if number('game_preview_status') == 5 and not number('tutorial_work_pending'):
                        return
                    advance(.2)
                raise AssertionError('Bounded preview pair did not complete')
            def photo(name):
                source = directory/(name+'-viewport.png')
                native = directory/(name+'.png')
                session.inspect('capture_screenshot', dict(path=str(source)))
                native_view(source, native)
                from PIL import Image
                with Image.open(source) as viewport:
                    source_geometry = list(viewport.size)
                surface = None
                if number('tutorial_active') and not number('tutorial_pending'):
                    surface = observer.surfaces.completed_surface(number('tutorial_published_generation'))
                if surface or name.startswith('resumed'):
                    # Explicit independent court-restore contract. HUD/status
                    # strip pointers retain their existing native ownership.
                    bank = observer.surfaces.banks[observer.surfaces.hardware_copper]
                    base = surface['surface'] if surface else symbols['plane0']
                    visual_checks[name+'-court-origins'] = assert_court_origins(bank, symbols, base)
                screenshots.append(dict(name=name, source=str(source.relative_to(ROOT)),
                                        native=str(native.relative_to(ROOT)),
                                        source_geometry=source_geometry, native_geometry=[256,208],
                                        stop=dict(stop), fields={n:number(n) for n in FIELDS},
                                        observed_surface=surface))
                return native
            advance(.7)
            photo('title')
            key(0x01, True, .1); key(0x01, False, 1.4)
            assert number('game_lifecycle', 2) == 1
            key(0x24, True); key(0x24, False, .08)
            key(0x24, True); key(0x24, False)
            ready(); prediction_complete(); ready(); released_picture = photo('released-serve')
            # The fixed released continuation remains honestly bounded at256 dispatcher phases plus sample0.
            # Its observed state is an attached human serve waiting for action.
            released_state = block('game_preview_released_state', 318)
            end = number('tutorial_end')
            phase = released_state[symbols['game_upper_phase' if end else 'game_lower_phase']-symbols['game_core_state']]
            # ABI2 native60-byte gameplay packet: end AI flags are bytes54/55.
            ai = released_state[symbols['game_play_state']-symbols['game_core_state']+54+end]
            assert number('tutorial_active_variant') == 1
            assert number('game_preview_ordinal',2) == 0xffff
            assert int.from_bytes(block('game_preview_outcomes',4)[2:], 'big') == 6
            assert block('game_preview_launches',2)[1] == 0 and phase == 0x40 and ai == 0
            assert int.from_bytes(block('game_preview_counts',4)[2:], 'big') == 257
            visual_checks['released-wait'] = dict(
                raster=assert_native_text(released_picture,200,'RELEASED - WAITING TO SERVE'),
                state=released_state.hex(), end=end, ordinal=0xffff,
                phase=phase, ai=ai, launches=0, outcome=6,
                sample_count=257, sample_limit=257, incomplete=True, outgoing_shot_claimed=False)
            old_xy = (number('tutorial_x'), number('tutorial_y'))
            movement_start = time
            key(0x22, True, .15); key(0x22, False)
            movement_end = actions[-1]['at_seconds']
            assert (number('tutorial_x'), number('tutorial_y')) != old_xy
            ready(); photo('edited-serve')
            held_action_start = time
            key(0x23, True); ready(); photo('held-serve')
            # Recompute after an actual position edit with F still held, so
            # endpoint latency excludes a later alternative-selection action.
            held_edit_start = time
            held_xy = (number('tutorial_x'), number('tutorial_y'))
            held_generation = number('tutorial_generation')
            # The preceding rightward hold can already reach the court limit.
            # Move left to require a fresh accepted edit rather than measuring
            # a cached endpoint under an ineffective boundary-held direction.
            key(0x20, True, .035); key(0x20, False)
            held_edit_end = time
            assert (number('tutorial_x'), number('tutorial_y')) != held_xy
            assert number('tutorial_generation') != held_generation
            ready(); photo('held-edited-serve')
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
            advance(.2); assert number('tutorial_menu'); ready()
            visual_checks['options'] = assert_tutorial_menu(photo('options'), 0)
            # Resume latest is the enabled action after disabled Play from here.
            key(0x4d, True); key(0x4d, False)
            ready(); visual_checks['options-resume'] = assert_tutorial_menu(photo('options-resume'), 1)
            key(0x44, True); key(0x44, False)
            advance(.2)
            assert not number('tutorial_active') and number('tutorial_resume_count') == 1
            assert first_resumed_boundary_matches and held_resume_samples >= 2
            photo('resumed')
            for index in range(2):
                advance(.1)
                photo(f'resumed-{index+1}')
            # Finish at a real outer-callback boundary, retaining no partial one.
            stop = session.inspect('run_until', dict(seconds=time+.1))
            assert stop.get('pc') == symbols['simulation_update'] and observer.pending is None
            memory = chip_memory(read)
            interval = (number('simulation_interval_whole', 4)*65536+
                        number('simulation_interval_fraction', 2))
            video = dict(presentation_last_line=number('presentation_last_line', 2),
                         simulation_interval_whole=number('simulation_interval_whole', 4),
                         simulation_interval_fraction=number('simulation_interval_fraction', 2))
            assert video == expected_video, 'Actual video selector/deadline contract differs'
            timing = observer.result(interval)
            missed_publications = number('missed_presentation_deadlines')
            assert missed_publications == 0
            raw = dict(records=session.records, uncompressed_bytes=session.raw_bytes,
                       cap_uncompressed_bytes=session.MAX_RAW_BYTES)
            surfaces = observer.surfaces.result()
            scene_offset = symbols['game_scene_objects']-symbols['game_core_state']
            original_objects = selected[scene_offset:scene_offset+64]
            active_publications = [p for p in surfaces['publications']
                                   if p['tutorial_fields']['tutorial_active']]
            for publication in active_publications:
                fields = publication['tutorial_fields']
                end = fields['tutorial_end']
                expected = bytearray(original_objects[:48])
                dx = fields['tutorial_x']-selected[end*10+3]
                dy = fields['tutorial_y']-selected[end*10+2]
                for obj in range(end*24,end*24+24,8):
                    expected[obj] = (expected[obj]+dy)&255
                    expected[obj+1] = (expected[obj+1]+dx)&255
                assert bytes.fromhex(publication['objects'])[:48] == bytes(expected), 'Published player is not latest edited native pose'
                assert not fields['tutorial_trails_enabled'], 'Trails unexpectedly gate the static proof'
            assert not any(r['state'].get('tutorial_render_phase') == 3
                           for r in timing['callbacks']), 'Disabled trails still consume menu callbacks'
            moving = [p for p in active_publications
                      if movement_start <= p['position']['seconds'] < movement_end]
            assert len({(p['tutorial_fields']['tutorial_x'],p['tutorial_fields']['tutorial_y'])
                        for p in moving}) >= 2, 'Continuous movement failed to publish changing player sprites'
            responses = []
            for request in observer.presentation_requests:
                pubs = [p for p in active_publications if
                        p['tutorial_fields']['tutorial_presentation_generation'] == request['generation']
                        and p['tutorial_fields']['tutorial_active_variant'] == request['variant']]
                if not pubs:
                    responses.append(dict(request, superseded_without_publication=True))
                    continue
                first = pubs[0]
                marker = next((p for p in pubs if p['tutorial_fields']['tutorial_marker_ready']),None)
                waiting = next((p for p in pubs if p['tutorial_fields']['tutorial_waiting_ready']),None)
                animation_pub = next((p for p in pubs if p['tutorial_fields']['tutorial_ball_mode'] == 2),None)
                origin = request['position']['seconds']
                responses.append(dict(request, player_publication_seconds=first['position']['seconds']-origin,
                    endpoint_publication_seconds=marker['position']['seconds']-origin if marker else None,
                    waiting_publication_seconds=waiting['position']['seconds']-origin if waiting else None,
                    animation_publication_seconds=animation_pub['position']['seconds']-origin if animation_pub else None))
            assert any(r.get('endpoint_publication_seconds') is not None for r in responses)
            assert any(r.get('waiting_publication_seconds') is not None for r in responses)
            held_requests = [r for r in responses if r['variant'] == 0
                             and held_edit_start <= r['position']['seconds'] < held_edit_end]
            held_latencies = [r['endpoint_publication_seconds'] for r in held_requests
                              if r.get('endpoint_publication_seconds') is not None]
            assert held_latencies, 'No fresh held-position to actual endpoint measurement'
            changed = next(p for p in moving if
                           (p['tutorial_fields']['tutorial_x'],p['tutorial_fields']['tutorial_y']) != old_xy)
            held_choice = next(p for p in active_publications if
                               p['position']['seconds'] >= held_action_start
                               and p['tutorial_fields']['tutorial_active_variant'] == 0
                               and p['tutorial_fields']['tutorial_marker_ready'])
            animation_steps = []
            previous = {}
            animation_epochs = {}
            for publication in active_publications:
                fields = publication['tutorial_fields']
                if fields['tutorial_ball_mode'] != 2 or fields['tutorial_menu']:
                    continue
                identity = (fields['tutorial_presentation_generation'], fields['tutorial_active_variant'],
                            fields['tutorial_render_generation'])
                old = previous.get(identity)
                index = fields['tutorial_animation_index']
                animation_epochs.setdefault(identity, []).append(publication)
                if old and index != old['tutorial_fields']['tutorial_animation_index']:
                    old_index = old['tutorial_fields']['tutorial_animation_index']
                    count = (fields['tutorial_counts'] >> (16 if identity[1] == 0 else 0)) & 65535
                    assert index == min(old_index+2, count-1), 'Dense native animation skipped samples or wrapped'
                    animation_steps.append(dict(generation=identity[0], variant=identity[1],
                        previous_index=old_index, index=index,
                        callback_interval=(publication['ready_generation']-old['ready_generation']) & 65535,
                        interval_seconds=publication['position']['seconds']-old['position']['seconds']))
                if old is None or index != old['tutorial_fields']['tutorial_animation_index']:
                    previous[identity] = publication
            assert len(animation_steps) >= 2, 'Insufficient actual native animation publications'
            cck_hz = 3546895 if standard == 'PAL' else 3579545
            tick_seconds = interval*5/(65536*cck_hz)
            field_seconds = (312.5 if standard == 'PAL' else 262.5)*227/cck_hz
            animation_cadence = []
            for identity, pubs in animation_epochs.items():
                first,last = pubs[0],pubs[-1]
                ticks = (last['tutorial_fields']['tutorial_animation_callback']-
                         first['tutorial_fields']['tutorial_animation_callback']) & 65535
                if ticks < 20:
                    continue
                elapsed = last['position']['seconds']-first['position']['seconds']
                nominal = ticks*tick_seconds
                drift = elapsed-nominal
                assert abs(drift) <= field_seconds+tick_seconds, 'Native ball playback accumulates game-time drift'
                producer_ticks = (last['ready_generation']-first['ready_generation']) & 65535
                assert abs(producer_ticks-ticks) <= 1, 'Animation loses nominal callback cadence'
                animation_cadence.append(dict(generation=identity[0], variant=identity[1],
                    ticks=ticks, producer_ticks=producer_ticks, elapsed_seconds=elapsed,
                    nominal_seconds=nominal, drift_seconds=drift,
                    maximum_drift_seconds=field_seconds+tick_seconds))
            assert animation_cadence, 'Insufficient normal-speed native playback extent'
            responsiveness = dict(requests=responses, moving_publications=len(moving),
                native_sprite_checks=len(surfaces['native_sprite_checks']),
                animation_steps=animation_steps, animation_dense_samples=True,
                animation_cadence=animation_cadence, animation_normal_speed=True,
                physical_movement_to_player_seconds=changed['position']['seconds']-movement_start,
                physical_held_choice_to_endpoint_seconds=held_choice['position']['seconds']-held_action_start,
                fresh_held_endpoint_seconds=held_latencies,
                fresh_held_edit=dict(start_seconds=held_edit_start,end_seconds=held_edit_end,
                                    generations=[r['generation'] for r in held_requests]),
                latest_pose_matches=True, trails_enabled=False,
                scope='Accepted request stores to specific actual native player/endpoint/waiting/animation publications; superseded requests need no prediction result.')
        target_log(directory, standard)
        capture = directory/'capture.json'
        atomic_json(capture, dict(boundaries=boundaries, actions=actions, waits=waits, timing=timing,
                                 memory=memory, loaded_hunks=loaded, surfaces=surfaces,
                                 visual_checks=visual_checks, responsiveness=responsiveness))
        report = dict(passed=True, subject='maintained-native', interface_flavor='enhanced',
            target=target, native_video=video, waits=waits,
            responsiveness=responsiveness,
            missed_presentation_deadlines=missed_publications,
            executable_sha256=hashlib.sha256(executable.read_bytes()).hexdigest(),
            capture=str(capture.relative_to(ROOT)), screenshots=screenshots,
            animation=str(movie.relative_to(ROOT)), literal_rpc=raw,
            literal_rpc_path=str((directory/'literal-rpc.jsonl.gz').relative_to(ROOT)),
            animation_frames=movie_info['frames'], animation_geometry=movie_info['geometry'],
            animation_source_frames=movie_info['source_frames'],
            visual_checks=visual_checks,
            shared_core=dict(bytes=len(shared), relocations=relocations, sink_branches=sinks,
                             normalized_sha256=hashlib.sha256(shared).hexdigest()), loaded_hunks=loaded,
            resume_readback=resume_readback, first_resumed_boundary_matches=first_resumed_boundary_matches,
            held_resume_no_pressed_edge=held_resume_samples >= 2,
            surface_ownership=dict(surface_write_count=surfaces['surface_write_count'],
                bank_write_count=surfaces['bank_write_count'],
                protected_surface_writes=0, protected_bank_writes=0,
                exact_queued_image_published=True,
                queued_images=len(surfaces['queues']), actual_publications=len(surfaces['publications']),
                court_restores_verified=surfaces['court_restores_verified'],
                resumed_native_banks=len({r['copper'] for r in surfaces['court_publications']
                    if r['after_resume'] and r['base'] == symbols['plane0']})),
            complete_state_bytes=318, public_history_bytes=72,
            native_memory=memory_summary(memory), timing=timing,
            frozen_boundaries=sum(bool(r['fields']['tutorial_active']) for r in boundaries),
            scope=f'Finite {standard} current-human-serve court prototype; physical double-tap/released-edit/held-edit/hold/release/modifier/menu/resume. No retained-shot navigation, live branching, full native gate or release claim.')
        manifest = json.loads((executable.parent/'baseline-rally.compile.json').read_text())
        artifacts = [p for p in directory.iterdir() if p.is_file() and p != output]
        transaction.finalize(output, report, [manifest], artifacts)
        print('tutorial-court-'+standard.lower()+' prototype capture PASS', flush=True)
    except BaseException as error:
        transaction.abort(error)
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--ntsc', action='store_true')
    run('NTSC' if parser.parse_args().ntsc else 'PAL')
