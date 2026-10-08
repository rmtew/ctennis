import copy
from pathlib import Path
import sys
import io
import tempfile
from unittest.mock import patch
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'scripts'))
from tutorial_capture import (CaptureSession, CallbackObserver, SurfaceObserver,
                              required_capture_extent, assert_native_text, assert_court_origins,
                              check_native_presentation)
from copperline_test_session import NativeControlSession


class TutorialCaptureTests(unittest.TestCase):
    def test_native_sprite_contract_rejects_header_and_stale_sample(self):
        image = (Path(__file__).resolve().parents[2]/'assets/native/scene/sprite-images.bin').read_bytes()
        objects = bytearray(64)
        objects[48:56] = bytes((11,10,0,0,1,1,0,0))
        sprites = bytearray(576)
        sprites[:72] = bytes((56,85,72,0))+image[:64]+bytes(4)
        paths = bytearray(4096)
        paths[8:16] = bytes((0,0,10,11,0,0,1,0))
        snapshot = dict(objects=objects.hex(),sprite_bytes=sprites.hex(),
            tutorial_fields=dict(tutorial_scene_layer=2,tutorial_ball_mode=1,tutorial_menu=0,
                tutorial_presentation_generation=7,tutorial_generation=7,
                tutorial_active_variant=0,tutorial_counts=2<<16,tutorial_animation_index=0))
        self.assertTrue(check_native_presentation(snapshot,paths)['matched'])
        broken = copy.deepcopy(snapshot)
        broken['sprite_bytes'] = '37'+broken['sprite_bytes'][2:]
        with self.assertRaises(AssertionError):
            check_native_presentation(broken,paths)
        broken = copy.deepcopy(snapshot)
        broken['tutorial_fields']['tutorial_generation'] = 8
        with self.assertRaises(AssertionError):
            check_native_presentation(broken,paths)
        paths[10] = 12
        with self.assertRaises(AssertionError):
            check_native_presentation(snapshot,paths)

    def test_authored_font_contract_rejects_absent_and_wrong_highlight(self):
        from PIL import Image
        text = 'RESUME LATEST'
        font = (Path(__file__).resolve().parents[2]/'assets/native/title/font.bin').read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'menu.png'
            image = Image.new('RGB',(256,208),'black')
            image.save(path)
            with self.assertRaises(AssertionError):
                assert_native_text(path,143,text,True)
            left = ((32-len(text))//2)*8
            for column,char in enumerate(text):
                for row in range(8):
                    byte = font[ord(char)*8+row] ^ 255
                    for bit in range(8):
                        image.putpixel((left+column*8+bit,143+row),
                            (255,255,255) if byte & (128>>bit) else (0,0,0))
            image.save(path)
            self.assertTrue(assert_native_text(path,143,text,True)['matched'])
            with self.assertRaises(AssertionError):
                assert_native_text(path,143,text,False)

    def test_fixed_court_restore_contract_rejects_original_surface(self):
        symbols = dict(copperlist=0)
        bank = bytearray(512)
        entries = [('cop_bpl'+str(n)+'h',None,n,0) for n in range(4)]
        entries += [('score_cop_'+str(244+n)+'_hi','score_cop_'+str(244+n)+'_lo',n,42) for n in range(4)]
        entries += [('score_cop_point_restore'+str(n)+'_hi','score_cop_point_restore'+str(n)+'_lo',n,64) for n in (0,2,3)]
        entries += [('score_cop_'+str(224+n)+'_hi','score_cop_'+str(224+n)+'_lo',n,104) for n in (0,2,3)]
        entries += [('score_cop_games_restore_hi','score_cop_games_restore_lo',1,120)]
        for index,(hi,lo,plane,row) in enumerate(entries):
            offset = index*8
            symbols[hi] = offset
            if lo: symbols[lo] = offset+4
            pointer = 100000+plane*6144+row*32
            bank[offset:offset+2] = (0xe0+plane*4).to_bytes(2,'big')
            bank[offset+4:offset+6] = (0xe2+plane*4).to_bytes(2,'big')
            bank[offset+2:offset+4] = (pointer>>16).to_bytes(2,'big')
            bank[offset+6:offset+8] = (pointer&65535).to_bytes(2,'big')
        self.assertEqual(assert_court_origins(bank,symbols,100000)['entries'],15)
        offset = symbols['score_cop_games_restore_lo']+2
        bank[offset:offset+2] = bytes(2)
        with self.assertRaises(AssertionError):
            assert_court_origins(bank,symbols,100000)

    def test_raw_overflow_preserves_failure_and_allows_shutdown(self):
        session = CaptureSession(Path('/tmp'))
        session.raw = io.StringIO()
        session.raw_bytes = session.records = 0
        session.raw_overflow = False
        session.MAX_RAW_BYTES = 1
        with self.assertRaisesRegex(AssertionError, 'raw-byte cap'):
            session.record(dict(type='request', method='run_until'))
        self.assertTrue(session.raw_overflow)
        self.assertEqual(session.raw.getvalue(), '')
        with patch.object(NativeControlSession, 'inspect', return_value={'shutdown': True}) as stop:
            self.assertEqual(session.inspect('shutdown'), {'shutdown': True})
        stop.assert_called_once_with('shutdown', None)

    def test_complete_callback_rejects_late_or_partial_work(self):
        observer = CallbackObserver(0, dict(game_stack_top=1024))
        observer.timer_start = dict(cck=0)
        observer.timer_origin = 65535
        observer.rows = [dict(callback=1, entry=dict(cck=0),
                              completion=dict(cck=50000), work_cck=50000)]
        result = observer.result(11838*65536+14906)
        self.assertGreater(result['minimum_absolute_headroom_cck'], 0)
        observer.rows[0]['completion']['cck'] = 100000
        with self.assertRaises(AssertionError):
            observer.result(11838*65536+14906)
        observer.rows[0]['completion']['cck'] = 50000
        observer.pending = dict(callback=2)
        with self.assertRaises(AssertionError):
            observer.result(11838*65536+14906)

    def test_capture_gate_rejects_missing_or_lossy_evidence(self):
        names = ['title','released-serve','edited-serve','held-serve',
                 'released-edited-serve','options','options-resume','resumed','resumed-1','resumed-2']
        names += [f'animation-{i:02d}' for i in range(24)]
        report = dict(complete_state_bytes=318, public_history_bytes=72,
                      frozen_boundaries=100, animation='build/tests/tutorial/movie.gif',
                      native_memory=dict(chip_free_bytes=60000),
                      screenshots=[dict(name=n) for n in names],
                      timing=dict(completed_callbacks=101, pending_callback=None,
                                  dropped_notifications=0, minimum_absolute_headroom_cck=100),
                      literal_rpc=dict(uncompressed_bytes=123))
        from native_evidence import TARGET
        report.update(target=TARGET, missed_presentation_deadlines=0,
            native_video=dict(presentation_last_line=311,
            simulation_interval_whole=11838, simulation_interval_fraction=14906),
            capture='build/tests/tutorial-court-pal/capture.json',
            literal_rpc_path='build/tests/tutorial-court-pal/literal-rpc.jsonl.gz',
            animation='build/tests/tutorial-court-pal/movie.gif', animation_frames=24,
            animation_source_frames=24, animation_geometry=[256,208],
            loaded_hunks=[dict(matched=True, expected_sha256='a'*64, actual_sha256='a'*64)],
            shared_core=dict(bytes=18020, relocations=257, sink_branches=14,
                normalized_sha256='9a457929bc223b843132bb53af7d604ed574441e32c4651eb69897aa0b48689d'),
            resume_readback=dict(state='00'*318, expected_state='00'*318, backup='00'*318,
                history='00'*72, expected_history='00'*72),
            first_resumed_boundary_matches=True, held_resume_no_pressed_edge=True)
        report['surface_ownership'] = dict(surface_write_count=1, bank_write_count=1,
            protected_surface_writes=0, protected_bank_writes=0,
            exact_queued_image_published=True, queued_images=1, actual_publications=1,
            court_restores_verified=True, resumed_native_banks=3)
        report['responsiveness'] = dict(latest_pose_matches=True, trails_enabled=False,
            moving_publications=2, native_sprite_checks=2, animation_dense_samples=True,
            animation_steps=[dict(previous_index=n,index=n+2,interval_seconds=.04) for n in (2,4)],
            requests=[dict(player_publication_seconds=.02, endpoint_publication_seconds=1.,
                           waiting_publication_seconds=None),
                      dict(player_publication_seconds=.02, waiting_publication_seconds=.2)])
        report['visual_checks'] = dict(
            options=[dict(matched=True, selected=n==0) for n in range(3)],
            **{'options-resume':[dict(matched=True, selected=n==1) for n in range(3)],
               'released-wait':dict(raster=dict(matched=True),state='40'+'00'*317,
                   end=0,ordinal=0xffff,phase=0x40,ai=0,launches=0,outcome=6,
                   sample_count=256,sample_limit=256,incomplete=True,outgoing_shot_claimed=False)})
        files = {report[n]:'a'*64 for n in ('capture','literal_rpc_path','animation')}
        for row in report['screenshots']:
            row.update(source='build/tests/tutorial-court-pal/'+row['name']+'-viewport.png',
                       native='build/tests/tutorial-court-pal/'+row['name']+'.png',
                       source_geometry=[716,285], native_geometry=[256,208])
            row.update(fields=dict(tutorial_published_generation=1),
                       observed_surface=dict(generation=1, surface_sha256='a'*64,
                           scope='stable-background-only', first_publication_frame=1, observation_frame=3))
            files[row['source']] = files[row['native']] = 'a'*64
        report['evidence'] = dict(files=files, actual_target=TARGET)
        self.assertTrue(required_capture_extent(report))
        ntsc = copy.deepcopy(report)
        ntsc['target']['video'] = ntsc['evidence']['actual_target']['video'] = 'NTSC'
        # A region label cannot substitute for the actual timer/line selectors.
        self.assertFalse(required_capture_extent(ntsc))
        ntsc['native_video'] = dict(presentation_last_line=261,
            simulation_interval_whole=11947, simulation_interval_fraction=13180)
        self.assertFalse(required_capture_extent(ntsc))  # PAL artifact paths
        for name in ('capture','literal_rpc_path','animation'):
            ntsc[name] = ntsc[name].replace('-pal/','-ntsc/')
        for row in ntsc['screenshots']:
            for name in ('source','native'):
                row[name] = row[name].replace('-pal/','-ntsc/')
        ntsc['evidence']['files'] = {k.replace('-pal/','-ntsc/'):v
                                   for k,v in ntsc['evidence']['files'].items()}
        self.assertTrue(required_capture_extent(ntsc))
        ntsc['native_video']['presentation_last_line'] = 311
        self.assertFalse(required_capture_extent(ntsc))
        for key, value in [('screenshots',[]), ('frozen_boundaries',0),
                           ('complete_state_bytes',88), ('animation',None)]:
            broken = copy.deepcopy(report); broken[key] = value
            self.assertFalse(required_capture_extent(broken), key)
        for key, value in [('dropped_notifications',1), ('pending_callback',{}),
                           ('minimum_absolute_headroom_cck',-1),
                           ('minimum_absolute_headroom_cck',float('inf')), ('completed_callbacks',1)]:
            broken = copy.deepcopy(report); broken['timing'][key] = value
            self.assertFalse(required_capture_extent(broken), key)
        broken = copy.deepcopy(report)
        broken['evidence']['files'].pop(broken['screenshots'][0]['source'])
        self.assertFalse(required_capture_extent(broken))
        for field, value in [('observation_frame', 2), ('scope', 'latest-bank'),
                             ('first_publication_frame', None)]:
            broken = copy.deepcopy(report)
            broken['screenshots'][1]['observed_surface'][field] = value
            self.assertFalse(required_capture_extent(broken), field)
        broken = copy.deepcopy(report); broken['missed_presentation_deadlines'] = 1
        self.assertFalse(required_capture_extent(broken))
        broken = copy.deepcopy(report); broken['resume_readback']['state'] = 'ff'*318
        self.assertFalse(required_capture_extent(broken))
        broken = copy.deepcopy(report); broken['visual_checks']['options'][0]['matched'] = False
        self.assertFalse(required_capture_extent(broken))
        broken = copy.deepcopy(report); broken['visual_checks']['released-wait']['launches'] = 1
        self.assertFalse(required_capture_extent(broken))
        broken = copy.deepcopy(report); broken['surface_ownership']['resumed_native_banks'] = 2
        self.assertFalse(required_capture_extent(broken))
        for key,value in [('latest_pose_matches',False),('trails_enabled',True),
                          ('moving_publications',1),('native_sprite_checks',0),
                          ('animation_steps',[]),('animation_dense_samples',False),('requests',[])]:
            broken = copy.deepcopy(report); broken['responsiveness'][key] = value
            self.assertFalse(required_capture_extent(broken),key)
        broken = copy.deepcopy(report)
        broken['responsiveness']['requests'][0]['endpoint_publication_seconds'] = float('nan')
        self.assertFalse(required_capture_extent(broken))

    def test_partial_longword_metadata_reconstructs_literal_bytes(self):
        symbols = dict(game_stack_top=1024, game_stack_bottom=512,
                       simulation_started_updates=10, simulation_updates=12,
                       simulation_timer_origin=14, generation=20)
        observer = CallbackObserver(0, symbols)
        observer.watches(dict(generation=4), lambda a,n:bytes(n))
        for address, value in [(20, 0x1234),(22, 0xabcd)]:
            observer.observe(dict(method='event.mmio', params=dict(addr=address,
                value=value, size=2, position=dict(cck=1), dropped_notifications=0)))
        self.assertEqual(observer.state['generation'], 0x1234abcd)
        with self.assertRaises(AssertionError):
            observer.observe(dict(method='event.frame', params=dict(dropped_notifications=1)))
        with self.assertRaises(AssertionError):
            observer.observe(dict(method='event.frame', params={}))

    def surface_fixture(self):
        symbols = dict(copperlist=400, copperlist_end=432, cop_bpl0h=400,
                       copperlist_back=600, copperlist_third=800,
                       tutorial_surface0=10000, tutorial_surface1=34576,
                       tutorial_surfaces_end=59152, plane0=65000,
                       title_copper=90000, ready_completed=8)
        def read(address, size):
            if address not in (400,600,800): return bytes(size)
            base = 10000 if address == 400 else 34576
            data = bytearray()
            for plane in range(4):
                ptr = base+plane*6144
                for word in (0xe0+plane*4, ptr>>16, 0xe2+plane*4, ptr&65535):
                    data.extend(word.to_bytes(2,'big'))
            return bytes(data)
        observer = SurfaceObserver(symbols, read)
        state = dict(ready_copper=600, display_ready=1, ready_completed=255,
                     tutorial_render_surface=10000, tutorial_published_generation=1,
                     ready_generation=5, simulation_started_updates=5,
                     ready_title_display=0, presentation_copper=600)
        def event(addr, value, size=2):
            return dict(addr=addr, value=value, size=size,
                        position=dict(cck=10, frame=1, vpos=253))
        return observer, state, event

    def test_surface_guard_rejects_visible_and_queued_writes(self):
        observer, state, event = self.surface_fixture()
        observer.hardware_copper = 400
        for address in (10000,34576,400,600):
            with self.assertRaises(AssertionError):
                observer.observe(event(address,0), state)

    def test_actual_publication_requires_complete_queue(self):
        observer, state, event = self.surface_fixture()
        state.update(tutorial_render_generation=1,tutorial_ball_mode=1)
        observer.observe(event(8,255,1), state)
        observer.observe(event(0xdff080,600,4), state)
        observer.observe(event(0xdff088,0), state)
        observer.last_frame = 3
        self.assertTrue(observer.current(1))
        self.assertIsNotNone(observer.current_presentation(state))
        state['tutorial_render_generation'] = 2
        self.assertIsNone(observer.current_presentation(state))
        state['tutorial_render_generation'] = 1
        state['tutorial_ball_mode'] = 2
        self.assertIsNone(observer.current_presentation(state))
        self.assertEqual(observer.displayed['surface'], 34576)
        # Animation can publish another Copper bank for the same background.
        # Screenshot metadata must bind only the stable surface, never that bank.
        surface = observer.completed_surface(1)
        self.assertEqual(surface['scope'], 'stable-background-only')
        self.assertNotIn('copper', surface)
        self.assertNotIn('bank_sha256', surface)
        self.assertEqual(surface['first_publication_frame'], 1)
        state['ready_completed'] = 0
        with self.assertRaises(AssertionError):
            observer.observe(event(0xdff088,0), state)
        state['ready_completed'] = 255
        late = event(0xdff088,0); late['position']['vpos'] = 312
        with self.assertRaises(AssertionError):
            observer.observe(late, state)

    def test_static_court_publication_retains_immutable_assets(self):
        observer, state, event = self.surface_fixture()
        bank = observer.banks[600]
        for plane in range(4):
            pointer = observer.static_base+plane*6144
            bank[plane*8+2:plane*8+4] = (pointer>>16).to_bytes(2,'big')
            bank[plane*8+6:plane*8+8] = (pointer&65535).to_bytes(2,'big')
        observer.observe(event(8,255,1), state)
        observer.observe(event(0xdff080,600,4), state)
        observer.observe(event(0xdff088,0), state)
        observer.last_frame = 3
        self.assertTrue(observer.current(1))
        self.assertEqual(observer.displayed['surface'], observer.static_base)
        with self.assertRaisesRegex(AssertionError,'immutable original court'):
            observer.observe(event(observer.static_base,0), state)


if __name__ == '__main__':
    unittest.main()
