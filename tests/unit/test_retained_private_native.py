"""Coverage requires real interrupt acknowledgements inside a completed body."""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from run_retained_private_native import private_irq_proofs,cover_private_irqs

class RetainedIRQCoverage(unittest.TestCase):
    def observer(self,role,start=10,end=20):
        return SimpleNamespace(irq_entry_pc=100,irq_exit_pc=110,
            irq_writes=[dict(pc=100,position=dict(cck=12)),dict(pc=110,position=dict(cck=14))],
            body_frames=SimpleNamespace(records=[dict(entry_index=0,api_row_index=0,ownership=dict(active=role),
                start=dict(cck=start),end=dict(cck=end))]),api_rows=[])

    def test_irq_inside_api_but_outside_body_cannot_satisfy_role(self):
        observer=self.observer(1,start=15)
        self.assertEqual(private_irq_proofs(observer),[])
        observer.body_frames.records[0]['start']['cck']=10
        self.assertEqual([r['role'] for r in private_irq_proofs(observer)],[1])
        observer.irq_writes.pop()
        self.assertEqual(private_irq_proofs(observer),[])

    def test_fixed_budget_normal_api_coverage_is_cancelled(self):
        observer=self.observer(2)
        calls=[]
        native=SimpleNamespace(observer=observer,status=1,generation=7)
        def call(name,args):
            calls.append((name,args));observer.api_rows.append(dict(name=name))
        native.call=call
        native.number=lambda name,width=2:native.generation if name=='game_preview_generation' else native.status
        def request(ordinal,x,y):
            native.generation+=1;call('game_preview_request',[native.generation-1,ordinal,x,y]);return native.generation
        native.request=request
        def step(generation,budget):
            call('game_preview_step',[generation,budget])
            observer.body_frames.records.append(dict(entry_index=1,api_row_index=2,ownership=dict(active=1),start=dict(cck=10),end=dict(cck=20)))
            return dict(bodies=3)
        native.step=step
        row=cover_private_irqs(native,1,20,30)
        self.assertTrue(row['passed']);self.assertTrue(row['cancelled_incomplete_job'])
        self.assertEqual([n for n,a in calls],['game_preview_cancel','game_preview_request','game_preview_step','game_preview_cancel'])
        self.assertEqual(calls[2][1],[8,3])
        self.assertEqual(row['worker_body_counts'],[3])
        self.assertEqual([p['role'] for p in row['final_proofs']],[1,2])

    def test_ready_at_irq_success_cannot_be_labelled_incomplete(self):
        observer=self.observer(2)
        native=SimpleNamespace(observer=observer,status=1,generation=8,
            call=lambda *a:observer.api_rows.append({}),request=lambda *a:8)
        native.number=lambda name,width=2:native.generation if name=='game_preview_generation' else native.status
        def step(*args):
            observer.body_frames.records.append(dict(entry_index=1,api_row_index=2,
                ownership=dict(active=1),start=dict(cck=10),end=dict(cck=20)))
            native.status=5;return dict(bodies=3)
        native.step=step
        with self.assertRaisesRegex(AssertionError,'completed before diagnostic cancellation'):
            cover_private_irqs(native,1,20,30)

    def test_ready_without_missing_role_is_failure_not_reuse(self):
        observer=self.observer(2)
        native=SimpleNamespace(observer=observer,call=lambda *a:None,request=lambda *a:8,
            number=lambda name,width=2:7 if name=='game_preview_generation' else 5)
        with self.assertRaisesRegex(AssertionError,'must resolve a cold'):
            cover_private_irqs(native,1,20,30)
