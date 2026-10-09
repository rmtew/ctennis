"""Natural exchanged-end fixture and declared wrapped-index representation.

Simulation proceeds only through recorded controls. Index relocation is a
one-time declared metadata fixture using the same actual completed records;
it tests ordinal/controller addressing without claiming natural 128-attempt
retention or injecting intermediate expected gameplay state.
"""
from build_match_core import load_image
from history_proof import attempts, field, cursor, seek
from match_core_cpu import Core
from preview_extended_proof import execute, continuous, table
from preview_proof import fixture, protected, call_checked, block
from run_shared_match_core import READONLY


class SelectionObserved(Exception):pass


def controller_selection(native, initial, history, store, end, x, y, expected):
    image,s=load_image(native)
    # Native hunk addresses differ; rebase the attached-store pointer in copied
    # metadata, not any gameplay state. All setup precedes actual controller CPU.
    with Core(image,s,initial=initial,readonly=dict(READONLY,tutorial_end=1,tutorial_x=1,tutorial_y=1)) as c:
        metadata=bytearray(history)
        metadata[s['game_history_store']-s['game_history_state']:s['game_history_store']-s['game_history_state']+4]=s['game_history_buffer'].to_bytes(4,'big')
        c.mem.w_block(s['game_history_state'],bytes(metadata));c.mem.w_block(s['game_history_buffer'],store)
        for n,v in (('tutorial_end',end),('tutorial_x',x),('tutorial_y',y)):c.mem.w8(s[n],v)
        before=protected(c);observed=[]
        def hook(pc):
            c.instruction(pc)
            if pc==s['game_preview_request']:
                observed.append([c.cpu.r_reg(r)&0xffff for r in (1,2,3)])
                raise SelectionObserved()
        c.cpu.set_instr_hook_callback(hook)
        try:c.call('tutorial_request')
        except SelectionObserved:pass
        else:raise AssertionError('Actual controller did not reach preview request')
        assert observed==[[expected,x,y]],(observed,expected)
        assert protected(c)==before,'Controller selector mutates simulation/history before request'
        c.audit_reads()
    return dict(passed=True,ordinal=expected,end=end,scope='actual native emitted selector through request entry; no presentation execution claimed')


def end_ring(executable,native):
    image,s=load_image(executable);observations=[]
    with Core(image,s,readonly=READONLY) as c:
        stream,states,_,launches=fixture(c,dispatches=4096,
            stop=lambda cpu,rows:sum(r['human'] and r['end']==1 and r['kind']==1 for r in rows)>=2)
        event=next(r for r in reversed(launches) if r['human'] and r['end']==1 and r['kind']==1)
        assert c.mem.r8(s['game_play_state']+54) and not c.mem.r8(s['game_play_state']+55)
        assert field(c,'game_mode',1)&16 and field(c,'game_lower_owner',1)==1 and field(c,'game_upper_owner',1)==0
        index=attempts(c);ordinal=next(i for i,(n,k,e) in enumerate(index) if (n,k,e)==(event['episode_origin'],1,1))
        incoming=max(r['origin'] for r in launches if r['end']==0 and r['origin']<event['origin'])
        assert cursor(c,'game_history_oldest')<=incoming
        c.call('game_history_freeze')
        before=protected(c)
        observation=execute(c,ordinal,cursor(c),event['x'],event['y'],stream,0xace1,'natural-upper-exchanged')
        assert protected(c)==before
        assert observation['result']['incoming_state']==states[incoming+1]
        observations.append(observation)
        # Rotate actual completed records across physical127->0 once; preserve
        # logical order/origins/kinds and all core/checkpoint/operation bytes.
        records=[]
        first=field(c,'game_history_attempt_first');count=field(c,'game_history_attempt_count')
        for i in range(count):records.append(bytes(c.mem.r_block(s['game_history_attempts']+((first+i)&127)*12,12)))
        assert count>=2 and not field(c,'game_history_probe_active',1)
        for i,record in enumerate(records):c.mem.w_block(s['game_history_attempts']+((127+i)&127)*12,record)
        c.mem.w16(s['game_history_attempt_first'],127)
        assert attempts(c)==index
        c.call('game_preview_cancel',{0:field(c,'game_preview_generation',4)})
        before=protected(c)
        wrapped=execute(c,ordinal,cursor(c),event['x'],event['y'],stream,0xace1,'wrapped-upper-return')
        assert protected(c)==before
        assert wrapped['result']==observation['result']
        observations.append(wrapped)
        # Warm selected-phase reuse accepts the same after-handoff coordinate.
        warm=execute(c,ordinal,cursor(c),event['x'],event['y'],stream,0xace1,'warm-upper-handoff')
        assert warm['costs']['cache_hit'] and warm['result']==wrapped['result']
        observations.append(warm)
        rejected=[]
        def reject_positions(request_ordinal):
            for cold in (False,True):
                if cold:c.call('game_preview_cancel',{0:field(c,'game_preview_generation',4)})
                saved=protected(c);g=field(c,'game_preview_generation',4)
                call_checked(c,'game_preview_request',{0:g,1:request_ordinal,2:event['x'],3:6},saved)
                assert c.cpu.r_reg(0)==1
                for _ in range(8192):
                    if field(c,'game_preview_status')>=5:break
                    call_checked(c,'game_preview_step',{0:g+1,1:4},saved)
                assert field(c,'game_preview_status')==6 and field(c,'game_preview_counts',4)==0
                before=block(c,'game_preview_storage','game_preview_storage_end')
                call_checked(c,'game_preview_result',{0:g+1},saved)
                assert c.cpu.r_reg(0)==0 and block(c,'game_preview_storage','game_preview_storage_end')==before
                rejected.append(dict(ordinal=request_ordinal,cold=cold,passed=True,invalid_y=6,result_rejected=True))
        reject_positions(ordinal)
        # Controller initial state and history cursor must describe one boundary.
        seek(c,event['origin']+1)
        completed_state=c.state()
        completed_metadata=bytes(c.mem.r_block(s['game_history_state'],72))
        seek(c,event['origin'])
        current=execute(c,0xfffe,event['origin'],event['x'],event['y'],stream,0xace1,'current-upper-handoff')
        assert all(current['result'][k]==wrapped['result'][k] for k in ('edited','contexts','paths','outputs','outcomes','incoming_state'))
        observations.append(current)
        precontact=c.state()
        metadata=bytes(c.mem.r_block(s['game_history_state'],72))
        store=bytes(c.mem.r_block(s['game_history_buffer'],s['game_history_buffer_end']-s['game_history_buffer']))
        reject_positions(0xfffe)
        initial=completed_state;end=1;x=event['x'];y=event['y']
        expected=max(i for i,(_,k,e) in enumerate(index) if k in (1,2) and e==end)
        c.audit_reads()
    rows=[continuous(image,s,o) for o in observations]
    controller=controller_selection(native,initial,completed_metadata,store,end,x,y,expected)
    current_controller=controller_selection(native,precontact,metadata,store,end,x,y,0xfffe)
    return dict(passed=True,cases=rows,controller=controller,current_controller=current_controller,invalid_positions=rejected,attempt_first=127,
        attempted_count=count,physical_index_wrap=True,natural_exchange=True,
        ring_layout_scope='same actual completed records relocated once before wrapped API tests')
