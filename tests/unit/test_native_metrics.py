"""Corruption, missing-evidence and phase-boundary checks for native metrics."""
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from native_hunk import hunk_layout
from native_metrics_observation import distribution, MetricsObserver
from native_metrics import identity, metric_deltas


class MetricsTests(unittest.TestCase):
    def test_hunks_count_payload_not_metadata_and_reject_truncation(self):
        words=[1011,0,2,0,1,1,0x40000002,1001,1,0x4e754e75,1010,1003,2,1010]
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'game';path.write_bytes(struct.pack('>'+len(words)*'I',*words))
            result=hunk_layout(path)
            self.assertEqual((result['code_bytes'],result['data_bytes'],result['bss_bytes']),(4,0,8))
            self.assertEqual(result['hunks'][1]['memory'],'chip')
            path.write_bytes(path.read_bytes()[:-1])
            with self.assertRaisesRegex(ValueError,'Truncated'):hunk_layout(path)

    def test_no_samples_remains_unknown_and_nearest_rank_is_bounded(self):
        self.assertIsNone(distribution([],100))
        result=distribution(range(1,101),90)
        self.assertEqual(result['typical_median_cck'],50.5)
        self.assertEqual(result['p95_cck'],95)
        self.assertEqual(result['minimum_headroom_cck'],-10)

    def test_bus_call_extents_ignore_nested_stack_and_catch_missing_return(self):
        names=('simulation_update','prepare_title_display','game_stack_top',
               'simulation_started_updates','simulation_updates','simulation_timer_origin',
               'game_lifecycle','game_mode','game_flight','ui_paused','ui_demo','ui_page')
        symbols=dict(zip(names,(0,100,1000,200,202,204,206,208,209,210,211,212)))
        listing='\n'.join(f'00:{pc:08X} 6100 1: bsr {target}' for pc,target in
                          ((10,'game_render_sprites'),(20,'game_tick_dispatch'),(30,'game_render_sprites'),(40,'game_tick_dispatch')))
        observer=MetricsObserver(0,symbols,listing)
        def event(a,cck,access='write',pc=0,size=2,v=1):
            observer.observe({'method':'event.mmio','params':{'addr':a,'value':v,'size':size,'pc':pc,'access':access,'position':{'cck':cck}}})
        event(200,10);event(994,20,pc=10);event(992,22,pc=10)
        event(988,24,'read');event(992,100,'read');event(994,102,'read');event(202,110)
        self.assertEqual(observer.rows[0]['phases']['render'],82)
        event(200,120,v=2);event(994,130,pc=20)
        with self.assertRaisesRegex(ValueError,'return missing'):event(202,140,v=2)

    def test_identity_is_content_order_stable(self):
        self.assertEqual(identity({'a':1,'b':2}),identity({'b':2,'a':1}))
        self.assertNotEqual(identity({'a':1}),identity({'a':2}))

    def test_deltas_do_not_cross_machine_contract(self):
        old={'identity':'old','static':{'layout':{'executable_bytes':10}},'runtime':{'one':{'metrics':{'clock':1,'boundaries':'bus'},'provenance':{'target':'PAL','tools':{}}}}}
        current={'static':{'layout':{'executable_bytes':12}},'runtime':{'one':{'metrics':{'clock':2,'boundaries':'bus'},'provenance':{'target':'NTSC','tools':{}}}}}
        delta=metric_deltas(old,current)
        self.assertEqual(delta['static_bytes']['executable_bytes'],2)
        self.assertEqual(delta['runtime']['one']['state'],'incompatible or unmeasured')
