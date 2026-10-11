"""Bounded CPU proof: actual controls produce a missed incoming shot.
No builder/native timing; compare full states with actual ordinary dispatcher.
"""
import argparse,json,hashlib,traceback,subprocess
from pathlib import Path
from build_match_core import load_image
from match_core_cpu import Core,cpu_tool_inputs
from native_evidence import ReportRun,inputs_for,snapshot,digest
from native_tools import ROOT
from run_shared_match_core import READONLY
from run_tutorial_exploration_cpu import setup,packet,request,field,hist,records,incoming,attach,nom

def main():
    p=argparse.ArgumentParser();p.add_argument('--image',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    manifest_path=a.image.parent/'baseline-rally.compile.json';manifest=json.loads(manifest_path.read_text())
    assert manifest['executable_sha256']==digest(a.image)
    for name,expected in manifest['files'].items():
        if not (ROOT/name).resolve().is_relative_to((ROOT/'build').resolve()):assert digest(ROOT/name)==expected,('Compiled source changed',name)
    paths,tools=inputs_for('build',__file__)
    paths|=cpu_tool_inputs()[0]|{a.image,a.image.parent/'native.lst',manifest_path}
    tx=ReportRun([a.output],'build','maintained-native','Missed exploration vs ordinary full-core stream')
    tx.meta.update(files=snapshot(paths),tools=dict(tools,machine68k={'version':'0.4.1','path':str(cpu_tool_inputs()[1]['path'])}),commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip())
    image,s=load_image(a.image);r=dict(passed=False,scope=__doc__,traces=[],events=[])
    try:
        with Core(image,s,readonly=dict(READONLY,game_preview_dispatch_stage_bodies=40)) as c:
            setup(c);original=c.state();metadata=hist(c);buffer=records(c);cache=incoming(c)
            packet(c,32);packet(c,0)
            for t in range(512):
                c.call('tutorial_exploration_update')
                assert hist(c)==metadata and records(c)==buffer and incoming(c)==cache
                if not field(c,'tutorial_running',1):break
            else:raise AssertionError('Serve did not stop')
            assert field(c,'tutorial_stop_reason',1)==2 and field(c,'tutorial_opponent_launched',1)
            request(c)
            # Continuous legal controls only; no canonical or intermediate writes.
            for t in range(255):
                before=field(c,'tutorial_x',1)
                packet(c,4)
                if field(c,'tutorial_x',1)==before:break
            else:raise AssertionError('Left boundary unreachable')
            packet(c,0);r['legal_left_x']=field(c,'tutorial_x',1)
            packet(c,32);assert field(c,'tutorial_gesture_ready',1)
            origin=bytes(c.mem.r_block(s['tutorial_gesture_state'],318));packet(c,0)
            assert field(c,'tutorial_running',1) and field(c,'tutorial_gesture_variant',1)==1
            for t in range(512):
                c.clear_events();c.call('tutorial_exploration_update')
                r['traces'].append(c.state());r['events'].append(list(c.events))
                assert hist(c)==metadata and records(c)==buffer and incoming(c)==cache
                if not field(c,'tutorial_running',1):break
            else:raise AssertionError('Miss did not stop at whole boundary')
            assert field(c,'tutorial_stop_reason',1)==3 and not field(c,'tutorial_human_launched',1),'Fixture did not miss'
            r.update(updates=len(r['traces']),stop_reason=3,miss_no_human_launch=True,original_history_records_incoming_unchanged=True,terminal318_sha256=hashlib.sha256(c.state()).hexdigest())
            c.call('tutorial_request');assert field(c,'tutorial_status',2)==5 and not field(c,'tutorial_ball_mode',1)
            c.call('game_history_resume_latest');assert c.cpu.r_reg(0)==1 and c.state()==original and records(c)==buffer and incoming(c)==cache
            expected=bytearray(metadata);expected[s['game_history_mode']-s['game_history_state']]=1
            off=s['game_history_position']-s['game_history_state'];cur=s['game_history_cursor']-s['game_history_state'];expected[off:off+8]=metadata[cur:cur+8]
            assert hist(c)==expected
            r.update(miss_context_unavailable=True,original_after_miss_exact318_history72_records_incoming=True);c.audit_reads()
        with Core(image,s,initial=origin,readonly=READONLY) as ref:
            attach(ref)
            for i,(expected,events) in enumerate(zip(r['traces'],r['events'])):
                ref.clear_events();nom(ref,0)
                assert ref.state()==expected,('Full318 mismatch',i)
                assert ref.events==events,('Ordered outputs mismatch',i)
            ref.audit_reads()
        r['passed']=True;r['ordinary_full318_ordered_outputs_equal']=True
    except BaseException as e:r.update(error=str(e),traceback=traceback.format_exc())
    r['traces']=[hashlib.sha256(x).hexdigest() for x in r['traces']]
    tx.finalize(a.output,r,compiled=[manifest]);print(a.output)
    return 0 if r['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
