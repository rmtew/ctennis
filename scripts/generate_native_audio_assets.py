"""Convert the identified score into native notes/envelopes/Paula periods offline.

The maintained sequencer never reads source opcodes, ROM addresses or PSG bytes.
Source cursor annotations live in separate diagnostic-only assets, not product notes.
"""
import configparser
import hashlib
import json
import struct
from fractions import Fraction
from pathlib import Path
from capture_test_reference import ROOT, ROM_SHA256

OUT = ROOT / 'build/amiga/native-audio'
# Identified source score boundaries, including the original preceding sentinel.
SCORES = ((0x1f05,79),(0x1f53,69),(0x1f97,34),(0x1fb8,38),(0x1fdd,23),(0x1ff3,9))

def decode_notes(rom, address, length):
    index = 1
    notes = []
    settings = {}
    def read():
        nonlocal index
        if not index:
            raise ValueError('Score argument crossed its terminal boundary')
        value = rom[address-1+index]
        index = (index+1) % length
        return value
    while index:
        command = read()
        handler, low = (command >> 4) & 7, command & 15
        if handler in (0,1):
            flags = 0
            if handler == 0:
                key, octave = max(0,low-1), 0
                if low == 0: flags |= 1
                explicit = bool(command & 128)
            else:
                argument = read()
                octave, key = divmod((argument & 127)-1,12)
                flags |= 4
                explicit = bool(argument & 128)
            duration = read() if explicit else 0
            if explicit: flags |= 2
            if not index: flags |= 8
            row = bytearray(16)
            row[0],row[2],row[3],row[9],row[12] = flags,key,octave,duration,index
            for bit, value in settings.items():
                row[1] |= 1 << bit
                row[(4,5,6,7,8,10,11)[bit]] = value
            notes.append(row);settings.clear()
        elif handler == 2:
            settings[5 if command & 128 else 0] = low if command & 128 else command & 7
        elif handler == 3: settings[1] = 15-low
        elif handler == 4: settings[2] = command & 7
        elif handler == 5: settings[3] = low
        elif handler == 6: settings[4] = read()
        else: settings[6] = read()
    if settings:
        row=bytearray(16);row[0]=24
        for bit,value in settings.items():
            row[1] |= 1 << bit;row[(4,5,6,7,8,10,11)[bit]]=value
        notes.append(row)
    if not notes: raise ValueError('Empty native score')
    return b''.join(notes)


def generate():
    config=configparser.ConfigParser(interpolation=None);config.read(ROOT/'config.local.ini')
    rom=Path(config['inputs']['cartridge']).read_bytes()
    if hashlib.sha256(rom).hexdigest()!=ROM_SHA256:raise ValueError('Unexpected source cartridge')
    OUT.mkdir(parents=True,exist_ok=True)
    scores=[decode_notes(rom,*row) for row in SCORES]
    cursors=[bytes([1])+bytes(score[n] for n in range(12,len(score),16)) for score in scores]
    scores=[bytes(0 if n%16==12 else b for n,b in enumerate(score)) for score in scores]
    for n,data in enumerate(cursors):(OUT/f"diagnostic-cursors-{n}.bin").write_bytes(data)
    for n,data in enumerate(scores):(OUT/f'score-{n}.bin').write_bytes(data)
    native_periods=bytearray();diagnostic_divisors=bytearray()
    for octave in range(8):
        for transpose in range(16):
            for key in range(12):
                index=key+transpose;shift=octave
                if index>=12:index-=12;shift+=1
                word=int.from_bytes(rom[0x18da+index*2:0x18dc+index*2],'big') >> (shift & 7)
                divisor=(word>>4)&1023
                physical=divisor or 1024
                period=max(123,round(Fraction(3546895*8*physical,3579545)))
                native_periods.extend(struct.pack('>H',period));diagnostic_divisors.extend(struct.pack('>H',divisor))
    envelopes=bytes(15 if n==0 else ((rom[0x19bc+(n-1)*8+step//2] >> (0 if step&1 else 4)) & 15)
                    for n in range(8) for step in range(16))
    (OUT/'periods.bin').write_bytes(native_periods)
    (OUT/'envelopes.bin').write_bytes(envelopes)
    (OUT/'diagnostic-divisors.bin').write_bytes(diagnostic_divisors)
    lines=['native_audio_scores:']+[f'        dc.l native_audio_score_{n}' for n in range(6)]
    for n in range(6):lines += [f'native_audio_score_{n}: incbin "build/amiga/native-audio/score-{n}.bin"']
    lines += ['native_audio_periods: incbin "build/amiga/native-audio/periods.bin"',
              'native_audio_envelopes: incbin "build/amiga/native-audio/envelopes.bin"']
    (OUT/'data.i').write_text('\n'.join(lines)+'\n')
    cursor_lines='native_audio_source_cursors:\n'+''.join(f'        dc.l native_audio_source_cursor_{n}\n' for n in range(6))+''.join(f'native_audio_source_cursor_{n}: incbin "build/amiga/native-audio/diagnostic-cursors-{n}.bin"\n' for n in range(6))+'        even\n'
    (OUT/'diagnostic.i').write_text(cursor_lines+'native_audio_source_scores:\n'+''.join(f'        dc.w ${a-1:04x},{l}\n' for a,l in SCORES)+
        'native_audio_source_divisors: incbin "build/amiga/native-audio/diagnostic-divisors.bin"\n')
    files=sorted(p for p in OUT.iterdir() if p.suffix in ('.bin','.i'))
    (OUT/'manifest.json').write_text(json.dumps({'kind':'native-note-score-assets','source_sha256':ROM_SHA256,
        'notes_per_score':[len(s)//16 for s in scores],'native_note_bytes':16,
        'outputs':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}},indent=2)+'\n')
    return [len(s)//16 for s in scores]

if __name__=='__main__':print(json.dumps({'notes_per_score':generate()}))
