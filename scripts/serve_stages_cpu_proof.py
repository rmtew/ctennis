"""Actual CPU qualification of root-only synthetic serve stages, no native bound.

Fixtures establish serve state through actual init/select/pads/result/dispatch,
freeze and preview APIs. No intermediate expected-state writes. Frozen original
and candidate images are copied before execution; all failures are retained.
"""
import argparse,hashlib,json,shutil,traceback
from pathlib import Path
from uuid import uuid4
from build_match_core import load_image
from match_core_cpu import Core,cpu_tool_inputs
from run_shared_match_core import READONLY
from history_proof import attach,field
from run_coherent_classifier_cpu import normalized_history_pointers
from serve_stage_discovery import STAGES,registers
from native_tools import ROOT

LAST_TRIAL={}

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def qualified_manifest(role,directory):
    """Reject copied stale compile metadata before executing either image."""
    executable=directory/'match-core';listing=directory/'match-core.lst'
    manifest=json.loads((directory/'match-core.compile.json').read_text())
    declared=manifest['executable'];files=manifest['files']
    assert manifest['executable_sha256']==digest(executable),role+' compile executable identity mismatch'
    assert files[declared]==digest(executable),role+' compiled executable binding mismatch'
    assert files[declared+'.lst']==digest(listing),role+' compiled listing binding mismatch'
    checked=[]
    if role=='candidate':
        assert 'amiga/game/preview_serve_stages.s' in files,'Candidate compile omits serve stages'
        for name,sha in files.items():
            path=(ROOT/name).resolve()
            if not path.is_relative_to((ROOT/'build').resolve()):
                assert path.is_file() and digest(path)==sha,'Candidate compiled input changed: '+name
                checked.append(name)
    return dict(executable_sha256=digest(executable),listing_sha256=digest(listing),
                current_candidate_inputs_checked=checked,
                original_scope='Frozen original source bindings retained; not compared with changed current sources.')

def setup(c,clock):
    s=c.symbols;c.call_logical('game_core_init',[]);attach(c);c.call_logical('game_core_select',[0,0xace1,0])
    for tick in range(150):
        playing=field(c,'game_lifecycle')==1
        for n,a in [('game_round_poll',[]),('game_core_sample_pads',[16 if clock and playing else 0,0]),('game_core_sample_result',[0]*6)]:c.call_logical(n,a)
        phase=field(c,'game_lower_phase',1)
        if playing and field(c,'game_score_initialized',1) and ((not clock and phase==0x40) or (clock and phase==0x20 and field(c,'game_serve_clock',1)==clock)):break
        c.call_logical('game_tick_dispatch',[])
    else:raise AssertionError('No genuine requested prelaunch phase')
    c.call('game_history_freeze');assert c.cpu.r_reg(0)==1
    generation=field(c,'game_preview_generation',4)
    c.call('game_preview_request',{0:generation,1:65535,2:field(c,'game_lower_x',1),3:field(c,'game_lower_y',1)})
    assert c.cpu.r_reg(0)==1 and field(c,'game_preview_kind')==3
    generation=field(c,'game_preview_generation',4)
    for v in (0,1):
        c.call('game_preview_step_variant',{0:generation,1:1,2:v});assert c.cpu.r_reg(0)==1
        c.call('game_preview_step_variant',{0:generation,1:3,2:v});assert c.cpu.r_reg(0)==1
        assert c.mem.r16(s['game_preview_synthetic_phases']+2*v)==3
    c.clear_events();return generation

def snapshot(c):
    s=c.symbols;return {n:bytes(c.mem.r_block(s[n],s[e]-s[n])) for n,e in [('game_core_state','game_core_state_end'),('game_history_state','game_history_state_end'),('game_history_buffer','game_history_buffer_end')]}
def protect(c,saved):
    assert snapshot(c)==saved,'Canonical/history/record ownership changed at yield'
    assert field(c,'game_preview_active',1)==0 and field(c,'game_history_replaying',1)==0

def summary(c):
    s=c.symbols;hist=bytes(c.mem.r_block(s['game_history_state'],72));out=dict(history=normalized_history_pointers('game_history_state',hist,s)[0],canonical=c.state().hex(),events=c.events,preview_events=c.preview_events)
    for n,z in [('game_preview_held_state',318),('game_preview_released_state',318),('game_preview_counts',4),('game_preview_outcomes',4),('game_preview_launches',2),('game_preview_interceptions',2),('game_preview_synthetic_phases',4),('game_preview_dispatches',4),('game_preview_launch_saved',2)]:out[n]=bytes(c.mem.r_block(s[n],z)).hex()
    out['paths']=[bytes(c.mem.r_block(s['game_preview_paths']+v*513*8,c.mem.r16(s['game_preview_counts']+v*2)*8)).hex() for v in (0,1)]
    return out

def boundary(c):
    return dict(state=c.working_state().hex(),events=list(c.preview_events),registers=registers(c),history=normalized_history_pointers('game_history_state',bytes(c.mem.r_block(c.symbols['game_history_state'],72)),c.symbols)[0])
def run_trial(image,s,clock,v,staged,mode='complete',stop=0):
    global LAST_TRIAL
    ro=dict(READONLY)
    if 'game_preview_dispatch_stage_bodies' in s:ro['game_preview_dispatch_stage_bodies']=40
    LAST_TRIAL=dict(clock=clock,variant=v,staged=staged,mode=mode,stop=stop)
    with Core(image,s,readonly=ro) as c:
        g=setup(c,clock);saved=snapshot(c);before=summary(c);bodies=[];entries=[];pending=None;current=None
        LAST_TRIAL.update(bodies=bodies,entries=entries)
        bypc={s[n]:n for n in STAGES}
        def hook(pc):
            nonlocal pending,current
            c.instruction(pc)
            if pending is not None and pc==pending:
                bodies.append(dict(stage=current,**boundary(c)));pending=None;current=None
            if pc in bypc and field(c,'game_preview_active',1)==2 and current is None:
                current=bypc[pc];entries.append(dict(stage=current,registers=registers(c)));pending=c.mem.r32(c.cpu.r_sp())
        c.cpu.set_instr_hook_callback(hook);costs=[];public=[]
        LAST_TRIAL.update(costs=costs,public_yields=public)
        if staged:
            for index in range(10):
                # Poison only caller context; continuation must restore its own.
                for reg in range(15):c.cpu.w_reg(reg,(0x84371529+reg*65537+index*0x1010101)&0xffffffff)
                c.cpu.w_sr(0x2700 | index)
                costs.append(c.call('game_preview_dispatch_stage',{0:g,1:v}));assert c.cpu.r_reg(0)==1
                complete=c.cpu.r_reg(1);protect(c,saved)
                public.append(dict(index=index,complete=complete,launches=field(c,'game_preview_launches'),phase=c.mem.r16(s['game_preview_synthetic_phases']+v*2),counts=field(c,'game_preview_counts',4)))
                if index<9:assert not complete and summary(c)['game_preview_launches']==before['game_preview_launches'] and summary(c)['game_preview_counts']==before['game_preview_counts'] and public[-1]['phase']==3,'Partial logical publication'
                else:assert complete==1
                if stop and index+1==stop:
                    if mode=='mixed':costs.append(c.call('game_preview_step_variant',{0:g,1:1,2:v}));protect(c,saved)
                    elif mode=='cancel':c.call('game_preview_cancel',{0:g});assert c.cpu.r_reg(0)==1
                    elif mode=='replace':c.call('game_preview_request',{0:g,1:65535,2:field(c,'game_lower_x',1),3:field(c,'game_lower_y',1)});assert c.cpu.r_reg(0)==1
                    elif mode=='seek':c.call('game_history_seek',{0:0,1:field(c,'game_history_position',8)});assert c.cpu.r_reg(0)==1
                    if mode!='mixed':
                        assert field(c,'game_preview_dispatch_stages',4)==0
                        after=snapshot(c)
                        assert after['game_core_state']==saved['game_core_state'] and after['game_history_buffer']==saved['game_history_buffer'],'Mutation protocol changed frozen canonical/records'
                        if mode!='seek':protect(c,saved)
                        retired=summary(c)
                        c.call('game_preview_dispatch_stage',{0:g,1:v});assert c.cpu.r_reg(0)==0 and summary(c)==retired,'Retired generation resumed stage'
                    break
        else:costs.append(c.call('game_preview_step_variant',{0:g,1:1,2:v}));protect(c,saved)
        if staged and mode in ('complete','mixed'):
            assert len(bodies)==10 and [x['stage'] for x in bodies]==list(STAGES)
            for a,b in zip(bodies,entries[1:]):
                assert a['registers']['da']==b['registers']['da'] and a['registers']['sr']&31==b['registers']['sr']&31,'Continuation register/CCR loss'
        LAST_TRIAL['summary']=summary(c)
        c.audit_reads();return dict(summary=summary(c),bodies=bodies,entries=entries,costs=costs,public_yields=public,stack=c.stack_bytes)

def dispatch_identity(products):
    rows={}
    for role,(image,s) in products.items():
        with Core(image,s,readonly=READONLY) as c:
            start=s['game_tick_dispatch_body'];end=s['game_service_tick']+8
            code=bytearray(c.mem.r_block(start,end-start));offset=s['game_service_tick']-start
            size,text=c.cpu.disassemble(s['game_service_tick'])
            assert size==4 and text=='bsr     $%x'%s['game_observe_pre_tail']
            code[offset+2:offset+4]=b'\0\0'
            rows[role]=dict(start=start,bytes=end-start,masked_hex=code.hex(),allowed_operand_offset=offset+2,target='game_observe_pre_tail')
    assert rows['original']['masked_hex']==rows['candidate']['masked_hex'],'Original dispatcher byte change outside declared pre-tail call relocation'
    return rows

def interleave(image,s,staged):
    with Core(image,s,readonly=dict(READONLY,**({'game_preview_dispatch_stage_bodies':40} if staged else {}))) as c:
        g=setup(c,16);saved=snapshot(c);previous={};pending=None;owner=None
        def hook(pc):
            nonlocal pending,owner
            c.instruction(pc)
            if pending is not None and pc==pending:previous[owner]=registers(c);pending=None
            if staged and pc in [s[n] for n in STAGES] and field(c,'game_preview_active',1)==2:
                owner=field(c,'game_preview_variant',1)
                if owner in previous:
                    a=previous[owner];b=registers(c)
                    assert a['da']==b['da'] and a['sr']&31==b['sr']&31,'Interleaved branch context loss'
                pending=c.mem.r32(c.cpu.r_sp())
        c.cpu.set_instr_hook_callback(hook)
        if staged:
            for i in range(10):
                for v in (0,1):
                    for reg in range(15):c.cpu.w_reg(reg,(0x94851519+reg*0x10101+i*31+v*32769)&0xffffffff)
                    c.cpu.w_sr(0x2700|i)
                    c.call('game_preview_dispatch_stage',{0:g,1:v});assert c.cpu.r_reg(0)==1 and c.cpu.r_reg(1)==int(i==9)
                    protect(c,saved)
        else:
            for v in (0,1):c.call('game_preview_step_variant',{0:g,1:1,2:v});protect(c,saved)
        result=summary(c);result.pop('preview_events');result['branch_events']={str(k):v for k,v in c.preview_event_groups.items()}
        c.audit_reads();return result

def sentinel(image,s):
    with Core(image,s,readonly=dict(READONLY,game_preview_dispatch_stage_bodies=40)) as c:
        setup(c,16)
        # Separate declared invalid-generation fixture before tested calls.
        c.mem.w32(s['game_preview_generation'],0xffffffff);before=summary(c);owners=snapshot(c)
        c.call('game_preview_dispatch_stage_eligible',{0:0xffffffff,1:0});assert c.cpu.r_reg(0)==0
        c.call('game_preview_dispatch_stage',{0:0xffffffff,1:0});assert c.cpu.r_reg(0)==0
        assert summary(c)==before and snapshot(c)==owners;c.audit_reads()
        return dict(rejected=True,unchanged=True)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--candidate-dir',type=Path,default=ROOT/'build/standalone');args=ap.parse_args()
    out=ROOT/'build/tests/serve-stages-cpu'/uuid4().hex;out.mkdir(parents=True);rows=[]
    for role,src in [('original',ROOT/'build/tests/serve-stage-design/2274bc41c5f047828cdbb281432ff66c'),('candidate',args.candidate_dir)]:
        d=out/role;d.mkdir()
        for n in ('match-core','match-core.lst','match-core.compile.json'):shutil.copy2(src/n,d/n)
    shutil.copy2(Path(__file__),out/'serve_stages_cpu_proof.py')
    report=dict(passed=False,directory=str(out),scope=__doc__)
    try:
        cp,ci=cpu_tool_inputs();report['cpu']=ci
        paths=list(out.glob('*/*'))+[out/'serve_stages_cpu_proof.py']+[ROOT/'scripts'/n for n in ('match_core_cpu.py','match_core_capture.py','build_match_core.py','serve_stage_discovery.py','run_coherent_classifier_cpu.py','run_shared_match_core.py','history_proof.py')]+sorted(cp)
        report['bindings']={str(p):digest(p) for p in paths}
        report['compile_identity_validation']={role:qualified_manifest(role,out/role) for role in ('original','candidate')}
        products={role:load_image(out/role/'match-core') for role in ('original','candidate')}
        report['original_dispatch_byte_identity']=dispatch_identity(products)
        with Core(*products['candidate'],readonly=READONLY) as table_cpu:
            cs=products['candidate'][1];entries=[table_cpu.mem.r32(cs['game_preview_dispatch_stage_bodies']+4*i) for i in range(10)]
            assert len(set(entries))==10 and entries==[cs['game_preview_dispatch_call_%d'%i] for i in range(10)],'Stage table does not bind distinct actual call stubs'
            report['stage_table_audit']=entries
        for clock in range(17):
            for v in (0,1):
                original=run_trial(*products['original'],clock,v,False)
                candidate=run_trial(*products['candidate'],clock,v,True)
                case=dict(clock=clock,variant=v,original=original,candidate=candidate)
                name='case-%03d.json'%len(rows);(out/name).write_text(json.dumps(case,indent=2)+'\n')
                assert original['summary']==candidate['summary'],('Completed original API mismatch',clock,v)
                for a,b in zip(original['bodies'],candidate['bodies']):
                    assert {k:a[k] for k in ('stage','state','events','history')}=={k:b[k] for k in ('stage','state','events','history')},('Intermediate original boundary mismatch',clock,v,a['stage'])
                rows.append(dict(case=name,sha256=digest(out/name),passed=True))
        for v in (0,1):
            for stage in (1,4,9):
                for mode in ('mixed','cancel','replace','seek'):
                    trial=run_trial(*products['candidate'],16,v,True,mode,stage)
                    if mode=='mixed':assert trial['summary']==run_trial(*products['original'],16,v,False)['summary']
                    name='case-%03d.json'%len(rows);(out/name).write_text(json.dumps(dict(mode=mode,stage=stage,variant=v,trial=trial),indent=2)+'\n');rows.append(dict(case=name,sha256=digest(out/name),passed=True))
        a=interleave(*products['original'],False);b=interleave(*products['candidate'],True)
        assert a==b,'Interleaved original branch output mismatch'
        report['interleaved_branches']=dict(passed=True,original=a,candidate=b)
        report['sentinel_generation']=sentinel(*products['candidate'])
        report.update(passed=True,cases=rows,limits='Finite initialhumanlower serve; no upper reachability, native admission cost, A500 bus/IRQ or WCET proof. Root fairness/service needs native integration qualification.')
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,cases=len(rows),report=str(out/'report.json'))),flush=True)
    except BaseException as error:
        report.update(error=str(error),traceback=traceback.format_exc(),completed=rows,partial_trial=LAST_TRIAL);(out/'failure.json').write_text(json.dumps(report,indent=2)+'\n');print(str(out/'failure.json'),flush=True);raise
if __name__=='__main__':main()
