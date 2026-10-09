"""Separate endpoint API against actual original incoming/contact/ball execution."""
from build_match_core import load_image
from history_proof import attempts,field,seek
from incoming_flight_proof import oracle
from match_core_cpu import Core
from preview_proof import block,call_checked,fixture,point,protected
from run_shared_match_core import READONLY


def run(executable):
    image,s=load_image(executable)
    with Core(image,s,readonly=READONLY) as c:
        stream,states,_,launches=fixture(c)
        contact=next(r for r in launches if r['human'] and r['kind']==1)
        incoming=max(r['origin'] for r in launches if r['end']!=contact['end'] and r['origin']<contact['origin'])
        source=states[incoming+1]
        ordinal=next(i for i,(_,kind,end) in enumerate(attempts(c)) if kind==1 and end==contact['end'])
    rows=[]
    for x,y in ((111,153),(111,140),(111,128),(111,112),(111,98),(100,153),(119,153),(40,153),(180,153)):
        player=s['game_play_state']-s['game_core_state']+10*contact['end']
        initial=bytearray(source);initial[player+3]=x;initial[player+2]=y
        expected=[oracle(image,s,initial,stream[incoming+1:],contact['end'],held,0x96) for held in (True,False)]
        with Core(image,s,readonly=READONLY,poison=0x96) as c:
            fixture(c);c.call('game_history_freeze');seek(c,contact['origin'])
            saved=protected(c);gen=field(c,'game_preview_generation',4)
            call_checked(c,'game_preview_request',{0:gen,1:ordinal,2:x,3:y},saved)
            assert c.cpu.r_reg(0)==1
            gen+=1;tried=set();early=set();copies={};costs=[];queries=[];early_products={}
            for job in range(4096):
                call_checked(c,'game_preview_step',{0:gen,1:(1,4,2)[job%3]},saved)
                for variant,(path,final,phase,boundaries,events) in enumerate(expected):
                    if c.mem.r8(s['game_preview_launch_saved']+variant):
                        actual=bytes(c.mem.r_block(s['game_preview_launch_states']+318*variant,318))
                        assert phase is not None and actual==boundaries[phase-1],(x,y,variant,'complete launch')
                        if variant in copies:assert copies[variant]==actual
                        copies[variant]=actual
                    # Stale generation must be entirely neutral, including scratch.
                    before=block(c,'game_preview_storage','game_preview_storage_end')
                    call_checked(c,'game_preview_endpoint_try',{0:gen-1,1:variant},saved)
                    assert c.cpu.r_reg(0)==0 and block(c,'game_preview_storage','game_preview_storage_end')==before
                    call_checked(c,'game_preview_endpoint_pending',{0:gen,1:variant},saved)
                    pending=c.cpu.r_reg(0)
                    assert block(c,'game_preview_storage','game_preview_storage_end')==before
                    dense=[bytes(c.mem.r_block(s[n],size)) for n,size in (
                        ('game_preview_held_state',318),('game_preview_released_state',318),
                        ('game_preview_counts',4),('game_preview_outcomes',4),('game_preview_status',2),
                        ('game_preview_flight_phases',4),('game_preview_stream_cursors',16))]
                    costs.append(call_checked(c,'game_preview_endpoint_try',{0:gen,1:variant},saved))
                    assert c.cpu.r_reg(0)==pending
                    if not pending:
                        assert block(c,'game_preview_storage','game_preview_storage_end')==before
                        continue
                    assert variant not in tried;tried.add(variant)
                    assert dense==[bytes(c.mem.r_block(s[n],size)) for n,size in (
                        ('game_preview_held_state',318),('game_preview_released_state',318),
                        ('game_preview_counts',4),('game_preview_outcomes',4),('game_preview_status',2),
                        ('game_preview_flight_phases',4),('game_preview_stream_cursors',16))]
                    reason=c.mem.r16(s['game_preview_endpoint_reasons']+2*variant)
                    ready=c.mem.r8(s['game_preview_endpoint_ready']+variant)
                    assert reason!=15, 'Accepted helper phase cannot precede an unfinished exact dense phase'
                    assert bool(ready)==(reason==0)
                    if not ready:
                        assert bytes(c.mem.r_block(s['game_preview_endpoint_scratch'],318))==copies[variant]
                    flags=final[s['game_contact']-s['game_core_state']]
                    outcome=2 if flags&1 else 3 if flags&0x88 else 1 if flags&2 else 6
                    queries.append(dict(variant=variant,reason=reason,ready=bool(ready),
                        dense_phase=int.from_bytes(dense[5][variant*2:variant*2+2],'big'),
                        endpoint_phase=c.mem.r16(s['game_preview_endpoint_phases']+2*variant),
                        full318_equal_or_rejected_unchanged=True,dense_state_counts_events_cursors_unchanged=True,
                        expected_outcome=outcome,outcome=c.mem.r16(s['game_preview_endpoint_outcomes']+2*variant)))
                    if ready:
                        assert bytes(c.mem.r_block(s['game_preview_endpoint_scratch'],318))==final
                        assert bytes(c.mem.r_block(s['game_preview_endpoints']+8*variant,8))==path[-1]
                        assert c.mem.r16(s['game_preview_endpoint_phases']+2*variant)==len(path)-1-phase
                        assert c.mem.r16(s['game_preview_endpoint_outcomes']+2*variant)==outcome
                        assert c.mem.r16(s['game_preview_outcomes']+2*variant)==0
                        early.add(variant)
                        early_products[variant]=(c.mem.r16(s['game_preview_endpoint_phases']+2*variant),c.mem.r16(s['game_preview_endpoint_outcomes']+2*variant),bytes(c.mem.r_block(s['game_preview_endpoints']+8*variant,8)))
                if field(c,'game_preview_status')==5:break
            else:raise AssertionError('Finite endpoint continuation cap')
            for variant,(path,final,phase,boundaries,events) in enumerate(expected):
                count=c.mem.r16(s['game_preview_counts']+2*variant)
                assert count==len(path)
                assert bytes(c.mem.r_block(s['game_preview_paths']+513*8*variant,8*count))==b''.join(path)
                assert bytes(c.mem.r_block(s['game_preview_held_state' if variant==0 else 'game_preview_released_state'],318))==final
                assert c.preview_event_groups.get((2,variant),[])==events
                if phase is not None:
                    assert bytes(c.mem.r_block(s['game_preview_endpoints']+8*variant,8))==path[-1]
                else:assert not c.mem.r8(s['game_preview_endpoint_ready']+variant)
                if variant in early_products:
                    assert early_products[variant]==(c.mem.r16(s['game_preview_endpoint_phases']+2*variant),c.mem.r16(s['game_preview_endpoint_outcomes']+2*variant),bytes(c.mem.r_block(s['game_preview_endpoints']+8*variant,8)))
            call_checked(c,'game_preview_cancel',{0:gen},saved)
            assert bytes(c.mem.r_block(s['game_preview_launch_saved'],6))==bytes(6)
            before=block(c,'game_preview_storage','game_preview_storage_end')
            for variant in (0,1,2,65535):
                call_checked(c,'game_preview_endpoint_try',{0:gen+1,1:variant},saved)
                assert c.cpu.r_reg(0)==0 and block(c,'game_preview_storage','game_preview_storage_end')==before
            c.audit_reads()
            rows.append(dict(passed=True,x=x,y=y,attempted=sorted(tried),early_endpoints=sorted(early),
                queries=queries,complete_launch_seeds_equal=True,original_dense_full318_points_events_equal=True,
                early_endpoint_unchanged_at_dense_completion=True,stale_and_cancelled_neutral=True,maximum_api_cpu_cycles=max(costs)))
    assert any(r['early_endpoints'] for r in rows)
    assert any(not r['attempted'] for r in rows)
    return dict(passed=True,cases=rows,scope='Original recorded incoming/contact and outgoing ball bodies, endpoint API and final dense equality; no native callback admission claim')


def prefix_policy(executable):
    """Declared once-initialized private flight fixtures, not natural reachability."""
    from history_proof import attach
    from landing_try_proof import corpus,reference
    image,s=load_image(executable)
    seeds,_=corpus(executable)
    rows=[]
    for seed in seeds:
        if seed['name'] not in ('accepted-short','accepted-long','special-net-reflection'):continue
        expected=reference(image,s,seed['state'])
        with Core(image,s,initial=seed['state'],readonly=READONLY) as c:
            attach(c);c.call('game_history_freeze')
            # One initial protocol fixture; subsequent state is only actual APIs.
            c.mem.w32(s['game_preview_generation'],1)
            c.mem.w16(s['game_preview_status'],3)
            c.mem.w8(s['game_preview_launches'],1)
            c.mem.w8(s['game_preview_launch_saved'],1)
            c.mem.w16(s['game_preview_counts'],1)
            for name in ('game_preview_selected_state','game_preview_held_state','game_preview_launch_states'):
                c.mem.w_block(s[name],seed['state'])
            c.mem.w_block(s['game_preview_paths'],point(seed['state'],s))
            c.mem.w_block(s['game_preview_history_saved'],block(c,'game_history_state','game_history_state_end'))
            saved=protected(c);attempts_count=0;phases=0
            for _ in range(256):
                call_checked(c,'game_preview_step',{0:1,1:1},saved)
                phases+=1
                call_checked(c,'game_preview_endpoint_pending',{0:1,1:0},saved)
                if c.cpu.r_reg(0):
                    assert phases>=4
                    call_checked(c,'game_preview_endpoint_try',{0:1,1:0},saved)
                    assert c.cpu.r_reg(0)==1;attempts_count+=1
                if c.mem.r16(s['game_preview_outcomes']):break
            assert bytes(c.mem.r_block(s['game_preview_held_state'],318))==expected[0]
            assert phases==expected[2] and c.mem.r16(s['game_preview_outcomes'])==expected[3]
            assert attempts_count==(0 if phases<=4 else 1)
            assert c.mem.r16(s['game_preview_flight_phases'])==phases
            c.audit_reads()
            rows.append(dict(name=seed['name'],passed=True,original_phases=phases,
                query_attempts=attempts_count,complete_state_equal=True,prefix_counted_once=True,
                initial_fixture='Declared initial ball fields and private protocol metadata once; no intermediate injection'))
    assert len(rows)==3 and any(r['original_phases']<=4 for r in rows)
    return dict(passed=True,cases=rows,natural_reachability_claimed=False)
