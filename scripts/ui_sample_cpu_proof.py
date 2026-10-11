"""Execute original/reference/candidate ui_sample on the pinned 68000 CPU.

Presentation/title sinks record calls and return; gameplay latch/clear routines
execute actual code. This is CPU equivalence evidence, not native timing acceptance.
"""
import argparse,hashlib,json,itertools
from pathlib import Path
from build_match_core import load_image
from match_core_cpu import cpu_tool_inputs

def fixtures():
    zero=bytes(128)
    for k in range(128):
        for old,new in ((0,255),(255,0),(255,255),(1,2),(2,0)):
            a=bytearray(zero);b=bytearray(zero);a[k]=old;b[k]=new
            yield dict(name=f'key-{k}-{old}-{new}',previous=bytes(a),current=bytes(b),active=255)
    for v in (0,1,255):
        yield dict(name=f'all-{v}',previous=zero,current=bytes([v])*128,active=255)
    for active,demo,paused,confirm,selection,life in itertools.product((0,255),(0,255),(0,255),(0,255),(0,1),(0,1,2,3,4,6,7,8)):
        # Include aliases, simultaneous menu/gameplay edges, unsupported keys.
        keys=bytearray(zero)
        for k in (0,0x11,0x21,0x20,0x22,0x44,0x45,0x19,0x7f):keys[k]=255
        yield dict(name=f'mode-{active}-{demo}-{paused}-{confirm}-{selection}-{life}',previous=zero,current=bytes(keys),active=active,demo=demo,paused=paused,confirm=confirm,selection=selection,life=life)
    for active,pad,logical in itertools.product((0,255),range(64),range(64)):
        yield dict(name=f'pad-{active}-{pad}-{logical}',previous=zero,current=zero,active=active,pad=pad,logical=logical)

    for pad in range(64):
        for active in (0,255):
            yield dict(name=f'pad-history-{active}-{pad}',previous=zero,current=zero,active=active,pad=pad,pad2=63-pad,pad_previous=63-pad,pad_previous2=pad,entry=pad)
    for key in (0x44,0x19,0x45):
        current=bytearray(zero);current[key]=255
        for paused in (0,255):
            yield dict(name=f'takeover-{key}-{paused}',previous=zero,current=bytes(current),active=0,demo=255,demo_choice=1,paused=paused,life=1)

class Runner:
    def __init__(self,path):
        import machine68k as m
        self.image,self.s=load_image(path);self.machine=m.Machine(m.CPUType.M68000,16384)
        self.mem,self.cpu=self.machine.mem,self.machine.cpu;self.traps=[];self.calls=[];self.mmio=[]
        self.end=self.machine.create_execute_end('done');self.addtrap(0x100000,lambda op,pc:self.end)
        for n in ('ui_feedback','ui_render','game_core_return_title'):
            def sink(op,pc,n=n):
                self.calls.append(n)
                sp=self.cpu.r_sp();self.cpu.w_pc(self.mem.cpu_r32(sp));self.cpu.w_sp(sp+4)
            self.addtrap(self.s[n],sink)
        self.executing=False;self.mem.set_trace_func(self.trace);self.mem.set_trace_mode(True)
    def addtrap(self,a,callback):
        t=self.machine.traps.alloc(callback);self.traps.append((a,t))
    def trace(self,mode,width,address,value):
        if self.executing and mode=='W':
            size=1<<width;s=self.s
            allowed=[(s['game_core_state'],s['game_core_state_end']),(s['ui_state'],s['ui_help_choice']+2),(0x1f0000,0x1ffff4)]
            assert any(lo<=address and address+size<=hi for lo,hi in allowed) or address in (0xdff0a8,0xdff0b8,0xdff0d8),f'Unexpected write {address:#x}'
            if address>=0xdff000:self.mmio.append((address,width,value))
    def run(self,f):
        for a,b in self.image:self.mem.w_block(a,b)
        for a,t in self.traps:self.mem.w16(a,0xa000|t)
        s=self.s;m=self.mem
        # Actual initialized data/BSS plus a complete fixed core/UI fixture.
        m.w_block(s['game_core_state'],bytes(s['game_core_state_end']-s['game_core_state']))
        m.w_block(s['ui_state'],bytes(s['ui_help_choice']+2-s['ui_state']))
        m.w_block(s['ui_previous_keys'],f['previous']);m.w_block(s['game_keyboard_matrix'],f['current'])
        for name,key in (('tutorial_active','active'),('ui_demo','demo'),('ui_paused','paused'),('ui_confirmation','confirm'),('ui_selection','selection'),('ui_demo_choice','demo_choice')):m.w8(s[name],f.get(key,0))
        m.w16(s['game_lifecycle'],f.get('life',0))
        m.w8(s['ui_joystick_bits'],f.get('pad',0));m.w8(s['ui_joystick_bits']+1,f.get('pad2',f.get('pad',0)))
        m.w8(s['ui_joystick_previous'],f.get('pad_previous',0));m.w8(s['ui_joystick_previous']+1,f.get('pad_previous2',0));m.w8(s['ui_joystick_entry'],f.get('entry',0))
        m.w8(s['game_input_pressed'],f.get('logical',0));m.w8(s['game_input_pressed']+1,f.get('logical',0))
        registers=[(0x56781234+i*0x01010101)&0xffffffff for i in range(15)]
        for i,v in enumerate(registers):self.cpu.w_reg(i,v)
        self.cpu.w_sr(0x2715);self.cpu.w_sp(0x1ffff0);m.w32(0x1ffff0,0x100000);self.cpu.w_pc(s['ui_sample'])
        self.calls=[];self.mmio=[];self.executing=True
        result=self.machine.execute(200000);self.executing=False
        assert result.result is self.end and self.cpu.r_sp()==0x1ffff4,f['name']
        assert [self.cpu.r_reg(i) for i in range(15)]==registers,f['name']
        history={name:hashlib.sha256(m.r_block(s[name],s[end]-s[name])).hexdigest() for name,end in (('game_history_state','game_history_state_end'),('game_history_buffer','game_history_buffer_end'))}
        return dict(history=history,core=m.r_block(s['game_core_state'],s['game_core_state_end']-s['game_core_state']).hex(),ui=m.r_block(s['ui_state'],s['ui_help_choice']+2-s['ui_state']).hex(),matrix=m.r_block(s['game_keyboard_matrix'],128).hex(),calls=self.calls,mmio=self.mmio),result.cycles
    def close(self):self.machine.cleanup()

def main():
    p=argparse.ArgumentParser();p.add_argument('--original',required=True);p.add_argument('--reference',required=True);p.add_argument('--candidate',required=True);p.add_argument('--output',required=True);args=p.parse_args()
    tool_paths,tool_binding=cpu_tool_inputs();paths=[args.original,args.reference,args.candidate];cycles=[];count=0
    expected=[];selected={}
    for index,path in enumerate(paths):
        runner=Runner(path)
        try:
            for i,f in enumerate(fixtures()):
                output,elapsed=runner.run(f)
                if index==0:expected.append(output)
                else:assert output==expected[i],f['name']
                if f['name'] in ('all-0','all-255','key-34-0-255'):
                    selected.setdefault(f['name'],{})[('original','reference','candidate')[index]]=elapsed
                if index==0:count+=1
        finally:runner.close()
    cycles=[dict(fixture=k,**v) for k,v in selected.items()]
    report=dict(passed=True,cases=count,cycles=cycles,sha256={str(p):hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in paths},proof_inputs={str(p):hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in set(tool_paths)|{Path(__file__),Path('scripts/build_match_core.py')}|{Path(p).parent/'native.lst' for p in paths}},cpu=tool_binding,scope='Actual 68000 input routine plus gameplay clear/latch; rendering/title synchronous observation sinks. CPU cycles exclude native bus contention/IRQ; no latency acceptance.')
    Path(args.output).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
