"""Actual emitted original/candidate arithmetic and shared-core differential."""
import hashlib
import json
import os
from collections import defaultdict
from pathlib import Path

from build_match_core import build, load_image
from build_native_game import build as build_native
from check_shared_core_bytes import run as shared_bytes
from match_core_cpu import Core, cpu_tool_inputs
from native_evidence import ReportRun, atomic_json, compile_manifest, digest, inputs_for, snapshot, status
from native_tools import ROOT
from private_state_proof import exercise
from prove_ball_query_seed import seeded32
from run_shared_match_core import READONLY

BASE_HEAD = '5623420afbbcb347b823c09b0f8e94d601516e34'
BASE_STANDALONE = '9cccfffd752e328cfa5f1a4a5c2c2ccd64e1d0c2c8fbc4b72cca7dbeaaabda8b'
BASE_NATIVE = '9bfd85797f8b3a997cff8fa1489be8bfdfca45a0396001935da019c3fc117454'
INPUT_HASHES = {
    'pal': '19d37f99ae8a68bdf90613dacb41e9feb39d5bd43486b9733ab04713b5f46fab',
    'ntsc': 'aa20c2a7ae6bb624b5f0c425fe6108ebe82afe1166a19c4f64946fce11b41024',
}


def code(core, low, high):
    return bytes(core.mem.r_block(core.symbols[low], core.symbols[high]-core.symbols[low]))


def arithmetic(old_path, new_path):
    old_image, old_symbols = load_image(old_path)
    image, symbols = load_image(new_path)
    original = []
    original_displacements = []
    untouched = {r: (0x965aa569 ^ r*0x1010101) & 0xffffffff for r in range(5, 15)}
    # machine68k supports one active machine; retain results, not two CPUs.
    with Core(old_image, old_symbols, readonly=READONLY) as cpu:
        original_code = code(cpu, 'game_ratio', 'game_launch_root')
        cpu.cpu.set_instr_hook_callback(None)
        cpu.mem.set_trace_mode(False)
        for a in range(256):
            for b in range(256):
                cpu.cpu.w_sr(0x2700 | ((a+b)&31))
                cycles = cpu.call('game_ratio', {0: 0x965aa500|a, 1: 0xa5695a00|b, 2: 0xffff0020, **untouched})
                original.append((cpu.cpu.r_reg(0), cpu.cpu.r_sr()&31, cycles))
        for v in range(256):
            for n in range(256):
                cpu.cpu.w_sr(0x2700 | ((v+n)&31))
                cycles = cpu.call('game_displacement', {0: 0x965aa500|v, 1: 0xa5695a00|n, **untouched})
                original_displacements.append((cpu.cpu.r_reg(0), cpu.cpu.r_reg(1), cpu.cpu.r_sr()&31, cycles))
    costs = defaultdict(list)
    instructions = []
    with Core(image, symbols, readonly=READONLY) as cpu:
        assert code(cpu, 'game_ratio', 'game_ratio32') == original_code, 'Variable divider changed'
        prefix = bytes(cpu.mem.r_block(symbols['game_ratio32'], 16))
        assert prefix.hex() == '0280000000ff0281000000ff7420c0c1'
        for a, b in ((0,0), (17,46), (96,90), (127,255), (255,255)):
            for incoming in range(32):
                cpu.cpu.w_sr(0x2700|incoming)
                cpu.call('game_ratio32', {0:0x965aa500|a, 1:0xa5695a00|b, **untouched})
                assert cpu.cpu.r_reg(0)==seeded32(a*b)
                assert cpu.cpu.r_sr()&31 == (4 if a*b==0 else 0)
        cpu.audit_reads()
        for name, a, b in (('game_ratio32',0,0),('game_ratio32',17,46),('game_ratio32',96,90),('game_ratio',96,90)):
            cpu.visits.clear()
            cycles=cpu.call(name,{0:a,1:b,2:32})
            instructions.append(dict(entry=name,a=a,b=b,instructions=sum(n for pc,n in cpu.visits.items() if pc!=0x100000),runner_cycles=cycles))
        cpu.cpu.set_instr_hook_callback(None)
        cpu.mem.set_trace_mode(False)
        for a in range(256):
            for b in range(256):
                expected, ccr, before = original[a*256+b]
                cpu.cpu.w_sr(0x2700|((a+b)&31))
                after=cpu.call('game_ratio32',{0:0x965aa500|a,1:0xa5695a00|b,**untouched})
                assert (cpu.cpu.r_reg(0),cpu.cpu.r_sr()&31)==(expected,ccr),(a,b)
                assert cpu.cpu.r_reg(2)==32 and cpu.cpu.r_reg(3)==expected&1 and cpu.cpu.r_reg(4)==65535
                assert cpu.cpu.r_reg(1)>>16==0
                assert all(cpu.cpu.r_reg(r)==v for r,v in untouched.items())
                assert after < before, ('Not faster',a,b,before,after)
                costs['ordinary' if a*b<8192 else 'overflow'].append((before,after))
        symbols['proof_ratio32_product']=symbols['game_ratio32']+16
        for p in range(65536):
            cpu.cpu.w_sr(0x271f)
            cpu.call('proof_ratio32_product',{0:p,1:0,2:32,**untouched})
            assert cpu.cpu.r_reg(0)==seeded32(p),p
            assert cpu.cpu.r_sr()&31==(4 if seeded32(p)==0 else 0)
        for v in range(256):
            for n in range(256):
                expected,d1,ccr,before=original_displacements[v*256+n]
                cpu.cpu.w_sr(0x2700|((v+n)&31))
                after=cpu.call('game_displacement',{0:0x965aa500|v,1:0xa5695a00|n,**untouched})
                assert (cpu.cpu.r_reg(0),cpu.cpu.r_reg(1),cpu.cpu.r_sr()&31)==(expected,d1,ccr),(v,n)
                assert all(cpu.cpu.r_reg(r)==x for r,x in untouched.items())
                assert after<before
        assert cpu.state()==bytes([0xa5])*318
    summary={name:dict(cases=len(rows),before_min=min(x[0] for x in rows),before_max=max(x[0] for x in rows),
        after_min=min(x[1] for x in rows),after_max=max(x[1] for x in rows),
        minimum_saved=min(x-y for x,y in rows),maximum_saved=max(x-y for x,y in rows)) for name,rows in costs.items()}
    return dict(full_factor_pairs=65536,word_products=65536,displacement_pairs=65536,
        incoming_ccr_representatives=160,variable_divider_byte_identical=True,
        all_applicable_pairs_faster_in_cpu_runner=True,costs=summary,instruction_samples=instructions,
        declared_clobber='D1 low word unspecified; D1 high word zero, D2/D3/D4 and all preserved registers/CCR match',
        ratio32_code_bytes=symbols['game_launch_root']-symbols['game_ratio32'],
        core_code_delta=(symbols['game_core_code_end']-symbols['game_core_code_begin'])-(old_symbols['game_core_code_end']-old_symbols['game_core_code_begin']))


def recorded(baseline, before, after, standalone):
    results=[]
    for region, expected_hash in INPUT_HASHES.items():
        path=baseline/'build/tests'/('private-state-retained-'+region)/'observations-unvalidated.json'
        assert digest(path)==expected_hash
        captured=json.loads(path.read_text())[0]
        reference=[]
        for index, executable in enumerate((before, after, standalone)):
            image,symbols=load_image(executable,base=0x10000 if index!=2 else 0x30000)
            with Core(image,symbols,readonly=READONLY,poison=(0xa5,0x5a,0x96)[index]) as cpu:
                cpu.call_logical('game_core_init',[])
                for tick,(name,args) in enumerate(captured['stream'],1):
                    cpu.clear_events();cpu.call_logical(name,args)
                    row=(cpu.state().hex(),list(cpu.events))
                    if index==0:reference.append(row)
                    else:assert row==reference[tick-1],(region,index,tick,name)
                    if tick==captured['selection']:assert cpu.state().hex()==captured['selected']
                cpu.audit_reads()
        results.append(dict(region=region,operations=len(reference),state_bytes=318,
            ordered_events_equal=True,selected_native_boundary=captured['selection'],input_sha256=expected_hash,
            standalone_relocated=True))
    return results


def run():
    output=ROOT/'build/tests/ratio32-cpu/report.json'
    transaction=ReportRun([output],'build','maintained-native','original/candidate actual 68000 arithmetic and state differential')
    try:
        baseline=Path(os.environ['CTENNIS_RATIO32_BASELINE_ROOT']).resolve()
        before=baseline/'build/amiga/interfaces/enhanced/baseline-rally'
        old_standalone=baseline/'build/standalone/match-core'
        assert digest(before)==BASE_NATIVE and digest(old_standalone)==BASE_STANDALONE
        paths,tools=inputs_for('build','scripts/run_ratio32_proof.py')
        cpu_paths,tools['machine68k']=cpu_tool_inputs()
        observations={baseline/'build/tests'/('private-state-retained-'+region)/'observations-unvalidated.json' for region in INPUT_HASHES}
        transaction.meta.update(files=snapshot(paths|cpu_paths|observations|{before,old_standalone}),tools=tools,
            actual_execution='actual-68000-cpu-only',target_scope='CPU cost excludes Amiga bus contention and native presentation')
        transaction.meta['environment'].update(PYTHONPATH=os.environ.get('PYTHONPATH'),CTENNIS_RATIO32_BASELINE_ROOT=str(baseline))
        standalone,listing=build();_,native=build_native()
        arithmetic_result=arithmetic(old_standalone,standalone)
        print(json.dumps(dict(stage='arithmetic',result=arithmetic_result)),flush=True)
        differential=exercise(before,native,standalone)
        capture_result=recorded(baseline,before,native,standalone)
        audit=shared_bytes()
        report=dict(passed=True,execution='actual-68000-cpu-only',baseline_head=BASE_HEAD,
            arithmetic=arithmetic_result,private_state_validation=differential,recorded=capture_result,
            shared_byte_audit=audit,executable_sha256=digest(native))
        transaction.finalize(output,report,compiled=[compile_manifest(standalone,listing),compile_manifest(native,native.parent/'native.lst')])
        assert status(output)['status']=='passed',status(output)
        print(json.dumps(dict(passed=True,report=str(output))),flush=True)
    except BaseException as error:
        transaction.abort(error)
        raise


if __name__=='__main__':
    run()
