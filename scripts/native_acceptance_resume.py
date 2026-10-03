"""Complete the preserved2219 gate with explicitly verified composite evidence."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from native_tools import ROOT
from native_evidence import atomic_json,digest,python_inputs
from native_composite import BASE,PLAN_ENV,verified_status
from progress import RECEIPTS,acceptance

SOURCE=ROOT/'build/tests/retained-restart-failure-2219fd6/report.json'
DIRECTORY=ROOT/'build/acceptance/composite'
PLAN=DIRECTORY/'plan.json'
PRODUCT={
 'build/amiga/interfaces/enhanced/baseline-rally':'1a5286650df54e65d4a3339557b1b54f5a0a7c398fcd552b3c7537e14d547e72',
 'build/amiga/interfaces/enhanced/delivery/baseline-rally':'4ee3c2b2c2e2e67e418c372997609cb21c05afb8f06508d74b4e8371e7993911',
 'build/amiga/interfaces/enhanced/delivery/baseline-rally.adf':'ff37da95d9adcb779ac276f5123125a098c964ecb866af2ec9f7ecd247f1be71'}
NAMES={4:'menu-cold',5:'inputs',6:'video-clock',7:'sprite-dma-pal',8:'sprite-dma-ntsc',9:'scoreboard',
 **dict(enumerate(('deuce','advantage','return-deuce','advantage-game','match-award','status-2','status-3','status-4','status-5','status-6','audio-hit'),10)),
 25:'demo',26:'takeover',27:'attract-cycles',28:'feedback-one',29:'feedback-two',30:'ordinary-one-cold',31:'ordinary-two',32:'bank-control',33:'restart-audio-early',34:'setup-proposal'}

def receipt_for(i):
 if 10<=i<=20:return ROOT/f'build/tests/native-contracts/{NAMES[i]}/report.json'
 if 21<=i<=24:
  return ROOT/f"build/tests/ct13-{('blue','red')[i%2==0]}-{('normal','exchanged')[i>=23]}/report.json"
 return ROOT/'build'/RECEIPTS[NAMES[i]]

def command_for(i,source):
 if i<34:return source['commands'][i]['command'][1:]
 return {34:['scripts/run_native_setup_tests.py','--self-test'],35:['scripts/build_native_adf.py','--self-test'],36:['scripts/native_metrics.py','--require-runtime']}[i]

def make_plan():
 source=json.loads(SOURCE.read_text())
 if source['commit']!=BASE or len(source['commands'])!=34 or source['commands'][-1]['exit_code']!=1:
  raise ValueError('Unexpected preserved failed gate')
 if any(r['exit_code'] for r in source['commands'][:33]):raise ValueError('Preserved pass prefix is not successful')
 if any(digest(ROOT/p)!=sha for p,sha in PRODUCT.items()):raise ValueError('Product differs from approved unchanged bytes')
 receipts={}
 for i in range(4,34):
  path=receipt_for(i)
  if not path.exists():continue
  report=json.loads(path.read_text());meta=report.get('evidence',{})
  if report.get('passed') is not True or meta.get('state')!='complete':continue
  expected=command_for(i,source)
  actual=meta['command']
  if Path(actual[0]).name!=Path(expected[0]).name or actual[1:]!=expected[1:]:raise ValueError(f'Stage{i} command mismatch')
  rel=str(path.relative_to(ROOT))
  archived=DIRECTORY/'original-receipts'/rel
  archived.parent.mkdir(parents=True,exist_ok=True);archived.write_bytes(path.read_bytes())
  receipts[rel]={'sha256':digest(path),'archive':str(archived.relative_to(ROOT)),
                'commit':meta['commit'],'command':actual,'started_utc':meta['started_utc'],
                'completed_utc':meta.get('completed_utc'),'stage':i}
 plan={'base_commit':BASE,'source_gate':str(SOURCE.relative_to(ROOT)),'source_gate_sha256':digest(SOURCE),
       'policy_sha256':digest(ROOT/'scripts/native_composite.py'),'runner_sha256':digest(Path(__file__)),
       'product':PRODUCT,'receipts':receipts,'scope':'Composite verified evidence; original receipts are preserved, never relabeled as a fresh single-head campaign.'}
 atomic_json(PLAN,plan);return source,plan

def verify(i,plan):
 path=receipt_for(i);rel=str(path.relative_to(ROOT));binding=plan['receipts'].get(rel)
 if not binding or digest(path)!=binding['sha256']:return {'status':'stale','reason':'Bound receipt missing or superseded'}
 result=verified_status(path,subject='maintained-native-mutant' if i==32 else 'maintained-native',plan=plan)
 if result['status']=='passed' and i in NAMES and not acceptance(NAMES[i],json.loads(path.read_text())):
  return {'status':'failed','reason':'Required original native extent/assertions absent'}
 return dict(result,receipt=rel,receipt_sha256=binding['sha256'],source_commit=binding['commit'],
             started_utc=binding['started_utc'],completed_utc=binding['completed_utc'])

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
 DIRECTORY.mkdir(parents=True,exist_ok=True)
 source,plan=make_plan();results={i:verify(i,plan) for i in range(4,35)}
 print(json.dumps({'verification':results}),flush=True)
 if args.verify_only:return 0 if all(results[i]['status']=='passed' for i in range(4,34)) else 1
 head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
 if subprocess.run(['git','diff','--quiet','HEAD'],cwd=ROOT).returncode:raise ValueError('Commit the composite verifier/observer before execution')
 report={'commit':head,'base_commit':BASE,'mode':'composite_verified','passed':False,'state':'incomplete',
         'started_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'product':PRODUCT,'plan_sha256':digest(PLAN),'commands':[]}
 for i in range(37):
  args=command_for(i,source)
  reuse=results.get(i) if i!=34 else None
  if reuse and reuse['status']=='passed':
   row={'stage':i,'command':[sys.executable,*args],'exit_code':0,'evidence':reuse,
        'disposition':'preserved_pass' if i<33 else 'fresh_repair_pass'}
   print('VERIFIED',i,row['disposition'],flush=True)
  elif i==3:
   row={'stage':i,'command':[sys.executable,*args],'exit_code':0,'disposition':'covered_by_identical_fresh_stage35',
        'original_successful_log':source['commands'][3]['log'],'original_log_sha256':digest(ROOT/source['commands'][3]['log'])}
  else:
   begin=dt.datetime.now(dt.timezone.utc).isoformat();log=DIRECTORY/f'{i:02d}-{Path(args[0]).stem}.log'
   print('RUN',i,' '.join(args),flush=True)
   with log.open('w') as out:
    r=subprocess.run([sys.executable,*args],cwd=ROOT,env=dict(os.environ,RUST_LOG='info',**{PLAN_ENV:str(PLAN)}),stdout=out,stderr=subprocess.STDOUT)
   row={'stage':i,'command':[sys.executable,*args],'exit_code':r.returncode,'disposition':'fresh_run',
        'started_utc':begin,'completed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'log':str(log.relative_to(ROOT)),
        'log_sha256':digest(log),'input_fingerprints':{str(p.relative_to(ROOT)):digest(p) for p in python_inputs(ROOT/args[0]) if p.is_relative_to(ROOT)} if args[0]!='-m' else {str(p.relative_to(ROOT)):digest(p) for p in (ROOT/'tests/unit').glob('*.py')}}
   if 4<=i<=34 and r.returncode==0:
    path=receipt_for(i);fresh=json.loads(path.read_text());meta=fresh['evidence']
    rel=str(path.relative_to(ROOT));plan['receipts'][rel]={'sha256':digest(path),'commit':meta['commit'],'command':meta['command'],'stage':i,
      'started_utc':meta['started_utc'],'completed_utc':meta['completed_utc']}
    atomic_json(PLAN,plan);row['evidence']=verify(i,plan)
    if row['evidence']['status']!='passed':row['exit_code']=1
  report['commands'].append(row);atomic_json(DIRECTORY/'report.json',report)
  if row['exit_code']:
   report.update(state='failed',first_failure=row);atomic_json(DIRECTORY/'report.json',report);return row['exit_code']
 final={i:verify(i,plan) for i in range(4,35)}
 package=json.loads((ROOT/'build/amiga/interfaces/enhanced/delivery/package-report.json').read_text())
 unchanged=(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==head and subprocess.run(['git','diff','--quiet','HEAD'],cwd=ROOT).returncode==0)
 report.update(state='complete',completed_utc=dt.datetime.now(dt.timezone.utc).isoformat(),head_unchanged=unchanged,
   plan_sha256=digest(PLAN),final_receipt_verification=final,
   passed=unchanged and all(r['status']=='passed' for r in final.values()) and package.get('passed') is True and package.get('reproducibility',{}).get('two_clean_builds') is True and all(digest(ROOT/p)==sha for p,sha in PRODUCT.items()))
 atomic_json(DIRECTORY/'report.json',report);atomic_json(ROOT/'build/acceptance/report.json',report)
 print(json.dumps({'passed':report['passed'],'report':str(DIRECTORY/'report.json')}),flush=True)
 return 0 if report['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
