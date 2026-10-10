"""Finite physical-state matched input scan diagnostic; no release acceptance."""
import argparse,json,re,hashlib,uuid,traceback
from pathlib import Path
from native_tools import ROOT,emulator_config
from native_evidence import ReportRun,snapshot,atomic_json,digest,inputs_for
from build_match_core import load_image
from native_hunk import loaded_hunks
from tutorial_capture import CaptureSession,CallbackObserver
from coherent_publication import CoherentSurfaceObserver,qualified_endpoint
from run_tutorial_capture import FIELDS
from tutorial_latency import instruction_map,StackTiming,LatencyObserver
from matched_planner_capture import require_anchor,read,PROVIDER_CLOCK,CLOCKS


def run(standard):
    directory=ROOT/'build/tests'/f'ui-scan-matched-{standard.lower()}'
    directory.mkdir(exist_ok=True);attempt=directory/uuid.uuid4().hex;attempt.mkdir()
    report_path=directory/'report.json';transaction=ReportRun([report_path],'native-feedback','maintained-native','Physical tutorial incoming and restored settled native anchor')
    paths,tools=inputs_for('native-feedback','scripts/run_ui_sample_matched.py');transaction.meta.update(files=snapshot(paths),tools=tools)
    report={'passed':False,'attempt':str(attempt),'scope':'One restored settled anchor, fixed fresh-D window; diagnostic only. No resume/deadline/full-release acceptance.'}
    try:
        product=ROOT/'build/amiga/interfaces/enhanced';exe=product/'baseline-rally';listing=(product/'native.lst').read_text()
        reference=ROOT/'build/tests/ui-scan-padded-reference-final';audit=json.loads((reference/'audit.json').read_text())
        report['executable_sha256']=digest(exe)
        transaction.meta.update(actual_target=dict(transaction.meta['target'],video=standard),commit=__import__('subprocess').check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),environment={'RUST_LOG':__import__('os').environ.get('RUST_LOG'),'PYTHONPATH':__import__('os').environ.get('PYTHONPATH')})
        assert digest(exe)==audit['candidate_sha256']
        with CaptureSession(attempt) as session:
            config=emulator_config();session.inspect('session_launch',dict(binary=config['tools']['copperline'],run=str(exe),args=['--chipset','OCS','--video',standard,'--cpu','68000','--chip','512K','--slow','0','--fast','0','--noaudio',config['inputs']['amiga_rom']]))
            stop=session.inspect('run_until',dict(seconds=30));assert stop['reason']=='loadseg'
            segments=session.inspect('segments.list')['current'];addresses=[h['start'] for h in segments]
            images,symbols=load_image(exe,hunk_addresses=addresses);original,rs=load_image(reference/'baseline-rally',hunk_addresses=addresses)
            loaded=loaded_hunks(exe,segments,lambda a,n:read(session,a,n))
            def number(name,width=2):return int.from_bytes(read(session,symbols[name],width),'big')
            def advance(delta):
                goal=session.inspect('status')['cck']+int(delta*CLOCKS[standard])
                for _ in range(20000):
                    stop=session.inspect('run_until',dict(seconds=goal/PROVIDER_CLOCK))
                    if stop['cck']>=goal or stop.get('reason')=='target':return stop
                raise AssertionError('Setup bounded stop cap')
            def key(code,held,delta=.06):session.inspect('input.key',dict(rawkey=code,action='press' if held else 'release'));advance(delta)
            advance(.5)
            key(1,True);key(1,False)
            for _ in range(100):
                if number('game_lifecycle')==1:break
                advance(.05)
            else:raise AssertionError('Physical selection not playing')
            key(0x23,True,.04);key(0x23,False,.02)
            for _ in range(200):
                if number('game_contact',1)&0x40 and number('game_flight',1)&0x40 and not number('game_contact',1)&0x8d:break
                advance(.02)
            else:raise AssertionError('No physical incoming flight')
            key(0x24,True,.02);key(0x24,False,.02);key(0x24,True,.02);key(0x24,False,.02)
            assert number('tutorial_active',1)
            key(0x23,True)
            # Setup may wait for all owners; measured window never ends adaptively.
            advance(2)
            if not number('game_preview_launches',1):
                count=number('game_preview_counts');path=read(session,symbols['game_preview_paths'],count*8)
                assert count,'No actual incoming samples for physical alignment'
                sample=min((path[i:i+8] for i in range(0,len(path),8)),key=lambda p:abs(p[1]-(number('tutorial_y')+27)))
                target_x=max(40,min(199,sample[0]-8));direction=0x20 if target_x<number('tutorial_x') else 0x22
                session.inspect('input.key',dict(rawkey=direction,action='press'))
                for _ in range(400):
                    x=number('tutorial_x')
                    if (direction==0x20 and x<=target_x) or (direction==0x22 and x>=target_x):break
                    advance(.01)
                else:raise AssertionError('Physical alignment cap')
                session.inspect('input.key',dict(rawkey=direction,action='release'));advance(2)
            assert number('game_preview_launches',1),'Aligned anchor has no actual held contact launch'
            assert number('game_preview_endpoint_ready',1),'Aligned anchor has no completed held endpoint'
            session.inspect('break.add',dict(kind='pc',addr=symbols['main_loop']))
            anchor=None
            for _ in range(20000):
                advance(.001)
                try:anchor=require_anchor(session,symbols);break
                except AssertionError:pass
            assert anchor is not None,'No settled main_loop anchor'
            session.inspect('break.clear');session.inspect('state.save',dict(path=str(attempt/'anchor.state')))
            region=anchor['cck'];press=region+int(.02*CLOCKS[standard]);release=press+int(.02*CLOCKS[standard]);end=region+int(1.2*CLOCKS[standard])
            # Relocated patch audit repeats at real LoadSeg addresses.
            ranges=[(symbols['ui_sample'],symbols['ui_latch_live_controls'])]
            differences=[a+j for (a,c),(b,r) in zip(images,original) for j,(x,y) in enumerate(zip(c,r)) if x!=y and not ranges[0][0]<=a+j<ranges[0][1]]
            assert len(differences)==1 and symbols['ui_resume']<=differences[0]<symbols['ui_return_title'];ranges.append((differences[0]&~1,(differences[0]&~1)+2))
            anchor_generation=number('tutorial_generation',4)
            assert [(a,len(b)) for a,b in images]==[(a,len(b)) for a,b in original]
            for (a,c),(b,r) in zip(images,original):
                assert all(x==y or any(lo<=a+i<hi for lo,hi in ranges) for i,(x,y) in enumerate(zip(c,r)))
            results=[]
            for label,treatment in (('baseline-1',False),('baseline-2',False),('candidate',True)):
                session.observer=None;session.inspect('events.unsubscribe');session.inspect('break.clear');session.inspect('state.load',dict(path=str(attempt/'anchor.state')))
                assert require_anchor(session,symbols)==anchor
                before=read(session,0,524288);regs=session.inspect('regs.get')
                if not treatment:
                    for lo,hi in ranges:
                        a,data=next((a,b) for a,b in original if a<=lo and hi<=a+len(b));session.inspect('mem.write',dict(addr=lo,data=data[lo-a:hi-a].hex(),encoding='hex'))
                after=read(session,0,524288)
                for lo,hi in ranges:
                    a,data=next((a,b) for a,b in (images if treatment else original) if a<=lo and hi<=a+len(b))
                    assert after[lo:hi]==data[lo-a:hi-a]
                assert session.inspect('regs.get')==regs
                assert all(x==y or any(lo<=i<hi for lo,hi in ranges) for i,(x,y) in enumerate(zip(before,after)))
                callbacks=CallbackObserver(0,symbols);callbacks.surfaces=CoherentSurfaceObserver(symbols,lambda a,n:read(session,a,n),last_line=311 if standard=='PAL' else 261,verify_sprites=True)
                pass_listing=listing if treatment else (reference/'native.lst').read_text()
                calls,returns=instruction_map(pass_listing,segments,lambda a,n:read(session,a,n))
                timing=StackTiming(calls,returns,symbols['game_stack_bottom'],symbols['game_stack_top'])
                detector=LatencyObserver(callbacks,timing)
                class Observe:
                    def __init__(self):self.events=[];self.ack=[]
                    def observe(self,message):
                        row=message.get('params',{});event={k:row[k] for k in ('position','addr','size','value','pc','access') if k in row}
                        if 'retired_instructions' in event.get('position',{}):event['position']=dict(event['position'],retired_instructions=event['position']['retired_instructions']-instruction_origin)
                        self.events.append(event)
                        if row.get('addr')==symbols['keyboard_ack']:self.ack.append(row)
                        detector.observe(message)
                instruction_origin=session.inspect('status')['retired_instructions']
                observer=Observe();session.observer=observer
                watches=callbacks.watches(dict(FIELDS,keyboard_ack=1,keyboard_ack_timer=2),lambda a,n:read(session,a,n))+callbacks.surfaces.watches()+[dict(addr=symbols['game_stack_bottom'],len=symbols['game_stack_top']-symbols['game_stack_bottom'],access='read')]
                callbacks.started=number('simulation_started_updates');callbacks.completed=number('simulation_updates')
                assert callbacks.started==callbacks.completed
                subscription=session.inspect('events.subscribe',dict(events=['mmio','frame'],mmio=watches));assert subscription.get('dropped_notifications',0)==0
                for cck,action in ((press,'press'),(release,'release')):session.inspect('input.key',dict(rawkey=0x22,action=action,at_seconds=cck/PROVIDER_CLOCK))
                current=region
                for _ in range(2000):
                    target=min(end,current+max(1,CLOCKS[standard]//1000));stop=session.inspect('run_until',dict(seconds=target/PROVIDER_CLOCK));current=stop['cck']
                    if current>=end or (stop.get('reason')=='target' and target==end):break
                else:raise AssertionError('Measured fixed-window cap')
                measured_stop=dict(stop)
                if 'retired_instructions' in measured_stop:measured_stop['retired_instructions']-=instruction_origin
                session.inspect('break.add',dict(kind='pc',addr=symbols['main_loop']))
                tail=session.inspect('run_until',dict(seconds=(end+int(.03*CLOCKS[standard]))/PROVIDER_CLOCK))
                assert session.inspect('regs.get')['pc']==symbols['main_loop'] and not timing.stack and callbacks.pending is None,'Tail failed to close complete owners/callback'
                assert tail['cck']<=end+int(.03*CLOCKS[standard])
                gen=number('tutorial_generation',4);assert gen!=anchor_generation,'Fresh D did not produce a new generation'
                assert number('keyboard_ack',1)==0 and read(session,symbols['game_keyboard_matrix']+0x22,1)==b'\0','Release/ACK not retired'
                assert observer.ack and any(row['value'] for row in observer.ack),'No measured physical keyboard ACK'
                scenes=[p for p in callbacks.surfaces.publications if qualified_endpoint(p,gen,press) and p['position']['cck']<=end]
                assert scenes,'No qualified actual endpoint in fixed window'
                assert scenes[0].get('endpoint_outcomes',0)>>16 and scenes[0].get('endpoint_points')!='00000000000000000000000000000000','Measured result is fallback rather than held endpoint'
                assert number('game_preview_launches',1),'Measured edit has no actual held contact'
                frozen={n:read(session,symbols[n],symbols[e]-symbols[n]).hex() for n,e in (('game_core_state','game_core_state_end'),('game_history_state','game_history_state_end'),('game_history_buffer','game_history_buffer_end'))}
                assert list(frozen.values())==[anchor['regions'][n] for n in ('canonical','history','records')]
                item=dict(label=label,final_regs=session.inspect('regs.get'),final_owner_snapshot={n:read(session,symbols[n],symbols[e]-symbols[n]).hex() for n,e in (('tutorial_state','tutorial_state_end'),('game_preview_storage','game_preview_storage_end'),('game_history_seek_storage','game_history_seek_storage_end'))},presentation_requests=callbacks.presentation_requests,final_ui=read(session,symbols['ui_state'],symbols['ui_help_choice']+2-symbols['ui_state']).hex(),events_sha256=hashlib.sha256(json.dumps(observer.events,sort_keys=True).encode()).hexdigest(),input_ack=observer.ack,measured_stop=measured_stop,fixed_end_cck=end,tail_end_cck=tail['cck'],stack_rows=timing.rows,latency_cck=scenes[0]['position']['cck']-press,latency_ms=(scenes[0]['position']['cck']-press)*1000/CLOCKS[standard],generation=gen,callbacks=callbacks.rows,publications=callbacks.surfaces.publications,frozen=frozen,endpoint_points=scenes[0].get('endpoint_points'),endpoint_outcomes=scenes[0].get('endpoint_outcomes'),memory_patch_ranges=ranges,restored_memory_sha256=hashlib.sha256(before).hexdigest())
                results.append(item);atomic_json(attempt/(label+'.json'),item)
                if label=='baseline-2':assert {k:v for k,v in results[0].items() if k!='label'}=={k:v for k,v in item.items() if k!='label'},'Baseline replay differs; treatment forbidden'
            requests=lambda p:[(r['generation']-anchor_generation,r['x'],r['y'],r['variant']) for r in p['presentation_requests']]
            assert requests(results[0])==requests(results[2]) and requests(results[0]),'Physical request sequence differs'
            report['accepted_requests']=requests(results[0])
            assert results[0]['endpoint_points']==results[2]['endpoint_points'] and results[0]['endpoint_outcomes']==results[2]['endpoint_outcomes'],'Causal endpoint differs'
            report.update(passed=True,standard=standard,target=dict(transaction.meta['target'],video=standard),anchor=anchor,passes=results,baseline_replay_equal=True,loaded_hunks=loaded)
        transaction.finalize(report_path,report,compiled=[json.loads((product/'baseline-rally.compile.json').read_text())],artifacts=list(attempt.iterdir())+[reference/'baseline-rally',reference/'native.lst',reference/'audit.json'])
    except BaseException as error:
        atomic_json(attempt/'failure.json',dict(error=str(error),traceback=traceback.format_exc(),partial=report));transaction.abort(error);raise
    print(json.dumps(dict(passed=report['passed'],attempt=str(attempt),timings=[p['latency_ms'] for p in report['passes']])))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--ntsc',action='store_true');args=p.parse_args();run('NTSC' if args.ntsc else 'PAL')
