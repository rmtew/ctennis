"""Convert the private original title tile asset to native Amiga bitplanes."""
import hashlib, json
from generate_amiga_sprite_probe import PALETTE
from run_translated_prng_probe import ROOT


def generate():
    source=ROOT/'tests/reference/presentation/one-player-match/f00119.vram'
    if source.exists():
        manifest=json.loads((source.parent/'manifest.json').read_text())
        sample=next(row for row in manifest['samples'] if row['frame']==119)
        expected=sample['hardware_sha256']['vram']
    else:
        source=ROOT/'build/reference/mode-one/a/f00119.vram'
        manifest=json.loads((source.parent.parent/'manifest.json').read_text())
        if not manifest['repeat_identical']:
            raise ValueError('Original title capture was not repeated')
        expected=manifest['files'][source.name]
    vram=source.read_bytes()
    if hashlib.sha256(vram).hexdigest()!=expected:
        raise ValueError('Private title asset differs from verified original capture')
    out=ROOT/'build/amiga/title';out.mkdir(parents=True,exist_ok=True)
    planes=[bytearray(32*192) for _ in range(4)]
    for y in range(192):
        bank=(y//64)*0x800
        for x in range(256):
            tile=vram[0x3c00+(y//8)*32+x//8]
            pattern=vram[0x2000+bank+tile*8+y%8]
            colour=vram[bank+tile*8+y%8]
            index=(colour>>4 if pattern&(128>>(x%8)) else colour&15)
            for n,p in enumerate(planes):
                if index&(1<<n): p[y*32+x//8]|=128>>(x%8)
    for n,p in enumerate(planes): (out/f'plane{n}.bin').write_bytes(p)
    commands=['title_copper:', '        dc.w $008e,$2c81,$0090,$ecc1,$0092,$0038,$0094,$00b0',
              '        dc.w $0100,$4200,$0102,0,$0104,0,$0108,0,$010a,0']
    for n in range(4): commands.append(f'title_pointer{n}: dc.w ${0xe0+4*n:04x},0,${0xe2+4*n:04x},0')
    for n in range(16): commands.append(f'        dc.w ${0x180+2*n:04x},${PALETTE.get(n,0):03x}')
    commands.append('        dc.w $ffff,$fffe')
    for n in range(4): commands.append(f'title_plane{n}: incbin "build/amiga/title/plane{n}.bin"')
    (out/'display.i').write_text('\n'.join(commands)+'\n')

if __name__=='__main__': generate()
