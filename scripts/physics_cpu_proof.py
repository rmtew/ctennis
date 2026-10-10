"""Same-layout scheduling switch proof over actual public incoming workers."""
import gzip,json,hashlib
from build_match_core import load_image
from deadline_cpu_proof import UI,BODY,initialize_image
from history_proof import field
from incoming_origin_proof import observed
from match_core_cpu import Core
from preview_proof import fixture as live_fixture,protected,call_checked
from run_shared_match_core import READONLY
from native_evidence import atomic_json
READS=dict(READONLY,**UI,tutorial_background_physics_enabled=2)


def capture(image,s,end):
    with Core(image,s,readonly=READONLY) as c:
        def stop(cpu,launches):
            origin=int.from_bytes(cpu.mem.r_block(s['game_history_incoming_cursor'],8),'big')
            cursor=int.from_bytes(cpu.mem.r_block(s['game_history_cursor'],8),'big')
            return field(cpu,'game_history_incoming_valid',1) and field(cpu,'game_history_incoming_end')==end and cursor>=origin+64
        live_fixture(c,seed=1,dispatches=6000,stop=stop)
        assert stop(c,[])
        owned=[(a,bytes(c.mem.r_block(a,b-a))) for a,b in [(c.start,c.stop),*c.mutable_regions]]
        c.audit_reads();return owned,c.state()


def trial(image,s,fixture,end,xy,poison):
    owned,state=fixture;rows=[];work=[];classes={};first=None
    with Core(initialize_image(image,owned),s,initial=state,poison=poison,readonly=READS) as c:
        c.call('game_history_freeze');gen=field(c,'game_preview_generation',4)
        player=s['game_play_state']+end*10
        x,y=xy or (c.mem.r8(player+3),c.mem.r8(player+2))
        c.call('game_preview_request_projected',{0:gen,1:0xfffe,2:x,3:y});gen+=1
        for n,w in UI.items():c.mem.w_block(s[n],(gen if w==4 else 255 if n in ('tutorial_active','ui_paused','tutorial_work_pending') else 0).to_bytes(w,'big'))
        saved=protected(c)
        names=(*BODY.values(),'game_preview_dispatch','game_derive_launch','game_launch_root','game_preview_finish_variant','game_preview_visibility','game_preview_endpoint_try','game_tick_dispatch_body')
        for _ in range(4000):
            before=[bytes(c.mem.r_block(a,b-a)) for a,b in c.regions]
            classify=c.call('tutorial_background_class');cls=c.cpu.r_reg(0)
            assert cls in (0,3,4,5,7,8,9)
            assert [bytes(c.mem.r_block(a,b-a)) for a,b in c.regions]==before
            assert protected(c)==saved
            visits={n:c.visits.get(s[n],0) for n in names};c.preview_event_groups.clear()
            cycles=call_checked(c,'game_preview_step',{0:gen,1:1},saved)
            actual={n:c.visits.get(s[n],0)-v for n,v in visits.items()}
            if cls:
                classes[cls]=classes.get(cls,0)+1
                if cls==8:
                    assert actual['game_preview_dispatch']==1 and actual['game_derive_launch']<=1 and actual['game_launch_root']<=1
                    assert not actual['game_preview_visibility'] and not actual['game_preview_endpoint_try'] and not actual['game_tick_dispatch_body']
                    # Retain one natural admitted pre-call image for domain fixtures.
                    if first is None:first=(list(zip([a for a,b in c.regions],before)),state,gen)
                else:assert actual[BODY[cls]]==1
            assert not field(c,'game_preview_active',1)
            rows.append(observed(c));work.append(dict(operation=cls,worker_cpu_cycles=cycles,classify_cpu_cycles=classify,visits=actual))
            if field(c,'game_preview_status')>=5:break
        assert field(c,'game_preview_status')==5,(end,xy,field(c,'game_preview_status'))
        c.audit_reads()
        return rows,dict(end=end,xy=[x,y],classes=classes,observations=len(rows),work=work,
            full_state_events_paths_cursors_equal=True,classifier_read_only=True,out_of_state_write_audit=True),first


def partitions(image,s,base,end):
    image,state,gen=base
    # Patches declare each complete initial domain fixture before its first API;
    # no running trajectory receives intermediate expected state.
    with Core(image,s,initial=state,readonly=READS) as c:
        c.call('game_preview_desired_variant');v=c.cpu.r_reg(7)
        c.call('game_preview_context_address');ctx=c.cpu.r_reg(8)
    def core(name,w,val):return(s[name]-s['game_core_state']+ctx,w,val)
    cases=[('allowed',[],8),('disabled',[(s['tutorial_background_physics_enabled'],2,0)],0)]
    for name,w,val in [('game_mode',1,4),('game_score_initialized',1,0),('game_contact',1,0x80),('game_flight',1,0x80),('game_lower_y',1,97),('game_lower_y',1,154),('game_upper_y',1,6),('game_upper_y',1,63),('game_lower_phase',1,0x80),('game_upper_phase',1,0x40)]:
        cases.append((name+str(val),[core(name,w,val)],0))
    for val,expected in ((15,0),(16,0),(17,8)):
        cases.append(('serve-clock'+str(val),[core('game_lower_phase',1,0x20),core('game_serve_clock',1,val)],expected))
    for name,address,val in [('path-cap',s['game_preview_counts']+v*2,512),('dispatch-cap',s['game_preview_dispatches']+v*2,255)]:cases.append((name,[(address,2,val)],0))
    def current(addr,w):
        return next(int.from_bytes(data[addr-a:addr-a+w],'big') for a,data in image if a<=addr and addr+w<=a+len(data))
    for name,w,val in [('game_lower_owner',1,1-end),('game_upper_owner',1,end),('game_score_flags',1,0),('game_contact',1,0 if end==0 else 64)]:
        cases.append(('role-'+name,[core(name,w,val)],0))
    cases.extend([
        ('score-stage',[(ctx+s['game_score_state']-s['game_core_state'],1,0)],0),
        ('other-path-overcap',[(s['game_preview_counts']+2*(1-v),2,514)],0),
        ('upper-timed-serve', [core('game_upper_phase',1,32),core('game_serve_clock',1,16)],0)])
    released=[(s['game_preview_status'],2,4),
        (s['game_preview_released_state'],318,current(s['game_preview_held_state'],318)),
        (s['game_preview_stream_cursors']+8,8,current(s['game_preview_stream_cursors'],8)),
        (s['game_preview_synthetic_phases']+2,2,current(s['game_preview_synthetic_phases'],2)),
        (s['game_preview_dispatches']+2,2,current(s['game_preview_dispatches'],2)),
        (s['game_preview_counts'],2,10),(s['game_preview_launches']+1,1,0)]
    for count,expected in ((8,8),(9,0),(10,8)):
        cases.append(('released-count-'+str(count),released+[(s['game_preview_counts']+2,2,count)],expected))
    rows=[]
    for name,patches,expected in cases:
        # Static switch word is the only code fixture patch, used to test refusal.
        declared=[]
        for a,data in image:
            data=bytearray(data)
            for addr,w,val in patches:
                if a<=addr and addr+w<=a+len(data):data[addr-a:addr-a+w]=val.to_bytes(w,'big')
            declared.append((a,bytes(data)))
        with Core(declared,s,initial=state,readonly=READS) as c:
            before=[bytes(c.mem.r_block(a,b-a)) for a,b in c.regions]
            cycles=c.call('tutorial_background_class');actual=c.cpu.r_reg(0)
            assert actual==expected,(end,name,actual,expected)
            assert [bytes(c.mem.r_block(a,b-a)) for a,b in c.regions]==before
            c.audit_reads();rows.append(dict(end=end,name=name,operation=actual,cpu_cycles=cycles,read_only=True))
    return rows


def run(candidate,control,raw):
    ci,s=load_image(candidate);bi,bs=load_image(control)
    assert s==bs,'Scheduling switch changed symbol layout'
    different=[a+i for (a,x),(b,y) in zip(ci,bi) for i,(u,v) in enumerate(zip(x,y)) if u!=v]
    assert different==[s['tutorial_background_physics_enabled']+1],different
    assert all(a==b and len(x)==len(y) for (a,x),(b,y) in zip(ci,bi))
    raw.mkdir(parents=True,exist_ok=True);pairs=[];guards=[]
    def serial(rows):return [dict(fields=[b.hex() for b in vals],events=[dict(owner=k[0],variant=k[1],events=v) for k,v in ev.items()]) for vals,ev in rows]
    for end in (0,1):
        fixture=capture(ci,s,end)
        atomic_json(raw/('fixture-%d.json'%end),dict(owned=[dict(address=a,bytes=b.hex()) for a,b in fixture[0]],state=fixture[1].hex()))
        for kind,xy in [('miss',None),('contact',(98,152) if end==0 else (64,9))]:
            reference,rr,_=trial(bi,s,fixture,end,xy,0x5a)
            result,row,base=trial(ci,s,fixture,end,xy,0xa5)
            assert result==reference,(end,kind)
            assert 8 in row['classes'] and 8 not in rr['classes']
            if kind=='contact':assert any(w['operation']==8 and w['visits']['game_derive_launch'] for w in row['work'])
            row['kind']=kind;pairs.append(row)
            with gzip.open(raw/('e%d-%s.json.gz'%(end,kind)),'wt') as h:json.dump(dict(candidate=serial(result),control=serial(reference)),h,separators=(',',':'))
            if kind=='contact':guards.extend(partitions(ci,s,base,end))
        print('Checked both-end contact/miss',end,flush=True)
    # Broad RNG values and boundary geometry are declared complete origins.
    # The selected current live fixture and all retained controls stay fixed.
    from predictor_boundary_proof import declared_cases
    domain=[]
    seeds=(0,1,2,7,15,31,63,64,127,128,191,224,250,253,254,255)
    for end in (0,1):
        original=json.loads((raw/('fixture-%d.json'%end)).read_text())
        fixture=([(r['address'],bytes.fromhex(r['bytes'])) for r in original['owned']],bytes.fromhex(original['state']))
        source=next(data[s['game_history_incoming_state']-a:s['game_history_incoming_state']-a+318] for a,data in fixture[0] if a<=s['game_history_incoming_state'] and s['game_history_incoming_state']+318<=a+len(data))
        cases=[]
        for seed in seeds:
            origin=bytearray(source);origin[s['game_random_seed']-s['game_core_state']]=seed
            cases.append(('rng-%d'%seed,bytes(origin),(98,152) if end==0 else (64,9)))
        if end==0:
            cases.extend((r['name'],r['origin'],(40,153)) for r in declared_cases(s,source))
            cases.extend((name,source,xy) for name,xy in [('near-contact',(98,153)),('forward-placement',(98,128)),('wide-contact',(111,152))])
        for name,origin,xy in cases:
            owned=[]
            for a,data in fixture[0]:
                data=bytearray(data)
                addr=s['game_history_incoming_state']
                if a<=addr and addr+318<=a+len(data):data[addr-a:addr-a+318]=origin
                owned.append((a,bytes(data)))
            declared=(owned,fixture[1])
            reference,_,_=trial(bi,s,declared,end,xy,0x5a)
            result,row,_=trial(ci,s,declared,end,xy,0xa5)
            assert reference==result,(end,name)
            row.update(name=name,initial_origin=origin.hex(),scope='Once-declared full incoming origin; controls thereafter, no intermediate patches')
            domain.append(row)
            with gzip.open(raw/('domain-e%d-%s.json.gz'%(end,name)),'wt') as h:json.dump(dict(candidate=serial(result),control=serial(reference)),h,separators=(',',':'))
        print('Checked RNG/boundary domains',end,len(cases),flush=True)
    validation=dict(passed=True,pairs=pairs,declared_domains=domain,guard_partitions=guards,same_layout_switch_only=True,changed_loaded_bytes=different,
        scope='Actual emitted native APIs, full private318 states, events, paths and cursors at every budget1 envelope; different working-state poison. Fixtures captured once after16 actual dispatches from incoming origin; no intermediate state feed. UI metadata declared once. Native scheduling/timing measured separately; no WCET.')
    atomic_json(raw/'physics-proof.json',validation);return validation


def required_extent(report):
    v=report.get('validation') or {};pairs=v.get('pairs') or [];guards=v.get('guard_partitions') or []
    required={'allowed','disabled','released-count-8','released-count-9','released-count-10','other-path-overcap','path-cap','dispatch-cap','upper-timed-serve','serve-clock15','serve-clock16','serve-clock17','score-stage','role-game_lower_owner','role-game_upper_owner','role-game_score_flags','role-game_contact'}
    return (report.get('execution')=='actual-68000-cpu-only' and v.get('passed') is True
        and v.get('same_layout_switch_only') is True and len(pairs)==4
        and {(r['end'],r['kind']) for r in pairs}=={(e,k) for e in (0,1) for k in ('contact','miss')}
        and all(required <= {r['name'] for r in guards if r['end']==e} for e in (0,1))
        and all(r['read_only'] and r['operation']==(8 if r['name'] in {'allowed','serve-clock17','released-count-8','released-count-10'} else 0) for r in guards)
        and all(r.get('full_state_events_paths_cursors_equal') and r.get('classifier_read_only') and r.get('out_of_state_write_audit') and r.get('observations',0)>0 and '8' in r.get('classes',{}) for r in pairs)
        and all(w['visits']['game_preview_dispatch']==1 and w['visits']['game_derive_launch']<=1 and w['visits']['game_launch_root']<=1 and not any(w['visits'][n] for n in ('game_preview_visibility','game_preview_endpoint_try','game_tick_dispatch_body')) for r in pairs for w in r['work'] if w['operation']==8)
        and all(any(w['operation']==8 and w['visits']['game_derive_launch'] for w in r['work']) for r in pairs if r['kind']=='contact')
        and len(v.get('declared_domains') or [])==40
        and all(r.get('full_state_events_paths_cursors_equal') and r.get('classifier_read_only') and r.get('out_of_state_write_audit') for r in v['declared_domains'])
        and (v.get('original_core_bytes') or {}).get('passed') is True)
