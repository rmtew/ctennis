"""Actual cooperative endpoint equivalence to an immutable old executable.

The new synchronous entry drives the new stages and is never the oracle.
Inputs are actual old-core launch snapshots or once-declared ball guard fixtures.
"""
from pathlib import Path

from build_match_core import load_image
from coherent_scheduler_proof import raw_json
from history_proof import field, seek
from landing_try_proof import corpus
from match_core_cpu import Core
from native_evidence import digest
from predictor_proof import discover
from preview_proof import fixture, protected, call_checked, block, point
from run_shared_match_core import READONLY

OLD_SHA='b08bdb39bde02bfe3b47d515dccdf7084ec407ff3af4f151307c8abad72e8eaa'


def helper(executable,row,staged,poison,ccr):
    image,s=load_image(executable)
    with Core(image,s,initial=bytes([poison^255])*318,poison=poison,readonly=READONLY) as cpu:
        target=s['game_preview_endpoint_scratch']
        workspace=s.get('game_preview_query_workspaces',0)
        cpu.mem.w_block(target,row['state'])
        if staged:cpu.mem.w_block(workspace,bytes([poison])*48)
        canonical=cpu.state();cpu.writes.clear()
        stages=[];roots=decisions=advances=0;root_decisions=[]
        def observe(pc):
            nonlocal roots,decisions,advances
            cpu.instruction(pc)
            if pc==s['landing_root']:roots+=1;root_decisions.append(0)
            if staged and pc==s['landing_root']+8:decisions+=1;root_decisions[-1]+=1
            if pc==s['game_advance_ball']:advances+=1
        cpu.cpu.set_instr_hook_callback(observe)
        def call(name):
            preserved={r:(0x965aa569^r*0x1010101^poison*0x10101)&0xffffffff for r in range(4,15)}
            preserved[13]=target
            if staged:preserved[11]=workspace
            registers={r:(0xfedcba98^r*0x1234567^poison)&0xffffffff for r in range(4)}
            before=cpu.mem.r16(workspace+36) if staged else None
            counts=(roots,decisions,advances)
            cpu.cpu.w_sr(0x2700|ccr)
            cycles=cpu.call(name,{**registers,**preserved})
            assert all(cpu.cpu.r_reg(r)==v for r,v in preserved.items()),(row['name'],name,'preserved ABI')
            assert cpu.state()==canonical,(row['name'],'canonical isolation')
            values=[cpu.cpu.r_reg(r) for r in range(4)]
            record=dict(api=name,cycles=cycles,result=values,before=before,
                roots=roots-counts[0],decisions=decisions-counts[1],advances=advances-counts[2],
                full=bytes(cpu.mem.r_block(target,318)).hex(),events=list(cpu.events),
                preview_events=list(cpu.preview_events),seek_events=list(cpu.seek_events))
            if staged:
                record.update(after=cpu.mem.r16(workspace+36),cursor=cpu.mem.r16(workspace+38),
                    workspace=bytes(cpu.mem.r_block(workspace,48)).hex())
                assert record['decisions']==record['roots']*8,(row['name'],'root decision bound')
                assert all(count==8 for count in root_decisions[counts[0]:]),(row['name'],'individual root decision bound')
                assert record['advances']<=1,(row['name'],'candidate stage executes multiple advances')
                if name=='landing_try_prepare':assert record['advances']==0
                if before==1:assert record['advances']==0
                if before==2:assert record['advances']==1
            stages.append(record)
            return values
        if staged:
            result=call('landing_try_prepare')
            for _ in range(10):
                if result[0]!=4:break
                result=call('landing_try_step')
            assert result[0] in (0,3),(row['name'],'stage cap')
            final=bytes(cpu.mem.r_block(target,318)).hex()
            saved_workspace=bytes(cpu.mem.r_block(workspace,48))
            repeat=call('landing_try_step')
            assert repeat==result and bytes(cpu.mem.r_block(target,318)).hex()==final
            assert bytes(cpu.mem.r_block(workspace,48))==saved_workspace
        else:
            result=call('landing_try_fast')
            final=bytes(cpu.mem.r_block(target,318)).hex()
        allowed=set(range(target,target+318))
        if staged:allowed.update(range(workspace,workspace+48))
        assert cpu.writes<=allowed,(row['name'],'out-of-owner writes')
        if result[0]==0:assert final==row['state'].hex(),(row['name'],'rejection rollback')
        assert cpu.visits.get(s['game_ball_tick'],0)==0,'Helper invoked sequential fallback'
        cpu.audit_reads()
        return dict(result=result,full=final,events=list(cpu.events),preview_events=list(cpu.preview_events),
            seek_events=list(cpu.seek_events),stages=stages,stack=cpu.stack_bytes)


def endpoint_call(cpu,args,saved):
    """Poison every non-argument register; public query preserves D1..A6."""
    registers={r:(0x965aa569^r*0x1010101)&0xffffffff for r in range(1,15)}
    registers.update(args)
    preserved={r:registers[r] for r in range(1,15)}
    cycles=call_checked(cpu,'game_preview_endpoint_step',registers,saved)
    assert all(cpu.cpu.r_reg(r)==v for r,v in preserved.items()),'Endpoint stage API ABI'
    return cycles


def invalid_stages(executable,origin,raw):
    image,s=load_image(executable);rows=[]
    for stage in (0,5,65535):
        with Core(image,s,initial=bytes([0x5a])*318,readonly=READONLY) as cpu:
            target=s['game_preview_endpoint_scratch'];workspace=s['game_preview_query_workspaces']
            cpu.mem.w_block(target,origin)
            cpu.mem.w_block(workspace,bytes([0x96])*48);cpu.mem.w16(workspace+36,stage)
            before=bytes(cpu.mem.r_block(workspace,48));canonical=cpu.state();cpu.writes.clear()
            cpu.call('landing_try_step',{13:target,11:workspace})
            values=[cpu.cpu.r_reg(r) for r in range(4)]
            assert values==[0,0,16,0]
            assert bytes(cpu.mem.r_block(workspace,48))==before and bytes(cpu.mem.r_block(target,318))==origin
            assert cpu.state()==canonical and not cpu.writes
            cpu.audit_reads();rows.append(dict(stage=stage,passed=True,result=values))
    raw_json(raw/'invalid-stages.json',rows)
    return rows


def setup(cpu,case):
    fixture(cpu,seed=case['seed'],dispatches=case['ticks'])
    cpu.call('game_history_freeze');seek(cpu,case['selected'])
    generation=field(cpu,'game_preview_generation',4)
    cpu.call('game_preview_request',{0:generation,1:0xfffe,2:111,3:153})
    assert cpu.cpu.r_reg(0)==1
    return generation+1


def endpoint_api(new,old,accepted,rejected,raw):
    image,s=load_image(new);case=discover(image,s,0xace1)[0];results=[]
    expected=[helper(old,row,False,0xa5,0) for row in (accepted,rejected)]
    for order in ((0,1),(1,0)):
        with Core(image,s,poison=0x96 if order[0] else 0xa5,readonly=READONLY) as cpu:
            generation=setup(cpu,case)
            for name,value in (('game_preview_status',3),('game_preview_primed_mask',3)):
                cpu.mem.w16(s[name],value)
            cpu.mem.w_block(s['game_preview_outcomes'],bytes(4))
            cpu.mem.w_block(s['game_preview_launch_saved'],b'\xff\xff')
            cpu.mem.w_block(s['game_preview_endpoint_attempted'],bytes(2))
            cpu.mem.w_block(s['game_preview_endpoint_ready'],bytes(2))
            cpu.mem.w_block(s['game_preview_endpoint_reasons'],bytes(4))
            for variant,row in enumerate((accepted,rejected)):
                cpu.mem.w_block(s['game_preview_launch_states']+variant*318,row['state'])
                cpu.mem.w16(s['game_preview_flight_phases']+variant*2,4)
                cpu.mem.w_block(s['game_preview_query_workspaces']+variant*48,bytes([0x96])*48)
                cpu.mem.w16(s['game_preview_query_workspaces']+variant*48+36,0)
            saved=protected(cpu)
            dense=block(cpu,'game_preview_paths','game_preview_storage_end')
            states=[bytes(cpu.mem.r_block(s[n],318)) for n in ('game_preview_held_state','game_preview_released_state')]
            rows=[];done=set()
            for index in range(24):
                variant=order[index%2]
                if variant in done:variant=1-variant
                before_compat=bytes(cpu.mem.r_block(s['game_preview_endpoint_scratch'],318))
                cycles=endpoint_call(cpu,{0:generation,1:variant},saved)
                assert cpu.cpu.r_reg(0)==1
                stage=cpu.mem.r16(s['game_preview_query_workspaces']+variant*48+36)
                attempted=cpu.mem.r8(s['game_preview_endpoint_attempted']+variant)
                reason=cpu.mem.r16(s['game_preview_endpoint_reasons']+variant*2)
                ready=cpu.mem.r8(s['game_preview_endpoint_ready']+variant)
                if stage in (1,2):
                    assert (attempted,reason,ready)==(0,0,0),'Partial query published result'
                    assert bytes(cpu.mem.r_block(s['game_preview_endpoint_scratch'],318))==before_compat
                else:
                    assert stage in (3,4) and attempted
                    assert reason==expected[variant]['result'][2]
                    actual=bytes(cpu.mem.r_block(s['game_preview_query_states']+variant*318,318)).hex()
                    assert actual==expected[variant]['full'],'Terminal query full-state mismatch'
                    assert bytes(cpu.mem.r_block(s['game_preview_endpoint_scratch'],318)).hex()==actual
                    accepted_result,phase,_,_=expected[variant]['result']
                    should_ready=accepted_result==3 and phase>4
                    assert bool(ready)==should_ready,'Terminal readiness differs from frozen result'
                    if should_ready:
                        assert not reason
                        assert cpu.mem.r16(s['game_preview_endpoint_phases']+variant*2)==phase
                        frozen=bytes.fromhex(expected[variant]['full'])
                        outcome=3 if frozen[s['game_contact']-s['game_core_state']]&0x88 else 1
                        assert cpu.mem.r16(s['game_preview_endpoint_outcomes']+variant*2)==outcome
                        assert bytes(cpu.mem.r_block(s['game_preview_endpoints']+variant*8,8))==point(frozen,s)
                    else:
                        assert cpu.mem.r16(s['game_preview_endpoint_phases']+variant*2)==0
                        assert cpu.mem.r16(s['game_preview_endpoint_outcomes']+variant*2)==0
                        assert bytes(cpu.mem.r_block(s['game_preview_endpoints']+variant*8,8))==bytes(8)
                    done.add(variant)
                assert dense==block(cpu,'game_preview_paths','game_preview_storage_end')
                assert states==[bytes(cpu.mem.r_block(s[n],318)) for n in ('game_preview_held_state','game_preview_released_state')]
                rows.append(dict(variant=variant,stage=stage,attempted=attempted,ready=ready,reason=reason,cycles=cycles))
                if len(done)==2:break
            assert done=={0,1}
            before=block(cpu,'game_preview_storage','game_preview_storage_end')
            for variant in (0,1):
                endpoint_call(cpu,{0:generation,1:variant},saved)
                assert cpu.cpu.r_reg(0)==0
            assert block(cpu,'game_preview_storage','game_preview_storage_end')==before
            cpu.audit_reads()
            result=dict(passed=True,order=order,rows=rows,stack=cpu.stack_bytes)
            raw_json(raw/('endpoint-api-'+str(order[0])+'.json'),result);results.append(result)
    return results


def retirements(new,accepted,raw):
    """Each ownership transition gets a fresh, once-initialized query fixture."""
    image,s=load_image(new);case=discover(image,s,0xace1)[0];rows=[]
    for variant in (0,1):
        for retire in ('replacement','cancel','seek','resume','variant-selection','synchronous'):
            with Core(image,s,readonly=READONLY) as cpu:
                generation=setup(cpu,case)
                cpu.mem.w16(s['game_preview_status'],3);cpu.mem.w16(s['game_preview_primed_mask'],3)
                for v in (0,1):
                    cpu.mem.w8(s['game_preview_launch_saved']+v,255)
                    cpu.mem.w16(s['game_preview_flight_phases']+v*2,4)
                    cpu.mem.w_block(s['game_preview_launch_states']+v*318,accepted['state'])
                saved=protected(cpu)
                endpoint_call(cpu,{0:generation,1:variant},saved)
                assert cpu.mem.r16(s['game_preview_query_workspaces']+variant*48+36)==1
                old_work=bytes(cpu.mem.r_block(s['game_preview_query_workspaces']+variant*48,48))
                if retire=='replacement':
                    call_checked(cpu,'game_preview_request',{0:generation,1:0xfffe,2:112,3:153},saved)
                elif retire=='cancel':call_checked(cpu,'game_preview_cancel',{0:generation},saved)
                elif retire=='seek':seek(cpu,case['selected']);saved=protected(cpu)
                elif retire=='resume':
                    cpu.call('game_history_resume_latest');saved=protected(cpu)
                elif retire=='variant-selection':
                    endpoint_call(cpu,{0:generation,1:1-variant},saved)
                    assert bytes(cpu.mem.r_block(s['game_preview_query_workspaces']+variant*48,48))==old_work
                    endpoint_call(cpu,{0:generation,1:variant},saved)
                    assert cpu.mem.r16(s['game_preview_query_workspaces']+variant*48+36)==2
                else:
                    call_checked(cpu,'game_preview_endpoint_try',{0:generation,1:variant},saved)
                    assert cpu.cpu.r_reg(0)==1
                    assert cpu.mem.r8(s['game_preview_endpoint_attempted']+variant)==255
                    before=block(cpu,'game_preview_storage','game_preview_storage_end')
                    endpoint_call(cpu,{0:generation,1:variant},saved)
                    assert cpu.cpu.r_reg(0)==0
                    assert block(cpu,'game_preview_storage','game_preview_storage_end')==before
                    call_checked(cpu,'game_preview_cancel',{0:generation},saved)
                if retire!='variant-selection':
                    assert cpu.mem.r16(s['game_preview_query_workspaces']+36)==0
                    assert cpu.mem.r16(s['game_preview_query_workspaces']+84)==0
                    before=block(cpu,'game_preview_storage','game_preview_storage_end')
                    if retire=='resume':
                        cpu.call('game_preview_endpoint_step',{0:generation,1:variant})
                        assert protected(cpu)==saved
                    else:endpoint_call(cpu,{0:generation,1:variant},saved)
                    assert cpu.cpu.r_reg(0)==0 and block(cpu,'game_preview_storage','game_preview_storage_end')==before
                cpu.audit_reads()
                rows.append(dict(variant=variant,retire=retire,passed=True,old_stage=1))
    raw_json(raw/'retirements.json',rows)
    return rows


def defensive_rollback(new,origin,raw):
    """Once-declared inconsistent bracket tests the defensive rollback path.

    This is not an admitted prepare result and is not old-helper equivalence.
    The original advance runs once; the initial complete seed is the expected
    rollback image, rather than a generated intermediate gameplay oracle.
    """
    image,s=load_image(new)
    with Core(image,s,initial=bytes([0x5a])*318,readonly=READONLY) as cpu:
        target=s['game_preview_endpoint_scratch'];workspace=s['game_preview_query_workspaces']
        cpu.mem.w_block(target,origin);cpu.mem.w_block(workspace,bytes(48))
        cpu.mem.w16(workspace+36,2);cpu.mem.w16(workspace+38,1)
        names=('game_step','game_ball_colour','game_shadow_colour','game_ball_x',
            'game_court_x','game_court_y','game_ball_y')
        cpu.mem.w_block(workspace+40,bytes(origin[s[n]-cpu.start] for n in names))
        cycles=cpu.call('landing_try_step',{13:target,11:workspace})
        result=[cpu.cpu.r_reg(r) for r in range(4)]
        assert result==[0,0,12,1],result
        assert bytes(cpu.mem.r_block(target,318))==origin,'Defensive rollback fails complete-state equality'
        assert cpu.visits.get(s['game_advance_ball'],0)==1
        cpu.audit_reads()
        row=dict(passed=True,result=result,cycles=cycles,full_state=origin.hex(),
            scope='Declared inconsistent continuation bracket; no natural reachability or old-admission equivalence claim')
        raw_json(raw/'defensive-rollback.json',row)
        return row


def run(new,old,raw):
    assert digest(old)==OLD_SHA,'Frozen helper reference identity changed'
    raw=Path(raw);raw.mkdir(parents=True,exist_ok=True)
    inputs,misses=corpus(old)
    rows=[];accepted=rejected=None
    for row in inputs:
        old_result=helper(old,row,False,0xa5,0)
        if old_result['result'][0]==3 and old_result['result'][1]>4:accepted=accepted or row
        if old_result['result'][2]==1:rejected=rejected or row
        runs=[]
        for poison,ccr in ((0xa5,0),(0x96,31)):
            legacy=helper(new,row,False,poison,ccr)
            staged=helper(new,row,True,poison,ccr)
            raw_json(raw/(row['name']+'-progress.json'),dict(input=row['state'].hex(),old=old_result,
                legacy=legacy,staged=staged,comparison_validated=False))
            for candidate in (legacy,staged):
                for key in ('result','full','events','preview_events','seek_events'):
                    assert candidate[key]==old_result[key],(row['name'],key,'Frozen old helper differs')
            runs.append(dict(poison=poison,ccr=ccr,legacy=legacy,staged=staged))
        raw_json(raw/(row['name']+'.json'),dict(input=row['state'].hex(),domain=row['domain'],
            old=old_result,new=runs,passed=True))
        rows.append(dict(name=row['name'],domain=row['domain'],end=row.get('end'),passed=True,
            result=old_result['result'],max_stage_cycles=max(r['cycles'] for run in runs for r in run['staged']['stages']),
            max_legacy_cycles=max(run['legacy']['stages'][0]['cycles'] for run in runs),
            max_staged_stack=max(run['staged']['stack'] for run in runs),
            max_synchronous_stack=max(run['legacy']['stack'] for run in runs),
            old_synchronous_stack=old_result['stack']))
    assert accepted and rejected
    invalid=invalid_stages(new,accepted['state'],raw)
    apis=endpoint_api(new,old,accepted,rejected,raw)
    retired=retirements(new,accepted,raw)
    rollback_origin=next(row['state'] for row in inputs if row['name']=='accepted-long')
    rollback=defensive_rollback(new,rollback_origin,raw)
    return dict(passed=True,reference_sha256=OLD_SHA,rows=rows,invalid_stages=invalid,
        endpoint_api=apis,retirements=retired,defensive_rollback=rollback,actual_misses_excluded=misses,
        scope='Finite actual old-helper versus new synchronous/staged execution and generation-owned endpoint API. Once-declared guard/boundary inputs are not natural reachability claims. CPU cycles exclude chip-bus waits, IRQs and native elapsed deadlines.')
