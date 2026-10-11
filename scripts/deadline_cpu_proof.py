"""Read-only native class peek and actual API equivalence at every envelope."""
import gzip,json
from build_match_core import load_image
from incoming_origin_proof import captured_fixture,observed
from history_proof import field
from match_core_cpu import Core
from preview_proof import protected,call_checked
from run_shared_match_core import READONLY

UI={'tutorial_active':1,'ui_paused':1,'tutorial_work_pending':1,'tutorial_generation':4,
    'tutorial_presentation_generation':4,'tutorial_menu':1,'tutorial_enter_pending':1,
    'tutorial_title_pending':1,'tutorial_resume_defer':1,'tutorial_placement_dirty':1,
    'tutorial_footer_dirty':1,'tutorial_animation_ready':1}
BODY={3:'game_core_sample_pads_body',4:'game_core_sample_result_body',5:'game_core_clear_inputs_body',
      7:'game_round_poll_body',9:'game_core_latch_actions_body'}


def initialize_image(image,owned):
    output=[]
    for a,data in image:
        data=bytearray(data)
        for low,values in owned:
            if a<=low and low+len(values)<=a+len(data):data[low-a:low-a+len(values)]=values
        output.append((a,bytes(data)))
    return output


def trial(image,s,fixture,end,projected,classified,poison):
    owned,state,_,_=fixture;rows=[];classes={};costs=[]
    with Core(initialize_image(image,owned),s,initial=state,poison=poison,readonly=dict(READONLY,**UI)) as c:
        c.call('game_history_freeze');gen=field(c,'game_preview_generation',4)
        player=s['game_play_state']+end*10
        api='game_preview_request_projected' if projected else 'game_preview_request'
        c.call(api,{0:gen,1:0xfffe,2:c.mem.r8(player+3),3:c.mem.r8(player+2)});gen+=1
        for n,w in UI.items():c.mem.w_block(s[n],(gen if w==4 else 255 if n in ('tutorial_active','ui_paused','tutorial_work_pending') else 0).to_bytes(w,'big'))
        saved=protected(c);original=c.instruction;seen=[]
        def observe(pc):
            original(pc)
            for n in (*BODY.values(),'game_preview_finish_variant','game_preview_dispatch'):
                if pc==s[n]:seen.append(n)
        c.cpu.set_instr_hook_callback(observe)
        for _ in range(3000):
            cls=0
            if classified:
                before=[bytes(c.mem.r_block(a,b-a)) for a,b in c.regions]
                elapsed=c.call('tutorial_background_class');cls=c.cpu.r_reg(0)
                assert cls in (0,3,4,5,7,9)
                assert [bytes(c.mem.r_block(a,b-a)) for a,b in c.regions]==before,'Class peek wrote owned/unclassified globals'
                assert protected(c)==saved
                if cls:classes[cls]=classes.get(cls,0)+1;costs.append(elapsed)
            seen.clear();c.preview_event_groups.clear()
            call_checked(c,'game_preview_step',{0:gen,1:1},saved)
            if cls:
                assert seen==[BODY[cls]],(cls,seen)
                assert field(c,'game_preview_active',1)==0
            rows.append(observed(c))
            if field(c,'game_preview_status')>=5:break
        assert field(c,'game_preview_status')==5
        c.audit_reads()
        return rows,dict(end=end,projected=projected,poison=poison,classes=classes,observations=len(rows),
            maximum_class_peek_cpu_cycles=max(costs,default=0),class_peek_read_only=True,eligible_body_only=True)


def partitions(image,s,fixture,end):
    # Once-declared classifier-only fixtures derived from a real primed origin.
    # These are domain tests, not naturally reached physical-input trajectories.
    owned,state,_,_=fixture
    with Core(initialize_image(image,owned),s,initial=state,readonly=dict(READONLY,**UI)) as c:
        c.call('game_history_freeze');gen=field(c,'game_preview_generation',4)
        player=s['game_play_state']+end*10
        c.call('game_preview_request_projected',{0:gen,1:0xfffe,2:c.mem.r8(player+3),3:c.mem.r8(player+2)})
        gen+=1
        for _ in range(2):c.call('game_preview_step',{0:gen,1:1})
        for n,w in UI.items():c.mem.w_block(s[n],(gen if w==4 else 255 if n in ('tutorial_active','ui_paused','tutorial_work_pending') else 0).to_bytes(w,'big'))
        c.call('game_preview_desired_variant');variant=c.cpu.r_reg(7)
        c.call('game_preview_context_address');context=c.cpu.r_reg(8)
        spans=[(a,bytes(c.mem.r_block(a,b-a))) for a,b in c.regions]
        initial=c.state();endcursor=int.from_bytes(c.mem.r_block(s['game_history_cursor'],8),'big')
        record=c.mem.r32(s['game_history_store'])+((endcursor-1)&4095)*14
        c.audit_reads()
    cursor=s['game_preview_stream_cursors']+variant*8
    phase=s['game_preview_synthetic_phases']+variant*2
    def value(a,w,v):return (a,v.to_bytes(w,'big'))
    poll=[value(cursor,8,endcursor),value(phase,2,0),value(context+s['game_score_initialized']-s['game_core_state'],1,255),
          value(context+s['game_score_state']-s['game_core_state']+3,1,0)]
    cases=[]
    for op in (3,4,5,7,9,8):
        cases.append(('retained-op%d'%op,poll+[value(cursor,8,endcursor-1),value(record,2,op),(record+2,bytes(12))],op if op!=8 else 0))
    for offset in (2,6,10):
        cases.append(('nonzero-result%d'%offset,poll+[value(cursor,8,endcursor-1),value(record,2,4),(record+2,bytes(12)),value(record+offset,4,1)],0))
    for n,expected in ((0,7),(1,3),(2,4),(3,0)):
        cases.append(('synthetic-phase%d'%n,poll+[value(phase,2,n)],expected))
    for n,w,v in [('tutorial_active',1,0),('ui_paused',1,0),('tutorial_work_pending',1,0),
            *[(n,1,255) for n in ('tutorial_menu','tutorial_enter_pending','tutorial_title_pending','tutorial_resume_defer','tutorial_placement_dirty','tutorial_footer_dirty','game_preview_active','game_history_replaying','game_history_seek_active')],
            ('game_history_mode',1,1),('game_history_seek_status',2,1),('game_history_seek_status',2,2),
            ('tutorial_generation',4,gen+1),('tutorial_presentation_generation',4,gen+1),('game_preview_status',2,2),('game_preview_status',2,5)]:
        cases.append(('reject-'+n+'-'+str(v),poll+[value(s[n],w,v)],0))
    for n,w,v in [('game_lifecycle',2,0),('game_core_command',1,1),('game_restart_context',1,1),('game_entropy_policy',1,1),('game_score_initialized',1,0)]:
        cases.append(('private-'+n,poll+[value(context+s[n]-s['game_core_state'],w,v)],0))
    cases.extend([
        ('synthetic-award',poll+[value(context+s['game_score_state']-s['game_core_state']+3,1,32)],0),
        ('retained-uninitialized-poll',poll+[value(cursor,8,endcursor-1),value(record,2,7),value(context+s['game_score_initialized']-s['game_core_state'],1,0)],0),
        ('retained-award-poll',poll+[value(cursor,8,endcursor-1),value(record,2,7),value(context+s['game_score_state']-s['game_core_state']+3,1,32)],0),
        ('exact-route',poll+[value(s['game_preview_predictor_routes']+variant,1,0)],0),
        ('launched',poll+[value(s['game_preview_launches']+variant,1,1)],0),
        ('future-cursor',poll+[value(cursor,8,endcursor+1)],0),
        ('evicted-cursor',poll+[value(cursor,8,0),value(s['game_history_oldest'],8,1)],0)])
    rows=[]
    for name,patches,expected in cases:
        with Core(spans,s,initial=initial,readonly=dict(READONLY,**UI)) as c:
            for address,data in patches:c.mem.w_block(address,data)
            before=[bytes(c.mem.r_block(a,b-a)) for a,b in c.regions]
            cycles=c.call('tutorial_background_class');actual=c.cpu.r_reg(0)
            assert actual==expected,(end,name,actual,expected)
            assert [bytes(c.mem.r_block(a,b-a)) for a,b in c.regions]==before
            c.audit_reads();rows.append(dict(end=end,name=name,operation=actual,cpu_cycles=cycles,read_only=True))
    return rows


def run(executable,raw):
    from native_evidence import atomic_json
    image,s=load_image(executable);pairs=[];partition_rows=[];raw.mkdir(parents=True,exist_ok=True)
    for end in (0,1):
        print('Discover native actual frozen origin',end,flush=True)
        fixture=captured_fixture(image,s,end)
        partition_rows.extend(partitions(image,s,fixture,end))
        for projected in (False,True):
            reference,_=trial(image,s,fixture,end,projected,False,0x5a)
            candidate,row=trial(image,s,fixture,end,projected,True,0xa5)
            assert candidate==reference,'Peek or altered scheduling changed full API state/events/cursors'
            row['complete_private_state_events_paths_cursors_equal']=True;pairs.append(row)
            def serial(trace):return [dict(fields=[b.hex() for b in values],events=[dict(owner=k[0],variant=k[1],events=v) for k,v in events.items()]) for values,events in trace]
            with gzip.open(raw/('native-e%d-p%d.json.gz'%(end,projected)),'wt') as handle:json.dump(dict(candidate=serial(candidate),reference=serial(reference)),handle,separators=(',',':'))
    assert all(not p['classes'] for p in pairs if not p['projected'])
    assert all({3,4,7}<=set(p['classes']) for p in pairs if p['projected'])
    result=dict(passed=True,pairs=pairs,classifier_partitions=partition_rows,scope='Actual emitted native classifier and original API, budget1 every envelope. UI scheduler metadata declared once per frozen initial fixture; physical timing/inputs proved separately. Read-only memory/bus audit, both ends/exact and projected with different CPU poison.')
    atomic_json(raw/'class-proof.json',result);return result


def required_extent(report):
    v=report.get('validation') or {};rows=v.get('pairs') or []
    return (report.get('execution')=='actual-68000-cpu-only' and v.get('passed') is True and len(rows)==4
        and {(r.get('end'),r.get('projected')) for r in rows}=={(e,p) for e in (0,1) for p in (False,True)}
        and all(r.get('class_peek_read_only') is True and r.get('eligible_body_only') is True
            and r.get('complete_private_state_events_paths_cursors_equal') is True and r.get('observations',0)>0 for r in rows)
        and all(not r.get('classes') for r in rows if not r['projected'])
        and all({'3','4','7'}<=set(r.get('classes') or {}) for r in rows if r['projected'])
        and len(v.get('classifier_partitions') or [])>=80
        and all(r.get('read_only') is True for r in v['classifier_partitions'])
        and (v.get('original_core_bytes') or {}).get('passed') is True)
