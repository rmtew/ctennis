"""PAL/NTSC native CIA cadence in colour-clock units, independent of host seconds."""
import hashlib,json,re
from fractions import Fraction
from build_native_game import build
from copperline_test_session import NativeControlSession
from native_evidence import atomic_json,tracked_call
from native_hunk import loaded_hunks
from native_tools import ROOT,emulator_config


def run():
    _,exe=build();cfg=emulator_config();listing=(exe.parent/'native.lst').read_text()
    located={n:(int(h),int(o,16)) for n,h,o in re.findall(r'^([A-Za-z_][\w]*)\s+(\d\d):([0-9A-Fa-f]{8})\s*$',listing,re.M)}
    cases=[]
    for standard,hz,whole,fraction in [('PAL',709379,11838,14906),('NTSC',715909,11947,13180)]:
        directory=ROOT/'build/tests/native-video-clock'/standard.lower();events=[]
        with NativeControlSession(directory) as s:
            s.inspect('session_launch',{'binary':cfg['tools']['copperline'],'run':str(exe),'args':['--chipset','OCS','--video',standard,'--cpu','68000','--chip','512K','--slow','0','--fast','0','--noaudio',cfg['inputs']['amiga_rom']]})
            stop=s.inspect('run_until',{'seconds':30});assert stop['reason']=='loadseg'
            segments=s.inspect('segments.list')['current']
            def address(n):h,o=located[n];return segments[h]['start']+o
            def raw(a,n):return bytes.fromhex(s.inspect('mem_read',{'addr':a,'len':n})['data'])
            def scalar(n,z):return int.from_bytes(raw(address(n),z),'big')
            loaded=loaded_hunks(exe,segments,raw);assert loaded and all(r['matched'] for r in loaded)
            def observe(message):
                if message.get('method')=='event.mmio':
                    e=message['params'];assert not e.get('dropped_events',0) and not e.get('dropped_notifications',0);events.append(e)
            s.notification_handler=observe
            sizes={'simulation_started_updates':2,'simulation_updates':2,'simulation_timer_origin':2}
            watches=[{'addr':address(n),'len':z,'access':'write'} for n,z in sizes.items()]+[{'addr':0xbfde00,'len':1,'access':'write'}]
            s.inspect('events.subscribe',{'events':['mmio'],'mmio':watches})
            s.inspect('run_until',{'cck':stop['cck']+hz*5*4})
            s.inspect('events.unsubscribe');s.notification_handler=None
            observed={'whole':scalar('simulation_interval_whole',4),'fraction':scalar('simulation_interval_fraction',2),'last_line':scalar('presentation_last_line',2),'last_safe_line':scalar('presentation_last_safe_line',2)}
            assert (observed['whole'],observed['fraction'])==(whole,fraction),observed
            assert (observed['last_line']<300)==(standard=='NTSC'),observed
        atomic_json(directory/'cpu-events.json',events)
        start=next(e['position']['cck'] for e in events if e['addr']==0xbfde00 and e['value']&1)
        origin_value=next(e['value'] for e in events if e['addr']==address('simulation_timer_origin'))
        origin=start+(65535-origin_value)*5
        entries=[e for e in events if e['addr']==address('simulation_started_updates')]
        completed=[e for e in events if e['addr']==address('simulation_updates')]
        interval=Fraction((whole*65536+fraction)*5,65536)
        assert len(completed)>=150
        checks=[]
        for n,e in enumerate(entries,1):
            assert e['value']==n
            delta=Fraction(e['position']['cck']-origin)-(n-1)*interval
            assert -5<=delta<interval,{'standard':standard,'entry':n,'lateness_cck':float(delta)}
            if n<=len(completed):
                c=completed[n-1];assert c['value']==n
                finish=Fraction(c['position']['cck']-origin)-(n-1)*interval
                assert finish<interval,{'standard':standard,'completion':n,'lateness_cck':float(finish)}
                checks.append({'update':n,'entry_cck':e['position']['cck'],'completion_cck':c['position']['cck'],'entry_lateness_cck':float(delta),'completion_lateness_cck':float(finish)})
        case={'standard':standard,'eclock_hz':hz,'cck_hz':hz*5,'cck_per_eclock':5,'selected':observed,'origin_cck':origin,'completed_updates':len(completed),'checks':checks,'rate_hz':float(Fraction(hz*65536,whole*65536+fraction)),'loaded_hunks':loaded}
        cases.append(case);print(standard,'PASS',len(completed),'strict callbacks',flush=True)
    atomic_json(ROOT/'build/tests/native-video-clock/report.json',{'passed':True,'interface_flavor':'enhanced','cases':cases,'executable_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'scope':'Native unmodified startup and CIA dispatcher, every observed callback deadline in CCK; PAL/NTSC physical time derived from documented E-clock rates. Copperline host seconds/audio timebase remain PAL; real hardware validation is not claimed.','frequency_source':'https://d0.se/include/exec/execbase.i','emulator_cia_source':'Copperline e65a9584ccd0c86e678661ed5d2c18622da63fd4 src/bus.rs cia_ticks_for_cck: total/5'})

if __name__=='__main__':
    raise SystemExit(tracked_call([ROOT/'build/tests/native-video-clock/report.json'],'video-clock','maintained-native','ordinary native startup','scripts/run_native_video_clock_tests.py',None,run,lambda p,r:[ROOT/'build/amiga/interfaces/enhanced/baseline-rally']))
