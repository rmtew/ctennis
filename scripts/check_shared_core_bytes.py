"""Compare actual shared emitted bytes; normalize only verified address fixups."""
import hashlib
import json
import re
import struct
from pathlib import Path

from build_match_core import load_image
from native_size import _units
from native_tools import ROOT

SINKS = ('game_render_sprites', 'game_scene_present_fields', 'game_core_title_requested',
         'game_core_status_present', 'game_audio_write_period', 'game_audio_write_level',
         'game_observe_pre_tail', 'game_apply_sound',
         'game_history_contact_begin', 'game_history_contact', 'game_history_serve')


def normalized(executable, listing, begin_name='game_core_code_begin',
               end_name='game_core_code_end', external_names=SINKS):
    image, symbols = load_image(executable)
    begin, end = symbols[begin_name], symbols[end_name]
    state_end = symbols['game_core_state_end'] if begin_name=='game_core_code_begin' else end
    origin = image[0][0]
    assert origin <= begin < end <= origin + len(image[0][1])
    data = bytearray(image[0][1][begin - origin:end - origin])
    raw, position = Path(executable).read_bytes(), 0
    def word():
        nonlocal position
        value = struct.unpack_from('>I', raw, position)[0]
        position += 4
        return value
    assert word() == 1011 and word() == 0
    count, first, last = word(), word(), word()
    assert first == 0 and last + 1 == count
    sizes = [word() & 0x3fffffff for _ in range(count)]
    relocations = []
    for hunk in range(count):
        kind, size = word() & 0x3fffffff, word() * 4
        assert size == sizes[hunk] * 4
        if kind != 1003:
            position += size
        while True:
            tag = word()
            if tag == 1010:
                break
            if tag == 1008:
                while (length := word()):
                    position += length * 4 + 4
            elif tag == 1004:
                while (length := word()):
                    assert word() < count
                    for _ in range(length):
                        offset = word()
                        assert offset % 2 == 0 and offset + 4 <= size
                        if hunk == 0 and begin - origin <= offset < end - origin:
                            relocations.append(offset - (begin - origin))
            else:
                raise ValueError('Unsupported hunk block: ' + str(tag))
    assert position == len(raw)
    for offset in relocations:
        value = struct.unpack_from('>I', data, offset)[0]
        if begin <= value <= state_end:
            token = 0x10000 + value - begin
        else:
            matches = [name for name in external_names if symbols.get(name) == value]
            assert matches, ('Undeclared external reference', offset, value)
            token = 0xf0000000 + external_names.index(matches[0])
        struct.pack_into('>I', data, offset, token)
    branches = 0
    for unit in _units(Path(listing).read_text()):
        offset = unit['start'] - (begin - origin)
        if unit['hunk'] != 0 or not 0 <= offset < len(data):
            continue
        match = re.fullmatch(r'(?:bra|bsr|jsr)\s+(\w+)', unit['statement'].strip())
        if match and match[1] in external_names:
            opcode = struct.unpack_from('>H', data, offset)[0]
            if opcode == 0x4eb9:
                assert offset + 2 in relocations
                assert struct.unpack_from('>I',data,offset+2)[0] == 0xf0000000 + external_names.index(match[1])
                continue
            assert opcode in (0x6000, 0x6100)
            displacement = struct.unpack_from('>h', data, offset + 2)[0]
            assert begin + offset + 2 + displacement == symbols[match[1]]
            struct.pack_into('>H', data, offset + 2, external_names.index(match[1]) + 1)
            branches += 1
    return bytes(data), len(relocations), branches


def run():
    native = ROOT / 'build/amiga/interfaces/enhanced/baseline-rally'
    standalone = ROOT / 'build/standalone/match-core'
    left, relocations, branches = normalized(native, native.parent / 'native.lst')
    right, other_relocations, other_branches = normalized(standalone, standalone.parent / 'match-core.lst')
    assert (relocations, branches) == (other_relocations, other_branches)
    assert left == right, ('Shared emitted bytes differ', next((i for i, pair in enumerate(zip(left, right)) if pair[0] != pair[1]), None))
    return {'passed': True, 'matched_bytes': len(left), 'relocations_each': relocations,
            'verified_sink_branches_each': branches, 'normalized_sha256': hashlib.sha256(left).hexdigest(),
            'executable_sha256': {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in (native, standalone)},
            'scope': 'Actual uninstrumented code/tables/alignment; only HUNK_RELOC32 and verified named synchronous-sink branch address fixups normalized; state bytes excluded'}


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
