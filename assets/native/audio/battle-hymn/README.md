# Battle Hymn of the Republic — authored native celebration assets

Selected by the user to replace the provisional celebration placeholder. This
asset-only package contains the corrected full eight-bar chorus in B-flat,
with independently written bass/fifth and arpeggio accompaniment. Engine,
looping and celebration integration belong to the celebration worker.

Reproduce with `python3 scripts/author_battle_hymn.py`. Standard library only;
no recording, cartridge, retained native music or WAV input is used. `notes.json`
is the editable/reviewable event export; the script is the authored source.

## Runtime file mapping

|File|Voice/role|Records|Bytes|
|---|---|---:|---:|
|melody.bin|voice0 / Paula AUD0|34|544|
|bass.bin|voice1 / Paula AUD1|33|528|
|arpeggio.bin|voice2 / Paula AUD3|65|1040|
|square.s8|shared DMA-looped signed8-bit waveform|2 Paula words|4|
|periods.bin|independent big-endian equal-tempered period lookup||3072|

Runtime assets total5188 bytes, plus existing96-byte voice state, code and
alignment. No long sampled music, preview WAV or fourth voice is needed.
Waveform bytes are `7f 7f 81 81` (+127,+127,−127,−127). Existing voice2 also
owns hit/cue SFX, so integration must resolve that ownership during celebration.

## Native format and pitch contract

Each record is16 bytes in master93bb640's prepared-score format. Pitched records
have byte0=6 (explicit octave and duration); rest records byte0=3. Byte1=0x4e
sets base level, envelope, release scale and global audio rate. Byte2=key,
byte3=octave, byte5=level index (melody3/bass6/arpeggio8), byte6=envelope0,
byte7=release scale7, byte9=duration, byte11=rate2. Other fields are zero.
Each stream ends with a silent one-unit record: byte0=11 (rest/duration/done),
byte9=1. All preterminal streams sum384 units; counts above include terminals.

Set global transpose0. Use the supplied independent `periods.bin` with these
octaves: key=MIDI%12; octave=floor(MIDI/12)−3; byte offset=
`octave*384 + transpose*24 + key*2`. Its octave origin differs from the retained
master period lookup; scores must not be attached to that retained lookup
unchanged. Own lookup has8 octaves ×16 transpositions ×12 keys, with periods
rounded from PAL Paula clock3546895Hz / (4 samples × equal-tempered frequency).
Every pitched record has been checked against its exported period. If the
engine uses direct-period events instead, `notes.json` supplies those periods.

## First-play completion and loop contract

PAL50Hz, audio rate2: unit=.04 sec; quarter=12 units;125 BPM. Phrase is384
units=15.36 sec from first event load. Pitched-note durations end by14.88 sec;
the final beat is silent. All terminal done/rest records load at15.36 sec,
after the full first phrase, and their one-unit duration ends15.40 sec. An idle
queue adds1–2 PAL ticks (.02–.04 sec) before the first event; an occupied voice
also waits for its current note. Do not interpret final pitched-note onset as
first-play completion. The physical sink/release may silence a note earlier
than its scheduled duration, which does not shorten the phrase boundary.

There is no loop opcode. Requeue after terminal load gives an earliest15.40-sec
cycle. Exact15.36-sec looping requires requeue during the final beat's rest,
before terminal load, preserving the current rest duration; that bypasses the
terminal done record on a looping traversal. An engine-level phrase boundary
must then account for the full384 units. This package does not implement that
scheduler or alter product lifecycle logic. Host audition sound used edge ramps,
softened stereo pan and RMS normalization; native rendering is still untested.

## Historical provenance and primary-source correction

Melody source: The Riverside Song Book (Houghton, Mifflin,1893), selected/arranged
by W. M. Lawrence and O. Blackman, printed pp.36–37. Only the upper chorus
melody and rhythm are used; the historical lower vocal/bass arrangement is not
reproduced. Readable notation transcription:
https://en.wikisource.org/wiki/The_Riverside_song_book/Battle_Hymn_of_the_Republic
Edition metadata: https://en.wikisource.org/wiki/The_Riverside_song_book

An independent source reviewer inspected the primary facsimile at the Image
link on https://en.wikisource.org/wiki/Page%3AThe_Riverside_song_book.djvu/61
(printed p.37), as reported through the parent worker. It corrects the
transcription's chorus bar3 final sixteenth: upper G4 of Eb4/G4, rather than
upper A4 of F4/A4. Corrected bar3 in quarter beats is G4(1.5),A4(.5),Bb4(.75),
A4(.25),Bb4(.75),G4(.25). This is MIDI67 at unit141 for3 units. The reviewer
reported the other chorus pitches/rhythms consistent with the facsimile.
Primary image inspection is attributed to that reviewer, not the local
asset worker. Bass/arpeggio, waveform and period table are newly authored.
No Sega melody, modern arrangement audio, recording, or lyrics were copied.
This private integration does not make a blanket public-release rights claim.
