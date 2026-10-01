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
