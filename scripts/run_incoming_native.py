"""Finite incoming/contact/outgoing physical latency and sprite probe.

Runs the current manifest-bound product; initializes no intermediate state.
Normal physical play supplies the opponent launch, then freezes via controls.
"""
import argparse
import gzip
import hashlib
import json
import math
import re
import os
import subprocess
from pathlib import Path

from deadline_policy import POLICY,record as deadline_policy_record
from native_evidence import ReportRun, TARGET, atomic_json, digest, inputs_for, snapshot
from native_hunk import loaded_hunks
from build_match_core import load_image
from landing_try_proof import reference as original_ball_reference
from match_core_cpu import cpu_tool_inputs
from native_tools import ROOT, emulator_config
from run_tutorial_capture import FIELDS
from tutorial_capture import CaptureSession, CallbackObserver, SurfaceObserver
from tutorial_latency import LatencyObserver, StackTiming, instruction_map
from predictor_native_proof import InputTrace, original_reference, contact_timing

from native_metrics import memory_summary
from ordinary_cadence import chip_memory
PROVIDER_CLOCK = 3546895
CLOCKS = {'PAL':3546895, 'NTSC':3579545}
CAPS = dict(physical_seconds=30, callbacks=2048, boundary_stops=8192,
            uncompressed_transcript_bytes=2*1024*1024*1024)


class LatencySession(CaptureSession):
    MAX_RAW_BYTES = CAPS['uncompressed_transcript_bytes']


def run(standard='PAL', baseline=None, predictor=False, origin_cache=False, deadline=False):
    assert standard in CLOCKS
    origin_cache = origin_cache or deadline
    predictor = predictor or origin_cache
    directory = ROOT/'build/tests'/(('deadline-native-' if deadline else 'incoming-origin-native-' if origin_cache else 'predictor-native-' if predictor else 'incoming-flight-native-')+standard.lower())
    directory.mkdir(parents=True, exist_ok=True)
    output = directory/'report.json'
    transaction = ReportRun([output], 'native-feedback', 'maintained-native',
                            'Current native product; fixed incoming, physical edit/publication and looping normal sprites')
    try:
        baseline = Path(baseline) if baseline else ROOT/'build/amiga/interfaces/enhanced'
        executable, listing_path, manifest_path = [baseline/n for n in (
            'baseline-rally','native.lst','baseline-rally.compile.json')]
        product_sha256 = digest(executable)
        manifest = json.loads(manifest_path.read_text())
        assert manifest['executable_sha256'] == product_sha256
        listing_hashes=[sha for name,sha in manifest['files'].items() if name.endswith('/native.lst')]
        assert listing_hashes==[digest(listing_path)], 'Retained listing is not manifest-bound'
        paths, tools = inputs_for('native-feedback','scripts/run_incoming_native.py')
        cpu_paths,tools['machine68k']=cpu_tool_inputs()
        transaction.meta.update(commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                                native_product_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                                files=snapshot(set(paths)|set(cpu_paths)|{executable,listing_path,manifest_path}|({POLICY} if deadline else set())),
                                tools=tools, runner='scripts/run_incoming_native.py',
                                actual_target=dict(TARGET, video=standard),
                                target_role='legacy-validator-reference',
                                target_scope='evidence.target is a PAL compatibility reference; report.target and actual_target bind executed region')
        transaction.meta['environment']['PYTHONPATH']=os.environ.get('PYTHONPATH')
        listing = listing_path.read_text()
        config = emulator_config()
        boundaries, actions, endpoints = [], [], []
        frozen = None;frozen_records=None;history_end=None;resume_readback=None;first_resumed_boundary=False;held_resume_samples=0
        frozen_origin=None;origin_captures=[];deadline_operations=[]
        with LatencySession(directory) as session:
            session.inspect('session_launch', dict(binary=config['tools']['copperline'],
                run=str(executable), args=['--chipset','OCS','--video',standard,
                    '--cpu','68000','--chip','512K','--slow','0','--fast','0',
                    '--noaudio',config['inputs']['amiga_rom']]))
            stop = session.inspect('run_until',dict(seconds=30))
            assert stop['reason'] == 'loadseg'
            segments = session.inspect('segments.list')['current']
            symbols = {n:segments[int(h)]['start']+int(o,16) for n,h,o in re.findall(
                r'^([A-Za-z_]\w*)\s+(\d\d):([\da-fA-F]{8})\s*$',listing,re.M)}
            def read(a,n):
                return bytes.fromhex(session.inspect('mem_read',dict(addr=a,len=n))['data'])
            def block(n,width):return read(symbols[n],width)
            def number(n,width=None):
                return int.from_bytes(block(n,FIELDS.get(n,2) if width is None else width),'big')
            loaded = loaded_hunks(executable,segments,read)
            calls, returns = instruction_map(listing,segments,read)
            simulation_calls=[pc for pc,c in calls.items() if c['callee']=='simulation_update']
            assert len(simulation_calls)==1
            probe_symbols=dict(title_copper=symbols['title_copper'],simulation_update_call_pc=simulation_calls[0],simulation_update=symbols['simulation_update'])
            callbacks = CallbackObserver(0,symbols)
            fields = dict(FIELDS,last_timer_count=4,simulation_phase=4,simulation_interval=4,game_title_display=1)
            if predictor:fields.update(game_preview_projection_requested=2,game_preview_predictor_routes=2,
                game_preview_predictor_reason=2,game_preview_dispatches=4,game_preview_launches=2,
                game_preview_stream_cursors=16,game_preview_synthetic_phases=4,keyboard_ack=1,keyboard_ack_timer=2,
                tutorial_packet=1,game_input_bits=2)
            if deadline:fields['game_preview_operation']=2
            callbacks.surfaces = SurfaceObserver(symbols,read,
                last_line=311 if standard=='PAL' else 261, verify_sprites=True)
            timing = StackTiming(calls,returns,symbols['game_stack_bottom'],symbols['game_stack_top'])
            session.observer = LatencyObserver(callbacks,timing)
            input_trace=InputTrace(symbols)
            if predictor:
                previous_observe=session.observer.observe
                def observe(message):
                    input_trace.observe(message);previous_observe(message)
                    row=message.get('params',{})
                    if deadline and row.get('access')=='write' and row.get('addr')==symbols['game_preview_operation']:
                        deadline_operations.append(dict(position=row['position'],operation=int(row['value'])))
                session.observer.observe=observe
            watches = callbacks.watches(fields,read)+callbacks.surfaces.watches()+[
                dict(addr=symbols['game_stack_bottom'],
                     len=symbols['game_stack_top']-symbols['game_stack_bottom'],access=access) for access in ('read','write')]+[
                dict(addr=a,len=1,access='read') for a in (0xbfd400,0xbfd500,0xbfd600,0xbfd700)]
            if predictor:watches+=input_trace.watches()
            subscribed = session.inspect('events.subscribe',dict(events=['mmio','frame'],mmio=watches))
            assert subscribed.get('dropped_notifications',0)==0
            session.inspect('break_add',dict(kind='pc',addr=symbols['simulation_update']))
            if predictor:session.inspect('break_add',dict(kind='pc',addr=symbols['tutorial_resume_restored']))
            if origin_cache:session.inspect('break_add',dict(kind='pc',addr=symbols['game_history_incoming_capture_complete']))
            drain_breaks=['tutorial_copy_court','ui_footer_draw'] if predictor else []
            for name in drain_breaks:session.inspect('break_add',dict(kind='pc',addr=symbols[name]))
            origin = stop['cck']
            def position():
                return dict(cck=stop['cck'], frame=stop['frame'],
                    provider_seconds=stop['seconds'],
                    physical_seconds=(stop['cck']-origin)/CLOCKS[standard])
            def advance(seconds):
                nonlocal stop,frozen,frozen_records,history_end,resume_readback,first_resumed_boundary,held_resume_samples,frozen_origin
                goal = stop['cck']+math.ceil(seconds*CLOCKS[standard])
                assert (goal-origin)/CLOCKS[standard] <= CAPS['physical_seconds']
                for _ in range(CAPS['boundary_stops']):
                    stop=session.inspect('run_until',dict(seconds=goal/PROVIDER_CLOCK))
                    if origin_cache and stop.get('pc')==symbols['game_history_incoming_capture_complete']:
                        cached=block('game_history_incoming_state',318)
                        assert cached==block('game_core_state',318)
                        assert number('game_history_incoming_cursor',8)==number('game_history_cursor',8)
                        origin_captures.append(dict(position=position(),state=cached.hex(),cursor=number('game_history_cursor',8),end=number('game_history_incoming_end')))
                    if predictor and stop.get('pc')==symbols['tutorial_resume_restored']:
                        assert frozen is not None and resume_readback is None
                        restored=block('game_core_state',318);history=block('game_history_state',72)
                        expected_history=bytearray(frozen[1]);base=symbols['game_history_state']
                        expected_history[symbols['game_history_mode']-base]=1
                        p=symbols['game_history_position']-base;c=symbols['game_history_cursor']-base
                        expected_history[p:p+8]=frozen[1][c:c+8]
                        assert restored==frozen[2] and history==expected_history
                        resume_readback=dict(passed=True,state=restored.hex(),expected=frozen[2].hex(),
                            history=history.hex(),expected_history=expected_history.hex(),position=position())
                    if stop.get('pc')==symbols['simulation_update']:
                        assert callbacks.pending is None
                        assert callbacks.completed <= CAPS['callbacks']
                        states=tuple(block(n,w) for n,w in (
                            ('game_core_state',318),('game_history_state',72),
                            ('tutorial_interrupted_state',318)))
                        fields={n:number(n) for n in FIELDS}
                        if fields['tutorial_active']:
                            if frozen is None:
                                frozen=states
                                if origin_cache:frozen_origin=block('game_history_incoming_storage',344)
                                if predictor:
                                    records_bytes=symbols['game_history_checkpoints']-symbols['game_history_buffer']
                                    frozen_records=block('game_history_buffer',records_bytes)
                                    history_end=number('game_history_cursor',8)
                            assert states==frozen, 'Frozen selected318/history72/livebackup changed'
                            if origin_cache:assert block('game_history_incoming_storage',344)==frozen_origin,'Paused origin cache changed'
                        elif predictor and resume_readback is not None and not first_resumed_boundary:
                            assert states[0]==frozen[2],'Resume dispatched before complete restored boundary'
                            first_resumed_boundary=True
                        elif predictor and first_resumed_boundary:
                            assert not block('game_input_pressed',2)[0]&16,'Carried held F invented a live action edge'
                            held_resume_samples+=1
                        boundaries.append(dict(position=position(), fields=fields,
                            state=states[0].hex(),history=states[1].hex(),backup=states[2].hex()))
                    if stop.get('reason')=='target' or stop['cck']>=goal:break
                else:raise AssertionError('Latency complete-boundary stop cap')
            def key(code,held,seconds=.06):
                actions.append(dict(rawkey=code,held=held,position=position(),tutorial_active=bool(number('tutorial_active'))))
                session.inspect('input_key',dict(rawkey=code,action='press' if held else 'release'))
                advance(seconds)
            def endpoint(label, previous_generation=None, request=None):
                request=position() if request is None else request
                for probe in range(300):
                    advance(.05)
                    if probe%20==0:
                        print(json.dumps(dict(label=label,probe=probe,status=number('game_preview_status'),
                              counts=block('game_preview_counts',4).hex(),
                              dispatches=block('game_preview_dispatches',4).hex(),
                              flight_phases=block('game_preview_flight_phases',4).hex(),
                              launches=block('game_preview_launches',2).hex())),flush=True)
                    generation=number('tutorial_generation',4)
                    published=[p for p in callbacks.surfaces.publications
                        if p['position']['cck']>=request['cck']
                        and p['tutorial_fields'].get('tutorial_generation')==generation
                        and p['tutorial_fields'].get('tutorial_presentation_generation')==generation
                        and p['tutorial_fields'].get('tutorial_placement_ready')
                        and not p['tutorial_fields'].get('tutorial_placement_dirty')
                        and p['tutorial_fields'].get('tutorial_active_variant')==0
                        and p['tutorial_fields'].get('tutorial_ball_mode') in (1,2)
                        and ((p.get('endpoint_outcomes',0)>>16) or (p['tutorial_fields'].get('tutorial_available_outcomes',0)>>16))]
                    if published and (previous_generation is None or generation!=previous_generation):
                        scene=published[0] # actual COPJMP, not a later animation/wait match
                        assert scene.get('native_sprite_check'), 'Endpoint sprite bank lacks actual check'
                        row=dict(label=label, request=request, observed=position(),
                            first_actual_publication=dict(scene),generation=generation,
                            latency_cck=scene['position']['cck']-request['cck'],
                            incoming_cursor=block('game_preview_incoming',8).hex(),
                            incoming_state_sha256=hashlib.sha256(block('game_preview_incoming_state',318)).hexdigest(),
                            counts=[int.from_bytes(block('game_preview_counts',4)[i:i+2],'big') for i in (0,2)],
                            outcomes=[int.from_bytes(block('game_preview_endpoint_outcomes',4)[i:i+2],'big') or int.from_bytes(block('game_preview_outcomes',4)[i:i+2],'big') for i in (0,2)],
                            dense_outcomes=[int.from_bytes(block('game_preview_outcomes',4)[i:i+2],'big') for i in (0,2)],
                            endpoint_ready_before_dense=bool(scene['tutorial_fields']['tutorial_ball_mode']==1 and scene.get('endpoint_outcomes',0)>>16 and scene.get('endpoint_ready',0)>>8 and scene.get('endpoint_generation')==generation and not (scene['tutorial_fields'].get('tutorial_available_outcomes',0)>>16)),
                            incoming_dispatches=[int.from_bytes(block('game_preview_dispatches',4)[i:i+2],'big') for i in (0,2)],
                            outgoing_phases=[int.from_bytes(block('game_preview_flight_phases',4)[i:i+2],'big') for i in (0,2)],
                            human_launches=list(block('game_preview_launches',2)),
                            held_launch_state=block('game_preview_launch_states',318).hex(),
                            held_endpoint_phase=number('game_preview_endpoint_phases',2),
                            held_endpoint_point=block('game_preview_endpoints',8).hex(),
                            held_query_attempted=number('game_preview_endpoint_attempted',1),
                            held_query_reason=number('game_preview_endpoint_reasons',2),
                            held_terminal_state=(block('game_preview_endpoint_scratch',318) if number('game_preview_endpoint_attempted',1) and not number('game_preview_endpoint_reasons',2) else block('game_preview_held_state',318)).hex())
                        if predictor:
                            row.update(incoming_state=block('game_preview_incoming_state',318).hex(),
                                held_path=block('game_preview_paths',number('game_preview_counts',2)*8).hex(),
                                history_oldest=number('game_history_oldest',8),
                                x=number('game_preview_x'),y=number('game_preview_y'),end=number('game_preview_end'),
                                routes=list(block('game_preview_predictor_routes',2)),
                                guard_reason=number('game_preview_predictor_reason'))
                            assert row['routes']==[1,1] and row['guard_reason']==0
                        # Negative latency means a stale already-published endpoint.
                        assert row['latency_cck']>=0
                        row['physical_latency_seconds']=row['latency_cck']/CLOCKS[standard]
                        endpoints.append(row)
                        print(json.dumps({k:v for k,v in row.items() if k!='first_actual_publication'}),flush=True)
                        return generation
                raise AssertionError('No actual fresh held endpoint within declared latency cap')
            advance(.3)
            for _ in range(100):
                if session.observer.title_ready:
                    break
                advance(.05)
            else:raise AssertionError('No actual native title publication before input')
            title_ready=dict(session.observer.title_ready)
            key(0x01,True);key(0x01,False)
            for _ in range(100):
                if number('game_lifecycle',2)==1 and not (number('game_mode',1)&0x80):
                    break
                advance(.05)
            else:raise AssertionError('One-player physical selection did not enter PLAYING')
            # Ordinary physical serve, then detect the actual receiving flight.
            key(0x23,True,.04);key(0x23,False,.02)
            for _ in range(200):
                if (number('game_contact',1)&0x40 and
                        number('game_flight',1)&0x40 and
                        not number('game_contact',1)&0x8d):
                    break
                advance(.02)
            else:raise AssertionError('No genuine opponent incoming launch under physical play')
            incoming_live=dict(position=position(),state=block('game_core_state',318).hex())
            if origin_cache:
                assert number('game_history_incoming_valid',1) and origin_captures
                incoming_live['origin_cache']=dict(state=block('game_history_incoming_state',318).hex(),cursor=number('game_history_incoming_cursor',8))
                assert incoming_live['origin_cache']['state']==origin_captures[-1]['state']
            key(0x24,True,.02);key(0x24,False,.02)
            key(0x24,True,.02);key(0x24,False,.02)
            assert number('tutorial_active')
            assert number('game_preview_ordinal',2)==0xfffe
            assert number('game_preview_kind',2)==0
            if origin_cache:
                assert block('game_preview_incoming_state',318).hex()==incoming_live['origin_cache']['state']
                assert number('game_preview_incoming',8)+1==incoming_live['origin_cache']['cursor']
            held_start=position()
            key(0x23,True) # F held; actual held alternative, not a supplied expected path.
            generation=endpoint('initial-held',request=held_start)
            if not endpoints[-1]['human_launches'][0]:
                # Choose a placement from actual displayed incoming samples;
                # physical controls perform the edit, and actual contact must
                # accept it. This is input selection, never expected injection.
                count=number('game_preview_counts',2)
                path=block('game_preview_paths',count*8)
                target_y=number('tutorial_y')+27
                samples=[path[i:i+8] for i in range(0,len(path),8)]
                sample=min(samples,key=lambda p:abs(p[1]-target_y))
                target_x=max(40,min(199,sample[0]-8))
                alignment_start=position()
                direction=0x20 if target_x<number('tutorial_x') else 0x22
                session.inspect('input_key',dict(rawkey=direction,action='press'))
                for _ in range(200):
                    advance(.02)
                    x=number('tutorial_x')
                    if (x<=target_x if direction==0x20 else x>=target_x):break
                else:raise AssertionError('Finite physical placement did not reach observed incoming shadow')
                session.inspect('input_key',dict(rawkey=direction,action='release'))
                advance(.02)
                generation=endpoint('aligned-held',request=alignment_start)
            assert endpoints[-1]['human_launches'][0]
            assert endpoints[-1]['outgoing_phases'][0]>0
            assert endpoints[-1]['outcomes'][0] in (1,2,3)
            previous_xy=(number('tutorial_x'),number('tutorial_y'))
            edit_start=position()
            key(0x22,True,.02);key(0x22,False,.001)
            assert (number('tutorial_x'),number('tutorial_y'))!=previous_xy
            endpoint('fresh-D-edit',generation,request=edit_start)
            assert endpoints[-1]['human_launches'][0] and endpoints[-1]['outgoing_phases'][0]>0
            assert endpoints[-1]['outcomes'][0] in (1,2,3)
            endpoints[-1]['physical_input_request']=edit_start
            endpoints[-1]['input_to_publication_cck']=(
                endpoints[-1]['first_actual_publication']['position']['cck']-edit_start['cck'])
            endpoints[-1]['physical_input_latency_seconds']=(
                endpoints[-1]['input_to_publication_cck']/CLOCKS[standard])
            assert any(e['endpoint_ready_before_dense'] for e in endpoints), 'No independent early endpoint publication'
            assert len({e['incoming_state_sha256'] for e in endpoints})==1
            assert len({e['incoming_cursor'] for e in endpoints})==1
            before_loop=len(callbacks.surfaces.publications)
            for _ in range(100):
                advance(.05)
                frames=callbacks.surfaces.publications[before_loop:]
                eligible=[p for p in frames if
                    p.get('tutorial_fields',{}).get('tutorial_generation')==number('tutorial_generation',4)
                    and p['tutorial_fields'].get('tutorial_active_variant')==0
                    and p['tutorial_fields'].get('tutorial_ball_mode')==2]
                pairs=list(zip(eligible,eligible[1:]))
                for a,b in pairs:
                    if b['tutorial_fields']['tutorial_animation_index']<a['tutorial_fields']['tutorial_animation_index']:
                        assert a['tutorial_fields']['tutorial_available_outcomes']>>16, 'Partial available path repeated before dense completion'
                        assert a['native_sprite_check']['actual_sample']==endpoints[-1]['held_endpoint_point']
                terminal=number('tutorial_counts',4)>>16
                repetitions=[(a,b) for a,b in pairs
                    if a['tutorial_fields'].get('tutorial_available_outcomes',0)>>16
                    and a.get('native_sprite_check',{}).get('actual_sample')==endpoints[-1]['held_endpoint_point']
                    and a['tutorial_fields'].get('tutorial_animation_index')==terminal-1
                    and b['tutorial_fields'].get('tutorial_animation_index')==0
                    and ((b['tutorial_fields']['tutorial_animation_callback']-
                          a['tutorial_fields']['tutorial_animation_callback'])&65535)>=30]
                if repetitions:break
            else:raise AssertionError('Normal ball sequence did not repeat after terminal dwell')
            loop_frames=eligible
            repeat_witness=list(repetitions[0])
            outgoing=[p for p in eligible
                if endpoints[-1]['incoming_dispatches'][0]<p['tutorial_fields']['tutorial_animation_index']<terminal-1
                and p.get('native_sprite_check',{}).get('matched')
                and p['native_sprite_check'].get('actual_sample')
                and bytes.fromhex(p['native_sprite_check']['actual_sample'])[6]&15
                and bytes.fromhex(p['native_sprite_check']['actual_sample'])[3]<192]
            assert outgoing, 'No actual visible outgoing ball sample publication'
            outgoing_witness=outgoing[0]
            assert repeat_witness[1]['position']['cck']-repeat_witness[0]['position']['cck']>=29*number('simulation_interval_whole',4)*5
            input_result=None
            if predictor:
                assert block('game_history_buffer',len(frozen_records))==frozen_records,'Paused native record store changed'
                # Release/repress movement, then resume while the fresh predictor
                # is still computing. Real menu actions invalidate that job.
                key(0x22,True,.02);key(0x22,False,.02)
                cancel_generation=number('tutorial_generation',4)
                assert number('game_preview_status') in (1,2,3,4),'Cancel challenge did not reach an active job'
                key(0x24,True,.02);key(0x24,False,.02)
                assert number('tutorial_menu')
                key(0x4d,True,.02);key(0x4d,False,.02)
                key(0x44,True,.02);key(0x44,False,.02)
                advance(.12)
                assert resume_readback and first_resumed_boundary and held_resume_samples>=2 and not number('tutorial_active')
                assert number('game_preview_generation',4)!=cancel_generation
                assert block('game_keyboard_matrix',128)[0x22]==0
            # Stop before the next real callback body, not inside an API.
            stop=session.inspect('run_until',dict(seconds=(stop['cck']+CLOCKS[standard]*.02)/PROVIDER_CLOCK))
            assert stop.get('pc')==symbols['simulation_update'] and callbacks.pending is None
            actual_video=[number('presentation_last_line',2),number('simulation_interval_whole',4),
                          number('simulation_interval_fraction',2)]
            assert actual_video == (
                        [311,11838,14906] if standard=='PAL' else [261,11947,13180]), 'Actual video selectors mismatch'
            interval=number('simulation_interval_whole',4)*65536+number('simulation_interval_fraction',2)
            callback_result=callbacks.result(interval)
            stack_result=timing.result()
            if predictor:input_result=input_trace.result(actions,stack_result['calls'])
            open_calls=stack_result['open_enclosing_calls']
            assert len(open_calls)==1 and open_calls[0]['callee']=='simulation_update'
            assert open_calls[0]['depth']==0 and open_calls[0]['caller'] is None
            assert open_calls[0]['entry_pc']==simulation_calls[0], 'Incomplete API/IRQ call at final boundary'
            assert open_calls[0]['entry_store_complete']['cck']<=stop['cck']
            final_stop=dict(stop)
            memory=memory_summary(chip_memory(read))
            assert any(r['category']=='public-preview' for r in stack_result['calls'])
            assert any(r['category']=='core-body' for r in stack_result['calls'])
            raw=dict(records=session.records,uncompressed_bytes=session.raw_bytes,
                     cap_uncompressed_bytes=session.MAX_RAW_BYTES)
        capture=directory/('latency.json.gz' if origin_cache else 'latency.json')
        captured=dict(boundaries=boundaries,actions=actions,endpoints=endpoints,
            timing=callback_result,stack_timing=stack_result, loaded_hunks=loaded,title_ready=title_ready,probe_symbols=probe_symbols,final_stop=final_stop,
            call_map=calls, return_pcs=sorted(returns),literal_rpc=raw,
            timer_reads=session.observer.timer_reads,
            incoming_live=incoming_live, loop_frames=loop_frames, repeat_witness=repeat_witness, outgoing_witness=outgoing_witness, native_memory=memory,
            timer_scope='Read-only literal cascaded CIA counter reads with actual saved phase/interval/epoch; '
                        'admission declines require emitted control-flow interpretation, not inferred host decisions.')
        if deadline:
            from deadline_extent import validate_capture,negative_controls
            captured['publications']=callbacks.surfaces.publications
            captured['deadline_operations']=deadline_operations
            with gzip.open(directory/'deadline-calibration-unvalidated.json.gz','wt',encoding='utf-8') as handle:json.dump(captured,handle,separators=(',',':'))
            captured['deadline']=validate_capture(captured)
            captured['deadline_negative_controls']=negative_controls(captured)
        cpu_image,cpu_symbols=load_image(executable)
        for row in endpoints:
            if predictor:row['original_incoming_reference']=original_reference(cpu_image,cpu_symbols,row,
                frozen_records,len(frozen_records)//14,history_end)
            if predictor:row['contact_timing']=contact_timing(row,stack_result['calls'],input_trace.launch_rows)
            if not row['human_launches'][0]:
                row['original_outgoing_reference']='No launch: no outgoing endpoint claimed'
                continue
            final,sample,phases,outcome,_=original_ball_reference(cpu_image,cpu_symbols,bytes.fromhex(row['held_launch_state']))
            scene=row['first_actual_publication']
            if scene['tutorial_fields']['tutorial_ball_mode']==1:
                assert scene['native_sprite_check']['actual_sample']==sample.hex()
                assert bytes.fromhex(scene['endpoint_points'])[:8]==sample
                assert scene['endpoint_phases']>>16==phases and scene['endpoint_outcomes']>>16==outcome
                assert scene['endpoint_ready']>>8 and scene['endpoint_generation']==row['generation']
            assert row['held_endpoint_point']==sample.hex()
            assert row['held_endpoint_phase']==phases and row['outcomes'][0]==outcome
            assert row['held_terminal_state']==final.hex()
            row['original_outgoing_reference']=dict(full318_equal=True,point_equal=True,phase_equal=True,
                outcome_equal=True,phases=phases,outcome=outcome,endpoint=sample.hex(),
                expected_full_state=final.hex(),seed_sha256=hashlib.sha256(bytes.fromhex(row['held_launch_state'])).hexdigest())
            if predictor:row['original_outgoing_reference']['scope']='Complete equality relative to captured reduced preview launch seed; not a full edited-match checkpoint'
        captured['endpoints']=endpoints
        report=dict(passed=True,subject='maintained-native',target=dict(TARGET,video=standard),
            executable_sha256=product_sha256, incoming_flight=True, endpoints=endpoints, native_memory=memory,
            repeated_sequence=True, loop_publications=len(loop_frames), repeat_witness=repeat_witness,
            actual_human_outgoing=True, outgoing_witness=outgoing_witness,
            capture=str(capture.relative_to(ROOT)),declared_caps=CAPS,
            timing=callback_result, full318_history72_backup_guard=True,
            frozen_boundaries=sum(bool(r['fields']['tutorial_active']) for r in boundaries),
            stack_protocol=stack_result['protocol'], dropped_notifications=callbacks.dropped,
            actual_video=actual_video,title_ready=title_ready,
            physical_clock_hz=CLOCKS[standard], provider_seconds_clock_hz=PROVIDER_CLOCK,
            scope='Current native physical incoming trial, changed placement, actual normal-sprite samples and repeat; '
                  'complete frozen318/history72/livebackup and finite timing. Full release/cold ADF acceptance remains pending.')
        if predictor:
            kernel_calls=[r for r in stack_result['calls'] if r['callee']=='input_update'
                and symbols['game_preview_predictor_code_begin']<=r['entry_pc']<symbols['game_preview_predictor_code_end']]
            assert kernel_calls,'No emitted predictor input call executed'
            report.update(guarded_predictor=True,input_probe=input_result,resume_latest=resume_readback,
                first_resumed_boundary_equal=first_resumed_boundary,record_store_unchanged=True,
                emitted_kernel_calls=len(kernel_calls),cancelled_active_job=True,held_resume_samples=held_resume_samples,
                observer_drain_breaks=drain_breaks,
                drain_scope='Read-only helper entry stops drain event bursts; no guest writes, clock advancement or callback regime selection')
            captured.update(input_probe=input_result,resume_latest=resume_readback,
                first_resumed_boundary_equal=first_resumed_boundary,kernel_calls=kernel_calls,
                records=frozen_records.hex(),history_end=history_end)
        if origin_cache:
            requests=[r for r in stack_result['calls'] if r['callee']=='game_preview_request_projected']
            assert requests and not any(r['callee']=='game_preview_resolve_one' for r in stack_result['calls'])
            origin_result=dict(passed=True,storage_bytes=344,captures=origin_captures,paused_immutable=True,
                current_request_cache_equal=True,original_resolver_calls=0,initial_request=requests[0],
                capture_calls=[r for r in stack_result['calls'] if r['callee']=='game_history_after' and any(r['entry_store_complete']['cck']<=c['position']['cck']<=r['exit']['cck'] for c in origin_captures)])
            assert origin_result['capture_calls']
            origin_result['initial_request_to_first_held_endpoint_cck']=endpoints[0]['first_actual_publication']['position']['cck']-requests[0]['entry']['cck']
            origin_result['initial_request_to_first_held_endpoint_seconds']=origin_result['initial_request_to_first_held_endpoint_cck']/CLOCKS[standard]
            placements=[p for p in callbacks.surfaces.publications if p['position']['cck']>=requests[0]['entry']['cck']
                and p.get('tutorial_fields',{}).get('tutorial_generation')==endpoints[0]['generation']
                and p['tutorial_fields'].get('tutorial_presentation_generation')==endpoints[0]['generation']
                and p['tutorial_fields'].get('tutorial_placement_ready') and not p['tutorial_fields'].get('tutorial_placement_dirty')]
            assert placements
            origin_result['initial_request_to_first_placement_cck']=placements[0]['position']['cck']-requests[0]['entry']['cck']
            report['incoming_origin']=origin_result;captured['incoming_origin']=origin_result
        if deadline:
            report['deadline']=captured['deadline']
            report['cost_policy']=deadline_policy_record(executable)
        if origin_cache:
            with gzip.open(capture,'wt',encoding='utf-8') as handle:json.dump(captured,handle,separators=(',',':'))
        else:atomic_json(capture,captured)
        atomic_json(directory/'results-unvalidated.json',report)
        artifacts=[p for p in directory.iterdir() if p.is_file() and p!=output]
        transaction.finalize(output,report,[manifest],artifacts)
    except BaseException as error:
        transaction.abort(error)
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--ntsc',action='store_true')
    parser.add_argument('--baseline',type=Path)
    parser.add_argument('--predictor',action='store_true')
    parser.add_argument('--origin-cache',action='store_true')
    parser.add_argument('--deadline',action='store_true')
    args=parser.parse_args()
    run('NTSC' if args.ntsc else 'PAL',args.baseline,args.predictor,args.origin_cache,args.deadline)
