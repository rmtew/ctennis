"""Finite physical ADF exploration interactions and complete callback deadlines.

No guest writes, expected-state injection or callback regime selection. Compact
scalar bus watch plus selected complete readbacks and native scanout. This does
not claim all DMA fetches, immutable bitmap lifetime or the full release gate.
"""
import argparse,json,subprocess,traceback
from pathlib import Path
from uuid import uuid4
from build_match_core import load_image
from native_tools import ROOT,emulator_config
from native_evidence import ReportRun,atomic_json,digest,inputs_for,snapshot
from native_hunk import loaded_hunks
from tutorial_capture import CaptureSession,CallbackObserver,native_view,assert_native_text

CLOCK={'PAL':3546895,'NTSC':3579545}
FIELDS=dict(tutorial_active=1,tutorial_running=1,tutorial_explored=1,
    tutorial_menu=1,tutorial_menu_selection=1,tutorial_x=1,tutorial_y=1,
    tutorial_generation=4,tutorial_gesture=1,tutorial_gesture_ready=1,
    tutorial_gesture_variant=1,tutorial_refresh_pending=1,tutorial_exploration_cycles=2,
    tutorial_exploration_ticks=2,tutorial_human_launched=1,tutorial_opponent_launched=1,
    tutorial_stop_reason=1,tutorial_status=2,tutorial_active_variant=1,
    game_preview_active=1,game_preview_status=2,game_preview_full_origin=2,
    game_preview_predictor_routes=2,game_history_mode=1,game_contact=1,game_lifecycle=2,
    missed_presentation_deadlines=2,keyboard_ack=1)

class CompactSession(CaptureSession):MAX_RAW_BYTES=128*1024*1024

def run(standard):
    directory=ROOT/('build/tests/tutorial-exploration-'+standard.lower());directory.mkdir(parents=True,exist_ok=True)
    attempt=directory/uuid4().hex;attempt.mkdir();output=directory/'report.json'
    tx=ReportRun([output],'native-feedback','maintained-native','Finite physical tutorial exploration and complete callbacks')
    report=dict(passed=False,attempt=str(attempt),standard=standard,scope=__doc__,actions=[],observations=[],checks={})
    try:
        paths,tools=inputs_for('native-feedback','scripts/run_tutorial_exploration.py')
        product=ROOT/'build/amiga/interfaces/enhanced';delivery=product/'delivery'
        adf=delivery/'baseline-rally.adf';release=delivery/'baseline-rally';development=product/'baseline-rally'
        bindings={adf,release,development,product/'native.lst',delivery/'package-report.json',delivery/'baseline-rally.compile.json'}
        tx.meta.update(files=snapshot(set(paths)|bindings),tools=tools,actual_target=dict(tx.meta['target'],video=standard),commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip())
        report.update(subject='maintained-native',interface_flavor='enhanced',adf_sha256=digest(adf),executable_sha256=digest(release),release_sha256=digest(release),development_sha256=digest(development))
        cfg=emulator_config()
        with CompactSession(attempt) as session:
            session.inspect('session_launch',dict(binary=cfg['tools']['copperline'],args=['--chipset','OCS','--video',standard,'--cpu','68000','--chip','512K','--slow','0','--fast','0','--noaudio','--floppy-drives','1','--floppy-speed','100',cfg['inputs']['amiga_rom']]))
            session.inspect('media.floppy.insert',dict(drive=0,path=str(adf),write_protected=True))
            catch=session.inspect('break.add',dict(kind='loadseg',name='baseline-rally'))
            position=session.inspect('run_until',dict(seconds=120));assert position['reason']=='loadseg',position
            session.inspect('break.remove',dict(id=catch['id']));segments=session.inspect('segments.list')['current']
            _,s=load_image(development,hunk_addresses=[r['start'] for r in segments])
            def raw(n,z):return bytes.fromhex(session.inspect('mem.read',dict(addr=s[n] if isinstance(n,str) else n,len=z))['data'])
            def value(n,z=1):return int.from_bytes(raw(n,z),'big')
            report['loaded_hunks']=loaded_hunks(release,segments,raw)
            callbacks=CallbackObserver(0,s);ackstart=None;acks=[]
            class Observer:
                def observe(self,msg):
                    nonlocal ackstart
                    callbacks.observe(msg)
                    row=msg.get('params',{})
                    if msg.get('method')=='event.mmio' and row.get('addr')==s['keyboard_ack']:
                        if row['value']:ackstart=row['position']['cck']
                        elif ackstart is not None:
                            duration=(row['position']['cck']-ackstart)*1e6/CLOCK[standard]
                            assert duration>=85,('keyboard ACK shorter than85us',duration)
                            acks.append(duration);ackstart=None
            session.observer=Observer()
            # No stack/canvas/full-bank tracing: finite timing and controls only.
            watches=callbacks.watches(FIELDS,raw)
            watches=[w for w in watches if w['addr']!=s['game_stack_bottom']]
            session.inspect('events.subscribe',dict(events=['mmio','frame'],mmio=watches))
            def advance(seconds):
                nonlocal position
                goal=position['cck']+int(seconds*CLOCK[standard])
                while position['cck']<goal:
                    # Transport batches only; every instruction/clock/input
                    # stays in the same guest order. Scalar loss telemetry is
                    # mandatory and fails on dropped notifications.
                    position=session.inspect('run_until',dict(cck=min(goal,position['cck']+CLOCK[standard]//50)))
            def state():return {n:value(n,z) for n,z in FIELDS.items()}
            def note(name,photo=False):
                row=dict(name=name,position=position,state=state(),core=raw('game_core_state',318).hex(),history=raw('game_history_state',72).hex())
                row['objects']=raw('game_scene_objects',64).hex()
                front=value('front_copper',4)
                if front:
                    bank=raw(front,s['copperlist_end']-s['copperlist'])
                    off=s['cop_spr0h']-s['copperlist']
                    pointers=[int.from_bytes(bank[off+i*8+2:off+i*8+4],'big')*65536+int.from_bytes(bank[off+i*8+6:off+i*8+8],'big') for i in range(8)]
                    row['displayed_sprite_headers']=[raw(p,4).hex() for p in pointers]
                if photo:
                    viewport=attempt/(name+'-viewport.png');view=attempt/(name+'.png')
                    session.inspect('capture.screenshot',dict(path=str(viewport)));native_view(viewport,view)
                    row.update(view=str(view),view_sha256=digest(view))
                report['observations'].append(row);return row
            def key(code,held):
                report['actions'].append(dict(rawkey=code,held=held,position=position))
                session.inspect('input.key',dict(rawkey=code,action='press' if held else 'release'))
            def tap(code,duration=.055):key(code,True);advance(duration);key(code,False);advance(.055)
            def until(name,predicate,seconds=8):
                limit=position['cck']+int(seconds*CLOCK[standard])
                while position['cck']<limit:
                    advance(.02)
                    if predicate():return note(name)
                raise AssertionError('Physical transition did not complete: '+name)
            def place_return():
                target=max(32,min(223,value('game_target_x')-8))
                x=value('tutorial_x');code=0x20 if x>target else 0x22
                if abs(x-target)<=1:
                    advance(1.2);preserve();return
                key(code,True)
                for _ in range(220):
                    advance(.02);x=value('tutorial_x')
                    if abs(x-target)<=1:break
                else:raise AssertionError('Physical legal placement did not reach incoming target')
                key(code,False);advance(1.2);preserve()
                note('reposition-'+str(value('tutorial_exploration_cycles',2)),True)
            advance(2.8);note('boot-title',True);tap(0x4c);tap(0x44)
            until('tutorial-entry',lambda:value('tutorial_active') and value('game_preview_status',2)>=2)
            advance(1.5);initial=note('initial-serve',True)
            assert_native_text(initial['view'],4,'TUTORIAL',True)
            assert_native_text(initial['view'],192,'WASD F ACT G TAP:TRY HOLD:MENU',True)
            report['checks']['boot_titleentry_initial_serve']=True
            original=raw('tutorial_interrupted_state',318);oldhist=raw('game_history_state',72)
            if value('game_preview_active'):oldhist=raw('game_preview_history_saved',72)
            oldrecords=raw('game_history_buffer',s['game_history_buffer_end']-s['game_history_buffer'])
            oldincoming=raw('game_history_incoming_storage',s['game_history_incoming_storage_end']-s['game_history_incoming_storage'])
            def preserve():
                assert raw('tutorial_interrupted_state',318)==original,'Original318 changed'
                assert raw('game_history_buffer',len(oldrecords))==oldrecords,'Original record/checkpoint buffer changed'
                if not value('game_preview_active'):
                    assert raw('game_history_state',72)==oldhist,'Public frozen72 changed'
                    assert raw('game_history_incoming_storage',len(oldincoming))==oldincoming,'Original incoming storage changed'
            # Direction modifier consumes G release without either menu or shot.
            key(0x24,True);key(0x20,True);advance(.075)
            key(0x20,False);key(0x24,False);advance(.12)
            assert not value('tutorial_menu') and value('tutorial_exploration_cycles',2)==0
            report['checks']['direction_chord_consumed']=True
            # Initial prospective held serve, including actual motion/AI response.
            tap(0x24)
            advance(.2);flight0=note('running-serve-0',True);assert flight0['state']['tutorial_running']
            advance(.2);flight1=note('running-serve-1',True);assert flight1['state']['tutorial_running']
            assert flight0['displayed_sprite_headers']!=flight1['displayed_sprite_headers'],'No native sprite motion in flight samples'
            report['checks']['running_native_sprite_scanout_samples']=True
            until('serve-opponent-response',lambda:not value('tutorial_running') and value('tutorial_exploration_cycles',2)==1)
            preserve();assert value('tutorial_stop_reason')==2 and value('tutorial_human_launched') and value('tutorial_opponent_launched')
            advance(1.2);incoming=note('first-incoming',True)
            assert value('game_preview_full_origin',2)==1 and value('game_preview_predictor_routes',2)==0x0101
            report['checks']['serve_stops_after_opponent_return']=True
            place_return()
            # Held press-time action, G and F released together.
            key(0x23,True);key(0x24,True);advance(.07);key(0x23,False);key(0x24,False)
            until('held-shot-stop',lambda:not value('tutorial_running') and value('tutorial_exploration_cycles',2)==2)
            preserve();assert value('tutorial_gesture_variant')==0,'B1 held press lost on release'
            advance(1.2);held=note('held-return',True)
            report['checks']['held_literal_press_snapshot']=True
            if value('tutorial_stop_reason')==2:
                place_return()
                tap(0x24)
                until('released-shot-stop',lambda:not value('tutorial_running') and value('tutorial_exploration_cycles',2)==3)
                preserve();assert value('tutorial_gesture_variant')==1
                advance(.8);note('released-return',True);report['checks']['released_literal_press_snapshot']=True
            else:raise AssertionError('Held return ended point before released-return coverage')
            # Long hold opens menu; confirm while G down and release do nothing.
            before=value('tutorial_exploration_cycles',2)
            key(0x24,True);advance(.55);assert value('tutorial_menu') and value('tutorial_gesture')==2
            tap(0x23);assert value('tutorial_active') and value('game_history_mode')==2
            key(0x24,False);advance(.15)
            assert value('tutorial_exploration_cycles',2)==before and value('tutorial_active')
            menu=note('options-fresh-confirm-required',True)
            for index,(y,text) in enumerate(((132,'PLAY FROM HERE'),(143,'RESUME ORIGINAL'),(154,'CLOSE MENU'))):assert_native_text(menu['view'],y,text,index==0)
            report['checks']['long_hold_release_consumed']=True
            # Resume Original at the exact restored boundary before reconcile.
            tap(0x4d)
            bp=session.inspect('break.add',dict(kind='pc',addr=s['tutorial_resume_restored']))
            key(0x44,True);position=session.inspect('run_until',dict(cck=position['cck']+2*CLOCK[standard]));assert position['pc']==s['tutorial_resume_restored'],position
            assert raw('game_core_state',318)==original and raw('game_history_buffer',len(oldrecords))==oldrecords
            expected=bytearray(oldhist);expected[s['game_history_mode']-s['game_history_state']]=1
            off=s['game_history_position']-s['game_history_state'];cur=s['game_history_cursor']-s['game_history_state'];expected[off:off+8]=oldhist[cur:cur+8]
            assert raw('game_history_state',72)==expected
            assert raw('game_history_incoming_storage',len(oldincoming))==oldincoming
            report['checks']['exact_original318_all72_records']=True
            session.inspect('break.remove',dict(id=bp['id']));advance(.055);key(0x44,False);advance(.12)
            assert not value('tutorial_active') and value('game_history_mode')==1
            # Re-enter through physical double G; explore and explicitly commit.
            tap(0x24);tap(0x24)
            until('reentry',lambda:value('tutorial_active'))
            advance(1.1);tap(0x24)
            until('second-exploration-stop',lambda:value('tutorial_explored') and not value('tutorial_running'))
            key(0x24,True);advance(.55);key(0x24,False);advance(.15)
            assert value('tutorial_menu') and value('tutorial_menu_selection')==0
            # This checkpoint breakpoint observes the actual committed full
            # state before physical reconciliation; no expected state supplied.
            bp=session.inspect('break.add',dict(kind='pc',addr=s['game_history_commit_current']))
            key(0x44,True);position=session.inspect('run_until',dict(cck=position['cck']+2*CLOCK[standard]));assert position['pc']==s['game_history_commit_current'],position
            committed=raw('game_core_state',318)
            commit_cursor=raw('game_history_cursor',8)
            session.inspect('break.remove',dict(id=bp['id']));advance(.055);key(0x44,False);advance(.12)
            assert not value('tutorial_active') and value('game_history_mode')==1
            checkpoints=[raw(s['game_history_buffer']+4096*14+i*(12+318),12+318) for i in range(64)]
            matching=[cp for cp in checkpoints if cp[:8]==commit_cursor]
            assert len(matching)==1 and matching[0][12:]==committed,'Play branch checkpoint differs from complete canonical boundary'
            report['checks']['play_from_here_full_checkpoint_exit']=True
            note('committed-live-play',True)
            # Stop at a normal loop boundary to avoid truncating a callback.
            bp=session.inspect('break.add',dict(kind='pc',addr=s['main_loop']))
            position=session.inspect('run_until',dict(cck=position['cck']+CLOCK[standard]//10));assert position['pc']==s['main_loop']
            session.inspect('break.remove',dict(id=bp['id']))
            interval=(value('simulation_interval_whole',4)<<16)|value('simulation_interval_fraction',2)
            report['callbacks']=callbacks.result(interval);report['callbacks'].pop('stack_bytes')
            report['keyboard_ack']=dict(count=len(acks),minimum_us=min(acks),maximum_us=max(acks),scope='Observed complete ACK pulses; no exhaustive hardware guarantee')
            assert ackstart is None and not value('keyboard_ack'),'Unclosed keyboard ACK at final boundary'
            assert not callbacks.dropped and acks and not value('missed_presentation_deadlines',2)
            report['raw_bytes']=session.raw_bytes;report['raw_cap_bytes']=session.MAX_RAW_BYTES
        report['passed']=True
    except BaseException as e:
        report.update(error=str(e),traceback=traceback.format_exc())
        if 'callbacks' in locals():report['partial_callbacks']=callbacks.rows
    tx.finalize(output,report,compiled=[json.loads((delivery/'baseline-rally.compile.json').read_text())],artifacts=[p for p in attempt.rglob('*') if p.is_file()])
    import shutil
    shutil.copy2(output,attempt/'report.json')
    print(json.dumps({k:v for k,v in report.items() if k not in ('callbacks','partial_callbacks','observations','actions','evidence')},indent=2))
    return report['passed']
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--ntsc',action='store_true');args=p.parse_args()
    raise SystemExit(0 if run('NTSC' if args.ntsc else 'PAL') else 1)
