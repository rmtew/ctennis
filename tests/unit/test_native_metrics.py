"""Corruption, missing-evidence and phase-boundary checks for native metrics."""
import copy
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from native_size import executable_attribution
from native_release import strip_symbols
from native_hunk import hunk_layout, loaded_hunks
from native_metrics_observation import distribution, MetricsObserver
from native_metrics import identity, metric_deltas, cold_timing, measurement_status, report_identity, cold_loading_issues, generate, main


class MetricsTests(unittest.TestCase):
    def test_release_only_symbols_removed_and_relocations_preserved(self):
        words=[1011,0,1,0,0,0x40000001,1001,1,4,1004,1,0,0,0,
               1008,1,0x78000000,0,0,1010]
        original=struct.pack('>'+len(words)*'I',*words)
        stripped,removed=strip_symbols(original)
        self.assertEqual(removed,20)
        self.assertEqual(stripped,struct.pack('>15I',*(words[:14]+[1010])))
        self.assertEqual(strip_symbols(stripped),(stripped,0))
        with tempfile.TemporaryDirectory() as directory:
            for name,blob in [('dev',original),('release',stripped)]:
                exe=Path(directory)/name;exe.write_bytes(blob)
                for base in (0x1000,0x25000):
                    result=loaded_hunks(exe,[{'start':base}],lambda addr,size:struct.pack('>I',base+4))
                    self.assertTrue(result[0]['matched'])
                self.assertEqual(hunk_layout(exe)['hunks'][0]['memory'],'chip')
        with self.assertRaisesRegex(ValueError,'Truncated'):strip_symbols(original[:-1])

    def test_bss_attribution_is_ram_only_and_rejects_bad_extent(self):
        with tempfile.TemporaryDirectory() as directory:
            exe=Path(directory)/'game';listing=Path(directory)/'game.lst'
            words=[1011,0,1,0,0,0x40000002,1003,2,1010]
            exe.write_bytes(struct.pack('>'+len(words)*'I',*words))
            listing.write_text('Source: "amiga/square_score_storage.i"\n00:00000000 00 3: score_bank_point_a_0_p2: ds.b 8\n')
            result=executable_attribution(exe,listing,{'files':{}})
            self.assertEqual(result['bss_ram_bytes'],8)
            self.assertEqual(result['bss_instances'][0]['file_bytes'],0)
            self.assertEqual(result['bss_instances'][0]['category'],'hud_strips_and_tiles')
            self.assertEqual(result['accounted_file_bytes'],len(exe.read_bytes()))
            listing.write_text(listing.read_text().replace('ds.b 8','ds.b 4'))
            with self.assertRaisesRegex(ValueError,'BSS declaration'):executable_attribution(exe,listing,{'files':{}})

    def test_size_attribution_reconciles_instructions_reserves_and_nop_padding(self):
        with tempfile.TemporaryDirectory() as directory:
            exe=Path(directory)/'game'; listing=Path(directory)/'game.lst'
            words=[1011,0,1,0,0,2,1001,2,0x4e750000,0x00004e71,1010]
            exe.write_bytes(struct.pack('>'+len(words)*'I',*words))
            listing.write_text('Source: "amiga/main.s"\n00:00000000 4E75 1: rts\n00:00000002 0000 2: game_stack_bottom: dcb.b 4,0\n')
            result=executable_attribution(exe,listing,{'files':{}})
            categories={r['category']:r['bytes'] for r in result['categories']}
            self.assertEqual(result['accounted_file_bytes'],44)
            self.assertEqual(categories['cpu_instructions'],2)
            self.assertEqual(categories['reserved_native_stack'],4)
            self.assertEqual(categories['hunk_payload_alignment_padding'],2)
            original=listing.read_text()
            listing.write_text(original.replace('4E75','4E71'))
            with self.assertRaisesRegex(ValueError,'Listing bytes differ'):executable_attribution(exe,listing,{'files':{}})
            listing.write_text(original)
            listing.write_text(listing.read_text().replace('dcb.b 4,0','dcb.b 1,0'))
            with self.assertRaisesRegex(ValueError,'exceeds'):executable_attribution(exe,listing,{'files':{}})
            listing.write_text('Source: "amiga/main.s"\n00:00000000 4E75 1: rts\n00:00000004 0000 2: dc.w 0\n')
            with self.assertRaisesRegex(ValueError,'gap'):executable_attribution(exe,listing,{'files':{}})

    def test_symbol_and_relocation_file_bytes_reconcile_without_loading_symbols(self):
        words=[1011,0,1,0,0,1,1001,1,0,1004,1,0,0,0,
               1008,1,0x78000000,0,0,1010]
        with tempfile.TemporaryDirectory() as directory:
            exe=Path(directory)/'game';exe.write_bytes(struct.pack('>'+len(words)*'I',*words))
            result=hunk_layout(exe);fmt=result['file_format']
            self.assertEqual(result['code_bytes'],4)
            self.assertEqual((fmt['symbol_name_bytes'],fmt['symbol_name_padding_bytes'],fmt['symbol_framing_bytes']),(1,3,16))
            self.assertEqual((fmt['relocation_bytes'],fmt['relocations']),(20,1))
            self.assertEqual(sum(fmt[k] for k in ('header_table_bytes','hunk_headers_and_end_bytes','symbol_bytes','relocation_bytes'))+4,len(exe.read_bytes()))
            words[16]=0x78000100;exe.write_bytes(struct.pack('>'+len(words)*'I',*words))
            with self.assertRaisesRegex(ValueError,'padding'):hunk_layout(exe)

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
               'game_lifecycle','game_mode','game_flight','ui_paused','ui_demo','ui_page','game_title_display')
        symbols=dict(zip(names,(0,100,1000,200,202,204,206,208,209,210,211,212,213)))
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

    def test_loading_overlap_is_preserved_and_boot_requires_display_and_input(self):
        capture={'cold_timing_points':{'reset':{'cck':0},'loadseg_complete':{'cck':100}},
                 'entry_stop':{'cck':100},'checkpoints':{'first_selection':{'position':{'cck':160}}}}
        report={'resource_metrics':{'assets_ready_and_controls_initialized':{'cck':120},
                                   'first_complete_title_frame':{'cck':180}},'adf_sha256':'disk'}
        result=cold_timing(capture,report)
        self.assertEqual(result['total_reset_to_input_cck'],160)
        self.assertEqual(result['total_reset_to_display_and_input_cck'],180)
        self.assertEqual(result['stages'][-1]['from_previous_listed_milestone_cck'],-20)
        self.assertEqual(result['measured_intervals_cck']['entry_to_assets_controls_ready'],20)
        self.assertIsNone(result['stages'][1]['cck'])
        self.assertIsNone(result['disk_reads'])

    @patch.dict("os.environ", {}, clear=True)
    def test_only_reporter_change_can_reuse_and_later_failures_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'receipt.json'
            report={'passed':True,'first_difference':None,'subject':'maintained-native','interface_flavor':'enhanced',
                    'evidence':{'state':'complete','subject':'maintained-native','interface_flavor':'enhanced'}}
            path.write_text(json.dumps(report))
            with patch('native_metrics.status',return_value={'status':'stale','changed_dependencies':['scripts/native_metrics.py']}):
                self.assertEqual(measurement_status(path)['freshness'],'reused')
                report.pop('subject');path.write_text(json.dumps(report))
                self.assertEqual(measurement_status(path)['freshness'],'reused')
                report['subject']='wrong';path.write_text(json.dumps(report))
                self.assertEqual(measurement_status(path)['status'],'stale')
                report['subject']='maintained-native'
                report['passed']=False;path.write_text(json.dumps(report))
                self.assertEqual(measurement_status(path)['status'],'stale')
            with patch('native_metrics.status',return_value={'status':'failed','reason':'latest failed'}):
                self.assertEqual(measurement_status(path)['status'],'failed')
            with patch('native_metrics.status',return_value={'status':'stale','changed_dependencies':['scripts/native_metrics_observation.py']}):
                self.assertEqual(measurement_status(path)['status'],'stale')

    def test_report_identity_rejects_changed_numbers_but_ignores_receipt_timestamp_identity(self):
        report={'product_identity':'product','static':{'layout':{'executable_bytes':10},'build_receipt_sha256':'old'},
                'measurement_inputs':{'source':'hash'},'report_generator_sha256':'writer',
                'runtime':{'one':{'metrics':{'max_cck':100},'memory':{'free':10},'receipt_sha256':'old'}}}
        original=report_identity(report)
        report['runtime']['one']['receipt_sha256']='new';report['static']['build_receipt_sha256']='new'
        self.assertEqual(report_identity(report),original)
        report['runtime']['one']['memory']['free']=11
        self.assertNotEqual(report_identity(report),original)

    def title_observer(self):
        names=('simulation_update','prepare_title_display','game_stack_top',
               'simulation_started_updates','simulation_updates','simulation_timer_origin',
               'game_lifecycle','game_mode','game_flight','ui_paused','ui_demo','ui_page','game_title_display')
        symbols=dict(zip(names,(0,100,1000,200,202,204,206,208,209,210,211,212,213)))
        listing='\n'.join(f'00:{pc:08X} 6100 1: bsr {target}' for pc,target in
                          ((10,'game_render_sprites'),(20,'game_tick_dispatch'),(30,'game_render_sprites'),(40,'game_tick_dispatch')))
        observer=MetricsObserver(0,symbols,listing,title_copper=0x4000)
        def write(a,v,frame=10,size=2):
            observer.observe({'method':'event.mmio','params':{'addr':a,'value':v,'size':size,'pc':0,
                'access':'write','position':{'frame':frame,'cck':frame*100}}})
        def frame(n):
            observer.observe({'method':'event.frame','params':{'position':{'frame':n,'cck':n*100}}})
        write(206,2);write(213,255,size=1)
        return observer,write,frame

    def test_complete_title_requires_loaded_pointer_and_continuous_selection(self):
        for fault in ('logical-switch','copper-switch','help-switch'):
            with self.subTest(fault=fault):
                observer,write,frame=self.title_observer()
                write(0xdff080,0x4000,size=4);write(0xdff088,0)
                frame(11);self.assertIsNone(observer.first_complete_title_frame)
                if fault=='logical-switch':write(213,0,11,size=1)
                elif fault=='copper-switch':write(0xdff080,0x5000,11,size=4)
                else:write(212,1,11,size=1)
                frame(12);frame(50)
                self.assertIsNone(observer.first_complete_title_frame)
                # Returning to title needs a new publication and a new full window.
                write(213,255,60,size=1);write(212,0,60,size=1)
                write(0xdff080,0x4000,60,size=4)
                frame(60);self.assertIsNone(observer.first_complete_title_frame)
                write(0xdff088,0,60);frame(61)
                self.assertIsNone(observer.first_complete_title_frame)
                frame(62)
                self.assertEqual(observer.first_complete_title_frame['frame'],62)
                self.assertEqual(observer.first_complete_title_frame['title_selected_since']['frame'],60)
                self.assertEqual(observer.first_complete_title_frame['title_copper'],0x4000)

    def test_wrong_or_partial_copper_pointer_cannot_publish_a_title_milestone(self):
        for pointer,size in ((0x5000,4),(0,2)):
            observer,write,frame=self.title_observer()
            write(0xdff080,pointer,size=size);write(0xdff088,0);frame(12)
            self.assertIsNone(observer.first_title_publication)
            self.assertIsNone(observer.first_complete_title_frame)

    def complete_loading(self):
        stages=[{'stage':name,'cck':cck} for name,cck in
                [('reset',0),('boot_script_begins',None),('loadseg_begin',None),
                 ('loadseg_complete',100),('executable_entry',110),('assets_ready',120),
                 ('first_complete_title_frame',180),('input_responsive',160)]]
        return {'stages':stages,'total_reset_to_display_and_input_cck':180,
                'title_frame_evidence':{'cck':180,'frame':3,'title_copper':0x4000,
                                        'title_selected_since':{'cck':115,'frame':1}}}

    def test_returned_title_cannot_certify_initial_boot(self):
        loading=self.complete_loading()
        loading['title_frame_evidence']['title_selected_since']['cck']=170
        self.assertTrue(any('returned title' in issue for issue in cold_loading_issues(loading)))

    def test_generate_rejects_missing_loading_milestones_despite_passing_profiles(self):
        from native_metrics_observation import PROFILES
        template={'classification':{'status':'passed'},'metrics':{'profiles':{p:{'callbacks':1} for p in PROFILES}},
                  'provenance':{'dependencies':{},'verified_dependencies':{},'verified_input_fingerprints':{}}}
        static={'executable_sha256':'exe','product_inputs':{},'release':{'executable_sha256':'release'}}
        for missing in (None,'reset','loadseg_complete','executable_entry','assets_ready',
                        'first_complete_title_frame','input_responsive','title-proof'):
            with self.subTest(missing=missing):
                loading=self.complete_loading()
                if missing=='title-proof':loading.pop('title_frame_evidence')
                elif missing:
                    next(s for s in loading['stages'] if s['stage']==missing)['cck']=None
                def case(name,*args):
                    value=copy.deepcopy(template)
                    if name=='cold-one':value['cold_loading']=copy.deepcopy(loading)
                    return value
                with tempfile.TemporaryDirectory() as directory,patch('native_metrics.ROOT',Path(directory)),patch('native_metrics.static_metrics',return_value=static),patch('native_metrics.read_case',side_effect=case),patch('native_metrics.subprocess.run') as accepted:
                    accepted.return_value.returncode=1
                    report=generate()
                self.assertEqual(report['state'],'complete' if missing is None else 'incomplete')
                self.assertEqual(bool(report['cold_loading_issues']),missing is not None)
        invalid=self.complete_loading();invalid['stages'][-1]['cck']=True
        self.assertTrue(cold_loading_issues(invalid))

    def test_check_rejects_old_writer_before_reusing_an_accepted_report(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);writer=root/'scripts/native_metrics.py'
            writer.parent.mkdir();writer.write_text('current writer')
            accepted=root/'current.json';accepted.write_text(json.dumps({'state':'complete','report_generator_sha256':'old'}))
            with patch('native_metrics.ROOT',root),patch('native_metrics.TRACKED',accepted),patch.object(sys,'argv',['native_metrics.py','--check']),patch('native_metrics.static_metrics') as static:
                with self.assertRaisesRegex(ValueError,'writer changed'):main()
                static.assert_not_called()
            output=json.loads((root/'build/metrics/current.json').read_text())
            self.assertEqual(output['state'],'failed')
            self.assertIn('writer changed',output['error'])

    def test_celebration_profile_uses_observed_pose_and_pause_takes_precedence(self):
        observer,write,frame=self.title_observer()
        observer.values['game_lifecycle']=6
        observer.values['game_celebration_pose']=0
        self.assertEqual(observer.profile(),'match-end')
        observer.values['game_celebration_pose']=255
        self.assertEqual(observer.profile(),'celebration')
        observer.values['ui_paused']=255
        self.assertEqual(observer.profile(),'pause')

    def test_runtime_deltas_require_matching_observer_definition(self):
        old={'identity':'old','static':{'layout':{'executable_bytes':10}},'measurement_inputs':{'scripts/native_metrics_observation.py':'old'},'runtime':{'case':{'metrics':{'clock':1,'boundaries':'bus'},'provenance':{'target':'PAL','startup':'cold','tools':{}}}}}
        current={'static':{'layout':{'executable_bytes':12}},'measurement_inputs':{'scripts/native_metrics_observation.py':'new'},'runtime':copy.deepcopy(old['runtime'])}
        self.assertEqual(metric_deltas(old,current)['runtime']['case']['state'],'incompatible or unmeasured')
