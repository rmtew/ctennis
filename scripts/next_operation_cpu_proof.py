"""Actual root routing over retained query-work boundaries, no hardware sinks.

Declared scheduler/branch metadata is initialized once per fixture. A4000E gap
cannot grant endpoint or outgoing work, so actual admission refuses before
clock/MMIO. Then actual cancel/invalidate APIs retire the tested generation.
This is not physical timing, native reachability or universal deadline proof.
"""
import itertools,json,os,hashlib
from pathlib import Path
from uuid import uuid4
from run_coherent_classifier_cpu import seed,normalized_history_pointers
from match_core_cpu import Core,cpu_tool_inputs
from history_proof import field
from coherent_scheduler_proof import raw_json
from run_shared_match_core import READONLY
from native_evidence import ReportRun,snapshot,inputs_for,compile_manifest,atomic_json,digest
from native_tools import ROOT

def trial(seed_data,variant,launch,phase,attempted,ready,outcome,stage,route):
    image,s,initial,owned,generation=seed_data
    with Core(image,s,initial=initial,readonly=dict(READONLY,ui_paused=1,
            simulation_interval=4,simulation_phase=4,blank_seen=1)) as c:
        for address,data in owned:c.mem.w_block(address,data)
        c.mutable_regions.append((s['tutorial_state'],s['tutorial_state_end']))
        c.mem.w_block(s['tutorial_state'],bytes(s['tutorial_state_end']-s['tutorial_state']))
        def write(name,width,value):c.mem.w_block(s[name],value.to_bytes(width,'big'))
        # Single declared initial fixture; private318 derives from actual APIs.
        for name,width,value in (('tutorial_active',1,255),('ui_paused',1,1),
            ('tutorial_work_pending',1,1),('tutorial_generation',4,generation),
            ('tutorial_presentation_generation',4,generation),('tutorial_active_variant',1,variant),
            ('simulation_interval',4,10000),('simulation_phase',4,6000),
            ('blank_seen',1,0),('game_preview_status',2,3),('game_preview_primed_mask',2,3),
            ('tutorial_animation_index',2,2)):
            write(name,width,value)
        c.mem.w_block(s['game_preview_launches'],b'\xff\xff')
        for name,width,value in (('game_preview_launch_saved',1,launch),
            ('game_preview_flight_phases',2,phase),('game_preview_endpoint_attempted',1,attempted),
            ('game_preview_endpoint_ready',1,ready),('game_preview_outcomes',2,outcome),
            ('game_preview_counts',2,10 if ready else 1)):
            c.mem.w_block(s[name]+variant*width,value.to_bytes(width,'big'))
        c.mem.w16(s['game_preview_query_workspaces']+variant*48+36,stage)
        route_fields={'generation':('tutorial_generation',4,generation-1),
            'presentation':('tutorial_presentation_generation',4,generation-1),
            'variant':('tutorial_active_variant',1,255),'seek-pending':('game_history_seek_status',2,1),
            'seek-ready':('game_history_seek_status',2,2),'seek-active':('game_history_seek_active',1,1),
            'replaying':('game_history_replaying',1,1),'owner':('game_preview_active',1,2),
            'producer':('tutorial_placement_dirty',1,1),'menu':('tutorial_menu',1,1)}
        if route in route_fields:write(*route_fields[route])
        owners={n:bytes(c.mem.r_block(s[n],s[e]-s[n])) for n,e in (
            ('game_core_state','game_core_state_end'),('game_history_state','game_history_state_end'),
            ('game_history_buffer','game_history_buffer_end'),('game_preview_storage','game_preview_storage_end'))}
        queries=[];classes=[];hits=[]
        forbidden={s[n]:n for n in ('game_preview_dispatch','game_ball_tick','game_preview_step_variant',
            'game_preview_endpoint_step','account_sim_timer','read_presentation_line')}
        def observe(pc):
            c.instruction(pc)
            if pc==s['game_preview_endpoint_pending']:queries.append(c.cpu.r_reg(1))
            if pc==s['tutorial_background_class']:classes.append(field(c,'tutorial_job_variant'))
            if pc in forbidden:hits.append(forbidden[pc])
        c.cpu.set_instr_hook_callback(observe);events=list(c.events);preview_events=list(c.preview_events)
        cycles=[];states=[]
        for _ in range(3):
            cycles.append(c.call('tutorial_background'))
            assert not hits,('Unadmitted work or hardware',hits)
            assert all(bytes(c.mem.r_block(s[n],len(v)))==v for n,v in owners.items())
            assert c.events==events and c.preview_events==preview_events
            states.append(bytes(c.mem.r_block(s['tutorial_state'],s['tutorial_state_end']-s['tutorial_state'])).hex())
        # Real mutation APIs, without rewriting scheduler state after execution.
        c.call('game_preview_cancel',{0:generation})
        after_cancel=bytes(c.mem.r_block(s['game_preview_storage'],s['game_preview_storage_end']-s['game_preview_storage']))
        cycles.append(c.call('tutorial_background'))
        assert bytes(c.mem.r_block(s['game_preview_storage'],len(after_cancel)))==after_cancel and not hits
        c.call('game_preview_invalidate')
        after_invalidate=bytes(c.mem.r_block(s['game_preview_storage'],len(after_cancel)))
        cycles.append(c.call('tutorial_background'))
        assert bytes(c.mem.r_block(s['game_preview_storage'],len(after_invalidate)))==after_invalidate and not hits
        assert all(bytes(c.mem.r_block(s[n],len(v)))==v for n,v in owners.items() if n!='game_preview_storage')
        c.audit_reads()
        normalized={n:(normalized_history_pointers(n,v,s)[0] if n in ('game_history_state','game_preview_storage') else v.hex()) for n,v in owners.items()}
        return dict(states=states,classes=classes,cancel=normalized_history_pointers('game_preview_storage',after_cancel,s)[0],
            invalidate=normalized_history_pointers('game_preview_storage',after_invalidate,s)[0],
            events=events,preview_events=preview_events,input_owner_hashes={n:hashlib.sha256(bytes.fromhex(v)).hexdigest() for n,v in normalized.items()}),dict(cycles=cycles,queries=queries,stack=c.stack_bytes)

def main():
    out=ROOT/'build/tests/next-operation-cpu'/uuid4().hex;out.mkdir(parents=True)
    report_path=out/'report.json';tx=ReportRun([report_path],'next-operation-cpu','maintained-native','actual68000 routing only')
    products={'original':ROOT/'build/tests/next-operation-pr49/baseline-rally',
        'reference':ROOT/'build/tests/next-operation-padded-pr49/baseline-rally',
        'candidate':ROOT/'build/amiga/interfaces/enhanced/baseline-rally'}
    rows=[]
    try:
        paths,tools=inputs_for('build','scripts/next_operation_cpu_proof.py');cpu_paths,tools['machine68k']=cpu_tool_inputs()
        tx.meta.update(files=snapshot(paths|cpu_paths),tools=tools,runner='scripts/next_operation_cpu_proof.py',actual_execution='actual68000 CPU',environment={'PYTHONPATH':os.environ.get('PYTHONPATH')})
        seeds={n:seed(p) for n,p in products.items()}
        descriptors=list(itertools.product((0,1),(0,255),(0,3,4,255,256),(0,255),(0,255),(0,1),(0,1,2,3),('normal',)))
        descriptors +=[(v,255,4,0,0,0,0,r) for v in (0,1) for r in ('generation','presentation','variant','seek-pending','seek-ready','seek-active','replaying','producer','menu')]
        for index,descriptor in enumerate(descriptors):
            results={};measurements={}
            for n,sd in seeds.items():results[n],measurements[n]=trial(sd,*descriptor)
            raw_json(out/f'case-{index:04}',dict(descriptor=descriptor,results=results,measurements=measurements))
            assert results['original']==results['reference']==results['candidate'],('Routing/output/state mismatch',descriptor)
            assert measurements['original']['cycles']==measurements['reference']['cycles'],('Padded reference cost differs',descriptor)
            assert len(measurements['candidate']['queries'])<=len(measurements['reference']['queries'])
            rows.append(dict(descriptor=descriptor,passed=True,measurements=measurements))
        compiled=[compile_manifest(p,p.parent/('native.lst')) for p in products.values()]
        tx.finalize(report_path,dict(passed=True,cases=rows,products={n:dict(path=str(p),sha256=digest(p)) for n,p in products.items()},scope=__doc__),compiled,list(out.glob('*.gz')))
        print(json.dumps(dict(passed=True,cases=len(rows),report=str(report_path))))
    except BaseException as error:
        atomic_json(out/'failure.json',dict(error=str(error),completed=rows));tx.abort(error);raise

if __name__=='__main__':main()
