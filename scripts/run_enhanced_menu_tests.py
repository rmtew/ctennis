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


def run(adf=False,help_only=False):
    package_report = package(self_test=True) if adf else None
    config, exe = build(flavor='enhanced'); config = emulator_config()
    symbols = code_symbols((exe.parent/'native.lst').read_text())
    for forbidden in ('initial_ram','captured_state','refresh_signs','game_audio_import_capture','scene_import_capture','psg_log'):
        if forbidden in symbols: raise ValueError('Ordinary executable contains diagnostic machinery: '+forbidden)
    directory = ROOT/'build/tests'/('help-navigation' if help_only else 'enhanced-menu-cold' if adf else 'enhanced-menu-ordinary')
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
            if n in ('menu','returned-title','players-two','help-selected','help-returned','controls-selected'):
                from native_identity_raster import assert_menu_selection_raster
                checks.append(assert_menu_selection_raster(path,number('ui_selection'),1+number('ui_player_count')))
            if n in ('menu','returned-title'):
                from native_identity_raster import assert_title_raster
                assert_title_raster(path)
            if n in ('paused','pause-return-selected','confirm-no','confirm-yes','demo-held-entry','demo-take-over-selected'):
                from native_identity_raster import assert_footer_raster
                if n=='paused':row=('PAUSED','RESUME','RESUME')
                elif n=='pause-return-selected':row=('PAUSED','RETURN TO TITLE','RETURN TO TITLE')
                elif n=='confirm-no':row=('RETURN TO TITLE?','NO - RESUME','NO - RESUME')
                elif n=='confirm-yes':row=('RETURN TO TITLE?','YES - RETURN TO TITLE','YES - RETURN TO TITLE')
                else:
                    first={0:'',2:'A WINS GAME',3:'B WINS GAME',4:'YOUR SERVE'}[number('ui_overlay_kind')]
                    row=(first,'DEMO - TAKE OVER / EXIT','TAKE OVER' if number('ui_demo_choice') else 'EXIT')
                checks.append(assert_footer_raster(path,*row))
            if n=='play':
                from native_identity_raster import assert_mode_raster,assert_logo_absent_initial_raster
                assert_mode_raster(path,2)
                assert_logo_absent_initial_raster(path)
        def help_photo(name):
            path=directory/(name+'.png');s.inspect('capture_screenshot',{'path':str(path)})
            from native_ui_raster import assert_ui_raster
            checks.append(assert_ui_raster(path,number('ui_page'),number('ui_player_count'),number('ui_selection'),(ROOT/'build/native/version.bin').read_bytes().rstrip(b'\0').decode('ascii'),number('ui_help_choice')))
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
        # Exercise the side-figure rows with actual physical input in all eight
        # mode/selection states. Full scanout guards catch full-row highlight
        # copies that would erase or turn the blue/red figures white.
        for players in (1,2):
            if players==2:
                key(0x4d);key(0x4e);key(0x4c)
            check('title role toggle '+str(players),number('ui_player_count'),players-1)
            for selection in range(4):
                check('title selection '+str((players,selection)),number('ui_selection'),selection)
                help_photo('side-menu-'+str(players)+'p-selection-'+str(selection))
                key(0x4d)
            check('title navigation wraps '+str(players),number('ui_selection'),0)
        key(0x4d);key(0x44)
        check('Mode action toggles back to AI',number('ui_player_count'),0)
        key(0x4c);key(0x4e)
        check('right outside Mode preserves roles',number('ui_player_count'),0)
        key(0x03);check('3 has no shortcut',number('game_lifecycle',2),2)
        edge(0x4d,True);advance(.4);check('held down selects players once',number('ui_selection'),1);edge(0x4d,False)
        edge(0x4e,True);advance(.4);check('held right selects two players once',number('ui_player_count'),1);edge(0x4e,False)
        photo('players-two')
        key(0x4f);check('left selects one player',number('ui_player_count'),0)
        key(0x4e);key(0x4d);photo('help-selected');key(0x44)
        check('Enter opens Help',number('ui_page'),1)
        check('help defaults NEXT',number('ui_help_choice'),2);help_photo('help-next')
        edge(0x4e,True);advance(.4)
        check('right clamps NEXT',number('ui_help_choice'),2)
        check('right does not page',number('ui_page'),1);edge(0x4e,False)
        edge(0x44,True);advance(.4)
        check('held Enter pages once',number('ui_page'),2)
        check('NEXT persists',number('ui_help_choice'),2);help_photo('scoring-next');edge(0x44,False)
        key(0x23);check('action advances to controls',number('ui_page'),3);help_photo('controls-next')
        key(0x44);check('NEXT advances to credits last',number('ui_page'),4);help_photo('credits-next')
        key(0x44);check('NEXT wraps credits to help',number('ui_page'),1)
        edge(0x4f,True);advance(.4)
        check('held left selects EXIT once',number('ui_help_choice'),1)
        check('left does not page',number('ui_page'),1);help_photo('help-exit');edge(0x4f,False)
        key(0x4f);check('left selects BACK',number('ui_help_choice'),0)
        key(0x4f);check('left clamps BACK',number('ui_help_choice'),0)
        key(0x44);check('BACK wraps help to credits',number('ui_page'),4)
        check('BACK persists after wrap',number('ui_help_choice'),0);help_photo('credits-back')
        key(0x23);check('BACK action returns controls',number('ui_page'),3);help_photo('controls-back')
        key(0x4e);check('right selects EXIT',number('ui_help_choice'),1)
        key(0x44);check('Enter activates EXIT',number('ui_page'),0);photo('help-returned')
        key(0x4d);photo('controls-selected');key(0x44)
        check('Controls entry resets NEXT',number('ui_help_choice'),2)
        check('Controls entry page',number('ui_page'),3)
        key(0x45);check('Escape exits regardless of NEXT',number('ui_page'),0)
        key(0x4c);key(0x44)
        check('Help reentry defaults NEXT',number('ui_help_choice'),2)
        key(0x4f);help_photo('help-exit-action')
        key(0x23);check('action activates EXIT',number('ui_page'),0)
        if help_only:
            target_log(directory)
            report={'passed':True,'checks':checks,'loaded_hunks':loaded,'scope':'Ordinary physical help navigation and exact native scanout','executable_sha256':hashlib.sha256(exe.read_bytes()).hexdigest()}
            atomic_json(directory/'report.json',report);print(json.dumps({'passed':True,'checks':len(checks),'report':str(directory/'report.json')}));return report
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
        key(0x45);edge(0x4d,True);advance(.4);check('held pause navigation selects once',number('ui_selection'),1);edge(0x4d,False);photo('pause-return-selected');key(0x44)
        check('return needs confirmation',number('ui_confirmation'),255)
        check('confirmation stays in game',number('game_lifecycle',2),1);photo('confirm-no')
        key(0x45);check('Escape cancels confirmation',number('ui_confirmation'),0)
        key(0x4d);key(0x44);edge(0x4e,True);advance(.4);check('held confirmation navigation selects YES once',number('ui_selection'),1);edge(0x4e,False);photo('confirm-yes');key(0x44)
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
        check('demo defaults to EXIT',number('ui_demo_choice'),0)
        key(0x4f);check('left selects TAKE OVER',number('ui_demo_choice'),1)
        key(0x4e);check('right selects EXIT',number('ui_demo_choice'),0)
        key(0x4f);photo('demo-take-over-selected')
        s.inspect('input_key',{'rawkey':0x44,'action':'press'})
        took_over=False
        for _ in range(12):
            until({'pc':base+symbols['ui_sample']});before=frozen()
            until({'pc':base+symbols['ui_input_draw']})
            if not number('ui_demo'):
                check('takeover preserves game, score, audio and clocks',frozen().hex(),before.hex())
                took_over=True;break
        check('selected Enter takes over',took_over,True)
        until({'pc':base+symbols['native_input_done']})
        check('takeover press is consumed',number('game_player_controls')&32,0)
        edge(0x44,False)
        advance(.4);photo('takeover')
        check('entry-held W stays physically down',mem('game_keyboard_matrix',128)[0x11],1)
        check('entry-held W cannot cause movement after takeover',number('game_player_controls')&2,0)
        check('takeover continues one-player AI',number('game_mode')&128,0)
        # Return and prove the alternative B action exits rather than taking over.
        key(0x19);key(0x4d);key(0x44);key(0x4e);key(0x44)
        advance(32);check('next demo starts',number('ui_demo'),255)
        key(0x3a);check('B slash exits demo',number('game_lifecycle',2),2)
        check('other input leaves demo',number('ui_demo'),0)
        # Same normal takeover path for the physical A second joystick button.
        advance(32);check('third demo starts',number('ui_demo'),255)
        s.inspect('input_set_port',{'port':2,'device':'joystick'})
        check('third demo defaults EXIT',number('ui_demo_choice'),0)
        edge(0x24,True);check('default G exits demo',number('ui_demo'),0)
        edge(0x24,False);advance(32);check('fourth demo starts',number('ui_demo'),255)
        key(0x4f);check('left selects joystick takeover',number('ui_demo_choice'),1)
        s.inspect('input_joy',{'port':2,'blue':True})
        # A physical control event may arrive after the next pad sample. Observe
        # bounded real UI samples as for G above; never inject takeover state.
        for _ in range(12):
            until({'pc':base+symbols['ui_sample']});before=frozen()
            until({'pc':base+symbols['ui_input_draw']})
            if not number('ui_demo'):break
        check('selected port2 button2 takes over A',number('ui_demo'),0)
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
    report = {'passed':True,'interface_flavor':'enhanced','startup':'cold ADF' if adf else 'ordinary executable',
              'checks':checks,'target':'Copperline 1.0.0-rc.1 PAL A500 68000 OCS 512KB chip/no expansion/Kickstart1.3',
              'executable_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),
              'native_modules':__import__('build_native_game').module_hashes(),
              'input_recording_sha256':hashlib.sha256((ROOT/'assets/interface/demo-inputs.json').read_bytes()).hexdigest(),
              'loaded_hunks':loaded,
              'adf_sha256':package_report['adf_sha256'] if adf else None,
              'scope':'Finite ordinary physical inputs; no game-state writes, source initialization or full-match parity'}
    atomic_json(directory/'report.json',report)
    print(json.dumps({'passed':True,'checks':len(checks),'report':str(directory/'report.json')}))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--adf', action='store_true')
    parser.add_argument('--help-only',action='store_true')
    args = parser.parse_args()
    path = ROOT / 'build/tests' / ('help-navigation' if args.help_only else 'enhanced-menu-cold' if args.adf else 'enhanced-menu-ordinary') / 'report.json'
    tracked_call([path], 'native-menu', 'maintained-native', 'cold ADF' if args.adf else 'ordinary title',
                 'scripts/run_enhanced_menu_tests.py', None, lambda: run(args.adf,args.help_only),
                 lambda path, report: [ROOT / 'build/amiga/interfaces/enhanced/baseline-rally'])
