"""Focused stripped-ADF boot and independent visible release-number raster.

No builder or physical gameplay schedule; run after reproducible packaging.
"""
import argparse,json,subprocess,traceback
from uuid import uuid4
from native_tools import ROOT,emulator_config
from native_evidence import ReportRun,inputs_for,snapshot,digest
from build_match_core import load_image
from native_hunk import loaded_hunks
from native_identity_raster import assert_title_raster,assert_menu_selection_raster
from copperline_test_session import NativeControlSession
from run_enhanced_menu_tests import execution_subject

def run(standard,version):
    attempt=ROOT/'build/tests/release-version-boot'/uuid4().hex;attempt.mkdir(parents=True)
    output=attempt/'report.json';tx=ReportRun([output],'native-menu','maintained-native','Release version boot only')
    product=ROOT/'build/amiga/interfaces/enhanced';delivery=product/'delivery'
    package=json.loads((delivery/'package-report.json').read_text());development=product/'baseline-rally'
    release,debug=execution_subject(development,package);adf=ROOT/package['adf']
    assert (ROOT/'amiga/VERSION').read_text().strip()==version
    label=(ROOT/'build/native/version.bin').read_bytes().rstrip(b'\0').decode('ascii');revision=label.split()[1]
    assert label=='BUILD '+revision
    paths,tools=inputs_for('native-menu',__file__)
    tx.meta.update(files=snapshot(paths|{adf,release,development,product/'native.lst',delivery/'package-report.json',delivery/'baseline-rally.compile.json'}),tools=tools,actual_target=dict(tx.meta['target'],video=standard),commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip())
    report=dict(passed=False,standard=standard,release_version=version,build_revision=revision,adf_sha256=digest(adf),executable_sha256=digest(release),development_sha256=digest(development),debug_symbol_source=debug,scope=__doc__)
    try:
        cfg=emulator_config()
        with NativeControlSession(attempt) as session:
            session.inspect('session_launch',dict(binary=cfg['tools']['copperline'],args=['--chipset','OCS','--video',standard,'--cpu','68000','--chip','512K','--slow','0','--fast','0','--noaudio','--floppy-drives','1','--floppy-speed','100',cfg['inputs']['amiga_rom']]))
            session.inspect('media.floppy.insert',dict(drive=0,path=str(adf),write_protected=True))
            bp=session.inspect('break.add',dict(kind='loadseg',name='baseline-rally'))
            position=session.inspect('run_until',dict(seconds=120));assert position['reason']=='loadseg',position
            session.inspect('break.remove',dict(id=bp['id']));segments=session.inspect('segments.list')['current']
            _,symbols=load_image(development,hunk_addresses=[x['start'] for x in segments])
            def raw(address,size):return bytes.fromhex(session.inspect('mem.read',dict(addr=address,len=size))['data'])
            report['loaded_hunks']=loaded_hunks(release,segments,raw)
            session.inspect('run_until',dict(seconds=position['seconds']+2))
            assert int.from_bytes(raw(symbols['game_lifecycle'],2),'big')==2
            assert raw(symbols['game_title_display'],1)==b'\xff'
            photo=attempt/'title.png';session.inspect('capture.screenshot',dict(path=str(photo)))
            report['rasters']=[assert_title_raster(photo),assert_menu_selection_raster(photo,0,1,build_hash=revision,standard=standard,release_version=version)]
            report['photo']=str(photo);report['photo_sha256']=digest(photo)
        report['passed']=True
    except BaseException as error:report.update(error=str(error),traceback=traceback.format_exc())
    tx.finalize(output,report,compiled=[json.loads((delivery/'baseline-rally.compile.json').read_text())],artifacts=[p for p in attempt.iterdir() if p.is_file() and p!=output])
    print(json.dumps(dict(passed=report['passed'],report=str(output),standard=standard)))
    return report['passed']

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--release-version',required=True);args=parser.parse_args()
    results=[run(standard,args.release_version) for standard in ('PAL','NTSC')]
    raise SystemExit(0 if all(results) else 1)
