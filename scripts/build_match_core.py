"""Build and relocate the actual shared 68000 core without an Amiga emulator."""
import hashlib
import json
import struct
from pathlib import Path

from native_tools import ROOT, ASSEMBLER, run, verify_build_tools

OUTPUT = ROOT / 'build/standalone'


def build():
    """Validate core table inputs and assemble the shared source and RTS sinks."""
    verify_build_tools()
    manifest = json.loads((ROOT / 'assets/native/manifest.json').read_text())
    if manifest['schema'] != 2:
        raise ValueError('Unsupported native asset manifest')
    declared = {item['path']: item for item in manifest['files']}
    # No generated UI, demo input, or graphics preparation is needed here.
    for directory in ('audio', 'scene'):
        for path in sorted((ROOT / 'assets/native' / directory).rglob('*.bin')):
            name = str(path.relative_to(ROOT))
            item = declared.get(name)
            if item is None:
                raise ValueError('Undeclared core table: ' + name)
            data = path.read_bytes()
            if len(data) != item['size_bytes'] or hashlib.sha256(data).hexdigest() != item['sha256']:
                raise ValueError('Incompatible versioned native input: ' + name)
    for name in declared:
        if name.startswith(('assets/native/audio/', 'assets/native/scene/')) and not (ROOT / name).is_file():
            raise FileNotFoundError('Missing versioned native input: ' + name)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    executable, listing = OUTPUT / 'match-core', OUTPUT / 'match-core.lst'
    run([str(ASSEMBLER), '-Fhunkexe', '-kick1hunks', '-m68000',
         '-L', str(listing), '-o', str(executable), 'amiga/standalone.s'])
    return executable, listing


def load_image(executable, base=0x10000, hunk_addresses=None):
    """Return relocated ``[(address, bytes)]`` and debug symbol addresses.

    Supports the emitted CODE/DATA/BSS/RELOC32/SYMBOL/END subset only. Hunks
    occupy consecutive longword-aligned addresses; no OS LoadSeg is involved.
    Reject malformed or unsupported input instead of guessing loader behavior.
    """
    if not isinstance(base, int) or base < 0 or base % 4:
        raise ValueError('Image base must be a nonnegative longword address')
    blob = Path(executable).read_bytes()
    position = 0

    def take(size):
        nonlocal position
        if size < 0 or position + size > len(blob):
            raise ValueError('Truncated hunk executable')
        data = blob[position:position+size]
        position += size
        return data

    def word():
        return struct.unpack('>I', take(4))[0]

    if word() != 1011 or word() != 0:
        raise ValueError('Expected anonymous HUNK_HEADER')
    count, first, last = word(), word(), word()
    if not count or first != 0 or last + 1 != count or count > (len(blob)-position)//4:
        raise ValueError('Invalid hunk table')
    sizes = [(word() & 0x3fffffff)*4 for _ in range(count)]
    addresses, cursor = [], base
    for size in sizes:
        addresses.append(cursor)
        cursor += size
    if hunk_addresses is not None:
        assert len(hunk_addresses)==count and all(type(a) is int and a>=0 and a%4==0 for a in hunk_addresses)
        assert all(a+size<=0x100000000 for a,size in zip(hunk_addresses,sizes))
        assert all(a+size<=b or b+other<=a for i,(a,size) in enumerate(zip(hunk_addresses,sizes)) for b,other in list(zip(hunk_addresses,sizes))[i+1:])
        addresses=list(hunk_addresses)
    if cursor > 0x100000000:
        raise ValueError('Image exceeds 32-bit address space')
    image, symbols = [], {}
    for index, declared in enumerate(sizes):
        kind, size = word() & 0x3fffffff, word()*4
        if kind not in (1001, 1002, 1003) or size != declared:
            raise ValueError('Unsupported hunk or size')
        data = bytearray(size) if kind == 1003 else bytearray(take(size))
        while True:
            block = word() & 0x3fffffff
            if block == 1010:
                break
            if block == 1008:
                while True:
                    length = word()
                    if not length:
                        break
                    raw = take(length*4)
                    name_bytes = raw.split(b'\0', 1)[0]
                    if not name_bytes or any(raw[len(name_bytes):]):
                        raise ValueError('Invalid symbol name or padding')
                    name, offset = name_bytes.decode('ascii'), word()
                    if offset > size:
                        raise ValueError('Symbol outside hunk')
                    address = addresses[index]+offset
                    if name in symbols and symbols[name] != address:
                        raise ValueError('Conflicting symbol: ' + name)
                    symbols[name] = address
            elif block == 1004:
                while True:
                    number = word()
                    if not number:
                        break
                    target = word()
                    if target >= count:
                        raise ValueError('Relocation target outside hunk table')
                    for _ in range(number):
                        offset = word()
                        if offset % 2 or offset+4 > size:
                            raise ValueError('Invalid relocation offset')
                        value = struct.unpack_from('>I', data, offset)[0]+addresses[target]
                        if value > 0xffffffff:
                            raise ValueError('Relocation exceeds 32-bit address space')
                        struct.pack_into('>I', data, offset, value)
            else:
                raise ValueError(f'Unsupported hunk block {block}')
        if size:
            image.append((addresses[index], bytes(data)))
    if position != len(blob):
        raise ValueError('Unexpected trailing executable data')
    return image, symbols


if __name__ == '__main__':
    executable, listing = build()
    image, symbols = load_image(executable)
    print(json.dumps({'executable': str(executable), 'listing': str(listing),
                      'loaded_bytes': sum(len(data) for _, data in image),
                      'symbols': len(symbols)}, indent=2))
