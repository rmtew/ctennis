"""Exclusive, durable finite campaigns; resume is between cases, never mid-case.

Uses existing native receipts unchanged. A detached controller owns its children
and socket clients. A reconnecting caller monitors it, rather than adopting its
emulator connection. Executor/container destruction can still interrupt a case.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import socket
import shutil
import subprocess
import sys
import time
import uuid

from native_evidence import atomic_json, digest, now, python_inputs, snapshot, status, changed
from native_tools import ROOT
from acceptance_cases import cases
from progress import acceptance

def read(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError,ValueError):
        return None

def process_identity(pid=None):
    pid = pid or os.getpid()
    try:
        # comm can contain spaces and parentheses; fields follow the final ')'.
        fields = Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()
        if fields[0] == 'Z':
            return None
        return dict(host=socket.gethostname(), boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                    pid=pid, start=fields[19], group=int(fields[2]))
    except (OSError,IndexError,ValueError):
        return None

def alive(identity):
    return bool(identity and process_identity(identity.get('pid')) == identity)

class WorkspaceLock:
    def __init__(self, build):
        self.path = Path(build).resolve()/'.acceptance-workspace.lock'
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.fd = os.open(self.path,os.O_RDWR|os.O_CREAT,0o600)
        try:
            fcntl.flock(self.fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            os.close(self.fd)
            raise RuntimeError('Shared build/test workspace is owned; monitor its campaign')
    def close(self):
        os.close(self.fd)

def canonical(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def orchestration_identity():
    directory=Path(__file__).resolve().parent
    return snapshot(directory/name for name in ('acceptance_campaign.py','acceptance_cases.py','native_acceptance.py'))

def commit_provenance(root):
    result=subprocess.run(['git','rev-parse','HEAD'],cwd=root,capture_output=True,text=True)
    dirty=subprocess.run(['git','diff','--quiet','HEAD'],cwd=root,capture_output=True).returncode
    return {'commit':result.stdout.strip() if result.returncode==0 else None,'tracked_clean':dirty==0}

def dependencies(case, root=ROOT):
    """Case observer closure plus conservative unclassified input fallback.

    Source closures and tools remain mandatory until a current compiled manifest
    proves the exact consumed bytes. No old report is rehashed to make it fresh.
    """
    root=Path(root)
    paths = python_inputs(root/case.args[0]) if case.args[0]!='-m' else set()
    manifests=[]
    if case.category=='native':
        # The emitted development product and listing are shared by native
        # observers; fixture reports additionally bind their own actual hunks.
        manifest=read(root/'build/amiga/interfaces/enhanced/baseline-rally.compile.json')
        if manifest and not changed(manifest.get('files',{})):
            manifests.append(manifest)
            paths.update(root/p for p in manifest['files'])
        else:
            # A missing/changed product cannot be assumed equivalent without
            # assembling it. Fall back conservatively, with an explicit reason.
            for directory in ('amiga','assets'):
                paths.update(p for p in (root/directory).rglob('*') if p.is_file())
        if case.id.startswith(('demo','takeover')) or case.id=='attract':
            paths.update(p for p in (root/'tests/fixtures/native-demo').rglob('*') if p.is_file())
        # Immutable independent scoreboard/font contracts used by raster readers.
        paths.update(p for p in (root/'docs/sprites').glob('*.json'))
        for prefix in ('assets/interface/font-mac','assets/interface/title'):
            paths.update(p for p in (root/prefix).rglob('*') if p.is_file())
    else:
        # Host collectors/unknown categories can execute dynamic subprocesses;
        # their declared fallback deliberately retains the full input closure.
        for directory in ('amiga','assets','tests/unit','tests/fixtures'):
            paths.update(p for p in (root/directory).rglob('*') if p.is_file())
        paths.update((root/'scripts').glob('*.py'))
    paths.update((root/'tools.lock.json',root/'config.local.ini',Path(sys.executable)))
    from configparser import ConfigParser
    cfg=ConfigParser(interpolation=None);cfg.read(root/'config.local.ini')
    for section, name in (('tools','copperline'),('inputs','amiga_rom')):
        paths.add(Path(cfg.get(section,name,fallback=str(root/('missing-'+name)))))
    paths.add(root/'.tools/vasm/vasmm68k_mot.exe')
    return {'policy':'compiled-product-and-observer-v1' if manifests else 'conservative-source-and-observer-closure-v1','files':snapshot(paths),
            'consumed_products':{m['executable']:m['executable_sha256'] for m in manifests},
            'command':[sys.executable,*case.args],'environment':{'RUST_LOG':'info','PYTHONPATH':os.environ.get('PYTHONPATH')},
            'target':'PAL/NTSC A500 68000 OCS 512K chip, case command/receipt defines exact extent'}

def compatible_receipt(case, root=ROOT):
    """Import only the latest exact-CLI passing receipt, with original provenance."""
    if case.category=='core-proof':
        from campaign_core_evidence import validate
        return validate(case,root)
    if not case.report:
        return None, 'No independently verifiable native receipt; run required'
    path=Path(root)/'build'/case.report
    report=read(path)
    if not report:
        return None,'Missing or unreadable latest receipt'
    row=status(path)
    if row['status']!='passed':
        return None,'Latest receipt '+row['status']+': '+str(row.get('reason',row.get('changed_dependencies','')))
    meta=report['evidence']
    command=meta.get('command',[])
    if not command or Path(command[0]).name!=Path(case.args[0]).name or command[1:]!=list(case.args[1:]):
        return None,'Full command/negative controls differ'
    if not required_extent(case,report):
        return None,'Required case extent absent'
    # Startup/selector and tail cases use their own exact command and passed
    # receipt, not a similarly named progress row. All files/artifacts in the
    # original receipt were verified by status() above.
    return {'path':str(path),'sha256':digest(path),'original_evidence':meta,
            'artifacts':meta['files'],'classification':'reused'}, 'Compatible latest receipt'

def required_extent(case,report):
    if report.get('passed') is not True:return False
    if case.extent and not acceptance(case.extent,report):return False
    if case.id=='video-standard':
        rows=report.get('rows',[])
        return (report.get('state')=='complete' and [r.get('frequency') for r in rows]==list(range(256))
                and all(r.get('passed') and r.get('actual')==r.get('expected') for r in rows)
                and bool(report.get('loaded_hunks')) and all(r.get('matched') for r in report['loaded_hunks']))
    if case.id=='startup':
        rows=report.get('cases',[])
        return ([(r.get('standard'),r.get('slow_ram')) for r in rows]==[('PAL','0'),('NTSC','0'),('PAL','512K'),('NTSC','512K')]
                and all(r.get('passed') and r.get('hardware_cop1lc')==r.get('presentation_copper')
                        and r.get('loaded_hunks') and all(h.get('matched') for h in r['loaded_hunks']) for r in rows))
    if case.id in ('takeover-tail','takeover-sound'):
        return (report.get('takeover') is True and report.get('takeover_tail') is True
                and report.get('takeover_round_sound') is (case.id=='takeover-sound')
                and report.get('takeover_confirmation_lifecycle') in ((5,) if case.id=='takeover-sound' else (4,5))
                and report.get('verified_input_ticks',0)>0 and report.get('missed_publications')==0
                and isinstance(report.get('entropy_request_observed'),bool))
    return True

def fresh_receipt(case,root,dependency_key):
    """Bind newly executed legacy observers without upgrading historical results."""
    path=Path(root)/'build'/case.report; report=read(path)
    if not report or not required_extent(case,report):return None
    if case.id not in ('startup','video-standard'):return None
    # These two observers lack ReportRun metadata. Only execution by this
    # controller can supply their missing identities; historical reports stay
    # ineligible. Capture emitted fixture/release bytes and all local artifacts.
    artifacts=snapshot(p for p in path.parent.rglob('*') if p.is_file())
    if case.id=='startup':
        product=Path(root)/'build/amiga/interfaces/enhanced'
        artifacts.update(snapshot([product/'delivery/baseline-rally',product/'delivery/baseline-rally.adf',product/'native.lst']))
        if (report.get('release_sha256')!=digest(product/'delivery/baseline-rally')
                or report.get('adf_sha256')!=digest(product/'delivery/baseline-rally.adf')):return None
    else:
        if report.get('executable_sha256')!=digest(path.parent/'fixture'):return None
    return {'path':str(path),'sha256':digest(path),'original_evidence':None,'artifacts':artifacts,
            'classification':'fresh-controller-bound','dependency_key':dependency_key}

def attempt_valid(attempt, case, deps, root=ROOT):
    if not attempt or attempt.get('state')!='complete' or attempt.get('exit_code')!=0:
        return False
    if attempt.get('dependency_key')!=canonical(deps) or changed(attempt.get('artifacts',{})):
        return False
    if attempt.get('orchestration')!=orchestration_identity():return False
    if case.report:
        saved=attempt.get('receipt',{})
        if saved.get('classification')=='fresh-controller-bound':
            path=Path(saved['path']);report=read(path)
            return bool(digest(path)==saved['sha256'] and not changed(saved['artifacts'])
                        and report and required_extent(case,report))
        imported,_=compatible_receipt(case,root)
        # The mutable latest receipt is authoritative even if an old immutable
        # attempt passed. A newer failure/incomplete result cannot hide behind it.
        return bool(imported)
    return True

def plan(case_list, directory, root=ROOT):
    result=[]
    for case in case_list:
        deps=dependencies(case,root)
        attempts=sorted((Path(directory)/'attempts'/case.id).glob('*'))
        latest=read(attempts[-1]/'completion.json') if attempts else None
        if attempts and not attempt_valid(latest,case,deps,root):
            # A latest same-key failure must be run, never search older passes.
            receipt=None;reason='Latest campaign attempt failed, incomplete or invalidated'
            if (latest and latest.get('state')=='complete' and latest.get('exit_code')==0
                    and latest.get('orchestration')!=orchestration_identity()):
                receipt,reason=compatible_receipt(case,root)
                reason='Orchestrator history invalidated; '+reason
        elif attempt_valid(latest,case,deps,root):
            receipt=latest.get('receipt');reason='Compatible completed campaign attempt'
        else:
            receipt,reason=compatible_receipt(case,root)
        result.append({'id':case.id,'action':'reuse' if receipt or attempt_valid(latest,case,deps,root) else 'run',
                       'reason':reason,'dependencies':deps,'dependency_key':canonical(deps),'receipt':receipt,
                       'prior_artifacts':dict(latest.get('artifacts',{}),**{str(attempts[-1]/'completion.json'):digest(attempts[-1]/'completion.json')}) if latest and attempt_valid(latest,case,deps,root) else {}})
    return result

def tagged_processes(campaign_id, owner=None):
    """Missing /proc access is ambiguous and blocks reclaim; never PID-only."""
    found=[]
    if not owner:return found
    current=process_identity()
    if owner.get('boot')!=current['boot']:return found
    marker=('CTENNIS_CAMPAIGN_ID='+campaign_id).encode()
    for item in Path('/proc').iterdir():
        if not item.name.isdigit() or int(item.name)==os.getpid():continue
        try:
            identity=process_identity(int(item.name))
            if not identity or int(identity['start'])<int(owner['start']):continue
            if identity['group']==owner['group']:
                found.append(identity);continue
            if marker in (item/'environ').read_bytes().split(b'\0'):
                if identity:found.append(identity)
        except FileNotFoundError:pass
        except PermissionError:
            # /proc/environ can deny access while a process is exiting, after
            # its first stat read. Recheck the complete identity before calling
            # that a live ownership ambiguity; never waive a live denial.
            current_identity=process_identity(int(item.name))
            if not current_identity or current_identity!=identity:continue
            # Other users are outside this controller's process ownership.
            try:
                same_user=item.stat().st_uid==os.getuid()
            except FileNotFoundError:
                continue
            if same_user:raise RuntimeError('Cannot verify owned descendant identity')
    return found

def require_idle_workspace(root=ROOT):
    """A new campaign cannot bypass an orphan from a differently named one."""
    previous=read(Path(root)/'build/acceptance-active.json')
    if not previous:return
    owner=previous.get('controller') or {}
    if owner.get('host')!=socket.gethostname():
        raise RuntimeError('Prior workspace owner is on another host; cannot establish it stopped')
    if alive(owner):raise RuntimeError('Shared workspace controller is still running')
    if tagged_processes(previous['campaign'],owner):
        raise RuntimeError('Prior workspace campaign has live descendants; refusing duplicate work')

def preserve_artifacts(files,directory):
    """Content-addressed copies survive canonical report/build overwrites.

    Sources/tools outside build remain dependency hashes. Private build evidence
    is retained, never moved or deleted; copy failure fails the attempt.
    """
    result={};objects=Path(directory)/'objects';objects.mkdir(exist_ok=True)
    for name,sha in files.items():
        source=ROOT/ name
        if not source.resolve().is_relative_to((ROOT/'build').resolve()):continue
        if not sha or digest(source)!=sha:raise ValueError('Artifact changed before preservation: '+name)
        target=objects/sha
        if not target.exists():
            temporary=objects/(sha+'.'+uuid.uuid4().hex)
            shutil.copyfile(source,temporary)
            if digest(temporary)!=sha:
                temporary.unlink();raise ValueError('Artifact changed during preservation: '+name)
            os.replace(temporary,target)
        if digest(target)!=sha:raise ValueError('Immutable object corrupted: '+str(target))
        result[str(target)]=sha
    return result

def worker(directory, case_list, root=ROOT, lock_fd=None):
    directory=Path(directory); campaign=read(directory/'campaign.json')
    if not campaign:raise ValueError('Missing campaign record')
    held=WorkspaceLock(Path(root)/'build') if lock_fd is None else None
    try:
        previous=read(directory/'owner.json')
        if previous and alive(previous.get('controller')):
            raise RuntimeError('Controller already running; monitor it')
        if previous and (previous.get('controller') or {}).get('host')!=socket.gethostname():
            raise RuntimeError('Prior owner belongs to another host; cannot establish it stopped')
        descendants=tagged_processes(campaign['id'],previous.get('controller') if previous else None)
        if descendants:raise RuntimeError('Prior campaign descendants are live; refusing duplicate work')
        atomic_json(directory/'owner.json',{'controller':process_identity(),'campaign':campaign['id']})
        atomic_json(Path(root)/'build/acceptance-active.json',{'controller':process_identity(),'campaign':campaign['id'],
                    'directory':str(directory),'resolved_build':str((Path(root)/'build').resolve())})
        atomic_json(directory/'report.json',{'campaign':campaign['id'],'state':'incomplete','passed':False,'cases':[]})
        os.environ['CTENNIS_CAMPAIGN_ID']=campaign['id']
        fd=held.fd if held else lock_fd
        rows=[]
        for case in case_list:
            decision=plan([case],directory,root)[0]
            base=directory/'attempts'/case.id;base.mkdir(parents=True,exist_ok=True)
            attempt=base/f'{len(list(base.iterdir()))+1:06d}';attempt.mkdir()
            started=now(); artifact={}
            provenance=commit_provenance(root);orchestration=orchestration_identity()
            atomic_json(attempt/'started.json',dict(decision,started_utc=started,controller=process_identity(),
                        provenance=provenance,orchestration=orchestration))
            if decision['action']=='reuse':
                code=0;receipt=decision['receipt']
                artifact.update(decision['prior_artifacts'])
            else:
                receipt=None
                with (attempt/'child.log').open('wb') as output:
                    child=subprocess.Popen([sys.executable,*case.args],cwd=root,
                        env=dict(os.environ,RUST_LOG='info'),stdout=output,stderr=subprocess.STDOUT,
                        pass_fds=(fd,))
                    atomic_json(attempt/'child.json',{'identity':process_identity(child.pid),'command':[sys.executable,*case.args]})
                    code=child.wait()
                artifact=snapshot([attempt/'child.log'])
                if code==0 and case.report:
                    receipt,reason=compatible_receipt(case,root)
                    if not receipt:receipt=fresh_receipt(case,root,decision['dependency_key'])
                    if not receipt:code=1;decision['validation_error']=reason
                if code==0 and changed(decision['dependencies']['files']):
                    code=1;decision['validation_error']='Dependencies changed during execution'
                if code==0 and orchestration_identity()!=orchestration:
                    code=1;decision['validation_error']='Orchestration changed during execution'
                if code==0:
                    decision['dependencies']=dependencies(case,root)
                    decision['dependency_key']=canonical(decision['dependencies'])
            if receipt:
                # Preserve the exact receipt bytes before another case can
                # overwrite its canonical path; original artifact paths remain
                # hash-bound, not silently copied/upgraded.
                value=read(receipt['path']);atomic_json(attempt/'receipt.json',value)
                artifact.update(snapshot([attempt/'receipt.json']))
                artifact.update(preserve_artifacts(receipt['artifacts'],directory))
            complete=dict(decision,state='complete' if code==0 else 'failed',exit_code=code,
                          started_utc=started,completed_utc=now(),receipt=receipt,artifacts=artifact,
                          provenance=provenance,orchestration=orchestration)
            atomic_json(attempt/'completion.json',complete)
            rows.append({'id':case.id,'attempt':str(attempt),'exit_code':code,'classification':decision['action']})
            atomic_json(directory/'report.json',{'campaign':campaign['id'],'state':'incomplete' if code==0 else 'failed','passed':False,'cases':rows})
            if code:return code
        coverage={}
        for case,row in zip(case_list,rows):
            completion=read(Path(row['attempt'])/'completion.json')
            coverage[case.id]=attempt_valid(completion,case,dependencies(case,root),root)
        passed=all(coverage.values())
        from campaign_core_evidence import core_cases
        mandatory={c.id for c in cases()+core_cases()}
        full=mandatory<={c.id for c in case_list}
        atomic_json(directory/'report.json',{'campaign':campaign['id'],'state':'complete' if passed else 'failed','passed':passed,
                    'completed_utc':now(),'cases':rows,'case_ids':[c.id for c in case_list],
                    'coverage':coverage,'full_native_catalog_covered':{c.id for c in cases()}<={c.id for c in case_list},
                    'acceptance_passed':passed and full,'mandatory_case_ids':sorted(mandatory),
                    'scope':'Complete native/core catalog' if full else 'Selected catalog cases only'})
        return 0 if passed else 1
    finally:
        if held:held.close()

def monitor(directory, child=None):
    """Only observes controller/atomic receipts; never opens emulator sockets."""
    directory=Path(directory)
    last=None
    try:
        while True:
            owner=read(directory/'owner.json')
            if not owner:
                active=read(ROOT/'build/acceptance-active.json')
                if active and active.get('directory')==str(directory):owner=active
            report=read(directory/'report.json')
            detail=(report or {}).get('cases',[])
            if len(detail)!=last:
                print(json.dumps({'campaign':directory.name,'completed_cases':len(detail),'state':(report or {}).get('state','starting')}),flush=True)
                last=len(detail)
            running=child.poll() is None if child is not None else bool(owner and alive(owner.get('controller')))
            if not running:
                if ((child is not None and child.returncode!=0) or not report
                        or report.get('state')!='complete' or not report.get('passed')):
                    print(json.dumps({'campaign':directory.name,'state':'failed-or-interrupted','report':report}),flush=True);return 1
                catalog=cases()
                from campaign_core_evidence import core_cases
                catalog+=core_cases()
                selected=[c for c in catalog if c.id in report.get('case_ids',[])]
                if (len(selected)!=len(report.get('case_ids',[]))
                        or any(r['action']!='reuse' for r in plan(selected,directory))):
                    print(json.dumps({'campaign':directory.name,'state':'invalidated','reason':'Completed cases no longer have compatible latest evidence'}),flush=True);return 1
                print(json.dumps({'campaign':directory.name,'state':'complete','passed':True,
                    'acceptance_passed':report.get('acceptance_passed',False),'scope':report.get('scope'),
                    'report':str(directory/'report.json')}),flush=True);return 0
            time.sleep(1)
    except KeyboardInterrupt:
        print('Monitor detached; controller remains owned by campaign '+directory.name,flush=True)
        return 130

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--campaign');parser.add_argument('--start',action='store_true')
    parser.add_argument('--resume',action='store_true');parser.add_argument('--worker',action='store_true')
    parser.add_argument('--run',action='store_true');parser.add_argument('--monitor',action='store_true');parser.add_argument('--plan',action='store_true')
    parser.add_argument('--details',action='store_true',help='Include complete dependency hashes in preflight output')
    parser.add_argument('--case',action='append');parser.add_argument('--lock-fd',type=int)
    args=parser.parse_args(); case_list=cases()
    try:
        from campaign_core_evidence import core_cases
        case_list += core_cases()
    except ModuleNotFoundError as error:
        if error.name!='campaign_core_evidence':raise
    if args.case:
        unknown=set(args.case)-{c.id for c in case_list}
        if unknown:parser.error('Unknown stable case IDs: '+str(sorted(unknown)))
        case_list=[c for c in case_list if c.id in args.case]
    directory=ROOT/'build/acceptance/campaigns'/(args.campaign or uuid.uuid4().hex)
    if args.resume and not args.case:
        saved=read(directory/'campaign.json')
        if saved:case_list=[c for c in case_list if c.id in saved['case_ids']]
    if args.worker:return worker(directory,case_list,lock_fd=args.lock_fd)
    owner=read(directory/'owner.json')
    active=read(ROOT/'build/acceptance-active.json')
    if args.plan and active and alive(active.get('controller')):
        print(json.dumps({'action':'already-running','owner':active,'reason':'Exclusive shared build/test workspace has an active controller'}));return 0
    if owner and alive(owner.get('controller')):
        if args.run or args.monitor:return monitor(directory)
        print(json.dumps({'action':'already-running','campaign':directory.name,'owner':owner,'report':read(directory/'report.json')}));return 0
    if args.monitor:return monitor(directory)
    if args.start or args.resume or args.run:
        if args.resume and not (directory/'campaign.json').exists():parser.error('Unknown campaign')
        lock=WorkspaceLock(ROOT/'build')
        try:
            require_idle_workspace(ROOT)
            full_catalog=cases()
            from campaign_core_evidence import core_cases
            full_catalog+=core_cases()
            if {c.id for c in case_list}=={c.id for c in full_catalog}:
                if subprocess.run(['git','diff','--quiet','HEAD'],cwd=ROOT).returncode:
                    raise ValueError('Run the complete acceptance campaign at a committed clean head')
                untracked=subprocess.check_output(['git','ls-files','--others','--exclude-standard','--','scripts','amiga','tests','docs','tools.lock.json'],cwd=ROOT,text=True)
                if untracked.strip():raise ValueError('Commit the untracked acceptance inputs before a complete campaign')
                if any((ROOT/name).exists() for name in ('tests/reference','build/reference','build/translation','analysis','tooling','roms')):
                    raise ValueError('Original inputs/obsolete directories present in gate checkout')
            if not args.resume:
                directory.mkdir(parents=True,exist_ok=False)
                atomic_json(directory/'campaign.json',{'schema':1,'id':directory.name,'created_utc':now(),
                    'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                    'root':str(ROOT),'resolved_build':str((ROOT/'build').resolve()),'case_ids':[c.id for c in case_list]})
            else:
                saved=read(directory/'campaign.json')
                if saved['case_ids']!=[c.id for c in case_list]:parser.error('Resume must preserve saved case selection')
                if saved['resolved_build']!=str((ROOT/'build').resolve()):parser.error('Shared workspace identity changed')
            command=[sys.executable,str(Path(__file__).resolve()),'--worker','--campaign',directory.name,'--lock-fd',str(lock.fd)]
            # The worker receives the resolved saved selection, including core
            # cases. Forwarding only CLI --case would expand a selected resume.
            for case in case_list:command += ['--case',case.id]
            with (directory/f'controller-{uuid.uuid4().hex}.log').open('wb') as output:
                child=subprocess.Popen(command,cwd=ROOT,stdout=output,stderr=subprocess.STDOUT,start_new_session=True,pass_fds=(lock.fd,))
            atomic_json(ROOT/'build/acceptance-active.json',{'controller':process_identity(child.pid),'campaign':directory.name,
                        'directory':str(directory),'resolved_build':str((ROOT/'build').resolve())})
            print(json.dumps({'action':'started','campaign':directory.name,'controller':process_identity(child.pid),'directory':str(directory)}))
        finally:lock.close()
        if args.run:return monitor(directory,child)
        return 0
    decisions=plan(case_list,directory)
    if not args.details:
        decisions=[{'id':r['id'],'action':r['action'],'reason':r['reason'],'dependency_key':r['dependency_key'],
                    'command':r['dependencies']['command'],'environment':r['dependencies']['environment'],
                    'dependency_policy':r['dependencies']['policy'],'dependency_files':len(r['dependencies']['files']),
                    'consumed_products':r['dependencies']['consumed_products'],
                    'receipt':{k:v for k,v in (r['receipt'] or {}).items() if k in ('path','sha256','classification')}} for r in decisions]
    print(json.dumps({'campaign':directory.name,'plan':decisions},indent=2));return 0

if __name__=='__main__':raise SystemExit(main())
