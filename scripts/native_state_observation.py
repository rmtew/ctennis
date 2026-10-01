"""Test-only projection of actual named native scalars to existing oracle fields.

No product byte page, writes to game state, or reconstructed expected outcomes.
The same source-format map is used by the captured initialization adapter.
"""
import re
from native_tools import ROOT

def field_addresses(base, symbols):
    pairs=re.findall(r'dc.w \$([0-9a-f]+)\s+dc.l (\w+)',
                     (ROOT/'amiga/tests/native_state_projection.s').read_text())
    return {int(offset,16):base+symbols[name] for offset,name in pairs}

def read_native_state(session, base, symbols):
    addresses=field_addresses(base,symbols)
    groups=[]
    for address in sorted(set(addresses.values())):
        if groups and address<=groups[-1][1]+4:
            groups[-1][1]=address+1
        else:
            groups.append([address,address+1])
    values={}
    for start,end in groups:
        data=bytes.fromhex(session.inspect('mem_read',{'addr':start,'len':end-start})['data'])
        values.update((start+i,v) for i,v in enumerate(data))
    out=bytearray(256)
    for offset,address in addresses.items():out[offset]=values[address]
    return bytes(out)
