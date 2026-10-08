"""Finite actual PAL/NTSC paused preview observation (campaign-owned only)."""
import argparse
from copy import deepcopy
from types import SimpleNamespace
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
from native_tools import ROOT,ASSEMBLER,run as run_command,emulator_config
from ordinary_cadence import chip_memory
from preview_extended_proof import continuous,table,value
from preview_proof import point
from preview_native_observation import Observer,INPUTS,RAW_CAP
from run_shared_match_core import READONLY

CAPS=dict(accepted_request_generations=7,playing_dispatches=512,ordinary_operations=2049,
    title_callbacks=256,paused_callbacks=2048,video_fields=4096,seconds=70,
    worker_calls_per_job=8192,samples_per_path=256,raw_bytes=RAW_CAP)
CPU9_RECEIPT=ROOT/'build/acceptance/campaigns/00b055e774894e9c9127e470d17e7823/attempts/preview-cpu/000009/receipt.json'
CPU9_CURRENT=ROOT/'build/tests/preview-cpu/report.json'
CPU9_SHA='b5b57f313123c2cf457b924bcc64c6b261375a12c41ac9679d817cf1079c401f'
SEEK_RECEIPT=ROOT/'build/acceptance/campaigns/69cd1780198c4e55a7f8d6c25484c239/attempts/seek-sliced-cpu/000004/receipt.json'
SEEK_CURRENT=ROOT/'build/tests/seek-sliced-cpu/report.json'
SEEK_SHA='1a0a8cc933c5c9f42507ca8b2f1cc7c260db769fffbd0a50570b35beb712995c'
CPU9_START=CPU9_RECEIPT.with_name('started.json')
SEEK_START=SEEK_RECEIPT.with_name('started.json')
CPU9_KEY='2fe61ee7c2ed6320263f1de1f580aa7449f23243d6cce325d3a8eb8507ae3adf'
SEEK_GUARD=('        cmpi.w  #SEEK_JOB_PENDING,game_history_seek_status\n'
    '        beq     .invalid\n        cmpi.w  #SEEK_JOB_READY,game_history_seek_status\n        beq     .invalid\n')
COMMANDS=('game_history_freeze','game_history_seek_begin','game_preview_request',
    'game_preview_step','game_preview_result','game_preview_cancel','game_history_resume_latest',
    'game_history_seek_step','game_history_seek_commit','game_history_seek_cancel')


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
    run_command([str(ASSEMBLER),'-Fhunkexe','-kick1hunks','-m68000','-DENHANCED_INTERFACE=1',
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


def verify_preview_retirement(before,after):
    assert after['generation']!=before['generation']
    assert after['status']==7 and after['cache_valid']==0, 'Preview retirement must be PREVIEW_CANCELED with invalid cache'


def verify_admission(admission):
    """Check captured guest downcounter arithmetic, including unsigned wrap."""
    assert set(admission)=={'current','last','phase','interval','remaining','reserve','admitted','requested_work'}
    assert all(type(v) is int and 0<=v<=0xffffffff for v in admission.values())
    elapsed=(admission['last']-admission['current'])&0xffffffff
    remaining=admission['interval']-admission['phase']-elapsed
    assert admission['remaining']==max(0,remaining) and admission['reserve']==10000
    assert admission['requested_work'] in (0,1)
    assert admission['admitted']==int(admission['requested_work']==1 and remaining>=admission['reserve'])
    return admission['admitted']


class Native:
    """Guest mailbox calls; host writes only command arguments, never core state."""
    def __init__(self,session,executable,listing,standard,cpu):
        self.directory=executable.parent;self.maximum_job_calls=0
        self.session=session;self.cpu=cpu;self.normal=[];self.states={};self.launches=[]
        self.selected_seconds=None;self.selected_frame=None;self.requests=0;self.paused_callbacks=0
        self.public_checks=0;self.callback_stops=[];self.input_actions=[];self.frozen_intervals=[];self.pause_volume_writes=[]
        self.internal_body_stops=0;self.seek_rows=[];self.seek_jobs=[]
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
            listing.read_text(),self.segments,locations,executable.parent/'events.jsonl.gz')
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
        self.states[len(self.normal)]=bytes.fromhex(row['state'])
        if row['operation']=='game_core_select':
            assert row['arguments'][1]==0xace1,'Fixture selection must declare its actual seed'
            self.selected_seconds=row['end']['seconds'];self.selected_frame=row['end']['frame']
            self.selection_operation=len(self.normal)-1

    def check_caps(self):
        self.session.flush_rpc();self.observer.raw.flush()
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

    def seek(self,target):
        selected=self.block('game_core_state','game_core_state_end').hex()
        metadata=self.block('game_history_state','game_history_state_end').hex()
        def preview():
            return dict(generation=self.number('game_preview_generation',4),
                status=self.number('game_preview_status'),cache_valid=self.number('game_preview_cache_valid'))
        def begin():
            index=len(self.observer.api_rows)
            self.call('game_history_seek_begin',[self.number('game_history_seek_generation',4),target>>32,target&0xffffffff])
            return index,self.number('game_history_seek_generation',4)
        def finish(generation):
            indices=[]
            for _ in range(CAPS['paused_callbacks']):
                if self.number('game_history_seek_status')==2:return indices
                assert self.number('game_history_seek_status')==1
                self.call('game_history_seek_step',[generation,1])
                indices.append(len(self.observer.api_rows)-1)
            raise AssertionError('Native admitted seek did not finish within unchanged callback cap')
        preview_before=preview()
        initial_begin,generation=begin()
        checkpoint=self.number('game_history_seek_cursor',8)
        preview_pending=preview()
        verify_preview_retirement(preview_before,preview_pending)
        decline_before=self.block('game_history_seek_storage','game_history_seek_storage_end')
        self.call('game_history_seek_step',[generation,0])
        decline_index=len(self.observer.api_rows)-1
        assert self.block('game_history_seek_storage','game_history_seek_storage_end')==decline_before
        assert self.observer.api_rows[decline_index]['bodies']==0
        self.call('game_preview_result',[preview_pending['generation']],accepted=False)
        result_rejection=len(self.observer.api_rows)-1
        self.call('game_preview_request',[preview_pending['generation'],0xffff,0,0],accepted=False)
        request_rejection=len(self.observer.api_rows)-1
        assert self.block('game_history_seek_storage','game_history_seek_storage_end')==decline_before
        canceled_steps=finish(generation)
        assert self.number('game_history_seek_status')==2
        self.call('game_history_seek_cancel',[generation]);cancel_index=len(self.observer.api_rows)-1
        canceled=self.block('game_history_seek_storage','game_history_seek_storage_end')
        self.call('game_history_seek_commit',[generation],accepted=False)
        canceled_commit_index=len(self.observer.api_rows)-1
        assert self.block('game_history_seek_storage','game_history_seek_storage_end')==canceled
        superseded_begin,superseded_generation=begin()
        superseded_steps=finish(superseded_generation)
        assert self.number('game_history_seek_status')==2
        begin_index,generation=begin()
        superseding=self.block('game_history_seek_storage','game_history_seek_storage_end')
        self.call('game_history_seek_commit',[superseded_generation],accepted=False)
        stale_commit_index=len(self.observer.api_rows)-1
        assert self.block('game_history_seek_storage','game_history_seek_storage_end')==superseding
        step_indices=finish(generation)
        self.call('game_history_seek_commit',[generation])
        self.seek_jobs.append(dict(target=target,checkpoint=checkpoint,generation=generation,
            selected_position=int.from_bytes(bytes.fromhex(metadata)[34:42],'big'),
            selected_state=selected,selected_metadata=metadata,
            initial_begin_api_row_index=initial_begin,admission_zero_api_row_index=decline_index,
            admission_zero_identity_preserved=True,canceled_commit_preserved=True,superseded_commit_preserved=True,
            canceled_job=dict(generation=int.from_bytes(decline_before[:4],'big'),
                begin_api_row_index=initial_begin,step_api_row_indices=canceled_steps,
                cancel_api_row_index=cancel_index,canceled_commit_api_row_index=canceled_commit_index,ready_before_cancel=True),
            superseded_job=dict(generation=superseded_generation,begin_api_row_index=superseded_begin,
                step_api_row_indices=superseded_steps,superseding_begin_api_row_index=begin_index,
                stale_commit_api_row_index=stale_commit_index,ready_before_supersession=True),
            preview_transition=dict(before=preview_before,after=preview_pending,retired=True,
                result_rejection_api_row_index=result_rejection,request_rejection_api_row_index=request_rejection),
            begin_api_row_index=begin_index,step_api_row_indices=step_indices,commit_api_row_index=len(self.observer.api_rows)-1,
            final_state=self.block('game_core_state','game_core_state_end').hex(),final_metadata=self.block('game_history_state','game_history_state_end').hex(),
            final_position=self.number('game_history_position',8)))

    def idle(self):
        assert self.at_before
        self.session.inspect('break_remove',{'id':self.breakpoint})
        self.breakpoint=self.arm('preview_native_return')
        self.stop=self.session.inspect('run_until',{'seconds':self.stop['seconds']+.2})
        assert self.stop['pc']==self.symbols['preview_native_return'],self.stop
        self.at_before=False;self.observer.finish();self.next_callback()

    def run_owned_api(self,name,budget):
        """Observe emitted bodies with read-only stops; never alter CPU state."""
        observer=self.observer;frames=observer.body_frames
        assert not frames.stack and observer.active is None,'Unfinished trace at owned API entry'
        entry_ids=[self.session.inspect('break_add',{'kind':'pc','addr':pc})['id']
            for pc in frames.body_map]
        return_ids={};deadline=self.stop['seconds']+1;previous=None;entry_count=0;outer_count=0
        try:
            for _ in range(16385): # <=8192 actual entries, paired exits, one public return.
                stop=self.session.inspect('run_until',{'seconds':deadline})
                registers=self.session.inspect('regs.get')
                pc,sp=registers['pc'],registers['a'][7]
                identity=(pc,sp,stop['cck'])
                assert identity!=previous,'Read-only body breakpoint resumed without progress'
                previous=identity
                assert pc==stop['pc'],'Body stop/register PC disagreement'
                assert not observer.drops and not observer.problems,'Body stop observation dropped or rejected accesses'
                if pc==self.symbols['preview_native_return']:
                    assert not frames.stack,'Public return precedes actual body return'
                    return stop
                self.internal_body_stops+=1
                # Notification delivery is drained by the synchronous run reply.
                state=self.block('game_core_state','game_core_state_end')
                assert state==observer.state(),'Actual body state differs from full write reconstruction'
                position={k:stop[k] for k in ('cck','frame','vpos','hpos','seconds')}
                if frames.stack and (pc,sp)==(frames.stack[-1]['return_pc'],frames.stack[-1]['entry_sp']+4):
                    for row in frames.exit(pc,sp,state,position):
                        self.session.inspect('break_remove',{'id':return_ids.pop(row['entry_index'])})
                        if row['depth']==1:
                            row['index']=len(observer.rows);observer.rows.append(row)
                    # A return may land at another real body entry (tail/caller
                    # sequence); process that entry at this same genuine stop.
                    if pc not in frames.body_map:continue
                assert pc in frames.body_map,'Unexpected stop inside actual native API'
                assert observer.inside_api(),'Body entry outside actual mailbox JSR bracket'
                entry_count+=1
                assert entry_count<=8192,'Native API body-entry observation bound exceeded'
                if name=='game_preview_step':assert entry_count<=budget,'Actual preview body entries exceed requested operation budget'
                return_pc=int.from_bytes(self.read(sp,4),'big')
                owner=dict(active=observer.number('game_preview_active',1),
                    status=observer.number('game_preview_status'),variant=observer.number('game_preview_variant',1),
                    seek_active=observer.number('game_history_seek_active',1),seek_status=observer.number('game_history_seek_status'),
                    seek_generation=observer.number('game_history_seek_generation',4),
                    seek_cursor=observer.number('game_history_seek_cursor',8))
                row=frames.entry(pc,registers,return_pc,state,position,owner,len(observer.api_rows))
                if row['depth']==1:
                    outer_count+=1
                    if name=='game_history_seek_step':assert outer_count<=1,'Actual seek logical bodies exceed one-body admission'
                observer.pending['bodies']+=1
                return_ids[row['entry_index']]=self.session.inspect('break_add',{'kind':'pc','addr':return_pc,
                    'cond':{'lhs':'sp','op':'eq','rhs':sp+4}})['id']
                self.check_caps()
            raise AssertionError('Native body entry/return stop bound exhausted')
        finally:
            for identifier in [*entry_ids,*return_ids.values()]:
                self.session.inspect('break_remove',{'id':identifier})

    def call(self,name,args=(),accepted=True):
        if not self.at_before:self.next_callback()
        self.session.flush_rpc()
        self.observer.finish() # Drain the genuine sampling interval before owning an API.
        self.check_caps()
        before=self.block('game_core_state','game_core_state_end')
        metadata=self.block('game_history_state','game_history_state_end')
        store=self.block('game_history_buffer','game_history_buffer_end')
        private_before=self.block('game_history_seek_storage','game_history_seek_storage_end')
        intents_before=deepcopy(self.cpu.seek_events)
        inputs={n:self.read(self.symbols[n],size) for n,size in INPUTS}
        frame=self.read(self.symbols['game_stack_top']-70,62)
        arguments=list(args)+[0]*(6-len(args))
        self.session.inspect('mem.write',{'addr':self.symbols['preview_native_arguments'],
            'data':b''.join(v.to_bytes(4,'big') for v in arguments).hex()})
        self.session.inspect('mem.write',{'addr':self.symbols['preview_native_command'],
            'data':(COMMANDS.index(name)+1).to_bytes(2,'big').hex()})
        self.check_caps() # Include flushed snapshot RPCs before beginning native work.
        self.observer.begin(name);self.subscribe(True)
        self.session.inspect('break_remove',{'id':self.breakpoint})
        self.breakpoint=self.arm('preview_native_return')
        self.stop=self.run_owned_api(name,arguments[1] if name=='game_preview_step' else 1 if name=='game_history_seek_step' else 4)
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
        elif name.startswith('game_history_seek_'):
            assert after_store==store
            admission=None
            if name=='game_history_seek_step':
                admission={key:self.number('preview_native_timer_'+key,4) for key in
                    ('current','last','phase','interval','remaining','reserve','admitted','requested_work')}
                verify_admission(admission)
                arguments[1]=admission['admitted']
                logical=sum(frame['depth']==1 for frame in self.observer.body_frames.records
                    if frame['api_row_index']==len(self.observer.api_rows)-1)
                assert logical==admission['admitted'],'Admission/logical body count disagreement'
            intent_start=len(self.cpu.seek_events)
            self.cpu.call(name,{i:v for i,v in enumerate(arguments[:3])})
            actual_intents=[event for frame in self.observer.body_frames.records
                if frame['api_row_index']==len(self.observer.api_rows)-1 and frame['depth']==1 for event in frame['events']]
            expected_intents=deepcopy(self.cpu.seek_events[intent_start:])
            assert actual_intents==expected_intents,'Native seek intents differ from uninterrupted actual core'
            assert self.cpu.cpu.r_reg(0)==int(accepted)
            assert self.cpu.state()==self.block('game_core_state','game_core_state_end')
            private=self.block('game_history_seek_storage','game_history_seek_storage_end')
            reference=bytes(self.cpu.mem.r_block(self.cpu.symbols['game_history_seek_storage'],734))
            assert private[:26]==reference[:26] and private[98:]==reference[98:],'Native seek semantic context differs'
            # Saved public metadata contains image-specific recorder pointers.
            # Preserve all actual72 bytes; compare semantic private header/images.
            assert private[26:98]==metadata,'Seek saved metadata differs from actual selected context'
            if not accepted or name!='game_history_seek_commit':
                assert self.block('game_core_state','game_core_state_end')==before
                assert self.block('game_history_state','game_history_state_end')==metadata
            if not accepted or (admission is not None and admission['admitted']==0):
                assert private==private_before and self.cpu.seek_events==intents_before,'Declined/rejected seek changes private context/intents'
            self.seek_rows.append(dict(api_row_index=len(self.observer.api_rows)-1,name=name,generation=arguments[0],
                admission=admission,body_operations=cost['bodies'],
                logical_body_operations=sum(frame['depth']==1 for frame in self.observer.body_frames.records
                    if frame['api_row_index']==len(self.observer.api_rows)-1),working_cursor=self.number('game_history_seek_cursor',8),
                working_state=self.block('game_history_seek_working','game_history_seek_storage_end').hex(),
                reference_working_state=bytes(self.cpu.mem.r_block(self.cpu.symbols['game_history_seek_working'],318)).hex(),
                public_state=self.block('game_core_state','game_core_state_end').hex(),
                public_metadata=self.block('game_history_state','game_history_state_end').hex(),
                selected_state=before.hex(),selected_metadata=metadata.hex(),events=actual_intents,reference_events=expected_intents,
                actual_core_equal=True,frozen_store_preserved=True))
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
        prefix_validation=verify_incoming_prefix(self,ordinal,selection,result)
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
            coincident=bool(self.number('game_preview_coincident')),incoming_prefix_validation=prefix_validation)
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


def verify_incoming_prefix(native,ordinal,selection,result):
    """Expected points come only from independently captured native boundaries."""
    if ordinal==0xffff:
        operations=[];expected=b''
    else:
        probe,kind,end=attempts(native.cpu)[ordinal]
        incoming=next((r for r in reversed(native.launches)
            if r['end']!=end and r['origin']<probe),None)
        assert kind in (1,2) and incoming is not None
        assert result['incoming']==incoming['origin']<=selection<=probe
        operations=[i for i in range(incoming['origin'],selection)
            if native.normal[i][0]=='game_tick_dispatch']
        expected=b''.join(point(native.states[i+1],native.symbols) for i in operations)
    assert len(expected)//8==result['prefix'],'Native prefix count differs from retained actual dispatches'
    assert all(path[:len(expected)]==expected for path in result['paths']), 'Native prefix differs from actual retained flight'
    return dict(passed=True,source='actual-native-retained-dispatch-boundaries',
        operation_cursors=operations,expected_samples=len(expected)//8,
        expected_bytes=expected.hex(),expected_sha256=hashlib.sha256(expected).hexdigest())


def qualify_resolver(native,generation):
    """Stop at the first prepared generation, even if batching crossed PRIME."""
    for _ in range(CAPS['worker_calls_per_job']):
        state=native.number('game_preview_status')
        assert native.number('game_preview_generation',4)==generation,'Replacement generation retired'
        if 2<=state<=5:
            assert native.number('game_preview_cache_valid')==1,'Post-resolve state has no prepared context'
            return
        assert state==1,('Replacement resolution became unavailable',state)
        native.step(generation,4)
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
    native.seek(candidate['probe'])
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


def reviewed_execution(saved,current,sha,start,expected_key=None):
    """Bind the reviewed pass and reject any later failed/interrupted actual run."""
    from acceptance_campaign import canonical,execution_blocker
    assert digest(saved)==sha,'Reviewed CPU receipt is unavailable or changed'
    assert digest(current)==sha,'Latest CPU proof is not the reviewed passing receipt'
    receipt=json.loads(current.read_text())
    assert receipt.get('passed') is True,'Latest CPU proof did not pass'
    started=json.loads(start.read_text())
    key=canonical(started['dependencies'])
    assert key==started['dependency_key'] and (expected_key is None or key==expected_key)
    blocker=execution_blocker(SimpleNamespace(id=started['id']),started['dependencies'])
    assert blocker is None,blocker
    return receipt


def inherited_endpoints():
    return reviewed_execution(CPU9_RECEIPT,CPU9_CURRENT,CPU9_SHA,CPU9_START,CPU9_KEY)


def worker_guard_closure(inherited):
    """Only three entry guards changed; their removal reproduces reviewed bytes."""
    source=(ROOT/'amiga/game/preview.s').read_bytes()
    guard=SEEK_GUARD.encode()
    assert source.count(guard)==3,'Unexpected preview ownership changes'
    original=source.replace(guard,b'')
    expected=inherited['evidence']['files']['amiga/game/preview.s']
    assert hashlib.sha256(original).hexdigest()==expected,'Preview changed beyond scoped seek guards'
    return dict(passed=True,removed_entry_guards=3,current_source_sha256=hashlib.sha256(source).hexdigest(),
        guard_removed_source_sha256=expected,
        scope='Exact source equality after removal of three seek-owner guards; physics/endpoints inherited, current ownership freshly proven.')


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
        paths|=cpu_paths|{ROOT/'scripts/preview_native_fixture.s',CPU9_RECEIPT,CPU9_CURRENT,CPU9_START,SEEK_RECEIPT,SEEK_CURRENT,SEEK_START}
        inherited=inherited_endpoints()
        guard_closure=worker_guard_closure(inherited)
        seek_receipt=reviewed_execution(SEEK_RECEIPT,SEEK_CURRENT,SEEK_SHA,SEEK_START)
        transaction.meta.update(files=snapshot(paths),tools=tools)
        transaction.meta['environment']['PYTHONPATH']=os.environ.get('PYTHONPATH')
        print('Preparing bounded native preview',standard,flush=True)
        _,product=build_native();standalone,_=build_core()
        assert {digest(product),digest(standalone)}==set(seek_receipt['evidence']['compiled_executables'].values()),'Fresh sliced CPU products no longer match'
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
                seek_storage_identity=dict(loaded_start=native.symbols['game_history_seek_storage'],
                    loaded_end=native.symbols['game_history_seek_storage_end'],bytes=734,
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
                    preview_storage_bytes=5550,preview_metadata_bytes=110,seek_storage_bytes=734,acquisition=acquisition,
                    seek_validation=dict(passed=True,cpu_receipt_sha256=SEEK_SHA,rows=native.seek_rows,jobs=native.seek_jobs,
                        one_body_per_slice=True,selected_pending_preserved=True,actual_guest_timer_admission=True,
                        reserve_eclock_ticks=10000,reserve_scope='Initial CPU-derived estimate; all actual callbacks and deadlines remain acceptance evidence.'),
                    replacement_cancel_cases=replacements,preservation={k:True for k in
                    ('selected_canonical','history_metadata','frozen_store','live_backup','caller_frame',
                     'input_globals','publication_irq_only','audio_cpu_configuration')},
                    interrupts=dict(inside_worker_entries=sum(r['irq'] for r in observer.api_rows if r['name']=='game_preview_step'),
                        inside_api_entries=observer.irq_inside,entry_exit_ack_pairs=True,
                        exact_pc_address_width_value_rules=[dict(pc=pc,**rule) for pc,rule in observer.rules.items()],keyboard_irq_allowances=0),
                    physical_inputs=physical,telemetry=dict(notifications=observer.notifications,
                        dropped_notifications=0,dropped_accesses=0,public_boundary_drain_checks=observer.drain_checks),
                    caps=CAPS,observed_caps=observed,costs=costs,
                    byte_cap_scope='stored-artifact-bytes; rpc-and-event-transcripts-gzip; uncompressed-transcripts-measured-separately',
                    endpoint_classification_scope='inherited-reviewed-cpu9; no-fresh-native-launch-hook-qualification',
                    inherited_endpoint_validation=dict(cpu_receipt_sha256=CPU9_SHA,
                        scope='CPU9-independent-endpoints; native-labels-only',worker_guard_closure=guard_closure,
                        current_ownership_cpu_receipt_sha256=SEEK_SHA),
                    resources=dict(fixture_chip_free_bytes=memory['chip_free_bytes'],
                        fixture_loaded_bytes=sum(h['bytes'] for h in native.hunks),
                        product_static_loaded_bytes=hunk_layout(product)['loaded_payload_bytes']),
                    compiled_identity=dict(loaded_hunks=native.hunks,worker_bytes=worker_identity,seek_storage=seek_storage_identity,overlay=overlay_identity,
                        normalized_shared_core=dict(matched=True,bytes=len(expected[0]),relocations=expected[1],
                            sink_branches=expected[2],sha256=hashlib.sha256(expected[0]).hexdigest()),
                        fixture_manifest_sha256=digest(Path(str(executable)+'.compile.json')),
                        product_manifest_sha256=digest(Path(str(product)+'.compile.json'))),
                    continuous_actual_core_equal=False)
                frames=observer.body_frames
                assert frames.entries==len(frames.records) and not frames.stack,'Unpaired actual body observations'
                validation['body_observation']=dict(
                    protocol='read-only-emitted-body-pc-and-matched-stack-return',
                    loaded_body_map=[dict(pc=pc,**spec) for pc,spec in frames.body_map.items()],
                    frames=sorted(frames.records,key=lambda row:row['entry_index']),
                    semantic_intents=observer.body_sink_events,internal_stops=native.internal_body_stops,
                    entry_return_observations=frames.internal_stops,
                    actual_body_entries=frames.entries,outer_logical_calls=sum(r['depth']==1 for r in frames.records),
                    unpaired_frames=0,maximum_nesting=9,maximum_entries_per_api=8192,
                    stack_bottom=native.symbols['game_stack_bottom'],stack_top=native.symbols['game_stack_top'],
                    source_closure='Exact fixture manifest and loaded core/worker bytes bound in compiled_identity.',
                    scope='Read-only internal debugger stops; no register/core writes or physical commands inside APIs. API JSR/RTS CCK includes all body/IRQ execution; host stop/RPC delay is not emulated work.')
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
            scope='Literal observer-local requests/replies; notifications are preserved separately in events.jsonl.gz.')
        validation['event_transcript']=dict(encoding='gzip-jsonl',path=str(observer.raw_path.relative_to(ROOT)),
            sha256=digest(observer.raw_path),compressed_bytes=observer.raw_path.stat().st_size,
            uncompressed_bytes=observer.raw_uncompressed_bytes,notifications=observer.notifications)
        completed=[]
        for observation in observations:
            print('Comparing uninterrupted actual core',observation['name'],flush=True)
            row=continuous(image,symbols,observation)
            row.pop('actual_accepted_launches') # Native labels are not a new hook-qualified endpoint oracle.
            row.update(case_id=observation['name'],native_jsr_rts_preserved=True,
                incoming_prefix_validation=observation['incoming_prefix_validation'],
                classification_scope='native-preview-outcome-labels; endpoint-qualification-inherited-reviewed-cpu9')
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
                callback_rows=native.observer.callback_rows,guard_problems=native.observer.problems,
                body_frames=native.observer.body_frames.records,
                unpaired_body_frames=native.observer.body_frames.stack,
                body_map=native.observer.body_frames.body_map))
            native.observer.close()
        transaction.abort(error)
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ntsc',action='store_true')
    args=parser.parse_args();run('NTSC' if args.ntsc else 'PAL')
