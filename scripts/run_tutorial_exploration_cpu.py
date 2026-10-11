"""Actual 68000 exploration vs ordinary full-core stream; presentation traps only.

One-time controller fixtures are initialized through real core/history/preview
APIs. Subsequent gameplay receives controls only. Complete318 comparisons use
another execution of the actual full dispatcher, not a tennis model. CPU cycles
exclude native presentation and do not establish Amiga callback deadlines.
"""
import hashlib,json,subprocess,traceback
from pathlib import Path
from uuid import uuid4
from build_match_core import load_image
from match_core_cpu import Core,cpu_tool_inputs
from history_proof import attach,field,cursor
from run_shared_match_core import READONLY
from native_tools import ROOT
from native_evidence import atomic_json,digest,snapshot,python_inputs,ReportRun,inputs_for

LAST={}

def block(c,n,e):return bytes(c.mem.r_block(c.symbols[n],c.symbols[e]-c.symbols[n]))
def put(c,n,v,w=1):c.mem.w_block(c.symbols[n],v.to_bytes(w,'big'))
def hist(c):return block(c,'game_history_state','game_history_state_end')
def records(c):return block(c,'game_history_buffer','game_history_buffer_end')
def incoming(c):return block(c,'game_history_incoming_storage','game_history_incoming_storage_end')
def nom(c,pad):
    c.call_logical('game_round_poll',[])
    c.call_logical('game_core_sample_pads',[pad,0])
    c.call_logical('game_core_sample_result',[field(c,'game_input_bits',1)&16,field(c,'game_input_pressed',1)&16,0,0,0,0])
    c.call('game_render_sprites',{13:c.start})
    c.call_logical('game_tick_dispatch',[])

def ui_fixture(c):
    s=c.symbols
    c.mutable_regions.extend([(s['tutorial_state'],s['tutorial_state_end']),
        (s['ui_state'],s['ui_help_choice']+2),(s['last_timer_count'],s['last_timer_count']+4)])
    c.readonly['game_keyboard_matrix']=128;c.readonly['game_keyboard_mapping']=66
    for lo,hi in c.mutable_regions[-3:]:c.mem.w_block(lo,bytes(hi-lo))
    c.mem.w_block(s['game_keyboard_matrix'],bytes(128))
    # Native presentation-only sinks: preserve actual controller and core code.
    for n in ('discard_ready_scene','complete_scene','tutorial_restore_court','tutorial_redraw'):
        def sink(op,pc):
            sp=c.cpu.r_sp();target=c.mem.cpu_r32(sp);c.cpu.w_sp(sp+4);c.cpu.w_pc(target)
        c._trap(s[n],sink)
    put(c,'tutorial_active',255);put(c,'ui_paused',255)
    put(c,'tutorial_active_variant',1);put(c,'tutorial_hold_ticks',24000,4)
    put(c,'last_timer_count',1000000,4)

def setup(c):
    c.call_logical('game_core_init',[]);attach(c);c.call_logical('game_core_select',[0,0xace1,0])
    for t in range(150):
        nom(c,0)
        if field(c,'game_lifecycle')==1 and field(c,'game_score_initialized',1) and field(c,'game_lower_phase',1)==0x40:break
    else:raise AssertionError('No genuine human serve-wait')
    c.call('game_history_freeze');assert c.cpu.r_reg(0)==1
    ui_fixture(c)
    for n,f in [('tutorial_x','game_lower_x'),('tutorial_y','game_lower_y')]:put(c,n,field(c,f,1))
    request(c)

def request(c):
    args={0:field(c,'game_preview_generation',4),2:field(c,'tutorial_x',1),3:field(c,'tutorial_y',1)}
    if field(c,'tutorial_explored',1):name='game_preview_request_full_current'
    else:name='game_preview_request_projected';args[1]=65535
    c.call(name,args);assert c.cpu.r_reg(0)==1,('request rejected',name)
    put(c,'tutorial_generation',field(c,'game_preview_generation',4),4)

def packet(c,p):
    c.call('tutorial_sample',{0:p,1:0});c.call('tutorial_controls')

def competing_seek(image,s):
    with Core(image,s,readonly=dict(READONLY,game_preview_dispatch_stage_bodies=40)) as c:
        setup(c);packet(c,32);assert field(c,'tutorial_gesture_ready',1)
        target=cursor(c)
        c.call('game_history_seek_begin',{0:field(c,'game_history_seek_generation',4),1:target>>32,2:target&0xffffffff})
        assert c.cpu.r_reg(0)==1 and field(c,'game_history_seek_status') in (1,2)
        before=c.state();metadata=hist(c);buffer=records(c)
        packet(c,0)
        assert not field(c,'tutorial_running',1) and c.state()==before and hist(c)==metadata and records(c)==buffer,'Press release stole seek ownership'
        preview=block(c,'game_preview_storage','game_preview_storage_end')
        c.call('game_preview_request_full_current',{0:field(c,'game_preview_generation',4),2:field(c,'tutorial_x',1),3:field(c,'tutorial_y',1)})
        assert c.cpu.r_reg(0)==0 and block(c,'game_preview_storage','game_preview_storage_end')==preview and c.state()==before and hist(c)==metadata
        c.audit_reads();return dict(pending_or_ready_seek_start_refused=True,full_current_atomic_refusal=True)

def prospective_serve(image,s,origin=None):
    with Core(image,s,initial=origin,readonly=dict(READONLY,game_preview_dispatch_stage_bodies=40)) as c:
        if origin is None:setup(c)
        else:
            attach(c);c.call('game_history_freeze');assert c.cpu.r_reg(0)==1
            ui_fixture(c)
            put(c,'tutorial_x',field(c,'game_lower_x',1));put(c,'tutorial_y',field(c,'game_lower_y',1));request(c)
        g=field(c,'game_preview_generation',4)
        for _ in range(256):
            c.call('game_preview_step_variant',{0:g,1:1,2:0})
            assert c.cpu.r_reg(0)==1
            if field(c,'game_preview_launch_saved',1):break
        else:raise AssertionError('No prospective held serve launch')
        expected=bytes(c.mem.r_block(s['game_preview_launch_states'],318));actual=[]
        def hook(pc):
            c.instruction(pc)
            if pc==s['game_history_serve'] and field(c,'tutorial_running',1) and not field(c,'game_preview_active',1):actual.append(True)
        c.cpu.set_instr_hook_callback(hook)
        packet(c,32);packet(c,0)
        for _ in range(128):
            c.call('tutorial_exploration_update')
            if actual:break
        assert len(actual)==1
        actual[0]=c.state()
        # Result continuation bits deliberately reflect ordinary held input.
        # They do not alter the pre-launch play/RNG/scene prefix; keep their
        # exact full-state differences explicit rather than masking gameplay.
        differences=[i for i,(a,b) in enumerate(zip(actual[0],expected)) if a!=b]
        allowed=[s[n]-s['game_core_state'] for n in ('game_continue_held','game_continue_pressed','game_input_pressed')]
        assert all(i in allowed for i in differences),('Prospective serve differs before launch',differences)
        c.audit_reads();return dict(full318_difference_offsets=differences,allowed_logical_edge_and_continue_offsets=allowed,gameplay_rng_scene_equal=True)

def prove(reference,image,s,variant,cycles=2):
    global LAST
    with Core(image,s,readonly=dict(READONLY,game_preview_dispatch_stage_bodies=40)) as c:
        setup(c);original=c.state();oldhist=hist(c);oldrecords=records(c);oldincoming=incoming(c)
        origins=[];traces=[];controller=[];outputs=[]
        LAST=dict(variant=variant,controller=controller,traces=traces)
        # Chord consumes the press even if it is released without directions.
        packet(c,40);packet(c,0)
        assert field(c,'tutorial_exploration_cycles')==0 and not field(c,'tutorial_running',1)
        # Long gesture consumes release; fresh menu confirmation is required.
        packet(c,32);put(c,'last_timer_count',975000,4);packet(c,32)
        assert field(c,'tutorial_menu',1) and field(c,'tutorial_gesture',1)==2
        packet(c,0);assert field(c,'tutorial_menu',1) and not field(c,'tutorial_running',1)
        # Close using physical down edges (ui_edges is physical sampled input).
        put(c,'ui_edges',2);packet(c,0);packet(c,0);put(c,'ui_edges',0)
        packet(c,16);packet(c,0);assert not field(c,'tutorial_menu',1)
        # Initial serve always prospective held, then incoming action literals.
        for cycle in range(cycles):
            if cycle:
                # Authored legal movement input steers toward the actual incoming
                # target; no canonical state or contact outcome is injected.
                target=max(32,min(223,field(c,'game_target_x',1)-8))
                for _ in range(255):
                    x=field(c,'tutorial_x',1)
                    if x==target:break
                    packet(c,4 if x>target else 1)
                else:raise AssertionError('Legal placement did not reach incoming target')
                packet(c,0)
            action=0 if cycle==0 else variant
            pad=16 if action==0 else 0
            # Simultaneous F+G press changes preview action generation after
            # accepted capture. Later releases must preserve that press origin.
            packet(c,32|pad)
            assert field(c,'tutorial_gesture_ready',1)
            origins.append(bytes(c.mem.r_block(s['tutorial_gesture_state'],318)))
            generation=field(c,'tutorial_gesture_generation',4)
            packet(c,0)
            assert field(c,'tutorial_running',1),('latched snapshot discarded',generation,field(c,'game_preview_generation',4))
            steps=[]
            events=[]
            for t in range(512):
                c.clear_events()
                c.call('tutorial_exploration_update')
                steps.append(c.state())
                events.append(list(c.events))
                assert hist(c)==oldhist and records(c)==oldrecords and incoming(c)==oldincoming,'Frozen Original/history mutated'
                if not field(c,'tutorial_running',1):break
            else:raise AssertionError('No bounded whole-boundary stop')
            stop=field(c,'tutorial_stop_reason',1)
            traces.append(steps);outputs.append(events);controller.append(dict(cycle=cycle,variant=action,updates=len(steps),stop=stop,human=field(c,'tutorial_human_launched',1),opponent=field(c,'tutorial_opponent_launched',1),last_sha256=hashlib.sha256(steps[-1]).hexdigest()))
            assert stop in (2,3) and field(c,'tutorial_human_launched',1),controller[-1]
            if stop==3:break
            request(c);assert field(c,'game_preview_full_origin')==1 and field(c,'game_preview_predictor_routes',1)==1,'Incoming full origin failed guarded projected route'
        assert len(controller)==cycles,'Named incoming-action case lacks genuine incoming coverage'
        # Branch commit is the actual UI operation, including position/pads and
        # full scene rebuilding, checkpoint installation, input reconciliation.
        explored=c.state();c.call('tutorial_play_from_here');assert field(c,'game_history_mode',1)==1
        committed=c.state();commit_cursor=cursor(c)
        c.call('game_history_freeze');c.call('game_history_seek',{0:commit_cursor>>32,1:commit_cursor&0xffffffff});assert c.cpu.r_reg(0)==1
        assert c.state()==committed,'Committed complete branch not seekable'
        # The immutable Original backup has been overwritten by this new freeze;
        # original restoration is proved in a separate execution below.
        c.audit_reads()
    refrows=[]
    for origin,steps,events,info in zip(origins,traces,outputs,controller):
        with Core(*reference,initial=origin,readonly=READONLY) as c:
            attach(c)
            for index,expected in enumerate(steps):
                c.clear_events()
                nom(c,16 if info['variant']==0 else 0)
                assert c.state()==expected,('full ordinary branch differs',info['cycle'],index)
                assert c.events==events[index],('ordered semantic outputs differ',info['cycle'],index)
            c.audit_reads();refrows.append(dict(cycle=info['cycle'],complete_states_equal=len(steps)))
    with Core(image,s,readonly=dict(READONLY,game_preview_dispatch_stage_bodies=40)) as c:
        setup(c);original=c.state();oldhist=hist(c);oldrecords=records(c);oldincoming=incoming(c);packet(c,32);packet(c,0)
        for t in range(512):
            c.call('tutorial_exploration_update')
            if not field(c,'tutorial_running',1):break
        assert c.state()!=original
        c.call('game_history_resume_latest');assert c.cpu.r_reg(0)==1 and c.state()==original and records(c)==oldrecords
        expected=bytearray(oldhist);expected[s['game_history_mode']-s['game_history_state']]=1
        off=s['game_history_position']-s['game_history_state'];cur=s['game_history_cursor']-s['game_history_state'];expected[off:off+8]=oldhist[cur:cur+8]
        assert hist(c)==expected,'Original public72 restore differs'
        assert incoming(c)==oldincoming,'Original incoming storage restore differs'
        c.audit_reads()
    return dict(variant=variant,controller=controller,reference=refrows,original_exact318_all72_records=True,committed_seek_exact318=True,chord_consumed=True,long_hold_consumed=True)

def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--native-origin-report',type=Path);args=parser.parse_args()
    directory=ROOT/'build/tests/tutorial-exploration-cpu'/uuid4().hex;directory.mkdir(parents=True)
    output=ROOT/'build/tests/tutorial-exploration-cpu/report.json'
    tx=ReportRun([output],'build','maintained-native','Logical controller actual-core branch proof')
    paths,tools=inputs_for('build','scripts/run_tutorial_exploration_cpu.py')
    origin=None
    if args.native_origin_report:
        observed=json.loads(args.native_origin_report.read_text())
        origin=bytes.fromhex(next(r['core'] for r in observed['observations'] if r['name']=='initial-serve'))
        assert len(origin)==318
        paths.add(args.native_origin_report)
    tx.meta.update(files=snapshot(paths|cpu_tool_inputs()[0]),tools=dict(tools,machine68k={'version':'0.4.1','path':str(cpu_tool_inputs()[1]['path'])}),commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip())
    executable=ROOT/'build/amiga/interfaces/enhanced/baseline-rally'
    # Preserve executable/listing/manifest for this small CPU receipt only.
    import shutil
    for n in ('baseline-rally','native.lst','baseline-rally.compile.json'):shutil.copy2(executable.parent/n,directory/n)
    manifest=json.loads((directory/'baseline-rally.compile.json').read_text())
    assert manifest['executable_sha256']==digest(directory/'baseline-rally')
    assert manifest['files'][manifest['executable']]==digest(directory/'baseline-rally')
    assert manifest['files'][manifest['executable']+'.lst']==digest(directory/'native.lst') if manifest['executable']+'.lst' in manifest['files'] else manifest['files']['build/amiga/interfaces/enhanced/native.lst']==digest(directory/'native.lst')
    for name,sha in manifest['files'].items():
        if not (ROOT/name).resolve().is_relative_to((ROOT/'build').resolve()):assert digest(ROOT/name)==sha,('Compiled input changed',name)
    image,s=load_image(directory/'baseline-rally');report=dict(passed=False,subject='maintained-native',scope=__doc__,directory=str(directory),commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),executable_sha256=digest(directory/'baseline-rally'),files=snapshot(cpu_tool_inputs()[0]|python_inputs(Path(__file__))|{directory/'baseline-rally',directory/'native.lst',directory/'baseline-rally.compile.json'}))
    try:
        report['rows']=[prove((image,s),image,s,v) for v in (0,1)];report['competing_seek']=competing_seek(image,s);report['prospective_serve']=prospective_serve(image,s);report['native_prospective_serve']=prospective_serve(image,s,origin) if origin else None;report['passed']=True
    except BaseException as e:report.update(error=str(e),traceback=traceback.format_exc(),last=LAST)
    # Keep compact state hashes instead of duplicated whole playthroughs.
    if 'last' in report:report['last']['traces']=[[hashlib.sha256(x).hexdigest() for x in trace] for trace in report['last'].get('traces',[])]
    tx.finalize(output,report,compiled=[manifest],artifacts=[p for p in directory.iterdir() if p.is_file()]);shutil.copy2(output,directory/'report.json')
    print(json.dumps({k:v for k,v in report.items() if k not in ('files','last')},indent=2));return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
