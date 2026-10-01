"""Ordinary native title and physical mode choice, through completed presentation."""
import argparse, configparser, hashlib, json, re
from pathlib import Path
from PIL import Image
from copperline_test_session import NativeControlSession
from run_presentation_tests import ROOT, digest, source_picture, map_source_palette, native_picture, compare
from presentation_reference import ACTIVE_AREA
from capture_native_presentation import code_symbols
from build_native_game import build, module_hashes
from evidence import tracked_call, compile_manifest
from run_translated_prng_probe import ASSEMBLER, run as command
CASES=('p1-accept-one-player','p1-accept-two-player')


def reference(case, frame):
    """Use retained source media, or the bounded replacement captured on this host."""
    if (ROOT/case['reference']).exists():
        root=json.loads((ROOT/case['reference']).read_text())
        if not root['source_media_checks_passed'] or root['recipe_sha256']!=digest(ROOT/'tests/cases/presentation.json'):
            raise ValueError('Original presentation contract changed')
        parent=root['references'][case['source_case']]
        manifest_path=(ROOT/case['reference']).parent/parent['manifest']
        if digest(manifest_path)!=parent['manifest_sha256']: raise ValueError('Original media manifest changed')
        media=manifest_path.parent
        manifest=json.loads((media/'manifest.json').read_text())
        sample=next(row for row in manifest['samples'] if row['frame']==frame)
        for ext in ('ram','vram','regs'):
            if digest(media/f'f{frame:05d}.{ext}')!=sample['hardware_sha256'][ext]:
                raise ValueError('Original mode hardware changed')
        image=Image.open(media/f'f{frame:05d}.png').convert('RGB')
        if hashlib.sha256(image.tobytes()).hexdigest()!=sample['rgb_sha256']:
            raise ValueError('Original mode pixels changed')
    else:
        mode='two' if case['source_case'].startswith('two') else 'one'
        root=ROOT/f'build/reference/mode-{mode}'
        manifest=json.loads((root/'manifest.json').read_text());media=root/'a'
        if not manifest['repeat_identical']: raise ValueError('Unverified original repeat')
        for name, sha in manifest['files'].items():
            if digest(media/name)!=sha: raise ValueError('Original mode media changed')
        image=Image.open(media/f'f{frame:05d}.png').convert('RGB')
    return image.crop(ACTIVE_AREA), (media/f'f{frame:05d}.ram').read_bytes(), digest(media/f'f{frame:05d}.png')


def capture(case, kind=None):
    config, ordinary=build()
    directory=ROOT/f'build/tests/{case["name"]}-{kind or "normal"}';directory.mkdir(parents=True,exist_ok=True)
    exe=directory/'native-application'
    command([str(ASSEMBLER),'-Fhunkexe','-kick1hunks','-m68000','-L',str(directory/'native.lst'),'-o',str(exe),case['native_source']])
    if digest(exe)!=digest(ordinary): raise ValueError('Mode test differs from ordinary executable')
    compile_manifest(exe,directory/'native.lst')
    compiled_modules=module_hashes()
    if kind=='sprite':
        raw=exe.read_bytes();old=bytes.fromhex('06400080')
        if raw.count(old)!=1: raise ValueError('Sprite mutation anchor changed')
        exe.write_bytes(raw.replace(old,bytes.fromhex('06400081')))
    elif kind=='mode':
        # Actual compiled Tab dispatch fault, not a changed expectation.
        path=ROOT/'amiga/game/menu.s';original=path.read_bytes()
        try:
            anchor=b'        moveq   #1,d0' if case['expected_mode_flags'] else b'        moveq   #0,d0'
            if original.count(anchor)!=1: raise ValueError('Mode mutation anchor changed')
            path.write_bytes(original.replace(anchor,b'        moveq   #0,d0' if case['expected_mode_flags'] else b'        moveq   #1,d0'))
            compiled_modules=module_hashes()
            command([str(ASSEMBLER),'-Fhunkexe','-kick1hunks','-m68000','-L',str(directory/'native.lst'),'-o',str(exe),case['native_source']])
        finally: path.write_bytes(original)
    symbols=code_symbols((directory/'native.lst').read_text())
    contract=json.loads((ROOT/'tests/cases/presentation.json').read_text())
    _, pre, _=reference(case,119)
    title, _, title_sha=reference(case,300)
    expected_title=map_source_palette(title,contract)
    if pre[0x3a] or pre[0x3b]: raise ValueError('Pre-choice reference is active')
    rows=[];events=[];differences=[]
    with NativeControlSession(directory) as s:
        launch=s.inspect('session_launch',{'binary':config['tools']['copperline'],'run':str(exe),'args':['--chipset','OCS','--video','PAL','--cpu','68000','--chip','512K','--slow','0','--fast','0','--noaudio',config['inputs']['amiga_rom']]})
        stop=s.inspect('run_until',{'seconds':30})
        if stop['reason']!='loadseg': raise RuntimeError(stop)
        base=int(re.search(r'first hunk \$([0-9A-Fa-f]+)',stop['detail'])[1],16);origin=stop['seconds']
        def mem(name,length=2):
            return int(s.inspect('mem_read',{'addr':base+symbols[name],'len':length})['data'],16)
        def state():
            return bytes.fromhex(s.inspect('mem_read',{'addr':base+symbols['virtual_memory']+0xc000,'len':256})['data'])
        def observe(label):
            stop=s.inspect('run_until',{'vpos':0,'hpos':0})
            if stop['reason']!='target': raise RuntimeError(stop)
            path=directory/(label+'.png');s.inspect('capture_screenshot',{'path':str(path)})
            with Image.open(path) as im: actual=native_picture(im,contract)
            ram=state()
            row={'stage':label,'lifecycle':mem('game_lifecycle'),'accepted_count':mem('game_accept_count'),'presented_generation':mem('game_presented_generation'),'selection_keys':mem('game_selection_keys',1),'mode_flags':ram[0x3d]&0x94,'player_phases':list(ram[0x3a:0x3c]),'source_rate_callbacks':mem('simulation_updates'),'pixel_sha256':hashlib.sha256(actual.tobytes()).hexdigest(),'stop':stop}
            rows.append(row);return row,actual
        s.inspect('run_until',{'seconds':origin+case.get('seconds_after_load',2)})
        row,actual=observe('before-selection')
        delta=compare(expected_title,actual,'stable-title')
        if delta: differences.append(delta)
        if row['lifecycle']!=2 or row['accepted_count'] or any(row['player_phases']):
            differences.append({'field':'title waits without gameplay','actual':row})
        if case['name']!='p1-title':
            source, wanted, reference_sha=reference(case,1299)
            expected=map_source_palette(source,contract)
            if wanted[0x3d]&0x94!=case['expected_mode_flags']: raise ValueError('Original mode disagrees with recipe')
            for action in ('press','release'):
                events.append({'action':action,'rawkey':case['rawkey'],'response':s.inspect('input_key',{'rawkey':case['rawkey'],'action':action})})
                if action=='press':
                    s.inspect('run_until',{'seconds':origin+7})
                    held,_=observe('held-selection')
                    if held['accepted_count']!=1 or held['lifecycle']!=3: differences.append({'field':'choice latched once while held','actual':held})
            # Observe the first complete court generation, before looking for the
            # retained ball-bob pose. It must belong to this physical choice.
            s.inspect('run_until',{'pc':base+symbols['presentation_commit_in_blank']})
            s.inspect('run_until',{'vpos':0,'hpos':0})
            first,first_picture=observe('first-accepted-generation')
            if first['presented_generation']!=1 or first['mode_flags']!=case['expected_mode_flags']:
                differences.append({'field':'first accepted generation owns selected mode','actual':first})
            # The source frame 1299 is in serve-wait with an animated ball. Align
            # only that observed pose; never inject state or choose a regime.
            # All pixels and all other required outcomes still compare exactly.
            mode_region=(208,144,248,152)
            delta=compare(expected.crop(mode_region), first_picture.crop(mode_region), 'first-accepted-mode-label')
            if delta: differences.append(delta)
            def ball_pose(picture):
                # White ball above its shadow, clear of either player/scoreboard.
                return tuple(y for y in range(152,178)
                             if any(picture.getpixel((x,y))==(255,255,255)
                                    for x in range(208,224)))
            wanted_pose=ball_pose(expected)
            if len(wanted_pose)!=2: raise ValueError('Original serve ball pose missing')
            matched=False
            for index in range(150):
                row,actual=observe('accepted-mode')
                if ball_pose(actual)==wanted_pose:
                    matched=True
                    delta=compare(expected,actual,'accepted-mode-viewport')
                    if delta: differences.append(delta)
                    break
                s.inspect('run_until',{'frame':row['stop']['frame']+1})
            if not matched: differences.append({'field':'retained serve-wait pose not reached','expected':wanted_pose})
            if row['accepted_count']!=1 or row['mode_flags']!=case['expected_mode_flags'] or row['player_phases'][0]!=0x40:
                differences.append({'field':'selected match waits for serve','actual':row})
            # Re-press a selection key during play: must not restart the match.
            s.inspect('input_key',{'rawkey':case['rawkey'],'action':'press'})
            s.inspect('run_until',{'frame':row['stop']['frame']+4})
            s.inspect('input_key',{'rawkey':case['rawkey'],'action':'release'})
            if mem('game_accept_count')!=1: differences.append({'field':'selection restarted live match'})
            # CT-03 ordinary-path proof: movement must change from its observed
            # start, reverse, and stop; connector 1 must not take over the AI.
            s.inspect('input.set_port',{'port':1,'device':'joystick'})
            def hold(p1,p2,frames=12):
                s.inspect('run_until',{'pc':base+symbols['simulation_update']})
                s.inspect('input_joy',{'port':2,**p1})
                s.inspect('input_joy',{'port':1,**p2})
                for _ in range(frames):
                    s.inspect('run_until',{'pc':base+symbols['game_observe_pre_tail']})
                    s.inspect('run_until',{'pc':base+symbols['simulation_update']})
                return state()
            before=state()
            left=hold({'left':True},{'right':True})
            right=hold({'right':True},{'left':True})
            released=hold({}, {})
            two=bool(case['expected_mode_flags'])
            controls={'stage':'ordinary-physical-controls','lower_x':[r[0x4a] for r in (before,left,right,released)],
                      'upper_x':[r[0x46] for r in (before,left,right,released)],
                      'players':2 if two else 1}
            rows.append(controls)
            if not left[0x4a]<before[0x4a] or not right[0x4a]>left[0x4a] or released[0x4a]!=right[0x4a]:
                differences.append({'field':'lower physical move/reverse/release','actual':controls})
            if two:
                if not left[0x46]>before[0x46] or not right[0x46]<left[0x46] or released[0x46]!=right[0x46]:
                    differences.append({'field':'independent upper move/reverse/release','actual':controls})
            elif any(r[0x46]!=before[0x46] for r in (left,right,released)):
                differences.append({'field':'connector 1 stole AI receiver','actual':controls})
            # Connector 1 action alone cannot start player 1's lower serve.
            other=hold({}, {'red':True},6)
            if other[0x3a]!=0x40: differences.append({'field':'wrong pad starts lower serve','actual':other[0x3a]})
            hold({'red':True},{},6)
            after=state()
            if after[0x3a]!=0x20: differences.append({'field':'physical fire starts serve','actual':after[0x3a]})
            s.inspect('input_joy',{'port':2,'red':False})
        else: reference_sha=title_sha
        log=Path(launch['log']).read_text()
        (directory/'copperline.log').write_text(log)
        for marker in ('cpu=M68000','chip_ram=512K','fast_ram=0K','slow_ram=0K','chipset=Ocs','video=Pal','Kickstart 1.3'):
            if marker not in log: raise ValueError(marker)
    return {'case':case['name'],'passed':not differences,'first_difference':differences[0] if differences else None,'differences':differences,'observations':rows,'physical_key_events':events,'executable_sha256':digest(exe),'native_modules':compiled_modules,'compiled_fault':kind,'emulator_sha256':digest(Path(config['tools']['copperline'])),'kickstart_sha256':digest(Path(config['inputs']['amiga_rom'])),'case_sha256':digest(ROOT/f'tests/cases/{case["name"]}.json'),'source_frame':300 if case['name']=='p1-title' else 1299,'reference_sha256':reference_sha,'source_initialization':'Ordinary title boot and runtime initialization; no captured RAM injection.','scope':case['contract']}


def _run(case_name,self_test=False):
    case=json.loads((ROOT/f'tests/cases/{case_name}.json').read_text())
    if case_name in CASES:
        expected=('one-player-match',0x46,0) if case_name==CASES[0] else ('two-player-match',0x42,128)
        if (case['source_case'],case['rawkey'],case['expected_mode_flags'])!=expected or case['checkpoint']!='accepted-mode':
            raise ValueError('Physical choice contract changed; revalidate original mapping')
    normal=capture(case);mutants=[]
    if self_test and case_name=='p1-title':
        contract=json.loads((ROOT/'tests/cases/presentation.json').read_text())
        picture,_,_=reference(case,300);expected=map_source_palette(picture,contract)
        changed=expected.copy();changed.putpixel((0,0),(255,255,255))
        if compare(expected,expected) is not None or compare(expected,changed) is None:
            raise AssertionError('Title pixel comparator control failed')
        normal['comparator_mutation_detected']=True
    if self_test and normal['passed'] and case_name!='p1-title':
        # Two existing fault kinds, now checked against full green acceptance.
        for kind in ('sprite','mode'):
            changed=capture(case,kind)
            if changed['passed']: raise AssertionError(f'Actual {kind} mutation escaped')
            mutants.append({'kind':kind,'detected':True,'first_difference':changed['first_difference']})
        build()  # restore ordinary executable after compiled variants
    normal.update(self_test=self_test,hardware_mutations=mutants)
    (ROOT/f'build/tests/{case_name}-report.json').write_text(json.dumps(normal,indent=2)+'\n')
    print(json.dumps({'case':case_name,'passed':normal['passed'],'differences':normal['differences'],'mutants':len(mutants)}),flush=True)
    return normal['passed']

def run(case_name,self_test=False):
    return tracked_call([ROOT/f'build/tests/{case_name}-report.json'], 'mode', 'maintained-native',
                        'ordinary title', 'scripts/run_mode_selection_tests.py', case_name,
                        lambda: _run(case_name,self_test),
                        lambda path, report: [ROOT/f'build/tests/{case_name}-normal/native-application'])

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--case',choices=('p1-title',)+CASES,required=True);parser.add_argument('--self-test',action='store_true');args=parser.parse_args();raise SystemExit(0 if run(args.case,args.self_test) else 1)
