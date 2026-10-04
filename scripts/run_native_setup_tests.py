"""Check UI callback deadlines and elapsed time without a setup exemption."""
import json,re,hashlib
from pathlib import Path
from native_tools import ROOT,emulator_config
from build_native_game import build
from native_observation import code_symbols,target_log
from native_setup_observation import SetupObserver
from native_metrics_observation import MetricsObserver
from native_evidence import atomic_json,tracked_call
from copperline_test_session import NativeControlSession


def run(baseline=None, control=None, fault_controls=None):
    if baseline is None: _,exe=build()
    else:
        exe=Path(baseline)
        if hashlib.sha256(exe.read_bytes()).hexdigest()!='c8dcaf04d63b593d4669ad72c47998c605e7de4360c66910d21048853f359548': raise ValueError('Unrecognized merged native baseline artifact')
    if control:
        from native_tools import ASSEMBLER, run as command
        source=(ROOT/'amiga/game/interface_render.s').read_text()
        delayed=source.replace('        clr.b   ui_dirty', '        clr.b   ui_dirty\n        move.w  #65535,d7\n.ui_overrun:\n        nop\n        dbra    d7,.ui_overrun')
        control_directory=ROOT/('build/tests/native-setup-'+control)
        control_directory.mkdir(parents=True,exist_ok=True)
        path=control_directory/'render.s'; path.write_text(delayed)
        main=(ROOT/'amiga/main.s').read_text()
        if control=='lost-wrap':
            main=main.replace('        add.l   d1,simulation_phase','        andi.l  #$ffff,d1\n        add.l   d1,simulation_phase')
        interface=(ROOT/'amiga/game/interface.s').read_text().replace('amiga/game/interface_render.s',str(path.relative_to(ROOT)))
        interface_path=control_directory/'interface.s'; interface_path.write_text(interface)
        main=main.replace('amiga/game/interface.s',str(interface_path.relative_to(ROOT)))
        main_path=control_directory/'main.s'; main_path.write_text(main)
        exe=control_directory/'ctennis-control'
        command([str(ASSEMBLER),'-Fhunkexe','-kick1hunks','-m68000','-L',str(exe.parent/'native.lst'),'-o',str(exe),str(main_path.relative_to(ROOT))])
    config=emulator_config();listing=(exe.parent/'native.lst').read_text();symbols=code_symbols(listing)
    directory=ROOT/('build/tests/native-setup-baseline' if baseline else 'build/tests/native-setup'+('-'+control if control else ''));callbacks=[];publications=[];checks=[];actions=[]
    with NativeControlSession(directory) as s:
        s.inspect('session_launch',{'binary':config['tools']['copperline'],'run':str(exe),'args':['--chipset','OCS','--video','PAL','--cpu','68000','--chip','512K','--slow','0','--fast','0','--noaudio',config['inputs']['amiga_rom']]})
        stop=s.inspect('run_until',{'seconds':30});assert stop['reason']=='loadseg',stop
        base=int(re.search(r'first hunk \$([0-9a-fA-F]+)',stop['detail'])[1],16); clock={'start':None,'origin':None,'started':0,'completed':0,'lifecycle':0,'ready_generation':0,'ready':None,'cop':bytearray(4)}
        observer=SetupObserver(base,symbols,listing)
        metrics=MetricsObserver(base,symbols,listing)
        accounting_pc=None if baseline else base+int(re.search(r'^00:([0-9A-Fa-f]{8})\s+[0-9A-Fa-f]+\s+\d+:\s*add.l\s+d1,simulation_phase',listing,re.M)[1],16)
        sample_pc=None if baseline else base+int(re.search(r'^00:([0-9A-Fa-f]{8})\s+[0-9A-Fa-f]+\s+\d+:\s*move.b\s+\$bfd400,d0',listing,re.M)[1],16)
        sample_position=None
        accounting={'phase':11838,'position':None,'samples':[],'bytes':bytearray(4),'seen':set(),'count':0,'maximum_error_cck':0,'maximum_elapsed_cck':0}
        def event(message):
            nonlocal sample_position
            metrics.observe(message)
            if message.get('method')!='event.mmio':return
            r=message['params'];a=r['addr'];v=r['value'];size=r['size'];p=r['position']
            if r.get('dropped_events',0) or r.get('dropped_notifications',0):raise AssertionError('Setup telemetry dropped')
            observer.observe(r)
            if a==0xbfd400 and r.get('access')=='read' and r['pc']==sample_pc:
                sample_position=p
            phase_address=base+symbols['simulation_phase']
            if phase_address<=a and a+size<=phase_address+4:
                offset=a-phase_address
                accounting['bytes'][offset:offset+size]=v.to_bytes(size,'big')
                accounting['seen'].update(range(offset,offset+size))
                if len(accounting['seen'])<4: return
                accounting['seen'].clear()
                v=int.from_bytes(accounting['bytes'],'big')
                if r['pc']==accounting_pc:
                    assert sample_position is not None,'Elapsed accounting lacks actual CIA sample'
                    previous=accounting['position'] if accounting['position'] is not None else clock['start']+(65535-clock['origin'])*5
                    elapsed=((v-accounting['phase'])&0xffffffff)*5
                    # An IRQ may delay the phase store after the timer sample.
                    # Compare the actual CIA read boundaries, keeping tolerance.
                    error=elapsed-(sample_position['cck']-previous)
                    accounting['count']+=1
                    accounting['maximum_error_cck']=max(accounting['maximum_error_cck'],abs(error))
                    accounting['maximum_elapsed_cck']=max(accounting['maximum_elapsed_cck'],elapsed)
                    if len(accounting['samples'])<8 or elapsed>327680: accounting['samples'].append({'cck':sample_position['cck'],'phase_store_cck':p['cck'],'sample_pc':sample_pc,'elapsed_cck':elapsed,'error_cck':error})
                    assert abs(error)<=(200 if accounting['position'] is None else 100),{'field':'elapsed accounting lost time','error_cck':error}
                    accounting['position']=sample_position['cck']
                accounting['phase']=v
            if a==(0xbfdf00 if baseline else 0xbfde00) and v&1 and clock['start'] is None:clock['start']=p['cck']
            if a==base+symbols['simulation_timer_origin']:clock['origin']=v
            if a==base+symbols['game_lifecycle']:clock['lifecycle']=v
            if a==base+symbols['simulation_started_updates']:
                assert v==clock['started']+1 and clock['completed']==clock['started'],'Setup callback sequence'
                clock['started']=v;callbacks.append({'callback':v,'entry':p})
            if a==base+symbols['ready_generation']:clock['ready_generation']=v
            if a==base+symbols['display_ready']:clock['ready']=clock['ready_generation'] if v else None
            if a==base+symbols['simulation_updates']:
                assert v==clock['completed']+1 and v==clock['started'],'Setup completion sequence'
                clock['completed']=v;callbacks[-1].update(completion=p,lifecycle=clock['lifecycle'])
            if 0xdff080<=a and a+size<=0xdff084:clock['cop'][a-0xdff080:a-0xdff080+size]=v.to_bytes(size,'big')
            if a==0xdff088 and clock['start'] is not None:
                publications.append({'position':p,'callback':clock['completed'],'pointer':int.from_bytes(clock['cop'],'big')})
                assert clock['ready'] is not None and clock['ready']<=clock['completed'],'Title publication of unfinished ready scene'
                assert p['vpos']<25 or p['vpos']>=252,'Title publication outside retained blank window'
        s.notification_handler=event
        watches=observer.watches()+[{'addr':base+symbols[n],'len':length,'access':'write'} for n,length in [('game_lifecycle',2),('simulation_timer_origin',2),('simulation_started_updates',2),('simulation_updates',2),('ready_generation',2),('display_ready',1),('simulation_phase',4)]]+[{'addr':0xbfdf00 if baseline else 0xbfde00,'len':1,'access':'write'},{'addr':0xdff080,'len':4,'access':'write'},{'addr':0xdff088,'len':2,'access':'write'}]
        watches+=metrics.watches()+[{'addr':0xbfd400,'len':1,'access':'read'}]
        s.inspect('events.subscribe',{'events':['mmio','frame'],'mmio':watches})
        time=stop['seconds']
        def advance(t):
            nonlocal time
            time+=t;s.inspect('run_until',{'seconds':time})
        def read(n):return int.from_bytes(bytes.fromhex(s.inspect('mem_read',{'addr':base+symbols[n],'len':1})['data']),'big')
        def check(label,actual,expected):
            checks.append({'label':label,'actual':actual,'expected':expected});assert actual==expected,checks[-1]
        from native_ui_raster import assert_ui_raster
        rasters=[]
        def raster(label):
            path=directory/(label+'.png')
            s.inspect('capture_screenshot',{'path':str(path)})
            rasters.append(assert_ui_raster(path,read('ui_page'),read('ui_player_count'),read('ui_selection'),(ROOT/'build/native/version.bin').read_bytes().rstrip(b'\0').decode('ascii'),read('ui_help_choice')))
        advance(.7);check('initial ordinary menu',read('ui_page'),0)
        if not control and not baseline: raster('initial')
        for label,key,page,selection in [('navigate-players',0x4d,0,1),('toggle-players',0x4e,0,1),('navigate-help',0x4d,0,2),('open-help',0x44,1,2),('open-scoring',0x44,2,2),('open-controls',0x44,3,2),('open-credits',0x44,4,2),('wrap-help',0x44,1,2),('select-exit',0x4f,1,2),('select-back',0x4f,1,2),('back-credits',0x44,4,2),('exit-page',0x45,0,2)]:
            before=len(observer.regions);s.inspect('input_key',{'rawkey':key,'action':'press'});advance(.5);s.inspect('input_key',{'rawkey':key,'action':'release'});advance(.5)
            check(label+' page',read('ui_page'),page);check(label+' selection',read('ui_selection'),selection)
            actions.append({'action':label,'regions':list(range(before,len(observer.regions)))})
            check(label+' explicit construction observed',len(observer.regions)>before,True)
            if not control and not baseline: raster(label)
        if not control and not baseline:
            for key,page in [(0x44,1),(0x44,2),(0x44,3),(0x44,4),(0x45,0)]:
                s.inspect('input_key',{'rawkey':key,'action':'press'});advance(.2)
                s.inspect('input_key',{'rawkey':key,'action':'release'});advance(.2)
                check('repeated navigation page',read('ui_page'),page)
            advance(15) # Continuous idle below the30-second attract threshold.
            def key(raw):
                s.inspect('input_key',{'rawkey':raw,'action':'press'});advance(.12)
                s.inspect('input_key',{'rawkey':raw,'action':'release'});advance(.12)
            def lifecycle():
                return int.from_bytes(bytes.fromhex(s.inspect('mem_read',{'addr':base+symbols['game_lifecycle'],'len':2})['data']),'big')
            key(0x01);advance(1.2);check('start after UI reaches active lifecycle',lifecycle(),1)
            key(0x24);advance(.3)
            check('fresh action advances flight after UI',bool(read('game_flight') and read('game_step')),True)
            key(0x19);check('pause after UI',read('ui_paused'),255)
            advance(.5)
            key(0x4d);key(0x44);check('return asks confirmation',read('ui_confirmation'),255)
            key(0x4e);key(0x44);check('return after UI reaches title',lifecycle(),2)
            advance(.3);raster('returned-title')
            key(0x01);advance(1.2);check('restart after UI reaches active lifecycle',lifecycle(),1)
            key(0x24);advance(.3)
            check('fresh action advances flight after UI',bool(read('game_flight') and read('game_step')),True)
        s.inspect('events.unsubscribe')
        missed_publications=int.from_bytes(bytes.fromhex(s.inspect('mem_read',{'addr':base+symbols['missed_presentation_deadlines'],'len':2})['data']),'big')
    target_log(directory)
    # At the end a callback may be pending; retain and label it, never promote it.
    pending=callbacks.pop() if callbacks and 'completion' not in callbacks[-1] else None
    origin=clock['start']+(65535-clock['origin'])*5
    diagnostic=observer.proposal(callbacks,origin)
    report={'missed_publications':missed_publications,'resource_metrics':metrics.result(observer.regions),'passed':True,'subject':'maintained-native','rasters':rasters,'elapsed_accounting_count':accounting['count'],'maximum_accounting_error_cck':accounting['maximum_error_cck'],'maximum_accounted_elapsed_cck':accounting['maximum_elapsed_cck'],'compiled_fault_controls':fault_controls or [],'elapsed_accounting_samples':accounting['samples'],'checked_callbacks':len(callbacks),'pending_final_callback':pending,'checks':checks,'actions':actions,'publications':publications,'phase_contract_proposal':diagnostic,'raw_all_callback_deadline_passed':not diagnostic['raw_deadline_failures'],'scope':'Uninterrupted strict UI cadence/elapsed accounting, repeated navigation/idle and representative scanout; historical proposal retained diagnostically with no exemption','executable_sha256':hashlib.sha256(exe.read_bytes()).hexdigest()}
    if not control and not baseline: assert report['raw_all_callback_deadline_passed'],diagnostic['raw_deadline_failures']
    atomic_json(directory/'report.json',report);atomic_json(directory/'measurement.json',{'callbacks':callbacks,'origin_cck':origin,'regions':observer.regions,'publications':publications})
    print(json.dumps({'measurements_passed':True,'phase_proposal_diagnostic_passed':diagnostic['diagnostic_passed'],'setup_cases':[{k:r[k] for k in ('kind','work_cck','bound_cck','catchup_callbacks')} for r in diagnostic['setup_cases']],'strict_failures':diagnostic['strict_nonsetup_failures'],'issues':diagnostic['issues']}),flush=True)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--self-test',action='store_true');parser.add_argument('--baseline',help='Exact previously frozen merged native executable, diagnostic only')
    args=parser.parse_args()
    if args.baseline:
        run(args.baseline); raise SystemExit(0)
    controls=[]
    if args.self_test:
        try: run(control='lost-wrap')
        except AssertionError as error:
            if error.args[0].get('field')!='elapsed accounting lost time' or abs(error.args[0].get('error_cck',0)+327680)>100: raise
            lost_failure=error.args[0]
            print('PASS lost-wrap accounting control rejected',str(error),flush=True)
        else: raise AssertionError('Lost-wrap control escaped')
        run(control='ui-overrun')
        fault=json.loads((ROOT/'build/tests/native-setup-ui-overrun/report.json').read_text())
        assert not fault['raw_all_callback_deadline_passed'],'UI overrun control escaped strict deadlines'
        assert any(row['elapsed_cck']>327680 for row in fault['elapsed_accounting_samples']),'Wrap control did not span one whole wrap'
        controls=[{'name':name,'artifact_directory':'build/tests/native-setup-'+name,
                   'executable_sha256':hashlib.sha256((ROOT/('build/tests/native-setup-'+name)/'ctennis-control').read_bytes()).hexdigest(),
                   'detected_failure':lost_failure if name=='lost-wrap' else {'field':'raw callback deadline','failures':len(fault['phase_contract_proposal']['raw_deadline_failures'])}}
                  for name in ('lost-wrap','ui-overrun')]
        print('PASS UI overrun rejected; whole wrap accounted without observer reset',flush=True)
    path=ROOT/'build/tests/native-setup/report.json'
    tracked_call([path],'native-setup','maintained-native','ordinary title','scripts/run_native_setup_tests.py',None,lambda:run(fault_controls=controls),lambda p,r:[ROOT/'build/amiga/interfaces/enhanced/baseline-rally'])
