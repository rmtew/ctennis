import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from tutorial_hotspots import WorkerTiming,decode_frame,summarize_workers,union


def encoded(pc=0x1234,total=10,instruction=7,wait=3,level=0xffffffff,vector=0xffffffff):
    return (struct.pack('<II',pc,0xffffffff-total),
            b'CLSM'+struct.pack('<II',1,1)+struct.pack('<IIIII',total,instruction,wait,level,vector))


class Tests(unittest.TestCase):
    def test_exact_charged_and_bus_wait(self):
        self.assertEqual(list(decode_frame(*encoded())),[(0x1234,10,7,3,False)])

    def test_irq_is_not_an_instruction(self):
        self.assertEqual(list(decode_frame(*encoded(pc=0x7fffffff,level=3,vector=27))),[(0x7fffffff,10,7,3,True)])
        with self.assertRaises(AssertionError):list(decode_frame(*encoded(pc=0x7fffffff)))

    def test_corrupt_or_partial_stream_rejects(self):
        stream,meta=encoded()
        for s,m in [(stream[:-1],meta),(stream,meta[:-1]),(stream,meta[:4]+struct.pack('<I',2)+meta[8:]),
                    encoded(wait=4)]:
            with self.assertRaises(AssertionError):list(decode_frame(s,m))

    def test_legal_max_chunk_fails_closed_as_unsupported_scope(self):
        with self.assertRaisesRegex(AssertionError,'Scope rejects legal'):
            list(decode_frame(*encoded(total=65535,instruction=65532)))

    def test_worker_scope_ignores_unobserved_enclosing_returns(self):
        calls={20:dict(return_pc=24,callee='game_preview_step'),30:dict(return_pc=34,callee='game_tick_dispatch_body')}
        timing=WorkerTiming(calls,{40,45},1000,1100)
        timing.state=dict(tutorial_generation=2,game_preview_status=3)
        def row(access,pc,slot,value,cck):
            return dict(access=access,pc=pc,addr=slot,value=value,size=4,position=dict(cck=cck))
        timing.active=True
        timing.observe(row('read',40,1096,24,0))
        timing.observe(row('write',20,1096,24,10))
        timing.observe(row('write',30,1092,34,20))
        timing.observe(row('read',45,1092,34,30))
        timing.observe(row('read',40,1096,24,50))
        result=summarize_workers(timing.rows,0,60,2)
        self.assertEqual(result['worker_calls'],1)
        self.assertEqual(result['worker_inclusive_bus_cck'],40)
        self.assertEqual(result['core_body_subtree_union_cck'],10)
        self.assertEqual(sum(result['exclusive_categories'].values()),40)

    def test_union_does_not_double_count_nested_spans(self):
        self.assertEqual(union([(10,20),(12,15),(20,25),(30,35)]),20)


if __name__=='__main__':unittest.main()
