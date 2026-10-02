"""Release-only HUNK_SYMBOL removal; development executable/listing stay intact."""
import hashlib
import struct
from native_hunk import hunk_layout


def strip_symbols(blob):
    """Preserve all payload, memory flags, relocation records and other framing."""
    pos=0
    def word():
        nonlocal pos
        if pos+4>len(blob):raise ValueError('Truncated release hunk')
        value=struct.unpack_from('>I',blob,pos)[0];pos+=4;return value
    if word()!=1011 or word()!=0:raise ValueError('Expected anonymous HUNK_HEADER')
    count,first,last=word(),word(),word()
    if first!=0 or last+1!=count:raise ValueError('Invalid release hunk table')
    for _ in range(count):word()
    output=bytearray(blob[:pos]);removed=0
    for _ in range(count):
        start=pos;kind=word()&0x3fffffff;size=word()*4
        if kind not in (1001,1002,1003):raise ValueError('Unsupported release hunk')
        if kind!=1003:pos+=size
        if pos>len(blob):raise ValueError('Truncated release payload')
        output.extend(blob[start:pos])
        while True:
            start=pos;block=word()&0x3fffffff
            if block==1008:
                while True:
                    n=word()
                    if not n:break
                    pos+=n*4;word()
                removed+=pos-start;continue
            if block==1004:
                while True:
                    n=word()
                    if not n:break
                    word()
                    for _ in range(n):word()
            elif block!=1010:raise ValueError('Unsupported release hunk record')
            output.extend(blob[start:pos])
            if block==1010:break
    if pos!=len(blob):raise ValueError('Trailing release hunk data')
    return bytes(output),removed


def release_executable(development, destination):
    before=hunk_layout(development)
    blob,removed=strip_symbols(development.read_bytes())
    destination.write_bytes(blob)
    after=hunk_layout(destination)
    if removed!=before['file_format']['symbol_bytes'] or after['file_format']['symbol_bytes']:
        raise ValueError('Release symbol removal failed')
    for key in ('code_bytes','data_bytes','bss_bytes','loaded_payload_bytes'):
        if before[key]!=after[key]:raise ValueError('Release loaded size changed')
    return {'executable_sha256':hashlib.sha256(blob).hexdigest(),'executable_bytes':len(blob),
            'development_executable_sha256':hashlib.sha256(development.read_bytes()).hexdigest(),
            'removed_symbol_bytes':removed,'layout':after,
            'policy':'Only HUNK_SYMBOL records removed; development executable and listing retain symbols.'}
