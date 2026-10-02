"""Bounded ordinary title/menu/help measurements; phase contract remains a proposal."""
import json,re,hashlib
from pathlib import Path
from native_tools import ROOT,emulator_config
from build_native_game import build
from native_observation import code_symbols,target_log
from native_setup_observation import SetupObserver
from native_evidence import atomic_json,tracked_call
from copperline_test_session import NativeControlSession


def run(baseline=None):
    if baseline is None: _,exe=build()
    else:
        exe=Path(baseline)
        if hashlib.sha256(exe.read_bytes()).hexdigest()!='c8dcaf04d63b593d4669ad72c47998c605e7de4360c66910d21048853f359548': raise ValueError('Unrecognized merged native baseline artifact')
    config=emulator_config();listing=(exe.parent/'native.lst').read_text();symbols=code_symbols(listing)
    directory=ROOT/('build/tests/native-setup-baseline' if baseline else 'build/tests/native-setup');callbacks=[];publications=[];checks=[];actions=[]
    with NativeControlSession(directory) as s:
        s.inspect('session_launch',{'binary':config['tools']['copperline'],'run':str(exe),'args':['--chipset','OCS','--video','PAL','--cpu','68000','--chip','512K','--slow','0','--fast','0','--noaudio',config['inputs']['amiga_rom']]})
        stop=s.inspect('run_until',{'seconds':30});assert stop['reason']=='loadseg',stop
        base=int(re.search(r'first hunk \$([0-9a-fA-F]+)',stop['detail'])[1],16); clock={'start':None,'origin':None,'started':0,'completed':0,'lifecycle':0,'cop':bytearray(4)}
        observer=SetupObserver(base,symbols,listing)
        def event(message):
            if message.get('method')!='event.mmio':return
            r=message['params'];a=r['addr'];v=r['value'];size=r['size'];p=r['position']
            if r.get('dropped_events',0) or r.get('dropped_notifications',0):raise AssertionError('Setup telemetry dropped')
            observer.observe(r)
            if a==0xbfdf00 and v&1 and clock['start'] is None:clock['start']=p['cck']
            if a==base+symbols['simulation_timer_origin']:clock['origin']=v
            if a==base+symbols['game_lifecycle']:clock['lifecycle']=v
            if a==base+symbols['simulation_started_updates']:
                assert v==clock['started']+1 and clock['completed']==clock['started'],'Setup callback sequence'
                clock['started']=v;callbacks.append({'callback':v,'entry':p})
            if a==base+symbols['simulation_updates']:
                assert v==clock['completed']+1 and v==clock['started'],'Setup completion sequence'
                clock['completed']=v;callbacks[-1].update(completion=p,lifecycle=clock['lifecycle'])
            if 0xdff080<=a and a+size<=0xdff084:clock['cop'][a-0xdff080:a-0xdff080+size]=v.to_bytes(size,'big')
            if a==0xdff088 and clock['start'] is not None:
                publications.append({'position':p,'callback':clock['completed'],'pointer':int.from_bytes(clock['cop'],'big')})
                assert clock['completed']==clock['started'],'Title publication of unfinished update'
                assert p['vpos']<25 or p['vpos']>=252,'Title publication outside retained blank window'
        s.notification_handler=event
        watches=observer.watches()+[{'addr':base+symbols[n],'len':length,'access':'write'} for n,length in [('game_lifecycle',2),('simulation_timer_origin',2),('simulation_started_updates',2),('simulation_updates',2),('display_ready',1)]]+[{'addr':0xbfdf00,'len':1,'access':'write'},{'addr':0xdff080,'len':4,'access':'write'},{'addr':0xdff088,'len':2,'access':'write'}]
        s.inspect('events.subscribe',{'events':['mmio'],'mmio':watches})
        time=stop['seconds']
        def advance(t):
            nonlocal time
            time+=t;s.inspect('run_until',{'seconds':time})
        def read(n):return int.from_bytes(bytes.fromhex(s.inspect('mem_read',{'addr':base+symbols[n],'len':1})['data']),'big')
        def check(label,actual,expected):
            checks.append({'label':label,'actual':actual,'expected':expected});assert actual==expected,checks[-1]
        advance(.7);check('initial ordinary menu',read('ui_page'),0)
        for label,key,page,selection in [('navigate-players',0x4d,0,1),('toggle-players',0x4e,0,1),('navigate-help',0x4d,0,2),('open-help',0x44,1,2),('open-controls',0x4e,2,2),('open-credits',0x4e,3,2),('wrap-help',0x4e,1,2),('back-credits',0x4f,3,2),('exit-page',0x45,0,2)]:
            before=len(observer.regions);s.inspect('input_key',{'rawkey':key,'action':'press'});advance(.5);s.inspect('input_key',{'rawkey':key,'action':'release'});advance(.5)
            check(label+' page',read('ui_page'),page);check(label+' selection',read('ui_selection'),selection)
            actions.append({'action':label,'regions':list(range(before,len(observer.regions)))})
            check(label+' explicit construction observed',len(observer.regions)>before,True)
        s.inspect('events.unsubscribe')
    target_log(directory)
    # At the end a callback may be pending; retain and label it, never promote it.
    pending=callbacks.pop() if callbacks and 'completion' not in callbacks[-1] else None
    origin=clock['start']+(65535-clock['origin'])*5
    diagnostic=observer.proposal(callbacks,origin)
    report={'passed':True,'subject':'maintained-native','checked_callbacks':len(callbacks),'pending_final_callback':pending,'checks':checks,'actions':actions,'publications':publications,'phase_contract_proposal':diagnostic,'raw_all_callback_deadline_passed':not diagnostic['raw_deadline_failures'],'scope':'Bounded setup measurement/logic/publication only; proposal does not adopt or waive raw cadence failures','executable_sha256':hashlib.sha256(exe.read_bytes()).hexdigest()}
    atomic_json(directory/'report.json',report);atomic_json(directory/'measurement.json',{'callbacks':callbacks,'origin_cck':origin,'regions':observer.regions,'publications':publications})
    print(json.dumps({'measurements_passed':True,'phase_proposal_diagnostic_passed':diagnostic['diagnostic_passed'],'setup_cases':[{k:r[k] for k in ('kind','work_cck','bound_cck','catchup_callbacks')} for r in diagnostic['setup_cases']],'strict_failures':diagnostic['strict_nonsetup_failures'],'issues':diagnostic['issues']}),flush=True)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--baseline',help='Exact previously frozen merged native executable, diagnostic only')
    args=parser.parse_args()
    if args.baseline:
        run(args.baseline); raise SystemExit(0)
    path=ROOT/'build/tests/native-setup/report.json'
    tracked_call([path],'native-setup','maintained-native','ordinary title','scripts/run_native_setup_tests.py',None,run,lambda p,r:[ROOT/'build/amiga/interfaces/enhanced/ctennis-enhanced'])
