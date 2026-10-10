"""Physical ADF entry and complete scanout evidence; never edits guest state."""
import argparse, gzip, json, os, shutil, subprocess, traceback
from pathlib import Path
from uuid import uuid4
from build_match_core import load_image
from native_tools import ROOT, emulator_config
from native_evidence import ReportRun, atomic_json, digest, inputs_for, snapshot
from native_hunk import loaded_hunks
from tutorial_capture import CaptureSession, CallbackObserver, native_view, animation, assert_native_text, assert_tutorial_menu
from tutorial_ux_observation import UXSurfaceObserver
from run_tutorial_capture import FIELDS
from tutorial_latency import instruction_map, StackTiming
from ordinary_cadence import chip_memory
from native_metrics import memory_summary

CLOCK = {'PAL':3546895, 'NTSC':3579545}

def blue_actor(path):
    from PIL import Image
    with Image.open(path) as source:
        image=source.convert('RGB')
        points=[(x,y) for y in range(120,192) for x in range(256) if image.getpixel((x,y))==(85,85,238)]
    assert points,'No lower native blue actor pixels'
    return min(x for x,y in points),min(y for x,y in points),max(x for x,y in points),max(y for x,y in points)

def pixel_response(rows,action,clock,predicate,limit_fields=3):
    for row in rows:
        if row['position']['cck']<=action['position']['cck']:continue
        try:predicate(row)
        except AssertionError:continue
        fields=row['position']['frame']-action['position']['frame']
        result=dict(observed_ms=(row['position']['cck']-action['position']['cck'])*1000/clock,
                    field_transitions=fields,first_pixel=row['name'],limit_fields=limit_fields)
        assert fields<=limit_fields,result
        return result
    raise AssertionError('Requested pixels never observed')

def run(standard, delivered, match):
    origin = 'match' if match else 'title'
    label = 'delivered' if delivered else 'candidate'
    directory = ROOT / ('build/tests/tutorial-ux-'+label+'-'+origin+'-'+standard.lower())
    directory.mkdir(parents=True, exist_ok=True)
    attempt = directory / uuid4().hex; attempt.mkdir()
    output = directory/'report.json'
    tx = ReportRun([output], 'native-feedback', 'maintained-native', 'Exact ADF physical tutorial entry and display scanout')
    report = dict(passed=False, attempt=str(attempt), standard=standard, origin=origin, product=label,
                  actions=[], frames=[], checks={}, scope='Finite physical scanout evidence; Copperline, not WinUAE.')
    try:
        paths, tools = inputs_for('native-feedback', 'scripts/run_tutorial_ux.py')
        product = ROOT/'build/delivery/tutorial-test-4baa6da' if delivered else ROOT/'build/amiga/interfaces/enhanced/delivery'
        adf = product/'baseline-rally.adf'
        release = product/('baseline-rally-release' if delivered else 'baseline-rally')
        development = product/'baseline-rally-development' if delivered else product.parent/'baseline-rally'
        listing = product/'native.lst' if delivered else product.parent/'native.lst'
        manifest = product/'release.compile.json' if delivered else product/'baseline-rally.compile.json'
        tx.meta.update(files=snapshot(set(paths)|{adf,release,development,listing,manifest}), tools=tools,
                       actual_target=dict(tx.meta['target'], video=standard),
                       commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                       environment={'RUST_LOG':os.environ.get('RUST_LOG'),'PYTHONPATH':os.environ.get('PYTHONPATH')})
        report.update(adf_sha256=digest(adf), executable_sha256=digest(release), development_sha256=digest(development))
        cfg=emulator_config()
        with CaptureSession(attempt) as session:
            session.inspect('session_launch', dict(binary=cfg['tools']['copperline'],args=['--chipset','OCS','--video',standard,'--cpu','68000','--chip','512K','--slow','0','--fast','0','--noaudio','--floppy-drives','1','--floppy-speed','100',cfg['inputs']['amiga_rom']]))
            session.inspect('media.floppy.insert',dict(drive=0,path=str(adf),write_protected=True))
            catch=session.inspect('break.add',dict(kind='loadseg',name='baseline-rally'))
            position=session.inspect('run_until',dict(seconds=120)); assert position['reason']=='loadseg',position
            session.inspect('break.remove',dict(id=catch['id']))
            segments=session.inspect('segments.list')['current']
            _, symbols=load_image(development,hunk_addresses=[r['start'] for r in segments])
            def raw(a,n):return bytes.fromhex(session.inspect('mem.read',dict(addr=a,len=n))['data'])
            report['loaded_hunks']=loaded_hunks(release,segments,raw)
            fields=dict(tutorial_active=1,tutorial_menu=1,tutorial_menu_selection=1,tutorial_x=1,tutorial_y=1,
                        tutorial_generation=4,tutorial_active_variant=1,tutorial_ball_mode=1,tutorial_render_phase=2,
                        tutorial_footer_dirty=1,tutorial_waiting_ready=1,tutorial_status=2,game_lifecycle=2,
                        game_score_initialized=1,game_lower_phase=1,game_upper_phase=1,
                        game_preview_status=2,game_preview_kind=2,game_preview_primed_mask=2,
                        game_preview_active=1,
                        game_preview_counts=4,game_preview_dispatch_stages=4,game_preview_synthetic_phases=4)
            callbacks=None;timing=None;frame_events=[];owners=[];control_writes=[];restores=[];frozen=None
            if not delivered:
                callbacks=CallbackObserver(0,symbols)
                callbacks.surfaces=UXSurfaceObserver(symbols,raw,last_line=311 if standard=='PAL' else 261,verify_sprites=True,verify_court_restores=True)
                calls,returns=instruction_map(listing.read_text(),segments,raw)
                timing=StackTiming(calls,returns,symbols['game_stack_bottom'],symbols['game_stack_top'])
                watched=dict(FIELDS,**fields,tutorial_preparing=1,tutorial_job_kind=2,tutorial_job_cost=4,
                             tutorial_jobs_completed=4,keyboard_ack=1,keyboard_ack_timer=2)
                class Observer:
                    def observe(self,message):
                        row=message.get('params',{})
                        if message.get('method')=='event.frame':frame_events.append(row)
                        if message.get('method')=='event.mmio' and symbols['game_stack_bottom']<=row.get('addr',0)<symbols['game_stack_top']:
                            previous_rows=len(timing.rows)
                            timing.observe(row)
                            if timing.stack and timing.stack[-1]['callee']=='tutorial_background' and timing.stack[-1]['entry']==row['position']:
                                timing.stack[-1]['jobs_before']=callbacks.state.get('tutorial_jobs_completed',0)
                            if len(timing.rows)>previous_rows and timing.rows[-1]['callee']=='tutorial_background':
                                call=timing.rows[-1]
                                call.update(job_kind=callbacks.state.get('tutorial_job_kind'),job_cost=callbacks.state.get('tutorial_job_cost'))
                                call['accepted']=callbacks.state.get('tutorial_jobs_completed',0)>call.get('jobs_before',0)
                                if call['accepted']:owners.append(call)
                        callbacks.observe(message)
                        if message.get('method')=='event.mmio':
                            for name in ('tutorial_x','tutorial_y','tutorial_menu','tutorial_menu_selection','tutorial_generation','keyboard_ack'):
                                if row.get('addr')==symbols[name]:control_writes.append(dict(name=name,value=row['value'],position=row['position']))
                session.observer=Observer()
                session.inspect('events.subscribe',dict(events=['mmio','frame'],mmio=callbacks.watches(watched,raw)+callbacks.surfaces.watches()+[dict(addr=symbols['game_stack_bottom'],len=symbols['game_stack_top']-symbols['game_stack_bottom'],access='access')]))
            else:
                class Frames:
                    def observe(self,message):
                        if message.get('method')=='event.frame':frame_events.append(message['params'])
                session.observer=Frames();session.inspect('events.subscribe',dict(events=['frame']))
            report['pixel_timing_basis']='Pinned screenshot renderer replays the last completed field. Times are observation upper bounds; run_until CCK batches are at most 1 ms, without guest delays.'
            # LoadSeg stops before entry/startup. Let the product install its
            # own low-resolution display before applying native pixel geometry.
            startup_goal=position['cck']+2*CLOCK[standard]
            while position['cck']<startup_goal:
                position=session.inspect('run_until',dict(cck=min(startup_goal,position['cck']+CLOCK[standard]//1000)))
            def state():return {n:int.from_bytes(raw(symbols[n],w),'big') for n,w in fields.items() if n in symbols}
            def frame(name):
                nonlocal position
                target_frame=position['frame']+1
                # Bound event batches, not guest work: every native instruction
                # and elapsed guest clock still runs in its original order.
                while position['frame']<target_frame:
                    position=session.inspect('run_until',dict(cck=position['cck']+CLOCK[standard]//1000))
                    if position.get('pc')==symbols.get('tutorial_resume_restored'):
                        core=raw(symbols['game_core_state'],318);history=raw(symbols['game_history_state'],72)
                        assert frozen is not None and core==frozen['interrupted'],'Resume differs from exact interrupted core'
                        assert raw(symbols['game_history_buffer'],symbols['game_history_buffer_end']-symbols['game_history_buffer'])==frozen['records'],'Frozen records changed before resume'
                        expected=bytearray(frozen['history']);origin=symbols['game_history_state']
                        expected[symbols['game_history_mode']-origin]=1
                        off=symbols['game_history_position']-origin;cursor=symbols['game_history_cursor']-origin
                        expected[off:off+8]=frozen['history'][cursor:cursor+8]
                        assert history==expected,'Resume differs from original history metadata'
                        restores.append(dict(position=position,core=core.hex(),history=history.hex(),expected_core=frozen['interrupted'].hex(),expected_history=expected.hex()))
                        session.inspect('break.remove',dict(id=resume_break['id']))
                viewport=attempt/(name+'-viewport.png'); native=attempt/(name+'.png')
                session.inspect('capture.screenshot',dict(path=str(viewport)));native_view(viewport,native)
                row=dict(name=name,position=position,path=str(native),sha256=digest(native),state=state())
                row['objects']=raw(symbols['game_scene_objects'],64).hex()
                row['core']=raw(symbols['game_core_state'],318).hex()
                row['history']=raw(symbols['game_history_state'],72).hex()
                if frozen is not None and row['state']['tutorial_active']:
                    assert row['core']==frozen['core'].hex(),'Tutorial changed frozen canonical core'
                    if not row['state']['game_preview_active']:
                        assert row['history']==frozen['history'].hex(),'Tutorial changed public frozen history'
                if callbacks is not None:
                    scenes=[p for p in callbacks.surfaces.publications if p['position']['frame']<=position['frame']-2]
                    if scenes:row['displayed_scene']=scenes[-1]
                row['completed_frame']=position['frame']-1
                report['frames'].append(row);return row
            def frames(prefix,count):return [frame(prefix+'-%03d'%i) for i in range(count)]
            def key(code,held):
                report['actions'].append(dict(rawkey=code,held=held,position=position))
                session.inspect('input.key',dict(rawkey=code,action='press' if held else 'release'))
                return report['actions'][-1]
            # Authored physical route, with no state/seed injection or dispatcher breaks.
            frames('boot-title',40)
            key(0x01 if match else 0x4c,True);frames('choose-entry',3)
            key(0x01 if match else 0x4c,False);frames('choose-release',3)
            if match:
                frames('match-start',70)
                for tap in range(2):
                    key(0x24,True);frames('enter-press-'+str(tap),2)
                    key(0x24,False);frames('enter-release-'+str(tap),2)
            else:
                key(0x44,True);frames('enter',4);key(0x44,False)
            # Equal initial observation duration across actual display standards:
            # PAL60 fields and NTSC72 fields are approximately1.2 seconds.
            # Sixty NTSC fields ended before the original score/serve boundary.
            initial_fields=60 if standard=='PAL' or delivered else 72
            stable=frames('tutorial-initial',initial_fields)
            assert any(r['state']['tutorial_active'] for r in stable),'Physical entry never activated tutorial'
            # Keep collecting after visual failures so slow controls remain measurable.
            def check(name,call):
                try:report['checks'][name]=dict(passed=True,result=call())
                except AssertionError as e:report['checks'][name]=dict(passed=False,error=str(e))
            check('initial-banner',lambda:assert_native_text(stable[-1]['path'],4,'TUTORIAL',True))
            if not delivered:
                check('initial-controls',lambda:assert_native_text(stable[-1]['path'],192,'WASD MOVE  HOLD F  G MENU',True))
                metadata=raw(symbols['game_preview_history_saved'],72) if stable[-1]['state']['game_preview_active'] else bytes.fromhex(stable[-1]['history'])
                frozen=dict(core=bytes.fromhex(stable[-1]['core']),history=metadata,interrupted=raw(symbols['tutorial_interrupted_state'],318),records=raw(symbols['game_history_buffer'],symbols['game_history_buffer_end']-symbols['game_history_buffer']))
                def frozen_ball():
                    scenes=[p for p in callbacks.surfaces.publications if (p.get('native_sprite_check') or {}).get('matched') and p['tutorial_fields'].get('tutorial_ball_mode')==0 and bytes.fromhex(p['objects'])[53] and bytes.fromhex(p['objects'])[61]]
                    assert scenes,'No actual visible frozen ball/shadow publication'
                    from PIL import Image
                    matched=[]
                    for photo in stable:
                        scene=photo.get('displayed_scene',{})
                        if scene not in scenes:continue
                        objects=bytes.fromhex(scene['objects']);x,y=objects[49],objects[48]+1
                        with Image.open(photo['path']) as image:
                            white=sum(image.convert('RGB').getpixel((px,py))==(255,255,255) for py in range(y,min(y+16,192)) for px in range(x,min(x+16,256)))
                        if white:matched.append(dict(photo=photo['name'],ball_pixels=white,objects=objects[48:64].hex()))
                    assert matched,'Frozen native ball has no visible white image pixels'
                    return matched
                check('frozen-ball',frozen_ball)
                resume_break=session.inspect('break.add',dict(kind='pc',addr=symbols['tutorial_resume_restored']))
            original_actor=blue_actor(stable[-1]['path'])
            movement=key(0x22,True);moving=frames('move-right',20);key(0x22,False);frames('move-release',3)
            def moved(row):assert blue_actor(row['path'])!=original_actor,'Actor pixels unchanged'
            if not delivered:check('movement-response',lambda:pixel_response(moving,movement,CLOCK[standard],moved))
            if not delivered:
                key(0x20,True);left=frames('move-left',30);key(0x20,False);frames('left-release',3)
                def continuous():
                    boxes=[blue_actor(r['path']) for r in left];changes=[i for i in range(1,len(boxes)) if boxes[i]!=boxes[i-1]]
                    assert len(changes)>=27,dict(changed_fields=len(changes),total_fields=len(boxes))
                    assert max(b-a for a,b in zip(changes,changes[1:]))<=2,changes
                    assert changes[0]<=2 and len(boxes)-1-changes[-1]<=2,changes
                    return dict(changed_fields=len(changes),total_fields=len(boxes),maximum_change_gap_fields=max(b-a for a,b in zip(changes,changes[1:])))
                check('continuous-movement',continuous)
            key(0x23,True);held=frames('held-preview',70 if delivered else 140)
            if not delivered:
                check('held-controls',lambda:assert_native_text(held[-1]['path'],192,'WASD MOVE  HOLD F  G MENU',True))
                def landing():
                    from PIL import Image
                    seen=[]
                    for photo in held:
                        scene=photo.get('displayed_scene',{});cue=scene.get('landing',{})
                        if not cue.get('valid'):continue
                        coords=[(cue['x']+dx,cue['y']+dy) for dx,dy in ((-2,0),(-1,0),(0,0),(1,0),(2,0),(0,-2),(0,-1),(0,1),(0,2))]
                        coords=[(x,y) for x,y in coords if 0<=x<256 and 0<=y<192 and not (96<=x<160 and 4<=y<12)]
                        with Image.open(photo['path']) as image:
                            white=sum(image.convert('RGB').getpixel(p)==(255,255,255) for p in coords)
                        if white:seen.append(dict(photo=photo['name'],ground=[cue['x'],cue['y']],visible_cross_pixels=white,index=scene['tutorial_fields']['tutorial_animation_index']))
                    assert seen,'No current native landing cross pixels observed'
                    assert len(seen)>=3,'Landing cue was not persistent across completed fields'
                    return seen
                check('landing-cue',landing)
            key(0x23,False);frames('released-preview',10)
            key(0x24,True);frames('menu-press',2);open_action=key(0x24,False)
            menu=frames('menu-open',160 if delivered else 8)
            check('menu-open',lambda:assert_tutorial_menu(menu[-1]['path'],0))
            if not delivered:check('menu-open-response',lambda:pixel_response(menu,open_action,CLOCK[standard],lambda r:assert_tutorial_menu(r['path'],0)))
            down_action=key(0x4d,True);down=frames('menu-down',3);key(0x4d,False);selection=frames('menu-select',160 if delivered else 8)
            check('menu-selected',lambda:assert_tutorial_menu(selection[-1]['path'],1))
            if not delivered:
                check('menu-selection-response',lambda:pixel_response(down+selection,down_action,CLOCK[standard],lambda r:assert_tutorial_menu(r['path'],1)))
                key(0x24,True);frames('close-press',2);close_action=key(0x24,False);closed=frames('menu-close',8)
                def closed_pixels(row):
                    assert_native_text(row['path'],192,'WASD MOVE  HOLD F  G MENU',True)
                    assert not row.get('displayed_scene',{}).get('tutorial_fields',{}).get('tutorial_menu',1),'Menu bank still displayed'
                check('menu-close-response',lambda:pixel_response(closed,close_action,CLOCK[standard],closed_pixels))
                key(0x24,True);frames('reopen-press',2);key(0x24,False);frames('menu-reopen',8)
                key(0x4d,True);frames('resume-down',3);key(0x4d,False);frames('resume-selected',4)
                key(0x44,True);frames('resume-press',3);key(0x44,False);resumed=frames('resumed',8)
                check('exact-resume',lambda:bool(len(restores)==1 and not resumed[-1]['state']['tutorial_active']) or (_ for _ in ()).throw(AssertionError('Exact original resume was not observed')))
                def resumed_pixels():
                    blue_actor(resumed[-1]['path'])
                    assert not resumed[-1].get('displayed_scene',{}).get('tutorial_fields',{}).get('tutorial_active',1),'Tutorial canvas still displayed after resume'
                    try:assert_native_text(resumed[-1]['path'],4,'TUTORIAL',True)
                    except AssertionError:return dict(original_display=True)
                    raise AssertionError('Tutorial banner remained after resume')
                check('resume-banner-cleared',resumed_pixels)
            report['animation']=animation([Path(r['path']) for r in report['frames'] if r['name'].startswith(('tutorial-initial','move-right','held-preview','menu-open','menu-select'))],attempt/'scanout.gif',20 if standard=='PAL' else 17)
            report['passed']=all(c['passed'] for c in report['checks'].values())
            report['frame_events']=frame_events
            report.update(control_writes=control_writes,restores=restores)
            if callbacks is not None:
                catch=session.inspect('break.add',dict(kind='pc',addr=symbols['main_loop']))
                tail=session.inspect('run_until',dict(cck=position['cck']+CLOCK[standard]//10))
                assert tail['pc']==symbols['main_loop'] and callbacks.pending is None and not timing.stack,'Incomplete final owner'
                session.inspect('break.remove',dict(id=catch['id']))
                report.update(publications=callbacks.surfaces.publications,callbacks=callbacks.rows,
                              footer_writes=callbacks.surfaces.footer_writes,memory=memory_summary(chip_memory(raw)))
                with gzip.open(attempt/'calls.jsonl.gz','wt') as stream:
                    for call in timing.rows:stream.write(json.dumps(call,separators=(',',':'))+'\n')
                report['owner_samples']=owners
                # Actual fixed-point interval is adjacent whole/fraction words.
                interval=int.from_bytes(raw(symbols['simulation_interval_whole'],4),'big')*65536+int.from_bytes(raw(symbols['simulation_interval_fraction'],2),'big')
                report['callback_timing']=callbacks.result(interval)
        tx.finalize(output,report,compiled=[json.loads(manifest.read_text())],artifacts=[p for p in attempt.rglob('*') if p.is_file()])
        shutil.copy2(output,attempt/'report.json')
        print(json.dumps(dict(passed=report['passed'],attempt=str(attempt),checks=report['checks'])),flush=True)
        return report['passed']
    except BaseException as error:
        if 'callbacks' in locals() and callbacks is not None:
            report.update(publications=callbacks.surfaces.publications,callbacks=callbacks.rows,owner_samples=owners)
        if 'timing' in locals() and timing is not None:
            with gzip.open(attempt/'calls.jsonl.gz','wt') as stream:
                for call in timing.rows:stream.write(json.dumps(call,separators=(',',':'))+'\n')
        atomic_json(attempt/'failure.json',dict(error=str(error),traceback=traceback.format_exc(),partial=report));tx.abort(error);raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--ntsc',action='store_true');p.add_argument('--delivered',action='store_true');p.add_argument('--match',action='store_true');a=p.parse_args()
    raise SystemExit(0 if run('NTSC' if a.ntsc else 'PAL',a.delivered,a.match) else 1)
