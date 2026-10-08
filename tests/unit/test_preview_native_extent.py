"""Synthetic receipt shapes only; these tests make no gameplay claim."""
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from acceptance_cases import cases
from acceptance_campaign import dependencies,required_extent
from preview_native_extent import CAPS


def receipt(ntsc=False):
    target=dict(video='NTSC' if ntsc else 'PAL',cpu='68000',chipset='OCS',chip_kib=512,slow_kib=0,fast_kib=0)
    video=dict(presentation_last_line=261 if ntsc else 311,simulation_interval_whole=11947 if ntsc else 11838,
        simulation_interval_fraction=13180 if ntsc else 14906)
    budget=(video['simulation_interval_whole']+video['simulation_interval_fraction']/65536)*5
    def distribution(samples,value):
        return dict(samples=samples,typical_median_cck=value,p95_cck=value,max_cck=value,
            budget_cck=budget,minimum_headroom_cck=budget-value)
    def job(name,x,generation):
        edited=bytearray(318);edited[2]=20;edited[3]=x
        return dict(case_id=name,passed=True,native_jsr_rts_preserved=True,
            continuous_state_path_output_equal=True,independent_continuation_policy_equal=True,
            live_history_output_preserved=True,edited_only_position_changed=True,
            seed=44257,selection=100,end=0,ordinal=65535 if name=='current-human-serve' else 1,
            prefix_samples=1,incoming_origin=64,action_boundary=120,coincident=False,
            bounds=dict(left=1,right=100,top=1,bottom=100),x=x,y=20,
            selected_state='00'*318,edited_state=edited.hex(),final_states=['00'*318]*2,
            paths=['00'*16]*2,path_counts=[2,2],classes=['no-contact','no-contact'],ordered_outputs=[[],[]],
            costs=dict(generation=generation,cache_hit=name=='warm-position-edit',
                resolver_operations=1 if name=='cold-incoming' else 0,worker_calls=1,
                worker_body_counts=[2],maximum_worker_operations=2,worker_elapsed_cck=10,
                maximum_worker_elapsed_cck=10,fields_to_result=1,seconds_to_result=.001))
    jobs=[job('current-human-serve',10,1),job('cold-incoming',10,2),job('warm-position-edit',11,3)]
    replacements=[dict(case_id='replacement-'+phase,passed=True,partial_phase=phase,
        partial_body_operations=1,old_generation=4+i*2,new_generation=5+i*2,
        old_position=[10,20],new_position=[11,20],replacement_resolver_operations=1,
        cold_replacement=True,edited_only_position_changed=True,old_result_rejected=True,
        canceled_result_rejected=True,selected_history_output_preserved=True) for i,phase in enumerate(('resolve','held'))]
    names=['game_history_freeze','game_history_seek',
        'game_preview_request','game_preview_step','game_preview_result','game_preview_result',
        'game_history_seek','game_preview_request','game_preview_step','game_preview_result',
        'game_preview_request','game_preview_step','game_preview_result',
        'game_preview_request','game_preview_step','game_preview_request','game_preview_step','game_preview_cancel',
        'game_preview_request','game_preview_step','game_preview_request','game_preview_step','game_preview_cancel',
        'game_history_resume_latest']
    rows=[]
    hz=3579545 if ntsc else 3546895
    for i,name in enumerate(names):
        begin=dict(cck=100*i,frame=0,seconds=100*i/hz,vpos=0,hpos=0)
        end=dict(begin,cck=100*i+10,seconds=(100*i+10)/hz,hpos=10)
        irq=int(name=='game_preview_step' and not any(r['irq'] for r in rows))
        rows.append(dict(name=name,begin=begin,end=end,bodies=2 if i in (3,8,11) else 4 if name=='game_preview_step' else 0,
            irq=irq,irq_acknowledgements=2*irq,elapsed_cck=10))
    for job,request,worker,result in zip(jobs,(2,7,10),(3,8,11),(5,9,12)):
        job['costs'].update(request_api_row_index=request,worker_api_row_indices=[worker],
            result_api_row_index=result,fields_to_result=0,
            seconds_to_result=rows[result]['end']['seconds']-rows[request]['begin']['seconds'])
    rules=[dict(pc=100+i*10,address=0xdff09c,bytes=2,operation='move',source='#$0010',
        destination='$dff09c',instruction='move.w #$0010,$dff09c') for i in range(2)]
    files={'amiga/main.s':'11'*32,'scripts/preview_native_fixture.s':'22'*32,
        'amiga/game/preview.s':'33'*32,'build/tests/preview-native/main.s':'44'*32,
        'build/tests/preview-native/fixture.compile.json':'55'*32,
        'build/amiga/interfaces/enhanced/baseline-rally.compile.json':'66'*32}
    observed=dict(CAPS,ordinary_operations=200,playing_dispatches=40,title_callbacks=2,
        paused_callbacks=30,video_fields=50,seconds=10,worker_calls_per_job=1,samples_per_path=2,raw_bytes=1024)
    stage=dict(passed=True,canonical_bytes=318,history_metadata_bytes=72,
        preview_storage_bytes=5550,preview_metadata_bytes=110,
        acquisition=dict(seed=44257,seed_policy='DEMO_RECORDING-selection-only',ordinary_operations=200,
            playing_dispatches=40,title_callbacks=2,completed_index_kind=2,incoming_origin=64,
            probe_origin=120,selected_cursor=100,ordinal=1,end=0),
        completed_jobs=jobs,replacement_cancel_cases=replacements,
        preservation={k:True for k in ('selected_canonical','history_metadata','frozen_store','live_backup',
            'caller_frame','input_globals','publication_irq_only','audio_cpu_configuration')},
        interrupts=dict(inside_worker_entries=1,inside_api_entries=1,entry_exit_ack_pairs=True,
            exact_pc_address_width_value_rules=rules,keyboard_irq_allowances=0),
        physical_inputs=dict(joystick_press_edges=1,joystick_release_edges=1,keyboard_presses=1,
            keyboard_releases=1,pause_resume_observed=True,fresh_input_callbacks=1),
        telemetry=dict(notifications=100,dropped_notifications=0,dropped_accesses=0,public_boundary_drain_checks=40),
        caps=dict(CAPS),observed_caps=observed,
        costs=dict(api_rows=rows,worker_distribution=distribution(7,10),callback_distribution=distribution(72,20),
            fresh_input_callback_distribution=distribution(1,30),minimum_callback_headroom_cck=budget-30,stack_bytes=300),
        resources=dict(fixture_chip_free_bytes=100000,fixture_loaded_bytes=258600,product_static_loaded_bytes=257828),
        compiled_identity=dict(loaded_hunks=[dict(hunk=0,start=4096,bytes=258600,expected_sha256='77'*32,
            actual_sha256='77'*32,matched=True)],normalized_shared_core=dict(matched=True,bytes=18020,
            relocations=257,sink_branches=14,sha256='9a457929bc223b843132bb53af7d604ed574441e32c4651eb69897aa0b48689d'),
            worker_bytes=dict(source_sha256='33'*32,loaded_sha256='88'*32,bytes=2048,
                loaded_start=8192,loaded_end=10240,fixture_executable_sha256='99'*32),
            overlay=dict(original_sources={'amiga/main.s':'11'*32},generated_sources={'build/tests/preview-native/main.s':'44'*32},
                insertion_anchor='        bsr     game_native_commands\n        tst.b   ui_paused\n',
                seed_policy='DEMO_RECORDING-selection-only',scope='Synthetic receipt shape'),
            fixture_manifest_sha256='55'*32,product_manifest_sha256='66'*32),continuous_actual_core_equal=True,
        outside_publication=dict(rules=[dict(pc=120,address=10000,bytes=1,operation='move',
            source='#1',destination='display_ready',instruction='move.b #1,display_ready')],
            writes=[dict(pc=120,address=10000,size=1,value=1,position=rows[0]['begin'])],count=1))
    stage['preservation'].update(publication_scope='worker-api-irq-only; outside-api-native-ui-attributed',
        input_scope='worker-api-only; native-physical-sampling-before-hook')
    return dict(passed=True,execution='actual-native-paused-preview',target=target,native_video=video,
        evidence=dict(target_role='legacy-validator-reference',actual_target=target,files=files,
            compiled_executables={'build/tests/preview-native/baseline-rally':'99'*32}),preview_native_validation=stage)


class NativePreviewExtent(unittest.TestCase):
    def case(self,ntsc=False):return next(c for c in cases() if c.id=='preview-native-'+('ntsc' if ntsc else 'pal'))

    def test_both_standards_require_their_actual_target(self):
        for ntsc in (False,True):
            self.assertTrue(required_extent(self.case(ntsc),receipt(ntsc)))
            self.assertFalse(required_extent(self.case(ntsc),receipt(not ntsc)))

    def test_partial_or_malformed_native_evidence_is_rejected(self):
        for path,value in ((('acquisition','playing_dispatches'),513),
                (('acquisition','ordinary_operations'),2050),(('acquisition','end'),True),
                (('preservation','live_backup'),False),(('preservation','audio_cpu_configuration'),False),
                (('interrupts','inside_worker_entries'),0),(('interrupts','keyboard_irq_allowances'),1),
                (('telemetry','dropped_accesses'),1),(('telemetry','public_boundary_drain_checks'),1),
                (('physical_inputs','keyboard_releases'),0),(('observed_caps','seconds'),float('nan')),
                (('observed_caps','raw_bytes'),CAPS['raw_bytes']+1),
                (('caps','worker_calls_per_job'),8192.0),(('completed_jobs',0,'ordinal'),1),
                (('completed_jobs',1,'costs','worker_body_counts'),[5]),
                (('completed_jobs',2,'costs','cache_hit'),False),
                (('completed_jobs',2,'costs','resolver_operations'),1),
                (('completed_jobs',2,'prefix_samples'),0),
                (('completed_jobs',2,'costs','worker_elapsed_cck'),11),
                (('completed_jobs',2,'costs','seconds_to_result'),1),
                (('completed_jobs',2,'costs','worker_api_row_indices'),[9]),
                (('completed_jobs',1,'final_states'),['00']*2),
                (('completed_jobs',1,'edited_state'),'01'*318),
                (('completed_jobs',1,'paths'),['00']*2),
                (('completed_jobs',1,'continuous_state_path_output_equal'),False),
                (('replacement_cancel_cases',0,'partial_phase'),'held'),
                (('replacement_cancel_cases',1,'new_generation'),6),
                (('replacement_cancel_cases',0,'old_result_rejected'),False),
                (('costs','minimum_callback_headroom_cck'),-1),
                (('costs','api_rows',0,'elapsed_cck'),11),
                (('costs','api_rows',3,'irq_acknowledgements'),1),
                (('costs','worker_distribution','samples'),1),
                (('compiled_identity','loaded_hunks',0,'matched'),False),
                (('compiled_identity','worker_bytes','source_sha256'),'00'*32),
                (('compiled_identity','worker_bytes','loaded_end'),10239),
                (('compiled_identity','normalized_shared_core','bytes'),18021),
                (('outside_publication','writes',0,'address'),10001),
                (('preservation','publication_scope'),'whole-frozen-interval-irq-only'),
                (('continuous_actual_core_equal',),False)):
            r=receipt();node=r['preview_native_validation']
            for key in path[:-1]:node=node[key]
            node[path[-1]]=value
            with self.subTest(path=path):self.assertFalse(required_extent(self.case(),r))

    def test_cross_job_prefix_and_self_consistent_counts_remain_bound(self):
        r=receipt();warm=r['preview_native_validation']['completed_jobs'][2]
        warm['paths']=['11'*8+'00'*8]*2
        self.assertFalse(required_extent(self.case(),r))
        r=receipt();warm=r['preview_native_validation']['completed_jobs'][2]
        warm['costs'].update(worker_body_counts=[1],maximum_worker_operations=1)
        self.assertFalse(required_extent(self.case(),r))

    def test_completed_intervals_cannot_omit_work_or_change_selection(self):
        r=receipt();stage=r['preview_native_validation']
        stage['costs']['api_rows'][4].update(name='game_preview_step',bodies=2)
        stage['costs']['worker_distribution']['samples']=8
        self.assertFalse(required_extent(self.case(),r))
        r=receipt()
        r['preview_native_validation']['costs']['api_rows'][4]['name']='game_preview_request'
        self.assertFalse(required_extent(self.case(),r))

    def test_native_fixture_assembly_changes_invalidate_dependencies(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'scripts').mkdir()
            (root/'scripts/run_preview_native.py').write_text('pass\n')
            fixture=root/'scripts/preview_native_fixture.s';fixture.write_text('rts\n')
            before=dependencies(self.case(),root)['files'][str(fixture)]
            fixture.write_text('nop\nrts\n')
            after=dependencies(self.case(),root)['files'][str(fixture)]
            self.assertNotEqual(before,after)


if __name__=='__main__':unittest.main()
