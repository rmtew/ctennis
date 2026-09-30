"""Restore only the missing original title/choice media needed by CT-02."""
import configparser, hashlib, json, os, subprocess, zipfile
from pathlib import Path
from PIL import Image
from presentation_reference import ROOT, ACTIVE_AREA, decode_vdp
from run_translated_player_frame_probe import ROM_SHA256


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    config=configparser.ConfigParser(interpolation=None);config.read(ROOT/'config.local.ini')
    cartridge=Path(config['inputs']['cartridge']).read_bytes()
    assert hashlib.sha256(cartridge).hexdigest()==ROM_SHA256
    with zipfile.ZipFile(ROOT/'build/mame/roms/sg1000/champtns.zip') as archive:
        assert len(archive.namelist())==1 and archive.read(archive.namelist()[0])==cartridge
    for mode in ('one','two'):
        directory=ROOT/f'build/reference/mode-{mode}'
        runs=[]
        for run in ('a','b'):
            out=directory/run;out.mkdir(parents=True,exist_ok=True)
            command=[str(ROOT/'.tools/mame-0.289/mame.exe'),'sc3000','-noreadconfig','-hashpath','.tools/mame-0.289/hash','-rompath','build/mame/roms','-cart','champtns','-video','none','-sound','none','-skip_gameinfo','-nothrottle','-seconds_to_run','24','-autoboot_script','scripts/capture_mode_reference.lua']
            result=subprocess.run(command,cwd=ROOT,env={**os.environ,'CT_MODE':mode,'CT_MODE_OUTPUT':str(out)},capture_output=True,text=True,timeout=120)
            (out/'capture.log').write_text(result.stdout+result.stderr)
            if result.returncode or 'MODE_REFERENCE_COMPLETE' not in result.stdout: raise RuntimeError(result.stdout+result.stderr)
            for frame in (119,300,1299):
                stem=out/f'f{frame:05d}'
                size=tuple(map(int,stem.with_suffix('.raster').read_text().split()))
                image=Image.frombytes('RGBA',size,stem.with_suffix('.pixels').read_bytes(),'raw','BGRA').convert('RGB')
                decoded=decode_vdp(stem.with_suffix('.vram').read_bytes(),stem.with_suffix('.regs').read_bytes())
                if frame != 1299:
                    assert image.crop(ACTIVE_AREA).tobytes()==decoded.tobytes()
                # Accepted court includes a moving ball: end-of-frame VRAM may
                # follow its scanout. The rendered raster remains the oracle.
                image.save(stem.with_suffix('.png'))
            runs.append({p.name:digest(p) for p in out.iterdir() if p.suffix!='.log'})
        assert runs[0]==runs[1], 'Original mode captures must repeat exactly'
        (directory/'manifest.json').write_text(json.dumps({'mode':mode,'rom_sha256':ROM_SHA256,'emulator_sha256':digest(ROOT/'.tools/mame-0.289/mame.bin'),'repeat_identical':True,'capture_script_sha256':digest(ROOT/'scripts/capture_mode_reference.lua'),'files':runs[0],'frames':[119,300,1299]},indent=2)+'\n')
        print(f'{mode}: title/choice media verified, repeated identically')

if __name__=='__main__': main()
