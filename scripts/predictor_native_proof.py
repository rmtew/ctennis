"""Read-only native predictor/input observations and original-core reference.

History decoding describes the existing envelope format, never tennis rules.
Each reference starts once at the captured full incoming origin and evolves
through original shared helpers with the captured input stream.
"""
from predictor_proof import execute, causal


class InputTrace:
    def __init__(self,symbols):
        self.symbols=symbols;self.rows=[];self.launch_rows=[]

    def watches(self):
        return [dict(addr=a,len=1,access=access) for a in (0xbfec01,0xbfed01,0xbfee01)
                for access in (('read','write') if a==0xbfee01 else ('read',))]+[
            dict(addr=self.symbols['game_keyboard_matrix'],len=128,access='write'),
            dict(addr=self.symbols['tutorial_packet'],len=1,access='write')]

    def observe(self,message):
        if message.get('method')!='event.mmio':return
        row=message['params'];a=row['addr'];s=self.symbols
        if a==s.get('game_preview_launches') and row['access']=='write' and row['value']:
            self.launch_rows.append(dict(row))
        if a in (0xbfec01,0xbfed01,0xbfee01,s['tutorial_packet']) or s['game_keyboard_matrix']<=a<s['game_keyboard_matrix']+128:
            self.rows.append(dict(row))

    def result(self,actions,calls=()):
        acknowledgements=[];start=None
        for row in self.rows:
            if row['addr']!=0xbfee01 or row['access']!='write':continue
            if row['value']&64:
                assert start is None,'Nested keyboard acknowledgement'
                start=row
            elif start is not None:
                duration=row['position']['cck']-start['position']['cck']
                assert duration>=350,'Keyboard ACK shorter than native 70 E-clock minimum'
                acknowledgements.append(dict(asserted=start,released=row,hold_cck=duration));start=None
        # A finite capture can end during a handshake. Disclose, never invent
        # the unobserved release or include it in completed-hold extrema.
        assert acknowledgements
        matrix=[r for r in self.rows if self.symbols['game_keyboard_matrix']<=r['addr']<self.symbols['game_keyboard_matrix']+128]
        matches=[]
        consumed=set()
        for index,action in enumerate(actions):
            expected=1 if action['held'] else 0
            limit=next((a['position']['cck'] for a in actions[index+1:] if a['rawkey']==action['rawkey']),float('inf'))
            found=next((r for r in matrix if id(r) not in consumed and r['addr']==self.symbols['game_keyboard_matrix']+action['rawkey']
                and r['value']==expected and action['position']['cck']<=r['position']['cck']<limit),None)
            assert found,('Physical key transition absent from native matrix',action)
            consumed.add(id(found))
            matches.append(dict(action=action,matrix=found,input_to_matrix_cck=found['position']['cck']-action['position']['cck']))
            # Tutorial nominal sampling is distinct from matrix reception. Only
            # actions issued while paused require the tutorial packet witness.
            if action.get('tutorial_active') and action['rawkey'] in (0x22,0x23,0x24):
                mask={0x22:1,0x23:16,0x24:32}[action['rawkey']]
                sample=next((r for r in self.rows if r['addr']==self.symbols['tutorial_packet']
                    and bool(r['value']&mask)==bool(action['held'])
                    and found['position']['cck']<=r['position']['cck']<limit),None)
                assert sample,('Matrix transition not nominally sampled',action)
                matches[-1].update(nominal_sample=sample,matrix_to_sample_cck=sample['position']['cck']-found['position']['cck'])
        polls=[r['position']['cck'] for r in self.rows if r['addr']==0xbfed01 and r['access']=='read']
        entries=sorted(r['entry']['cck'] for r in calls if r['callee']=='game_poll_keyboard')
        assert len(polls)>1
        return dict(passed=True,rows=self.rows,transitions=matches,acknowledgements=acknowledgements,
            minimum_ack_hold_cck=min(r['hold_cck'] for r in acknowledgements),
            maximum_ack_hold_cck=max(r['hold_cck'] for r in acknowledgements),
            maximum_receive_ready_icr_gap_cck=max(b-a for a,b in zip(polls,polls[1:])),
            maximum_keyboard_poll_gap_cck=max((b-a for a,b in zip(entries,entries[1:])),default=None),
            maximum_input_to_matrix_cck=max(r['input_to_matrix_cck'] for r in matches),
            incomplete_ack=start,scope='Finite CIA serial/matrix/poll/ACK observations; no approved universal maximum inferred')


def original_reference(image,symbols,row,records,records_count,history_end):
    operations=('game_core_init','game_core_select','game_core_sample_pads',
        'game_core_sample_result','game_core_clear_inputs','game_core_return_title',
        'game_round_poll','game_tick_dispatch','game_core_latch_actions')
    incoming=int(row['incoming_cursor'],16);stream=[]
    assert records_count>0 and records_count&(records_count-1)==0
    assert row['history_oldest']<=incoming<incoming+1<=history_end
    assert history_end-(incoming+1)<=records_count,'Incoming records were overwritten'
    for index in range(incoming+1,history_end):
        record=records[(index&(records_count-1))*14:((index&(records_count-1))+1)*14]
        opcode=int.from_bytes(record[:2],'big');assert 1<=opcode<=len(operations)
        stream.append((operations[opcode-1],[int.from_bytes(record[i:i+2],'big') for i in range(2,14,2)]))
    origin=bytearray.fromhex(row['incoming_state']);end=row['end']
    origin[end*10+3]=row['x'];origin[end*10+2]=row['y']
    reference=execute(image,symbols,bytes(origin),stream,end,True,False,0x96)
    actual=bytes.fromhex(row['held_path'])
    expected=bytes.fromhex(''.join(reference['path']))
    assert actual==expected[:len(actual)],'Native incoming/contact/outgoing samples differ from original replay'
    assert len(actual)>=8*(reference['boundaries'][-1]['dispatches']+1),'Captured prefix omits contact/miss'
    assert bool(row['human_launches'][0])==bool(reference['ledger']['launches'])
    if row['human_launches'][0]:
        assert causal(bytes.fromhex(row['held_launch_state']),symbols)==causal(bytes.fromhex(reference['incoming_final']),symbols)
    return dict(passed=True,path_prefix_equal=True,incoming_dispatches=reference['boundaries'][-1]['dispatches'],
        launch_equal=True,launch_causal_state_equal=bool(row['human_launches'][0]),
        compared_samples=len(actual)//8,original_total_samples=len(expected)//8,
        ledger=reference['ledger'],termination=reference['termination'],
        origin_complete=True,reference_scope='Original full incoming replay from captured retained origin and native envelopes; outgoing uses original geometric ball phase')


def contact_timing(row,calls,launch_rows):
    if not row['human_launches'][0]:return dict(scope='No accepted held contact')
    publication=row['first_actual_publication']['position']['cck'];request=row['request']['cck']
    marker=next((r for r in launch_rows if request<=r['position']['cck']<=publication),None)
    assert marker,'No native accepted-launch marker in request/publication interval'
    contact=next((r for r in calls if r['callee']=='game_history_contact'
        and r['entry']['cck']<=marker['position']['cck']<=r['exit']['cck']),None)
    dispatch=next((r for r in calls if r['callee']=='game_preview_dispatch'
        and r['entry']['cck']<=marker['position']['cck']<=r['exit']['cck']),None)
    assert contact and dispatch and dispatch['exit']['cck']<=publication
    return dict(request_to_accepted_hook_cck=contact['entry']['cck']-request,
        accepted_hook_to_helper_return_cck=contact['exit']['cck']-contact['entry']['cck'],
        accepted_hook_to_dispatch_return_cck=dispatch['exit']['cck']-contact['entry']['cck'],
        dispatch_return_to_copjmp_cck=publication-dispatch['exit']['cck'],
        marker=marker,contact_call=contact,dispatch_call=dispatch,
        scope='Emitted accepted-launch hook BSR store through matched RTS bus boundaries and actual COPJMP; instruction tails outside those boundaries are not isolated')
