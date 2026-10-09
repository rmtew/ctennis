"""Latest-origin proof using actual recorded envelopes and the original resolver."""
import hashlib
from build_match_core import load_image
from history_proof import attach, cursor, field, seek
from match_core_cpu import Core
from preview_proof import block, fixture, protected, call_checked
from run_shared_match_core import READONLY


def latest_fixture(cpu, end=0):
    def stop(c, launches):
        return bool(field(c,'game_history_incoming_valid',1)) and field(c,'game_history_incoming_end')==end
    return fixture(cpu,seed=1,dispatches=4000,stop=stop)


def observed(cpu):
    names=(('game_preview_held_state',318),('game_preview_released_state',318),
        ('game_preview_paths',2*513*8),('game_preview_counts',4),
        ('game_preview_outcomes',4),('game_preview_stream_cursors',16),
        ('game_preview_synthetic_phases',4),('game_preview_dispatches',4),
        ('game_preview_launches',2),('game_preview_launch_states',2*318),
        ('game_preview_flight_phases',4),('game_preview_incoming_state',318))
    return tuple(bytes(cpu.mem.r_block(cpu.symbols[n],w)) for n,w in names),dict(cpu.preview_event_groups)


def captured_fixture(image,symbols,end):
    # Capture real recorded owned memory once. Trials initialize from this
    # immutable fixture; no candidate receives an intermediate expected state.
    with Core(image,symbols,readonly=READONLY) as cpu:
        _,states,_,launches=latest_fixture(cpu,end)
        spans=[(cpu.start,cpu.stop),*cpu.mutable_regions]
        owned=[(low,bytes(cpu.mem.r_block(low,high-low))) for low,high in spans]
        cpu.audit_reads()
        return owned,cpu.state(),{cursor(cpu):states[cursor(cpu)]},launches


def branch(image,symbols,end,poison,budget,projected,miss=None,historical=False,captured=None):
    initial=None
    if captured:
        owned,initial,states,launches=captured
        initialized=[]
        for address,data in image:
            data=bytearray(data)
            for low,values in owned:
                if address<=low and low+len(values)<=address+len(data):
                    data[low-address:low-address+len(values)]=values
            initialized.append((address,bytes(data)))
        image=initialized
    with Core(image,symbols,initial=initial,poison=poison,readonly=READONLY) as cpu:
        if not captured:_,states,_,launches=latest_fixture(cpu,end)
        origin=cursor(cpu,'game_history_incoming_cursor')
        assert origin==cursor(cpu)
        assert block(cpu,'game_history_incoming_state','game_history_incoming_cursor')==states[origin]
        assert launches[-1]['origin']+1==origin and not launches[-1]['human']
        cache=block(cpu,'game_history_incoming_storage','game_history_incoming_storage_end')
        cpu.call('game_history_freeze')
        if historical:seek(cpu,origin-4)
        if miss:
            name,width,value=miss
            cpu.mem.w_block(symbols[name],value.to_bytes(width,'big'))
            cache=block(cpu,'game_history_incoming_storage','game_history_incoming_storage_end')
        saved=protected(cpu)
        receiving=field(cpu,'game_history_incoming_end') if not miss or miss[0]!='game_history_incoming_end' else end
        player=symbols['game_play_state']+receiving*10
        x,y=cpu.mem.r8(player+3),cpu.mem.r8(player+2)
        gen=field(cpu,'game_preview_generation',4)
        api='game_preview_request_projected' if projected else 'game_preview_request'
        request_cycles=call_checked(cpu,api,{0:gen,1:0xfffe,2:x,3:y},saved)
        assert cpu.cpu.r_reg(0)==1
        initial_status=field(cpu,'game_preview_status')
        assert initial_status==(1 if miss or historical else 2),(end,miss,initial_status)
        gen+=1;resolver_calls=0;work=[];cycles=[]
        for _ in range(20000):
            before=field(cpu,'game_preview_status')
            cpu.preview_event_groups.clear()
            # Resolve with one envelope so the comparison starts at the same
            # PRIME public boundary; requested grouping applies to both branches.
            elapsed=call_checked(cpu,'game_preview_step',{0:gen,1:1 if before==1 else budget},saved)
            assert block(cpu,'game_history_incoming_storage','game_history_incoming_storage_end')==cache
            after=field(cpu,'game_preview_status')
            if before==1:resolver_calls+=1
            else:work.append(observed(cpu));cycles.append(elapsed)
            if after>=5:break
        assert after==5,(end,miss,historical,after)
        if not historical:assert cursor(cpu,'game_preview_incoming')==origin-1
        # A cancelled/stale worker cannot touch cache, canonical state or scratch.
        call_checked(cpu,'game_preview_cancel',{0:gen},saved)
        preview=block(cpu,'game_preview_storage','game_preview_storage_end')
        call_checked(cpu,'game_preview_step',{0:gen,1:budget},saved)
        assert cpu.cpu.r_reg(0)==0 and block(cpu,'game_preview_storage','game_preview_storage_end')==preview
        cpu.call('game_history_resume_latest')
        assert cpu.state()==states[origin]
        assert block(cpu,'game_history_incoming_storage','game_history_incoming_storage_end')==cache
        cpu.audit_reads()
        return work,dict(end=end,poison=poison,budget=budget,projected=projected,
            miss=None if not miss else miss[0],historical=historical,origin=origin,
            request_cpu_cycles=request_cycles,resolver_calls=resolver_calls,worker_calls=len(work),
            maximum_worker_cpu_cycles=max(cycles),stack_bytes=cpu.stack_bytes,
            paused_cache_canonical_history_neutral=True,resume_latest_equal=True,stale_neutral=True)


def lifetime(image,symbols):
    with Core(image,symbols,readonly=READONLY) as cpu:
        cpu.call_logical('game_core_init',[]);attach(cpu)
        cpu.call_logical('game_core_select',[0,1,0])
        snapshots={cursor(cpu):cpu.state()};captures=[];retirements=0;evictions=0;tickwraps=0
        previous_valid=False;oldest=0;last_tick=field(cpu,'game_tick',1)
        for tick in range(3200):
            for name,args in (('game_round_poll',[]),('game_core_sample_pads',[(16 if tick%64>=8 else 0)|(8 if tick%96<48 else 4),0]),
                ('game_core_sample_result',[0]*6),('game_tick_dispatch',[])):
                cpu.clear_events();cpu.call_logical(name,args)
                now=cursor(cpu);snapshots[now]=cpu.state()
                valid=bool(field(cpu,'game_history_incoming_valid',1))
                if valid:
                    origin=cursor(cpu,'game_history_incoming_cursor')
                    assert origin>=cursor(cpu,'game_history_oldest') and origin<=now
                    assert block(cpu,'game_history_incoming_state','game_history_incoming_cursor')==snapshots[origin]
                    assert field(cpu,'game_history_incoming_schema')==2
                    assert field(cpu,'game_history_incoming_simulation')==3
                    if origin==now:captures.append(dict(cursor=now,end=field(cpu,'game_history_incoming_end'),checkpoint_aligned=now%64==0))
                if previous_valid and not valid:retirements+=1
                previous_valid=valid
                new_oldest=cursor(cpu,'game_history_oldest')
                if new_oldest!=oldest:evictions+=1;oldest=new_oldest
                current_tick=field(cpu,'game_tick',1)
                tickwraps+=current_tick<last_tick;last_tick=current_tick
        assert {r['end'] for r in captures}=={0,1} and retirements>0 and evictions>0 and tickwraps>0
        # Actual reset operations retire the sole live identity without changing retention.
        epoch=field(cpu,'game_history_live_epoch',4)
        cpu.call_logical('game_core_return_title',[])
        assert not field(cpu,'game_history_incoming_valid',1) and not field(cpu,'game_history_incoming_pending',1)
        assert field(cpu,'game_history_live_epoch',4)==epoch+1
        cpu.audit_reads()
        return dict(operations=cursor(cpu),captures=captures,retirements=retirements,
            checkpoint_evictions=evictions,tick_wraps=tickwraps,complete_capture_every_boundary=True,title_retires=True)


def run(executable,raw):
    from native_evidence import atomic_json
    image,symbols=load_image(executable);rows=[]
    fixtures={end:captured_fixture(image,symbols,end) for end in (0,1)}
    for end in (0,1):
        for projected in (False,True):
            for budget in (1,2,3,4):
                cold,cold_row=branch(image,symbols,end,0x5a,budget,projected,('game_history_incoming_valid',1,0),captured=fixtures[end])
                warm,warm_row=branch(image,symbols,end,0xa5,budget,projected,captured=fixtures[end])
                assert warm==cold,('Warm/cold private state, events, paths/cursors differ',end,projected,budget)
                rows.append(dict(warm=warm_row,cold=cold_row,full_yield_state_events_paths_cursors_equal=True,
                    yield_sha256=hashlib.sha256(repr(warm).encode()).hexdigest()))
    misses=[]
    for end in (0,1):
        reference,_=branch(image,symbols,end,0x5a,4,False,('game_history_incoming_valid',1,0),captured=fixtures[end])
        for fault in (('game_history_incoming_end',2,1-end),('game_history_incoming_schema',2,0),
            ('game_history_incoming_simulation',2,0),('game_history_incoming_epoch',4,0),
            ('game_history_incoming_cursor',8,0),('game_history_incoming_cursor',8,0xffffffffffffffff)):
            result,row=branch(image,symbols,end,0xa5,4,False,fault,captured=fixtures[end])
            assert result==reference,('Invalid identity did not cold-fallback',fault,end)
            misses.append(row)
        _,row=branch(image,symbols,end,0xa5,4,False,historical=True,captured=fixtures[end]);misses.append(row)
    life=lifetime(image,symbols)
    raw.mkdir(parents=True,exist_ok=True)
    for end,(owned,initial,_,launches) in fixtures.items():
        atomic_json(raw/('captured-origin-'+str(end)+'.json'),dict(owned=[dict(address=a,bytes=b.hex()) for a,b in owned],state=initial.hex(),last_launch=launches[-1],scope='Once-captured actual recorded controls fixture, complete initial owned memory; never intermediate state injection'))
    validation=dict(passed=True,storage_bytes=symbols['game_history_incoming_storage_end']-symbols['game_history_incoming_storage'],
        rows=rows,misses=misses,lifetime=life,scope='Actual core; two natural recorded origins captured once as complete immutable initial fixtures; every warm/cold public computational yield. Explicit cache identity corruptions are fault fixtures, not intermediate expected simulation state.')
    atomic_json(raw/'origin-proof.json',validation)
    return validation


def required_extent(report):
    v=report.get('validation') or {};rows=v.get('rows') or [];misses=v.get('misses') or [];life=v.get('lifetime') or {}
    return (report.get('execution')=='actual-68000-cpu-only' and v.get('passed') is True and v.get('storage_bytes')==344
        and len(rows)==16 and len(misses)==14
        and {(r['warm']['end'],r['warm']['projected'],r['warm']['budget']) for r in rows}=={(e,p,b) for e in (0,1) for p in (False,True) for b in (1,2,3,4)}
        and all(r.get('full_yield_state_events_paths_cursors_equal') is True and r['warm']['resolver_calls']==0 and r['cold']['resolver_calls']>0 for r in rows)
        and life.get('complete_capture_every_boundary') is True and life.get('title_retires') is True
        and life.get('checkpoint_evictions',0)>0 and life.get('retirements',0)>0 and life.get('tick_wraps',0)>0
        and (v.get('original_core_bytes') or {}).get('passed') is True)
