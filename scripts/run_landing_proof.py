"""Differential proof of a test-only native intrinsic query; no match oracle."""
import hashlib
import itertools
import json
import os
from collections import Counter,defaultdict
from pathlib import Path
from landing_cases import CASES
from build_landing_prototype import build
from build_match_core import load_image
from check_shared_core_bytes import normalized
from match_core_cpu import Core,cpu_tool_inputs
from native_evidence import ReportRun,atomic_json,digest,python_inputs,snapshot,inputs_for,status
from native_tools import ROOT
from prove_ball_queries import Packet,first_event,point
from prove_ball_query_forms import landing_guard,first_ge
from run_shared_match_core import READONLY

REASONS={0:'accepted',1:'negative-height',2:'not-active',3:'low-speed-or-negative-zero',
    4:'special-net-reflection',5:'step-wrap',6:'displacement-overflow',7:'height-factor-wrap',
    8:'height-quotient-overflow',9:'screen-clamp-or-wrap',10:'court-x-bound',
    11:'nonzero-phase',12:'defensive-bracket-miss',13:'court-y-bound',14:'preexisting-stopping-flags'}
EVENTS={'none':0,'launch':1,'inactive':2,'inactive-out':2,'bounce':3,'net-reflect':4,'outside':5}
PARAMS=('velocity_x','velocity_y','velocity_z','base_x','base_y','base_screen_y','flight','contact','step')
CAP=256


def grid():
    for vx,vy,z,bx,h,by in itertools.product((0,5,127,128,133,255),
            (4,7,17,31,63,127,132,135,145,159,191,255),(0,4,32,64,128,192,255),
            (32,64,128,231),(0,1,2,8,24,64,128),(32,64,110,184,203)):
        if by>=h:yield (vx,vy,z,bx,by,by-h,64,0,0)


def boundary_cases():
    # All phase-wrap Y bytes, flight/contact combinations and boundary priority.
    for vy,flight,contact,bx,by,screen in itertools.product(range(256),
            (0,32,64,72,128,192),(0,1,2,4,7,255),(31,32,231,232),
            (3,4,107,108,110,112,113,203,204),(0,110,255)):
        yield (255,vy,255,bx,by,screen,flight,contact,255)
    # Negative H, nonzero phase, negative zero and height-wrap domain.
    for phase,vy,z,by,screen in itertools.product((0,1,127,254),(0,3,4,128,132,255),
            (0,127,255),(0,4,100,203,255),(0,4,100,203,255)):
        yield (255,vy,z,128,by,screen,64,0,phase)


def initial(packet,args,poison=165):
    state=bytearray([poison]*318)
    for name,value in zip(PARAMS,args):packet.set(state,name,value)
    # Pending-launch bytes are independent initial fixture parameters.
    for name,value in zip(('launch_x','launch_y','launch_z','launch_screen_y','launch_base_x','launch_base_y'),args[:6]):
        packet.set(state,name,value)
    return bytes(state)


def expected_reason(args):
    vx,vy,z,bx,by,screen,flight,contact,phase=args
    if contact&0x8b:return 'preexisting-stopping-flags'
    if by<screen:return 'negative-height'
    if not flight&64 or flight&128:return 'not-active'
    if phase:return 'nonzero-phase'
    return landing_guard(vx,vy,z,bx,by,screen,flight,contact)[1]


def reference(cpu,packet,state):
    cpu.mem.w_block(cpu.start,state)
    costs=0
    for steps in range(1,CAP+1):
        current=cpu.state()
        p=packet.evaluate(current)
        kind=first_event(packet.get(current,'velocity_y'),packet.get(current,'flight'),packet.get(current,'contact'),p)
        costs+=cpu.call('game_ball_tick',{12:packet.play,13:cpu.start})
        if kind!='none':return cpu.state(),EVENTS[kind],steps,costs
    return cpu.state(),0,CAP,costs


def check(cpu,packet,args,trace=False,state_override=None,sr=None):
    state=initial(packet,args) if state_override is None else state_override
    cpu.clear_events()
    expected,event,steps,before=reference(cpu,packet,state)
    private=cpu.symbols['game_preview_held_state']
    cpu.mem.w_block(private,state)
    owners=bytes(cpu.mem.r_block(cpu.symbols['game_preview_released_state'],318))
    history=bytes(cpu.mem.r_block(cpu.symbols['game_history_state'],72))
    preserved={r:(0x965aa569^r*0x1010101)&0xffffffff for r in range(4,15)}
    preserved[13]=private
    cpu.writes.clear()
    cpu.cpu.w_sr(0x2700 | ((sum(args)&31) if sr is None else sr))
    incoming={r:(0xfedcba98 ^ (r+1)*0x1234567 ^ sum(args))&0xffffffff for r in range(4)}
    after=cpu.call('landing_query',{**incoming,**preserved})
    actual=bytes(cpu.mem.r_block(private,318))
    outputs=[cpu.cpu.r_reg(r) for r in range(4)]
    assert actual==expected,('state',args,outputs)
    assert outputs[:2]==[event,steps],('event/steps',args,outputs,event,steps)
    assert REASONS[outputs[2]]==expected_reason(args),('guard',args,outputs,expected_reason(args))
    assert outputs[3]<=6 and (outputs[2]!=0 or 1<=outputs[3]<=6)
    assert all(cpu.cpu.r_reg(r)==v for r,v in preserved.items()),('ABI',args)
    assert cpu.state()==expected and bytes(cpu.mem.r_block(cpu.symbols['game_preview_released_state'],318))==owners
    assert bytes(cpu.mem.r_block(cpu.symbols['game_history_state'],72))==history
    assert not cpu.events and not cpu.preview_events and not cpu.seek_events
    if trace:
        assert cpu.writes<=set(range(private,private+318)),('out-of-owner',args)
        cpu.audit_reads()
    return outputs[2],outputs[3],before,after,steps,event


def run():
    directory=ROOT/'build/tests/guarded-landing-cpu';directory.mkdir(parents=True,exist_ok=True)
    output=directory/'report.json'
    tx=ReportRun([output],'cpu-proof','guarded-landing-prototype','Intrinsic ball only; complete match semantics unchanged')
    try:
        executable,listing,manifest=build()
        base=Path(os.environ['CTENNIS_LANDING_BASELINE_ROOT'])
        product=base/'build/standalone/match-core'
        assert digest(product)=='2b82218b3eb31909e3d694cd7bf4fae5dcc34ca5b62e43687ed47029d96e672b'
        audit=normalized(executable,listing)
        assert audit==normalized(product,product.with_suffix('.lst'))
        assert (len(audit[0]),audit[1],audit[2],hashlib.sha256(audit[0]).hexdigest())==(17606,7,14,
            '99c543c170c036137be81d07ebd30b522ef3abdff04bd7b1af38f00047bb99d5')
        cpu_paths,cpu_tool=cpu_tool_inputs()
        paths,tools=inputs_for('build','scripts/run_landing_proof.py')
        tools['machine68k']=cpu_tool
        tx.meta.update(files=snapshot(set(paths)|set(cpu_paths)|
            {ROOT/'scripts/fixtures/guarded_landing.s',executable,listing,product}),
            tools=tools,cpu_tool=cpu_tool)
        tx.meta['environment'].update(CTENNIS_LANDING_BASELINE_ROOT=str(base),PYTHONPATH=os.environ.get('PYTHONPATH'),CTENNIS_LANDING_RECORDING_ROOT=os.environ.get('CTENNIS_LANDING_RECORDING_ROOT'))
        image,symbols=load_image(executable)
        packet=Packet(symbols);counts=Counter();costs=defaultdict(list);max_checks=0
        with Core(image,symbols,readonly=READONLY) as cpu:
            # Root exhaustiveness is independent of the fixture flight grid.
            cpu.cpu.set_instr_hook_callback(None);cpu.mem.set_trace_mode(False)
            for h,z in itertools.product(range(256),repeat=2):
                for extra in (1,63):
                    threshold=32*h+extra
                    cpu.call('landing_root',{0:threshold,1:z})
                    assert cpu.cpu.r_reg(0)==first_ge(z,threshold),(h,z,extra)
            roots=dict(height_z_pairs=65536,root_calls=131072,eight_decisions=True)
            cpu.cpu.set_instr_hook_callback(cpu.instruction);cpu.mem.set_trace_mode(True)
            probes=[args for name,args in CASES]
            for args in probes:check(cpu,packet,args,trace=True)
            # All incoming CCR values for each declared benchmark fixture.
            for incoming_ccr in range(32):
                for args in probes:
                    check(cpu,packet,args,trace=True,sr=incoming_ccr)
            cpu.cpu.set_instr_hook_callback(None);cpu.mem.set_trace_mode(False)
            for label,cases in [('isolated-grid',grid()),('phase-wrap-and-boundaries',boundary_cases()),('declared-native-fixtures',probes)]:
                total=0
                for args in cases:
                    reason,checks,before,after,steps,event=check(cpu,packet,args)
                    counts[(label,REASONS[reason])]+=1;total+=1;max_checks=max(max_checks,checks)
                    costs[REASONS[reason]].append((before,after,steps))
                assert total>0
                print(json.dumps(dict(stage=label,cases=total)),flush=True)
        retained=[]
        recording_root=Path(os.environ['CTENNIS_LANDING_RECORDING_ROOT'])
        hashes={'pal':'19d37f99ae8a68bdf90613dacb41e9feb39d5bd43486b9733ab04713b5f46fab',
                'ntsc':'aa20c2a7ae6bb624b5f0c425fe6108ebe82afe1166a19c4f64946fce11b41024'}
        for region,sha in hashes.items():
            path=recording_root/'build/tests'/('private-state-retained-'+region)/'observations-unvalidated.json'
            assert digest(path)==sha
            tx.meta['files'][str(path)]=sha
            recording=json.loads(path.read_text())[0];starts={};region_counts=Counter()
            with Core(image,symbols,readonly=READONLY,poison=0x5a) as cpu:
                original=cpu.instruction
                def hook(pc):
                    original(pc)
                    if pc==symbols['game_advance_ball'] and packet.get(cpu.state(),'step')==0:
                        state=cpu.state();args=tuple(packet.get(state,n)for n in PARAMS)
                        starts.setdefault(args,state)
                cpu.cpu.set_instr_hook_callback(hook)
                cpu.call_logical('game_core_init',[])
                for index,(name,args) in enumerate(recording['stream'],1):
                    cpu.call_logical(name,args)
                    if index==recording['selection']:assert cpu.state().hex()==recording['selected']
                cpu.audit_reads();cpu.cpu.set_instr_hook_callback(cpu.instruction)
                for args,state in starts.items():
                    reason,checks,before,after,steps,event=check(cpu,packet,args,trace=True,state_override=state)
                    region_counts[REASONS[reason]]+=1
            retained.append(dict(region=region,logical_operations=len(recording['stream']),
                unique_phase_zero_tuples=len(starts),guard_counts=dict(region_counts),input_sha256=sha))
        summaries={name:dict(cases=len(rows),reference_min=min(x[0]for x in rows),reference_max=max(x[0]for x in rows),
            query_min=min(x[1]for x in rows),query_max=max(x[1]for x in rows),
            minimum_saved=min(x[0]-x[1]for x in rows),maximum_saved=max(x[0]-x[1]for x in rows),
            faster_cases=sum(y<x for x,y,n in rows),slower_cases=sum(y>x for x,y,n in rows))for name,rows in costs.items()}
        report=dict(passed=True,scope='Ball-only fixed segment; no full-match fast-forward or preview endpoint replacement',
            production_core_unchanged=True,normalized_core_bytes=len(audit[0]),query_code_bytes=symbols['landing_query_end']-symbols['landing_query_begin'],
            query_static_data_bytes=0,query_frame_bytes=48,query_saved_register_bytes=44,
            maximum_point_checks=max_checks,fallback_cap=CAP,trace_probes=len(probes),
            exhaustive_access_trace=False,counts={label:{reason:n for (group,reason),n in counts.items()if group==label}for label in ('isolated-grid','phase-wrap-and-boundaries','declared-native-fixtures')},
            roots=roots,retained=retained,incoming_ccr_fixture_calls=32*len(probes),cpu_costs=summaries,executable_sha256=digest(executable))
        tx.finalize(output,report,compiled=[manifest]);assert status(output)['status']=='passed',status(output);print(json.dumps(dict(passed=True,report=str(output))),flush=True)
    except BaseException as error:
        tx.abort(error);raise


if __name__=='__main__':run()
