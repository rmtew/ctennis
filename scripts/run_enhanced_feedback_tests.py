"""Bounded ordinary physical play: game-win identity and tally feedback across ends."""
import argparse,hashlib,json,re
from build_native_game import build,module_hashes
from capture_native_presentation import code_symbols
from copperline_test_session import NativeControlSession
from evidence import ROOT,atomic_json
from run_interface_tests import target_log


def run(mode):
    config,exe=build(flavor='enhanced')
    symbols=code_symbols((exe.parent/'native.lst').read_text())
    directory=ROOT/f'build/tests/enhanced-feedback-{mode}'
    rows=[];checks=[]
    def check(label,actual,expected):
        checks.append({'label':label,'actual':actual,'expected':expected})
        if actual!=expected:raise AssertionError(checks[-1])
    with NativeControlSession(directory) as s:
        s.inspect('session_launch',{'binary':config['tools']['copperline'],'run':str(exe),'args':[
            '--chipset','OCS','--video','PAL','--cpu','68000','--chip','512K','--slow','0','--fast','0','--noaudio',config['inputs']['amiga_rom']]})
        stop=s.inspect('run_until',{'seconds':30});assert stop['reason']=='loadseg',stop
        base=int(re.search(r'first hunk \$([0-9a-fA-F]+)',stop['detail'])[1],16);time=stop['seconds']
        def advance(t=.1):
            nonlocal time
            time+=t;s.inspect('run_until',{'seconds':time})
        def mem(name,n=1):return bytes.fromhex(s.inspect('mem_read',{'addr':base+symbols[name],'len':n})['data'])
        def num(name,n=1):return int.from_bytes(mem(name,n),'big')
        advance(2)
        key=0x01 if mode=='one' else 0x02
        s.inspect('input_key',{'rawkey':key,'action':'press'});advance(1.3)
        s.inspect('input_key',{'rawkey':key,'action':'release'});advance(.1)
        for port in (1,2):
            s.inspect('input_set_port',{'port':port,'device':'joystick'})
            s.inspect('input_joy',{'port':port,'red':True})
        games=[0,0];seen_exchange=False
        for tick in range(1800): # <=180 seconds; finite first two awards, no phase starts
            advance()
            current=list(mem('game_games_a',2))
            flipped=bool(num('game_mode')&16)
            if flipped:seen_exchange=True
            if current==games:continue
            winner=0 if current[0]>games[0] else 1
            advance(.1)
            check('logical colour winning feedback',num('ui_overlay_kind'),2+winner)
            check('Blue tally after award',num('ui_tally_blue_digit'),48+current[0])
            check('Pink tally after award',num('ui_tally_pink_digit'),48+current[1])
            check('Blue style stays on physical player',mem('game_play_state',60)[9],3 if flipped else 2)
            check('Pink style stays on physical player',mem('game_play_state',60)[19],2 if flipped else 3)
            photo=directory/f'game-{sum(current)}-{("blue","pink")[winner]}.png'
            s.inspect('capture_screenshot',{'path':str(photo)})
            rows.append({'games':current,'winner':('Blue','Pink')[winner],'exchanged':flipped,
                         'callback':num('simulation_updates',2),'screenshot':str(photo.relative_to(ROOT)),
                         'overlay_kind':num('ui_overlay_kind')})
            games=current
            if len(rows)==2:break
        check('two ordinary game awards observed',len(rows),2)
        check('ordinary end exchange reached',seen_exchange,True)
        failures=num('missed_presentation_deadlines',2)
    target_log(directory)
    report={'passed':True,'mode':mode,'checks':checks,'awards':rows,'observed_missed_publication_deadlines':failures,
            'executable_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'native_modules':module_hashes(),
            'scope':'Ordinary title/input/first two games/end exchange; no state writes or full-match claim'}
    atomic_json(directory/'report.json',report)
    print(json.dumps({'passed':True,'awards':rows,'missed_publications':failures}))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--mode',choices=('one','two'),required=True)
    run(parser.parse_args().mode)
