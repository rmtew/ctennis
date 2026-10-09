"""Synthetic receipt shapes only; these tests make no gameplay claim."""
import sys
import hashlib
import copy
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from acceptance_cases import cases
from acceptance_campaign import dependencies,required_extent
from preview_native_extent import CAPS,BYTE_CAP_SCOPE,CPU9_RECEIPTS,BODY_ARITIES,SEEK_CPU_RECEIPTS
CPU9_SHA="b5"*32
SEEK_CPU_SHA="1a"*32


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
        prefix=0
        expected=bytes(8)
        return dict(case_id=name,passed=True,native_jsr_rts_preserved=True,
            continuous_state_path_output_equal=True,independent_continuation_policy_equal=True,
            live_history_output_preserved=True,edited_only_position_changed=True,
            seed=44257,selection=100,end=0,ordinal=65535 if name=='current-human-serve' else 1,
            prefix_samples=prefix,incoming_origin=64,action_boundary=120,coincident=False,
            classification_scope='native-preview-outcome-labels; endpoint-qualification-current-cpu',
            incoming_prefix_validation=dict(passed=True,source='actual-native-post-dispatch-incoming-state',
                operation_cursors=[] if name=='current-human-serve' else [64],expected_samples=1,incoming_state='00'*318,
                expected_bytes=expected.hex(),expected_sha256=hashlib.sha256(expected).hexdigest()),
            bounds=dict(left=1,right=100,top=1,bottom=100),x=x,y=20,
            selected_state='00'*318,edited_state=edited.hex(),final_states=['00'*318]*2,
            paths=['00'*16]*2,path_counts=[2,2],classes=['no-contact','no-contact'],ordered_outputs=[[],[]],
            costs=dict(generation=generation,cache_hit=name=='warm-position-edit',
                resolver_operations=1 if name=='cold-incoming' else 0,worker_calls=1,
                worker_body_counts=[2],maximum_worker_operations=2,worker_elapsed_cck=10,
                maximum_worker_elapsed_cck=10,fields_to_result=1,seconds_to_result=.001))
    jobs=[job('current-human-serve',10,1),job('cold-incoming',10,2),job('warm-position-edit',11,3)]
    jobs[1]['costs'].update(worker_body_counts=[3],maximum_worker_operations=3)
    replacements=[dict(case_id='replacement-'+phase,passed=True,partial_phase=phase,
        partial_body_operations=1,old_generation=4+i*2,new_generation=5+i*2,
        old_position=[10,20],new_position=[11,20],replacement_resolver_operations=1 if phase=='resolve' else 0,
        cold_replacement=phase=='resolve',cache_replacement=phase=='held',edited_only_position_changed=True,old_result_rejected=True,
        canceled_result_rejected=True,selected_history_output_preserved=True) for i,phase in enumerate(('resolve','held'))]
    names=['game_history_freeze','game_history_freeze',
        'game_preview_request','game_preview_step','game_preview_result','game_preview_result',
        'game_history_freeze','game_preview_request','game_preview_step','game_preview_result',
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
        rows.append(dict(name=name,begin=begin,end=end,bodies=3 if i==8 else 2 if i in (3,11) else 4 if name=='game_preview_step' else 0,
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
        'build/amiga/interfaces/enhanced/baseline-rally.compile.json':'66'*32,
        'build/tests/preview-native/rpc.jsonl.gz':'aa'*32,
        'build/tests/preview-native/events.jsonl.gz':'ab'*32,
        'build/tests/preview-cpu/report.json':CPU9_SHA}
    files.update({path:CPU9_SHA for path in CPU9_RECEIPTS})
    observed=dict(CAPS,ordinary_operations=200,playing_dispatches=40,title_callbacks=2,
        paused_callbacks=30,video_fields=50,seconds=10,worker_calls_per_job=1,samples_per_path=2,raw_bytes=1024)
    stage=dict(passed=True,canonical_bytes=318,history_metadata_bytes=72,
        preview_storage_bytes=9986,preview_metadata_bytes=116,seek_storage_bytes=734,
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
        resources=dict(fixture_chip_free_bytes=100000,fixture_loaded_bytes=258600,product_static_loaded_bytes=319520),
        compiled_identity=dict(product_layout=dict(loaded_payload_bytes=319520,hunks=[dict(bytes=319520)],executable_sha256='66'*32),loaded_hunks=[dict(hunk=0,start=4096,bytes=258600,expected_sha256='77'*32,
            actual_sha256='77'*32,matched=True)],normalized_shared_core=dict(matched=True,bytes=17606,
            relocations=7,sink_branches=14,sha256='99c543c170c036137be81d07ebd30b522ef3abdff04bd7b1af38f00047bb99d5'),
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
    stage['physical_inputs'].update(observed_edges=[
        dict(name=name,index=0,old=old,new=new,pressed_bits=new&~old,released_bits=old&~new,
            frozen=True,position=rows[0]['begin'])
        for name in ('ui_joystick_bits','game_keyboard_matrix') for old,new in ((0,1),(1,0))],
        joystick_pressed_observations=[dict(index=0,value=1,expected=1)])
    stage.update(byte_cap_scope=BYTE_CAP_SCOPE,
        rpc_transcript=dict(encoding='gzip-jsonl',path='build/tests/preview-native/rpc.jsonl.gz',
            sha256='aa'*32,compressed_bytes=100,uncompressed_bytes=200,calls=2,records=4),
        inherited_endpoint_validation=dict(cpu_receipt_sha256=CPU9_SHA,
            scope='current-CPU-independent-endpoints; native-labels-only'))
    frames=[];body_pc=12000;stack_top=24000
    for api_index,row in enumerate(rows):
        for n in range(row['bodies']):
            start=dict(row['begin'],cck=row['begin']['cck']+1+n*2)
            end=dict(start,cck=start['cck']+1)
            frame=dict(api_row_index=api_index,entry_index=len(frames),operation='game_core_sample_pads',arity=2,
                arguments=[0,0],before='00'*318,after='00'*318,state='00'*318,
                entry_pc=body_pc+8,entry_sp=stack_top-100,return_pc=body_pc+100,
                exit_pc=body_pc+100,exit_sp=stack_top-96,start=start,end=end,elapsed_cck=1,
                depth=1,ownership=dict(active=2,status=3,variant=n%2,seek_active=0,seek_status=0,seek_generation=0,seek_cursor=0),events=[],
                entry_registers=dict(d=[0]*8,a=[0]*7+[stack_top-100],pc=body_pc+8,sr=0x2000,stopped=False))
            frames.append(frame)
    for job,api_index in zip(jobs,(3,8,11)):
        selected=[f for f in frames if f['api_row_index']==api_index]
        if api_index==8:
            selected[0]['ownership'].update(active=1,status=1)
            selected=selected[1:]
        for variant,frame in enumerate(selected):
            frame['ownership']['variant']=variant;frame['before']=job['edited_state']
        if api_index==11:
            frame=selected[-1];frame.update(operation='game_ball_tick',arity=0,arguments=[],entry_pc=body_pc+36)
            frame['entry_registers']['pc']=body_pc+36
    stage['body_observation']=dict(protocol='read-only-emitted-body-pc-and-matched-stack-return',
        ball_phase_scope='standalone-outgoing-only; dispatched-ball-covered-by-complete-logical-body',
        loaded_body_map=[dict(pc=body_pc+4*i,operation=name,arity=arity,label=name if name=='game_ball_tick' else name+'_body',entry_bytes='4e714e71')
            for i,(name,arity) in enumerate(BODY_ARITIES.items())],frames=frames,semantic_intents=[],
        actual_body_entries=len(frames),outer_logical_calls=len(frames),internal_stops=2*len(frames),
        entry_return_observations=2*len(frames),unpaired_frames=0,maximum_nesting=9,maximum_entries_per_api=8192,
        stack_bottom=stack_top-4096,stack_top=stack_top)
    stage['event_transcript']=dict(encoding='gzip-jsonl',path='build/tests/preview-native/events.jsonl.gz',
        sha256='ab'*32,compressed_bytes=100,uncompressed_bytes=200,notifications=100)
    add_seek_shape(stage,files,ntsc)
    return dict(passed=True,execution='actual-native-paused-preview',target=target,native_video=video,
        evidence=dict(target_role='legacy-validator-reference',actual_target=target,files=files,
            compiled_executables={'build/tests/preview-native/baseline-rally':'99'*32,'product':'66'*32}),preview_native_validation=stage)


def add_seek_shape(stage,files,ntsc):
    """Synthetic control/readback structure, without a gameplay model."""
    files.update({path:SEEK_CPU_SHA for path in SEEK_CPU_RECEIPTS})
    stage['compiled_identity']['seek_storage']=dict(loaded_start=25000,loaded_end=25734,bytes=734,fixture_executable_sha256='99'*32)
    stage['inherited_endpoint_validation'].update(current_ownership_cpu_receipt_sha256=SEEK_CPU_SHA,
        worker_source_closure=dict(passed=True,current_source_sha256='33'*32,
            preview_cpu_run_id='12'*16,scope='Synthetic exact current source closure shape'))
    rows=stage['costs']['api_rows'];block=stage['body_observation'];frames=block['frames'];proof=[]
    selected='00'*318;metadata=bytearray(72);metadata[:4]=bytes.fromhex("00030000");metadata[4]=2;metadata[34:42]=(835).to_bytes(8,'big');metadata=metadata.hex()
    def working(cursor):
        state=bytearray(318);state[100:108]=cursor.to_bytes(8,'big');return state.hex()
    cursor=512;hz=3579545 if ntsc else 3546895
    def call(name,generation,requested=None,commit=False):
        nonlocal cursor
        index=len(rows);start=dict(cck=100*index,frame=0,seconds=100*index/hz,vpos=0,hpos=0)
        end=dict(start,cck=start['cck']+10,seconds=(start['cck']+10)/hz,hpos=10)
        if name=='game_history_seek_begin':cursor=512
        previous=working(cursor);bodies=int(requested==1)
        if bodies:cursor+=1
        rows.append(dict(name=name,begin=start,end=end,bodies=bodies,irq=0,irq_acknowledgements=0,elapsed_cck=10))
        if bodies:
            template=copy.deepcopy(frames[0]);template.update(api_row_index=index,entry_index=len(frames),
                before=previous,after=working(cursor),state=working(cursor),start=dict(start,cck=start['cck']+1),
                end=dict(end,cck=start['cck']+2),elapsed_cck=1,events=[],
                ownership=dict(active=0,status=7,variant=0,seek_active=1,seek_status=1,seek_generation=generation,seek_cursor=cursor-1))
            frames.append(template)
        if name.startswith('game_history_seek_'):
            final_meta=bytearray.fromhex(metadata)
            if commit:final_meta[34:42]=(569).to_bytes(8,'big')
            proof.append(dict(api_row_index=index,name=name,generation=generation,
                admission=None if requested is None else dict(current=1000,last=1000,phase=0,interval=11947 if ntsc else 11838,
                    remaining=11947 if ntsc else 11838,reserve=10000,admitted=requested,requested_work=requested),
                body_operations=bodies,logical_body_operations=bodies,working_cursor=cursor,
                working_state=working(cursor),reference_working_state=working(cursor),
                public_state=working(cursor) if commit else selected,public_metadata=final_meta.hex(),
                selected_state=selected,selected_metadata=metadata,events=[],reference_events=[],
                actual_core_equal=True,frozen_store_preserved=True))
        return index
    def finish(generation):return [call('game_history_seek_step',generation,1) for _ in range(57)]
    cb=call('game_history_seek_begin',0);zero=call('game_history_seek_step',1,0)
    reject_result=call('game_preview_result',4);reject_request=call('game_preview_request',4)
    canceled_steps=finish(1);cancel=call('game_history_seek_cancel',1);oldcommit=call('game_history_seek_commit',1)
    sb=call('game_history_seek_begin',2);superseded_steps=finish(3)
    begin=call('game_history_seek_begin',3);stale=call('game_history_seek_commit',3);steps=finish(4);commit=call('game_history_seek_commit',4,commit=True)
    finalmeta=bytearray.fromhex(metadata);finalmeta[34:42]=(569).to_bytes(8,'big')
    job=dict(target=569,checkpoint=512,generation=4,selected_position=835,selected_state=selected,selected_metadata=metadata,
        initial_begin_api_row_index=cb,admission_zero_api_row_index=zero,admission_zero_identity_preserved=True,
        canceled_commit_preserved=True,superseded_commit_preserved=True,
        canceled_job=dict(generation=1,begin_api_row_index=cb,step_api_row_indices=canceled_steps,
            cancel_api_row_index=cancel,canceled_commit_api_row_index=oldcommit,ready_before_cancel=True),
        superseded_job=dict(generation=3,begin_api_row_index=sb,step_api_row_indices=superseded_steps,
            superseding_begin_api_row_index=begin,stale_commit_api_row_index=stale,ready_before_supersession=True),
        preview_transition=dict(before=dict(generation=3,status=2,cache_valid=1),after=dict(generation=4,status=7,cache_valid=0),
            retired=True,result_rejection_api_row_index=reject_result,request_rejection_api_row_index=reject_request),
        begin_api_row_index=begin,step_api_row_indices=steps,commit_api_row_index=commit,
        final_state=working(569),final_metadata=finalmeta.hex(),final_position=569)
    stage['seek_validation']=dict(passed=True,cpu_receipt_sha256=SEEK_CPU_SHA,rows=proof,jobs=[job],
        one_body_per_slice=True,selected_pending_preserved=True,actual_guest_timer_admission=True,
        reserve_eclock_ticks=10000,reserve_scope='Initial estimate; finite measured callbacks remain required.')
    stage['telemetry']['public_boundary_drain_checks']=len(rows)+1
    stage['observed_caps']['paused_callbacks']=len(rows)+1
    added=171
    for key in ('actual_body_entries','outer_logical_calls'):block[key]+=added
    for key in ('internal_stops','entry_return_observations'):block[key]+=2*added



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
                (('physical_inputs','observed_edges'),[]),
                (('physical_inputs','observed_edges',0,'frozen'),False),
                (('physical_inputs','observed_edges',0,'pressed_bits'),0),
                (('physical_inputs','joystick_pressed_observations',0,'expected'),0),
                (('byte_cap_scope',),'all-uncompressed-bytes'),
                (('rpc_transcript','records'),3),(('rpc_transcript','sha256'),'bb'*32),
                (('rpc_transcript','compressed_bytes'),1025),
                (('event_transcript','notifications'),99),(('event_transcript','sha256'),'bb'*32),
                (('event_transcript','uncompressed_bytes'),99),
                (('body_observation','frames'),[]),(('body_observation','actual_body_entries'),0),
                (('body_observation','frames',0,'exit_sp'),23900),
                (('body_observation','frames',0,'after'),'00'),
                (('body_observation','frames',0,'arguments'),[1,0]),
                (('body_observation','frames',0,'entry_registers','sr'),0x2700),
                (('body_observation','frames',0,'depth'),2),
                (('body_observation','frames',0,'ownership','status'),8),
                (('body_observation','frames',0,'elapsed_cck'),2),
                (('body_observation','internal_stops'),1),
                (('body_observation','unpaired_frames'),1),
                (('inherited_endpoint_validation','cpu_receipt_sha256'),'00'*32),
                (('observed_caps','raw_bytes'),CAPS['raw_bytes']+1),
                (('caps','worker_calls_per_job'),8192.0),(('completed_jobs',0,'ordinal'),1),
                (('completed_jobs',1,'costs','worker_body_counts'),[5]),
                (('completed_jobs',2,'costs','cache_hit'),False),
                (('completed_jobs',2,'costs','resolver_operations'),1),
                (('completed_jobs',2,'prefix_samples'),1),
                (('completed_jobs',2,'costs','worker_elapsed_cck'),11),
                (('completed_jobs',2,'costs','seconds_to_result'),1),
                (('completed_jobs',2,'costs','worker_api_row_indices'),[9]),
                (('completed_jobs',1,'final_states'),['00']*2),
                (('completed_jobs',1,'edited_state'),'01'*318),
                (('completed_jobs',1,'paths'),['00']*2),
                (('completed_jobs',1,'incoming_prefix_validation','source'),'preview-result'),
                (('completed_jobs',1,'incoming_prefix_validation','operation_cursors'),[100]),
                (('completed_jobs',1,'incoming_prefix_validation','expected_sha256'),'00'*32),
                (('completed_jobs',1,'incoming_prefix_validation','expected_bytes'),'11'*8),
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

    def test_seek_timer_identity_retirement_and_provenance_fail_closed(self):
        for path,value in ((('rows',1,'admission','admitted'),1),
                (('rows',1,'admission','requested_work'),True),
                (('rows',1,'admission','remaining'),11839),
                (('rows',1,'admission','interval'),0xffffffff),
                (('rows',1,'admission','reserve'),9999),
                (('rows',1,'logical_body_operations'),1),
                (('rows',1,'public_state'),'11'*318),
                (('rows',1,'public_metadata'),'00'*72),
                (('rows',1,'working_state'),'11'*318),
                (('jobs',0,'target'),570),(('jobs',0,'checkpoint'),511),
                (('jobs',0,'selected_position'),834),
                (('jobs',0,'canceled_commit_preserved'),False),
                (('jobs',0,'superseded_commit_preserved'),False),
                (('jobs',0,'canceled_job','ready_before_cancel'),False),
                (('jobs',0,'superseded_job','ready_before_supersession'),False),
                (('jobs',0,'preview_transition','after','status'),0),
                (('jobs',0,'preview_transition','after','cache_valid'),1),
                (('jobs',0,'preview_transition','after','generation'),3),
                (('jobs',0,'final_metadata'),'00'*72),
                (('rows',3,'generation'),2),
                (('reserve_scope',),'Measured universal bound')):
            r=receipt();node=r['preview_native_validation']['seek_validation']
            for key in path[:-1]:node=node[key]
            node[path[-1]]=value
            with self.subTest(path=path):self.assertFalse(required_extent(self.case(),r))
        for offset,value in ((4,1),(71,1)):
            r=receipt();node=r['preview_native_validation']['seek_validation']['rows'][1]
            metadata=bytearray.fromhex(node['selected_metadata']);metadata[offset]=value
            node['selected_metadata']=node['public_metadata']=metadata.hex()
            self.assertFalse(required_extent(self.case(),r))
        for path in SEEK_CPU_RECEIPTS:
            r=receipt();r['evidence']['files'].pop(path)
            self.assertFalse(required_extent(self.case(),r))
        for key,value in (('current_source_sha256','00'*32),('preview_cpu_run_id','not-a-run')):
            r=receipt();r['preview_native_validation']['inherited_endpoint_validation']['worker_source_closure'][key]=value
            self.assertFalse(required_extent(self.case(),r))
        r=receipt();r['preview_native_validation']['compiled_identity']['seek_storage']['bytes']=733
        self.assertFalse(required_extent(self.case(),r))
        r=receipt();r['preview_native_validation']['seek_validation']['rows'].pop(1)
        self.assertFalse(required_extent(self.case(),r))
        r=receipt();frame=next(f for f in r['preview_native_validation']['body_observation']['frames'] if f['ownership']['seek_active'])
        frame['ownership']['active']=1
        self.assertFalse(required_extent(self.case(),r))

    def test_stable_outside_publication_requires_complete_guarded_zero(self):
        r=receipt();outside=r['preview_native_validation']['outside_publication']
        outside.update(writes=[],count=0)
        self.assertTrue(required_extent(self.case(),r))
        for key,value in (('count',True),('count',-1),('count',1),('rules',[])):
            candidate=copy.deepcopy(r);candidate['preview_native_validation']['outside_publication'][key]=value
            with self.subTest(key=key,value=value):self.assertFalse(required_extent(self.case(),candidate))
        candidate=copy.deepcopy(r);candidate['preview_native_validation']['outside_publication']['writes']=[dict(pc=999,address=10000,size=1,value=1,position=r['preview_native_validation']['costs']['api_rows'][0]['begin'])]
        candidate['preview_native_validation']['outside_publication']['count']=1
        self.assertFalse(required_extent(self.case(),candidate))
        candidate=copy.deepcopy(r);candidate['preview_native_validation']['telemetry']['dropped_notifications']=1
        self.assertFalse(required_extent(self.case(),candidate))

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

    def test_missing_outgoing_phase_and_product_layout_are_rejected(self):
        for change in ('phase','label','layout','scope','source'):
            r=receipt();stage=r['preview_native_validation']
            if change=='phase':
                for frame in stage['body_observation']['frames']:
                    if frame['operation']=='game_ball_tick':
                        frame.update(operation='game_core_sample_pads',arity=2,arguments=[0,0],entry_pc=12008)
                        frame['entry_registers']['pc']=12008
            if change=='label':stage['body_observation']['loaded_body_map'][-1]['label']='game_ball_tick_body'
            if change=='layout':stage['compiled_identity']['product_layout']['hunks'][0]['bytes']-=4
            if change=='scope':stage['body_observation']['ball_phase_scope']='all match bodies skipped'
            if change=='source':stage['completed_jobs'][1]['incoming_prefix_validation']['incoming_state']='11'*318
            with self.subTest(change=change):self.assertFalse(required_extent(self.case(),r))

    def test_latest_cpu_receipt_is_a_required_dependency(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'scripts').mkdir()
            (root/'scripts/run_preview_native.py').write_text('pass\n')
            current=root/CPU9_RECEIPTS[0];current.parent.mkdir(parents=True)
            current.write_text('{"passed":true}\n')
            before=dependencies(self.case(),root)['files'][str(current)]
            current.write_text('{"passed":false}\n')
            after=dependencies(self.case(),root)['files'][str(current)]
            self.assertNotEqual(before,after)
        for path in CPU9_RECEIPTS:
            r=receipt();r['evidence']['files'].pop(path)
            with self.subTest(path=path):self.assertFalse(required_extent(self.case(),r))

    def test_body_boundaries_bind_counts_and_tail_intents_once(self):
        r=receipt();block=r['preview_native_validation']['body_observation']
        parent,child=[f for f in block['frames'] if f['api_row_index']==14][:2]
        self.assertEqual(parent['api_row_index'],child['api_row_index'])
        parent['end']=dict(child['end']);parent['elapsed_cck']=parent['end']['cck']-parent['start']['cck']
        child.update(depth=2,entry_sp=parent['entry_sp'],exit_sp=parent['exit_sp'],
            return_pc=parent['return_pc'],exit_pc=parent['exit_pc'])
        child['entry_registers']['a'][7]=child['entry_sp']
        parent['events']=child['events']=[['title']]
        block['semantic_intents']=[dict(event=['title'],position=child['start'],api_row_index=parent['api_row_index'])]
        block['outer_logical_calls']-=1
        block['internal_stops']-=1;block['entry_return_observations']-=1
        self.assertTrue(required_extent(self.case(),r))
        block['semantic_intents'].append(dict(block['semantic_intents'][0]))
        self.assertFalse(required_extent(self.case(),r))
        block['semantic_intents'].pop();block['frames'].pop()
        self.assertFalse(required_extent(self.case(),r))

    def test_nonworker_api_cannot_claim_seek_bodies(self):
        r=receipt();stage=r['preview_native_validation'];block=stage['body_observation']
        api=stage['costs']['api_rows'][1];api['bodies']=1
        frame=copy.deepcopy(block['frames'][0]);frame.update(api_row_index=1,before='00'*318)
        frame['start']=dict(api['begin'],cck=101);frame['end']=dict(api['end'],cck=102)
        frame['ownership'].update(active=0,status=7)
        block['frames'].insert(0,frame)
        for index,frame in enumerate(block['frames']):frame['entry_index']=index
        block['actual_body_entries']+=1;block['outer_logical_calls']+=1
        block['internal_stops']+=2;block['entry_return_observations']+=2
        self.assertFalse(required_extent(self.case(),r))


if __name__=='__main__':unittest.main()
