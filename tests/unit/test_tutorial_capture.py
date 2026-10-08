import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'scripts'))
from tutorial_capture import CallbackObserver, required_capture_extent


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
        report.update(target=TARGET, native_video=dict(presentation_last_line=311,
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
        files = {report[n]:'a'*64 for n in ('capture','literal_rpc_path','animation')}
        for row in report['screenshots']:
            row.update(source='build/tests/tutorial-court-pal/'+row['name']+'-viewport.png',
                       native='build/tests/tutorial-court-pal/'+row['name']+'.png',
                       source_geometry=[716,285], native_geometry=[256,208])
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


if __name__ == '__main__':
    unittest.main()
