#!/usr/bin/env python3
"""Reproduce the independent Battle Hymn score assets using only the stdlib.

No recordings, cartridge data, retained score/pitch assets, or preview WAVs are
inputs. Run from any directory; the default destination is repository-local.
"""
import argparse
import json
from pathlib import Path
import struct

DEFAULT = Path(__file__).resolve().parents[1] / 'assets/native/audio/battle-hymn'
# MIDI pitch:duration in .04-second units. Full eight-bar B-flat chorus.
# Primary facsimile correction: bar3 final sixteenth is G4 (67), not A4 (69).
MELODY = ('65:18 63:6 62:9 65:3 70:9 72:3 74:24 70:12 R:12 '
          '67:18 69:6 70:9 69:3 70:9 67:3 65:24 62:24 '
          '65:18 63:6 62:9 65:3 70:9 72:3 74:24 70:12 R:6 70:6 '
          '72:12 72:12 70:12 69:12 70:36 R:12')
CHORDS = [(46,50,53),(46,50,53),(51,55,58),(46,50,53),
          (46,50,53),(46,50,53),(51,55,58),(53,57,60)]

def events(pairs, voice, level):
    cursor = 0
    result = []
    for midi, duration in pairs:
        event = dict(start_unit=cursor, duration_units=duration, midi=midi,
                     voice=voice, level_index=level)
        if midi is not None:
            frequency = 440 * 2**((midi-69)/12)
            event['paula_period_4byte_wave'] = round(3546895/(4*frequency))
        result.append(event)
        cursor += duration
    assert cursor == 384
    return result

def native(voice):
    result = bytearray()
    for event in voice:
        record = bytearray(16)
        midi = event['midi']
        record[0] = 3 if midi is None else 6
        record[1] = 0x4e # explicit base, envelope, release scale, audio rate
        if midi is not None:
            record[2] = midi % 12
            record[3] = midi // 12 - 3
        record[5] = event['level_index']
        record[6] = 0
        record[7] = 7
        record[9] = event['duration_units']
        record[11] = 2
        result.extend(record)
    terminal = bytearray(16)
    terminal[0] = 11 # explicit-duration rest + done; no premature final attack
    terminal[9] = 1
    result.extend(terminal)
    return bytes(result)

def build(destination):
    destination.mkdir(parents=True, exist_ok=True)
    melody = [(None if n == 'R' else int(n), int(d))
              for n,d in (token.split(':') for token in MELODY.split())]
    bass = []; arpeggio = []
    for chord in CHORDS:
        bass.extend([(chord[0],12),(chord[0]+7,12)]*2)
        arpeggio.extend((chord[i%3]+12,6) for i in range(8))
    bass[-1] = (None,12)
    arpeggio[-2:] = [(None,6),(None,6)]
    voices = [events(melody,0,3),events(bass,1,6),events(arpeggio,2,8)]
    for name,voice in zip(['melody','bass','arpeggio'],voices):
        (destination / (name+'.bin')).write_bytes(native(voice))
    (destination/'notes.json').write_text(json.dumps(dict(
        unit_seconds=.04, quarter_units=12, bpm=125, voices=voices),indent=2)+'\n')
    (destination/'square.s8').write_bytes(bytes([127,127,129,129]))
    periods = [round(3546895/(4*(440*2**(((o+3)*12+k+t-69)/12))))
               for o in range(8) for t in range(16) for k in range(12)]
    lookup = struct.pack('>'+str(len(periods))+'H',*periods)
    (destination/'periods.bin').write_bytes(lookup)
    for voice in voices:
        for event in voice:
            if event['midi'] is None:
                continue
            midi = event['midi']; offset = ((midi//12-3)*192+midi%12)*2
            assert int.from_bytes(lookup[offset:offset+2],'big') == event['paula_period_4byte_wave']

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=DEFAULT)
    build(parser.parse_args().output)
