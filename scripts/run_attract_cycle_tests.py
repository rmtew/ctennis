"""Two unattended native attract cycles: actual bank publications and title pixels."""
import argparse,hashlib,json,re
from build_native_game import build
from copperline_test_session import NativeControlSession
from native_tools import ROOT,emulator_config
from native_observation import code_symbols,target_log
from native_evidence import atomic_json,tracked_call
from native_identity_raster import assert_title_raster,assert_menu_selection_raster


def run():
    _,exe=build();config=emulator_config();listing=(exe.parent/'native.lst').read_text();symbols=code_symbols(listing)
    directory=ROOT/'build/tests/attract-two-cycles';checks=[];windows=[];entries=[];publications=[];captures=[]
    def check(label,actual,expected):
        checks.append(dict(label=label,actual=actual,expected=expected));assert actual==expected,checks[-1]
    with NativeControlSession(directory) as s:
        s.inspect('session_launch',dict(binary=config['tools']['copperline'],run=str(exe),args=['--chipset','OCS','--video','PAL','--cpu','68000','--chip','512K','--slow','0','--fast','0','--noaudio',config['inputs']['amiga_rom']]))
        stop=s.inspect('run_until',{'seconds':30});assert stop['reason']=='loadseg',stop
        base=int(re.search(r'first hunk \$([0-9a-fA-F]+)',stop['detail'])[1],16)
        segments=s.inspect('segments.list')['current'];located={n:(int(h),int(o,16)) for n,h,o in re.findall(r'^([A-Za-z_][\w]*)\s+(\d\d):([0-9A-Fa-f]{8})\s*$',listing,re.M)}
        def address(n):
            h,offset=located[n];return segments[h]['start']+offset
        title=address('title_copper');courts={address(n) for n in ('copperlist','copperlist_back')}
        # Observe the complete menu/hint area, rather than startup's bulk
        # branding initialization, which can exceed CCP's4096-event queue.
        # Branding pixels are independently checked in all eight scanouts.
        planes=[(address(f'title_plane{i}')+144*32,48*32) for i in range(4)]
        state=dict(life=0,demo=0,dirty=0,idle=0,started=0,completed=0,award=None,first=None,loops=0,pointer=bytearray(4))
        fields={base+symbols[n]:n for n in ('game_lifecycle','ui_demo','ui_dirty','ui_idle','simulation_started_updates','simulation_updates','game_celebration_first_play','game_celebration_loops','display_ready')}
        def event(message):
            if message.get('method')!='event.mmio':return
            r=message['params'];a=r['addr'];v=r['value'];size=r['size'];p=r['position'];n=fields.get(a)
            assert not r.get('dropped_events',0) and not r.get('dropped_notifications',0),{'label':'Attract telemetry dropped','position':p,'dropped_events':r.get('dropped_events',0),'dropped_notifications':r.get('dropped_notifications',0)}
            if n=='simulation_started_updates':state['started']=v
            elif n=='simulation_updates':
                state['completed']=v
                if windows and windows[-1]['next_entry'] is None:
                    offset=v-windows[-1]['returned']['callback']
                    if offset in (4,600,1200,1790):
                        path=directory/f'cycle-{len(windows)}-title-{offset}.png';captures.append(path)
                        s.send_async('capture.screenshot',{'path':str(path)})
            elif n=='ui_dirty':state['dirty']=v
            elif n=='ui_idle':state['idle']=v
            elif n=='game_celebration_loops':state['loops']=v
            elif n=='game_celebration_first_play' and v:state['first']=dict(callback=state['started'],position=p)
            elif n=='ui_demo':
                state['demo']=v
                if v:
                    entry=dict(callback=state['started'],position=p,idle=state['idle']);entries.append(entry)
                    check('automatic attract enters after full title idle',state['idle'],1800)
                    if windows:windows[-1]['next_entry']=entry
            elif n=='game_lifecycle':
                state['life']=v
                assert v not in (7,8),'Attract reached superseded intermediate title/court lifecycle'
                if v==6:state.update(award=dict(callback=state['completed'],position=p),first=None,loops=0)
                elif v==2 and state['award'] is not None:
                    check('automatic return follows actual first-play completion',state['first'] is not None,True)
                    check('exact full native phrase before unattended return',state['first']['callback']-state['award']['callback'],926)
                    check('one completed phrase before unattended return',state['loops'],1)
                    windows.append(dict(award=state['award'],first_play=state['first'],returned=dict(callback=state['completed'],position=p),next_entry=None,publications=0,stable=False,unexpected_title_writes=0))
                    state['award']=None
            elif n=='display_ready' and v and windows and windows[-1]['next_entry'] is None and state['life']==2 and not state['dirty']:
                windows[-1]['stable']=True
            if any(start<=a<a+size<=start+length for start,length in planes):
                if windows and windows[-1]['next_entry'] is None and windows[-1]['stable']:
                    windows[-1]['unexpected_title_writes']+=1
                    raise AssertionError('Quiet menu bitmap changed after completed menu construction')
            if 0xdff080<=a and a+size<=0xdff084:state['pointer'][a-0xdff080:a-0xdff080+size]=v.to_bytes(size,'big')
            if a==0xdff088:
                pointer=int.from_bytes(state['pointer'],'big')
                check('publication has a complete native callback',state['started'],state['completed'])
                if state['started']:assert p['vpos']<25 or p['vpos']>=252,{'label':'retained sprite/header blank window','position':p}
                assert pointer==title or pointer in courts,'Unknown published Copper bank'
                if windows and windows[-1]['next_entry'] is None:
                    check('every returned-title publication selects actual title bank',pointer,title)
                    windows[-1]['publications']+=1
                publications.append(dict(pointer=pointer,position=p,lifecycle=state['life'],demo=state['demo']))
        s.notification_handler=event
        watches=[{'addr':a,'len':1 if n in ('ui_demo','ui_dirty','game_celebration_first_play','display_ready') else 2,'access':'write'} for a,n in fields.items()]
        watches += [{'addr':a,'len':length,'access':'write'} for a,length in planes]
        watches += [{'addr':0xdff080,'len':4,'access':'write'},{'addr':0xdff088,'len':2,'access':'write'}]
        s.inspect('events.subscribe',{'events':['mmio'],'mmio':watches})
        # No injected state, keyboard/pad actions, seeded fixture or callback stops.
        s.inspect('run_until',{'seconds':stop['seconds']+570});s.inspect('events.unsubscribe');s.notification_handler=None
        check('two unattended result-to-title cycles',len(windows),2)
        check('third attract starts after second idle',len(entries),3)
        for cycle,window in enumerate(windows,1):
            check('title construction completed',window['stable'],True)
            check('title actual bank publications observed',window['publications']>0,True)
            check('no hidden quiet menu bitmap mutation',window['unexpected_title_writes'],0)
            elapsed=window['next_entry']['position']['seconds']-window['returned']['position']['seconds']
            check('retained bounded 30-second title idle',29.9<elapsed<30.2,True)
            for offset in (4,600,1200,1790):
                path=directory/f'cycle-{cycle}-title-{offset}.png'
                assert_title_raster(path);assert_menu_selection_raster(path,0,1)
    target_log(directory)
    report=dict(passed=True,checks=checks,windows=windows,entries=entries,publications=publications,captures=[str(p.relative_to(ROOT)) for p in captures],
                executable_sha256=hashlib.sha256(exe.read_bytes()).hexdigest(),scope='Two uninterrupted ordinary unattended cycles through selected tune, actual title COP1LC/blank publications, immutable idle menu bitmap and eight authored-font scanouts; no physical inputs/state writes or hardware parity claim')
    atomic_json(directory/'report.json',report);print(json.dumps(dict(passed=True,cycles=len(windows),entries=len(entries),publications=len(publications),title_frames=len(captures))))


if __name__=='__main__':
    tracked_call([ROOT/'build/tests/attract-two-cycles/report.json'],'native-demo','maintained-native','ordinary title','scripts/run_attract_cycle_tests.py',None,run,
                 lambda p,r:[ROOT/'build/amiga/interfaces/enhanced/baseline-rally'])
