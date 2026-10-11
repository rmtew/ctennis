"""Finite isolated native costs of bounded helper plus actual state copy.

No production admission/cadence claim: diagnostic hook owns separate states.
"""
import argparse
import hashlib
import json
import math
import os
import re
import statistics
import subprocess
from pathlib import Path
from build_match_core import build
from landing_try_proof import corpus, reference as original_reference, check as bounded_check
from build_match_core import load_image
from check_shared_core_bytes import normalized
SAMPLES=2
from match_core_cpu import Core,cpu_tool_inputs
from native_evidence import ReportRun,TARGET,atomic_json,compile_manifest,digest,inputs_for,snapshot,status
from native_hunk import loaded_hunks,hunk_layout
from native_tools import ROOT,ASSEMBLER,run as command,emulator_config,verify_build_tools
from run_shared_match_core import READONLY
from tutorial_capture import CaptureSession
from tutorial_latency import StackTiming,instruction_map

CLOCKS={'PAL':3546895,'NTSC':3579545}
CAPS=dict(physical_seconds=30,jobs=84,raw_bytes=256*1024*1024)


def fixtures():
    executable,listing=build();manifest=compile_manifest(executable,listing)
    image,symbols=load_image(executable)
    seeds,misses=corpus(executable);rows=[]
    assert len(seeds)==42 and len(seeds)*SAMPLES==CAPS['jobs']
    for seed in seeds:
        final,sample,steps,outcome,cycles=original_reference(image,symbols,seed['state'])
        query=bounded_check(executable,0x10000,seed,(final,sample,steps,outcome,cycles),0,0xa5)
        rows.append(dict(name=seed['name'],domain=seed['domain'],initial=seed['state'].hex(),
            endpoint=final.hex(),steps=steps,outcome=outcome,reference_cpu_cycles=cycles,
            query_expected=query,query_endpoint=final.hex() if query['accepted'] else seed['state'].hex()))
    text=f'LANDING_NATIVE_TOTAL equ {len(rows)*SAMPLES}\nlanding_native_inputs:\n'
    for row in rows:
        data=bytes.fromhex(row['initial'])
        for offset in range(0,len(data),16):text+='        dc.b '+','.join(f'${x:02x}'for x in data[offset:offset+16])+'\n'
        text+=f"        dc.w {row['steps']}\n"
    path=ROOT/'build/tests/landing-try-native-inputs.i';path.write_text(text)
    return rows,manifest


def overlay(directory):
    directory.mkdir(parents=True,exist_ok=True)
    verify_build_tools()
    source=ROOT/'amiga/main.s';text=source.read_text()
    anchor='        bsr     game_native_commands\n        jsr     tutorial_tick'
    assert text.count(anchor)==1
    text=text.replace(anchor,'        bsr     game_native_commands\n        jsr     landing_try_native_hook\n        jsr     tutorial_tick')
    generated=directory/'landing-main.s';generated.write_text(text+'\n        include "scripts/fixtures/landing_try_native.s"\n')
    executable,listing=directory/'landing-native',directory/'landing-native.lst'
    command([str(ASSEMBLER),'-Fhunkexe','-kick1hunks','-m68000','-DENHANCED_INTERFACE=1',
        '-L',str(listing),'-o',str(executable),str(generated.relative_to(ROOT))])
    manifest=compile_manifest(executable,listing)
    manifest['files'].update(snapshot([source,ROOT/'scripts/fixtures/landing_try_native.s']))
    atomic_json(str(executable)+'.compile.json',manifest)
    return executable,listing,manifest


class Session(CaptureSession):
    MAX_RAW_BYTES=CAPS['raw_bytes']


class Observer:
    def __init__(self,timing):self.timing=timing;self.events=0
    def observe(self,message):
        row=message.get('params',{})
        if message.get('method','').startswith('event.'):
            assert type(row.get('dropped_notifications'))is int and row['dropped_notifications']==0
            for name in ('dropped_events','dropped_accesses','queue_overflow','access_overflow','notification_overflow','overflow'):
                assert row.get(name,0)==0
            self.events+=1
        if message.get('method')=='event.mmio':self.timing.observe(row)


def summary(values):
    values=sorted(values)
    return dict(samples=len(values),minimum=values[0],median=statistics.median(values),p95=values[math.ceil(.95*len(values))-1],maximum=values[-1])


def run(region):
    directory=ROOT/'build/tests'/('landing-try-native-'+region.lower());directory.mkdir(parents=True,exist_ok=True)
    output=directory/'report.json';tx=ReportRun([output],'native-feedback','bounded-landing-helper','Isolated ball diagnostic jobs; no live match fast-forward')
    try:
        cases,cpu_manifest=fixtures();executable,listing_path,manifest=overlay(directory)
        shipping=ROOT/'build/amiga/interfaces/enhanced/baseline-rally'
        core=normalized(executable,listing_path)
        assert core==normalized(shipping,shipping.parent/'native.lst')
        kwargs=dict(begin_name='landing_try_begin',end_name='landing_try_end',
                    external_names=('game_advance_ball','game_bounce'))
        helper=normalized(executable,listing_path,**kwargs)
        assert helper==normalized(shipping,shipping.parent/'native.lst',**kwargs)
        assert hashlib.sha256(core[0]).hexdigest()=='99c543c170c036137be81d07ebd30b522ef3abdff04bd7b1af38f00047bb99d5'
        paths,tools=inputs_for('native-feedback','scripts/run_landing_try_native.py');cpu_paths,cpu_tool=cpu_tool_inputs()
        tx.meta.update(files=snapshot(set(paths)|set(cpu_paths)|{ROOT/'scripts/fixtures/landing_try_native.s',
            ROOT/'scripts/landing_cases.py',executable,listing_path,shipping}),tools=tools,cpu_tool=cpu_tool,
            actual_target=dict(TARGET,video=region),
            commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip())
        tx.meta['environment'].update(PYTHONPATH=os.environ.get('PYTHONPATH'))
        config=emulator_config();listing=listing_path.read_text();jobs=[]
        with Session(directory) as session:
            session.inspect('session_launch',dict(binary=config['tools']['copperline'],run=str(executable),
                args=['--chipset','OCS','--video',region,'--cpu','68000','--chip','512K','--slow','0','--fast','0','--noaudio',config['inputs']['amiga_rom']]))
            stop=session.inspect('run_until',dict(seconds=30));assert stop['reason']=='loadseg'
            origin=stop['cck'];segments=session.inspect('segments.list')['current']
            symbols={n:segments[int(h)]['start']+int(o,16)for n,h,o in re.findall(r'^([A-Za-z_]\w*)\s+(\d\d):([\da-fA-F]{8})\s*$',listing,re.M)}
            def read(address,size):return bytes.fromhex(session.inspect('mem_read',dict(addr=address,len=size))['data'])
            def block(name,size):return read(symbols[name],size)
            def number(name,size=2):return int.from_bytes(block(name,size),'big')
            loaded=loaded_hunks(executable,segments,read)
            calls,returns=instruction_map(listing,segments,read)
            timing=StackTiming(calls,returns,symbols['game_stack_bottom'],symbols['game_stack_top'])
            session.observer=Observer(timing)
            result=session.inspect('events.subscribe',dict(events=['mmio'],mmio=[dict(addr=symbols['game_stack_bottom'],
                len=symbols['game_stack_top']-symbols['game_stack_bottom'],access=access)for access in ('read','write')]))
            assert result.get('dropped_notifications',0)==0
            before=session.inspect('break_add',dict(kind='pc',addr=symbols['landing_native_before']))
            after=session.inspect('break_add',dict(kind='pc',addr=symbols['landing_native_after']))
            def advance():
                nonlocal stop
                stop=session.inspect('run_until',dict(seconds=(origin+math.ceil(CAPS['physical_seconds']*CLOCKS[region]))/3546895))
                assert stop.get('pc')in(symbols['landing_native_before'],symbols['landing_native_after'])
                assert (stop['cck']-origin)/CLOCKS[region]<=CAPS['physical_seconds']
            def protected():
                return dict(immutable_fixture=block('landing_native_reference_initial',318).hex(),canonical=block('game_core_state',318).hex(),history=block('game_history_state',72).hex(),
                    history_buffer_sha256=hashlib.sha256(block('game_history_buffer',symbols['game_history_buffer_end']-symbols['game_history_buffer'])).hexdigest(),
                    preview_storage_sha256=hashlib.sha256(block('game_preview_storage',symbols['game_preview_storage_end']-symbols['game_preview_storage'])).hexdigest(),
                    seek_storage_sha256=hashlib.sha256(block('game_history_seek_storage',symbols['game_history_seek_storage_end']-symbols['game_history_seek_storage'])).hexdigest(),
                    canaries=[block(n,4).hex()for n in ('landing_native_left_canary','landing_native_middle_canary','landing_native_right_canary')])
            for index in range(CAPS['jobs']):
                advance();assert stop['pc']==symbols['landing_native_before']
                assert number('landing_native_completed')==index
                fixture=cases[index//SAMPLES];initial_state=bytes.fromhex(fixture['initial'])
                assert block('landing_native_query_state',318)==block('landing_native_reference_state',318)==initial_state
                saved=protected();start=stop['cck']
                advance();assert stop['pc']==symbols['landing_native_after']
                assert number('landing_native_completed')==index+1 and protected()==saved
                expected=bytes.fromhex(fixture['endpoint'])
                assert block('landing_native_reference_state',318)==expected
                assert block('landing_native_query_state',318).hex()==fixture['query_endpoint']
                outputs=[int.from_bytes(block('landing_native_results',16)[i:i+4],'big')for i in range(0,16,4)]
                query=fixture['query_expected']
                assert outputs==[3 if query['accepted'] else 0,fixture['steps'] if query['accepted'] else 0,query['reason'],query['checks']]
                spans=[r for r in timing.rows if r['callee']in('landing_reference','landing_try_copied')and start<=r['entry']['cck']<=r['exit']['cck']<=stop['cck']]
                assert len(spans)==2 and [r['callee']for r in spans]==['landing_reference','landing_try_copied']
                jobs.append(dict(index=index,name=fixture['name'],outputs=outputs,start_cck=start,end_cck=stop['cck'],
                    reference_cck=spans[0]['elapsed_bus_cck'],query_cck=spans[1]['elapsed_bus_cck'],
                    protected=saved,full318_expected_equal=True,accepted=query['accepted'],rejected_input_unchanged=not query['accepted']))
            actual_video=[number('presentation_last_line'),number('simulation_interval_whole',4),number('simulation_interval_fraction')]
            assert actual_video==([311,11838,14906]if region=='PAL'else[261,11947,13180])
            stack_result=timing.result()
            assert [f['callee'] for f in stack_result['open_enclosing_calls']]==['simulation_update','landing_try_native_hook'], stack_result['open_enclosing_calls']
            raw=dict(records=session.records,uncompressed_bytes=session.raw_bytes,cap=CAPS['raw_bytes'])
        distributions={name:dict(reference=summary([x['reference_cck']for x in jobs if x['name']==name]),
            query=summary([x['query_cck']for x in jobs if x['name']==name]),
            minimum_saved=min(x['reference_cck']-x['query_cck']for x in jobs if x['name']==name),
            maximum_saved=max(x['reference_cck']-x['query_cck']for x in jobs if x['name']==name))for name in (r['name'] for r in cases)}
        capture=directory/'capture.json';atomic_json(capture,dict(jobs=jobs,stack=stack_result,loaded_hunks=loaded,cases=cases,
            call_map=calls,returns=sorted(returns),actual_video=actual_video,raw=raw))
        product_layout=hunk_layout(executable);baseline_layout=hunk_layout(shipping)
        report=dict(passed=True,executable_sha256=digest(executable),scope='Diagnostic callback hook runs isolated private ball jobs; it does not preserve production callback cadence or replace preview/match endpoints',
            target=dict(TARGET,video=region),region=region,jobs=len(jobs),samples_per_fixture=SAMPLES,distributions=distributions,full_state_bytes=318,
            complete_owner_guard=True,normalized_shipping_core_unchanged=True,normalized_core_bytes=len(core[0]),
            helper_code_bytes=symbols['landing_try_end']-symbols['landing_try_begin'],declared_caps=CAPS,actual_video=actual_video,physical_clock_hz=CLOCKS[region],
            loaded_hunks=loaded,product_layout=product_layout,baseline_layout=baseline_layout,
            capture=str(capture.relative_to(ROOT)),stack_protocol=stack_result['protocol'],raw=raw)
        artifacts=[p for p in directory.iterdir()if p.is_file()and p!=output]
        tx.finalize(output,report,[manifest,cpu_manifest],artifacts)
        assert status(output)['status']=='passed',status(output)
        print(json.dumps(dict(passed=True,region=region,report=str(output))),flush=True)
    except BaseException as error:tx.abort(error);raise


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--ntsc',action='store_true');args=parser.parse_args()
    run('NTSC'if args.ntsc else'PAL')
