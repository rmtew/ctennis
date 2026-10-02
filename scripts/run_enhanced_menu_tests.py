from native_tools import emulator_config
"""Finite ordinary physical-input acceptance of the enhanced menu and lifecycle."""
import argparse, hashlib, json, re
from pathlib import Path
from build_native_game import build
from build_native_adf import package
from native_observation import code_symbols
from copperline_test_session import NativeControlSession
from native_evidence import ROOT, atomic_json, tracked_call
from native_observation import target_log


def execution_subject(development, package_report=None):
    """Bind execution to packaged bytes, keeping debug symbols as a sidecar."""
    sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    debug={'executable':str(development.relative_to(ROOT)),
           'executable_sha256':sha(development),
           'listing':str((development.parent/'native.lst').relative_to(ROOT)),
           'listing_sha256':sha(development.parent/'native.lst')}
    if package_report is None:return development,debug
    if debug['executable_sha256']!=package_report['release']['development_executable_sha256']:
        raise ValueError('Menu debug source differs from packaged development product')
    executable=ROOT/package_report['executable']
    if sha(executable)!=package_report['executable_sha256']:
        raise ValueError('Menu release executable differs from package')
    if sha(ROOT/package_report['adf'])!=package_report['adf_sha256']:
        raise ValueError('Menu ADF differs from package')
    return executable,debug


def run(adf=False,boot_only=False):
    package_report = package(self_test=True) if adf else None
    config, exe = build(flavor='enhanced'); config = emulator_config()
    development=exe
    exe,debug_source=execution_subject(development,package_report)
    symbols = code_symbols((development.parent/'native.lst').read_text())
    for forbidden in ('initial_ram','captured_state','refresh_signs','game_audio_import_capture','scene_import_capture','psg_log'):
        if forbidden in symbols: raise ValueError('Ordinary executable contains diagnostic machinery: '+forbidden)
    directory = ROOT/'build/tests'/(('enhanced-menu-cold' if adf else 'enhanced-menu-ordinary')+('-boot-binding' if boot_only else ''))
    checks = []
    def check(label, actual, expected):
        checks.append({'label': label, 'actual': actual, 'expected': expected})
        if actual != expected:
            raise AssertionError(checks[-1])
    with NativeControlSession(directory) as s:
        launch = {'binary': config['tools']['copperline'], 'args': [
            '--chipset','OCS','--video','PAL','--cpu','68000','--chip','512K',
            '--slow','0','--fast','0','--noaudio',config['inputs']['amiga_rom']]}
        if not adf: launch['run'] = str(exe)
        else: launch['args'] += ['--floppy-drives','1','--floppy-speed','100']
        s.inspect('session_launch', launch)
        if adf:
            s.inspect('media.floppy.insert', {'drive':0,'path':str(ROOT/package_report['adf']), 'write_protected':True})
            catch=s.inspect('break_add',{'kind':'loadseg','name':'baseline-rally'})
            s.inspect('machine.reset', {'kind':'cold'})
        stop = s.inspect('run_until', {'seconds':120 if adf else 30})
        if stop['reason'] != 'loadseg': raise RuntimeError(stop)
        if adf: s.inspect('break_remove',{'id':catch['id']})
        base = int(re.search(r'first hunk \$([0-9a-fA-F]+)', stop['detail'])[1],16)
        time = stop['seconds']
        def until(args):
            nonlocal time
            result = s.inspect('run_until',args);time = result['seconds'];return result
        def advance(t=.09): until({'seconds':time+t})
        def mem(n,k=1): return bytes.fromhex(s.inspect('mem_read',{'addr':base+symbols[n],'len':k})['data'])
        def number(n,k=1): return int.from_bytes(mem(n,k),'big')
        def edge(k,held):
            s.inspect('input_key',{'rawkey':k,'action':'press' if held else 'release'});advance()
        def key(k): edge(k,True);edge(k,False)
        def photo(n):
            path=directory/(n+'.png')
            s.inspect('capture_screenshot',{'path':str(path)})
            if n in ('menu','returned-title'):
                from native_identity_raster import assert_title_raster
                assert_title_raster(path)
            if n=='play':
                from native_identity_raster import assert_mode_raster
                assert_mode_raster(path,2)
        def frozen():
            return (mem('game_play_state',60)+mem('game_score_state',28)+mem('game_audio_voices',96)
                    +mem('game_audio_wait')+mem('game_action_clock')+mem('game_status_clock')+mem('game_aux_clock'))
        from native_hunk import loaded_hunks
        loaded = loaded_hunks(exe,s.inspect('segments.list')['current'],lambda a,n: bytes.fromhex(s.inspect('mem_read',{'addr':a,'len':n})['data']))
        check('actual relocated executable hunks match',all(row['matched'] for row in loaded),True)
        advance(2)
        check('ordinary title',number('game_lifecycle',2),2)
        check('title display chosen',number('game_title_display'),255)
        photo('menu')
        if boot_only:
            write_report(development,exe,debug_source,package_report,directory,checks,loaded,adf,boot_only)
            return
        key(0x03);check('3 has no shortcut',number('game_lifecycle',2),2)
        key(0x4d);check('down selects players',number('ui_selection'),1)
        key(0x4e);check('right selects two players',number('ui_player_count'),1)
        photo('players-two')
        key(0x4f);check('left selects one player',number('ui_player_count'),0)
        key(0x4e);key(0x4d);key(0x44)
        check('Enter opens Help',number('ui_page'),1);photo('help')
        key(0x4e);check('right opens Controls',number('ui_page'),2);photo('controls')
        key(0x4e);check('credits/version page',number('ui_page'),3);photo('credits')
        key(0x4e);check('right page wrap',number('ui_page'),1)
        key(0x4f);check('left page wrap',number('ui_page'),3)
        key(0x45);check('Escape exits page',number('ui_page'),0)
        key(0x44);check('Enter opens selected Help',number('ui_page'),1)
        key(0x23);check('action exits page',number('ui_page'),0)
        # Both main-digit and legacy choice retain the ordinary held-release gate.
        edge(0x02,True);advance(1.2)
        check('2 chooses two players',number('game_selected_mode'),1)
        check('two-player gameplay mode selected',number('game_mode')&128,128)
        check('held choice gate',number('game_lifecycle',2),3)
        edge(0x02,False);advance(.2);check('choice release plays',number('game_lifecycle',2),1)
        photo('play')
        advance(.6)
        check('waiting human has YOUR SERVE',number('ui_overlay_kind'),4)
        edge(0x11,True) # Carry an old movement key through title/demo/takeover.
        edge(0x24,True)
        check('action removes YOUR SERVE',number('ui_overlay_kind')!=4,True)
        advance(.22)
        key(0x19);check('P pauses',number('ui_paused'),255)
        saved=mem('ui_saved_volumes',6)
        check('pause starts during audible native phrase',any(int.from_bytes(saved[i:i+2],'big') for i in (0,2,4)),True)
        check('paused Paula muted',[s.inspect('custom.read',{'reg':n})['value'] for n in ('AUD0VOL','AUD1VOL','AUD3VOL')],[0,0,0])
        before=frozen();advance(1);check('state, timers and native audio freeze',frozen().hex(),before.hex())
        photo('paused')
        s.inspect('input_key',{'rawkey':0x19,'action':'press'})
        until({'pc':base+symbols['ui_resume']})
        until({'pc':base+symbols['ui_input_draw']})
        expected_volumes=[int.from_bytes(mem('ui_saved_volumes',6)[i:i+2],'big') for i in (0,2,4)]
        check('resume restores actual native voice levels',[s.inspect('custom.read',{'reg':n})['value'] for n in ('AUD0VOL','AUD1VOL','AUD3VOL')],expected_volumes)
        edge(0x19,False)
        check('P resumes',number('ui_paused'),0)
        check('held action suppressed on resume',number('game_player_controls')&32,0)
        key(0x45);key(0x4d);key(0x44)
        check('return needs confirmation',number('ui_confirmation'),255)
        check('confirmation stays in game',number('game_lifecycle',2),1);photo('confirm-no')
        key(0x45);check('Escape cancels confirmation',number('ui_confirmation'),0)
        key(0x4d);key(0x44);key(0x4e);key(0x44)
        check('confirmed return reaches title',number('game_lifecycle',2),2)
        check('confirmation press consumed',number('ui_selection'),0)
        check('remembers two players',number('ui_player_count'),1)
        photo('returned-title')
        # Hold a gameplay key across demo entry. A sampled old hold must be ignored.
        check("G remains physically held at title",mem("game_keyboard_matrix",128)[0x24],1)
        advance(28)
        check('no premature demo',number('ui_demo'),0)
        advance(4);check('idle starts demo',number('ui_demo'),255)
        check('demo ordinary gameplay',number('game_lifecycle',2),1)
        check('demo one-player mode',number('game_mode')&128,0)
        until({'pc':base+symbols['native_input_done']})
        check('recorded packet passes normal input dispatcher',number('game_player_controls'),number('ui_demo_mask'))
        check('demo preserves remembered player count',number('ui_player_count'),1)
        photo('demo-held-entry');advance(.4)
        check('entry-held G does not take over',number('ui_demo'),255)
        edge(0x24,False)
        s.inspect('input_key',{'rawkey':0x24,'action':'press'})
        took_over=False
        for _ in range(12):
            until({'pc':base+symbols['ui_sample']});before=frozen()
            until({'pc':base+symbols['ui_input_draw']})
            if not number('ui_demo'):
                check('takeover preserves game, score, audio and clocks',frozen().hex(),before.hex())
                took_over=True;break
        check('fresh G takes over',took_over,True)
        until({'pc':base+symbols['native_input_done']})
        check('takeover press is consumed',number('game_player_controls')&32,0)
        advance(.4);photo('takeover')
        check('entry-held W stays physically down',mem('game_keyboard_matrix',128)[0x11],1)
        check('entry-held W cannot cause movement after takeover',number('game_player_controls')&2,0)
        check('takeover continues one-player AI',number('game_mode')&128,0)
        # Return and prove the alternative P2 action exits rather than taking over.
        key(0x19);key(0x4d);key(0x44);key(0x4e);key(0x44)
        advance(32);check('next demo starts',number('ui_demo'),255)
        key(0x3a);check('P2 slash exits demo',number('game_lifecycle',2),2)
        check('other input leaves demo',number('ui_demo'),0)
        # Same normal takeover path for the physical P1 second joystick button.
        advance(32);check('third demo starts',number('ui_demo'),255)
        s.inspect('input_set_port',{'port':2,'device':'joystick'})
        check('G is still held before fresh joystick takeover',mem('game_keyboard_matrix',128)[0x24],1)
        s.inspect('input_joy',{'port':2,'blue':True})
        until({'pc':base+symbols['ui_sample']});before=frozen()
        until({'pc':base+symbols['ui_input_draw']})
        check('port2 button2 takes over Blue',number('ui_demo'),0)
        check('joystick takeover preserves complete native state',frozen().hex(),before.hex())
        until({'pc':base+symbols['native_input_done']})
        check('joystick takeover press consumed',number('game_player_controls')&32,0)
        s.inspect('input_joy',{'port':2,'blue':False});advance(.2)
        check('old G is ignored after new joystick release',number('game_input_bits')&32,0)
        check('old W remains ignored after joystick takeover',number('game_input_bits')&2,0)
        edge(0x11,False);edge(0x11,True)
        check('released entry direction rearms normally',number('game_input_bits')&2,2)
        edge(0x11,False);edge(0x24,False)
        key(0x19);key(0x4d);key(0x44);key(0x4e);key(0x44)
        # Legacy immediate-start aliases.
        key(0x46);advance(1.3);check('Delete starts one player',number('game_selected_mode'),0)
        check('legacy start plays',number('game_lifecycle',2),1)
        photo('legacy-play')
        def return_title():
            key(0x19);key(0x4d);key(0x44);key(0x4e);key(0x44)
            check('menu reached for next selection',number('game_lifecycle',2),2)
        return_title();key(0x01);advance(1.3)
        check('main1 immediate start',number('game_selected_mode'),0)
        return_title();key(0x42);advance(1.3)
        check('Tab immediate two-player start',number('game_selected_mode'),1)
        check('Tab selects actual two-player gameplay',number('game_mode')&128,128)
        return_title();key(0x44);advance(1.3)
        check('Start game uses remembered player count',number('game_selected_mode'),1)
        check('Enter starts ordinary gameplay',number('game_lifecycle',2),1)
    target_log(directory)
    write_report(development,exe,debug_source,package_report,directory,checks,loaded,adf,boot_only)

def write_report(development,exe,debug_source,package_report,directory,checks,loaded,adf,boot_only):
    # Fail if execution/debug/package files changed while the harness ran.
    final_exe,final_debug=execution_subject(development,package_report)
    if final_exe!=exe or final_debug!=debug_source:raise ValueError('Menu product changed during execution')
    report = {'executable':str(exe.relative_to(ROOT)),'debug_symbol_source':debug_source,'passed':True,'interface_flavor':'enhanced','startup':'cold ADF' if adf else 'ordinary executable',
              'checks':checks,'target':'Copperline 1.0.0-rc.1 PAL A500 68000 OCS 512KB chip/no expansion/Kickstart1.3',
              'executable_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),
              'native_modules':__import__('build_native_game').module_hashes(),
              'input_recording_sha256':hashlib.sha256((ROOT/'assets/interface/demo-inputs.json').read_bytes()).hexdigest(),
              'loaded_hunks':loaded,
              'adf':package_report['adf'] if adf else None,
              'adf_sha256':package_report['adf_sha256'] if adf else None,
              'complete_menu_sequence':not boot_only,
              'scope':'Boot binding/title only; no menu lifecycle acceptance' if boot_only else 'Finite ordinary physical inputs; no game-state writes, source initialization or full-match parity'}
    atomic_json(directory/'report.json',report)
    print(json.dumps({'passed':True,'checks':len(checks),'report':str(directory/'report.json')}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--adf', action='store_true')
    parser.add_argument('--boot-only',action='store_true',help='Only loaded release/debug binding and initial title; no full menu acceptance')
    args = parser.parse_args()
    if args.boot_only and not args.adf:parser.error('--boot-only requires --adf')
    path = ROOT / 'build/tests' / (('enhanced-menu-cold' if args.adf else 'enhanced-menu-ordinary')+('-boot-binding' if args.boot_only else '')) / 'report.json'
    tracked_call([path], 'native-menu', 'maintained-native', 'cold ADF' if args.adf else 'ordinary title',
                 'scripts/run_enhanced_menu_tests.py', None, lambda: run(args.adf,args.boot_only),
                 lambda path, report: [ROOT / report['executable']])
