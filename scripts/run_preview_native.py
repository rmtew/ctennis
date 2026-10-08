"""Finite actual PAL/NTSC paused preview observation (campaign-owned only)."""
import argparse
import gzip
import hashlib
import json
import os
import re
from pathlib import Path
from fractions import Fraction
from build_match_core import build as build_core,load_image
from build_native_game import build as build_native
from check_shared_core_bytes import normalized
from copperline_test_session import NativeControlSession
from history_proof import attach,attempts,cursor,field
from match_core_cpu import Core,cpu_tool_inputs
from native_evidence import (ReportRun,atomic_json,assembly_inputs,python_inputs,
    compile_manifest,digest,inputs_for,snapshot,status)
from native_hunk import loaded_hunks,hunk_layout
from native_metrics import memory_summary
from native_metrics_observation import distribution
from native_tools import ROOT,ASSEMBLER,run,emulator_config
from ordinary_cadence import chip_memory
from preview_extended_proof import continuous,table,value
from preview_native_observation import Observer,INPUTS,RAW_CAP
from run_shared_match_core import READONLY

CAPS=dict(accepted_request_generations=7,playing_dispatches=512,ordinary_operations=2049,
    title_callbacks=256,paused_callbacks=2048,video_fields=4096,seconds=70,
    worker_calls_per_job=8192,samples_per_path=256,raw_bytes=RAW_CAP)
COMMANDS=('game_history_freeze','game_history_seek','game_preview_request',
    'game_preview_step','game_preview_result','game_preview_cancel','game_history_resume_latest')


def overlay(directory):
    original=ROOT/'amiga/main.s';text=original.read_text()
    anchor='        bsr     game_native_commands\n        tst.b   ui_paused'
    assert text.count(anchor)==1,'Native after-physical-sampling hook anchor changed'
    text=text.replace(anchor,'        bsr     game_native_commands\n        jsr     preview_native_hook\n        tst.b   ui_paused')
    include='        include "amiga/game/preview.s"'
    assert text.count(include)==1,'Preview worker include anchor changed'
    text=text.replace(include,'preview_native_worker_begin:\n'+include+'\npreview_native_worker_end:')
    source=directory/'main-preview-observer.s'
    source.write_text(text+'\n        include "scripts/preview_native_fixture.s"\n')
    executable,listing=directory/'preview-native',directory/'preview-native.lst'
    run([str(ASSEMBLER),'-Fhunkexe','-kick1hunks','-m68000','-DENHANCED_INTERFACE=1',
        '-DCORE_TRACE=1','-DDEMO_RECORDING=1','-L',str(listing),'-o',str(executable),
        str(source.relative_to(ROOT))])
    manifest=compile_manifest(executable,listing)
    identity=dict(original_sources=snapshot([original,ROOT/'scripts/preview_native_fixture.s']),
        generated_sources=snapshot([source]),insertion_anchor=anchor,
        seed_policy='DEMO_RECORDING-selection-only',
        scope='Test-only physical callback mailbox; original worker and gameplay source unchanged.')
    manifest['files'].update(identity['original_sources']);manifest['preview_fixture']=identity
    atomic_json(str(executable)+'.compile.json',manifest)
    return executable,listing,manifest,identity


class ObservedSession(NativeControlSession):
    """Observer-local literal RPC archive; shared CPU receipt inputs untouched."""
    def __enter__(self):
        self.directory.mkdir(parents=True,exist_ok=True)
        self.rpc_path=self.directory/'rpc.jsonl.gz'
        self.rpc=gzip.open(self.rpc_path,'wt',encoding='utf-8',compresslevel=3)
        self.rpc_uncompressed_bytes=0;self.rpc_records=0;self.rpc_calls=0
        return super().__enter__()

    def record_rpc(self,value):
        text=json.dumps(value,separators=(',',':'))+'\n'
        self.rpc.write(text);self.rpc_uncompressed_bytes+=len(text.encode());self.rpc_records+=1

    def flush_rpc(self):self.rpc.flush()

    def inspect(self,method,arguments=None):
        self.rpc_calls+=1;call=self.rpc_calls
        self.record_rpc(dict(call=call,type='request',method=method,arguments=arguments or {}))
        try:
            result=super().inspect(method,arguments)
        except BaseException as error:
            self.record_rpc(dict(call=call,type='error',error=str(error)));self.flush_rpc();raise
        self.record_rpc(dict(call=call,type='reply',result=result))
        return result

    def __exit__(self,*arguments):
        try:return super().__exit__(*arguments)
        finally:self.rpc.close()


class Native:
    """Guest mailbox calls; host writes only command arguments, never core state."""
    def __init__(self,session,executable,listing,standard,cpu):
        self.directory=executable.parent;self.maximum_job_calls=0
        self.session=session;self.cpu=cpu;self.normal=[];self.states={};self.launches=[]
        self.selected_seconds=None;self.selected_frame=None;self.requests=0;self.paused_callbacks=0
        self.public_checks=0;self.callback_stops=[];self.input_actions=[];self.frozen_intervals=[];self.pause_volume_writes=[]
        config=emulator_config()
        session.inspect('session_launch',dict(binary=config['tools']['copperline'],run=str(executable),
            args=['--chipset','OCS','--video',standard,'--cpu','68000','--chip','512K',
                  '--slow','0','--fast','0','--noaudio',config['inputs']['amiga_rom']]))
        self.stop=session.inspect('run_until',{'seconds':30})
        assert self.stop['reason']=='loadseg',self.stop
        self.segments=session.inspect('segments.list')['current']
        locations={n:(int(h),int(o,16)) for n,h,o in re.findall(
            r'^([A-Za-z_]\w*)\s+(\d\d):([0-9a-fA-F]{8})\s*$',listing.read_text(),re.M)}
        self.symbols={n:self.segments[h]['start']+o for n,(h,o) in locations.items()}
        self.hunks=loaded_hunks(executable,self.segments,self.read)
        self.worker=self.block('preview_native_worker_begin','preview_native_worker_end')
        regions=[(row['start'],row['size']) for row in self.segments]
        s=self.symbols
        self.observer=Observer(s,self.read(s['game_core_state'],318),self.read,regions,
            listing.read_text(),self.segments,locations,executable.parent/'events.jsonl')
        self.observer.on_row=self.logical
        session.notification_handler=self.observer.observe
        old=cpu.instruction
        def launches(pc):
            old(pc)
            if field(cpu,'game_history_replaying',1):return
            if pc not in (cpu.symbols['game_history_serve'],cpu.symbols['game_history_contact']):return
            end=cpu.cpu.r_reg(7)&0xffff
            self.launches.append(dict(origin=cursor(cpu),end=end,
                kind=3 if pc==cpu.symbols['game_history_serve'] else 1,
                human=not bool(cpu.mem.r8(cpu.symbols['game_play_state']+54+end))))
            if pc==cpu.symbols['game_history_contact'] and field(cpu,'game_history_probe_active',1):
                address=cpu.symbols['game_history_attempts']+field(cpu,'game_history_probe_index')*12
                self.launches[-1]['episode_origin']=int.from_bytes(cpu.mem.r_block(address,8),'big')
        cpu.cpu.set_instr_hook_callback(launches)
        self.subscribe(False)
        self.breakpoint=self.arm('preview_native_before')
        self.stop=session.inspect('run_until',{'seconds':self.stop['seconds']+3})
        assert self.stop['pc']==s['preview_native_before'],self.stop
        self.at_before=True;self.callback_stops.append(dict(self.stop));self.observer.finish()

    def read(self,address,length):
        return bytes.fromhex(self.session.inspect('mem_read',{'addr':address,'len':length})['data'])

    def block(self,first,last):return self.read(self.symbols[first],self.symbols[last]-self.symbols[first])
    def number(self,name,width=2):return int.from_bytes(self.read(self.symbols[name],width),'big')
    def arm(self,name):return self.session.inspect('break_add',{'kind':'pc','addr':self.symbols[name]})['id']

    def subscribe(self,inside):
        telemetry=self.session.inspect('events.subscribe',{'events':['mmio','frame','bus'],
            'mmio':self.observer.watches(inside)})
        assert telemetry.get('dropped_notifications')==0,'Subscription reports dropped notifications' 

    def logical(self,row):
        if self.observer.pending is not None:return
        self.cpu.clear_events();self.cpu.call_logical(row['operation'],row['arguments'])
        assert self.cpu.state().hex()==row['state'],('Actual native ordinary state',row['index'])
        assert self.cpu.events==row['events'],('Actual native ordinary intents',row['index'])
        if row['operation']=='game_core_init':attach(self.cpu);self.states[0]=self.cpu.state();return
        self.normal.append((row['operation'],row['arguments']))
        self.states[len(self.normal)]=self.cpu.state()
        if row['operation']=='game_core_select':
            assert row['arguments'][1]==0xace1,'Fixture selection must declare its actual seed'
            self.selected_seconds=row['end']['seconds'];self.selected_frame=row['end']['frame']
            self.selection_operation=len(self.normal)-1

    def check_caps(self):
        assert total_bytes(self.directory.iterdir())<RAW_CAP-8*1024*1024,'All-artifact native cap approached'
        if self.selected_seconds is None:
            assert len(self.callback_stops)<=CAPS['title_callbacks'],'Title acquisition cap'
            return
        ordinary=len(self.normal)-self.selection_operation
        dispatches=sum(n=='game_tick_dispatch' for n,_ in self.normal[self.selection_operation:])
        assert ordinary<=CAPS['ordinary_operations'],'Ordinary operation acquisition cap'
        assert dispatches<=CAPS['playing_dispatches'],'Playing dispatch acquisition cap'
        assert self.paused_callbacks<=CAPS['paused_callbacks'],'Paused callback cap'
        assert self.stop['frame']-self.selected_frame<=CAPS['video_fields'],'Video field cap'
        assert self.stop['seconds']-self.selected_seconds<=CAPS['seconds'],'Emulated duration cap'
        assert self.requests<=CAPS['accepted_request_generations'],'Accepted request count cap'

    def next_callback(self):
        assert not self.at_before
        self.subscribe(False);self.session.inspect('break_remove',{'id':self.breakpoint})
        self.breakpoint=self.arm('preview_native_before')
        self.stop=self.session.inspect('run_until',{'seconds':self.stop['seconds']+.2})
        assert self.stop['pc']==self.symbols['preview_native_before'],self.stop
        self.at_before=True;self.callback_stops.append(dict(self.stop))
        if self.observer.frozen:self.paused_callbacks+=1
        self.observer.finish();self.check_caps()
        if self.observer.frozen:assert self.number('ui_paused',1),'Frozen owner lost actual UI pause' 

    def idle(self):
        assert self.at_before
        self.session.inspect('break_remove',{'id':self.breakpoint})
        self.breakpoint=self.arm('preview_native_return')
        self.stop=self.session.inspect('run_until',{'seconds':self.stop['seconds']+.2})
        assert self.stop['pc']==self.symbols['preview_native_return'],self.stop
        self.at_before=False;self.observer.finish();self.next_callback()

    def call(self,name,args=(),accepted=True):
        if not self.at_before:self.next_callback()
        self.session.flush_rpc()
        self.observer.finish() # Drain the genuine sampling interval before owning an API.
        before=self.block('game_core_state','game_core_state_end')
        metadata=self.block('game_history_state','game_history_state_end')
        store=self.block('game_history_buffer','game_history_buffer_end')
        inputs={n:self.read(self.symbols[n],size) for n,size in INPUTS}
        frame=self.read(self.symbols['game_stack_top']-70,62)
        arguments=list(args)+[0]*(6-len(args))
        self.session.inspect('mem.write',{'addr':self.symbols['preview_native_arguments'],
            'data':b''.join(v.to_bytes(4,'big') for v in arguments).hex()})
        self.session.inspect('mem.write',{'addr':self.symbols['preview_native_command'],
            'data':(COMMANDS.index(name)+1).to_bytes(2,'big').hex()})
        self.observer.begin(name);self.subscribe(True)
        self.session.inspect('break_remove',{'id':self.breakpoint})
        self.breakpoint=self.arm('preview_native_return')
        self.stop=self.session.inspect('run_until',{'seconds':self.stop['seconds']+1})
        assert self.stop['pc']==self.symbols['preview_native_return'],self.stop
        self.at_before=False;cost=self.observer.finish();self.public_checks+=1
        assert self.read(self.symbols['game_stack_top']-70,62)==frame,'Caller register/SR frame overwritten'
        assert all(self.read(self.symbols[n],size)==data for n,data in inputs.items() for size in [len(data)]),'API mutates native input/audio shadows'
        result=[int.from_bytes(self.read(self.symbols['preview_native_results']+4*i,4),'big') for i in range(6)]
        assert result[0]==int(accepted),(name,result)
        after_store=self.block('game_history_buffer','game_history_buffer_end')
        if name.startswith('game_preview_'):
            assert self.block('game_core_state','game_core_state_end')==before
            assert self.block('game_history_state','game_history_state_end')==metadata
            assert after_store==store,'Preview changes frozen recorder/live backup'
        elif name=='game_history_freeze':
            assert after_store[:-318]==store[:-318] and after_store[-318:]==before
            self.cpu.call(name);self.observer.frozen=True
            assert self.block('game_core_state','game_core_state_end')==before
            self.frozen_intervals.append(dict(begin=cost['end'],end=None))
        elif name=='game_history_seek':
            assert after_store==store
            self.cpu.call(name,{0:arguments[0],1:arguments[1]})
            assert self.cpu.cpu.r_reg(0)==1 and self.cpu.state()==self.block('game_core_state','game_core_state_end')
        elif name=='game_history_resume_latest':
            assert after_store==store
            self.cpu.call(name);self.observer.frozen=False
            self.frozen_intervals[-1]['end']=cost['begin']
        if name=='game_preview_request' and accepted:self.requests+=1
        assert self.block('preview_native_worker_begin','preview_native_worker_end')==self.worker,'Loaded worker bytes changed'
        self.session.flush_rpc()
        self.check_caps();return result,cost

    def key(self,raw,pressed):
        self.session.inspect('input_key',{'rawkey':raw,'action':'press' if pressed else 'release'})
        self.input_actions.append(dict(kind='keyboard',rawkey=raw,pressed=pressed))
        for _ in range(8):
            if not self.at_before:self.next_callback()
            else:self.idle()
            if self.read(self.symbols['game_keyboard_matrix']+raw,1)==bytes([int(pressed)]):break
        else:raise AssertionError('Actual keyboard sample not observed within eight callbacks')

    def joystick(self,pressed):
        self.session.inspect('input_set_port',{'port':2,'device':'joystick'})
        self.session.inspect('input_joy',{'port':2,'left':pressed})
        self.input_actions.append(dict(kind='joystick',pressed=pressed))
        for _ in range(8):
            if not self.at_before:self.next_callback()
            else:self.idle()
            if bool(self.number('ui_joystick_bits',1)&4)==pressed:break
        else:raise AssertionError('Actual physical joystick direction not sampled')

    def fire(self,pressed):
        self.session.inspect('input_set_port',{'port':2,'device':'joystick'})
        self.session.inspect('input_joy',{'port':2,'red':pressed})
        self.input_actions.append(dict(kind='fire',pressed=pressed))
        self.idle()

    def freeze(self):
        first_audio=len(self.observer.audio_writes)
        self.key(0x19,True);self.key(0x19,False)
        assert self.number('ui_paused',1),'Ordinary physical pause did not own callback'
        pause_writes=[r for r in self.observer.audio_writes[first_audio:] if r['address'] in (0xdff0a8,0xdff0b8,0xdff0d8) and r['value']==0]
        assert {r['address'] for r in pause_writes}=={0xdff0a8,0xdff0b8,0xdff0d8},'Actual native pause volume zeros absent'
        self.pause_volume_writes.extend(pause_writes)
        self.call('game_history_freeze')
        native=self.block('game_history_buffer','game_history_live_backup')
        actual=bytes(self.cpu.mem.r_block(self.cpu.symbols['game_history_buffer'],80318-318))
        assert native==actual,'Actual native recording differs from same actual core'

    def resume(self):
        self.call('game_history_resume_latest')
        self.key(0x19,True);self.key(0x19,False)
        assert not self.number('ui_paused',1),'Ordinary physical resume not observed'

    def position(self,end):
        state=self.block('game_core_state','game_core_state_end')
        offset=self.symbols['game_play_state']-self.symbols['game_core_state']+10*end
        return state[offset+3],state[offset+2]

    def request(self,ordinal,x,y):
        generation=self.number('game_preview_generation',4)
        self.call('game_preview_request',[generation,ordinal,x,y])
        assert self.number('game_preview_generation',4)==generation+1
        return generation+1

    def step(self,generation,budget=4):
        _,cost=self.call('game_preview_step',[generation,budget])
        assert cost['bodies']<=budget,'Native worker exceeds actual operation cap'
        return cost

    def snapshot_result(self):
        counts=[self.number('game_preview_counts',2),int.from_bytes(self.read(self.symbols['game_preview_counts']+2,2),'big')]
        contexts=[self.block('game_preview_held_state','game_preview_released_state'),
            self.block('game_preview_released_state','game_preview_paths')]
        outcomes=[int.from_bytes(self.read(self.symbols['game_preview_outcomes']+2*i,2),'big') for i in (0,1)]
        return dict(edited=self.block('game_preview_edited_state','game_preview_held_state'),
            contexts=contexts,paths=[self.read(self.symbols['game_preview_paths']+2048*i,8*n) for i,n in enumerate(counts)],
            outcomes=outcomes,prefix=self.number('game_preview_prefix_count'),
            incoming=self.number('game_preview_incoming',8),action=self.number('game_preview_action',8))

    def completed(self,name,ordinal,selection,end,x,y):
        print('Native paired job',name,'ordinal',ordinal,'selection',selection,flush=True)
        selected=self.block('game_core_state','game_core_state_end')
        first=len(self.observer.rows)
        was_ready=self.number('game_preview_status')==5 and self.number('game_preview_cache_valid')==1
        request_index=len(self.observer.api_rows)
        generation=self.request(ordinal,x,y)
        cache_hit=was_ready and self.number('game_preview_status')==2
        costs=[];worker_indices=[]
        for n in range(CAPS['worker_calls_per_job']):
            if self.number('game_preview_status')>=5:break
            if n==0:self.joystick(True);self.key(0x12,True)
            if n==2:self.joystick(False);self.key(0x12,False)
            worker_indices.append(len(self.observer.api_rows));costs.append(self.step(generation))
            if n%64==63:print('Native worker progress',name,n+1,'status',self.number('game_preview_status'),flush=True)
        else:raise AssertionError('Native paired job reached worker-call cap')
        assert self.number('game_preview_status')==5,'Native preview did not reach honest READY'
        result_index=len(self.observer.api_rows)
        registers,_=self.call('game_preview_result',[generation])
        result=self.snapshot_result()
        assert all(len(p)//8<=256 for p in result['paths'])
        assert registers[1:3]==[len(p)//8 for p in result['paths']]
        expected=bytearray(selected);offset=self.symbols['game_play_state']-self.symbols['game_core_state']+10*end
        expected[offset+3]=x;expected[offset+2]=y
        assert result['edited']==bytes(expected),'Native edit changes more than requested legal X/Y'
        traces={0:[],1:[]};outputs={0:[],1:[]};boundaries={0:[],1:[]};resolver=0
        for row in self.observer.rows[first:]:
            owner=row['ownership']
            if owner['active']==1:resolver+=1
            if owner['active']!=2:continue
            variant=owner['variant']
            traces[variant].append((row['operation'],row['arguments'],bytes.fromhex(row['before'])))
            outputs[variant].extend(row['events'])
            if row['operation']=='game_tick_dispatch':
                state=bytes.fromhex(row['state'])
                boundaries[variant].append(dict(contact=value(state,self.symbols,'game_contact'),
                    flight=value(state,self.symbols,'game_flight'),lifecycle=value(state,self.symbols,'game_lifecycle',2)))
        result['outputs']=[outputs[0],outputs[1]]
        classes=[{1:'landing',2:'net',3:'out',4:'interception',5:'no-contact',6:'limit',7:'lifecycle'}[v] for v in result['outcomes']]
        self.maximum_job_calls=max(self.maximum_job_calls,len(costs))
        request_begin=self.observer.api_rows[request_index]['begin']
        result_end=self.observer.api_rows[result_index]['end']
        costs_report=dict(generation=generation,cache_hit=cache_hit,resolver_operations=resolver,
            request_api_row_index=request_index,worker_api_row_indices=worker_indices,result_api_row_index=result_index,
            worker_calls=len(costs),worker_body_counts=[c['bodies'] for c in costs],
            maximum_worker_operations=max(c['bodies'] for c in costs),
            worker_elapsed_cck=sum(c['elapsed_cck'] for c in costs),
            maximum_worker_elapsed_cck=max(c['elapsed_cck'] for c in costs),
            fields_to_result=result_end['frame']-request_begin['frame'],seconds_to_result=result_end['seconds']-request_begin['seconds'])
        observation=dict(name=name,seed=0xace1,ordinal=ordinal,selection=selection,end=end,x=x,y=y,
            selected=selected,stream=list(self.normal),traces=traces,result=result,classes=classes,
            launches={0:[],1:[]},boundaries=boundaries,costs=costs_report,bounds=table(self.cpu,end),
            coincident=bool(self.number('game_preview_coincident')))
        return observation

    def replacement(self,phase,ordinal,end,x,y):
        first_call=len(self.observer.api_rows)
        generation=self.request(ordinal,x,y);rows=len(self.observer.rows)
        for _ in range(CAPS['worker_calls_per_job']):
            self.step(generation,1 if phase=='resolve' else 4)
            actual=[r for r in self.observer.rows[rows:] if
                r['ownership']['active']==(1 if phase=='resolve' else 2)
                and (phase=='resolve' or r['ownership']['status']==3)]
            if actual:break
        else:raise AssertionError('Native partial phase body unavailable within worker cap')
        bounds=table(self.cpu,end);new_x=x+1 if x<bounds['right']-1 else x-1
        assert bounds['left']<=new_x<bounds['right'] and new_x!=x
        new_generation=self.request(ordinal,new_x,y)
        assert new_generation>generation and self.number('game_preview_status')==1
        before=self.block('game_preview_storage','game_preview_storage_end')
        self.call('game_preview_result',[generation],accepted=False)
        assert self.block('game_preview_storage','game_preview_storage_end')==before
        rows=len(self.observer.rows)
        qualify_resolver(self,new_generation)
        resolver=sum(r['ownership']['active']==1 for r in self.observer.rows[rows:])
        assert resolver>0
        selected=self.block('game_core_state','game_core_state_end');expected=bytearray(selected)
        offset=self.symbols['game_play_state']-self.symbols['game_core_state']+10*end
        expected[offset+3]=new_x;expected[offset+2]=y
        assert self.block('game_preview_edited_state','game_preview_held_state')==bytes(expected)
        self.call('game_preview_cancel',[new_generation])
        before=self.block('game_preview_storage','game_preview_storage_end')
        self.call('game_preview_result',[new_generation],accepted=False)
        assert self.block('game_preview_storage','game_preview_storage_end')==before
        job_calls=sum(r['name']=='game_preview_step' for r in self.observer.api_rows[first_call:])
        assert job_calls<=CAPS['worker_calls_per_job']
        self.maximum_job_calls=max(self.maximum_job_calls,job_calls)
        return dict(case_id='replacement-'+phase,passed=True,partial_phase=phase,
            partial_body_operations=len(actual),old_generation=generation,new_generation=new_generation,
            old_position=[x,y],new_position=[new_x,y],replacement_resolver_operations=resolver,
            cold_replacement=True,edited_only_position_changed=True,old_result_rejected=True,
            canceled_result_rejected=True,selected_history_output_preserved=True)


def qualify_resolver(native,generation):
    """Budget one makes PRIME observable without executing either primer."""
    for _ in range(CAPS['worker_calls_per_job']):
        state=native.number('game_preview_status')
        if state==2:return
        assert state==1,('Resolver qualification crossed PRIME without observing it',state)
        native.step(generation,1)
    raise AssertionError('Replacement resolver cap')


def json_value(value):
    """Private observations are readbacks, never state supplied to the guest."""
    if isinstance(value,bytes):return value.hex()
    if isinstance(value,dict):return {str(k):json_value(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [json_value(v) for v in value]
    return value


def retained_candidate(native):
    """Actual completed index plus the preceding accepted opponent launch."""
    for ordinal,(probe,kind,end) in enumerate(attempts(native.cpu)):
        if kind not in (1,2):continue
        state=native.states.get(probe)
        if state is None:continue
        offset=native.cpu.symbols['game_play_state']-native.cpu.start
        if state[offset+54+end]:continue
        incoming=next((r for r in reversed(native.launches)
            if r['end']!=end and r['origin']<probe),None)
        if incoming is None:continue
        if kind==1 and not any(r.get('episode_origin')==probe and r['human']
                and r['end']==end for r in native.launches):continue
        assert cursor(native.cpu,'game_history_oldest')<=incoming['origin']<probe
        return dict(ordinal=ordinal,kind=kind,end=end,probe=probe,incoming=incoming['origin'])
    return None


def schedule(native,directory):
    """Seven accepted requests; all acquisition changes are physical inputs."""
    native.key(0x01,True);native.key(0x01,False)
    for _ in range(CAPS['playing_dispatches']):
        state=native.block('game_core_state','game_core_state_end')
        end=1 if value(state,native.symbols,'game_score_flags')&2 else 0
        player=native.symbols['game_play_state']-native.symbols['game_core_state']+10*end
        if (value(state,native.symbols,'game_lifecycle',2)==1 and state[player]==0x40
                and not state[player-10*end+54+end]):break
        native.idle()
    else:raise AssertionError('Current actual human serve setup absent within acquisition cap')
    native.freeze();selection=cursor(native.cpu,'game_history_position');x,y=native.position(end)
    observations=[native.completed('current-human-serve',0xffff,selection,end,x,y)]
    atomic_json(directory/'observations-unvalidated.json',json_value(observations))
    native.resume();native.fire(True)
    for _ in range(CAPS['playing_dispatches']):
        candidate=retained_candidate(native)
        if candidate is not None:break
        native.idle()
    else:raise AssertionError('Actual retained completed human return/miss with incoming context absent within acquisition cap')
    native.fire(False);native.freeze()
    native.call('game_history_seek',[candidate['probe']>>32,candidate['probe']&0xffffffff])
    end=candidate['end'];x,y=native.position(end);selection=candidate['probe']
    observations.append(native.completed('cold-incoming',candidate['ordinal'],selection,end,x,y))
    bounds=table(native.cpu,end);edited_x=x+1 if x<bounds['right']-1 else x-1
    assert bounds['left']<=edited_x<bounds['right'] and edited_x!=x
    observations.append(native.completed('warm-position-edit',candidate['ordinal'],selection,end,edited_x,y))
    cold,warm=observations[-2:];prefix=cold['result']['prefix']
    assert prefix==warm['result']['prefix'] and cold['result']['paths'][0][:8*prefix]==warm['result']['paths'][0][:8*prefix]
    assert observations[-1]['costs']['cache_hit'] and observations[-1]['costs']['resolver_operations']==0
    atomic_json(directory/'observations-unvalidated.json',json_value(observations))
    native.call('game_preview_cancel',[native.number('game_preview_generation',4)])
    replacements=[native.replacement(phase,candidate['ordinal'],end,x,y) for phase in ('resolve','held')]
    assert native.requests==7,'Accepted request schedule changed'
    native.resume()
    # Finish the final genuinely sampled callback; stop at its real caller.
    native.session.inspect('break_remove',{'id':native.breakpoint})
    native.breakpoint=native.arm('main_loop')
    native.stop=native.session.inspect('run_until',{'seconds':native.stop['seconds']+.2})
    assert native.stop['pc']==native.symbols['main_loop'],native.stop
    native.observer.finish();native.check_caps()
    assert native.observer.current_callback is None,'Final callback is incomplete'
    return observations,replacements,candidate


def measurement(native,video):
    observer=native.observer
    interval=Fraction((video['simulation_interval_whole']*65536+video['simulation_interval_fraction'])*5,65536)
    assert observer.timer_start is not None and observer.timer_origin is not None
    origin=observer.timer_start+(65535-observer.timer_origin)*5
    callbacks=observer.callback_rows
    assert callbacks and all('completion' in row for row in callbacks)
    values=[r['completion']['cck']-r['entry']['cck'] for r in callbacks]
    fresh=[v for v,r in zip(values,callbacks) if r['fresh_input']]
    workers=[r['elapsed_cck'] for r in observer.api_rows if r['name']=='game_preview_step']
    headrooms=[float(origin+r['callback']*interval-r['completion']['cck']) for r in callbacks]
    return dict(api_rows=observer.api_rows,worker_distribution=distribution(workers,interval),
        callback_distribution=distribution(values,interval),fresh_input_callback_distribution=distribution(fresh,interval),
        minimum_callback_headroom_cck=min(headrooms),stack_bytes=native.symbols['game_stack_top']-observer.stack_min)


def total_bytes(paths):
    return sum(path.stat().st_size for path in set(paths) if path.is_file())


def run(standard):
    directory=ROOT/'build/tests'/('preview-native-'+standard.lower());directory.mkdir(parents=True,exist_ok=True)
    path=directory/'report.json'
    target=dict(video=standard,cpu='68000',chipset='OCS',chip_kib=512,slow_kib=0,fast_kib=0)
    transaction=ReportRun([path],'preview-native','maintained-native','actual native physical sampling and paused worker')
    transaction.meta.update(target_role='legacy-validator-reference',actual_target=target,
        target_scope='evidence.target is a compatibility reference only; actual_target is the executed A500 target.')
    native=None
    try:
        paths,tools=inputs_for('preview-native','scripts/run_preview_native.py')
        cpu_paths,tools['machine68k']=cpu_tool_inputs()
        paths|=cpu_paths|{ROOT/'scripts/preview_native_fixture.s'}
        transaction.meta.update(files=snapshot(paths),tools=tools)
        transaction.meta['environment']['PYTHONPATH']=os.environ.get('PYTHONPATH')
        print('Preparing bounded native preview',standard,flush=True)
        _,product=build_native();standalone,_=build_core()
        product_listing=product.parent/'native.lst';core_listing=standalone.parent/'match-core.lst'
        executable,listing,manifest,overlay_identity=overlay(directory)
        product_manifest=compile_manifest(product,product_listing)
        core_manifest=compile_manifest(standalone,core_listing)
        expected=normalized(standalone,core_listing)
        assert normalized(product,product_listing)==expected and normalized(executable,listing)==expected
        image,symbols=load_image(standalone)
        with Core(image,symbols,readonly=READONLY) as cpu:
            with ObservedSession(directory) as session:
                native=Native(session,executable,listing,standard,cpu)
                observations,replacements,candidate=schedule(native,directory)
                video={n:native.number(n,size) for n,size in
                    (('presentation_last_line',2),('simulation_interval_whole',4),('simulation_interval_fraction',2))}
                expected_video=dict(zip(video,(311,11838,14906) if standard=='PAL' else (261,11947,13180)))
                assert video==expected_video,('Actual native video selector',video)
                costs=measurement(native,video)
                memory=memory_summary(chip_memory(native.read))
                worker_start=native.symbols['preview_native_worker_begin']
                worker_identity=dict(source_sha256=digest(ROOT/'amiga/game/preview.s'),
                    loaded_sha256=hashlib.sha256(native.worker).hexdigest(),bytes=len(native.worker),
                    loaded_start=worker_start,loaded_end=worker_start+len(native.worker),
                    fixture_executable_sha256=digest(executable))
                observer=native.observer
                physical=dict(joystick_press_edges=sum(e['pressed_bits'].bit_count() for e in observer.physical_edges if e['name']=='ui_joystick_bits'),
                    joystick_release_edges=sum(e['released_bits'].bit_count() for e in observer.physical_edges if e['name']=='ui_joystick_bits'),
                    keyboard_presses=sum(bool(e['pressed_bits']) for e in observer.physical_edges if e['name']=='game_keyboard_matrix'),
                    keyboard_releases=sum(bool(e['released_bits']) for e in observer.physical_edges if e['name']=='game_keyboard_matrix'),
                    pause_resume_observed=not native.number('ui_paused',1),
                    fresh_input_callbacks=sum(r['fresh_input'] for r in observer.callback_rows),pause_volume_zero_writes=native.pause_volume_writes,
                    observed_edges=observer.physical_edges,joystick_pressed_observations=observer.joystick_pressed_observations,
                    requested_commands=native.input_actions,scope='Observed raw joystick-bit/keymatrix transitions; counters do not count host requests.')
                ordinary=native.normal[native.selection_operation:]
                acquisition=dict(seed=0xace1,seed_policy='DEMO_RECORDING-selection-only',
                    ordinary_operations=len(ordinary),playing_dispatches=sum(n=='game_tick_dispatch' for n,_ in ordinary),
                    title_callbacks=sum(p['seconds']<native.selected_seconds for p in native.callback_stops),
                    completed_index_kind=candidate['kind'],incoming_origin=candidate['incoming'],
                    probe_origin=candidate['probe'],selected_cursor=candidate['probe'],ordinal=candidate['ordinal'],end=candidate['end'])
                observed={k:acquisition[k] for k in ('ordinary_operations','playing_dispatches','title_callbacks')}
                observed.update(accepted_request_generations=native.requests,paused_callbacks=native.paused_callbacks,
                    video_fields=native.stop['frame']-native.selected_frame,seconds=native.stop['seconds']-native.selected_seconds,
                    worker_calls_per_job=native.maximum_job_calls,
                    samples_per_path=max(len(p)//8 for o in observations for p in o['result']['paths']),raw_bytes=0)
                validation=dict(passed=True,canonical_bytes=318,history_metadata_bytes=72,
                    preview_storage_bytes=5550,preview_metadata_bytes=110,acquisition=acquisition,
                    replacement_cancel_cases=replacements,preservation={k:True for k in
                    ('selected_canonical','history_metadata','frozen_store','live_backup','caller_frame',
                     'input_globals','publication_irq_only','audio_cpu_configuration')},
                    interrupts=dict(inside_worker_entries=sum(r['irq'] for r in observer.api_rows if r['name']=='game_preview_step'),
                        inside_api_entries=observer.irq_inside,entry_exit_ack_pairs=True,
                        exact_pc_address_width_value_rules=[dict(pc=pc,**rule) for pc,rule in observer.rules.items()],keyboard_irq_allowances=0),
                    physical_inputs=physical,telemetry=dict(notifications=observer.notifications,
                        dropped_notifications=0,dropped_accesses=0,public_boundary_drain_checks=observer.drain_checks),
                    caps=CAPS,observed_caps=observed,costs=costs,
                    resources=dict(fixture_chip_free_bytes=memory['chip_free_bytes'],
                        fixture_loaded_bytes=sum(h['bytes'] for h in native.hunks),
                        product_static_loaded_bytes=hunk_layout(product)['loaded_payload_bytes']),
                    compiled_identity=dict(loaded_hunks=native.hunks,worker_bytes=worker_identity,overlay=overlay_identity,
                        normalized_shared_core=dict(matched=True,bytes=len(expected[0]),relocations=expected[1],
                            sink_branches=expected[2],sha256=hashlib.sha256(expected[0]).hexdigest()),
                        fixture_manifest_sha256=digest(Path(str(executable)+'.compile.json')),
                        product_manifest_sha256=digest(Path(str(product)+'.compile.json'))),
                    continuous_actual_core_equal=False)
                validation['preservation'].update(publication_scope='worker-api-irq-only; outside-api-native-ui-attributed',
                    input_scope='worker-api-only; native-physical-sampling-before-hook')
                validation['outside_publication']=dict(rules=list(observer.outside_publication_rules.values()),
                    writes=observer.outside_publication_writes,count=len(observer.outside_publication_writes))
                validation['frozen_intervals']=native.frozen_intervals
                atomic_json(directory/'native-results-unvalidated.json',json_value(validation))
                assert observer.irq_inside>0 and validation['interrupts']['inside_worker_entries']>0,'No actual IRQ inside workers'
                assert physical['fresh_input_callbacks']>0 and not observer.drops
                cpu.audit_reads()
                observer.close()
        validation['rpc_transcript']=dict(encoding='gzip-jsonl',path=str(session.rpc_path.relative_to(ROOT)),
            sha256=digest(session.rpc_path),compressed_bytes=session.rpc_path.stat().st_size,
            uncompressed_bytes=session.rpc_uncompressed_bytes,records=session.rpc_records,calls=session.rpc_calls,
            scope='Literal observer-local requests/replies; notifications are preserved separately in events.jsonl.')
        completed=[]
        for observation in observations:
            print('Comparing uninterrupted actual core',observation['name'],flush=True)
            row=continuous(image,symbols,observation)
            row.update(case_id=observation['name'],native_jsr_rts_preserved=True)
            completed.append(row)
        validation.update(completed_jobs=completed,continuous_actual_core_equal=True)
        report=dict(passed=True,execution='actual-native-paused-preview',target=target,native_video=video,
            preview_native_validation=validation,
            scope='Finite physical/native paused worker and actual IRQ/input/audio isolation; no UI prototype or full release gate. Seed fixed only at ordinary selection by DEMO_RECORDING.')
        artifacts=[p for p in directory.iterdir() if p.is_file() and p!=path]
        artifacts += [Path(str(product)+'.compile.json'),Path(str(standalone)+'.compile.json')]
        atomic_json(directory/'native-results-unvalidated.json',dict(report,receipt_validated=False))
        assert costs['minimum_callback_headroom_cck']>=0,('Actual native callback deadline miss',costs['minimum_callback_headroom_cck'])
        # Include the final receipt itself in the bound. Its size converges when
        # the decimal byte count has the same width; this only serializes evidence.
        for _ in range(3):
            transaction.finalize(path,report,compiled=[product_manifest,core_manifest,manifest],artifacts=artifacts)
            observed['raw_bytes']=total_bytes(artifacts+[path])
        assert observed['raw_bytes']<CAPS['raw_bytes']
        assert status(path)['status']=='passed',status(path)
        print(json.dumps(dict(passed=True,report=str(path),costs=costs,observed_caps=observed)),flush=True)
    except BaseException as error:
        if native is not None:
            atomic_json(directory/'failure-progress.json',dict(error=str(error),requests=native.requests,
                normal_operations=len(native.normal),api_rows=native.observer.api_rows,
                callback_rows=native.observer.callback_rows,guard_problems=native.observer.problems))
            native.observer.close()
        transaction.abort(error)
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ntsc',action='store_true')
    args=parser.parse_args();run('NTSC' if args.ntsc else 'PAL')
