"""Package the private maintained executable as a reproducible Kickstart1.x ADF.

Requires explicit prepare_native_assets.py output. No cartridge is packaged.
All output is ignored and must stay private because it contains original assets.
"""
import os,sys,json,hashlib,subprocess
from pathlib import Path
from native_tools import ROOT,run
from build_native_game import build
from native_evidence import atomic_json,tracked_call

OUT=ROOT/'build/amiga/ctennis-delivery'
def _package(flavor):
    out=ROOT/"build/amiga/interfaces"/flavor/"delivery"
    _,executable=build(flavor=flavor)
    out.mkdir(parents=True,exist_ok=True)
    startup=out/'startup-sequence';startup.write_bytes(b'ctennis\n')
    adf=out/f'ctennis-{flavor}.adf'
    adf.unlink(missing_ok=True) # format must start from a clean filesystem
    # Pinned local installation, no dependency on global PATH/site settings.
    env=dict(os.environ,PYTHONPATH=str(ROOT/'.tools/python'))
    command=[sys.executable,'-m','amitools.tools.xdftool','-f',str(adf),
             'format','CTENNIS','+', 'makedir','S','+',
             'write',str(startup),'S/startup-sequence','+',
             'write',str(executable),'ctennis','+', 'boot','install','boot1x']
    r=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,text=True)
    if r.returncode:raise RuntimeError(f"xdftool exit{r.returncode}: {r.stdout} {r.stderr}")
    # Pinned0.8.1's `time` CLI treats its successful None return as failure.
    # Use its supported filesystem API to freeze all metadata, no byte patch.
    sys.path.insert(0,str(ROOT/'.tools/python'))
    from amitools.fs.blkdev.BlkDevFactory import BlkDevFactory
    from amitools.fs.ADFSVolume import ADFSVolume
    from amitools.fs.FSString import FSString
    from amitools.fs.TimeStamp import TimeStamp
    stamp=TimeStamp();assert stamp.parse('01.01.2000 00:00:00')
    device=BlkDevFactory().open(str(adf),read_only=False)
    volume=ADFSVolume(device);volume.open()
    for name in ('S','S/startup-sequence','ctennis'):
        volume.get_path_name(FSString(name)).change_mod_ts(stamp)
    embedded=volume.get_path_name(FSString('ctennis')).get_file_data()
    if embedded!=executable.read_bytes():raise ValueError('ADF executable differs from maintained build')
    volume.change_create_ts(stamp);volume.change_mod_ts(stamp);volume.change_disk_ts(stamp)
    volume.close();device.close()
    report={'subject':'maintained-native','interface_flavor':flavor,'passed':True,'embedded_executable_verified':True,'executable':str(executable.relative_to(ROOT)),
            'executable_sha256':hashlib.sha256(executable.read_bytes()).hexdigest(),
            'adf':str(adf.relative_to(ROOT)),'adf_sha256':hashlib.sha256(adf.read_bytes()).hexdigest(),
            'startup_sequence':str(startup.relative_to(ROOT)),
            'amitools_version':'0.8.1','command':command,'output':r.stdout+r.stderr,
            'scope':'Package only; cold boot and independent target not implied'}
    atomic_json(out/'package-report.json',report)
    return report
def package(self_test=False, flavor="enhanced"):
    out=ROOT/"build/amiga/interfaces"/flavor/"delivery"
    def action():
        first=_package(flavor)
        if self_test:
            second=_package(flavor)
            if (first['adf_sha256']!=second['adf_sha256'] or first['executable_sha256']!=second['executable_sha256']):
                raise ValueError('Clean rebuild is not byte-identical')
            second['reproducibility']={'two_clean_builds':True,'first_adf_sha256':first['adf_sha256'],
                                       'second_adf_sha256':second['adf_sha256']}
            atomic_json(out/'package-report.json',second)
            return second
        return first
    return tracked_call([out/'package-report.json'],'native-package','maintained-native','package only',
                        'scripts/build_native_adf.py',None,action,
                        lambda path,report:[ROOT/report['executable']])

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--self-test',action='store_true')
    parser.add_argument('--interface', choices=('enhanced',), default='enhanced')
    args=parser.parse_args()
    print(json.dumps(package(args.self_test,args.interface),indent=2))
