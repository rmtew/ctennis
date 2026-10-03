"""Finite actual sprite DMA/publication checks and one-time startup phase sweep."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from build_native_game import build
from copperline_test_session import NativeControlSession
from native_evidence import atomic_json, compile_manifest, tracked_call
from native_hunk import loaded_hunks
from native_observation import target_log
from native_sprite_dma import analyse, legacy_header_control
from native_tools import ROOT, ASSEMBLER, emulator_config, run as assemble

NAMES=('front_copper','back_copper','ready_copper','spare_copper','display_ready',
       'ready_generation','ready_title_display','simulation_updates','simulation_started_updates',
       'presentation_copper','presentation_last_line','presentation_last_safe_line',
       'copperlist','copperlist_back','copperlist_third','copperlist_end',
       'sprite0','sprite_back','sprite_third','title_copper')


def execute_case(name, phase, scenario='play', standard='PAL', control=None, lace=False, frames=72):
    cfg=emulator_config();directory=ROOT/'build/tests/native-sprite-dma'/name
    directory.mkdir(parents=True,exist_ok=True)
    source=(ROOT/'amiga/main.s').read_text()
    marker='        bsr     read_sim_timer\n        move.l  d0,last_timer_count'
    if source.count(marker)!=1:raise ValueError('Initial clock-origin marker changed')
    wait=f'''fixture_startup_phase:
        bsr     read_presentation_line
        cmpi.w  #{phase},d0
        bne.s   fixture_startup_phase
'''
    source=source.replace(marker,wait+marker)
    if lace:
        display=(ROOT/'amiga/display.i').read_text().replace('$0100,$4200','$0100,$4204')
        (directory/'display-lace.i').write_text(display)
        source=source.replace('        include "amiga/display.i"',f'        include "{directory}/display-lace.i"')
    if control=='stale':
        source=source.replace('        move.l  ready_copper,d0','        move.l  front_copper,d0',1)
    elif control=='unknown':
        source=source.replace('presentation_selected:\n','presentation_selected:\n        addq.l  #4,d0\n')
    elif control=='height':
        source=source.replace('        addi.w  #16,d2','        addi.w  #15,d2')
    fixture=directory/'fixture.s';fixture.write_text(source)
    exe,listing=directory/'native-fixture',directory/'native.lst'
    assemble([str(ASSEMBLER),'-Fhunkexe','-kick1hunks','-m68000','-DENHANCED_INTERFACE=1',
              '-L',str(listing),'-o',str(exe),str(fixture)])
    compile_manifest(exe,listing)
    located={n:(int(h),int(o,16)) for n,h,o in re.findall(
        r'^([A-Za-z_][\w]*)\s+(\d\d):([0-9A-Fa-f]{8})\s*$',listing.read_text(),re.M)}
    samples=[];cpu_events=[]
    with NativeControlSession(directory) as s:
        s.inspect('session_launch',{'binary':cfg['tools']['copperline'],'run':str(exe),
            'args':['--chipset','OCS','--video',standard,'--cpu','68000','--chip','512K',
                    '--slow','0','--fast','0','--noaudio',cfg['inputs']['amiga_rom']]})
        stop=s.inspect('run_until',{'seconds':30});assert stop['reason']=='loadseg'
        segments=s.inspect('segments.list')['current']
        def address(n):h,o=located[n];return segments[h]['start']+o
        def raw(a,n):return bytes.fromhex(s.inspect('mem_read',{'addr':a,'len':n})['data'])
        def scalar(n,size=2):return int.from_bytes(raw(address(n),size),'big')
        loaded=loaded_hunks(exe,segments,raw)
        assert loaded and all(r['matched'] for r in loaded)
        t=stop['seconds']
        def advance(dt):
            nonlocal t
            t=max(t,s.inspect('status')['seconds'])+dt
            return s.inspect('run_until',{'seconds':t})
        def key(k,held):s.inspect('input_key',{'rawkey':k,'action':'press' if held else 'release'})
        for port in (1,2):s.inspect('input_set_port',{'port':port,'device':'joystick'})
        advance(.8)
        if scenario!='title':
            key(2 if scenario=='two' else 1,True);advance(.1);key(2 if scenario=='two' else 1,False)
            advance(1.5)
            if scenario!='serve':
                s.inspect('input_joy',{'port':2,'red':True});advance(.4)
                s.inspect('input_joy',{'port':2,'red':False});advance(.1)
        profile=directory/'trace'
        watches=[{'addr':address(n),'len':z,'access':'write'} for n,z in [('front_copper',4),('back_copper',4),('ready_copper',4),('spare_copper',4),('display_ready',1),('ready_generation',2),('ready_title_display',1),('simulation_updates',2),('simulation_started_updates',2),('presentation_copper',4)]]
        watches += [{'addr':address(n),'len':address('copperlist_end')-address('copperlist'),'access':'write'} for n in ('copperlist','copperlist_back','copperlist_third')]
        watches += [{'addr':address(n),'len':576,'access':'write'} for n in ('sprite0','sprite_back','sprite_third')]
        watches += [{'addr':0xdff080,'len':4,'access':'write'},{'addr':0xdff088,'len':2,'access':'write'},{'addr':0xdff004,'len':4,'access':'read'}]
        def observe(message):
            if message.get('method')=='event.mmio':cpu_events.append(message['params'])
        s.notification_handler=observe
        s.inspect('events.subscribe',{'events':['mmio'],'mmio':watches})
        s.inspect('profile.start',{'path':str(profile),'frames':frames,'slots':True,'memory':True,
                                  'screenshots':'last','pc_samples':False})
        schedule={}
        if scenario=='title':schedule={4:(0x4c,True),6:(0x4c,False),10:(0x44,True),12:(0x44,False),26:(0x45,True),28:(0x45,False)}
        elif scenario=='pause':schedule={10:(0x45,True),12:(0x45,False),40:(0x45,True),42:(0x45,False)}
        elif scenario=='return':schedule={10:(0x45,True),12:(0x45,False),20:(0x4e,True),22:(0x4e,False),30:(0x44,True),32:(0x44,False),42:(0x4e,True),44:(0x4e,False),54:(0x44,True),56:(0x44,False)}
        fired=set()
        while True:
            status=s.inspect('profile.status');written=status['frames_written']
            if status.get('done'):break
            for threshold,event in schedule.items():
                if threshold<=written and threshold not in fired:key(*event);fired.add(threshold)
            frame=s.inspect('status')['frame']
            s.inspect('run_until',{'frame':frame+1})
            stop=s.inspect('run_until',{'vpos':44,'hpos':64})
            front=scalar('front_copper',4)
            bank=[address(n) for n in ('copperlist','copperlist_back','copperlist_third')].index(front)
            data=raw(address(('sprite0','sprite_back','sprite_third')[bank]),576)
            sample={'position':stop,'front':front,'installed':scalar('presentation_copper',4),
                    'sprite_bytes':data.hex(),'paused':scalar('ui_paused',1),
                    'lifecycle':scalar('game_lifecycle'),'page':scalar('ui_page',1)}
            samples.append(sample)
        s.inspect('profile.stop')
        s.inspect('events.unsubscribe')
        s.notification_handler=None
        atomic_json(directory/'cpu-events.json',cpu_events)
        binding={'addresses':{n:address(n) for n in NAMES},'loaded_hunks':loaded,
                 'executable_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'executable_path':str(exe.relative_to(ROOT)),
                 'profile':status,'phase':phase,'scenario':scenario,'standard':standard,'control':control,
                 'fixture':'one-time initial clock phase wait; then native main loop and physical input only',
                 'observed_last_line':scalar('presentation_last_line'),
                 'observed_last_safe_line':scalar('presentation_last_safe_line')}
    target_log(directory, standard=standard)
    metadata=[json.loads(line) for line in (profile/'profile.jsonl').read_text().splitlines()]
    full={d['frame'] for d in metadata if not d['partial']}
    used=[s for s in samples if s['position']['frame']+1 in full]
    excluded=[dict(position=s['position'],reason='outside complete profile extent') for s in samples if s['position']['frame']+1 not in full]
    result=analyse(profile,binding['addresses'],standard,live_samples=used,cpu_events=cpu_events,require_three=scenario!='title')
    result.update(binding=binding,live_samples=used,excluded_samples=excluded)
    if not control:
        if len(used)<6:raise AssertionError('Insufficient independent live samples')
        if scenario=='pause' and not any(s['paused'] for s in used):raise AssertionError('Physical pause not observed')
        if scenario=='title' and not any(s['page'] for s in used):raise AssertionError('Physical help page not observed')
        if scenario=='return' and not any(s['lifecycle']==2 for s in used):raise AssertionError('Physical returned title not observed')
    atomic_json(directory/'report.json',result)
    print(name,'PASS' if result['passed'] else 'REJECT',result['failures'][:1],flush=True)
    return result


def run(self_test=False, ntsc=False):
    build();cases=[]
    standard='NTSC' if ntsc else 'PAL'
    phases=(0,22,253,255,256,258) if ntsc else (0,22,253,255,256,308)
    for phase in phases:
        r=execute_case(f'{standard.lower()}-phase-{phase}',phase,standard=standard)
        assert r['passed'],r['failures'];cases.append(r)
    if not ntsc:
        for scenario,frames in [('two',72),('serve',72),('pause',96),('return',120),('title',72)]:
            r=execute_case(scenario,253,scenario,frames=frames);assert r['passed'],r['failures'];cases.append(r)
        r=execute_case('alternating-fields',253,lace=True)
        assert r['passed'],r['failures'];assert len(r['field_geometries'])==2,r['field_geometries'];cases.append(r)
    controls=[]
    if self_test:
        wanted={'stale':'strobe does not install current latest completed scene',
                'unknown':'unknown installed Copper list','height':'malformed visible sprite geometry'}
        for control,reason in wanted.items():
            r=execute_case('control-'+control,22,control=control,frames=24)
            assert not r['passed'] and any(f['reason']==reason for f in r['failures']),r['failures']
            controls.append(dict(control=control,detected=True,first_failure=r['failures'][0],binding=r['binding']))
    report=dict(passed=True,interface_flavor='enhanced',executable_sha256=cases[0]['binding']['executable_sha256'],target=f'A500/68000/OCS/{standard}/512KB chip/zero slow and fast/external Kick1.3',
                cases=cases,compiled_controls=controls,
                scope='One-time startup phase fixtures, actual native dispatcher and physical input. Address/generation/ownership coverage; raw sidecar data values explicitly uncertified.')
    atomic_json(ROOT/f'build/tests/native-sprite-dma-{standard.lower()}-report.json',report)
    return 0


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test',action='store_true');parser.add_argument('--ntsc',action='store_true')
    parser.add_argument('--legacy-profile',type=Path);parser.add_argument('--legacy-executable',type=Path)
    parser.add_argument('--legacy-banks',type=lambda s:[int(x,0) for x in s.split(',')])
    args=parser.parse_args()
    if args.legacy_profile:
        assert args.legacy_executable and args.legacy_banks
        assert hashlib.sha256(args.legacy_executable.read_bytes()).hexdigest()=='fe03f7f33ba3a322528a9e5db129b61bc0a9734c9f351c5a562738e94a074382'
        report=legacy_header_control(args.legacy_profile,args.legacy_banks)
        assert not report['passed'] and report['failures'],'Actual released header-as-DATA control escaped'
        atomic_json(ROOT/'build/tests/native-sprite-dma-old-release.json',report)
        print('exact released control REJECT',len(report['failures']));raise SystemExit(0)
    name='ntsc' if args.ntsc else 'pal';path=ROOT/f'build/tests/native-sprite-dma-{name}-report.json'
    raise SystemExit(tracked_call([path],'sprite-dma','maintained-native','one-time startup phase fixtures',
        'scripts/run_sprite_dma_tests.py',None,lambda:run(args.self_test,args.ntsc),
        lambda p,r:[ROOT/c['binding']['executable_path'] for c in r['cases']]))
