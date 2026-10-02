; Three native monophonic voices. A note is a prepared 16-byte musical record;
; no source stream, source address or PSG register is used by the sequencer.
        rsset 0
AV_NEXT rs.l 1
AV_CLIP rs.b 1
AV_CURSOR rs.b 1
AV_DONE rs.b 1
AV_OCTAVE rs.b 1
AV_BASE rs.b 1
AV_ENVELOPE rs.b 1
AV_RELEASE_SCALE rs.b 1
AV_DEFAULT_DURATION rs.b 1
AV_DURATION rs.b 1
AV_RELEASE rs.b 1
AV_ENVELOPE_STEP rs.b 1
AV_LEVEL rs.b 1
AV_KEY rs.b 1
AV_NOTE_OCTAVE rs.b 1
AV_PERIOD rs.w 1
        rs.b 12 ; reserved bytes20..31, preserve 32-byte voice stride
AV_SIZE rs.b 0
