import importlib.util
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
spec=importlib.util.spec_from_file_location('queries',ROOT/'scripts/tutorial_latency_queries.py')
q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)


def call(index,name,start,end,depth,caller=None):
    return dict(index=index,callee=name,entry=dict(cck=start),exit=dict(cck=end),depth=depth,caller=caller)


class QueryTests(unittest.TestCase):
    def test_nested_owner_classification_deepest_and_gaps(self):
        rows=[call(1,'tutorial_background',10,90,0),
              call(2,'tutorial_background_class',20,70,1),
              call(3,'tutorial_dispatch_allowance',30,40,2)]
        spans=q.primary_segments(rows,0,100)
        self.assertEqual(sum(b-a for a,b,*_ in spans),100)
        self.assertEqual(sum(b-a for a,b,cat,*_ in spans if cat=='scheduler_classification'),50)
        self.assertEqual(sum(b-a for a,b,cat,deep,*_ in spans if deep==3),10)
        self.assertEqual(sum(b-a for a,b,cat,deep,owner,*_ in spans if owner is None),20)

    def test_irq_service_priority_does_not_double_count_timer(self):
        rows=[call(1,'account_sim_timer',0,100,0),
              call(2,'read_sim_timer',10,90,1),
              call(3,'poll_presentation',30,50,2)]
        spans=q.primary_segments(rows,0,100)
        self.assertEqual(sum(b-a for a,b,cat,deep,owner,acc,service in spans if service=='account_sim_timer'),80)
        self.assertEqual(sum(b-a for a,b,cat,deep,owner,acc,service in spans if service=='poll_presentation'),20)

    def test_outgoing_ball_scope_preserves_landing_owner(self):
        rows=[call(1,'landing_try_step',0,60,0),
              call(2,'game_ball_tick',10,20,1,'landing_try_step'),
              call(3,'game_ball_tick',70,90,0,'game_preview_flight_one')]
        spans=q.primary_segments(rows,0,100)
        self.assertEqual(sum(b-a for a,b,cat,*_ in spans if cat=='landing_algorithm'),60)
        self.assertEqual(sum(b-a for a,b,cat,*_ in spans if cat=='actual_outgoing_ball'),20)

    def test_next_entry_snapshot_and_private_bytes_remain_distinct(self):
        rows=dict(boundaries=[dict(position=dict(cck=10),fields=dict(tutorial_generation=1)),
                              dict(position=dict(cck=20),fields=dict(tutorial_generation=2))])
        self.assertEqual(q.next_snapshot(rows,11)['fields']['tutorial_generation'],2)
        self.assertIsNone(q.next_snapshot(rows,21))
        v=q.scrub(dict(state='00'*318,workspace='00'*48,counts='00010002'))
        self.assertNotIn('workspace',v)
        self.assertEqual(v['state']['omitted_bytes'],318)
        self.assertEqual(v['counts'],'00010002')

    def test_accepted_work_and_callback_fence_observed_signature_repeats(self):
        row=dict(accepted=False,next_entry_generation=99,next_entry_preview_generation=99,
            route_witness='selected_primary_witness',classification='zero_budget_without_admission',
            final_job_fields=dict(tutorial_job_variant=0,tutorial_job_budget=0))
        self.assertEqual(q.observed_signature_repeats([
            dict(owners=[row,row,dict(accepted=True),row]),dict(owners=[row])]),
            {'zero_budget_without_admission':1})
