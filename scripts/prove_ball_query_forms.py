"""Bounded proof of compact R32 and guarded first-bounce queries; test only."""
import hashlib
import json
import math
import time
from collections import Counter
from pathlib import Path
from prove_ball_queries import (ROOT,HEAD,IMAGE_SHA,Core,READONLY,Packet,load_image,digest,
    ratio32,point,first_event,signed_y)


def smear(bits):
    bits|=bits>>1;bits|=bits>>2;bits|=bits>>4
    return bits


def compact32(product):
    h=product>>13;low=(product>>5)&255
    if h==0 or h==4 and low>=128 or h in (2,6) and low>=192:return low
    runs=low&(low>>1)&(low>>2)
    return (low|~smear(runs))&255


MASK32=bytes(255 if index==0 else (~((smear(index)<<1)|1))&255 for index in range(32))


def table32(product):
    h=product>>13;low=(product>>5)&255
    if h==0 or h==4 and low>=128 or h in (2,6) and low>=192:return low
    return low|MASK32[(low&(low>>1)&(low>>2))>>1]


def trunc32(n):return n//32 if n>=0 else -((-n)//32)


def first_ge(z,threshold):
    """Exact ascending root ceil, requiring nonnegative z and positive threshold."""
    n=(z+math.isqrt(z*z+8*threshold))//4
    return n+int(2*n*n-z*n<threshold)


def landing_guard(vx,vy,vz,bx,by,screen,flight=64,contact=0):
    h=by-screen
    if h<0:return None,'negative-height'
    if not flight&64 or flight&128:return None,'not-active'
    if vy==128 or vy&127<4:return None,'low-speed-or-negative-zero'
    if flight&8 and not contact&1:return None,'special-net-reflection'
    lo=first_ge(vz,32*h+1);hi=first_ge(vz,32*h+63);v=signed_y(vy)
    if hi>255:return None,'step-wrap'
    if max(vx&127,vy&127)*hi>=8192:return None,'displacement-overflow'
    a0=v-vz;a1=a0+2*hi
    if max(abs(a0),abs(a1))>255:return None,'height-factor-wrap'
    k=max(0,min(hi,(vz-v)//4))
    numerators=[0,2*hi*hi+(v-vz)*hi,2*k*k+(v-vz)*k]
    if k<hi:numerators.append(2*(k+1)*(k+1)+(v-vz)*(k+1))
    if max(abs(g) for g in numerators)>=8192:return None,'height-quotient-overflow'
    if not 0<=screen+trunc32(min(numerators))<=screen+trunc32(max(numerators))<=255:return None,'screen-clamp-or-wrap'
    dx=(-1 if vx&128 else 1)*((vx&127)*hi//32);dy=trunc32(v*hi)
    if not 32<=min(bx,bx+dx)<=max(bx,bx+dx)<232:return None,'court-x-bound'
    if not 4<=min(by,by+dy)<=max(by,by+dy)<204:return None,'court-y-bound'
    return (lo,hi),'accepted'


def run():
    started=time.monotonic();image_path=ROOT/'build/standalone/match-core';assert digest(image_path)==IMAGE_SHA
    assert digest(ROOT/'scripts/prove_ball_queries.py')=='ac8e059decbf2f03923d0895dad6a2ca0c153190a13bc2d2a06122f1c6eb5705'
    image,symbols=load_image(image_path);packet=Packet(symbols)
    report=dict(passed=False,base_head=HEAD,production_unchanged=True,image_sha256=IMAGE_SHA,
        source_sha256=digest(Path(__file__)),primitive_proof_sha256=digest(ROOT/'build/tests/ball-query-math/report.json'),
        mask32=dict(bytes=32,sha256=hashlib.sha256(MASK32).hexdigest()))
    with Core(image,symbols,readonly=READONLY) as core:
        core.cpu.set_instr_hook_callback(None);core.mem.set_trace_mode(False)
        assert bytes(core.mem.r_block(symbols['game_ratio'],24)).hex()=='0280000000ff0281000000ff0282000000ffc0c176007807'
        symbols['proof_ratio_suffix']=symbols['game_ratio']+24
        for p in range(65536):
            expected=compact32(p);assert expected==table32(p)==ratio32(p)
            core.call('proof_ratio_suffix',{0:p,2:32,3:0,4:7});assert core.cpu.r_reg(0)==expected
        for a in range(256):
            for b in range(256):
                core.call('game_ratio',{0:0x965aa500|a,1:0xa5695a00|b,2:0xffff0020})
                assert core.cpu.r_reg(0)==compact32(a*b)
        core.call('game_ratio',{0:96,1:90,2:32});assert core.cpu.r_reg(0)==254
        report['compact32_emitted']=dict(all_word_products=65536,all_byte_factor_pairs=65536,
            counterexample=dict(a=96,b=90,actual=254,ordinary_quotient=270,wrapped=14,saturated=255))
        max_candidates=0
        for h in range(256):
            for z in range(256):
                lo=first_ge(z,32*h+1);hi=first_ge(z,32*h+63)
                assert 2*lo*lo-z*lo>=32*h+1 and 2*(lo-1)*(lo-1)-z*(lo-1)<32*h+1
                assert 2*hi*hi-z*hi>=32*h+63 and 2*(hi-1)*(hi-1)-z*(hi-1)<32*h+63
                assert 1<=hi-lo+1<=6;max_candidates=max(max_candidates,hi-lo+1)
        report['ascending_brackets']=dict(height_z_pairs=65536,maximum_candidate_ticks=max_candidates)
        # Each parameter triple covers all H=0..255 using monotone extreme H.
        bound_cases=0
        for vy in range(256):
            if vy==128:continue
            v=signed_y(vy)
            for n in range(256):
                if abs(v)*n>=8192:continue
                for z in range(256):
                    a=v+2*n-z
                    if abs(a)>255 or abs(a)*n>=8192:continue
                    f=2*n*n-z*n;e=trunc32(a*n)-trunc32(v*n)
                    h_min=max(0,(f+31)//32)
                    if h_min<=255:assert e<=h_min,('no-bounce',v,n,z,e,f,h_min)
                    h_max=min(255,(f-63)//32)
                    if h_max>=0:assert e>h_max,('guarantee',v,n,z,e,f,h_max)
                    bound_cases+=1
        report['ordinary_height_bounds']=dict(parameter_triples=bound_cases,all_initial_heights_0_to_255_by_monotonicity=True)
        print(json.dumps(dict(stage='landing-bounds',parameter_triples=bound_cases)),flush=True)
        rejected=Counter();accepted=0;actual_calls=0;largest_span=0
        for vx in (0,5,127,128,133,255):
            for vy in (4,7,17,31,63,127,132,135,145,159,191,255):
                for z in (0,4,32,64,128,192,255):
                    for bx in (32,64,128,231):
                        for h in (0,1,2,8,24,64,128):
                            for by in (32,64,110,184,203):
                                if by<h:continue
                                screen=by-h;args=(vx,vy,z,bx,by,screen)
                                bracket,reason=landing_guard(*args);rejected[reason]+=1
                                if bracket is None:continue
                                lo,hi=bracket
                                expected=next(n for n in range(lo,hi+1) if first_event(vy,64,0,point(*args,n))=='bounce')
                                scan=next(n for n in range(1,hi+1) if first_event(vy,64,0,point(*args,n))!='none')
                                assert expected==scan
                                state=bytearray([165]*318)
                                for name,value in dict(step=0,velocity_x=vx,velocity_y=vy,velocity_z=z,
                                    base_x=bx,base_y=by,base_screen_y=screen,flight=64,contact=0).items():packet.set(state,name,value)
                                core.mem.w_block(core.start,bytes(state))
                                for n in range(1,expected+1):
                                    predicted,kind=packet.tick(core.state());core.call('game_ball_tick',{12:packet.play})
                                    assert core.state()==bytes(predicted);actual_calls+=1
                                    assert kind==('bounce' if n==expected else 'none')
                                assert packet.get(core.state(),'contact')&2
                                accepted+=1;largest_span=max(largest_span,hi-lo+1)
        report['guarded_landing_scans']=dict(accepted_flights=accepted,actual_uninterrupted_ball_calls=actual_calls,
            maximum_candidates=largest_span,domain_counts=dict(rejected),full318_compared_at_each_return=True,
            restrictions='Isolated active ball with fixed parameters, no earlier player contact; normal division, no clamp/wrap/outside/net preemption')
    # Audit guards on reachable launches without changing the actual replay.
    reach=[]
    for region in ('pal','ntsc'):
        path=ROOT/('build/tests/private-state-retained-'+region+'/observations-unvalidated.json')
        recorded=json.loads(path.read_text())[0];counts=Counter();firsts=set()
        with Core(image,symbols,readonly=READONLY) as core:
            original_hook=core.instruction
            def hook(pc):
                original_hook(pc)
                if pc==symbols['game_advance_ball']:
                    state=core.state()
                    if packet.get(state,'step')!=0:return
                    args=tuple(packet.get(state,n) for n in ('velocity_x','velocity_y','velocity_z','base_x','base_y','base_screen_y','flight','contact'))
                    if args in firsts:return
                    firsts.add(args);_,reason=landing_guard(*args);counts[reason]+=1
            core.cpu.set_instr_hook_callback(hook);core.call('game_core_init')
            for index,(name,args) in enumerate(recorded['stream'],1):
                core.call_logical(name,args)
                if index==recorded['selection']:assert core.state()==bytes.fromhex(recorded['selected'])
            core.audit_reads()
        reach.append(dict(region=region,input_sha256=digest(path),logical_operations=len(recorded['stream']),
            unique_step0_parameter_tuples=len(firsts),guard_counts=dict(counts)))
    report['reachable_guard_audit']=reach;report['elapsed_host_seconds']=time.monotonic()-started;report['passed']=True
    assert digest(image_path)==IMAGE_SHA
    output=ROOT/'build/tests/ball-query-math/forms-report.json';output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(passed=True,report=str(output))),flush=True)


if __name__=='__main__':run()
