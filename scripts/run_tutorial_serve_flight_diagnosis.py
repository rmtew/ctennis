"""Read-only CPU diagnostic. No builder; one captured318 fixture per Core.
Run only when native owner is idle with PYTHONPATH=.tools/proof-python:scripts.
Measures semantic trajectory, not elapsed native timing or WCET.
"""
import argparse,hashlib,json,traceback,subprocess
from pathlib import Path
from build_match_core import load_image
from match_core_cpu import Core,cpu_tool_inputs
from native_evidence import ReportRun,inputs_for,snapshot,digest
from native_tools import ROOT
from run_shared_match_core import READONLY
from run_tutorial_exploration_cpu import attach,field,put,ui_fixture,request,packet

def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
# Native G layout, explicit field list: exclude players/random/ticks/audio.
NAMES=['court_y','court_x','shadow_colour','flight','contact','ball_y','ball_x','ball_image','ball_colour','launch_x','launch_y','launch_z','launch_screen_y','launch_base_x','launch_base_y','target_y','target_x','height','velocity_x','velocity_y','velocity_z','base_screen_y','base_x','base_y','step']
def ball(state):return dict(zip(NAMES,state[20:45]))
def initialize(c,origin):
    attach(c);c.call('game_history_freeze');assert c.cpu.r_reg(0)==1
    ui_fixture(c);put(c,'tutorial_x',field(c,'game_lower_x',1));put(c,'tutorial_y',field(c,'game_lower_y',1));request(c)
def main():
    p=argparse.ArgumentParser();p.add_argument('--image',type=Path,required=True);p.add_argument('--origin-report',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists(),'Never overwrite diagnostic receipt'
    manifest_path=a.image.parent/'baseline-rally.compile.json'
    manifest=json.loads(manifest_path.read_text())
    assert manifest['executable_sha256']==digest(a.image)
    for name,expected in manifest['files'].items():
        if not (ROOT/name).resolve().is_relative_to((ROOT/'build').resolve()):assert digest(ROOT/name)==expected,('Compiled source changed',name)
    paths,tools=inputs_for('build',__file__)
    paths|=cpu_tool_inputs()[0]|{a.image,a.origin_report,a.image.parent/'native.lst',manifest_path}
    tx=ReportRun([a.output],'build','maintained-native','Captured serve flight diagnosis; completion is not acceptance')
    tx.meta.update(files=snapshot(paths),tools=dict(tools,machine68k={'version':'0.4.1','path':str(cpu_tool_inputs()[1]['path'])}),commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip())
    image,s=load_image(a.image);native=json.loads(a.origin_report.read_text());origin=bytes.fromhex(next(x['core'] for x in native['observations'] if x['name']=='initial-serve'));assert len(origin)==318
    r=dict(scope=__doc__,files={str(x):sha(x) for x in (a.image,a.origin_report,Path(__file__))},origin318_sha256=hashlib.sha256(origin).hexdigest(),passed=False)
    try:
        projected=[]
        with Core(image,s,initial=origin,readonly=dict(READONLY,game_preview_dispatch_stage_bodies=40)) as c:
            initialize(c,origin);generation=field(c,'game_preview_generation',4);last=-1;launch=None
            for step in range(768):
                c.call('game_preview_step_variant',{0:generation,1:1,2:0})
                if field(c,'game_preview_launch_saved',1):
                    if launch is None:
                        launch=bytes(c.mem.r_block(s['game_preview_launch_states'],318));projected.append(ball(launch));last=field(c,'game_preview_flight_phases',2)
                    n=field(c,'game_preview_flight_phases',2)
                    if n!=last:
                        assert n==last+1;projected.append(ball(bytes(c.mem.r_block(s['game_preview_held_state'],318))));last=n
                if field(c,'game_preview_outcomes',2):break
                assert c.cpu.r_reg(0)==1,'Preview no progress before terminal'
            else:raise AssertionError('Preview extent exhausted')
            assert launch is not None
            r.update(projected_ball=projected,projected_outcome=field(c,'game_preview_outcomes',2),projected_points=field(c,'game_preview_counts',2));c.audit_reads()
        actual=[];entries=[];accepted=[];serve=[]
        with Core(image,s,initial=origin,readonly=dict(READONLY,game_preview_dispatch_stage_bodies=40)) as c:
            initialize(c,origin)
            def hook(pc):
                c.instruction(pc)
                if not field(c,'tutorial_running',1) or field(c,'game_preview_active',1):return
                if pc==s['game_history_serve']:serve.append(len(actual))
                if pc==s['game_history_contact']:
                    accepted.append(dict(end=c.cpu.r_reg(7)&65535,state318=c.state().hex(),ball=ball(c.state())))
                if pc==s['game_ball_tick'] and serve:entries.append(dict(index=len(actual),ball=ball(c.state())))
            c.cpu.set_instr_hook_callback(hook);packet(c,32);packet(c,0)
            for step in range(256):
                c.call('tutorial_exploration_update')
                if serve:
                    if accepted:break # Exclude dispatch containing accepted interception.
                    actual.append(ball(c.state()))
                if not field(c,'tutorial_running',1):break
            else:raise AssertionError('Actual extent exhausted')
            r.update(actual_pre_interception_ball=actual,actual_ball_tick_entries=entries,actual_accepted_contacts=accepted,actual_stop_reason=field(c,'tutorial_stop_reason',1));c.audit_reads()
        pairs=min(len(actual),len(projected));r['first_difference']=next((dict(index=i,projected=projected[i],actual=actual[i]) for i in range(pairs) if actual[i]!=projected[i]),None)
        r['compared_samples']=pairs;r['unpaired_actual']=len(actual)-pairs;r['unpaired_projected']=len(projected)-pairs
        r['passed']=True # Diagnostic completion, NOT an equality/acceptance claim.
    except BaseException as e:r.update(error=str(e),traceback=traceback.format_exc())
    tx.finalize(a.output,r,compiled=[manifest]);print(a.output)
    return 0 if r['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
