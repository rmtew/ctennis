"""Verify actual LoadSeg bytes against the native vasm hunk executable.

Supports only the emitted HUNK_CODE/DATA/BSS/RELOC32/SYMBOL/END subset and rejects
anything else, rather than accepting a guessed program or filename.
"""
import hashlib,struct

def loaded_hunks(path, segments, read):
    blob=path.read_bytes();pos=0
    def word():
        nonlocal pos
        n=struct.unpack_from('>I',blob,pos)[0];pos+=4;return n
    if word()!=1011 or word()!=0:raise ValueError('Expected anonymous HUNK_HEADER')
    count,first,last=word(),word(),word()
    if first!=0 or last+1!=count or count!=len(segments):raise ValueError('Loaded hunk table mismatch')
    sizes=[word()&0x3fffffff for _ in range(count)]
    checks=[]
    for index in range(count):
        kind=word()&0x3fffffff;size=word()*4
        if kind not in (1001,1002,1003) or size!=sizes[index]*4:
            raise ValueError('Unsupported native hunk or size')
        data=bytearray(size) if kind==1003 else bytearray(blob[pos:pos+size])
        if kind!=1003:pos+=size
        while True:
            block=word()&0x3fffffff
            if block==1010:break
            if block==1008: # HUNK_SYMBOL is linker/debug metadata, not loaded bytes.
                while True:
                    length=word()
                    if not length:break
                    pos+=length*4
                    word() # symbol value
                continue
            if block!=1004:raise ValueError(f'Unsupported native hunk block{block}')
            while True:
                n=word()
                if not n:break
                target=word()
                if target>=count:raise ValueError('Relocation target outside hunk table')
                for _ in range(n):
                    offset=word()
                    if offset+4>size or offset%2:raise ValueError('Invalid relocation offset')
                    value=struct.unpack_from('>I',data,offset)[0]+segments[target]['start']
                    struct.pack_into('>I',data,offset,value)
        actual=read(segments[index]['start'],size)
        expected_sha=hashlib.sha256(data).hexdigest();actual_sha=hashlib.sha256(actual).hexdigest()
        checks.append({'hunk':index,'start':segments[index]['start'],'bytes':size,
                       'expected_sha256':expected_sha,'actual_sha256':actual_sha,'matched':data==actual})
        if data!=actual:raise ValueError(f'Loaded executable differs in hunk{index}')
    if pos!=len(blob):raise ValueError('Unexpected trailing executable data')
    return checks


def hunk_layout(path):
    """Loaded size by emitted hunk kind, excluding symbols/relocation metadata."""
    blob=path.read_bytes();pos=0
    def word():
        nonlocal pos
        if pos+4>len(blob): raise ValueError('Truncated hunk executable')
        value=struct.unpack_from('>I',blob,pos)[0];pos+=4;return value
    def skip(n):
        nonlocal pos
        if n<0 or pos+n>len(blob): raise ValueError('Truncated hunk payload')
        pos+=n
    if word()!=1011 or word()!=0: raise ValueError('Expected anonymous HUNK_HEADER')
    count,first,last=word(),word(),word()
    if first!=0 or last+1!=count: raise ValueError('Invalid hunk table')
    sizes=[word() for _ in range(count)];rows=[]
    framing={'header_table_bytes':pos,'hunk_headers_and_end_bytes':0,
             'relocation_bytes':0,'relocations':0,'symbol_bytes':0,'symbols':0,
             'symbol_name_bytes':0,'symbol_name_padding_bytes':0,'symbol_framing_bytes':0,'debug_bytes':0}
    for index,declared in enumerate(sizes):
        kind=word()&0x3fffffff;size=word()*4
        if kind not in (1001,1002,1003) or size!=(declared&0x3fffffff)*4:
            raise ValueError('Unsupported hunk or size')
        framing['hunk_headers_and_end_bytes']+=8
        rows.append({'file_offset':pos,'index':index,'kind':{1001:'code',1002:'data',1003:'bss'}[kind],
                     'bytes':size,'memory':'chip' if declared&0x40000000 else 'fast' if declared&0x80000000 else 'any'})
        if kind!=1003: skip(size)
        while True:
            block_start=pos
            block=word()&0x3fffffff
            if block==1010:
                framing['hunk_headers_and_end_bytes']+=4;break
            if block==1008:
                framing['symbol_framing_bytes']+=8
                while True:
                    length=word()
                    if not length:break
                    name_start=pos;skip(length*4);word()
                    raw=blob[name_start:name_start+length*4];name=raw.split(b'\0',1)[0]
                    if any(raw[len(name):]):raise ValueError('Nonzero symbol-name padding')
                    framing['symbols']+=1;framing['symbol_name_bytes']+=len(name)
                    framing['symbol_name_padding_bytes']+=len(raw)-len(name)
                    framing['symbol_framing_bytes']+=8
                framing['symbol_bytes']+=pos-block_start
            elif block==1004:
                while True:
                    n=word()
                    if not n:break
                    target=word()
                    framing['relocations']+=n
                    if target>=count:raise ValueError('Invalid relocation target')
                    for _ in range(n):
                        offset=word()
                        if offset%2 or offset+4>size:raise ValueError('Invalid relocation offset')
                framing['relocation_bytes']+=pos-block_start
            else:raise ValueError(f'Unsupported hunk block {block}')
    if pos!=len(blob):raise ValueError('Unexpected trailing hunk bytes')
    return {'executable_bytes':len(blob),'hunks':rows,'file_format':framing,
            **{kind+'_bytes':sum(r['bytes'] for r in rows if r['kind']==kind) for kind in ('code','data','bss')},
            'loaded_payload_bytes':sum(r['bytes'] for r in rows)}
