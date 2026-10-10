"""Compare actual native prefix planners; consumes builds, never builds/boots."""
import argparse
import hashlib
import json
import os
from pathlib import Path
from uuid import uuid4

from build_match_core import load_image
from coherent_scheduler_edges import setup
from coherent_scheduler_proof import raw_json
from history_proof import field
from match_core_cpu import Core, cpu_tool_inputs
from native_evidence import ReportRun, atomic_json, compile_manifest, digest, inputs_for, snapshot, status
from native_tools import ROOT
from predictor_proof import discover
from run_shared_match_core import READONLY

OLD_SHA='f96f0b3f051535ec95a313e2def46eb2f0c93baee34afba36c5a949fafd5bf00'
BUDGETS=(999,1000,1001,1570,1999,2000,2001,2999,3000,3001,3999,4000,4001,9999,10000,10001)
RETAINED=((4,8),(3,4,8),(7,3,4,8),(3,4,5,9),(4,2,8),(8,))


def seed(executable):
    image,s=load_image(executable);case=discover(image,s,0xace1)[0]
    with Core(image,s,readonly=READONLY) as c:
        generation=setup(c,case)
        for _ in range(3000):
            if field(c,'game_preview_primed_mask')==3:break
            for variant in (0,1):
                if not field(c,'game_preview_primed_mask')&(1<<variant):
                    c.call('game_preview_step_variant',{0:generation,1:1,2:variant})
        assert field(c,'game_preview_primed_mask')==3,'Actual API seed did not prime both variants'
        c.audit_reads()
        owned=[(a,bytes(c.mem.r_block(a,b-a))) for a,b in c.mutable_regions]
        return image,s,c.state(),owned,generation


def trial(seed_data,variant,domain,prefix,usable,poison):
    image,s,initial,owned,generation=seed_data
    with Core(image,s,initial=initial,poison=poison,readonly=READONLY) as c:
        for address,data in owned:c.mem.w_block(address,data)
        c.mutable_regions.append((s['tutorial_state'],s['tutorial_state_end']))
        c.mem.w_block(s['tutorial_state'],bytes(s['tutorial_state_end']-s['tutorial_state']))
        for name,width,value in (('tutorial_generation',4,generation),('tutorial_job_variant',2,variant),
                ('simulation_interval',4,usable+1000),('simulation_phase',4,0),
                ('game_preview_status',2,3),('game_preview_primed_mask',2,3)):
            c.mem.w_block(s[name],value.to_bytes(width,'big'))
        c.mem.w_block(s['game_preview_launches'],bytes(2))
        c.mem.w8(s['game_preview_predictor_routes']+variant,1)
        tail=int.from_bytes(c.mem.r_block(s['game_history_cursor'],8),'big')
        cursor=s['game_preview_stream_cursors']+variant*8
        slots=[]
        if domain=='retained':
            first=tail-len(prefix)
            assert first>=0
            c.mem.w_block(cursor,first.to_bytes(8,'big'))
            c.mem.w_block(s['game_history_oldest'],first.to_bytes(8,'big'))
            store=c.mem.r32(s['game_history_store'])
            for index,op in enumerate(prefix):
                address=store+((first+index)&4095)*14
                c.mem.w_block(address,op.to_bytes(2,'big')+bytes(12));slots.append(address)
        else:
            c.mem.w_block(cursor,tail.to_bytes(8,'big'))
            c.mem.w16(s['game_preview_synthetic_phases']+variant*2,prefix)
        owners=[(name,end) for name,end in (('game_core_state','game_core_state_end'),
            ('game_preview_storage','game_preview_storage_end'),('game_history_state','game_history_state_end'),
            ('game_history_buffer','game_history_buffer_end'),('game_history_seek_storage','game_history_seek_storage_end'),
            ('game_history_incoming_storage','game_history_incoming_storage_end')) if name in s]
        before={name:bytes(c.mem.r_block(s[name],s[end]-s[name])) for name,end in owners}
        calls=[]
        def observe(pc):
            c.instruction(pc)
            if pc==s['tutorial_dispatch_allowance']:calls.append('dispatch_allowance')
        c.cpu.set_instr_hook_callback(observe);c.writes.clear();c.reads.clear()
        cycles=c.call('tutorial_background_class')
        after={name:bytes(c.mem.r_block(s[name],s[end]-s[name])) for name,end in owners}
        assert after==before,'Classifier changed complete owner state'
        assert not c.events and not c.preview_events and not c.seek_events,'Classifier emitted outputs'
        allowed=set(range(s['tutorial_job_budget'],s['tutorial_job_budget']+2))
        allowed.update(range(s['tutorial_job_cost'],s['tutorial_job_cost']+4))
        assert c.writes<=allowed,'Classifier wrote outside its declared plan fields'
        c.audit_reads()
        budget=field(c,'tutorial_job_budget');cost=field(c,'tutorial_job_cost',4)
        peeked=[index for index,address in enumerate(slots) if address in c.reads or address+1 in c.reads]
        full={name:value.hex() for name,value in after.items() if name!='game_history_buffer'}
        return dict(budget=budget,cost=cost,cycles=cycles,stack=c.stack_bytes,
            dispatch_allowance_calls=len(calls),peeked_slots=peeked,full_owners=full,
            history_buffer_sha256=hashlib.sha256(after['game_history_buffer']).hexdigest(),
            input_sha256=hashlib.sha256(b''.join(before.values())).hexdigest(),
            ordered_events=[c.events,c.preview_events,c.seek_events],writes_owned=True,unchanged=True)


def run(new,old,raw):
    assert digest(old)==OLD_SHA,'Frozen classifier identity changed'
    raw.mkdir(parents=True,exist_ok=True)
    seeds=[seed(old),seed(new)];rows=[];eliminated=0
    for variant in (0,1):
        for domain,prefix in [('retained',p) for p in RETAINED]+[('synthetic',p) for p in range(4)]:
            for usable in BUDGETS:
                identity=f'{variant}-{domain}-{str(prefix)}-{usable}'
                reference=trial(seeds[0],variant,domain,prefix,usable,0x5a)
                candidate=trial(seeds[1],variant,domain,prefix,usable,0xa5)
                raw_json(raw/(identity+'.json'),dict(reference=reference,candidate=candidate,
                    variant=variant,domain=domain,prefix=prefix,usable_e=usable,comparison_validated=False))
                assert (candidate['budget'],candidate['cost'])==(reference['budget'],reference['cost']),(identity,'plan differs')
                assert candidate['full_owners']['game_core_state']==reference['full_owners']['game_core_state']
                assert candidate['full_owners']['game_preview_storage']==reference['full_owners']['game_preview_storage'],'Full preview differs'
                assert candidate['history_buffer_sha256']==reference['history_buffer_sha256'],'Complete retained history differs'
                assert candidate['ordered_events']==reference['ordered_events']
                assert candidate['dispatch_allowance_calls']<=reference['dispatch_allowance_calls']
                assert set(candidate['peeked_slots'])<=set(reference['peeked_slots'])
                cheap_slack=candidate['budget']>0 and usable-candidate['cost']<1000
                if cheap_slack:
                    assert len(candidate['peeked_slots'])<=candidate['budget'],'Unadmittable retained opcode was peeked'
                    if domain=='retained' and prefix==(4,8):
                        assert candidate['peeked_slots']==[0] and reference['peeked_slots']==[0,1]
                        assert candidate['dispatch_allowance_calls']==0 and reference['dispatch_allowance_calls']==1
                        eliminated+=1
                    if domain=='synthetic' and prefix==2:
                        assert candidate['dispatch_allowance_calls']==0 and reference['dispatch_allowance_calls']==1
                rows.append(dict(identity=identity,variant=variant,domain=domain,prefix=prefix,usable_e=usable,
                    passed=True,budget=candidate['budget'],cost=candidate['cost'],old_cycles=reference['cycles'],
                    new_cycles=candidate['cycles'],old_dispatch_calls=reference['dispatch_allowance_calls'],
                    new_dispatch_calls=candidate['dispatch_allowance_calls'],cheap_slack=cheap_slack))
    assert eliminated>=8,'Missing both-variant cheap-slack lookup witnesses'
    return dict(passed=True,rows=rows,cheap_slack_lookup_eliminations=eliminated,
        max_new_cpu_cycles=max(r['new_cycles'] for r in rows),max_old_cpu_cycles=max(r['old_cycles'] for r in rows),
        scope='Actual old/new native classifier planning on fresh once-declared actual API seed fixtures. Full owner state/output unchanged per call; cost/budget and routes compared. Relocated native pointer bytes are preserved locally, not conflated across images. No body execution, native timing, physical input or ordinary reachability claim.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--executable',type=Path,default=ROOT/'build/amiga/interfaces/enhanced/baseline-rally')
    parser.add_argument('--reference',type=Path,default=ROOT/'build/tests/coherent-frozen-classifier-f96/baseline-rally')
    parser.add_argument('--informal',action='store_true');args=parser.parse_args()
    new=args.executable.resolve();old=args.reference.resolve()
    output=ROOT/'build/tests/coherent-classifier-cpu/report.json'
    if args.informal:
        raw=output.parent/('informal-'+uuid4().hex)
        try:atomic_json(raw/'results-unvalidated.json',run(new,old,raw))
        except BaseException as error:
            atomic_json(raw/'failure-unvalidated.json',dict(passed=False,error=repr(error)));raise
        print(json.dumps(dict(passed=True,informal=True,raw=str(raw))),flush=True);return
    transaction=ReportRun([output],'coherent-classifier-cpu','maintained-native','actual 68000 CPU only')
    try:
        paths,tools=inputs_for('build','scripts/run_coherent_classifier_cpu.py')
        cpu_paths,tools['machine68k']=cpu_tool_inputs()
        transaction.meta.update(files=snapshot(paths|cpu_paths|{old,old.parent/'native.lst'}),tools=tools,
            reference_binding='Frozen f96 native executable/listing, not candidate source')
        transaction.meta['environment']['PYTHONPATH']=os.environ.get('PYTHONPATH')
        manifest=compile_manifest(new,new.parent/'native.lst')
        raw=output.parent/('raw-'+transaction.meta['run_id']);validation=run(new,old,raw)
        atomic_json(raw/'results-unvalidated.json',validation)
        transaction.finalize(output,dict(passed=True,execution='actual-68000-cpu-only',validation=validation,
            executable_sha256=digest(new),reference_executable_sha256=OLD_SHA),[manifest],list(raw.glob('*')))
        assert status(output)['status']=='passed',status(output)
        print(json.dumps(dict(passed=True,report=str(output),sha256=digest(output))),flush=True)
    except BaseException as error:
        transaction.abort(error);output.with_name('failed-'+transaction.meta['run_id']+'.json').write_bytes(output.read_bytes());raise


if __name__=='__main__':main()
