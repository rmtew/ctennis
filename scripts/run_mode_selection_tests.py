"""Fresh native application selection via physical keys; no selected-mode injection."""
import argparse,configparser,hashlib,json,re
from pathlib import Path
from PIL import Image
from copperline_test_session import CopperlineSession
from run_presentation_tests import ROOT,build_native,digest,source_picture,map_source_palette,native_picture,compare
from capture_native_presentation import code_symbols
CASES=('p1-accept-one-player','p1-accept-two-player')

def capture(case,kind=None):
    config=configparser.ConfigParser(interpolation=None);config.read(ROOT/'config.local.ini',encoding='utf-8')
    directory=ROOT/f'build/tests/{case["name"]}-{kind or "normal"}';directory.mkdir(parents=True,exist_ok=True)
    # Both choices start the SAME current ordinary application, never a selected R2 state.
    build_case={**case,'source_case':'one-player-match'}
    def mutate(text):
        marker='        lea     pointer_sources(pc),a0'
        if text.count(marker)!=1:raise ValueError('Startup mutation anchor changed')
        return text.replace(marker,'        ori.b   #$80,$3d(a5)\n'+marker)
    exe=build_native(build_case,directory)
    if kind=='mode':
        # Private compiled variant of the maintained source; keep the initial fixture unchanged.
        source=(ROOT/case['native_source']).read_text();private=directory/'mode-mutant.s';private.write_text(mutate(source))
        build_case['native_source']=str(private.relative_to(ROOT));exe=build_native(build_case,directory)
    elif kind=='sprite':
        raw=exe.read_bytes();old=bytes.fromhex('0640006c')
        if raw.count(old)!=1:raise ValueError('Sprite origin mutation anchor changed')
        exe.write_bytes(raw.replace(old,bytes.fromhex('0640006d')))
    symbols=code_symbols((directory/'native.lst').read_text())
    ctl=Path(config['tools']['copperline']).with_name('copperline-ctl.exe');rows=[];events=[]
    contract=json.loads((ROOT/'tests/cases/presentation.json').read_text())
    source,frame,reference_sha=source_picture(case);expected=map_source_palette(source,contract)
    media=ROOT/'tests/reference/presentation'/case['source_case']
    manifest=json.loads((media/'manifest.json').read_text());sample=next(row for row in manifest['samples'] if row['frame']==frame)
    ram=media/f'f{frame:05d}.ram'
    if digest(ram)!=sample['hardware_sha256']['ram'] or (ram.read_bytes()[0x3d]&0x94)!=case['expected_mode_flags']:
        raise ValueError('Accepted mode flags differ from independent original hardware')
    pre=media/'f00119.ram';pre_sample=next(row for row in manifest['samples'] if row['frame']==119)
    if digest(pre)!=pre_sample['hardware_sha256']['ram']:
        raise ValueError('Original pre-choice state changed')
    pre_ram=pre.read_bytes()
    if not pre_ram[0x3d]&4 and (pre_ram[0x3a] or pre_ram[0x3b]):
        raise ValueError('Original pre-choice snapshot contains active gameplay')
    with CopperlineSession(ctl,ROOT) as s:
        launch=s.inspect('session_launch',{'factory':True,'model':'A500','binary':config['tools']['copperline'],'run':str(exe),'args':['--chipset','OCS','--video','PAL','--cpu','68000','--chip','512K','--slow','0','--fast','0','--noaudio',config['inputs']['amiga_rom']]})
        stop=s.inspect('run_until',{'seconds':30,'wait_ms':50000})
        if stop['reason']!='loadseg':raise RuntimeError(stop)
        base=int(re.search(r'first hunk \$([0-9A-Fa-f]+)',stop['detail']).group(1),16);origin=stop['seconds']
        for label,elapsed,action in [('before-selection',2,'press'),('held-selection',7,'release'),('accepted-mode',22,None)]:
            stop=s.inspect('run_until',{'seconds':origin+elapsed,'wait_ms':50000})
            if stop['reason']!='target' or stop.get('bridge'):raise RuntimeError(stop)
            stop=s.inspect('run_until',{'vpos':0,'hpos':0,'wait_ms':50000})
            if stop['reason']!='target' or stop.get('bridge') or stop['vpos']!=0:raise RuntimeError(stop)
            mode=int(s.inspect('mem_read',{'addr':base+symbols['virtual_memory']+0xc03d,'len':1})['data'],16)&0x94
            count=int(s.inspect('mem_read',{'addr':base+symbols['simulation_updates'],'len':2})['data'],16)
            phases=list(bytes.fromhex(s.inspect('mem_read',{'addr':base+symbols['virtual_memory']+0xc03a,'len':2})['data']))
            active=not bool(mode&4) and any(phases)
            fields=s.inspect('mem_read',{'addr':base+symbols['field_values'],'len':6})['data']
            path=directory/(label+'.png');image=s.inspect('capture_screenshot',{'path':str(path)})
            with Image.open(path) as im:actual=native_picture(im,contract)
            pixel=compare(expected,actual,'accepted-mode-viewport') if label=='accepted-mode' else None
            rows.append({'stage':label,'source_rate_callbacks':count,'player_phases':phases,'active_gameplay':active,'mode_flags':mode,'fields':fields,'pixel_difference':pixel,'pixel_sha256':hashlib.sha256(actual.tobytes()).hexdigest(),'stop':stop,'capture':image})
            if action:events.append({'stage':label,'request':{'rawkey':case['rawkey'],'action':action},'response':s.inspect('input_key',{'rawkey':case['rawkey'],'action':action})})
        log=Path(launch['log']).read_text(encoding='utf-8',errors='replace')
        for marker in ('cpu=M68000','cpu_clock=7.09MHz','chip_ram=512K','fast_ram=0K','slow_ram=0K','chipset=Ocs','video=Pal','Kickstart 1.3'):
            if marker not in log:raise ValueError(marker)
    differences=[]
    if not rows[-1]['active_gameplay']:
        differences.append({'update':0,'boundary':'accepted-mode','field':'gameplay started after choice','expected':True,'actual':False})
    if rows[0]['active_gameplay']:
        differences.append({'update':0,'boundary':'before-mode-selection','field':'gameplay started before choice','expected':False,'actual':True})
    if rows[-1]['mode_flags']!=case['expected_mode_flags']:
        differences.append({'update':0,'boundary':'accepted-mode','field':'mode flags','expected':case['expected_mode_flags'],'actual':rows[-1]['mode_flags']})
    if rows[-1]['pixel_difference']:differences.append(rows[-1]['pixel_difference'])
    # Exclude scheduler-dependent callback counts and stop metadata from known-red acceptance.
    # The actual counts remain evidence; all output values and pixel hashes are pinned.
    observations=[{k:v for k,v in row.items() if k in ('stage','mode_flags','player_phases','active_gameplay','fields','pixel_difference','pixel_sha256')} for row in rows]
    return {'case':case['name'],'passed':not differences,'first_difference':differences[0] if differences else None,'differences':differences,'baseline_observations':observations,'observations':rows,'physical_key_events':events,'executable_sha256':digest(exe),'native_source_sha256':digest(ROOT/case['native_source']),'emulator_sha256':digest(Path(config['tools']['copperline'])),'bridge_sha256':digest(ctl),'kickstart_sha256':digest(Path(config['inputs']['amiga_rom'])),'source_prechoice_ram_sha256':digest(pre),'source_mode_ram_sha256':digest(ram),'reference_sha256':reference_sha,'source_frame':frame,'case_sha256':digest(ROOT/f'tests/cases/{case["name"]}.json'),'source_initialization':'Current ordinary R1 application initialization, identical for both requested choices; no R2 fixture or selected-mode RAM writes.','scope':case['contract']}

def run(case_name,self_test=False):
    case=json.loads((ROOT/f'tests/cases/{case_name}.json').read_text())
    expected=('one-player-match',0x46,0) if case_name==CASES[0] else ('two-player-match',0x42,128)
    if (case['source_case'],case['rawkey'],case['expected_mode_flags'])!=expected or case['checkpoint']!='accepted-mode':
        raise ValueError('Physical choice contract changed; revalidate original key/accepted-mode mapping')
    path=ROOT/f'build/tests/{case_name}-report.json';path.unlink(missing_ok=True)
    normal=capture(case);mutants=[]
    if self_test:
        for kind in ('sprite','mode'):
            changed=capture(case,kind)
            if changed['baseline_observations']==normal['baseline_observations']:raise AssertionError(f'Actual {kind} mutation escaped')
            if changed['first_difference']!=normal['first_difference']:raise AssertionError('Mutation did not preserve early failure')
            from run_test_suite import classify,failure_check_digest
            policy={'signature':normal['first_difference'],'complete_checks_sha256':failure_check_digest(normal)}
            assert classify(normal,policy)=='known-red' and classify(changed,policy)=='unexpected-red'
            mutants.append({'kind':kind,'detected':True,'classification':'unexpected-red','report':changed})
    if self_test:
        repeated=capture(case)
        if repeated['baseline_observations']!=normal['baseline_observations'] or repeated['first_difference']!=normal['first_difference']:
            raise AssertionError('Ordinary native outputs changed on repeat')
        normal['repeat_identical_observations']=True
        normal['repeat_execution']={'executable_sha256':repeated['executable_sha256'],'observations':repeated['observations'],'physical_key_events':repeated['physical_key_events']}
    normal.update(self_test=self_test,hardware_mutations=mutants);path.write_text(json.dumps(normal,indent=2)+'\n')
    print(json.dumps({'case':case_name,'passed':normal['passed'],'differences':normal['differences'],'mutants':len(mutants)}),flush=True)
    return normal['passed']

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--case',choices=CASES,required=True);parser.add_argument('--self-test',action='store_true');args=parser.parse_args();raise SystemExit(0 if run(args.case,args.self_test) else 1)
