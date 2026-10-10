"""Physical ADF entry and complete scanout evidence; never edits guest state."""
import argparse, json, os, shutil, subprocess, traceback
from pathlib import Path
from uuid import uuid4
from build_match_core import load_image
from native_tools import ROOT, emulator_config
from native_evidence import ReportRun, atomic_json, digest, inputs_for, snapshot
from native_hunk import loaded_hunks
from tutorial_capture import CaptureSession, native_view, animation, assert_native_text, assert_tutorial_menu

CLOCK = {'PAL':3546895, 'NTSC':3579545}

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
            # LoadSeg stops before entry/startup. Let the product install its
            # own low-resolution display before applying native pixel geometry.
            position=session.inspect('run_until',dict(seconds=(position['cck']+2*CLOCK[standard])/3546895))
            fields=dict(tutorial_active=1,tutorial_menu=1,tutorial_menu_selection=1,tutorial_x=1,tutorial_y=1,
                        tutorial_generation=4,tutorial_active_variant=1,tutorial_ball_mode=1,tutorial_render_phase=2,
                        tutorial_footer_dirty=1,tutorial_waiting_ready=1,tutorial_status=2,game_lifecycle=2,
                        game_score_initialized=1,game_lower_phase=1,game_upper_phase=1,
                        game_preview_status=2,game_preview_kind=2,game_preview_primed_mask=2,
                        game_preview_counts=4,game_preview_dispatch_stages=4,game_preview_synthetic_phases=4)
            def state():return {n:int.from_bytes(raw(symbols[n],w),'big') for n,w in fields.items() if n in symbols}
            def frame(name):
                nonlocal position
                position=session.inspect('run_until',dict(frame=position['frame']+1))
                viewport=attempt/(name+'-viewport.png'); native=attempt/(name+'.png')
                session.inspect('capture.screenshot',dict(path=str(viewport)));native_view(viewport,native)
                row=dict(name=name,position=position,path=str(native),sha256=digest(native),state=state())
                row['objects']=raw(symbols['game_scene_objects'],64).hex()
                row['core']=raw(symbols['game_core_state'],318).hex()
                row['history']=raw(symbols['game_history_state'],72).hex()
                report['frames'].append(row);return row
            def frames(prefix,count):return [frame(prefix+'-%03d'%i) for i in range(count)]
            def key(code,held):
                report['actions'].append(dict(rawkey=code,held=held,position=position))
                session.inspect('input.key',dict(rawkey=code,action='press' if held else 'release'))
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
            stable=frames('tutorial-initial',60)
            assert any(r['state']['tutorial_active'] for r in stable),'Physical entry never activated tutorial'
            # Keep collecting after visual failures so slow controls remain measurable.
            def check(name,call):
                try:report['checks'][name]=dict(passed=True,result=call())
                except AssertionError as e:report['checks'][name]=dict(passed=False,error=str(e))
            check('initial-banner',lambda:assert_native_text(stable[-1]['path'],4,'TUTORIAL',True))
            key(0x22,True);frames('move-right',20);key(0x22,False);frames('move-release',3)
            key(0x23,True);held=frames('held-preview',70)
            key(0x23,False);frames('released-preview',10)
            key(0x24,True);frames('menu-press',2);key(0x24,False)
            menu=frames('menu-open',160)
            check('menu-open',lambda:assert_tutorial_menu(menu[-1]['path'],0))
            key(0x4d,True);frames('menu-down',3);key(0x4d,False);selection=frames('menu-select',160)
            check('menu-selected',lambda:assert_tutorial_menu(selection[-1]['path'],1))
            report['animation']=animation([Path(r['path']) for r in report['frames'] if r['name'].startswith(('tutorial-initial','move-right','held-preview','menu-open','menu-select'))],attempt/'scanout.gif',20 if standard=='PAL' else 17)
            report['passed']=all(c['passed'] for c in report['checks'].values())
        tx.finalize(output,report,compiled=[json.loads(manifest.read_text())],artifacts=list(attempt.iterdir()))
        shutil.copy2(output,attempt/'report.json')
        print(json.dumps(dict(passed=report['passed'],attempt=str(attempt),checks=report['checks'])),flush=True)
        return report['passed']
    except BaseException as error:
        atomic_json(attempt/'failure.json',dict(error=str(error),traceback=traceback.format_exc(),partial=report));tx.abort(error);raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--ntsc',action='store_true');p.add_argument('--delivered',action='store_true');p.add_argument('--match',action='store_true');a=p.parse_args()
    raise SystemExit(0 if run('NTSC' if a.ntsc else 'PAL',a.delivered,a.match) else 1)
