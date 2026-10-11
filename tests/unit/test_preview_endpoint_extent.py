"""Negative controls for accepting incomplete endpoint API evidence."""
import copy
import unittest
from acceptance_campaign import preview_endpoint_extent


def evidence():
    rows=[]
    for x,y in ((111,153),(111,140),(111,128),(111,112),(111,98),(100,153),(119,153),(40,153),(180,153)):
        queries=[]
        if y!=98 and x in (111,100):
            for v in (0,1):
                accepted=y in (153,112)
                queries.append(dict(variant=v,reason=0 if accepted else 4,ready=accepted,dense_phase=4,
                    endpoint_phase=60 if accepted else 0,outcome=1 if accepted else 0,expected_outcome=1,
                    full318_equal_or_rejected_unchanged=True,dense_state_counts_events_cursors_unchanged=True))
        rows.append(dict(passed=True,x=x,y=y,queries=queries,attempted=[q['variant'] for q in queries],
            early_endpoints=[q['variant'] for q in queries if q['ready']],complete_launch_seeds_equal=True,
            original_dense_full318_points_events_equal=True,early_endpoint_unchanged_at_dense_completion=True,
            stale_and_cancelled_neutral=True))
    prefix=dict(passed=True,natural_reachability_claimed=False,cases=[dict(name=n,passed=True,
        original_phases=p,query_attempts=0 if p<=4 else 1,complete_state_equal=True,prefix_counted_once=True)
        for n,p in (('accepted-short',3),('accepted-long',78),('special-net-reflection',1))])
    return dict(passed=True,cases=rows,prefix_policy=prefix)


class EndpointExtentTests(unittest.TestCase):
    def test_complete_extent(self):
        self.assertTrue(preview_endpoint_extent(evidence()))

    def test_rejects_unpublished_acceptance_wrong_terminal_or_changed_dense(self):
        for key,value in (('ready',False),('reason',15),('endpoint_phase',4),('outcome',3),
            ('dense_state_counts_events_cursors_unchanged',False),('full318_equal_or_rejected_unchanged',False)):
            row=evidence();row['cases'][0]['queries'][0][key]=value
            self.assertFalse(preview_endpoint_extent(row),key)

    def test_rejects_stale_completion_and_short_query_overhead(self):
        for key in ('complete_launch_seeds_equal','early_endpoint_unchanged_at_dense_completion','stale_and_cancelled_neutral'):
            row=evidence();row['cases'][0][key]=False
            self.assertFalse(preview_endpoint_extent(row),key)
        row=evidence();row['prefix_policy']['cases'][0]['query_attempts']=1
        self.assertFalse(preview_endpoint_extent(row))
        row=evidence();row.pop('prefix_policy')
        self.assertFalse(preview_endpoint_extent(row))
