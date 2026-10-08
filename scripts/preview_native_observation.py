"""Lossless native API brackets and frozen write guards; no gameplay oracle."""
import hashlib
import json
import re
from pathlib import Path
from match_core_capture import TraceCollector
from native_longword_observer import LongwordObserver
from native_size import _units

RAW_CAP=256*1024*1024
RESERVE=8*1024*1024
PUBLICATION=('blank_seen','presentation_frames','presentation_copper','spare_copper',
    'front_copper','ready_copper','game_presented_generation','display_ready',
    'ready_completed','missed_presentation_deadlines','log_timer')
PHYSICAL_INPUTS=('game_keyboard_matrix','ui_joystick_bits')
INPUTS=(('game_keyboard_matrix',128),('ui_keyboard_entry_keys',128),
    ('ui_previous_keys',128),('ui_joystick_bits',2),('ui_joystick_previous',2),
    ('ui_joystick_pressed',2),('ui_joystick_entry',2),('game_native_pad_bits',2),
    ('game_native_selection_keys',1),('keyboard_ack',1),('keyboard_ack_timer',2),
    ('ui_saved_volumes',6))


def irq_rules(listing,symbols,segments,locations):
    """Whitelist exact emitted presentation instructions, address and width."""
    rules={}
    for row in _units(listing):
        pc=segments[row['hunk']]['start']+row['start']
        if not symbols['presentation_interrupt']<=pc<symbols['complete_scene']:continue
        text=row['statement'].split(';',1)[0].strip()
        match=re.fullmatch(r'(move|clr|addq|subq)\.(b|w|l)\s+(.+)',text)
        if not match:continue
        operation,width,args=match.groups();width={'b':1,'w':2,'l':4}[width]
        arguments=args.split(',');destination=arguments[-1].strip()
        if destination in PUBLICATION:address=symbols[destination]
        elif destination.lower() in ('$dff09c','$dff096','$dff080','$dff088'):
            address=int(destination[1:],16)
        else:continue
        source=arguments[0].strip() if len(arguments)>1 else None
        rules[pc]=dict(address=address,bytes=width,operation=operation,source=source,
            destination=destination,instruction=text)
    assert rules and sum(r['destination'].lower()=='$dff09c' for r in rules.values())==2
    return rules


def outside_publication_rules(listing,symbols,segments):
    """Exact native scene/UI producer instructions, never API allowances."""
    rules={}
    for row in _units(listing):
        pc=segments[row['hunk']]['start']+row['start']
        if not symbols['complete_scene']<=pc<symbols['prepare_title_display']:continue
        text=row['statement'].split(';',1)[0].strip()
        match=re.fullmatch(r'(move|clr|st)\.(b|w|l)\s+(.+)',text)
        if not match:
            match=re.fullmatch(r'(st)\s+(.+)',text)
            if not match:continue
            operation,args=match.groups();width=1
        else:
            operation,width,args=match.groups();width={'b':1,'w':2,'l':4}[width]
        arguments=args.split(',');destination=arguments[-1].strip()
        if destination not in (*PUBLICATION,'ready_title_display','ready_game_generation','back_copper','ready_generation'):continue
        rules[pc]=dict(pc=pc,address=symbols[destination],bytes=width,operation=operation,
            source=arguments[0].strip() if len(arguments)>1 else None,
            destination=destination,instruction=text)
    assert rules
    return rules


class Observer(TraceCollector):
    def __init__(self,symbols,initial,read,regions,listing,segments,locations,path):
        super().__init__(symbols,initial,symbols['core_trace_marker'],symbols['core_trace_arguments'])
        self.read=read;self.regions=regions;self.raw=Path(path).open('w')
        self.raw_bytes=0;self.notifications=0;self.drops=0;self.pending=None
        self.api_rows=[];self.frozen=False;self.problems=[];self.stack_min=symbols['game_stack_top']
        self.callback_rows=[];self.drain_checks=0;self.current_callback=None;self.timer_start=None;self.timer_origin=None
        self.input_shadow={n:bytearray(read(symbols[n],size)) for n,size in INPUTS}
        self.physical_edges=[];self.joystick_pressed_observations=[];self.expected_joystick_pressed=[0,0]
        self.rules=irq_rules(listing,symbols,segments,locations)
        self.outside_publication_rules=outside_publication_rules(listing,symbols,segments)
        self.outside_publication_writes=[]
        self.irq_writes=[];self.irq_inside=0;self.body_counts=[];self.audio_writes=[]
        acknowledgements=sorted(pc for pc,r in self.rules.items() if r['destination'].lower()=='$dff09c')
        self.irq_entry_pc,self.irq_exit_pc=acknowledgements
        self.publication={n:bytearray(read(symbols[n],4 if 'copper' in n else
            1 if n in ('blank_seen','display_ready','ready_completed','ready_title_display') else 2))
            for n in (*PUBLICATION,'ready_title_display','ready_game_generation')}
        self.source_shadow={n:bytearray(read(symbols[n],size)) for n,size in
            (('back_copper',4),('ready_generation',2),('simulation_started_updates',2))}
        self.producer_bank=None
        self.beam_reads={};self.rts_pcs=set();self.restore_dummy_pcs=set()
        for row in _units(listing):
            pc=segments[row['hunk']]['start']+row['start']
            if row['encoded'].lower()=='4e75':self.rts_pcs.add(pc)
            if (re.fullmatch(r'4cdf[0-9a-f]{4}',row['encoded'].lower())
                    and int(row['encoded'][4:],16)
                    and re.fullmatch(r'movem\.l\s+\(sp\)\+,[dDaA0-9/.-]+',row['statement'].split(';',1)[0].strip())):
                self.restore_dummy_pcs.add(pc)
            if symbols['read_presentation_line']<=pc<symbols['select_video_standard']:
                match=re.fullmatch(r'move\.w\s+\$(dff004|dff006),d[012]',row['statement'].strip())
                if match:self.beam_reads[pc]=int(match[1],16)
        assert len(self.beam_reads)==3
        self.meta=bytearray(read(symbols['game_preview_state'],110))
        self.history=bytearray(read(symbols['game_history_state'],72))
        self.slot=symbols['game_stack_top']-74 # callback+hook+SR+15 registers+JSR
        self.return_store=LongwordObserver();self.return_reads=LongwordObserver()

    def field(self,name,size):
        if self.start<=self.symbols[name]<self.stop:return super().field(name,size)
        for start,shadow in ((self.symbols['game_preview_state'],self.meta),
                             (self.symbols['game_history_state'],self.history)):
            offset=self.symbols[name]-start
            if 0<=offset<=len(shadow)-size:return bytes(shadow[offset:offset+size])
        return self.read(self.symbols[name],size)

    def number(self,name,size=2):return int.from_bytes(self.field(name,size),'big')

    def _marker(self,value,position):
        if value in self.operations:
            before=self.state().hex()
            ownership=dict(active=self.number('game_preview_active',1),
                status=self.number('game_preview_status'),variant=self.number('game_preview_variant',1))
            super()._marker(value,position)
            self.active.update(before=before,ownership=ownership)
        else:super()._marker(value,position)

    def watches(self,inside=False):
        ranges=super().watches()+[{'addr':self.symbols[n],'len':length,'access':'write'}
            for n,length in [('game_preview_storage',5550),('game_history_state',72),
                             ('game_history_buffer',80318),*INPUTS]]
        ranges += [{'addr':self.symbols['simulation_started_updates'],'len':2,'access':'write'},
            {'addr':self.symbols['simulation_timer_origin'],'len':2,'access':'write'},
            {'addr':0xbfde00,'len':1,'access':'write'}]
        ranges += [{'addr':0xdff0a0,'len':0x40,'access':'write'},
            {'addr':0xdff096,'len':2,'access':'write'},
            {'addr':0xdff09e,'len':2,'access':'write'}]
        for name,data in {**self.publication,**self.source_shadow}.items():
            ranges.append({'addr':self.symbols[name],'len':len(data),'access':'write'})
        if inside:
            ranges += [{'addr':0,'len':0x1000000,'access':'write'}]
            ranges += [{'addr':self.slot,'len':4,'access':'read'},
                {'addr':0xdff000,'len':0x200,'access':'access'},
                {'addr':0xbf0000,'len':0x10000,'access':'access'}]
        return ranges

    def begin(self,name):
        assert self.pending is None
        self.pending=dict(name=name,begin=None,end=None,bodies=0,irq=0,irq_acknowledgements=0)

    def finish(self):
        self.drain_checks+=1
        self.raw.flush()
        assert not self.drops, ('Native observation dropped notifications/accesses',self.drops)
        assert not self.problems,self.problems[0] if self.problems else None
        assert self.raw_bytes<RAW_CAP-RESERVE,'Native raw cap approached at completed public boundary'
        if self.pending is None:return None
        row=self.pending;self.pending=None
        assert row['begin'] is not None and row['end'] is not None,'Incomplete actual JSR/RTS bracket'
        assert row['end']['cck']>=row['begin']['cck']
        assert row['irq_acknowledgements']==row['irq']*2,'Unpaired actual presentation IRQ acknowledgements'
        row['elapsed_cck']=row['end']['cck']-row['begin']['cck']
        self.api_rows.append(row);return row

    def inside_api(self):
        return self.pending is not None and self.pending.get('begin') is not None and self.pending.get('end') is None

    def _guard(self,r):
        a,size,pc,value=r['addr'],r['size'],r['pc'],r['value']
        s=self.symbols
        overlap=lambda name,length:a<s[name]+length and a+size>s[name]
        contained=lambda name,length:s[name]<=a<a+size<=s[name]+length
        if self.frozen and overlap('game_history_buffer',80318):
            self.problems.append('CPU writes frozen history/live backup')
        audio=(a<0xdff0e0 and a+size>0xdff0a0) or (a<0xdff0a0 and a+size>0xdff09e)
        if audio:self.audio_writes.append(dict(pc=pc,address=a,size=size,value=value,position=r['position'],frozen=self.frozen))
        if not self.inside_api():
            publication_write=any(a<s[name]+len(data) and a+size>s[name]
                for name,data in {**self.publication,**{n:d for n,d in getattr(self,'source_shadow',{}).items() if n!='simulation_started_updates'}}.items())
            if self.frozen and publication_write:
                rule=self.rules.get(pc)
                if rule is not None:
                    # Reuse the exact source/value IRQ guard, without API counts.
                    self.irq_write(r,rule)
                else:
                    rule=self.outside_publication_rules.get(pc)
                    if not (rule and rule['address']<=a<a+size<=rule['address']+rule['bytes']):
                        self.problems.append('Unattributed frozen native publication write')
                    else:
                        if rule['destination']=='ready_completed' and pc<s['discard_ready_scene']:
                            self.producer_bank=(int.from_bytes(self.publication['ready_copper'],'big')
                                or int.from_bytes(self.publication['spare_copper'],'big'))
                        if rule['operation']=='clr':expected=0
                        elif rule['operation']=='st':expected=(1<<(8*rule['bytes']))-1
                        elif rule['source'] in self.publication:expected=int.from_bytes(self.publication[rule['source']],'big')
                        elif rule['source'] in self.source_shadow:expected=int.from_bytes(self.source_shadow[rule['source']],'big')
                        elif rule['source'] in ('game_accept_count','game_title_display'):
                            expected=self.number(rule['source'],rule['bytes'])
                        elif rule['source']=='d0':
                            assert self.producer_bank is not None,'No tracked native producer bank'
                            expected=self.producer_bank
                        elif rule['source'].startswith('#'):expected=int(rule['source'][1:])
                        else:raise AssertionError('Unspecified native producer source: '+str(rule['source']))
                        encoded=(expected&((1<<(rule['bytes']*8))-1)).to_bytes(rule['bytes'],'big')
                        if value.to_bytes(size,'big')!=encoded[a-rule['address']:a-rule['address']+size]:
                            self.problems.append('Incorrect actual native UI producer write value')
                        self.outside_publication_writes.append(dict(pc=pc,address=a,size=size,
                            value=value,position=r['position']))
            rule=self.rules.get(pc)
            if not publication_write and rule and rule['address']<=a<a+size<=rule['address']+rule['bytes']:
                self.irq_write(r,rule)
            if self.frozen and overlap('game_preview_storage',5550):self.problems.append('External caller writes frozen preview context')
            if self.frozen and audio:self.problems.append('External native caller writes frozen audio/config hardware')
            if self.frozen and a<0xdff098 and a+size>0xdff096:
                rule=self.rules.get(pc)
                if not (rule and a==0xdff096 and rule['address']==0xdff096 and size==2
                        and value==int(rule['source'][2:],16)):
                    self.problems.append('External frozen caller writes DMA configuration')
            if self.frozen and (overlap('game_core_state',318) or overlap('game_history_state',72)):
                self.problems.append('External native caller writes frozen selected/history state')
            return
        if s['game_stack_bottom']<=a<a+size<=s['game_stack_top']:
            self.stack_min=min(self.stack_min,a);return
        if contained('game_preview_storage',5550):return
        if contained('preview_native_mailbox',50):return
        if contained('core_trace_arguments',12) or contained('core_trace_marker',2):return
        if contained('game_core_state',318) or contained('game_history_state',72):return
        if self.pending['name']=='game_history_freeze' and overlap('game_history_buffer',80318):return
        rule=self.rules.get(pc)
        if rule and rule['address']<=a<a+size<=rule['address']+rule['bytes']:
            self.irq_write(r,rule);return
        self.problems.append(f'Forbidden native API nonstate/hardware write {pc:#x}->{a:#x}/{size}')

    def irq_write(self,r,rule):
        a,size,pc,value=r['addr'],r['size'],r['pc'],r['value']
        s=self.symbols
        source=rule['source'];operation=rule['operation']
        current=int.from_bytes(self.publication.get(rule['destination'],b'\0'),'big')
        if operation=='clr':expected=0
        elif operation in ('addq','subq'):
            amount=int(source[1:]);expected=current+(amount if operation=='addq' else -amount)
        elif source.startswith('#'):
            text=source[1:];expected=int(text[1:],16) if text.startswith('$') else int(text)
        elif source in self.publication:expected=int.from_bytes(self.publication[source],'big')
        elif source=='d0':
            expected=s['title_copper'] if self.publication['ready_title_display'][0] else int.from_bytes(self.publication['ready_copper'],'big')
        else:raise AssertionError('Unspecified presentation IRQ value source: '+str(source))
        expected=(expected&((1<<(8*rule['bytes']))-1)).to_bytes(rule['bytes'],'big')
        offset=a-rule['address']
        if value.to_bytes(size,'big')!=expected[offset:offset+size]:
            self.problems.append('Incorrect actual presentation IRQ write value')
        self.irq_writes.append(dict(pc=pc,address=a,size=size,value=value,position=r['position']))
        if rule['destination'].lower()=='$dff09c' and self.inside_api():
            self.pending['irq_acknowledgements']+=1
            if pc==self.irq_entry_pc:self.pending['irq']+=1;self.irq_inside+=1
        return


    def return_read(self,record):
        """MOVEM's extra first-word read is not the actual RTS return."""
        if not self.inside_api():return
        pc,address,size,value=record['pc'],record['addr'],record['size'],record['value']
        if pc in self.rts_pcs:
            result=self.return_reads.write(address-self.slot,value,size,pc)
            if result is not None:
                assert result==self.symbols['preview_native_after'],'RTS returns to another address'
                self.pending['end']=record['position']
            return
        assert (pc in self.restore_dummy_pcs and address==self.slot and size==2
                and value==self.symbols['preview_native_after']>>16), 'Return-slot read is not an exact emitted MOVEM dummy read or RTS'
        self.pending.setdefault('restore_dummy_reads',[]).append(record)

    def return_slot_write(self,record):
        # A presentation IRQ before JSR or after RTS legitimately reuses this
        # future/free stack slot. It is outside the actual API return bracket.
        if not self.inside_api():
            if self.pending.get('begin') is not None or record['pc']!=self.symbols['preview_native_call']:return
            self.pending['begin']=record['position']
            self.stack_min=min(self.stack_min,record['addr'])
        assert record['pc']==self.symbols['preview_native_call'],'Actual JSR return slot overwritten'
        result=self.return_store.write(record['addr']-self.slot,record['value'],record['size'],record['pc'])
        if result is not None:assert result==self.symbols['preview_native_after']

    def input_write(self,name,address,data,position):
        """Physical edges come from raw native samples, not host commands/timers."""
        shadow=self.input_shadow[name];offset=address-self.symbols[name]
        previous=bytes(shadow[offset:offset+len(data)])
        for n,(old,new) in enumerate(zip(previous,data),offset):
            if name in PHYSICAL_INPUTS and old!=new:
                if name=='game_keyboard_matrix':assert old in (0,1) and new in (0,1)
                self.physical_edges.append(dict(name=name,index=n,old=old,new=new,
                    pressed_bits=new&~old,released_bits=old&~new,position=position,
                    callback=self.current_callback['callback'] if self.current_callback is not None else None,
                    frozen=self.frozen))
                if self.current_callback is not None:self.current_callback['fresh_input']=True
            if name=='ui_joystick_previous':self.expected_joystick_pressed[n]=new&~old
            if name=='ui_joystick_pressed':
                assert new==self.expected_joystick_pressed[n],'Native raw pressed mask differs from actual previous/current samples'
                self.joystick_pressed_observations.append(dict(index=n,value=new,
                    expected=self.expected_joystick_pressed[n],position=position))
        shadow[offset:offset+len(data)]=data

    def observe(self,message):
        encoded=json.dumps(message,separators=(',',':'))+'\n'
        self.raw_bytes+=len(encoded.encode());self.notifications+=1
        if self.raw_bytes<=RAW_CAP:self.raw.write(encoded)
        else:self.problems.append('Native raw evidence cap exceeded')
        r=message.get('params',{})
        if message.get('method','').startswith('event.') and 'dropped_notifications' not in r:
            self.problems.append('Notification lacks explicit overflow telemetry')
        self.drops+=r.get('dropped_events',0)+r.get('dropped_notifications',0)
        if message.get('method')!='event.mmio':return
        a,size,value=r['addr'],r['size'],r['value'];data=value.to_bytes(size,'big')
        if r['access']=='write':
            self._guard(r)
            if a==0xbfde00 and value==1 and self.timer_start is None:self.timer_start=r['position']['cck']
            if a==self.symbols['simulation_timer_origin']:self.timer_origin=value
            if a==self.symbols['simulation_started_updates']:
                assert self.current_callback is None,'Missing native callback completion'
                self.current_callback=dict(callback=value,entry=r['position'],fresh_input=False)
            if a==self.symbols['simulation_updates'] and self.current_callback is not None:
                assert value==self.current_callback['callback'],'Native callback ordinal mismatch'
                self.current_callback['completion']=r['position'];self.callback_rows.append(self.current_callback);self.current_callback=None
            for name,shadow in self.input_shadow.items():
                start=self.symbols[name]
                if start<=a<a+size<=start+len(shadow):
                    self.input_write(name,a,data,r['position'])
            for start,shadow in ((self.symbols['game_preview_state'],self.meta),
                                 (self.symbols['game_history_state'],self.history)):
                if start<=a<a+size<=start+len(shadow):shadow[a-start:a-start+size]=data
            for name,shadow in {**self.publication,**self.source_shadow}.items():
                start=self.symbols[name]
                if start<=a<a+size<=start+len(shadow):shadow[a-start:a-start+size]=data
            if self.start<=a<a+size<=self.stop:
                self.shadow[a-self.start:a-self.start+size]=data;return
            if self.pending and self.slot<=a<a+size<=self.slot+4:
                self.return_slot_write(r)
        elif self.inside_api() and a>=0xbf0000:
            if not (self.beam_reads.get(r['pc'])==a and size==2):
                self.problems.append('Forbidden native API hardware read')
        elif self.pending and self.slot<=a<a+size<=self.slot+4:
            self.return_read(r)
        if a==self.marker and value in self.operations and self.inside_api():self.pending['bodies']+=1
        # Canonical copying outside logical bodies is already reconstructed above.
        # The existing mailbox decoder remains the independent semantic protocol.
        if a==self.marker or self.arguments<=a<a+size<=self.arguments+12 or a==self.symbols['simulation_updates']:
            super().observe(message)

    def close(self):self.raw.close()
