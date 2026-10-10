"""Isolated actual CPU serve classifier thresholds; no live admission or native bound."""
import json,hashlib,shutil,traceback
from pathlib import Path
from uuid import uuid4
from build_match_core import load_image
from match_core_cpu import Core,cpu_tool_inputs
from run_shared_match_core import READONLY
from serve_stages_cpu_proof import setup,snapshot,summary
from history_proof import field
from native_tools import ROOT

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 src=ROOT/'build/tests/tutorial-serve-pal/224fcde4f1914c85ac5a1b0b0a3591f6';out=ROOT/'build/tests/serve-stage-classifier'/uuid4().hex;out.mkdir(parents=True)
 for n in ('baseline-rally','native.lst'):shutil.copy2(src/n,out/n)
 shutil.copy2(Path(__file__),out/Path(__file__).name)
 image,s=load_image(out/'baseline-rally');report=dict(passed=False,scope=__doc__,cases=[])
 try:
  tools,info=cpu_tool_inputs();paths=[out/'baseline-rally',out/'native.lst',out/Path(__file__).name]+[ROOT/'scripts'/n for n in ('serve_stages_cpu_proof.py','match_core_cpu.py','build_match_core.py','history_proof.py','run_shared_match_core.py')]+list(tools)
  report.update(bindings={str(p):sha(p) for p in paths},cpu=info)
  for v in (0,1):
   for pending in (False,True):
    for mode in ('4999','5000','5001','cancel','invalid-generation'):
     with Core(image,s,readonly=dict(READONLY,game_preview_dispatch_stage_bodies=40)) as c:
      g=setup(c,0)
      if pending:c.call('game_preview_dispatch_stage',{0:g,1:v});assert c.cpu.r_reg(0)==1 and c.cpu.r_reg(1)==0
      if mode=='cancel':c.call('game_preview_cancel',{0:g});assert c.cpu.r_reg(0)==1
      # Declared scheduler fixture only, before tested call; actual private state untouched.
      c.mutable_regions.append((s['tutorial_state'],s['tutorial_state_end']))
      c.mem.w_block(s['tutorial_state'],bytes(s['tutorial_state_end']-s['tutorial_state']))
      for n,z,val in [('tutorial_generation',4,g if mode!='invalid-generation' else g+1),('tutorial_job_variant',2,v),('simulation_interval',4,int(mode) if mode.isdigit() else 5001),('simulation_phase',4,0)]:
       c.mutable_regions.append((s[n],s[n]+z));c.mem.w_block(s[n],val.to_bytes(z,'big'))
      owners=snapshot(c);before=summary(c);c.writes.clear();c.clear_events();cycles=c.call('tutorial_background_class')
      result={n:field(c,n,z) for n,z in [('tutorial_job_budget',2),('tutorial_job_stage',2),('tutorial_job_cost',4)]}
      accepted=mode in ('5000','5001');assert result==dict(tutorial_job_budget=int(accepted),tutorial_job_stage=int(accepted),tutorial_job_cost=4000 if accepted else 0),result
      assert snapshot(c)==owners and summary(c)==before and not c.events and not c.preview_events
      allowed=set()
      for n,z in [('tutorial_job_budget',2),('tutorial_job_stage',2),('tutorial_job_cost',4)]:allowed.update(range(s[n],s[n]+z))
      assert c.writes<=allowed;c.audit_reads()
      report['cases'].append(dict(variant=v,pending=pending,mode=mode,result=result,cycles=cycles,unchanged=True,writes_owned=True))
  report['passed']=True
 except Exception:report['error']=traceback.format_exc()
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(out,report['passed'],len(report['cases']))
 if not report['passed']:raise RuntimeError(report['error'])
if __name__=='__main__':main()
