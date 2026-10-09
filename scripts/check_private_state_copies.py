"""Read-only copy-call counts from completed tutorial capture transcripts.

Usage: python scripts/check_private_state_copies.py --output PATH CAPTURE_DIR...
No build, emulator, gameplay reconstruction or elapsed worker-cost claim.
"""
import collections,gzip,hashlib,json,re
from pathlib import Path

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def examine(directory):
 directory=Path(directory);report_path=directory/'report.json';report=json.loads(report_path.read_text())
 assert report['passed'] and report['timing']['dropped_notifications']==0
 assert report['evidence']['state']=='complete' and not report['evidence'].get('changed_during_run')
 capture=directory/'capture.json'
 if not capture.exists():capture=directory/Path(report['capture']).name
 data=json.loads(capture.read_text());listing=directory/'native.lst';text=listing.read_text()
 executable=directory/'baseline-rally'; manifest=directory/'baseline-rally.compile.json'
 assert digest(executable)==report['executable_sha256']==json.loads(manifest.read_text())['executable_sha256']
 bound=report['evidence']['files']
 for p in (capture,listing,manifest,directory/'literal-rpc.jsonl.gz'):
  matches=[sha for name,sha in bound.items() if name.endswith('/tutorial-court-'+report['target']['video'].lower()+'/'+p.name)]
  assert matches==[digest(p)], ('Capture artifact is not receipt-bound',p)
 assert all(r['matched'] and r['actual_sha256']==r['expected_sha256'] for r in report['loaded_hunks'])
 segments={r['hunk']:r['start'] for r in report['loaded_hunks']}
 calls={}
 for h,o,encoded,mnemonic,operand in re.findall(r'^(\d\d):([\da-fA-F]{8})[ \t]+([\dA-F]+)[ \t]+[^\n]*?:[ \t]*(bsr|jsr)(?:\.[swl])?[ \t]*([^\n]*)$',text,re.M|re.I):
  pc=segments[int(h)]+int(o,16);code=bytes.fromhex(encoded);assert len(code) in (2,4,6)
  calls[pc]=(pc+len(code),operand.split(';')[0].strip())
 symbols={n:segments[int(h)]+int(o,16) for n,h,o in re.findall(r'^([A-Za-z_]\w*)\s+(\d\d):([\da-fA-F]{8})\s*$',text,re.M)}
 candidates=[r for r in report['responsiveness']['requests'] if r['variant']==0 and r.get('endpoint_publication_seconds') is not None and report['responsiveness']['fresh_held_edit']['start_seconds']<=r['position']['seconds']<report['responsiveness']['fresh_held_edit']['end_seconds']]
 assert len(candidates)==1;request=candidates[0];generation=request['generation'];start=request['position']['cck']
 pubs=[p for p in data['surfaces']['publications'] if p['tutorial_fields']['tutorial_presentation_generation']==generation and p['tutorial_fields']['tutorial_active_variant']==0 and p['tutorial_fields']['tutorial_marker_ready']]
 endpoint=pubs[0]['position'];stop=endpoint['cck'];clock=3546895 if report['target']['video']=='PAL' else 3579545
 assert abs((stop-start)/3546895-request['endpoint_publication_seconds'])<1e-9
 counts=collections.Counter();entries=[]
 with gzip.open(directory/'literal-rpc.jsonl.gz','rt') as stream:
  for line in stream:
   message=json.loads(line)
   if message.get('type')!='notification':continue
   value=message['value']
   if value.get('method')!='event.mmio':continue
   r=value['params'];assert r.get('dropped_notifications',0)==0 and r.get('dropped_events',0)==0
   if not (start<=r['position']['cck']<=stop and r['access']=='write' and r['size']==4 and symbols['game_stack_bottom']<=r['addr']<symbols['game_stack_top'] and r['pc'] in calls):continue
   return_pc,callee=calls[r['pc']];assert r['value']==return_pc
   counts[callee]+=1
   if callee in ('game_preview_step','game_history_copy_state'):
    entries.append(dict(callee=callee,pc=r['pc'],cck=r['position']['cck'],return_pc=return_pc))
 return dict(directory=str(directory),native_sha=report['executable_sha256'],generation=generation,start_cck=start,stop_cck=stop,latency_cck=stop-start,provider_seconds=(stop-start)/3546895,regional_seconds=(stop-start)/clock,preview_worker_entries=counts['game_preview_step'],state_copy_entries=counts['game_history_copy_state'],copy_call_sites=dict(collections.Counter(str(r['pc']) for r in entries if r['callee']=='game_history_copy_state')),entries=entries,inputs={str(p):digest(p) for p in (report_path,capture,listing,manifest,executable,directory/'literal-rpc.jsonl.gz')},scope='Actual emitted call stack write entries in accepted fresh held request to first actual endpoint publication; exact return values; no call-return timing or completed-worker cost claim')
if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--output',required=True,type=Path)
 parser.add_argument('directories',nargs='+',type=Path)
 args=parser.parse_args()
 rows=[examine(p) for p in args.directories]
 args.output.parent.mkdir(parents=True,exist_ok=True)
 args.output.write_text(json.dumps(rows,indent=2)+'\n')
 print(json.dumps([{k:v for k,v in r.items() if k not in ('entries','inputs')} for r in rows],indent=2))
