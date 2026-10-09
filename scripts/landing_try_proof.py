"""Bounded endpoint attempts against uninterrupted original ball instructions.

Natural seeds are complete actual post-dispatch launch states. Declared domain
fixtures change named initial ball bytes once. No expected intermediate state,
contact timing, trajectory model, or fallback is injected into a query.
"""
import hashlib
from build_match_core import load_image
from history_proof import field
from incoming_flight_proof import oracle
from landing_cases import CASES
from match_core_cpu import Core
from preview_proof import fixture, point
from run_shared_match_core import READONLY

PARAMS=('game_velocity_x','game_velocity_y','game_velocity_z','game_base_x',
        'game_base_y','game_base_screen_y','game_flight','game_contact','game_step')


def corpus(executable):
    image,s=load_image(executable);rows=[];misses=[];template=None
    for seed in (0xace1,0x0001,0x1234):
        with Core(image,s,readonly=READONLY) as c:
            stream,states,_,launches=fixture(c,seed=seed)
            for i,row in enumerate(launches):
                if row['human']:
                    state=states[row['origin']+1]
                    rows.append(dict(name=f'natural-{seed:04x}-{i}',state=state,
                        domain='actual-recorded-post-dispatch',end=row['end'],origin=row['origin'],seed=seed))
                    template=template or state
            if seed==0xace1:
                contact=next(r for r in launches if r['human'] and r['kind']==1)
                incoming=max(r['origin'] for r in launches if r['end']!=contact['end'] and r['origin']<contact['origin'])
                source=states[incoming+1]
        if seed==0xace1:
            player=s['game_play_state']-s['game_core_state']+10*contact['end']
            for x,y in ((111,153),(111,140),(111,128),(111,112),(111,98),(100,153),(119,153),(40,153),(180,153)):
                initial=bytearray(source);initial[player+3]=x;initial[player+2]=y
                for held in (True,False):
                    _,terminal,phase,boundaries,_=oracle(image,s,initial,stream[incoming+1:],contact['end'],held,0x96)
                    name=f'edited-{x}-{y}-{int(held)}'
                    if phase is None:
                        assert terminal[s['game_contact']-s['game_core_state']]&0x8d, (name, 'bounded no-launch is not an actual miss')
                        misses.append(name)
                        continue
                    state=boundaries[phase-1]
                    assert state[s['game_step']-s['game_core_state']]==0
                    rows.append(dict(name=name,state=state,domain='actual-edited-post-dispatch',
                        end=contact['end'],incoming_origin=incoming,x=x,y=y,held=held,contact_phase=phase))
    with Core(image,s,readonly=READONLY) as c:
        _,states,_,launches=fixture(c,dispatches=4096,
            stop=lambda cpu,events:sum(r['human'] and r['end']==1 and r['kind']==1 for r in events)>=2)
        assert field(c,'game_mode',1)&16 and field(c,'game_lower_owner',1)==1 and field(c,'game_upper_owner',1)==0
        for i,r in enumerate(launches):
            if r['human'] and r['end']==1:
                rows.append(dict(name=f'exchanged-upper-{i}',state=states[r['origin']+1],
                    domain='actual-exchanged-post-dispatch',end=1,origin=r['origin']))
    assert template is not None
    descriptors=CASES+[('accepted-court-out-bounce',(0,5,0,32,100,100,64,0,0))]
    for name,args in descriptors:
        state=bytearray(template)
        for field_name,v in zip(PARAMS,args):state[s[field_name]-s['game_core_state']]=v
        rows.append(dict(name=name,state=bytes(state),domain='declared-initial-ball-fields',arguments=list(args)))
    assert len(rows)<=128 and len(misses)<=18
    return rows,misses


def reference(image,s,initial):
    with Core(image,s,initial=initial,readonly=READONLY) as c:
        phases=[];cycles=0
        for n in range(1,257):
            cycles+=c.call('game_ball_tick',{12:s['game_play_state'],13:c.start})
            state=c.state();phases.append(state)
            if state[s['game_contact']-c.start]&0x8b:break
        flags=phases[-1][s['game_contact']-c.start]
        outcome=2 if flags&1 else 3 if flags&0x88 else 1 if flags&2 else 6
        c.audit_reads()
        assert not c.events
        return phases[-1],point(phases[-1],s),len(phases),outcome,cycles


def check(executable,base,row,expected,ccr,poison):
    image,s=load_image(executable,base=base)
    final,sample,phases,outcome,reference_cycles=expected
    initial=row['state']
    # Canonical working state deliberately differs from the immutable seed.
    with Core(image,s,initial=bytes([poison])*318,readonly=READONLY) as c:
        source=s['game_preview_incoming_state'];target=s['game_preview_held_state']
        c.mem.w_block(source,initial)
        canonical=c.state();events=list(c.events)
        c.writes.clear()
        copy_cycles=c.call('game_history_copy_state',{8:target,9:source})
        assert bytes(c.mem.r_block(target,318))==initial
        preserved={r:(0x965aa569^r*0x1010101)&0xffffffff for r in range(4,15)}
        preserved[13]=target
        registers={r:(0xfedcba98^(r+1)*0x1234567^ccr)&0xffffffff for r in range(4)}
        c.cpu.w_sr(0x2700|ccr)
        query_cycles=c.call('landing_try_fast',{**registers,**preserved})
        result=[c.cpu.r_reg(r) for r in range(4)]
        actual=bytes(c.mem.r_block(target,318))
        assert all(c.cpu.r_reg(r)==v for r,v in preserved.items()),(row['name'],'ABI')
        assert c.state()==canonical and bytes(c.mem.r_block(source,318))==initial
        assert c.events==events and not c.preview_events and not c.seek_events
        assert c.writes<=set(range(target,target+318)),(row['name'],'out-of-owner')
        assert 0<=result[3]<=6 and 0<=result[2]<=14
        assert c.visits.get(s['game_ball_tick'],0)==0,'Try-fast runs synchronous fallback'
        if result[2]==0:
            assert result[:2]==[3,phases] and 1<=phases<=255 and 1<=result[3]<=6
            assert actual==final and point(actual,s)==sample,(row['name'],'full318 endpoint')
            assert outcome in (1,3),(row['name'],'accepted terminal priority')
        else:
            assert result[:2]==[0,0] and actual==initial,(row['name'],'rejection neutrality')
        c.audit_reads()
        return dict(accepted=result[2]==0,reason=result[2],checks=result[3],
            query_cpu_cycles=query_cycles,copy318_cpu_cycles=copy_cycles,
            copied_query_cpu_cycles=copy_cycles+query_cycles,
            reference_cpu_cycles=reference_cycles,reference_phases=phases,
            outcome=outcome if result[2]==0 else None,stack_bytes=c.stack_bytes,
            full318_endpoint_equal=result[2]==0,rejection_full318_unchanged=result[2]!=0,
            original_ball_fallback_calls=0,ordered_events_equal=True,canonical_source_preserved=True)


def proof(standalone,native):
    rows,misses=corpus(standalone)
    image,s=load_image(standalone)
    expected={r['name']:reference(image,s,r['state']) for r in rows}
    results=[];baseline={}
    for role,executable,base,poison in (('standalone',standalone,0x10000,0xa5),
            ('relocated',standalone,0x30000,0x96),('emitted-native',native,0x10000,0x5a)):
        for row in rows:
            # All incoming CCRs on declared domains; natural complete states
            # additionally repeat across relocated/native code and poison states.
            ccrs=range(32) if row['domain']=='declared-initial-ball-fields' else (0,31)
            runs=[check(executable,base,row,expected[row['name']],ccr,poison) for ccr in ccrs]
            signature=[(r['accepted'],r['reason'],r['checks'],r['reference_phases'],r['outcome']) for r in runs]
            assert len(set(signature))==1
            if role=='standalone':baseline[row['name']]=signature[0]
            else:assert signature[0]==baseline[row['name']]
            results.append(dict(name=row['name'],domain=row['domain'],role=role,base=base,
                seed_sha256=hashlib.sha256(row['state']).hexdigest(),ccr_runs=len(runs),
                **runs[0],maximum_copied_query_cpu_cycles=max(r['copied_query_cpu_cycles'] for r in runs)))
        print('Bounded endpoint proof',role,'cases',len(rows),flush=True)
    assert any(r['accepted'] and r['reference_phases']<=4 for r in results)
    assert any(r['accepted'] and r['reference_phases']>32 for r in results)
    assert any(r['name']=='accepted-court-out-bounce' and r['accepted'] and r['outcome']==3 for r in results)
    reasons=sorted({r['reason'] for r in results if not r['accepted']})
    return dict(passed=True,canonical_bytes=318,phase_cap=256,candidate_cap=6,
        cases=results,natural_seed_count=sum(r['domain']!='declared-initial-ball-fields' for r in rows),
        declared_seed_count=sum(r['domain']=='declared-initial-ball-fields' for r in rows),
        actual_misses_excluded=misses,rejection_reasons_observed=reasons,
        defensive_bracket_reason12_observed=12 in reasons,
        rollback_scope='Seven original advance-written bytes restored on defensive rejection; no injected intermediate bracket failure',
        maximum_copied_query_cpu_cycles=max(r['maximum_copied_query_cpu_cycles'] for r in results),
        maximum_stack_bytes=max(r['stack_bytes'] for r in results),
        scope='Actual bounded helper and original ball endpoint reference; CPU cycles exclude native chip-bus waits/IRQs. No UI readiness or normal-callback admission pass.')
