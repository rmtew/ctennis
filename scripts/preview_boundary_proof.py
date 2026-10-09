"""Explicit cap metadata fixtures; actual original dispatcher/ball reference.

Each instance initializes its state and declared preview-owned setup once.
No intermediate expected gameplay states or counters are injected. These are
boundary API tests, not claims that natural play reaches these counter values.
"""
from build_match_core import load_image
from history_proof import field
from match_core_cpu import Core
from preview_proof import point, block
from run_shared_match_core import READONLY


def cap_boundaries(executable, timed_state, waiting_state):
    image,s = load_image(executable)
    rows=[]
    # One real pre-launch snapshot obtained by the controlled A1 fixture.
    incoming=bytes.fromhex(timed_state)
    start=s['game_core_state'];play=s['game_play_state']-start
    for label, initial, entry, count, outgoing, expected in (
        ('incoming-launch-on-256',incoming,'game_preview_continue_one',256,False,0),
        ('incoming-no-launch-on-256',bytes.fromhex(waiting_state),'game_preview_continue_one',256,False,6),
        ('outgoing-out-on-256',incoming,'game_preview_flight_one',256,True,3),
        ('outgoing-no-event-256-then-cap',incoming,'game_preview_flight_one',256,True,0),
        ('total-513-terminal-priority',incoming,'game_preview_flight_one',512,True,3),
    ):
        initial=bytearray(initial)
        if outgoing:
            # Independent declared isolated-flight inputs: vy<4 causes original
            # outside, inactive produces no event. Other bytes stay complete.
            initial[s['game_velocity_y']-start]=3
            initial[s['game_contact']-start]=0
            initial[s['game_step']-start]=0
            initial[s['game_flight']-start]=64 if expected==3 else 0
        with Core(image,s,initial=initial,readonly=READONLY) as ref:
            if outgoing:ref.call('game_ball_tick',{12:s['game_play_state'],13:start})
            else:ref.call_logical('game_tick_dispatch',[])
            final=ref.state();sample=point(final,s);events=list(ref.events)
            ref.audit_reads()
        with Core(image,s,initial=initial,readonly=READONLY) as cpu:
            # Declared metadata/setup before the first tested helper operation.
            for name in ('game_preview_selected_state','game_preview_edited_state','game_preview_held_state'):
                cpu.mem.w_block(s[name],bytes(initial))
            for name,value in (('game_preview_status',3),('game_preview_kind',3),
                    ('game_preview_end',0),('game_preview_counts',count),
                    ('game_preview_dispatches',255),('game_preview_flight_phases',255 if outgoing else 0),
                    ('game_preview_synthetic_phases',3)):
                cpu.mem.w16(s[name],value)
            cpu.mem.w8(s['game_history_mode'],2)
            cpu.mem.w8(s['game_preview_active'],2)
            cpu.mem.w8(s['game_preview_launches'],255 if outgoing else 0)
            canonical=cpu.state()
            cpu.call(entry,{7:0,13:s['game_preview_held_state']})
            actual=bytes(cpu.mem.r_block(s['game_preview_held_state'],318))
            assert actual==final,(label,'full318')
            assert bytes(cpu.mem.r_block(s['game_preview_paths']+count*8,8))==sample,label
            assert cpu.mem.r16(s['game_preview_counts'])==count+1,label
            assert cpu.mem.r16(s['game_preview_outcomes'])==expected,(label,field(cpu,'game_preview_outcomes'))
            assert cpu.state()==canonical,label
            assert cpu.preview_event_groups.get((2,0),[])==events,label
            if not outgoing and expected==0:
                assert field(cpu,'game_preview_dispatches')==256 and field(cpu,'game_preview_launches',1)
                assert field(cpu,'game_preview_status')==3
            elif not outgoing:
                assert field(cpu,'game_preview_dispatches')==256 and not field(cpu,'game_preview_launches',1)
            elif expected==0:
                # Reaching the outgoing bound alone does not erase phase256.
                before=block(cpu,'game_preview_held_state','game_preview_released_state')
                cpu.call(entry,{7:0,13:s['game_preview_held_state']})
                assert field(cpu,'game_preview_outcomes')==6
                assert cpu.mem.r16(s['game_preview_counts'])==count+1
                assert block(cpu,'game_preview_held_state','game_preview_released_state')==before
            cpu.audit_reads()
        rows.append(dict(label=label,passed=True,full318_equal=True,ordered_events_equal=True,
                         sample_equal=True,counter_setup='explicit-once-preview-owned-boundary-metadata',
                         final_count=count+1,terminal_outcome=expected))
    return dict(passed=True,cases=rows,natural_reachability_claimed=False)


def flight_cases(executable, complete_state):
    """Declared short/long/rejected geometry inputs; original ball phases only."""
    from landing_cases import CASES
    image,s=load_image(executable);start=s['game_core_state'];rows=[]
    descriptors=CASES+[('fault-bounce-out',(0,5,0,32,100,101,64,0,0))]
    names=('game_velocity_x','game_velocity_y','game_velocity_z',
           'game_base_x','game_base_y','game_base_screen_y','game_flight','game_contact','game_step')
    for label,values in descriptors:
        initial=bytearray.fromhex(complete_state)
        for name,v in zip(names,values):initial[s[name]-start]=v
        reference=[]
        with Core(image,s,initial=initial,readonly=READONLY) as c:
            for _ in range(256):
                c.call('game_ball_tick',{12:s['game_play_state'],13:start})
                state=c.state();reference.append((state,point(state,s)))
                flags=state[s['game_contact']-start]
                if flags&0x8b:break
            c.audit_reads()
        flags=reference[-1][0][s['game_contact']-start]
        if label=='fault-bounce-out':
            assert not values[7] and flags&0x0a==0x0a and reference[-1][0][s['game_step']-start]==0, 'Fault fixture must detect a new original bounce/court-out'
        outcome=2 if flags&1 else 3 if flags&0x88 else 1 if flags&2 else 6
        with Core(image,s,initial=initial,readonly=READONLY) as c:
            c.mem.w_block(s['game_preview_selected_state'],bytes(initial))
            c.mem.w_block(s['game_preview_held_state'],bytes(initial))
            c.mem.w16(s['game_preview_status'],3);c.mem.w16(s['game_preview_counts'],1)
            c.mem.w8(s['game_preview_launches'],255);c.mem.w8(s['game_preview_active'],2)
            c.mem.w8(s['game_history_mode'],2)
            canonical=c.state()
            for phase,(state,sample) in enumerate(reference,1):
                c.call('game_preview_flight_one',{7:0,13:s['game_preview_held_state']})
                assert bytes(c.mem.r_block(s['game_preview_held_state'],318))==state,(label,phase,'full318')
                assert bytes(c.mem.r_block(s['game_preview_paths']+phase*8,8))==sample,(label,phase,'sample')
                assert c.state()==canonical and not c.events and not c.preview_events,(label,phase,'isolation')
                if phase<len(reference):assert field(c,'game_preview_outcomes')==0,(label,'first-event')
            if not flags&0x8b:
                before=bytes(c.mem.r_block(s['game_preview_held_state'],318))
                c.call('game_preview_flight_one',{7:0,13:s['game_preview_held_state']})
                assert bytes(c.mem.r_block(s['game_preview_held_state'],318))==before
            assert field(c,'game_preview_outcomes')==outcome,label
            assert field(c,'game_preview_counts')==len(reference)+1,label
            c.audit_reads()
        rows.append(dict(label=label,passed=True,phases=len(reference),outcome=outcome,
            complete_state_every_phase=True,exact_sample_every_phase=True,first_event_priority=True,bounce_fault_detected=label=='fault-bounce-out',
            event_scope='preexisting stopping flags' if values[7]&0x8b else 'original phase detection'))
    assert rows[0]['phases']<=4 and rows[1]['phases']>32
    assert next(r for r in rows if r['label']=='fault-bounce-out')['outcome']==3
    return dict(passed=True,cases=rows,scope='actual ball-only boundary worker; declared inputs include PR40 guard rejection descriptors, no shipping query execution claimed; preexisting contact flags test stopping priority rather than new intrinsic event timing')


def required_boundary_extent(validation):
    caps=validation.get('cap_boundary_validation') or {}
    flights=validation.get('flight_boundary_validation') or {}
    ring=validation.get('end_ring_validation') or {}
    expected={
        'incoming-launch-on-256':(257,0), 'incoming-no-launch-on-256':(257,6),
        'outgoing-out-on-256':(257,3),'outgoing-no-event-256-then-cap':(257,0),
        'total-513-terminal-priority':(513,3)}
    rows=caps.get('cases')
    if caps.get('passed') is not True or caps.get('natural_reachability_claimed') is not False or not isinstance(rows,list) or len(rows)!=5:return False
    if {r.get('label') for r in rows}!=set(expected):return False
    for r in rows:
        if any(r.get(k) is not True for k in ('passed','full318_equal','ordered_events_equal','sample_equal')) or (r.get('final_count'),r.get('terminal_outcome'))!=expected[r['label']]:return False
    from landing_cases import CASES
    rows=flights.get('cases')
    if flights.get('passed') is not True or not isinstance(rows,list) or len(rows)!=len(CASES)+1 or {r.get('label') for r in rows}!={n for n,_ in CASES}|{'fault-bounce-out'}:return False
    for r in rows:
        if any(r.get(k) is not True for k in ('passed','complete_state_every_phase','exact_sample_every_phase','first_event_priority')) or type(r.get('phases')) is not int or not 1<=r['phases']<=256 or r.get('outcome') not in (1,2,3,6):return False
    fault=next(r for r in rows if r['label']=='fault-bounce-out')
    if fault['outcome']!=3 or fault.get('bounce_fault_detected') is not True:return False
    if any(ring.get(k) is not True for k in ('passed','physical_index_wrap','natural_exchange')) or ring.get('attempt_first')!=127 or type(ring.get('attempted_count')) is not int or ring['attempted_count']<2:return False
    rows=ring.get('cases')
    if not isinstance(rows,list) or {r.get('name') for r in rows}!={'natural-upper-exchanged','wrapped-upper-return','warm-upper-handoff','current-upper-handoff'} or len(rows)!=4:return False
    for r in rows:
        if r.get('end')!=1 or any(r.get(k) is not True for k in ('passed','continuous_state_path_output_equal','independent_continuation_policy_equal','live_history_output_preserved')):return False
    for name,ordinal in (('controller',None),('current_controller',0xfffe)):
        c=ring.get(name) or {}
        if c.get('passed') is not True or c.get('end')!=1 or type(c.get('ordinal')) is not int or (c['ordinal']!=ordinal if ordinal is not None else not 0<=c['ordinal']<ring['attempted_count']):return False
    rejects=ring.get('invalid_positions')
    return isinstance(rejects,list) and len(rejects)==4 and {(r.get('ordinal')==0xfffe,r.get('cold')) for r in rejects}=={(a,b) for a in (False,True) for b in (False,True)} and all(r.get('passed') is True and r.get('result_rejected') is True for r in rejects)
