"""Two unattended native attract cycles: actual bank publications and title pixels."""
import argparse,hashlib,json,re
from PIL import Image
from build_native_game import build
from copperline_test_session import NativeControlSession
from native_tools import ROOT,emulator_config
from native_observation import code_symbols,target_log
from native_evidence import atomic_json,tracked_call
from native_identity_raster import assert_title_raster,assert_menu_selection_raster


def run():
    _,exe=build();config=emulator_config();listing=(exe.parent/'native.lst').read_text();symbols=code_symbols(listing)
    directory=ROOT/'build/tests/attract-two-cycles';checks=[];windows=[];entries=[];publications=[];captures=[];quiet_requests={}
    def check(label,actual,expected):
        checks.append(dict(label=label,actual=actual,expected=expected));assert actual==expected,checks[-1]
    with NativeControlSession(directory) as s:
        s.inspect('session_launch',dict(binary=config['tools']['copperline'],run=str(exe),args=['--chipset','OCS','--video','PAL','--cpu','68000','--chip','512K','--slow','0','--fast','0','--noaudio',config['inputs']['amiga_rom']]))
        stop=s.inspect('run_until',{'seconds':30});assert stop['reason']=='loadseg',stop
        base=int(re.search(r'first hunk \$([0-9a-fA-F]+)',stop['detail'])[1],16)
        segments=s.inspect('segments.list')['current'];located={n:(int(h),int(o,16)) for n,h,o in re.findall(r'^([A-Za-z_][\w]*)\s+(\d\d):([0-9A-Fa-f]{8})\s*$',listing,re.M)}
        def address(n):
            h,offset=located[n];return segments[h]['start']+offset
        title=address('title_copper');courts={address(n) for n in ('copperlist','copperlist_back','copperlist_third')}
        # Let ordinary startup finish without a callback stop, then watch
        # every title bitmap/control byte through both result/idle windows.
        # This avoids startup's bulk branding writes filling the4096 queue.
        s.inspect('run_until',{'seconds':stop['seconds']+1})
        initial=directory/'initial-title.png'
        s.inspect('capture.screenshot',{'path':str(initial)})
        assert_title_raster(initial);assert_menu_selection_raster(initial,0,1)
        with Image.open(initial) as image:
            assert image.size==(716,285)
            expected_digest=0xcbf29ce484222325
            for byte in image.convert('RGBA').tobytes():
                expected_digest=((expected_digest^byte)*0x100000001b3)&0xffffffffffffffff
        expected_digest=f'{expected_digest:016x}'
        planes=[(address(f'title_plane{i}'),192*32) for i in range(4)]
        controls=[(title,address('title_plane0')-title)]
        state=dict(life=0,demo=0,dirty=0,idle=0,started=0,completed=0,award=None,first=None,loops=0,ready_generation=0,ready=None,pointer=bytearray(4))
        fields={base+symbols[n]:n for n in ('game_lifecycle','ui_demo','ui_dirty','ui_idle','simulation_started_updates','simulation_updates','game_celebration_first_play','game_celebration_loops','ready_generation','display_ready')}
        def event(message):
            if message.get('id') in quiet_requests:
                window=quiet_requests.pop(message['id'])
                assert 'error' not in message,{'label':'quiet bitmap subscription rejected','reply':message}
                result=message['result']
                check('quiet bitmap subscription includes all requested watches',result['mmio'],quiet_watches)
                check('quiet bitmap subscription active', 'mmio' in result['active'],True)
                check('quiet bitmap subscription has zero dropped notifications',result['dropped_notifications'],0)
                window['quiet_subscription_ack']=dict(request_id=message['id'],result=result)
                return
            if message.get('method')=='event.frame':
                r=message['params']
                assert not r.get('dropped_notifications',0),'Title frame telemetry dropped'
                if windows and windows[-1]['next_entry'] is None:
                    window=windows[-1];first=window.get('first_title_publication_frame')
                    frame=r['position']['frame']
                    if first is not None and first<=frame<=first+4:
                        s.send_async('capture.screenshot',{'path':str(directory/f'cycle-{len(windows)}-transition-request-{frame}.png')})
                    # A capture describes the preceding completed scan. Begin
                    # after the first wholly title-owned visible field.
                    if first is not None and frame>=first+2:
                        digest=r.get('digest',{})
                        assert digest.get('width')==716 and digest.get('height')==285
                        if digest.get('digest')!=expected_digest:
                            failure=directory/f'cycle-{len(windows)}-changed-field-{frame}.png'
                            s.inspect('capture.screenshot',{'path':str(failure)})
                            atomic_json(directory/'changed-field.json',dict(frame=frame,digest=digest,expected=expected_digest,window=window,state={**state,'pointer':state['pointer'].hex()},capture=str(failure),custom=s.inspect('custom_dump')))
                            raise AssertionError({'label':'continuous actual title field changed','frame':frame,'actual':digest,'expected':expected_digest,'capture':str(failure)})
                        samples=window['title_frame_digests']
                        if samples:assert frame==samples[-1]['frame']+1,'Title frame observation gap'
                        samples.append(dict(frame=frame,digest=digest['digest'],position=r['position']))
                return
            if message.get('method')!='event.mmio':return
            r=message['params'];a=r['addr'];v=r['value'];size=r['size'];p=r['position'];n=fields.get(a)
            assert not r.get('dropped_events',0) and not r.get('dropped_notifications',0),{'label':'Attract telemetry dropped','position':p,'dropped_events':r.get('dropped_events',0),'dropped_notifications':r.get('dropped_notifications',0)}
            if n=='ready_generation':state['ready_generation']=v
            if n=='display_ready':state['ready']=state['ready_generation'] if v else None
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
            elif n=='game_celebration_loops':state['loops']=max(state['loops'],v) # Return clears the live counter before lifecycle2.
            elif n=='game_celebration_first_play' and v:state['first']=dict(callback=state['started'],position=p)
            elif n=='ui_demo':
                state['demo']=v
                if v:
                    entry=dict(callback=state['started'],position=p,idle=state['idle']);entries.append(entry)
                    check('automatic attract enters after full title idle',state['idle'],1800)
                    if windows:
                        windows[-1]['next_entry']=entry
                        s.send_async('events.subscribe',{'events':['frame','mmio'],'frame_interval':50,'frame_digest':False,'mmio':watches})
            elif n=='game_lifecycle':
                state['life']=v
                assert v not in (7,8),'Attract reached superseded intermediate title/court lifecycle'
                if v==6:state.update(award=dict(callback=state['completed'],position=p),first=None,loops=0)
                elif v==2 and state['award'] is not None:
                    check('automatic return follows actual first-play completion',state['first'] is not None,True)
                    check('exact full native phrase before unattended return',state['first']['callback']-state['award']['callback'],926)
                    check('one completed phrase before unattended return',state['loops'],1)
                    windows.append(dict(award=state['award'],first_play=state['first'],returned=dict(callback=state['completed'],position=p),next_entry=None,publications=0,stable=False,unexpected_title_writes=0,title_frame_digests=[],first_title_publication_frame=None))
                    s.send_async('events.subscribe',{'events':['frame'],'frame_interval':1,'frame_digest':True})
                    state['award']=None
            elif n=='display_ready' and v and windows and windows[-1]['next_entry'] is None and state['life']==2 and not state['dirty']:
                windows[-1]['stable']=True
            if any(start<=a<a+size<=start+length for start,length in planes+controls):
                if windows and windows[-1]['next_entry'] is None and windows[-1]['stable']:
                    windows[-1]['unexpected_title_writes']+=1
                    raise AssertionError('Quiet menu bitmap changed after completed menu construction')
            if 0xdff080<=a and a+size<=0xdff084:state['pointer'][a-0xdff080:a-0xdff080+size]=v.to_bytes(size,'big')
            if a==0xdff088:
                pointer=int.from_bytes(state['pointer'],'big')
                check('publication has a complete native ready scene',state['ready'] is not None and state['ready']<=state['completed'],True)
                if state['started']:assert p['vpos']>=253,{'label':'retained sprite/header blank window','position':p}
                assert pointer==title or pointer in courts,'Unknown published Copper bank'
                if windows and windows[-1]['next_entry'] is None:
                    check('every returned-title publication selects actual title bank',pointer,title)
                    windows[-1]['publications']+=1
                    if windows[-1]['first_title_publication_frame'] is None:
                        windows[-1]['first_title_publication_frame']=p['frame']
                        # Observe quiet bitmap writes after construction, which
                        # exceeds Copperline's bounded per-field event queue.
                        # Continuous field digests start at the same publication.
                        request=s.send_async('events.subscribe',{'events':['mmio'],'mmio':quiet_watches})
                        quiet_requests[request]=windows[-1]
                publications.append(dict(pointer=pointer,position=p,lifecycle=state['life'],demo=state['demo']))
        def read(n,length=1):return int.from_bytes(bytes.fromhex(s.inspect('mem_read',{'addr':base+symbols[n],'len':length})['data']),'big')
        state.update(life=read('game_lifecycle',2),demo=read('ui_demo'),dirty=read('ui_dirty'),idle=read('ui_idle',2),started=read('simulation_started_updates',2),completed=read('simulation_updates',2),ready_generation=read('ready_generation',2),ready=read('ready_generation',2) if read('display_ready') else None)
        regs=s.inspect('custom_dump')['regs'];state['pointer']=bytearray(((regs['COP1LCH']<<16)|regs['COP1LCL']).to_bytes(4,'big'))
        s.notification_handler=event
        watches=[{'addr':a,'len':1 if n in ('ui_demo','ui_dirty','game_celebration_first_play','display_ready') else 2,'access':'write'} for a,n in fields.items()]
        watches += [{'addr':a,'len':length,'access':'write'} for a,length in controls]
        watches += [{'addr':0xdff080,'len':4,'access':'write'},{'addr':0xdff088,'len':2,'access':'write'}]
        quiet_watches=watches+[{'addr':a,'len':length,'access':'write'} for a,length in planes]
        s.inspect('events.subscribe',{'events':['mmio'],'mmio':watches})
        # No injected state, keyboard/pad actions, seeded fixture or callback stops.
        s.inspect('run_until',{'seconds':stop['seconds']+570});s.inspect('events.unsubscribe');s.notification_handler=None
        check('two unattended result-to-title cycles',len(windows),2)
        check('third attract starts after second idle',len(entries),3)
        check('all quiet subscriptions acknowledged',len(quiet_requests),0)
        for cycle,window in enumerate(windows,1):
            check('every PAL title field checked continuously',len(window['title_frame_digests'])>=1400,True)
            check('title construction completed',window['stable'],True)
            check('quiet bitmap subscription acknowledged',bool(window.get('quiet_subscription_ack')),True)
            check('title actual bank publications observed',window['publications']>0,True)
            check('no hidden quiet menu bitmap mutation',window['unexpected_title_writes'],0)
            elapsed=window['next_entry']['position']['seconds']-window['returned']['position']['seconds']
            check('retained bounded 30-second title idle',29.9<elapsed<30.2,True)
            for offset in (4,600,1200,1790):
                path=directory/f'cycle-{cycle}-title-{offset}.png'
                assert_title_raster(path);assert_menu_selection_raster(path,0,1)
    target_log(directory)
    report=dict(passed=True,checks=checks,windows=windows,entries=entries,publications=publications,captures=[str(p.relative_to(ROOT)) for p in captures],
                executable_sha256=hashlib.sha256(exe.read_bytes()).hexdigest(),scope='Two uninterrupted ordinary unattended cycles through selected tune, actual title COP1LC/blank publications, continuous full-title bitmap/control write watch, every PAL title field digest and eight authored-font scanouts; invariant full-field digest anchored to independently checked ordinary startup title; no physical inputs/state writes or hardware parity claim')
    atomic_json(directory/'report.json',report);print(json.dumps(dict(passed=True,cycles=len(windows),entries=len(entries),publications=len(publications),title_frames=len(captures))))


if __name__=='__main__':
    tracked_call([ROOT/'build/tests/attract-two-cycles/report.json'],'native-demo','maintained-native','ordinary title','scripts/run_attract_cycle_tests.py',None,run,
                 lambda p,r:[ROOT/'build/amiga/interfaces/enhanced/baseline-rally'])
