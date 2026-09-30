"""Restore one reachable exchanged-end source window for CT-03 (no full match)."""
import hashlib
import json
import os
import subprocess
from pathlib import Path
from round_reference import parse_capture
from physical_input_reference import ROOT, sha


def main():
    directory=ROOT/'build/reference/control-ownership'
    directory.mkdir(parents=True,exist_ok=True)
    source=json.loads((ROOT/'tests/reference/input-map.json').read_text())
    command=list(source['source_command'])
    command[command.index('-seconds_to_run')+1]='180'
    payloads=[]
    for name in ('a','b'):
        env=os.environ.copy()
        env.update(CT_TEST_SELECT='two',CT_TEST_FIRE='0',CT_TEST_CAPTURE=str(directory/f'{name}.tsv'),
                   CT_TEST_POLICY='scripts/capture_control_ownership.lua',CT_TEST_LAST_FRAME='10000',CT_TEST_CONTACT_MARKERS='0')
        result=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,text=True,timeout=240)
        (directory/f'{name}.log').write_text(result.stdout+result.stderr)
        if result.returncode or 'ROUND_REFERENCE_COMPLETE' not in result.stdout or 'LUA ERROR' in result.stdout+result.stderr:
            raise RuntimeError('Source ownership capture failed; see local log')
        payloads.append((directory/f'{name}.tsv').read_bytes())
    if payloads[0]!=payloads[1]: raise ValueError('Source ownership repeats differ')
    callbacks,timeline=parse_capture(payloads[0])
    start=next(i for i,r in enumerate(callbacks) if bytes.fromhex(r['ram'])[0x3d]&0x10 and bytes.fromhex(r['ram'])[0x3a]==0x40)
    rows=callbacks[start:]
    if len(rows)>120 or len(rows)<100: raise ValueError('Bounded exchanged-end window missing')
    record={'repeat_identical':True,'rom_sha256':source['rom_sha256'],'capture_sha256':hashlib.sha256(payloads[0]).hexdigest(),
            'source_command':command,'scripts':{str(p):sha(ROOT/p) for p in map(Path,('scripts/capture_control_ownership.lua','scripts/capture_two_player_match.lua','scripts/capture_round_reference.lua'))},
            'initial_source_callback':start,'callbacks':rows,'timeline':timeline}
    (directory/'reference.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({k:v for k,v in record.items() if k not in ('callbacks','timeline')},indent=2))

if __name__=='__main__': main()
