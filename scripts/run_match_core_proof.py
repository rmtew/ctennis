"""Bounded shared-68000 core proof; not a portable snapshot or full-match gate."""
import hashlib
import json
import re
from pathlib import Path
from build_native_game import build
from native_tools import ROOT, ASSEMBLER, run, emulator_config
from native_hunk import loaded_hunks, hunk_layout
from copperline_test_session import NativeControlSession

OWNED = {
    'game_play_state':60, 'game_score_state':28, 'game_score_initialized':1,
    'game_score_flags':5, 'game_input_bits':10, 'game_old_action_latches':2,
    'game_lifecycle':2, 'game_selection_delay':7, 'game_new_mode':1,
    'game_celebration_loops':8, 'game_audio_voices':100,
    'game_scene_objects':65, 'game_display_state':8,
    'score_dirty':1, 'field_values':6, 'ui_entropy_state':2, 'ui_demo':1,
}
# Immutable tables read by this bounded trajectory, audited against declarations.
READONLY = {
    'game_audio_registers':6, 'game_height_choices':9, 'game_lower_depth':9,
    'game_lower_width':9, 'game_upper_limits':16, 'game_scene_poses':112,
    'game_scene_robot_poses':112, 'game_scene_animations':36,
    'score_stage_flags':5, 'score_sample_fields':88, 'game_audio_levels':16,
    'native_audio_scores':28, 'native_audio_score_4':128,
    'native_audio_score_5':16, 'native_audio_periods':3072,
    'native_audio_envelopes':128,
}
PAULA = (0xdff0a6,0xdff0a8,0xdff0b6,0xdff0b8,0xdff0d6,0xdff0d8)

class Core:
    def __init__(self, image, symbols, initial, poison=0xa5, fault=None):
        import machine68k as m
        from importlib.metadata import version
        assert version('machine68k')=='0.4.1','Use the proof dependency pin'
        self.machine=m.Machine(m.CPUType.M68000,2048)
        self.mem=self.machine.mem; self.cpu=self.machine.cpu; self.symbols=symbols
        self.mem.w_block(0,bytes([poison])*0x200000)
        self.regions=[]
        for address,data in image:
            self.mem.w_block(address,data);self.regions.append((address,address+len(data)))
        for name,data in initial.items():
            if fault!='omit-audio' or name!='game_audio_voices':self.mem.w_block(symbols[name],data)
        self.owned={symbols[n]+i for n,z in OWNED.items() for i in range(z)}
        self.events=[];self.writes=set();self.reads=set();self.visits={};self.stack_low=0x1ffff0;self.instructions=set();self.pcs=set()
        self.cpu.set_instr_hook_callback(self.instruction)
        self.end=self.machine.create_execute_end('return')
        self.trap=self.machine.traps.alloc(lambda opcode,pc:self.end)
        self.mem.w16(0x100000,0xa000|self.trap)
        # Only presentation sinks are replaced. Scene semantics remain actual code.
        for name in ('game_render_sprites','game_scene_present_fields'):
            self.mem.w16(symbols[name],0x4e75)
        self.mem.set_special_range_write_funcs(0xdf0000,1,None,self.paula,None)
        self.mem.set_invalid_func(self.invalid)
        self.mem.set_trace_func(self.trace);self.mem.set_trace_mode(True)
        self.cpu.w_sr(0x2700)
        for register in range(15):self.cpu.w_reg(register,poison*0x01010101)
        if fault=='out-of-state':self.owned.remove(symbols['game_tick'])
        if fault=='write-trap':
            # MOVE.W #0,$00100000: execute the forbidden write on the CPU.
            self.mem.w_block(symbols['game_round_poll'],bytes.fromhex('33fc000000100000'))
        if fault=='hardware':
            start=symbols['native_entropy_bit']
            code=bytes(self.mem.r_block(start,80))
            address=start+code.index(bytes.fromhex('103900bfe401'))
            self.mem.w16(start,0x4ef9);self.mem.w32(start+2,address)

    def instruction(self,pc):
        if pc not in self.pcs:
            self.pcs.add(pc)
            size,_=self.cpu.disassemble(pc)
            self.instructions.update(range(pc,pc+size))
        for name in ('game_return_vector','game_entropy'):
            if pc==self.symbols[name]:self.visits[name]=self.visits.get(name,0)+1

    def invalid(self,mode,width,address):
        raise AssertionError(f'Forbidden bus access {mode}{1<<width} at {address:#x}')

    def paula(self,address,value):
        if address not in PAULA:raise AssertionError(f'Unexpected output {address:#x}')
        self.events.append([address,2,value])

    def trace(self,mode,width,address,value):
        size=1<<width
        if 0x1f0000<=address and address+size<=0x200000:
            self.stack_low=min(self.stack_low,address)
            return
        if address==0x100000:
            if mode=='R' and width==1:return  # 16-bit return-trap instruction fetch
            raise AssertionError(f'Forbidden return-trap access {mode}{size} at {address:#x}')
        if address in PAULA:
            if mode!='W':raise AssertionError('Hardware read')
            return
        if mode=='W':
            for a in range(address,address+size):
                if a not in self.owned:raise AssertionError(f'Out-of-state write {a:#x}')
                self.writes.add(a)
            for n,z in [('game_scene_objects',65),('field_values',6)]:
                if self.symbols[n]<=address<self.symbols[n]+z:self.events.append([address,size,value])
        else:
            if not any(a<=address and address+size<=b for a,b in self.regions):
                raise AssertionError(f'Out-of-image read {address:#x}')
            self.reads.update(range(address,address+size))

    def call(self,name):
        self.cpu.w_sp(0x1ffff0);self.mem.w32(0x1ffff0,0x100000)
        self.cpu.w_pc(self.symbols[name])
        result=self.machine.execute(2000000)
        if result.result is not self.end:raise AssertionError(f'Unbounded call {name}')
        return result.cycles

    def state(self):return {n:bytes(self.mem.r_block(self.symbols[n],z)) for n,z in OWNED.items()}

    def tick(self,pads):
        self.events=[]
        before=self.state();cycles=self.call('game_round_poll')
        if self.state()!=before or self.events:raise AssertionError('Poll not inert in bounded point lifecycle')
        cycles+=self.call('game_round_poll')
        if self.state()!=before or self.events:raise AssertionError('Repeated poll changes bounded point lifecycle')
        for player,pad in enumerate(pads):
            self.cpu.w_reg(0,pad);self.cpu.w_reg(8,self.symbols['game_input_bits']+player)
            cycles+=self.call('game_store_pad')
        dispatch_cycles=self.call('game_tick_dispatch')
        self.step_cycles=cycles+dispatch_cycles
        return dispatch_cycles

    def audit_reads(self):
        allowed={self.symbols[n]+i for n,z in READONLY.items() for i in range(z)}
        unknown=self.reads-self.owned-self.instructions-allowed
        assert not unknown,('Undeclared data read',sorted(unknown)[:10])

    def close(self):
        self.machine.traps.free(self.trap);self.machine.cleanup()


def negative_controls(image,symbols,initial,rows):
    negatives={}
    for fault in ('omit-audio','out-of-state','hardware','write-trap'):
        core=Core(image,symbols,initial,0x5a,fault)
        try:
            for row in rows:
                core.tick(row['pads'])
                if {n:v.hex() for n,v in core.state().items()}!=row['state']:
                    raise AssertionError('Full-state mismatch')
            raise RuntimeError('Negative control escaped: '+fault)
        except AssertionError as error:
            message=str(error)
            expected={'omit-audio':'Full-state mismatch','out-of-state':'Out-of-state write','hardware':'0xbfe401','write-trap':'Forbidden return-trap access W2 at 0x100000'}[fault]
            assert expected in message,(fault,message)
            negatives[fault]=message
        finally:core.close()
    return negatives


def main():
    directory=ROOT/'build/tests/match-core-proof'
    directory.mkdir(parents=True,exist_ok=True)
    (directory/'report.json').write_text(json.dumps({'passed':False,'state':'incomplete'})+'\n')
    _,ordinary=build()
    ordinary_sha=hashlib.sha256(ordinary.read_bytes()).hexdigest()
    directory=ROOT/'build/tests/match-core-proof';directory.mkdir(parents=True,exist_ok=True)
    exe=directory/'native';listing=directory/'native.lst'
    run([str(ASSEMBLER),'-Fhunkexe','-kick1hunks','-m68000','-DENHANCED_INTERFACE=1',
         '-DDEMO_RECORDING=1','-L',str(listing),'-o',str(exe),'amiga/main.s'])
    locations={n:(int(h),int(o,16)) for n,h,o in re.findall(r'^([A-Za-z_]\w*)\s+(\d\d):([0-9a-fA-F]{8})\s*$',listing.read_text(),re.M)}
    config=emulator_config();rows=[];events=[];cores=[]
    with NativeControlSession(directory) as s:
        s.inspect('session_launch',{'binary':config['tools']['copperline'],'run':str(exe),'args':[
            '--chipset','OCS','--video','PAL','--cpu','68000','--chip','512K','--slow','0','--fast','0','--noaudio',config['inputs']['amiga_rom']]})
        stop=s.inspect('run_until',{'seconds':30});assert stop['reason']=='loadseg',stop
        segments=s.inspect('segments.list')['current']
        symbols={n:segments[h]['start']+o for n,(h,o) in locations.items()}
        def raw(a,n):return bytes.fromhex(s.inspect('mem_read',{'addr':a,'len':n})['data'])
        checks=loaded_hunks(exe,segments,raw)
        image=[(r['start'],raw(r['start'],r['bytes'])) for r in checks]
        def state():return {n:raw(symbols[n],z) for n,z in OWNED.items()}
        stop=s.inspect('run_until',{'seconds':stop['seconds']+2})
        for port in (1,2):
            s.inspect('input_set_port',{'port':port,'device':'joystick'})
            s.inspect('input_joy',{'port':port,'red':True})
        s.inspect('input_key',{'rawkey':0x46,'action':'press'})
        stop=s.inspect('run_until',{'seconds':stop['seconds']+5})
        s.inspect('input_key',{'rawkey':0x46,'action':'release'})
        def until(name):
            bp=s.inspect('break_add',{'kind':'pc','addr':symbols[name]})
            result=s.inspect('run_until',{'seconds':stop['seconds']+100})
            s.inspect('break_remove',{'id':bp['id']})
            assert result['pc']==symbols[name],result
            return result
        boundary=until('simulation_update')
        initial=state()
        for _ in range(128):
            if initial['game_lifecycle']==b'\0\1':break
            until('complete_update');boundary=until('simulation_update');initial=state()
        else:raise AssertionError('No live match')
        assert initial['game_old_action_latches']==bytes([16,16]),initial['game_old_action_latches']
        (directory/'initial.json').write_text(json.dumps({
            'symbols':symbols,'state':{n:v.hex() for n,v in initial.items()},
            'image':[[a,data.hex()] for a,data in image]},indent=2)+'\n')
        cores=[Core(image,symbols,initial,poison) for poison in (0xa5,)]
        def event(message):
            if message.get('method')!='event.mmio':return
            e=message['params'];assert not e.get('dropped_events',0) and not e.get('dropped_notifications',0)
            events.append([e['addr'],e['size'],e['value']])
        s.notification_handler=event
        s.inspect('events.subscribe',{'events':['mmio'],'mmio':[
            {'addr':symbols[n],'len':z,'access':'write'} for n,z in [('game_scene_objects',65),('field_values',6)]]+
            [{'addr':a,'len':2,'access':'write'} for a in PAULA]})
        saw_pause=False;saw_wait=False;returned=False
        first_counter=int.from_bytes(raw(symbols['simulation_updates'],2),'big')
        for tick in range(2000):
            # Ordinary held fire, with release/repress during the first point wait.
            stage=cores[0].state()['game_score_state'][0]
            pad=0 if tick==10 or (stage==2 and not returned) else 16
            if stage==2:saw_pause=True
            if stage==4:saw_wait=True;returned=True
            for port in (1,2):s.inspect('input_joy',{'port':port,'red':bool(pad)})
            events.clear()
            completed=until('complete_update')
            actual=state();native_events=list(events)
            if tick<10:
                assert actual['game_old_action_latches']==bytes([16,16])
                assert actual['game_input_bits'][6:8]==bytes(2)
                assert actual['game_play_state'][23]==0,'Held selection started serve'
            if tick==10:assert actual['game_old_action_latches']==bytes(2)
            counter=int.from_bytes(raw(symbols['simulation_started_updates'],2),'big')
            assert counter==(first_counter+tick+1)&65535,('Callback discontinuity',tick,counter)
            cycles=[]
            for core in cores:
                cycles.append(core.tick([pad,pad]))
                for name,expected in core.state().items():
                    if actual[name]!=expected:
                        raise AssertionError((tick,name,actual[name].hex(),expected.hex()))
                if native_events!=core.events:
                    raise AssertionError(('events',tick,native_events[:12],core.events[:12]))
            rows.append({'tick':tick,'stage':actual['game_score_state'][0], 'flight':actual['game_play_state'][23],
                         'state':{n:v.hex() for n,v in actual.items()},'events':native_events,'cpu_cycles':cycles[0], 'native_callback_cck':completed['cck']-boundary['cck'],
                         'step_cpu_cycles':cores[0].step_cycles, 'pads':[pad,pad], 'visits':dict(cores[0].visits)})
            if tick%100==0:print('Compared',tick,'stage',rows[-1]['stage'],flush=True)
            if saw_pause and saw_wait and returned and rows[-1]['stage']==1 and rows[-1]['flight']:
                break
            boundary=until('simulation_update')
        else:raise AssertionError('No point and next serve within bound')
        s.inspect('events.unsubscribe')
    assert cores[0].visits.get('game_return_vector',0)>0,'No successful return'
    assert cores[0].visits.get('game_entropy',0)>0,'No entropy consumed'
    cores[0].audit_reads()
    written=len(cores[0].writes);read=len(cores[0].reads)
    other=sorted(cores[0].reads-cores[0].owned-cores[0].instructions)
    labels=sorted((a,n) for n,a in symbols.items())
    from bisect import bisect_right
    readonly={}
    for address in other:
        a,n=labels[bisect_right(labels,(address,chr(0x10ffff)))-1]
        readonly.setdefault(n,[]).append(address-a)
    stack_bytes=0x1ffff4-cores[0].stack_low
    for core in cores:core.close()
    replay=Core(image,symbols,initial,0x5a)
    for row in rows:
        replay.tick(row['pads'])
        assert {n:v.hex() for n,v in replay.state().items()}==row['state'],('poisoned replay',row['tick'])
        assert replay.events==row['events'],('poisoned events',row['tick'])
    replay.audit_reads();replay.close()
    negatives=negative_controls(image,symbols,initial,rows)
    import platform
    report={'schema':1, 'runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'cpu_harness':'machine68k 0.4.1 / Musashi', 'python':platform.python_version(),
            'target':{'video':'PAL','cpu':'68000','chipset':'OCS','chip_kib':512,'slow_kib':0,'fast_kib':0},
            'assembler_sha256':hashlib.sha256(Path(ASSEMBLER).read_bytes()).hexdigest(),
            'emulator_sha256':hashlib.sha256(Path(config['tools']['copperline']).read_bytes()).hexdigest(),
            'rom_sha256':hashlib.sha256(Path(config['inputs']['amiga_rom']).read_bytes()).hexdigest(),
            'ordinary_static':hunk_layout(ordinary), 'fixture_static':hunk_layout(exe),'base_commit':run(['git','rev-parse','HEAD']).strip(),
            'ordinary_executable_sha256':ordinary_sha, 'passed':True, 'negative_controls':negatives, 'written_bytes':written, 'read_bytes':read,
            'standalone_stack_bytes':stack_bytes, 'readonly_inventory':READONLY, 'readonly_reads':readonly, 'poisoned_replay':True, 'ownership':OWNED,'ticks':len(rows),'state_bytes':sum(OWNED.values()),'loaded_hunks':checks,
            'initial_sha256':hashlib.sha256((directory/'initial.json').read_bytes()).hexdigest(),
            'fixture_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'rows':rows}
    (directory/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('rows','loaded_hunks','readonly_reads','ownership','readonly_inventory','ordinary_static','fixture_static')}))

def replay_capture(directory):
    report=json.loads((directory/'report.json').read_text())
    assert report['schema']==1 and report['passed']
    assert report['runner_sha256']==hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'Proof code changed; capture again'
    data=(directory/'initial.json').read_bytes()
    assert hashlib.sha256(data).hexdigest()==report['initial_sha256']
    capture=json.loads(data)
    image=[(a,bytes.fromhex(blob)) for a,blob in capture['image']]
    for (a,blob),check in zip(image,report['loaded_hunks'],strict=True):
        assert a==check['start'] and hashlib.sha256(blob).hexdigest()==check['actual_sha256']
    initial={n:bytes.fromhex(v) for n,v in capture['state'].items()}
    core=Core(image,capture['symbols'],initial,0x3c)
    try:
        for row in report['rows']:
            core.tick(row['pads'])
            assert {n:v.hex() for n,v in core.state().items()}==row['state'],row['tick']
            assert core.events==row['events'],row['tick']
        core.audit_reads()
    finally:core.close()
    negatives=negative_controls(image,capture['symbols'],initial,report['rows'])
    print('Negative controls:',json.dumps(negatives))
    print('Standalone replay matched',len(report['rows']),'boundaries; no emulator or ROM opened')

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--replay',type=Path,help='Replay a previously captured proof without Copperline or a ROM')
    args=parser.parse_args()
    if args.replay:replay_capture(args.replay)
    else:main()
