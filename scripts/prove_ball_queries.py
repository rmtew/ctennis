"""Test-only exact ball-query derivation against unchanged emitted 68000 code.

This is an arithmetic specification and differential proof, not a gameplay core.
No build, emulator, production source edit, new package or expected trajectory.
"""
import hashlib
import json
import time
from pathlib import Path
from build_match_core import load_image
from match_core_cpu import Core,cpu_tool_inputs
from native_tools import ROOT
from run_shared_match_core import READONLY

HEAD='5623420afbbcb347b823c09b0f8e94d601516e34'
IMAGE_SHA='9cccfffd752e328cfa5f1a4a5c2c2ccd64e1d0c2c8fbc4b72cca7dbeaaabda8b'


def divider(product,divisor):
    """Derived quotient/remainder recurrence, including legacy overflow."""
    r=product>>8;q=0
    for k in range(7,-1,-1):
        u=2*r+((product>>k)&1);bit=int(u>=divisor)
        r=(u-divisor*bit)&255;q=2*q+bit
    return q,r


def ratio32(product):
    """Exact piecewise form; highest set bit is bounded to six positions."""
    n=product>>5;h=n>>8;low=n&255
    if h==0 or h==4 and low>=128 or h in (2,6) and low>=192:return low
    runs=low&(low>>1)&(low>>2)
    return low|((255<<(runs.bit_length()-1))&255) if runs else 255


def signed_y(v):
    magnitude=v&127
    return magnitude if v<128 else -magnitude if magnitude else -256


def displacement(v,n):
    q=ratio32((v&127)*n)
    return (-q if v&128 else q)&255


def point(vx,vy,vz,bx,by,screen,n):
    x=(bx+displacement(vx,n))&255;y=(by+displacement(vy,n))&255
    a=signed_y(vy)+2*n-vz;q=ratio32((abs(a)&255)*n)
    ball=0 if a<0 and q>screen else screen-q if a<0 and q else (screen+q)&255
    colour=0 if a<0 and q>screen else 15;shadow=1
    if colour and 94<=y<110:
        shadow=0
        if 94<=ball<110:colour=0
    return dict(x=x,y=y,ball=ball,colour=colour,shadow=shadow,a=a,q=q,n=n,vx=vx,vy=vy,vz=vz)


def first_event(vy,flight,contact,p):
    if flight&128:return 'launch'
    if not flight&64:return 'inactive-out' if flight&32 else 'inactive'
    if vy&127<4:return 'outside'
    if p['y']<p['ball']:return 'bounce'
    if flight&8 and not contact&1 and abs(p['y']-110)<3:return 'net-reflect'
    if not (32<=p['x']<232 and 4<=p['y']<204):return 'outside'
    return 'none'


class Packet:
    def __init__(self,symbols):
        self.s=symbols;self.start=symbols['game_core_state'];self.play=symbols['game_play_state']
    def offset(self,name):
        # G_SOUND_EVENT has no exported alias; literal layout byte58 is pinned.
        return self.play-self.start+58 if name=='sound_event' else self.s['game_'+name]-self.start
    def get(self,state,name):return state[self.offset(name)]
    def set(self,state,name,value):state[self.offset(name)]=value&255
    def evaluate(self,state,n=None):
        g=lambda name:self.get(state,name)
        return point(*(g(name) for name in ('velocity_x','velocity_y','velocity_z','base_x','base_y','base_screen_y')),
            ((g('step')+1)&255) if n is None else n)
    def advance(self,state):
        out=bytearray(state);p=self.evaluate(state)
        for name,value in dict(step=(self.get(state,'step')+1)&255,ball_x=p['x'],court_x=p['x'],
                court_y=p['y'],ball_y=p['ball'],ball_colour=p['colour'],shadow_colour=p['shadow']).items():self.set(out,name,value)
        return out,p
    def tick(self,state):
        g=lambda name:self.get(state,name);flight=g('flight');contact=g('contact')
        p=self.evaluate(state);kind=first_event(g('velocity_y'),flight,contact,p);out=bytearray(state)
        if kind=='launch':
            for dst,src in zip(('velocity_x','velocity_y','velocity_z','base_screen_y','base_x','base_y'),
                    ('launch_x','launch_y','launch_z','launch_screen_y','launch_base_x','launch_base_y')):self.set(out,dst,g(src))
            for name,value in dict(step=0,sound_event=1,flight=(flight&127)|64).items():self.set(out,name,value)
            return out,kind
        if kind=='inactive-out':self.set(out,'court_y',194)
        if kind.startswith('inactive'):return out,kind
        out,p=self.advance(state)
        if kind=='outside':
            self.set(out,'contact',contact|128);self.set(out,'flight',(flight&~64)|32);return out,kind
        if kind=='none':return out,kind
        vx,vy=g('velocity_x'),g('velocity_y')
        if kind=='net-reflect':contact|=1;vy^=128;damp,z_damp=64,192
        else:
            if contact&2:contact|=4
            else:
                yy=p['y'];yy_index=(yy-39)//4
                if not (39<=yy<184 and 79-yy_index<p['x']<=175+yy_index):contact|=8
                contact|=2
            damp,z_damp=(240,128) if flight&10 else (255,192)
            self.set(out,'ball_x',p['x']);self.set(out,'ball_y',p['y'])
        self.set(out,'contact',contact)
        self.set(out,'base_x',p['x']);self.set(out,'base_y',p['y'])
        self.set(out,'base_screen_y',p['ball'] if kind=='net-reflect' else p['y'])
        self.set(out,'velocity_z',((max(4*self.get(out,'step')-g('velocity_z'),0)&255)*z_damp)>>8)
        self.set(out,'velocity_x',(vx&128)|(((vx&127)*damp)>>8))
        self.set(out,'velocity_y',(vy&128)|(((vy&127)*damp)>>8))
        self.set(out,'step',0)
        for name in ('lower_animation','upper_animation'):self.set(out,name,(g(name)&159)|96)
        return out,kind


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def run():
    image_path=ROOT/'build/standalone/match-core';assert digest(image_path)==IMAGE_SHA
    image,symbols=load_image(image_path);packet=Packet(symbols);tools,tool=cpu_tool_inputs()
    report=dict(passed=False,base_head=HEAD,production_unchanged=True,image_sha256=IMAGE_SHA,
        script_sha256=digest(Path(__file__)),cpu_tool=tool,
        inputs={str(p.relative_to(ROOT)):digest(p) for p in [image_path,ROOT/'amiga/game/gameplay_math.s',
            ROOT/'amiga/game/gameplay_ball.s',ROOT/'amiga/game/gameplay_state.i',ROOT/'scripts/match_core_cpu.py']},
        tool_hashes={str(p):digest(p) for p in tools},scope='Exact arithmetic/ball-packet proof; not full match replay replacement or native timing gate')
    started=time.monotonic();products={a*b for a in range(256) for b in range(256)}
    expected={p:bytes(divider(p,d)[0] for d in range(256)) for p in products}
    table=bytes(ratio32(n<<5) for n in range(2048));fallback=bytes(ratio32((256+n)<<5) for n in range(256))
    for p in range(65536):assert divider(p,32)[0]==ratio32(p)==table[p>>5],p
    report['ratio32_all_word_products']=65536
    report['table2048']=dict(bytes=len(table),sha256=hashlib.sha256(table).hexdigest())
    report['fallback256']=dict(bytes=len(fallback),sha256=hashlib.sha256(fallback).hexdigest())
    report['distinct_factor_products']=len(products)
    # Guarded representatives retain instruction and memory-access auditing.
    with Core(image,symbols,readonly=READONLY) as core:
        for i in range(4096):
            a=i&255;b=(i*73+19)&255;d=(i>>4)&255
            core.call('game_ratio',{0:0xa55a5a00|a,1:0x5aa5a500|b,2:0x965a6900|d})
            assert core.cpu.r_reg(0)==expected[a*b][d]
        core.audit_reads();assert core.state()==bytes([0xa5])*318
        report['guarded_ratio_cases']=4096
        for i in range(1000):
            state=bytearray([165]*318)
            for name,value in dict(step=i,velocity_x=i,velocity_y=(i*31)&255,velocity_z=i,
                base_x=i,base_y=i,base_screen_y=i,flight=(i*19)&255,contact=(i*7)&255).items():packet.set(state,name,value)
            expected_state,_=packet.tick(state);core.mem.w_block(core.start,bytes(state))
            core.call('game_ball_tick',{12:packet.play});assert core.state()==bytes(expected_state)
        core.audit_reads();report['guarded_ball_cases']=1000
        core.cpu.set_instr_hook_callback(None);core.mem.set_trace_mode(False)
        calls=0;ordinary=0;result_hash=hashlib.sha256()
        for a in range(256):
            for b in range(256):
                p=a*b;answers=expected[p];result_hash.update(answers)
                for d in range(256):
                    core.call('game_ratio',{0:0xa55a5a00|a,1:0x5aa5a500|b,2:0x965a6900|d})
                    q=core.cpu.r_reg(0)
                    assert q==answers[d],('ratio',a,b,d,q,answers[d])
                    assert core.cpu.r_sr()&31==(4 if q==0 else 0),('ratio-CCR',a,b,d)
                    assert core.cpu.r_reg(2)==d and core.cpu.r_reg(3)==q&1 and core.cpu.r_reg(4)==65535
                    if d and p<256*d:assert q==p//d;ordinary+=1
                    calls+=1
            if a%32==31:print(json.dumps(dict(stage='emitted-ratio',cases=calls)),flush=True)
        report['emitted_ratio']=dict(cases=calls,safe_division_cases=ordinary,result_sha256=result_hash.hexdigest(),
            full_d0_ccr_and_d2_d3_d4_checked=True,upper_input_bits_poisoned=True)
        # The actual divider suffix allows all 16-bit products, including those
        # impossible to factor into two bytes. Its prefix is verified literally.
        prefix=bytes(core.mem.r_block(symbols['game_ratio'],24))
        assert prefix.hex()=='0280000000ff0281000000ff0282000000ffc0c176007807'
        symbols['proof_ratio_suffix']=symbols['game_ratio']+24
        for p in range(65536):
            core.call('proof_ratio_suffix',{0:p,2:32,3:0,4:7})
            assert core.cpu.r_reg(0)==table[p>>5],('all-word-suffix',p)
        report['emitted_ratio32_suffix_word_products']=65536
        for v in range(256):
            for n in range(256):
                core.call('game_displacement',{0:0xa55a5a00|v,1:0x965a6900|n})
                q=ratio32((v&127)*n);expected_ccr=4 if not v&128 or q==0 else 17|(8 if q<=128 else 0)|(2 if q==128 else 0)
                assert core.cpu.r_reg(0)==displacement(v,n)
                assert core.cpu.r_sr()&31==expected_ccr,('displacement-CCR',v,n)
        report['emitted_displacement_cases']=65536
        original=bytes([0xa5])*318
        def check_packet(state,name,expected):
            core.mem.w_block(core.start,bytes(state));core.call(name,{12:packet.play,5:0x12345678,6:0x965aa569})
            assert core.state()==bytes(expected),(name,dict((n,packet.get(state,n)) for n in ('step','velocity_x','velocity_y','velocity_z','base_screen_y')))
            if name=='game_advance_ball':assert core.cpu.r_reg(5)==0x12345678 and core.cpu.r_reg(6)==0x965aa569
        # Every possible A at every byte n, with threshold-adjacent screen bases.
        height_cases=0
        for n in range(256):
            for base_a in range(-511,128):
                if base_a<=-256:vy=128;vz=-256-base_a
                elif base_a<-127:vy=255;vz=-127-base_a
                else:vy=base_a if base_a>=0 else 128-base_a;vz=0
                q=ratio32((abs(base_a+2*n)&255)*n)
                for screen in sorted({0,255,q,max(0,q-1),min(255,q+1)}):
                    state=bytearray(original)
                    for name,value in dict(step=n-1,velocity_x=(n*37)&255,velocity_y=vy,velocity_z=vz,
                            base_x=31+n,base_y=110,base_screen_y=screen).items():packet.set(state,name,value)
                    expected_state,_=packet.advance(state);check_packet(state,'game_advance_ball',expected_state);height_cases+=1
            if n%64==63:print(json.dumps(dict(stage='emitted-height',cases=height_cases)),flush=True)
        report['emitted_point_height_cases']=height_cases
        event_cases=0;event_counts={}
        geometries=((31,110,111),(232,110,111),(128,110,111),(31,110,100),(232,110,100),
            (128,110,100),(32,4,4),(231,203,203),(32,3,3),(128,204,204),(128,108,100),(128,113,100))
        for x,y,screen in geometries:
            for flight in range(256):
                for contact in range(256):
                    state=bytearray(original)
                    for name,value in dict(step=0,velocity_x=0,velocity_y=4,velocity_z=4,
                            base_x=x,base_y=y,base_screen_y=screen,flight=flight,contact=contact).items():packet.set(state,name,value)
                    expected_state,kind=packet.tick(state);check_packet(state,'game_ball_tick',expected_state)
                    event_cases+=1;event_counts[kind]=event_counts.get(kind,0)+1
            print(json.dumps(dict(stage='emitted-event-priority',cases=event_cases)),flush=True)
        # Low-velocity outside must precede bounce/net/bounds, including -zero.
        for vy in (0,1,2,3,128,129,130,131):
            for flight in range(256):
                state=bytearray(original)
                for name,value in dict(step=0,velocity_x=0,velocity_y=vy,velocity_z=4,base_x=31,
                    base_y=110,base_screen_y=111,flight=flight,contact=0).items():packet.set(state,name,value)
                expected_state,_=packet.tick(state);check_packet(state,'game_ball_tick',expected_state)
        report['emitted_event_priority']=dict(cases=event_cases,classes=event_counts,low_velocity_cases=2048)
    # Reachable states: initialize once, replay actual recorded logical controls.
    reachable=[]
    for region in ('pal','ntsc'):
        path=ROOT/('build/tests/private-state-retained-'+region+'/observations-unvalidated.json')
        recorded=json.loads(path.read_text())[0];hits=[];pending=[]
        with Core(image,symbols,readonly=READONLY) as core:
            original_hook=core.instruction
            def hook(pc):
                original_hook(pc)
                if pending and pc==pending[-1]['return_pc']:
                    row=pending.pop();assert core.state()==bytes(row['expected']);hits.append(row['point'])
                if pc==symbols['game_advance_ball']:
                    before=core.state();expected_state,p=packet.advance(before)
                    pending.append(dict(return_pc=core.mem.r32(core.cpu.r_sp()),expected=expected_state,point=p))
            core.cpu.set_instr_hook_callback(hook);core.call('game_core_init')
            for index,(name,args) in enumerate(recorded['stream'],1):
                core.call_logical(name,args)
                if index==recorded['selection']:assert core.state()==bytes.fromhex(recorded['selected'])
            assert not pending
            core.audit_reads()
        reachable.append(dict(region=region,input_sha256=digest(path),logical_operations=len(recorded['stream']),
            observed_advance_calls=len(hits),selected_boundary_verified=recorded['selection'],height_factor_overflow=sum((abs(p['a'])&255)*p['n']>=8192 for p in hits),
            displacement_overflow=sum((p['vx']&127)*p['n']>=8192 or (p['vy']&127)*p['n']>=8192 for p in hits),
            maximum_step=max((p['n'] for p in hits),default=0),negative_zero_y=sum(p['vy']==128 for p in hits),
            scope='Full guarded actual recorded-control replay; all complete318 bytes checked at each advance return'))
    report['reachable']=reachable;report['elapsed_host_seconds']=time.monotonic()-started;report['passed']=True
    output=ROOT/'build/tests/ball-query-math/report.json';output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(dict(passed=True,report=str(output))),flush=True)


if __name__=='__main__':run()
