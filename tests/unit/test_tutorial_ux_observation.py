import sys
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
from tutorial_ux_observation import UXSurfaceObserver
from coherent_publication import CoherentSurfaceObserver


class TutorialUXOwnershipTests(TestCase):
    def observer(self):
        observer = UXSurfaceObserver.__new__(UXSurfaceObserver)
        observer.symbols = dict(tutorial_surface0=1000, tutorial_surface1=2000,
            tutorial_footer0=3000, tutorial_footer1=4000, tutorial_canvas_markers=5000)
        observer.images = {1000: bytearray(24576), 2000: bytearray(24576)}
        observer.footers = {3000: bytearray(512), 4000: bytearray(512)}
        observer.markers = bytearray(40)
        observer.hardware_copper = 10
        observer.queued = None
        observer.footer_writes = 0
        return observer

    def test_private_canvas_rejects_original_or_other_footer(self):
        for pointer in (6000, 4000):
            observer = self.observer()
            with patch.object(CoherentSurfaceObserver, 'snapshot', return_value=dict(surface=1000, tutorial_fields={})), \
                 patch.object(observer, 'footer', return_value=pointer):
                with self.assertRaisesRegex(AssertionError, 'Footer does not belong'):
                    observer.snapshot(20, dict(tutorial_active=1), {})

    def test_publication_rejects_changed_queued_footer(self):
        observer = self.observer()
        observer.queued = dict(copper=20, footer_bytes=bytes(512).hex(), landing=dict(valid=False))
        observer.footers[3000][100] = 1
        with patch.object(CoherentSurfaceObserver, 'snapshot', return_value=dict(surface=1000, tutorial_fields={})), \
             patch.object(observer, 'footer', return_value=3000):
            with self.assertRaisesRegex(AssertionError, 'changes queued footer'):
                observer.snapshot(20, dict(tutorial_active=1), {}, actual=True)

    def test_write_rejects_displayed_and_completed_queued_footer(self):
        for protected in (10, 20):
            observer = self.observer()
            with patch.object(observer, 'footer', side_effect=lambda copper: 3000 if copper == protected else 4000):
                with self.assertRaisesRegex(AssertionError, 'displayed/eligible queued footer'):
                    observer.observe(dict(addr=3000, size=2, value=0),
                        dict(ready_copper=20, display_ready=1, ready_completed=1,
                             tutorial_render_surface=1000))

    def test_old_prediction_cannot_use_neutral_pose_exception(self):
        for changed in ('tutorial_ball_mode', 'tutorial_menu', 'tutorial_marker_ready'):
            observer = self.observer()
            fields = dict(tutorial_generation=1, tutorial_ball_mode=0,
                tutorial_menu=0, tutorial_marker_ready=0)
            fields[changed] = 1
            with patch.object(CoherentSurfaceObserver, 'snapshot',
                              return_value=dict(surface=1000, tutorial_fields=fields)):
                with self.assertRaisesRegex(AssertionError, 'Stale prediction-bearing'):
                    observer.snapshot(20, dict(tutorial_generation=2), {}, actual=True)
