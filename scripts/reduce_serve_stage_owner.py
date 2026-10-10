"""Reduce a closed native serve receipt without building or running a guest.

Emitted-stack spans exclude instruction tails; enclosing timer-write brackets
include full owner call/return and extra main-loop/accounting work. All measured
bounds are finite observations, not WCET. Milliseconds use the declared native
PAL/NTSC clock; provider position.seconds metadata is retained without conversion.
"""
import argparse,json,hashlib,bisect,collections
from pathlib import Path
from build_match_core import load_image
from serve_stage_discovery import STAGES
from native_tools import ROOT

CLOCK={'PAL':3546895,'NTSC':3579545}

def reduce(report_path,include_rows=False):
    p=Path(report_path).resolve();r=json.loads(p.read_text());exe=p.parent/'baseline-rally'
    assert r['passed'] is True and r['evidence']['state']=='complete','Requires a closed passing native report'
    hz=CLOCK[r['standard']]
    assert hashlib.sha256(exe.read_bytes()).hexdigest()==r['executable_sha256'],'Executable receipt binding mismatch'
    assert all(x['matched'] for x in r['loaded_hunks']),'Loaded native hunks were not qualified'
    image,s=load_image(exe,hunk_addresses=[x['start'] for x in r['loaded_hunks']]);frames=r['stack_rows'];fields=sorted(r['field_rows'],key=lambda x:x['position']['cck'])
    def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
    bycallee=collections.defaultdict(list)
    for f in frames:bycallee[f['callee']].append(f)
    bodyframes=sorted([f for f in frames if f['callee'] in STAGES],key=lambda f:f['entry']['cck'])
    bodytimes=[f['entry']['cck'] for f in bodyframes]
    for fs in bycallee.values():fs.sort(key=lambda f:f['entry']['cck'])
    calleetimes={n:[f['entry']['cck'] for f in fs] for n,fs in bycallee.items()}
    fieldmap=collections.defaultdict(list)
    for f in fields:fieldmap[f['addr']].append(f)
    fieldtimes={a:[f['position']['cck'] for f in fs] for a,fs in fieldmap.items()}
    def enclosing(child,name):
     a,b=child['entry']['cck'],child['exit']['cck'];i=bisect.bisect_right(calleetimes[name],a)-1
     if i<0:return None
     x=bycallee[name][i];return x if x['exit']['cck']>=b else None
    plan_widths={'tutorial_job_variant':2,'tutorial_job_stage':2,'tutorial_job_cost':4}
    planbytes=collections.defaultdict(list)
    for f in fields:
     for n,width in plan_widths.items():
      base=s[n];address=f['addr'];size=f['size']
      if address<base+width and base<address+size:
       data=f['value'].to_bytes(size,'big')
       for offset,value in enumerate(data):
        if base<=address+offset<base+width:planbytes[address+offset].append((f['position']['cck'],value))
    plantimes={a:[x[0] for x in xs] for a,xs in planbytes.items()}
    def latest(name,at):
     values=[]
     for address in range(s[name],s[name]+plan_widths[name]):
      i=bisect.bisect_right(plantimes.get(address,[]),at)-1
      if i<0:return None
      values.append(planbytes[address][i][1])
     return int.from_bytes(bytes(values),'big')
    rows=[]
    for api in frames:
     if api['callee']!='game_preview_dispatch_stage':continue
     owner=enclosing(api,'tutorial_background');assert owner is not None
     a,b=api['entry']['cck'],api['exit']['cck'];bodies=[x for x in bodyframes[bisect.bisect_left(bodytimes,a):bisect.bisect_right(bodytimes,b)] if x['exit']['cck']<=b]
     cb=enclosing(api,'simulation_update');prev=[x for x in r['callbacks'] if x.get('completion',{}).get('cck',10**30)<=owner['entry']['cck']];nxt=[x for x in r['callbacks'] if x['entry']['cck']>=owner['exit']['cck']]
     n=owner['elapsed_bus_cck'];rows.append(dict(body=[x['callee'] for x in bodies],owner=owner,api=api,owner_bus_e=n/5,owner_bus_ms=n*1000/hz,reserve_bus_margin_cck=20000-n,variant=latest('tutorial_job_variant',a),planned_stage=latest('tutorial_job_stage',a),planned_cost=latest('tutorial_job_cost',a),callback_enclosing=cb,preceding_callback=prev[-1]['callback'] if prev else None,next_callback=nxt[0]['callback'] if nxt else None))
    phase_pc=s['account_sim_timer']+16
    code=next(data[phase_pc-base:phase_pc-base+6] for base,data in image if base<=phase_pc<base+len(data))
    assert code==bytes.fromhex('d3b9')+s['simulation_phase'].to_bytes(4,'big'),'Expected actual add.l d1,simulation_phase'
    phasewrites=[f for f in fieldmap[s['simulation_phase']] if f['pc']==phase_pc]
    phasetimes=[f['position']['cck'] for f in phasewrites]
    for row in rows:
     i=bisect.bisect_left(phasetimes,row['owner']['entry']['cck'])-1;j=bisect.bisect_right(phasetimes,row['owner']['exit']['cck'])
     assert i>=0 and j<len(phasewrites)
     row['whole_owner_bracket']=dict(before=phasewrites[i],after=phasewrites[j],cck=phasetimes[j]-phasetimes[i],includes='Complete tutorial_background call/return plus enclosing main-loop and timer-accounting work; finite bus timestamp upper bracket.')
    assert all(len(x['body'])==1 for x in rows),'Expected exactly one actual top-level stage body per API'
    assert rows and all(x['planned_stage']==1 and x['planned_cost']==4000 for x in rows)
    out=dict(schema=1,standard=r['standard'],native_clock_hz=hz,scope=__doc__,report=str(p),bindings={str(q):h(q) for q in (p,exe,p.parent/'native.lst',Path(__file__),ROOT/'scripts/build_match_core.py',ROOT/'scripts/serve_stage_discovery.py',ROOT/'scripts/native_tools.py')},passed_report=r['passed'],count=len(rows),max_whole_owner_bracket_cck=max(x['whole_owner_bracket']['cck'] for x in rows),all_complete_owner_brackets_under_4000_e=all(x['whole_owner_bracket']['cck']<=20000 for x in rows),max_owner_bus_cck=max(x['owner']['elapsed_bus_cck'] for x in rows),all_bus_spans_under_4000_e=all(x['reserve_bus_margin_cck']>=0 for x in rows),limitations=['Reduction validates exported completed stack rows, not independent replay of literal RPC observations.','Owner begins call-stack store complete and ends last RTS stack read; entry/return instruction tails unclassified.','Intrinsic spans include nested ownership and IRQ elapsed but omit tails; enclosing timer brackets qualify finite complete-owner upper observations. Neither establishes WCET or unseen-case qualification.','Classifier fixtures and native fresh admission are separate evidence.','Older field_rows exports only watched base-address writes; newer exports all watchedbytes. Planvalues are reconstructed from width-qualified writes, never inferred from missing subwords.'],rows=rows)
    bybody={}
    for row in rows:bybody.setdefault(row['body'][0],[]).append(row)
    out['summary_by_body']={name:dict(count=len(xs),owner_bus_min_cck=min(x['owner']['elapsed_bus_cck'] for x in xs),owner_bus_max_cck=max(x['owner']['elapsed_bus_cck'] for x in xs),complete_owner_upper_max_cck=max(x['whole_owner_bracket']['cck'] for x in xs),variants=sorted(set(x['variant'] for x in xs))) for name,xs in bybody.items()}
    out['max_whole_owner_bracket_e']=out['max_whole_owner_bracket_cck']/5
    out['max_whole_owner_bracket_ms']=out['max_whole_owner_bracket_cck']*1000/hz
    out['all_ten_bodies_observed']=set(bybody)==set(STAGES)
    if not include_rows:out.pop('rows')
    return out

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('report',type=Path)
    ap.add_argument('--include-rows',action='store_true',help='Include detailed owner/body/timer boundary rows')
    ap.add_argument('--output',type=Path,help='Write a new reduction; refuses to overwrite an existing file')
    args=ap.parse_args();result=reduce(args.report,args.include_rows);text=json.dumps(result,indent=2)+'\n'
    if args.output:
        with args.output.open('x') as f:f.write(text)
    else:print(text,end='')
if __name__=='__main__':main()
