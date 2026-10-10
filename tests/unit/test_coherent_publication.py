import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from coherent_publication import qualified_endpoint,early_endpoint


def scene():
    return dict(position=dict(cck=100),tutorial_fields=dict(tutorial_generation=7,tutorial_presentation_generation=7,
        tutorial_placement_ready=255,tutorial_placement_dirty=255,tutorial_active_variant=0,tutorial_ball_mode=1,
        tutorial_marker_ready=255,tutorial_available_outcomes=0),
        publication_live_fields=dict(tutorial_generation=7,tutorial_presentation_generation=7,tutorial_placement_dirty=0,tutorial_ball_mode=1),
        endpoint_outcomes=65536,endpoint_ready=65280,endpoint_generation=7,endpoint_points=bytes(16).hex(),
        native_sprite_check=dict(matched=True,actual_sample=bytes(8).hex()))


class CoherentPublication(unittest.TestCase):
    def test_queued_dirty_flag_does_not_override_clean_actual_publication(self):
        self.assertTrue(early_endpoint(scene(),7,50))

    def test_dirty_at_copjmp_does_not_meet_controller_clean_gate(self):
        s=scene();s['publication_live_fields']['tutorial_placement_dirty']=255
        self.assertFalse(qualified_endpoint(s,7,50))

    def test_missing_live_publication_fields_cannot_pass(self):
        s=scene();s.pop('publication_live_fields')
        self.assertFalse(early_endpoint(s,7,50))

    def test_failed_sprite_check_is_not_publication_evidence(self):
        s=scene();s['native_sprite_check']['matched']=False
        self.assertFalse(early_endpoint(s,7,50))

    def test_live_clean_does_not_repair_stale_queued_bank(self):
        s=scene();s['tutorial_fields']['tutorial_generation']=6
        self.assertFalse(early_endpoint(s,7,50))

    def test_live_marker_does_not_repair_queued_animation(self):
        s=scene();s['tutorial_fields']['tutorial_ball_mode']=2
        self.assertFalse(early_endpoint(s,7,50))

    def test_terminal_dense_or_wrong_point_is_not_early_endpoint(self):
        for key,value in (('tutorial_available_outcomes',65536),('tutorial_marker_ready',0)):
            s=scene();s['tutorial_fields'][key]=value
            self.assertFalse(early_endpoint(s,7,50))
        s=scene();s['native_sprite_check']['actual_sample']=(bytes([1])*8).hex()
        self.assertFalse(early_endpoint(s,7,50))


if __name__=='__main__':unittest.main()
