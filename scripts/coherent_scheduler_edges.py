"""Declared one-time API edge fixtures; actual 68000 references, no tennis model.

Counters and geometry jobs are deliberately initialized at API limits once,
before the first tested call. They do not claim natural match reachability.
"""
import argparse
import json
import os
from pathlib import Path

from build_match_core import load_image
from coherent_scheduler_proof import raw_json, cursors
from history_proof import field, seek, cursor
from match_core_cpu import Core, cpu_tool_inputs, STACK_BASE, STACK_TOP
from native_evidence import (ReportRun, atomic_json, compile_manifest, digest,
    inputs_for, snapshot, status)
from native_tools import ROOT
from predictor_proof import discover
from preview_proof import fixture, point, protected, call_checked
from run_shared_match_core import READONLY


def setup(cpu, case, retained_reset=False):
    fixture(cpu, seed=case['seed'], dispatches=case['ticks'])
    if retained_reset:
        cpu.call_logical('game_core_return_title',[])
    cpu.call('game_history_freeze')
    seek(cpu,case['selected'])
    generation=field(cpu,'game_preview_generation',4)
    cpu.call('game_preview_request',{0:generation,1:0xfffe,2:111,3:153})
    assert cpu.cpu.r_reg(0)==1
    return generation+1


def full(cpu,name):
    return bytes(cpu.mem.r_block(cpu.symbols[name],318))


def geometry(image,s,case,path,raw):
    rows=[]
    variants=[('empty',0,0,None),('equal-512',512,512,None),
        ('equal-513',513,513,None),('last-coordinate-513',513,513,'coordinate'),
        ('last-tick-513',513,513,'tick'),('visibility-equivalent-513',513,513,'visibility'),
        ('ignored-flags-513',513,513,'flags'),('count-mismatch',512,513,None)]
    for label,left_count,right_count,change in variants:
        left=b''.join(path[:left_count]);right=bytearray(b''.join(path[:right_count]))
        if change=='coordinate':right[-8]^=1
        if change=='tick':right[-1]^=1
        if change=='flags':right[-4]^=255;right[-3]^=255
        if change=='visibility':
            for i in range(6,len(right),8):
                value=right[i]
                right[i]=(2 if value&15 else 0)|(0x20 if value&240 else 0)
        results=[]
        for reference in (True,False):
            with Core(image,s,poison=0xa5 if reference else 0x96,readonly=READONLY) as cpu:
                generation=setup(cpu,case)
                # Entire declared completion fixture is initialized once here.
                for name,value in (('game_preview_status',4),('game_preview_primed_mask',3),
                    ('game_preview_counts',left_count),('game_preview_counts_right',right_count)):
                    address=s['game_preview_counts']+2 if name.endswith('_right') else s[name]
                    cpu.mem.w16(address,value)
                cpu.mem.w_block(s['game_preview_outcomes'],b'\x00\x01\x00\x01')
                cpu.mem.w16(s['game_preview_geometry_cursor'],0)
                cpu.mem.w16(s['game_preview_coincident'],0)
                cpu.mem.w_block(s['game_preview_paths'],left)
                cpu.mem.w_block(s['game_preview_paths']+513*8,bytes(right))
                saved=protected(cpu)
                immutable=dict(states=[full(cpu,n).hex() for n in
                    ('game_preview_held_state','game_preview_released_state')],
                    paths=bytes(cpu.mem.r_block(s['game_preview_paths'],2*513*8)).hex(),
                    outcomes=bytes(cpu.mem.r_block(s['game_preview_outcomes'],4)).hex())
                old_trace=cpu.trace
                allowed=set()
                for name in ('game_preview_status','game_preview_geometry_cursor','game_preview_coincident'):
                    allowed.update(range(s[name],s[name]+2))
                def guard(mode,width,address,value):
                    size=1<<width
                    if mode=='W' and not STACK_BASE<=address<address+size<=STACK_TOP+4:
                        assert set(range(address,address+size))<=allowed, ('Geometry non-job write',label,hex(address))
                    old_trace(mode,width,address,value)
                cpu.mem.set_trace_func(guard)
                calls=[]
                if reference:
                    cycles=cpu.call('game_preview_compare_geometry')
                    calls.append(dict(cycles=cycles))
                else:
                    for _ in range(66):
                        before=field(cpu,'game_preview_geometry_cursor')
                        cycles=call_checked(cpu,'game_preview_complete',{0:generation},saved)
                        after=field(cpu,'game_preview_geometry_cursor')
                        assert 0<=after-before<=8,('Geometry budget',label,before,after)
                        calls.append(dict(cycles=cycles,before=before,after=after,status=field(cpu,'game_preview_status')))
                        if field(cpu,'game_preview_status')==5:break
                    assert field(cpu,'game_preview_status')==5,label
                    if change is None and left_count==right_count:
                        assert len(calls)==max(1,(left_count+7)//8),(label,len(calls))
                    before=bytes(cpu.mem.r_block(s['game_preview_storage'],s['game_preview_storage_end']-s['game_preview_storage']))
                    call_checked(cpu,'game_preview_complete',{0:generation},saved)
                    assert bytes(cpu.mem.r_block(s['game_preview_storage'],len(before)))==before
                assert protected(cpu)==saved
                assert immutable==dict(states=[full(cpu,n).hex() for n in
                    ('game_preview_held_state','game_preview_released_state')],
                    paths=bytes(cpu.mem.r_block(s['game_preview_paths'],2*513*8)).hex(),
                    outcomes=bytes(cpu.mem.r_block(s['game_preview_outcomes'],4)).hex())
                cpu.audit_reads()
                results.append(dict(coincident=field(cpu,'game_preview_coincident'),calls=calls,
                    stack=cpu.stack_bytes,immutable=immutable))
        assert results[0]['coincident']==results[1]['coincident'],label
        expected=int(change not in ('coordinate','tick') and left_count==right_count)
        assert results[1]['coincident']==expected,label
        raw_json(raw/(label+'.json'),dict(passed=True,reference=results[0],candidate=results[1]))
        rows.append(dict(label=label,passed=True,count=left_count,coincident=expected,
            calls=len(results[1]['calls']),max_points_per_job=8,
            max_cpu_cycles=max(r['cycles'] for r in results[1]['calls'])))
    return rows


def boundaries(image,s,case,incoming,prelaunch,raw):
    rows=[];start=s['game_core_state']
    # One-time metadata declarations, not ordinary match-length claims.
    descriptors=[('incoming-launch-256',prelaunch,256,255,0,False,0,True),
        ('incoming-limit-256',incoming,256,255,0,False,6,True),
        ('out-on-outgoing-256',incoming,256,0,255,True,3,True),
        ('out-terminal-at-513',incoming,512,0,255,True,3,True),
        ('outgoing-limit-before-body',incoming,257,0,256,True,6,False),
        ('already-full-513',incoming,513,0,255,True,6,True),
        ('lifecycle-result-boundary',incoming,1,0,0,False,7,True),
        ('lifecycle-retained-title-reset',incoming,1,0,0,False,7,False)]
    for label,origin,count,dispatches,flight_phases,outgoing,expected,execute_body in descriptors:
        initial=bytearray(origin)
        operation='game_ball_tick' if outgoing else 'game_tick_dispatch'
        if outgoing:
            for name,value in (('game_velocity_y',3),('game_contact',0),('game_step',0),('game_flight',64)):
                initial[s[name]-start]=value
        if label=='lifecycle-result-boundary':
            initial[s['game_lifecycle']-start:s['game_lifecycle']-start+2]=b'\x00\x00'
            operation='game_core_sample_result'
        with Core(image,s,initial=bytes(initial),readonly=READONLY) as ref:
            if execute_body:
                if outgoing:ref.call('game_ball_tick',{12:s['game_play_state'],13:start})
                else:ref.call_logical(operation,[0]*6 if operation=='game_core_sample_result' else [])
            expected_state=ref.state();expected_events=list(ref.events)
            ref.audit_reads()
        # Both owners use the same declared edge, testing offset and ownership.
        actuals=[]
        for variant in (1,0):
            with Core(image,s,poison=0x96 if variant else 0xa5,readonly=READONLY) as cpu:
                generation=setup(cpu,case,retained_reset=label=='lifecycle-retained-title-reset')
                for name in ('game_preview_held_state','game_preview_released_state'):
                    cpu.mem.w_block(s[name],bytes(initial))
                for name,value in (('game_preview_status',3),('game_preview_kind',1),
                    ('game_preview_primed_mask',3),('game_preview_primed',2)):
                    cpu.mem.w16(s[name],value)
                cpu.mem.w_block(s['game_preview_outcomes'],bytes(4))
                cpu.mem.w_block(s['game_preview_predictor_routes'],bytes(2))
                for name,value in (('game_preview_counts',count),('game_preview_dispatches',dispatches),
                    ('game_preview_flight_phases',flight_phases),
                    ('game_preview_synthetic_phases',2 if operation=='game_core_sample_result' else 3)):
                    cpu.mem.w16(s[name]+variant*2,value)
                cpu.mem.w8(s['game_preview_launches']+variant,255 if outgoing else 0)
                latest=cursor(cpu)-(1 if label=='lifecycle-retained-title-reset' else 0)
                cpu.mem.w_block(s['game_preview_stream_cursors']+variant*8,latest.to_bytes(8,'big'))
                saved=protected(cpu);before=cursors(cpu,variant)
                other=1-variant;other_name='game_preview_held_state' if other==0 else 'game_preview_released_state'
                other_state=full(cpu,other_name)
                paths_before=bytes(cpu.mem.r_block(s['game_preview_paths'],2*513*8))
                old_trace=cpu.trace
                def guard(mode,width,address,value):
                    size=1<<width
                    if cpu.mem.r8(s['game_preview_active']) and address<cpu.stop and address+size>cpu.start:
                        raise AssertionError(('Private canonical access',label,hex(address)))
                    if mode=='W' and address<s['game_history_buffer_end'] and address+size>s['game_history_buffer']:
                        raise AssertionError(('Frozen history write',label))
                    old_trace(mode,width,address,value)
                cpu.mem.set_trace_func(guard)
                cpu.preview_events.clear();cpu.preview_event_groups.clear()
                cycles=call_checked(cpu,'game_preview_step_variant',{0:generation,1:1,2:variant},saved)
                assert cpu.cpu.r_reg(0)==1
                name='game_preview_held_state' if variant==0 else 'game_preview_released_state'
                actual=full(cpu,name)
                assert actual==expected_state,(label,variant,'full318')
                assert cpu.preview_events==expected_events,(label,variant,'ordered events')
                assert full(cpu,other_name)==other_state,(label,'other branch state')
                assert cpu.mem.r16(s['game_preview_outcomes']+variant*2)==expected,(label,variant,'outcome')
                after=cursors(cpu,variant)
                assert after['stream']==before['stream'],label
                expected_dispatches=dispatches+(1 if execute_body and operation=='game_tick_dispatch' else 0)
                assert after['dispatches']==expected_dispatches,label
                assert after['flight']==flight_phases+(1 if execute_body and outgoing else 0),label
                append=execute_body and operation!='game_core_sample_result' and count<513
                assert cpu.mem.r16(s['game_preview_counts']+variant*2)==count+int(append),label
                after_paths=bytes(cpu.mem.r_block(s['game_preview_paths'],2*513*8))
                expected_paths=bytearray(paths_before)
                if append:expected_paths[(variant*513+count)*8:(variant*513+count+1)*8]=point(expected_state,s)
                assert after_paths==bytes(expected_paths),(label,'exact append/no overflow')
                if expected:
                    prior=actual
                    call_checked(cpu,'game_preview_step_variant',{0:generation,1:4,2:variant},saved)
                    assert full(cpu,name)==prior and cursors(cpu,variant)==after
                elif label=='incoming-launch-256':
                    assert cpu.mem.r8(s['game_preview_launches']+variant),label
                cpu.audit_reads()
                actuals.append(dict(variant=variant,state=actual.hex(),events=list(cpu.preview_events),
                    before=before,after=after,cycles=cycles,outcome=expected,stack=cpu.stack_bytes))
        raw_json(raw/(label+'.json'),dict(passed=True,reference_state=expected_state.hex(),
            reference_events=expected_events,candidate=actuals))
        rows.append(dict(label=label,passed=True,variants=[1,0],outcome=expected,
            full_state_events_cursors_equal=True,exact_append_no_overflow=True,
            max_cpu_cycles=max(a['cycles'] for a in actuals)))
    return rows


def run(executable,raw):
    image,s=load_image(executable);case=discover(image,s,0xace1)[0]
    with Core(image,s,readonly=READONLY) as cpu:
        _,states,_,_=fixture(cpu,seed=case['seed'],dispatches=case['ticks'])
        prelaunch=states[case['human']['origin']]
    # Derive every geometry point through the original ball helper, never a
    # host trajectory. Completion fixtures then declare those points once.
    with Core(image,s,initial=case['source'],readonly=READONLY) as ref:
        path=[point(ref.state(),s)]
        for _ in range(512):
            ref.call('game_ball_tick',{12:s['game_play_state'],13:s['game_core_state']})
            path.append(point(ref.state(),s))
        ref.audit_reads()
    geometry_rows=geometry(image,s,case,path,raw)
    boundary_rows=boundaries(image,s,case,case['source'],prelaunch,raw)
    return dict(passed=True,geometry=geometry_rows,boundaries=boundary_rows,
        initialized_once=True,natural_reachability_claimed=False,
        scope='Declared public variant/geometry API capacity and lifecycle edge fixtures against actual original 68000 helpers. No ordinary-play reachability, native timing, IRQ or release claim.')


def root_decline(native,raw):
    """Actual native scheduler rejects before clock/MMIO; no timer emulation."""
    image,s=load_image(native);case=discover(image,s,0xace1)[0]
    rows=[]
    for variant in (0,1):
        with Core(image,s,poison=0xa5 if variant==0 else 0x96,
                readonly=dict(READONLY,ui_paused=1,simulation_interval=4,simulation_phase=4,blank_seen=1)) as cpu:
            generation=setup(cpu,case)
            cpu.mutable_regions.append((s['tutorial_state'],s['tutorial_state_end']))
            # Declare scheduler and eligible endpoint ownership once. This is
            # an admission-regression fixture, not a physical launch receipt.
            cpu.mem.w_block(s['tutorial_state'],bytes(s['tutorial_state_end']-s['tutorial_state']))
            for name,value,width in (('tutorial_active',1,1),('ui_paused',1,1),
                ('tutorial_work_pending',1,1),('tutorial_generation',generation,4),
                ('tutorial_presentation_generation',generation,4),('tutorial_active_variant',variant,1),
                ('simulation_interval',10000,4),('simulation_phase',2000,4),('blank_seen',0,1),
                ('game_preview_status',3,2),('game_preview_primed_mask',3,2)):
                cpu.mem.w_block(s[name],value.to_bytes(width,'big'))
            for name,width,value in (('game_preview_launch_saved',1,255),
                ('game_preview_launches',1,255),('game_preview_flight_phases',2,4)):
                cpu.mem.w_block(s[name]+variant*width,value.to_bytes(width,'big'))
            cpu.mem.w_block(s['game_preview_endpoint_attempted'],bytes(2))
            cpu.mem.w_block(s['game_preview_endpoint_ready'],bytes(2))
            cpu.mem.w_block(s['game_preview_outcomes'],bytes(4))
            cpu.call('game_preview_endpoint_pending',{0:generation,1:variant})
            assert cpu.cpu.r_reg(0)==1,'Declared query seed is not eligible'
            saved_events=list(cpu.events);saved_preview_events=list(cpu.preview_events)
            forbidden=('game_preview_dispatch','game_ball_tick','game_preview_step_variant',
                'game_preview_endpoint_try','account_sim_timer','read_presentation_line')
            hits=[]
            def observe(pc):
                cpu.instruction(pc)
                if pc in {s[name] for name in forbidden}:hits.append(pc)
            cpu.cpu.set_instr_hook_callback(observe)
            frozen=bytes(cpu.mem.r_block(s['game_history_buffer'],s['game_history_buffer_end']-s['game_history_buffer']))
            saved_state=cpu.state();saved_history=bytes(cpu.mem.r_block(s['game_history_state'],72))
            before_preview=bytes(cpu.mem.r_block(s['game_preview_storage'],s['game_preview_storage_end']-s['game_preview_storage']))
            cycles=[]
            for _ in range(3):
                cycles.append(cpu.call('tutorial_background'))
                assert not hits,'Declined query advanced work or reached MMIO service'
                assert bytes(cpu.mem.r_block(s['game_preview_storage'],len(before_preview)))==before_preview
                assert field(cpu,'tutorial_job_kind')==2 and field(cpu,'tutorial_jobs_completed',4)==0
            cpu.call('game_preview_cancel',{0:generation})
            before_preview=bytes(cpu.mem.r_block(s['game_preview_storage'],len(before_preview)))
            cycles.append(cpu.call('tutorial_background'))
            assert not hits and bytes(cpu.mem.r_block(s['game_preview_storage'],len(before_preview)))==before_preview
            assert cpu.state()==saved_state and bytes(cpu.mem.r_block(s['game_history_state'],72))==saved_history
            assert bytes(cpu.mem.r_block(s['game_history_buffer'],len(frozen)))==frozen
            assert cpu.events==saved_events and cpu.preview_events==saved_preview_events, 'Scheduler changed preexisting output ledger'
            cpu.audit_reads()
            rows.append(dict(variant=variant,passed=True,declines=3,cancel_return=True,
                gap_e=8000,query_total_reserve_e=10000,no_selected_advance=True,
                no_clock_beam_or_hardware_reads=True,cycles=cycles,stack=cpu.stack_bytes,
                before_preview=before_preview.hex()))
    result=dict(passed=True,rows=rows,
        scope='Actual native tutorial_background early endpoint-decline branch with once-declared scheduler metadata. No admitted query, timer behavior, physical input or elapsed-time bound claimed.')
    raw_json(raw/'native-root-decline.json',result)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--executable',type=Path,default=ROOT/'build/standalone/match-core')
    parser.add_argument('--native',type=Path,default=ROOT/'build/amiga/interfaces/enhanced/baseline-rally')
    args=parser.parse_args();executable=args.executable.resolve()
    output=ROOT/'build/tests/coherent-scheduler-edges/report.json'
    transaction=ReportRun([output],'coherent-scheduler-edges','maintained-native','actual 68000 CPU only')
    try:
        paths,tools=inputs_for('build','scripts/coherent_scheduler_edges.py')
        cpu_paths,tools['machine68k']=cpu_tool_inputs()
        transaction.meta.update(files=snapshot(paths|cpu_paths),tools=tools)
        transaction.meta['environment']['PYTHONPATH']=os.environ.get('PYTHONPATH')
        manifest=compile_manifest(executable,executable.parent/'match-core.lst')
        native=args.native.resolve()
        native_manifest=compile_manifest(native,native.parent/'native.lst')
        raw=output.parent/('raw-'+transaction.meta['run_id']);raw.mkdir(parents=True,exist_ok=True)
        validation=run(executable,raw)
        validation['native_root_decline']=root_decline(native,raw)
        unvalidated=raw/'results-unvalidated.json';atomic_json(unvalidated,validation)
        transaction.finalize(output,dict(passed=True,execution='actual-68000-cpu-only',
            executable_sha256=digest(executable),native_executable_sha256=digest(native),
            validation=validation),[manifest,native_manifest],list(raw.glob('*')))
        assert status(output)['status']=='passed',status(output)
        print(json.dumps(dict(passed=True,report=str(output),sha256=digest(output))),flush=True)
    except BaseException as error:
        transaction.abort(error)
        # Preserve this failed invocation separately from the mutable latest.
        archive=output.parent/('failed-'+transaction.meta['run_id']+'.json')
        archive.write_bytes(output.read_bytes())
        raise


if __name__=='__main__':main()
