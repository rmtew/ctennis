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
CAPS = dict(physical_seconds=25, callbacks=2048, boundary_stops=8192,
            uncompressed_transcript_bytes=2*1024*1024*1024)


class LatencySession(CaptureSession):
    MAX_RAW_BYTES = CAPS['uncompressed_transcript_bytes']


class CoherentLatencySession(LatencySession):
    # Storage bounds, not emulator-time or scheduling guarantees.
    MAX_RAW_BYTES = 512*1024*1024
    MAX_COMPRESSED_BYTES = 80*1024*1024

    def record(self,value):
        super().record(value)
        if self.records % 512 == 0:
            self.raw.flush()
            if (self.directory/'literal-rpc.jsonl.gz').stat().st_size > self.MAX_COMPRESSED_BYTES:
                self.raw_overflow=True
                raise AssertionError('Coherent observer compressed raw-byte cap exceeded')


def run(standard='PAL', coherent=False):
    baseline=None;predictor=origin_cache=deadline=physics=True;physics_control=False
    assert standard in CLOCKS
    deadline = deadline or physics
    origin_cache = origin_cache or deadline
    predictor = predictor or origin_cache
    directory = ROOT/'build/tests'/(('coherent-contact-native-' if coherent else 'physics-contact-native-')+standard.lower())
    directory.mkdir(parents=True, exist_ok=True)
    output = directory/'report.json'
    transaction = ReportRun([output], 'native-feedback', 'maintained-native',
                            'Current native product; fixed incoming, physical edit/publication and looping normal sprites')
    try:
        baseline = Path(baseline) if baseline else ROOT/('build/amiga/interfaces/physics-control' if physics_control else 'build/amiga/interfaces/enhanced')
        executable, listing_path, manifest_path = [baseline/n for n in (
            'baseline-rally','native.lst','baseline-rally.compile.json')]
        product_sha256 = digest(executable)
        manifest = json.loads(manifest_path.read_text())
        assert manifest['executable_sha256'] == product_sha256
        listing_hashes=[sha for name,sha in manifest['files'].items() if name.endswith('/native.lst')]
        assert listing_hashes==[digest(listing_path)], 'Retained listing is not manifest-bound'
        paths, tools = inputs_for('native-feedback','scripts/run_physics_contact_native.py')
        cpu_paths,tools['machine68k']=cpu_tool_inputs()
        transaction.meta.update(commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                                native_product_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                                files=snapshot(set(paths)|set(cpu_paths)|{executable,listing_path,manifest_path}|({ROOT/'docs/tutorial-coherent-cost-policy.json' if coherent else POLICY} if deadline else set())),
                                tools=tools, runner='scripts/run_physics_contact_native.py',
                                actual_target=dict(TARGET, video=standard),
                                target_role='legacy-validator-reference',
                                target_scope='evidence.target is a PAL compatibility reference; report.target and actual_target bind executed region')
        transaction.meta['environment']['PYTHONPATH']=os.environ.get('PYTHONPATH')
        listing = listing_path.read_text()
        config = emulator_config()
        boundaries, actions, endpoints = [], [], []
        frozen = None;frozen_records=None;history_end=None;resume_readback=None;first_resumed_boundary=False;held_resume_samples=0
        frozen_origin=None;origin_captures=[];deadline_operations=[];dispatch_samples=[];branch_boundaries=[];job_writes=[];endpoint_query_samples=[];overlay_writes=[];admission_writes=[];footer_commit_samples=[]
        with (CoherentLatencySession if coherent else LatencySession)(directory) as session:
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
            initial_admission_state={name:number(name,4) for name in ('simulation_phase','simulation_interval')} if coherent else {}
            loaded = loaded_hunks(executable,segments,read)
            calls, returns = instruction_map(listing,segments,read)
            step_returns={c['return_pc'] for c in calls.values() if c['callee']=='game_preview_step_variant'} if coherent else set()
            endpoint_returns={c['return_pc'] for c in calls.values() if c['callee']=='game_preview_endpoint_try'} if coherent else set()
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
            if coherent:fields.update(tutorial_job_kind=2,tutorial_job_variant=2,tutorial_job_budget=2,tutorial_job_cost=4,tutorial_jobs_completed=4)
            callbacks.surfaces = SurfaceObserver(symbols,read,
                last_line=311 if standard=='PAL' else 261, verify_sprites=True)
            timing = StackTiming(calls,returns,symbols['game_stack_bottom'],symbols['game_stack_top'])
            session.observer = LatencyObserver(callbacks,timing)
            input_trace=InputTrace(symbols)
            if coherent:
                from coherent_write_observer import CoherentWriteObserver
                coherent_writes=CoherentWriteObserver(symbols)
            if predictor:
                previous_observe=session.observer.observe
                def observe(message):
                    input_trace.observe(message);previous_observe(message)
                    row=message.get('params',{})
                    if deadline and row.get('access')=='write' and row.get('addr')==symbols['game_preview_operation']:
                        deadline_operations.append(dict(position=row['position'],operation=int(row['value'])))
                    if coherent and row.get('access')=='write':
                        if symbols['ui_overlay_plane']<=row.get('addr',0)<symbols['ui_overlay_plane']+512:
                            overlay_writes.append(dict(row,tutorial_active=bool(callbacks.state.get('tutorial_active'))))
                        completed=coherent_writes.observe(row)
                        if completed:
                            (admission_writes if completed['field'] in ('simulation_phase','simulation_interval') else job_writes).append(completed)
                session.observer.observe=observe
            watches = callbacks.watches(fields,read)+callbacks.surfaces.watches()+[
                dict(addr=symbols['game_stack_bottom'],
                     len=symbols['game_stack_top']-symbols['game_stack_bottom'],access=access) for access in ('read','write')]+[
                dict(addr=a,len=1,access='read') for a in (0xbfd400,0xbfd500,0xbfd600,0xbfd700)]
            if predictor:watches+=input_trace.watches()
            if coherent:watches.append(dict(addr=symbols['ui_overlay_plane'],len=512,access='write'))
            subscribed = session.inspect('events.subscribe',dict(events=['mmio','frame'],mmio=watches))
            assert subscribed.get('dropped_notifications',0)==0
            session.inspect('break_add',dict(kind='pc',addr=symbols['simulation_update']))
            if predictor:session.inspect('break_add',dict(kind='pc',addr=symbols['tutorial_resume_restored']))
            if origin_cache:session.inspect('break_add',dict(kind='pc',addr=symbols['game_history_incoming_capture_complete']))
            drain_breaks=['tutorial_copy_court','ui_footer_draw'] if predictor else []
            for name in drain_breaks:session.inspect('break_add',dict(kind='pc',addr=symbols[name]))
            session.inspect('break_add',dict(kind='pc',addr=symbols['game_preview_dispatch']))
            if coherent:session.inspect('break_add',dict(kind='pc',addr=symbols['tutorial_footer_commit']))
            for pc in step_returns|endpoint_returns:session.inspect('break_add',dict(kind='pc',addr=pc))
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
                    if coherent and stop.get('pc')==symbols['tutorial_footer_commit']:
                        footer_commit_samples.append(dict(position=position(),generation=number('tutorial_generation',4),
                            footer_generation=number('tutorial_footer_generation',4),staged=block('tutorial_footer_scratch',512).hex()))
                    if stop.get('pc') in endpoint_returns:
                        variant=number('tutorial_job_variant',2)
                        endpoint_query_samples.append(dict(position=position(),generation=number('game_preview_generation',4),variant=variant,
                            reason=number('game_preview_endpoint_reasons',4)>>(16 if variant==0 else 0)&65535,
                            state=block('game_preview_endpoint_scratch',318).hex()))
                    if stop.get('pc') in step_returns:
                        branch_boundaries.append(dict(position=position(),generation=number('game_preview_generation',4),
                            held_state=block('game_preview_held_state',318).hex(),released_state=block('game_preview_released_state',318).hex(),
                            cursors=block('game_preview_stream_cursors',16).hex(),synthetic_phases=block('game_preview_synthetic_phases',4).hex(),
                            counts=block('game_preview_counts',4).hex(),outcomes=block('game_preview_outcomes',4).hex(),
                            history=block('game_history_state',72).hex(),active=number('game_preview_active',1)))
                        assert not branch_boundaries[-1]['active'],'Public worker return retains private ownership'
                    if stop.get('pc')==symbols['game_preview_dispatch']:
                        regs=session.inspect('regs.get')
                        dispatch_samples.append(dict(position=position(),registers=regs,private_state=read(regs['a'][5],318).hex(),counts=block('game_preview_counts',4).hex(),dispatches=block('game_preview_dispatches',4).hex(),generation=number('game_preview_generation',4)))
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
                        if coherent and row['held_query_attempted'] and not row['held_query_reason']:
                            query=next((r for r in reversed(endpoint_query_samples) if r['generation']==generation and r['variant']==0 and r['reason']==0),None)
                            assert query,'Accepted held query lacks its own completed scratch sample'
                            row['held_terminal_state']=query['state']
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
            # Fixed bounded physical placement/input phases. No callback,
            # timer, simulation or preview state is written by the observer.
            delays=(.003,.009,.015,.021,.027,.033)
            for trial,delay in enumerate(delays):
                roots=[r for r in timing.rows if r['callee']=='game_launch_root']
                owners=[r for r in timing.rows if r['callee']=='tutorial_background']
                if not coherent and any(o['entry']['cck']<=r['entry']['cck']<=r['exit']['cck']<=o['exit']['cck'] for o in owners for r in roots):break
                advance(delay)
                previous=number('tutorial_generation',4)
                # Change actual contact height by physical W; subsequent trials
                # vary contact dispatch tick as well as input reception phase.
                key(0x11,True,.04);key(0x11,False,.02)
                endpoint('contact-phase-'+str(trial),previous,request=actions[-2]['position'])
            advance(.03)
            # End on an actual upcoming callback boundary; never cut an owner.
            simulation_return=calls[simulation_calls[0]]['return_pc']
            session.inspect('break_add',dict(kind='pc',addr=simulation_return))
            final_goal=(stop['cck']+CLOCKS[standard])/PROVIDER_CLOCK
            for _ in range(8192):
                stop=session.inspect('run_until',dict(seconds=final_goal))
                if stop.get('pc')==simulation_return:break
            else:raise AssertionError('No complete final callback boundary')
            actual_video=[number('presentation_last_line',2),number('simulation_interval_whole',4),number('simulation_interval_fraction',2)]
            assert actual_video==([311,11838,14906] if standard=='PAL' else [261,11947,13180])
            interval=number('simulation_interval_whole',4)*65536+number('simulation_interval_fraction',2)
            callback_result=callbacks.result(interval);stack_result=timing.result()
            assert not stack_result['open_enclosing_calls'],'Final stop must be after complete callback RTS'
            if coherent:coherent_writes.require_complete()
            input_result=input_trace.result(actions,stack_result['calls'])
            if not coherent:assert input_result['maximum_keyboard_poll_gap_cck']<=50000
            assert frozen is not None and frozen_records==block('game_history_buffer',len(frozen_records))
            records_count=(symbols['game_history_checkpoints']-symbols['game_history_buffer'])//14
            records=frozen_records;final_stop=dict(stop)
        captured=dict(boundaries=boundaries,actions=actions,endpoints=endpoints,
            timing=callback_result,stack_timing=stack_result,loaded_hunks=loaded,
            title_ready=title_ready,probe_symbols=probe_symbols,final_stop=final_stop,
            call_map=calls,return_pcs=sorted(returns),timer_reads=session.observer.timer_reads,
            deadline_operations=deadline_operations,publications=callbacks.surfaces.publications,
            input_probe=input_result,launch_rows=input_trace.launch_rows,
            retained_records=records.hex(),history_end=history_end,
            literal_rpc=dict(records=session.records,uncompressed_bytes=session.raw_bytes),
            footer_commit_samples=footer_commit_samples,initial_admission_state=initial_admission_state,admission_writes=admission_writes,overlay_writes=overlay_writes,overlay_base=symbols['ui_overlay_plane'],
            coherent_policy=(dict(policy=json.loads((ROOT/'docs/tutorial-coherent-cost-policy.json').read_text()),policy_sha256=digest(ROOT/'docs/tutorial-coherent-cost-policy.json'),scheduler_source_sha256=digest(ROOT/'amiga/game/tutorial_deadline.s'),executable_sha256=product_sha256) if coherent else None),
            endpoint_query_samples=endpoint_query_samples,scheduler_job_writes=job_writes,dispatch_samples=dispatch_samples,branch_boundaries=branch_boundaries,phase_delays_seconds=list(delays),no_simulation_state_injection=True)
        if coherent:
            from coherent_native_extent import validate_capture,negative_controls
        else:
            from deadline_extent import validate_capture,negative_controls
        from deadline_service_reduction import reduce_capture
        try:captured['deadline']=validate_capture(captured)
        except BaseException:
            with gzip.open(directory/'calibration-unvalidated.json.gz','wt') as h:json.dump(captured,h,separators=(',',':'))
            raise
        captured['deadline_negative_controls']=negative_controls(captured)
        cpu_image,cpu_symbols=load_image(executable)
        for row in endpoints:
            row['original_incoming_reference']=original_reference(cpu_image,cpu_symbols,row,records,records_count,history_end)
            if coherent and row['human_launches'][0]:
                final,sample,phases,outcome,_=original_ball_reference(cpu_image,cpu_symbols,bytes.fromhex(row['held_launch_state']))
                assert row['held_terminal_state']==final.hex() and row['held_endpoint_point']==sample.hex()
                assert row['held_endpoint_phase']==phases and row['outcomes'][0]==outcome
                row['original_outgoing_reference']=dict(passed=True,expected_full_state=final.hex(),actual_full_state=row['held_terminal_state'],
                    expected_point=sample.hex(),actual_point=row['held_endpoint_point'],phases=phases,outcome=outcome)
        chunks=captured['deadline']['chunks'];calls=stack_result['calls']
        roots=[r for r in calls if r['callee']=='game_launch_root']
        witnesses=[]
        for chunk in chunks:
            if not coherent and chunk['operation']!=8:continue
            nested=[r for r in roots if chunk['entry']['cck']<=r['entry']['cck']<=r['exit']['cck']<=chunk['exit']['cck']]
            launches=[r for r in input_trace.launch_rows if chunk['entry']['cck']<=r['position']['cck']<=chunk['exit']['cck']]
            if nested and launches:witnesses.append(dict(owner=chunk,roots=nested,launches=launches))
        if coherent:
            from coherent_native_extent import validate_witnesses
            validate_witnesses(captured,witnesses)
        captured['contact_owner_witnesses']=witnesses
        capture=directory/'latency.json.gz'
        with gzip.open(capture,'wt') as h:json.dump(captured,h,separators=(',',':'))
        services=reduce_capture(captured);assert services['passed']
        artifact=directory/'service.json.gz'
        with gzip.open(artifact,'wt') as h:json.dump(({k:v for k,v in services.items() if k!='spans'} if coherent else services),h,separators=(',',':'))
        summary=dict(passed=bool(witnesses),execution=('coherent-physical-input-contact-phase-probe' if coherent else 'physical-input-contact-phase-probe'),
            target=dict(TARGET,video=standard),executable_sha256=product_sha256,
            capture=str(capture.relative_to(ROOT)),contact_owner_witnesses=witnesses,
            trial_count=len(endpoints),deadline=captured['deadline'],coherent_policy=captured['coherent_policy'],
            input_probe={k:v for k,v in input_result.items() if k not in ('rows','transitions','acknowledgements')},
            frozen_complete_state_history_records_equal=True,reference_rows=[r['original_incoming_reference'] for r in endpoints],
            services={k:v for k,v in services.items() if k!='spans'},
            no_simulation_state_injection=True,normative_deadline_safety=False,
            observer_limits=(dict(CAPS,uncompressed_transcript_bytes=CoherentLatencySession.MAX_RAW_BYTES,compressed_transcript_bytes=CoherentLatencySession.MAX_COMPRESSED_BYTES) if coherent else CAPS))
        transaction.finalize(output,summary,[manifest],[capture,artifact,directory/'literal-rpc.jsonl.gz',directory/'emulator.log'])
        print(json.dumps(dict(report=str(output),passed=bool(witnesses),witnesses=len(witnesses))),flush=True)
        assert witnesses,'Bounded physical phase trials did not admit an accepted-contact/root owner; raw failure retained'
    except BaseException as error:
        # A missing witness remains a complete negative experiment with raw
        # evidence; earlier observer failures retain the incomplete receipt.
        if not output.exists() or not json.loads(output.read_text()).get('evidence',{}).get('state')=='complete':transaction.abort(error)
        raise




def required_extent(report,standard):
    """Recompute enclosure and complete owner detector from retained accesses."""
    if not (report.get('passed') is True and report.get('target')==dict(TARGET,video=standard)
            and report.get('execution')=='physical-input-contact-phase-probe'
            and report.get('no_simulation_state_injection') is True
            and report.get('frozen_complete_state_history_records_equal') is True):return False
    path=ROOT/report['capture']
    if report.get('evidence',{}).get('files',{}).get(report['capture'])!=digest(path):return False
    with gzip.open(path,'rt') as h:c=json.load(h)
    from deadline_extent import validate_capture
    if validate_capture(c)!=report['deadline']:return False
    rows=c['endpoints']
    if not 3<=len(rows)<=9 or not all(r.get('original_incoming_reference',{}).get('passed') is True for r in rows):return False
    calls=c['stack_timing']['calls'];w=[]
    for chunk in c['deadline']['chunks']:
        if chunk['operation']!=8:continue
        roots=[r for r in calls if r['callee']=='game_launch_root' and chunk['entry']['cck']<=r['entry']['cck']<=r['exit']['cck']<=chunk['exit']['cck']]
        launches=[r for r in c['launch_rows'] if chunk['entry']['cck']<=r['position']['cck']<=chunk['exit']['cck']]
        if roots and launches:w.append(dict(owner=chunk,roots=roots,launches=launches))
    return bool(w) and w==report['contact_owner_witnesses']==c['contact_owner_witnesses']


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--ntsc',action='store_true');parser.add_argument('--coherent',action='store_true')
    args=parser.parse_args();run('NTSC' if args.ntsc else 'PAL',coherent=args.coherent)
