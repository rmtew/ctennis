import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'scripts'))
from tutorial_capture import CallbackObserver, SurfaceObserver, required_capture_extent


class TutorialCaptureTests(unittest.TestCase):
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
                 'released-edited-serve','options','resumed']
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
            exact_queued_image_published=True, queued_images=1, actual_publications=1)
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
                       tutorial_surfaces_end=59152, title_copper=90000, ready_completed=8)
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
        observer.observe(event(8,255,1), state)
        observer.observe(event(0xdff080,600,4), state)
        observer.observe(event(0xdff088,0), state)
        observer.last_frame = 3
        self.assertTrue(observer.current(1))
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


if __name__ == '__main__':
    unittest.main()
