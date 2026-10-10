"""Actual original68000 serve boundary discovery; no build or A500 bound.

One native init/select/controls trajectory per policy establishes pre-dispatch
states. Independent runs start from those complete observed fixtures. Sequential
actual returned bodies are compared with uninterrupted original dispatch; only
presentation/audio adapter sinks are replaced by the existing CPU harness.
Costs include call-return trap; exclude root ownership, yield glue and chip waits.
"""
import argparse,hashlib,json,shutil,traceback
from pathlib import Path
from uuid import uuid4
from build_match_core import load_image
from match_core_cpu import Core,cpu_tool_inputs
from run_shared_match_core import READONLY
from history_proof import field
from native_tools import ROOT

STAGES=('game_scene_update_fields','input_update','game_score_tick','game_play_tick',
        'game_scene_finish_tick','game_observe_pre_tail','game_advance_clocks',
        'game_audio_tick','game_apply_sound','game_scene_service')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def registers(c):return dict(da=[c.cpu.r_reg(i) for i in range(15)],sr=c.cpu.r_sr())
def observed(c):return dict(state=c.state().hex(),registers=registers(c),events=list(c.events),
                           preview_events=list(c.preview_events),history=bytes(c.mem.r_block(c.symbols['game_history_state'],72)).hex())
def discover(image,s,held):
    samples=[];actions=[];launches=[]
    with Core(image,s,readonly=READONLY) as c:
        def hook(pc):
            c.instruction(pc)
            if pc==s['game_history_serve']:launches.append(dict(end=c.cpu.r_reg(7)&65535,human=c.mem.r8(s['game_play_state']+54+(c.cpu.r_reg(7)&65535))==0))
        c.cpu.set_instr_hook_callback(hook)
        for name,args in [('game_core_init',[]),('game_core_select',[0,0xace1,0])]:c.call_logical(name,args);actions.append([name,args])
        for tick in range(120):
            playing=field(c,'game_lifecycle')==1
            pads=16 if held and playing else 0
            for name,args in [('game_round_poll',[]),('game_core_sample_pads',[pads,0]),('game_core_sample_result',[0]*6)]:c.call_logical(name,args);actions.append([name,args])
            phase=field(c,'game_lower_phase',1);clock=field(c,'game_serve_clock',1)
            if field(c,'game_lifecycle')==1 and field(c,'game_core_command',1)==0 and field(c,'game_score_initialized',1) and phase in (0x40,0x20) and clock<=16:
                # Snapshot actual fixture once for each independent boundary trial.
                samples.append(dict(tick=tick,phase=phase,serve_clock=clock,held=held,state=c.state(),registers=registers(c),owned=[(a,bytes(c.mem.r_block(a,b-a))) for a,b in c.mutable_regions],input_stream=list(actions)))
            c.call_logical('game_tick_dispatch',[]);actions.append(['game_tick_dispatch',[]])
            if any(x['human'] for x in launches):break
            if not held and len(samples)>=3:break
        c.audit_reads()
    return samples,launches

def execute(image,s,sample,split):
    with Core(image,s,initial=sample['state'],readonly=READONLY) as c:
        for a,b in sample['owned']:c.mem.w_block(a,b)
        for i,v in enumerate(sample['registers']['da']):c.cpu.w_reg(i,v)
        c.cpu.w_sr(sample['registers']['sr']);c.clear_events()
        boundaries=[];cycles=[]
        if split:
            for stage in STAGES:
                cycles.append(c.call(stage));boundaries.append(dict(stage=stage,**observed(c)))
        else:
            pending=None;index=0
            def hook(pc):
                nonlocal pending,index
                c.instruction(pc)
                if pending is not None and pc==pending:
                    boundaries.append(dict(stage=STAGES[index],**observed(c)));index+=1;pending=None
                if index<len(STAGES) and pc==s[STAGES[index]]:
                    pending=c.mem.r32(c.cpu.r_sp())
            c.cpu.set_instr_hook_callback(hook);cycles.append(c.call('game_tick_dispatch_body'))
            assert len(boundaries)==len(STAGES),('Missing actual returned boundaries',len(boundaries),pending,index)
        c.audit_reads();return dict(final=observed(c),boundaries=boundaries,cycles=cycles,stack=c.stack_bytes)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source-dir',type=Path,default=ROOT/'build/tests/serve-stage-design/2274bc41c5f047828cdbb281432ff66c',help='Explicit frozen original product/listing/compile directory; never rebuild')
    source=parser.parse_args().source_dir
    out=ROOT/'build/tests/serve-stage-design'/uuid4().hex;out.mkdir(parents=True)
    for name in ('match-core','match-core.lst','match-core.compile.json'):shutil.copy2(source/name,out/name)
    shutil.copy2(Path(__file__),out/'serve_stage_discovery.py')
    rows=[];report=dict(passed=False,directory=str(out),scope=__doc__)
    try:
        cpu_paths,cpu_identity=cpu_tool_inputs();image,s=load_image(out/'match-core')
        report.update(source_directory=str(source),bindings={str(p):sha(p) for p in [out/n for n in ('match-core','match-core.lst','match-core.compile.json','serve_stage_discovery.py')]+[ROOT/'scripts'/n for n in ('build_match_core.py','match_core_cpu.py','run_shared_match_core.py','history_proof.py')]+sorted(cpu_paths)},cpu=cpu_identity)
        for held in (False,True):
            samples,launches=discover(image,s,held)
            assert samples,('No actual initialhumanserve samples',held)
            for sample in samples:
                original=execute(image,s,sample,False);split=execute(image,s,sample,True)
                state_events=lambda x:{k:x[k] for k in ('state','events','preview_events','history')}
                checks=dict(final=state_events(original['final'])==state_events(split['final']),
                    boundaries=all(state_events(a)==state_events(b) for a,b in zip(original['boundaries'],split['boundaries'])),
                    registers=all(a['registers']==b['registers'] for a,b in zip(original['boundaries'],split['boundaries'])))
                raw=dict(fixture={k:v for k,v in sample.items() if k not in ('state','owned')},fixture_state=sample['state'].hex(),original=original,sequential=split,checks=checks)
                name='case-%04d.json'%len(rows);(out/name).write_text(json.dumps(raw,indent=2)+'\n')
                rows.append(dict(case=name,sha256=sha(out/name),held=held,tick=sample['tick'],phase=sample['phase'],serve_clock=sample['serve_clock'],checks=checks,original_cycles=original['cycles'][0],stage_call_cycles=dict(zip(STAGES,split['cycles']))))
                assert all(checks.values()),('Actual original/sequential mismatch',name,checks)
        report.update(passed=True,cases=rows,upper_end='Not reached by declared initialoneplayer start/control trajectories; no upper fixture invented.',cost_limits='Cycles include actual CPU harness return trap; no native owner/yield/service/CCR-save overhead or A500 contention. No WCET or admitted reservation.',launches=launches)
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,cases=len(rows),report=str(out/'report.json'))),flush=True)
    except BaseException as error:
        report.update(error=str(error),traceback=traceback.format_exc(),completed=rows)
        (out/'failure.json').write_text(json.dumps(report,indent=2)+'\n');print(str(out/'failure.json'),flush=True);raise
if __name__=='__main__':main()
