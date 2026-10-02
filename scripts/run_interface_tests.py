"""Finite enhanced-interface hardware checks; ordinary title and physical keys."""
import argparse,json,re
from pathlib import Path
from PIL import Image
from build_native_game import build
from capture_native_presentation import code_symbols
from copperline_test_session import NativeControlSession
from native_state_observation import read_native_state
from run_presentation_tests import source_picture,map_source_palette,native_picture,compare
from evidence import ROOT,tracked_call,atomic_json,digest
from run_mode_selection_tests import reference as mode_reference

LINES=("1 ONE PLAYER / 2 TWO PLAYERS", "P1 WASD MOVE  RED F BLUE G",
       "P2 ARROWS MOVE RED . BLUE /", "KEYPAD 8/4/2/6 MOVE RED0 BLUE.",
       "JOYSTICKS P1 PORT2 P2 PORT1", "DELETE / TAB ALSO SELECT")

def target_log(directory):
    log=(directory/'emulator.log').read_text()
    for marker in ('cpu=M68000','chip_ram=512K','slow_ram=0K','fast_ram=0K','chipset=Ocs','video=Pal','Kickstart 1.3'):
        if marker not in log:raise ValueError('Missing actual target marker: '+marker)
    (directory/'copperline.log').write_text(log)


def expected_title(contract):
    case=json.loads((ROOT/'tests/cases/p1-title.json').read_text())
    source,_,_=source_picture(case)
    picture=map_source_palette(source,contract)
    vram=(ROOT/'tests/reference/presentation/one-player-match/f00119.vram').read_bytes()
    font={c:list(vram[0x3000+n*8:0x3008+n*8])
          for n,c in enumerate('012389=/©ABCDEFGHIKLMNOPRSTUVY',0x44)}
    font.update(json.loads((ROOT/'assets/interface/small-font-additions.json').read_text()))
    font[' ']=[0]*8
    for y in range(144,192):
        for x in range(256):picture.putpixel((x,y),(0,0,0))
    for row,text in enumerate(LINES):
        x=((32-len(text))//2)*8
        for col,c in enumerate(text):
            for dy,bits in enumerate(font[c]):
                for dx in range(8):
                    picture.putpixel((x+col*8+dx,144+row*8+dy), (255,255,255) if bits&(128>>dx) else (0,0,0))
    return picture

def run(mode):
    config,exe=build(flavor='enhanced')
    directory=ROOT/f'build/tests/interface-{mode}-enhanced';directory.mkdir(parents=True,exist_ok=True)
    symbols=code_symbols((exe.parent/'native.lst').read_text());checks=[];observations={}
    def check(label,actual,expected):
        checks.append({'label':label,'actual':actual,'expected':expected})
        if actual!=expected:raise AssertionError(checks[-1])
    with NativeControlSession(directory) as s:
        s.inspect('session_launch',{'binary':config['tools']['copperline'],'run':str(exe),
          'args':['--chipset','OCS','--video','PAL','--cpu','68000','--chip','512K','--slow','0','--fast','0','--noaudio',config['inputs']['amiga_rom']]})
        stop=s.inspect('run_until',{'seconds':30});assert stop['reason']=='loadseg',stop
        base=int(re.search(r'first hunk \$([0-9a-fA-F]+)',stop['detail'])[1],16)
        time=stop['seconds']
        def advance(seconds=.08):
            nonlocal time
            time+=seconds;s.inspect('run_until',{'seconds':time})
        def mem(name,n=1):return bytes.fromhex(s.inspect('mem_read',{'addr':base+symbols[name],'len':n})['data'])
        def keys(events):
            for key,held in events:
                s.inspect('input_key',{'rawkey':key,'action':'press' if held else 'release'});advance(.025)
        def pads():return list(mem('game_input_bits',2))
        advance(2)
        check('ordinary waiting title',int.from_bytes(mem('game_lifecycle',2),'big'),2)
        screenshot=directory/'title.png';s.inspect('capture_screenshot',{'path':str(screenshot)})
        contract=json.loads((ROOT/'tests/cases/presentation.json').read_text())
        contract['amiga_active_rectangle']=[126,16,638,208]
        with Image.open(screenshot) as image:
            difference=compare(expected_title(contract),native_picture(image,contract))
            check('intended title raster',difference,None)
            for side,box in [('left',(62,16,126,208)),('right',(638,16,702,208))]:
                check(side+' title margin',image.crop(box).convert('RGB').getcolors(),[(64*192,(0,0,0))])
        keys([(0x11,True),(0x22,True),(0x23,True),(0x4f,True),(0x3c,True)])
        check('simultaneous diagonal/actions',pads(),[19,36])
        keys([(0x2d,True),(0x4f,False)])
        check('alias release retains other held key',pads(),[19,36])
        keys([(k,False) for k in (0x11,0x22,0x23,0x2d,0x3c)])
        check('all released',pads(),[0,0])
        aliases=(0x3e,0x2d,0x1e,0x2f,0x0f,0x3c)
        keys([(k,True) for k in aliases]);check('all six keypad aliases',pads(),[0,63])
        keys([(k,False) for k in aliases]);check('keypad released',pads(),[0,0])
        # Real A500 matrix suppresses ambiguous multi-key rectangles. Test
        # each opposing pair without synthesizing impossible key rollover.
        keys([(0x20,True),(0x22,True)]);check('opposing horizontal packet',pads(),[5,0])
        keys([(0x20,False),(0x22,False)])
        keys([(0x11,True),(0x21,True)]);check('opposing vertical packet',pads(),[10,0])
        keys([(0x11,False),(0x21,False)])
        s.inspect('input_set_port',{'port':2,'device':'joystick'})
        keys([(0x23,True)])
        s.inspect('input_joy',{'port':2,'red':True});advance()
        keys([(0x23,False)]);check('keyboard release retains joystick action',pads(),[16,0])
        s.inspect('input_joy',{'port':2,'red':False});advance();check('combined action released',pads(),[0,0])
        keys([(0x24,True),(0x39,True),(0x3a,True)]);check('other action buttons',pads(),[32,48])
        keys([(k,False) for k in (0x24,0x39,0x3a)])
        choose=0x01 if mode=='one' else 0x02
        keys([(choose,True)]);advance(1.4)
        check('main digit mode',mem('game_selected_mode')[0],0 if mode=='one' else 1)
        check('held selection accepted once',int.from_bytes(mem('game_accept_count',2),'big'),1)
        check('held selection waits',int.from_bytes(mem('game_lifecycle',2),'big'),3)
        legacy=0x46 if mode=='one' else 0x42
        keys([(legacy,True),(choose,False)])
        check('legacy alias keeps selection held',int.from_bytes(mem('game_lifecycle',2),'big'),3)
        s.inspect('input_key',{'rawkey':legacy,'action':'release'})
        completed=s.inspect('run_until',{'pc':base+symbols['presentation_commit_in_blank']})
        if completed['reason']!='target':raise RuntimeError(completed)
        time=completed['seconds']
        check('released selection plays',int.from_bytes(mem('game_lifecycle',2),'big'),1)
        # Compare only the unchanged original mode glyphs; enhanced title text
        # and animated ball pose do not manufacture or widen this oracle.
        mode_case=json.loads((ROOT/f'tests/cases/p1-accept-{mode}-player.json').read_text())
        source,_,reference_sha=mode_reference(mode_case,1299)
        expected_mode=map_source_palette(source,contract).crop((208,144,248,152))
        accepted=directory/'accepted-mode.png'
        s.inspect('run_until',{'vpos':0,'hpos':0})
        completed=s.inspect('run_until',{'vpos':0,'hpos':0})
        time=completed['seconds']
        check('first accepted court generation',int.from_bytes(mem('game_presented_generation',2),'big'),1)
        s.inspect('capture_screenshot',{'path':str(accepted)})
        with Image.open(accepted) as image:
            mode_picture=native_picture(image,contract).crop((208,144,248,152))
            check('accepted original mode label',compare(expected_mode,mode_picture),None)
        advance(.3)

        before=read_native_state(s,base,symbols);observations['before']=before.hex()
        keys([(0x20,True),(0x4e,True)]);advance(.15)
        after=read_native_state(s,base,symbols);observations['after']=after.hex()
        check('P1 moves left from actual initial X',after[0x4a]<before[0x4a],True)
        check('P2 assignment excludes one-player AI',mem('game_player_controls',2)[1],1 if mode=='two' else 0)
        if mode=='two':check('P2 moves right from actual initial X',after[0x46]>before[0x46],True)
        keys([(0x20,False),(0x4e,False),(0x22,True),(0x4f,True)]);advance(.15)
        reverse=read_native_state(s,base,symbols);observations['reverse']=reverse.hex()
        check('P1 reverses',reverse[0x4a]>after[0x4a],True)
        if mode=='two':check('P2 reverses',reverse[0x46]<after[0x46],True)
        keys([(0x22,False),(0x4f,False)]);check('gameplay release neutral',pads(),[0,0])
        waiting=read_native_state(s,base,symbols);observations['waiting']=waiting.hex()
        check('blue serve starts from wait',bool(waiting[0x38] and waiting[0x66]),False)
        keys([(0x24,True)]);advance(.8)
        flight=read_native_state(s,base,symbols);observations['flight']=flight.hex()
        check('P1 keyboard blue launches serve',bool(flight[0x38] and flight[0x66]),True)
        keys([(0x24,False)])
    target_log(directory)
    report={'passed':True,'subject':'maintained-native','interface_flavor':'enhanced','first_difference':None,
      'startup':'ordinary title','executable_sha256':digest(exe),'executable':str(exe),
      'screenshot':str(screenshot.relative_to(ROOT)),'accepted_mode_screenshot':str(accepted.relative_to(ROOT)),
      'accepted_mode_reference_sha256':reference_sha,'capture':str((directory/'emulator.log').relative_to(ROOT)),
      'checks':checks,'observations':observations,'mode':mode,
      'scope':'Ordinary physical raw keys/title/movement; whole-match restart and local exchanged-end ownership are separate'}
    atomic_json(ROOT/f'build/tests/interface-{mode}-enhanced-report.json',report)
    return report

def run_exchanged():
    from physical_input_reference import ownership_reference
    from native_tools import ASSEMBLER,run as assemble
    from evidence import compile_manifest
    source,_=ownership_reference()
    config,_=build(flavor='enhanced')
    directory=ROOT/'build/tests/interface-exchanged-enhanced';directory.mkdir(parents=True,exist_ok=True)
    initial=directory/'initial.bin';initial.write_bytes(bytes.fromhex(source['callbacks'][0]['post_tail_ram']))
    text=(ROOT/'amiga/gameplay_integration_probe.s').read_text()
    marker='initial_ram: incbin "build/translation/live-initial-ram.bin"'
    assert text.count(marker)==1
    wrapper=directory/'native-phase.s';wrapper.write_text(text.replace(marker,f'initial_ram: incbin "{initial}"'))
    exe=directory/'native-application';listing=directory/'native.lst'
    assemble([str(ASSEMBLER),'-Fhunkexe','-kick1hunks','-m68000','-DLIVE_PHASE_START=1',
              '-DENHANCED_INTERFACE=1','-L',str(listing),'-o',str(exe),str(wrapper)])
    compile_manifest(exe,listing);symbols=code_symbols(listing.read_text());checks=[];observations={}
    def check(label,actual,expected):
        checks.append({'label':label,'actual':actual,'expected':expected})
        if actual!=expected:raise AssertionError(checks[-1])
    with NativeControlSession(directory) as s:
        s.inspect('session_launch',{'binary':config['tools']['copperline'],'run':str(exe),
          'args':['--chipset','OCS','--video','PAL','--cpu','68000','--chip','512K','--slow','0','--fast','0','--noaudio',config['inputs']['amiga_rom']]})
        stop=s.inspect('run_until',{'seconds':30});assert stop['reason']=='loadseg'
        base=int(re.search(r'first hunk \$([0-9a-fA-F]+)',stop['detail'])[1],16);time=stop['seconds']
        def advance(seconds=.025):
            nonlocal time
            time+=seconds;s.inspect('run_until',{'seconds':time})
        def keys(events):
            for key,held in events:
                s.inspect('input_key',{'rawkey':key,'action':'press' if held else 'release'});advance()
        advance(.3)
        owner=bytes.fromhex(s.inspect('mem_read',{'addr':base+symbols['game_lower_owner'],'len':2})['data'])
        check('exchanged logical owners',list(owner),[1,0])
        before=read_native_state(s,base,symbols);observations['before']=before.hex()
        keys([(0x20,True),(0x4e,True)]);advance(.15);after=read_native_state(s,base,symbols);observations['after']=after.hex()
        check('P1 keyboard moves upper left',after[0x46]<before[0x46],True)
        check('P2 keyboard moves lower right',after[0x4a]>before[0x4a],True)
        keys([(0x20,False),(0x4e,False),(0x22,True),(0x4f,True)]);advance(.15)
        reverse=read_native_state(s,base,symbols);observations['reverse']=reverse.hex()
        check('P1 upper reverses',reverse[0x46]>after[0x46],True)
        check('P2 lower reverses',reverse[0x4a]<after[0x4a],True)
        keys([(0x22,False),(0x4f,False)])
        waiting=read_native_state(s,base,symbols);observations['waiting']=waiting.hex()
        check('blue serve starts from wait',bool(waiting[0x38] and waiting[0x66]),False)
        keys([(0x3c,True)]);advance(.8)
        flight=read_native_state(s,base,symbols);observations['flight']=flight.hex()
        check('P2 keypad blue launches its own serve',bool(flight[0x38] and flight[0x66]),True)
        keys([(0x3c,False)])
    target_log(directory)
    report={'passed':True,'subject':'maintained-native','interface_flavor':'enhanced','first_difference':None,
            'executable_sha256':digest(exe),'executable':str(exe),'checks':checks,'observations':observations,
            'initial_source_callback':source['initial_source_callback'],'startup':'captured exchanged-end phase',
            'scope':'One original-derived initial state, no intermediate expected writes; local keyboard ownership/serve, not ordinary reachability'}
    atomic_json(ROOT/'build/tests/interface-exchanged-enhanced-report.json',report)
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--mode',choices=('one','two'))
    parser.add_argument('--ownership',action='store_true')
    args=parser.parse_args()
    if bool(args.mode)==args.ownership:parser.error('Select one --mode or --ownership')
    name='exchanged' if args.ownership else args.mode
    path=ROOT/f'build/tests/interface-{name}-enhanced-report.json'
    return tracked_call([path],'physical' if args.ownership else 'interface-controls','maintained-native',
        'captured exchanged-end phase' if args.ownership else 'ordinary title',__file__,
        ['p3-input-p2-button2'] if args.ownership else ['p1-title',f'p1-accept-{args.mode}-player'],
        run_exchanged if args.ownership else lambda:run(args.mode),lambda path,report:[Path(report['executable'])])
if __name__=='__main__':
    print(json.dumps(main(),indent=2))
