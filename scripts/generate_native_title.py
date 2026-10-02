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
    # Original output is byte-preserved; enhanced artwork is a separate offline
    # product asset. The logo/copyright above the instruction rows is retained.
    original = [bytes(p) for p in planes]
    glyphs = {c: list(vram[0x3000 + n*8:0x3008 + n*8])
              for n,c in enumerate("012389=/©ABCDEFGHIKLMNOPRSTUVY", 0x44)}
    additions = json.loads((ROOT/'assets/interface/small-font-additions.json').read_text())
    if any(len(rows)!=8 or any(type(b)!=int or not 0<=b<=255 for b in rows)
           for rows in additions.values()):
        raise ValueError('Small font glyph must contain eight byte rows')
    glyphs.update(additions);glyphs[' '] = [0]*8
    lines = ["1 ONE PLAYER / 2 TWO PLAYERS",
             "P1 WASD MOVE  RED F BLUE G",
             "P2 ARROWS MOVE RED . BLUE /",
             "KEYPAD 8/4/2/6 MOVE RED0 BLUE.",
             "JOYSTICKS P1 PORT2 P2 PORT1",
             "DELETE / TAB ALSO SELECT"]
    for p in planes: p[144*32:] = bytes(48*32)
    for row,line in enumerate(lines):
        if len(line)>32: raise ValueError('Title instruction exceeds picture width')
        x=(32-len(line))//2
        for col,c in enumerate(line):
            for dy,bits in enumerate(glyphs[c]):
                for p in planes: p[(144+row*8+dy)*32+x+col]=bits
    # Private native font: glyph bytes are offline assets, never committed.
    font = bytearray(128*8)
    for c, rows in glyphs.items():
        if ord(c)<128: font[ord(c)*8:ord(c)*8+8] = bytes(rows)
    (out/'enhanced').mkdir(parents=True,exist_ok=True)
    (out/'enhanced/font.bin').write_bytes(font)
    recording = json.loads((ROOT/'assets/interface/demo-inputs.json').read_text())
    packets = recording['packets']
    if sum(n for n, mask in packets) != recording['frames'] or any(
            type(n) is not int or not 0<n<65536 or type(mask) is not int or not 0<=mask<64
            for n, mask in packets):
        raise ValueError('Invalid ordinary physical input recording')
    (out/'enhanced/demo-inputs.i').write_text('ui_demo_packets:\n'+''.join(
        f'        dc.w {n},{mask}\n' for n,mask in packets)+'        dc.w 0\n')
    for flavor, data in [('original', original), ('enhanced', planes)]:
        directory=out if flavor=='original' else out/'enhanced'
        directory.mkdir(parents=True,exist_ok=True)
        for n,p in enumerate(data): (directory/f'plane{n}.bin').write_bytes(p)
        start,stop=(0x38,0xb0) if flavor=='original' else (0x48,0xc0)
        commands=['title_copper:', f'        dc.w $008e,$2c81,$0090,$ecc1,$0092,${start:04x},$0094,${stop:04x}',
                  '        dc.w $0100,$4200,$0102,0,$0104,0,$0108,0,$010a,0']
        for n in range(4): commands.append(f'title_pointer{n}: dc.w ${0xe0+4*n:04x},0,${0xe2+4*n:04x},0')
        for n in range(16): commands.append(f'        dc.w ${0x180+2*n:04x},${PALETTE.get(n,0):03x}')
        commands.append('        dc.w $ffff,$fffe')
        for n in range(4): commands.append(f'title_plane{n}: incbin "{directory.relative_to(ROOT)}/plane{n}.bin"')
        (directory/'display.i').write_text('\n'.join(commands)+'\n')
    (out/'enhanced/instructions.json').write_text(json.dumps({'lines':lines,'first_row':144,
        'font_additions_sha256':hashlib.sha256((ROOT/'assets/interface/small-font-additions.json').read_bytes()).hexdigest(),
        'source_sha256':expected},indent=2)+'\n')

if __name__=='__main__': generate()
