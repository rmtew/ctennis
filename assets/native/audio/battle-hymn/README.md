# Battle Hymn celebration assets

The user selected the full eight-bar chorus in B-flat. The melody follows the
historical source below. Bass, arpeggio, waveform and period table are authored
for this native arrangement. The native celebration engine uses these assets.

Run `python scripts/author_battle_hymn.py` to reproduce them. The script uses
the Python standard library. It reads no recording, cartridge or WAV file.
`notes.json` is the reviewable event export and a native celebration test input.

| File | Voice or role | Records | Bytes |
| --- | --- | ---: | ---: |
| `melody.bin` | Voice 0 / Paula AUD0 | 34 | 544 |
| `bass.bin` | Voice 1 / Paula AUD1 | 33 | 528 |
| `arpeggio.bin` | Voice 2 / Paula AUD3 | 65 | 1,040 |
| `square.s8` | Shared signed 8-bit DMA waveform | 2 Paula words | 4 |
| `periods.bin` | Big-endian period table | | 3,072 |

Runtime assets occupy 5,188 bytes. Voice state, code and alignment are separate.
Waveform bytes are `7f 7f 81 81`. Voice 2 also carries ordinary hit/cue effects;
the celebration lifecycle controls its ownership.

Each event record has 16 bytes. Byte 0 is 6 for pitched events and 3 for rests.
Byte 1 is `0x4e`. Byte 2 is the key and byte 3 is the octave. Byte 5 selects
level 3, 6 or 8 for melody, bass or arpeggio. Byte 6 selects envelope 0.
Byte 7 sets release scale 7. Byte 9 is duration and byte 11 sets rate 2.
Other fields are zero. Each stream ends with a silent record: byte 0 is 11
and byte 9 is 1. Preterminal durations sum to 384 units in every stream.

Use transpose 0 and the supplied period table. For each MIDI note, key is
`MIDI % 12` and octave is `floor(MIDI / 12) - 3`. The byte offset is
`octave * 384 + transpose * 24 + key * 2`. The table has eight octaves,
16 transpositions and 12 keys. Periods use the PAL Paula clock, 3,546,895 Hz,
divided by four samples and the equal-tempered note frequency. The octave
origin differs from the retained effects table. Do not interchange the tables.

The authoring contract uses a 40 ms unit, 12 units per quarter and 125 BPM.
The 384-unit phrase lasts 15.36 seconds at that nominal rate. The final beat
is silent. The terminal rest adds one unit. There is no loop opcode.

The game uses about 59.923 simulation updates per second on PAL video.
Celebration audio alternates two and three simulation ticks, averaging
2.4 ticks per unit. A complete native loop includes the terminal rest:
385 units, 924 simulation ticks, about 15.4205 seconds. First playback adds
two startup ticks. Actual duration and level completion trigger reload and
the winner prompt. The effects cadence and period table remain separate.

The melody source is *The Riverside Song Book* (Houghton, Mifflin, 1893),
selected and arranged by W. M. Lawrence and O. Blackman, printed pages 36–37.
Only the upper chorus melody and rhythm are used. The historical lower voices
are not reproduced. See the [notation transcription](https://en.wikisource.org/wiki/The_Riverside_song_book/Battle_Hymn_of_the_Republic)
and [edition metadata](https://en.wikisource.org/wiki/The_Riverside_song_book).

An independent source reviewer inspected the [primary facsimile, printed page 37](https://en.wikisource.org/wiki/Page%3AThe_Riverside_song_book.djvu/61).
That review corrected the transcription's final sixteenth in chorus bar 3
from A4 to G4. The corrected event is MIDI 67 at unit 141 for three units.
Bar 3, in quarter beats, is G4(1.5), A4(.5), Bb4(.75), A4(.25), Bb4(.75),
G4(.25). The reviewer found the other chorus pitches and rhythms consistent
with the facsimile. This records that review; it does not claim a new source
inspection during repository cleanup.

No Sega melody, modern arrangement recording or lyrics were copied. Private
integration does not establish blanket public-release rights.
