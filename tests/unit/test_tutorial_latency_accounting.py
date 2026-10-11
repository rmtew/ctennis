import importlib.util
from pathlib import Path
import unittest


spec = importlib.util.spec_from_file_location('accounting',
    Path(__file__).resolve().parents[2]/'scripts/tutorial_latency_accounting.py')
accounting = importlib.util.module_from_spec(spec)
spec.loader.exec_module(accounting)


class PartitionTests(unittest.TestCase):
    def test_nested_and_overlapping_wall_spans_are_counted_once(self):
        result = accounting.partition(10, 110,
            [(10, 10, 100), (4, 20, 80), (1, 30, 50), (1, 40, 60)])
        self.assertEqual(sum(result.values()), 100)
        self.assertEqual(result['shared_preview_dispatch'], 30)
        self.assertEqual(result['preview_envelopes_state_support'], 30)
        self.assertEqual(result['scheduler_owner_other'], 30)
        self.assertEqual(result['unclassified'], 10)

    def test_clip_half_open_edges_and_zero_spans(self):
        result = accounting.partition(20, 40,
            [(0, 0, 20), (1, 20, 30), (2, 30, 60), (3, 25, 25)])
        self.assertEqual(result['landing_algorithm'], 0)
        self.assertEqual(result['shared_preview_dispatch'], 10)
        self.assertEqual(result['hardware_service'], 10)
        self.assertEqual(sum(result.values()), 20)

    def test_union_does_not_sum_nested_parents(self):
        self.assertEqual(accounting.union_duration(0, 100,
            [(10, 80), (20, 40), (60, 90)]), 80)

    def test_intersection_unions_nested_service_masks(self):
        self.assertEqual(accounting.intersection_duration(15, 85,
            [(0, 30), (20, 60), (80, 100)], [(10, 90), (20, 50)]), 50)

    def test_known_tail_is_subtracted_before_collapsing(self):
        full = dict.fromkeys(accounting.CATEGORIES, 10)
        tail = dict.fromkeys(accounting.CATEGORIES, 2)
        result = accounting.collapsed_breakdown(full, tail, 1000)
        self.assertEqual(sum(result['partition_cck'].values()), sum(full.values()))
        self.assertEqual(result['partition_cck']['known_upper_bound_to_qualifying_copjmp'],
                         sum(tail.values()))

    def test_selected_zero_cohort_uses_next_entry_and_job_invalidation(self):
        def call(name,start,end):
            return dict(callee=name,entry=dict(cck=start),exit=dict(cck=end))
        owners = [dict(start=a,end=b,accepted=accepted)
                  for a,b,accepted in [(20,30,False),(40,50,False),
                                       (60,70,True),(80,90,False),(95,99,False)]]
        calls = [call('tutorial_background',o['start'],o['end']) for o in owners]
        calls += [call('tutorial_background_class',a+1,b-1)
                  for a,b in [(20,30),(40,50),(80,90),(95,99)]]
        writes = []
        for a,b in [(20,30),(40,50),(80,90)]:
            writes += [dict(position=dict(cck=a+1),field='tutorial_job_variant',value=0),
                       dict(position=dict(cck=b-1),field='tutorial_job_budget',value=0)]
        # A residual turn ending at variant0 is not the selected branch.
        writes += [dict(position=dict(cck=96),field='tutorial_job_variant',value=1),
                   dict(position=dict(cck=97),field='tutorial_job_variant',value=0),
                   dict(position=dict(cck=98),field='tutorial_job_budget',value=0)]
        c = dict(stack_timing=dict(calls=calls),scheduler_job_writes=writes,
                 boundaries=[dict(position=dict(cck=0),fields=dict(
                     tutorial_active_variant=1,tutorial_generation=6)),
                     dict(position=dict(cck=100),fields=dict(
                     tutorial_active_variant=0,tutorial_generation=7))],
                 timing=dict(callbacks=[dict(callback=1,completion=dict(cck=10))]))
        rows = accounting.selected_classifier_zero_cohort(c,owners)
        self.assertEqual([r['generation'] for r in rows],[7,7,7])
        self.assertEqual([r['repeat_since_same_epoch_first'] for r in rows],
                         [False,True,False])
