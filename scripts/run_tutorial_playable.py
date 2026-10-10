"""Finite physical prototype controls/resume capture; no full acceptance claim.

No world writes or callback injection. The original initial-serve failure remains an immutable failed court receipt.
The optional serve probe qualifies the staged lower initial-serve route; neither
probe claims title Tutorial or complete playable acceptance.
"""
import argparse,hashlib,json,os,shutil,subprocess,traceback
from pathlib import Path
from uuid import uuid4
from build_match_core import load_image
from build_native_game import build
from native_tools import ROOT,emulator_config
from native_evidence import ReportRun,atomic_json,digest,inputs_for,snapshot
from native_hunk import loaded_hunks
from tutorial_capture import CaptureSession,CallbackObserver,native_view,animation,assert_tutorial_menu
from coherent_publication import CoherentSurfaceObserver
from run_tutorial_capture import FIELDS
from tutorial_latency import instruction_map,StackTiming
from ordinary_cadence import chip_memory
from native_metrics import memory_summary

CLOCK={'PAL':3546895,'NTSC':3579545};PROVIDER=3546895

def run(standard,serve=False):
    directory=ROOT/'build/tests'/(('tutorial-serve-' if serve else 'tutorial-playable-')+standard.lower())
    directory.mkdir(exist_ok=True);attempt=directory/uuid4().hex;attempt.mkdir()
    output=directory/'report.json';tx=ReportRun([output],'native-feedback','maintained-native','Physical current prototype incoming, controls and exact original resume')
    report={'passed':False,'attempt':str(attempt),'standard':standard,'origin':'initial-serve' if serve else 'incoming'}
    try:
        paths,tools=inputs_for('native-feedback','scripts/run_tutorial_playable.py')
        tx.meta.update(files=snapshot(paths),tools=tools,actual_target=dict(tx.meta['target'],video=standard),commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),environment={'RUST_LOG':os.environ.get('RUST_LOG'),'PYTHONPATH':os.environ.get('PYTHONPATH')})
        build()
        product=ROOT/'build/amiga/interfaces/enhanced'
        for n in ('baseline-rally','baseline-rally.compile.json','native.lst'):shutil.copy2(product/n,attempt/n)
        exe=attempt/'baseline-rally';report['executable_sha256']=digest(exe)
        listing=(attempt/'native.lst').read_text();cfg=emulator_config();hz=CLOCK[standard]
        menu_stage_samples=[];stage_snapshots=[];stage_protocols=[];photos=[];actions=[];restores=[];interrupted=None;frozen=None;metadata=None;first_resume=None;logical_samples=[];checkpoints=[]
        with CaptureSession(attempt) as session:
            session.inspect('session_launch',dict(binary=cfg['tools']['copperline'],run=str(exe),args=['--chipset','OCS','--video',standard,'--cpu','68000','--chip','512K','--slow','0','--fast','0','--noaudio',cfg['inputs']['amiga_rom']]))
            stop=session.inspect('run_until',dict(seconds=30));assert stop['reason']=='loadseg'
            segments=session.inspect('segments.list')['current'];images,s=load_image(exe,hunk_addresses=[x['start'] for x in segments])
            def raw(a,n):return bytes.fromhex(session.inspect('mem.read',dict(addr=a,len=n))['data'])
            def block(n,e):return raw(s[n],s[e]-s[n])
            def num(n,width=None):return int.from_bytes(raw(s[n],FIELDS.get(n,2) if width is None else width),'big')
            loaded=loaded_hunks(exe,segments,raw)
            callbacks=CallbackObserver(0,s)
            callbacks.surfaces=CoherentSurfaceObserver(s,raw,last_line=311 if standard=='PAL' else 261,verify_sprites=True)
            calls,returns=instruction_map(listing,segments,raw);timing=StackTiming(calls,returns,s['game_stack_bottom'],s['game_stack_top'])
            stack_low=s['game_stack_top'];ack=[];field_rows=[]
            extra=dict(tutorial_job_cost=4,tutorial_job_budget=2,tutorial_job_kind=2,tutorial_job_variant=2,tutorial_job_stage=2,
                game_preview_dispatch_stages=4,game_preview_dispatch_generations=8,game_preview_dispatch_launches=2,
                game_preview_primed_mask=2,game_preview_synthetic_phases=4,game_preview_flight_phases=4,
                simulation_interval=4,simulation_phase=4,keyboard_ack=1,keyboard_ack_timer=2)
            watched=dict(FIELDS,**extra);by_address={s[n]+offset:n for n,width in watched.items() for offset in range(width)}
            class Observer:
                def observe(self,message):
                    nonlocal stack_low
                    row=message.get('params',{})
                    if row.get('access') in ('read','write') and s['game_stack_bottom']<=row.get('addr',0)<s['game_stack_top']:
                        if row['access']=='write':stack_low=min(stack_low,row['addr'])
                        timing.observe(row)
                    if row.get('addr')==s['keyboard_ack'] and row.get('access')=='write':ack.append(row)
                    if row.get('addr') in by_address and row.get('access')=='write':
                        field_rows.append({k:row[k] for k in ('addr','size','value','pc','position')})
                    if frozen is not None and callbacks.state.get('tutorial_active') and row.get('access')=='write':
                        address=row.get('addr',0);size=row.get('size',0)
                        assert address+size<=s['game_history_buffer'] or address>=s['game_history_buffer_end'],'Paused history record write'
                    callbacks.observe(message)
            session.observer=Observer()
            subscription=session.inspect('events.subscribe',dict(events=['mmio','frame'],mmio=callbacks.watches(watched,raw)+callbacks.surfaces.watches()+[dict(addr=s['game_history_buffer'],len=s['game_history_buffer_end']-s['game_history_buffer'],access='write'),dict(addr=s['game_stack_bottom'],len=s['game_stack_top']-s['game_stack_bottom'],access='access')]))
            assert not subscription.get('dropped_notifications',0),'Dropped native write-watch notifications'
            session.inspect('break.add',dict(kind='pc',addr=s['simulation_update']))
            session.inspect('break.add',dict(kind='pc',addr=s['tutorial_resume_restored']))
            if serve:session.inspect('break.add',dict(kind='pc',addr=s['tutorial_redraw']))
            beginning=stop['cck'];current=beginning;resume_pending=False;reconciled=0
            def advance(seconds,stop_partial=False):
                nonlocal current,interrupted,frozen,metadata,resume_pending,first_resume,reconciled
                goal=current+round(seconds*hz);assert goal-beginning<90*hz
                for _ in range(200000):
                    result=session.inspect('run_until',dict(seconds=min(goal,current+hz//1000)/PROVIDER));current=result['cck']
                    if serve and result.get('pc')==s['tutorial_redraw'] and num('tutorial_menu',1):
                        menu_stage_samples.append(dict(position=result,generation=num('tutorial_generation',4),stages=raw(s['game_preview_dispatch_stages'],4).hex(),owners=raw(s['game_preview_dispatch_generations'],8).hex()))
                    if result.get('pc')==s['tutorial_resume_restored']:
                        assert interrupted is not None
                        assert block('game_history_buffer','game_history_buffer_end')==frozen['game_history_buffer'],'Frozen records changed before exact resume'
                        state=raw(s['game_core_state'],318);history=raw(s['game_history_state'],72)
                        assert state==raw(s['tutorial_interrupted_state'],318)==interrupted
                        expected=bytearray(metadata);origin=s['game_history_state']
                        expected[s['game_history_mode']-origin]=1
                        off=s['game_history_position']-origin;cursor=s['game_history_cursor']-origin
                        expected[off:off+8]=metadata[cursor:cursor+8]
                        assert history==expected,'Exact resume modified unrelated history metadata'
                        restores.append(dict(state=state.hex(),expected_state=interrupted.hex(),history=history.hex(),expected_history=expected.hex(),position=result));resume_pending=True
                    if result.get('pc')==s['simulation_update']:
                        assert callbacks.pending is None
                        if num('tutorial_active',1):
                            state=raw(s['game_core_state'],318);history=raw(s['game_history_state'],72)
                            if interrupted is None:
                                interrupted=raw(s['tutorial_interrupted_state'],318);metadata=history
                                assert not interrupted[s['game_input_bits']-s['game_core_state']]&0x10,'Interrupted logical F must be released'
                                frozen={n:block(n,e) for n,e in (('game_core_state','game_core_state_end'),('game_history_buffer','game_history_buffer_end'))}
                            assert block('game_core_state','game_core_state_end')==frozen['game_core_state']
                            assert history==metadata and raw(s['tutorial_interrupted_state'],318)==interrupted
                            if serve:
                                stages=raw(s['game_preview_dispatch_stages'],4)
                                if int.from_bytes(stages,'big'):
                                    sample=dict(position=result,generation=num('tutorial_generation',4),preview_generation=num('game_preview_generation',4),stages=stages.hex(),owners=raw(s['game_preview_dispatch_generations'],8).hex(),launches=raw(s['game_preview_launches'],2).hex(),counts=raw(s['game_preview_counts'],4).hex(),phases=raw(s['game_preview_synthetic_phases'],4).hex())
                                    stage_snapshots.append(sample)
                                    if stop_partial and sample['generation']==sample['preview_generation']:return sample
                        elif resume_pending:
                            assert raw(s['game_core_state'],318)==interrupted,'Normal callback preceded exact restoration'
                            first_resume=result;resume_pending=False
                        elif first_resume is not None:
                            logical_samples.append(dict(position=result,bits=raw(s['game_input_bits'],2).hex(),pressed=raw(s['game_input_pressed'],2).hex()))
                            assert not (raw(s['game_input_pressed'],2)[0]&0x10),'Newly held confirm leaked as shot edge'
                            assert not (raw(s['game_input_bits'],2)[0]&0x10),'Newly held physical F leaked as logical action'
                            reconciled+=1
                    if current>=goal or result.get('reason')=='target' and current>=goal-1:return
                raise AssertionError('Finite complete-boundary cap')
            def partial_checkpoint(early=False):
                for _ in range(200):
                    sample=advance(.01,stop_partial=True)
                    if sample and (not early or 1<=int(sample['stages'][:4],16)<=2):return sample
                raise AssertionError('No genuine partial serve stage at callback boundary')
            def key(code,held,seconds=.06):
                actions.append(dict(rawkey=code,held=held,cck=current))
                session.inspect('input.key',dict(rawkey=code,action='press' if held else 'release'));advance(seconds)
            def photo(name):
                viewport=attempt/(name+'-viewport.png');native=attempt/(name+'.png')
                session.inspect('capture_screenshot',dict(path=str(viewport)));native_view(viewport,native)
                photos.append(dict(name=name,path=str(native),sha256=digest(native)));return native
            def scene_checkpoint(name,after,variant,endpoint=False,waiting=False):
                generation=num('tutorial_generation',4)
                for _ in range(200):
                    scenes=[p for p in callbacks.surfaces.publications if p['position']['cck']>=after
                        and p.get('tutorial_fields',{}).get('tutorial_active_variant')==variant
                        and p.get('tutorial_fields',{}).get('tutorial_generation')==generation
                        and p.get('publication_live_fields',{}).get('tutorial_generation')==generation
                        and p.get('native_sprite_check',{}).get('matched')]
                    if waiting:
                        scenes=[p for p in scenes if p['tutorial_fields'].get('tutorial_waiting_ready')]
                    if endpoint:
                        scenes=[p for p in scenes if p['tutorial_fields'].get('tutorial_ball_mode') in (1,2)
                            and (p.get('endpoint_ready',0)>>8 if variant==0 else p.get('endpoint_ready',0)&255)
                            and (p.get('endpoint_outcomes',0)>>(16 if variant==0 else 0))&65535]
                    if scenes:
                        checkpoints.append(dict(name=name,generation=generation,variant=variant,scene=scenes[-1],requires_endpoint=endpoint));return
                    advance(.01)
                raise AssertionError('No current-generation published '+name)
            def menu_checkpoint(name,selection,after):
                generation=num('tutorial_generation',4);render=num('tutorial_render_generation',2)
                for _ in range(1000):
                    scenes=[p for p in callbacks.surfaces.publications if p['position']['cck']>=after
                        and p.get('tutorial_fields',{}).get('tutorial_menu')
                        and p['tutorial_fields'].get('tutorial_menu_selection')==selection
                        and p['tutorial_fields'].get('tutorial_render_generation')==render
                        and p['tutorial_fields'].get('tutorial_generation')==generation
                        and p.get('surface') in (s['tutorial_surface0'],s['tutorial_surface1'])
                        and p.get('native_sprite_check',{}).get('matched')]
                    if scenes:
                        advance(.05) # Two complete fields after actual COPJMP, for raster capture.
                        stable=callbacks.surfaces.current_presentation(callbacks.state)
                        displayed=callbacks.surfaces.displayed
                        assert stable and displayed and displayed['surface']==scenes[-1]['surface']
                        bank=displayed['tutorial_fields']
                        assert bank['tutorial_menu'] and bank['tutorial_menu_selection']==selection
                        assert bank['tutorial_render_generation']==render and bank['tutorial_generation']==generation
                        raster=assert_tutorial_menu(photo(name),selection)
                        checkpoints.append(dict(name=name,generation=generation,render_generation=render,selection=selection,scene=scenes[-1],capture_scene=displayed,capture_cck=current,raster=raster));return
                    advance(.01)
                raise AssertionError('No completed visible menu '+name)
            advance(.7);photo('title')
            key(1,True);key(1,False,1.4);assert num('game_lifecycle',2)==1
            if not serve:
                key(0x23,True,.04);key(0x23,False,.02)
                for _ in range(200):
                    if num('game_contact',1)&0x40 and num('game_flight',1)&0x40 and not num('game_contact',1)&0x8d:break
                    advance(.02)
                else:raise AssertionError('No actual physical incoming flight')
            key(0x24,True,.02);key(0x24,False,.02);key(0x24,True,.02);key(0x24,False,.02)
            assert num('tutorial_active',1)
            if serve:
                advance(1);assert num('game_preview_kind',2)==3
                scene_checkpoint('initial-released-wait',beginning,1,waiting=True)
            key(0x23,True);advance(2)
            if serve:
                for _ in range(200):
                    if num('game_preview_launches',1) and num('game_preview_endpoint_ready',1):break
                    advance(.05)
                else:raise AssertionError('No finite initial-serve held endpoint')
            elif not num('game_preview_launches',1):
                count=num('game_preview_counts');path=raw(s['game_preview_paths'],count*8);assert count
                sample=min((path[i:i+8] for i in range(0,len(path),8)),key=lambda p:abs(p[1]-(num('tutorial_y',1)+27)))
                target=max(40,min(199,sample[0]-8));direction=0x20 if target<num('tutorial_x',1) else 0x22
                session.inspect('input.key',dict(rawkey=direction,action='press'));actions.append(dict(rawkey=direction,held=True,cck=current))
                for _ in range(400):
                    x=num('tutorial_x',1)
                    if direction==0x20 and x<=target or direction==0x22 and x>=target:break
                    advance(.01)
                else:raise AssertionError('Physical alignment cap')
                key(direction,False);advance(2)
            assert num('game_preview_launches',1) and num('game_preview_endpoint_ready',1),'No actual held edited contact endpoint'
            scene_checkpoint('incoming-held',beginning,0,True)
            photo('incoming-held')
            frames=[]
            for i in range(10):advance(.1);frames.append(photo('animation-%02d'%i))
            animation_info=animation(frames,attempt/'incoming-animation.gif',100)
            if serve:
                key(0x22,True,.02);key(0x22,False,.01)
                pending=partial_checkpoint();old=pending['generation']
                key(0x20,True,.02);key(0x20,False,.01)
                assert num('tutorial_generation',4)>old,'Physical edit did not replace partial generation'
                stages=raw(s['game_preview_dispatch_stages'],4);owners=raw(s['game_preview_dispatch_generations'],8)
                assert all(not int.from_bytes(stages[2*v:2*v+2],'big') or int.from_bytes(owners[4*v:4*v+4],'big')!=old for v in (0,1)),'Retired partial generation remains owned'
                stage_protocols.append(dict(kind='physical-replacement',before=pending,after_generation=num('tutorial_generation',4),after_stages=stages.hex(),after_owners=owners.hex(),cck=current))
            start_generation=num('tutorial_generation',4);edit_start=current
            key(0x22,True,.1);key(0x22,False);key(0x20,True,.1);key(0x20,False);advance(1)
            assert num('tutorial_generation',4)>start_generation,'Continuous physical edits did not invalidate prediction'
            scene_checkpoint('after-edits',edit_start,0,True)
            photo('after-edits');release_start=current;key(0x23,False);advance(1)
            assert num('tutorial_active_variant',1)==1;scene_checkpoint('released-alternative',release_start,1,waiting=serve);photo('released-alternative')
            held_start=current;key(0x23,True);advance(1);assert num('tutorial_active_variant',1)==0
            scene_checkpoint('held-reselected',held_start,0,True)
            # Modifier consumes direction and release; navigation is absent.
            selected_cursor=raw(s['tutorial_selected_cursor'],8)
            key(0x24,True);key(0x22,True);key(0x22,False);key(0x24,False)
            assert not num('tutorial_menu',1) and raw(s['tutorial_selected_cursor'],8)==selected_cursor
            if serve:
                key(0x22,True,.02);key(0x22,False,.01)
                key(0x24,True)
                pending_resume=partial_checkpoint(early=True)
                menu_start=current;key(0x24,False)
            else:
                menu_start=current;key(0x24,True);key(0x24,False)
            assert num('tutorial_menu',1)
            if serve:
                accepted=menu_stage_samples[-1]
                assert accepted['position']['cck']>=menu_start and int(accepted['stages'],16),'Menu did not accept a genuine partial serve'
                assert accepted['generation']==pending_resume['generation']
                assert raw(s['game_preview_dispatch_stages'],4).hex()==accepted['stages'],'Opened menu advanced suspended serve operation'
                stage_protocols.append(dict(kind='pending-original-resume',before_physical_release=pending_resume,at_menu_accept=accepted,menu_cck=current))
            menu_checkpoint('options',0,menu_start)
            menu_start=current;key(0x4d,True);key(0x4d,False);assert num('tutorial_menu_selection',1)==1
            menu_checkpoint('options-resume',1,menu_start)
            preview_before_resume=num('game_preview_generation',4)
            key(0x44,True);key(0x44,False);advance(.2)
            assert not num('tutorial_active',1) and len(restores)==1 and first_resume and reconciled>=2
            assert num('game_preview_generation',4)!=preview_before_resume and num('game_preview_status',2)==7,'Resume did not retire preview generation'
            assert num('game_preview_dispatch_stages',4)==0,'Canceled continuation remains eligible'
            assert num('game_preview_endpoint_ready',2)==0 and num('game_preview_launch_saved',2)==0,'Canceled preview still eligible'
            assert num('keyboard_ack',1)==0 and raw(s['game_keyboard_matrix']+0x24,1)==b'\0'
            assert any(r['value'] for r in ack) and any(not r['value'] for r in ack),'No complete physical keyboard ACK'
            assert all(raw(s['game_keyboard_matrix']+k,1)==b'\0' for k in (0x20,0x22,0x24,0x44,0x4d)), 'Direction/menu keys not released'
            assert raw(s['game_keyboard_matrix']+0x23,1)!=b'\0','F must remain physically held for reconciliation fixture'
            photo('resumed-original')
            session.inspect('break.clear');session.inspect('break.add',dict(kind='pc',addr=s['main_loop']))
            tail=session.inspect('run_until',dict(seconds=(current+round(.03*hz))/PROVIDER))
            assert tail.get('pc')==s['main_loop'] and callbacks.pending is None and not timing.stack,'Incomplete final native owner'
            memory=memory_summary(chip_memory(raw))
            publications=callbacks.surfaces.publications
            tutorial_scenes=[p for p in publications if p.get('tutorial_fields',{}).get('tutorial_active')]
            assert tutorial_scenes,'No actual completed tutorial publication'
            # Export observed evidence before audits, including a failed audit.
            report.update(menu_stage_samples=menu_stage_samples,stage_snapshots=stage_snapshots,stage_protocols=stage_protocols,actions=actions,photos=photos,checkpoints=checkpoints,restores=restores,first_resumed_boundary=first_resume,
                reconciled_samples=logical_samples,ack=ack,memory=memory,stack_used_bytes=s['game_stack_top']-stack_low,
                publications=publications,callbacks=callbacks.rows,stack_rows=timing.rows,field_rows=field_rows)
            for p in tutorial_scenes:
                bank=p['tutorial_fields'];live=p.get('publication_live_fields',{})
                assert bank['tutorial_generation']==bank['tutorial_presentation_generation']==live['tutorial_generation'],'Stale published tutorial generation'
                assert bank['tutorial_active_variant']==live['tutorial_active_variant'],'Stale published tutorial alternative'
                assert p['native_sprite_check']['matched'],'Actual native sprite mismatch'
                if bank.get('tutorial_marker_ready'):assert bank['tutorial_marker_generation']==bank['tutorial_generation']
                if bank.get('tutorial_animation_ready'):assert bank['tutorial_animation_generation']==bank['tutorial_generation']
            assert any(p['tutorial_fields'].get('tutorial_ball_mode') in (1,2) for p in tutorial_scenes)
            report.update(passed=True,target=dict(tx.meta['target'],video=standard),loaded_hunks=loaded,
                actions=actions,photos=photos,checkpoints=checkpoints,animation=animation_info,restores=restores,first_resumed_boundary=first_resume,
                reconciled_samples=logical_samples,ack=ack,memory=memory,stack_used_bytes=s['game_stack_top']-stack_low,
                publications=publications,callbacks=callbacks.rows,stack_rows=timing.rows,field_rows=field_rows,
                frozen_sha256={n:hashlib.sha256(v).hexdigest() for n,v in frozen.items()},
                scope=('Finite physical lower initial-serve prototype' if serve else 'Finite physical lower-receiver incoming prototype')+', edits, alternatives, modifier discrimination, menu and newly held F exact original resume. No retained navigation, branching, title tutorial completion, all reconciliation combinations, WCET or full acceptance.')
        tx.finalize(output,report,compiled=[json.loads((attempt/'baseline-rally.compile.json').read_text())],artifacts=list(attempt.iterdir()))
        shutil.copy2(output,attempt/'report.json');print(json.dumps(dict(passed=True,attempt=str(attempt),restores=len(restores),publications=len(publications))),flush=True)
    except BaseException as error:
        # Keep already observed controls/publications even if an early visual gate fails.
        for name in ('menu_stage_samples','stage_snapshots','stage_protocols','actions','photos','checkpoints','restores','first_resume','logical_samples','ack','field_rows'):
            if name in locals():report[name]=locals()[name]
        if 'callbacks' in locals():report.update(callbacks=callbacks.rows,publications=callbacks.surfaces.publications)
        if 'timing' in locals():report['stack_rows']=timing.rows
        atomic_json(attempt/'failure.json',dict(error=str(error),traceback=traceback.format_exc(),partial=report));tx.abort(error);raise

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--ntsc',action='store_true');parser.add_argument('--serve',action='store_true');args=parser.parse_args();run('NTSC' if args.ntsc else 'PAL',args.serve)
