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

def execution_records(case,deps,root=ROOT,directory=None):
    key=canonical(deps);build=(Path(root)/'build').resolve()
    index=build/'.acceptance-case-history'/case.id/key
    starts=[p/'started.json' for p in index.glob('*') if p.is_dir()]
    starts+=list((build/'acceptance/campaigns').glob('*/attempts/'+case.id+'/*/started.json'))
    starts += [p.with_name('started.json') for p in (build/'acceptance/campaigns').glob('*/attempts/'+case.id+'/*/completion.json')]
    if directory:starts+=list((Path(directory)/'attempts'/case.id).glob('*/started.json'))
    runs=[]
    for path in set(starts):
        begin=read(path)
        if path.is_relative_to(index) and (not begin or begin.get('dependency_key')!=key
                                         or begin.get('action') not in ('run','reuse')):
            runs.append((None,str(path),None));continue
        if not begin:begin=read(path.with_name('completion.json'))
        if not begin or begin.get('dependency_key')!=key or begin.get('action')=='reuse':continue
        complete=read(path.with_name('completion.json'))
        stamp=begin.get('started_utc')
        runs.append((stamp,str(path),complete))
    return runs

def execution_blocker(case, deps, root=ROOT, directory=None):
    """Latest actual execution wins; reused passes never clear a failed run."""
    runs=execution_records(case,deps,root,directory)
    for stamp,path,_ in runs:
        if not isinstance(stamp,str):return 'Unverifiable actual execution in shared workspace: '+path
    if not runs:return None
    _,path,latest=max(runs)
    if not latest or latest.get('state')!='complete' or latest.get('exit_code')!=0:
        return 'Latest shared-workspace execution failed or was interrupted: '+path
    return None

def bound_receipt(case,deps,root=ROOT):
    """Reuse only explicit environment bindings made by actual executions."""
    runs=execution_records(case,deps,root)
    if not runs or any(not isinstance(r[0],str) for r in runs):return None
    for _,_,complete in sorted(runs,reverse=True):
        if not complete or complete.get('state')!='complete' or complete.get('exit_code')!=0:continue
        saved=complete.get('receipt') or {}
        if (saved.get('classification')!='fresh-controller-bound'
                or complete.get('dependency_key')!=canonical(deps)
                or saved.get('environment')!=deps['environment']
                or saved.get('environment')!={'RUST_LOG':'info','PYTHONPATH':os.environ.get('PYTHONPATH')}
                or changed(complete.get('artifacts',{})) or changed(saved.get('artifacts',{}))):continue
        path=Path(root)/'build'/case.report;report=read(path)
        if saved.get('path')!=str(path) or digest(path)!=saved.get('sha256'):continue
        if not report or not required_extent(case,report):continue
        if report.get('evidence') and status(path)['status']!='passed':continue
        environment=(report.get('evidence') or {}).get('environment',{})
        if 'PYTHONPATH' in environment and environment['PYTHONPATH']!=os.environ.get('PYTHONPATH'):continue
        return saved
    return None

def dependencies(case, root=ROOT):
    """Case observer closure plus conservative unclassified input fallback.

    Source closures and tools remain mandatory until a current compiled manifest
    proves the exact consumed bytes. No old report is rehashed to make it fresh.
    """
    root=Path(root)
    paths = python_inputs(root/case.args[0]) if case.args[0]!='-m' else set()
    manifests=[]
    optional_absence={}
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
    environment={'RUST_LOG':'info','PYTHONPATH':os.environ.get('PYTHONPATH')}
    if case.id=='metrics':
        from native_metrics import CASES
        product=root/'build/amiga/interfaces/enhanced'
        paths.update((product/'baseline-rally',product/'baseline-rally.compile.json',product/'native.lst',product/'build-report.json'))
        for relative in CASES.values():
            report_path=root/relative;paths.add(report_path);report=read(report_path) or {}
            if isinstance(report.get('capture'),str):paths.add(root/report['capture'])
            meta=report.get('evidence') or {}
            paths.update(root/name for name in meta.get('files',{}))
            paths.update(root/name for name in meta.get('compiled_executables',{}))
            for name in meta.get('optional_inputs_absent',[]):
                optional=root/name;optional_absence[str(optional)]=not optional.exists()
                if optional.exists():paths.add(optional)
        composite=os.environ.get('CTENNIS_ACCEPTANCE_COMPOSITE')
        environment['CTENNIS_ACCEPTANCE_COMPOSITE']=composite
        if composite:paths.add(Path(composite))
    return {'policy':'compiled-product-and-observer-v1' if manifests else 'conservative-source-and-observer-closure-v1','files':snapshot(paths),
            'consumed_products':{m['executable']:m['executable_sha256'] for m in manifests},
            **({'optional_absence':optional_absence} if case.id=='metrics' else {}),
            'command':[sys.executable,*case.args],'environment':environment,
            'target':'PAL/NTSC A500 68000 OCS 512K chip, case command/receipt defines exact extent'}

def compatible_receipt(case, root=ROOT, check_history=True):
    """Import only the latest exact-CLI passing receipt, with original provenance."""
    if check_history:
        blocker=execution_blocker(case,dependencies(case,root),root)
        if blocker:return None,blocker
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
        if case.id in ('startup','video-standard'):
            bound=bound_receipt(case,dependencies(case,root),root)
            if bound:return bound,'Compatible legacy observer bound by prior actual controller execution'
        return None,'Latest receipt '+row['status']+': '+str(row.get('reason',row.get('changed_dependencies','')))
    meta=report['evidence']
    environment=meta.get('environment',{})
    if 'PYTHONPATH' not in environment or environment['PYTHONPATH']!=os.environ.get('PYTHONPATH'):
        bound=bound_receipt(case,dependencies(case,root),root) if 'PYTHONPATH' not in environment else None
        if bound:return bound,'Compatible environment bound by prior actual controller execution'
        return None,'Recorded PYTHONPATH differs or is unverified'
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

def history_negative_extent(proof):
    controls=proof.get('negative_controls')
    if not isinstance(controls,list) or any(not isinstance(c,str) for c in controls):return False
    controls=set(controls)
    return ({'checkpoint-byte-8','checkpoint-byte-10','checkpoint-byte-326','checkpoint-byte-104'}<=controls
            and len({c for c in controls if c.startswith('out-of-range-')})>=2)

def history_boundary_extent(proof):
    retained=proof.get('retained_operations');boundaries=proof.get('boundaries_checked');seeks=proof.get('seeks');operations=proof.get('operations')
    return (type(operations) is int and operations>0 and type(retained) is int and retained>0
            and type(boundaries) is int and boundaries==retained+1
            and type(seeks) is int and seeks>=2*boundaries and history_negative_extent(proof)
            and proof.get('frozen_operations_checked')==9
            and proof.get('register_sr_equivalence_operations')==proof.get('operations')
            and proof.get('failure_preserves_older_position') is True)

def preview_a1_extent(stage):
    """Finite A1 coverage; discovery and native-image proofs remain later stages."""
    def integer(value, low=0, high=None):
        return type(value) is int and value>=low and (high is None or value<=high)
    def flags(row, names):
        return isinstance(row,dict) and all(row.get(name) is True for name in names)
    def costs(row, edited=True):
        return (isinstance(row,dict) and row.get('edited_only_position_changed') is edited
                and type(row.get('cache_hit')) is bool and integer(row.get('resolver_operations'))
                and integer(row.get('maximum_worker_operations'),1,4)
                and all(integer(row.get(name),1) for name in ('generation','request_cpu_cycles',
                    'total_worker_cpu_cycles','maximum_worker_cpu_cycles','worker_calls','stack_bytes')))
    def accepted(row, allow_empty=False):
        if not flags(row, ('passed','continuous_state_path_output_equal','independent_continuation_policy_equal',
                            'edited_only_position_changed','live_history_output_preserved')) or not costs(row.get('costs')):
            return False
        classes=row.get('classes');counts=row.get('path_counts');boundaries=row.get('actual_final_boundaries')
        launches=row.get('actual_accepted_launches')
        if (not isinstance(classes,list) or len(classes)!=2 or any(name not in
                ('landing','net','out','interception','no-contact','limit','lifecycle','incomplete') for name in classes)
                or not isinstance(counts,list) or len(counts)!=2
                or any(not integer(n,0 if allow_empty else 1,256) for n in counts)
                or not isinstance(boundaries,list) or len(boundaries)!=2
                or not isinstance(launches,dict) or set(launches)!={'0','1'}):return False
        for boundary in boundaries:
            if boundary is not None and (not isinstance(boundary,dict)
                    or any(not integer(boundary.get(name),0,255) for name in ('contact','flight'))
                    or not integer(boundary.get('lifecycle'),0,65535)):return False
        for events in launches.values():
            if not isinstance(events,list):return False
            for event in events:
                if (not isinstance(event,dict) or not integer(event.get('end'),0,1)
                        or event.get('kind') not in (1,3) or not integer(event.get('dispatch'))):return False
        return True
    names={'human-serve-fallback','title-dual-rejection','no-contact','limit-256',
           'replacement-resolve','replacement-held','non-dispatch-lifecycle','truncated-completed-context'}
    if (not isinstance(stage,dict) or stage.get('passed') is not True
            or [stage.get(key) for key in ('canonical_bytes','history_metadata_bytes','total_samples_per_path',
                                          'maximum_worker_operations')]!=[318,72,256,4]
            or stage.get('other_stages_pending')!=['A2-endpoint-discovery','A3-relocation-native-history']
            or not isinstance(stage.get('cases'),dict) or set(stage['cases'])!=names):return False
    rows=stage['cases'];fallback=rows['human-serve-fallback'];miss=rows['no-contact']
    if not accepted(fallback) or not accepted(miss):return False
    if (not flags(fallback, ('human','legal_position_verified','released_no_launch'))
            or fallback.get('lifecycle')!=1 or not integer(fallback.get('phase'),0,255)
            or fallback['phase']&0xe0!=0x40 or fallback.get('released_outgoing_path_claimed') is not False
            or fallback['classes'][1]!='limit' or fallback['path_counts'][1]!=256):return False
    timed=fallback.get('timed_prelaunch') or {};post=fallback.get('postlaunch_rejection') or {}
    if (not flags(timed, ('passed','actual_launch_absent_before_requests','held_actual_launch_after_requests'))
            or timed.get('phase')!=32 or timed.get('complete_boundary_clocks')!=[15,16]
            or timed.get('launch_entry_clock')!=16 or not isinstance(timed.get('cases'),list)
            or len(timed['cases'])!=2 or not all(accepted(row) for row in timed['cases'])):return False
    if (not flags(post, ('passed','actual_human_launch_observed','legal_position_verified','request_rejected',
                         'full_live_history_output_preview_preserved'))
            or post.get('lifecycle')!=1 or not integer(post.get('phase'),0,255) or post['phase']&0xe0!=32
            or not integer(post.get('serve_clock'),17,255) or not integer(post.get('operations'),1)
            or post.get('launch_entry_clock')!=16 or post.get('first_postlaunch_boundary_clock')!=17):return False
    if ('no-contact' not in miss['classes'] or miss.get('no_contact_outgoing_path_claimed') is not False
            or not integer(miss.get('end'),0,1)):return False
    for variant,name in enumerate(miss['classes']):
        if name=='no-contact' and any(event['end']==miss['end'] for event in miss['actual_accepted_launches'][str(variant)]):return False
    title=rows['title-dual-rejection'];limit=rows['limit-256']
    if (not flags(title, ('passed','fallback_rejected','historical_rejected','full_live_history_output_preview_preserved'))
            or title.get('lifecycle')!=2 or not integer(title.get('stale_phase'),0,255)
            or title['stale_phase']&0xe0==0):return False
    if (not flags(limit, ('passed','no_actual_human_launch','incomplete','full_live_history_output_preserved',
                          'continuous_state_path_output_equal','independent_continuation_policy_equal'))
            or limit.get('samples')!=256 or limit.get('total_sample_limit')!=256
            or limit.get('outgoing_path_claimed') is not False):return False
    for name,phase in (('replacement-resolve',1),('replacement-held',3)):
        row=rows[name]
        if (not flags(row, ('passed','cold_restart','old_and_partial_results_unavailable',
                           'full_live_history_output_preserved','edited_only_position_changed'))
                or row.get('phase')!=phase or not integer(row.get('retired_generation'),1,0xfffffffe)
                or row.get('new_generation')!=row['retired_generation']+1 or not integer(row.get('partial_prefix_samples'))
                or any(not integer(row.get(key),0,255) for key in ('old_x','old_y','new_x','new_y'))
                or (row['old_x'],row['old_y'])==(row['new_x'],row['new_y'])
                or any(not integer(row.get(key),1) for key in ('request_cpu_cycles','replacement_cpu_cycles',
                      'maximum_worker_cpu_cycles','worker_calls','maximum_stack_bytes',
                      'replacement_resolver_worker_calls','replacement_resolver_cpu_cycles'))):return False
    lifecycle=rows['non-dispatch-lifecycle']
    if (not flags(lifecycle, ('passed','clear_latch_result_order_preserved','reset_not_executed'))
            or lifecycle.get('reset_operations')!=['game_core_init','game_core_select','game_core_return_title']
            or not isinstance(lifecycle.get('cases'),list) or len(lifecycle['cases'])!=3):return False
    for row in lifecycle['cases']:
        if (not accepted(row,allow_empty=True) or row['classes']!=['lifecycle','lifecycle']
                or row['path_counts']!=[0,0] or row['actual_final_boundaries']!=[None,None]):return False
    truncated=rows['truncated-completed-context']
    if (not flags(truncated, ('passed','request_accepted','context_missing','result_rejected',
                             'unavailable_scratch_preserved','full_live_history_output_preserved'))
            or truncated.get('cache_valid') is not False or truncated.get('completed_kind') not in (1,2)
            or not costs(truncated.get('costs'),edited=False) or truncated['costs']['cache_hit'] is not False
            or truncated['costs']['resolver_operations']<=0
            or any(not integer(truncated.get(key)) for key in ('incoming_origin','oldest','probe_origin'))
            or not truncated['incoming_origin']<truncated['oldest']<=truncated['probe_origin']
            or not integer(truncated.get('dispatches'),1,512) or not integer(truncated.get('operations'),1,8192)
            or truncated.get('non_tick_calls_between_launch_and_probe')!=128):return False
    return True


def preview_a2_extent(stage):
    """Require bounded discovery, actual endpoint evidence and chosen replays."""
    def integer(value, low=0, high=None):
        return type(value) is int and value>=low and (high is None or value<=high)
    def sha(value):
        return isinstance(value,str) and len(value)==64 and all(c in '0123456789abcdef' for c in value)
    def costs(row):
        return (isinstance(row,dict) and row.get('edited_only_position_changed') is True
                and type(row.get('cache_hit')) is bool and integer(row.get('resolver_operations'))
                and integer(row.get('maximum_worker_operations'),1,4)
                and integer(row.get('worker_calls'),1,8192)
                and all(integer(row.get(key),1) for key in ('generation','request_cpu_cycles',
                    'total_worker_cpu_cycles','maximum_worker_cpu_cycles','stack_bytes')))
    def qualification(facts,end,prefix=None):
        if (not isinstance(facts,dict) or facts.get('source')!='actual-full-canonical-and-accepted-hooks'
                or facts.get('geometry_source')!='actual-sampled-drawn-geometry-visibility-ticks'
                or facts.get('classifier_priority')!=['interception','net','out','landing']
                or type(facts.get('geometry_coincident')) is not bool):return None
        variants=facts.get('variants')
        if (not isinstance(variants,list) or len(variants)!=2
                or not integer(facts.get('prefix_samples'),0,255)
                or (prefix is not None and facts['prefix_samples']!=prefix)):return None
        prefix=facts['prefix_samples']
        coverage=set()
        for variant,row in enumerate(variants):
            if (not isinstance(row,dict) or not integer(row.get('variant'),variant,variant)
                    or type(row.get('has_human_launch')) is not bool
                    or type(row.get('outgoing_samples_present')) is not bool
                    or not integer(row.get('samples'),1,256)
                    or any(not integer(row.get(key),0,255) for key in ('contact','flight'))
                    or not integer(row.get('lifecycle'),0,65535)
                    or not sha(row.get('final_state_sha256'))
                    or row.get('first_terminal_boundary_checked') is not True
                    or not integer(row.get('last_sampled_dispatch'),0,row['samples']-1)
                    or row['last_sampled_dispatch']!=row['samples']-prefix-1):return None
            boundary=row.get('last_sampled_boundary')
            if not isinstance(boundary,dict) or any(boundary.get(key)!=row[key] for key in ('contact','flight','lifecycle')):return None
            human=row.get('human_launch');opponent=row.get('opponent_contact')
            if row['has_human_launch']:
                if (not isinstance(human,dict) or human.get('end')!=end or human.get('kind')!=1
                        or not integer(human.get('dispatch'),0,row['last_sampled_dispatch'])
                        or not integer(row.get('human_launch_order'))):return None
                if opponent is not None:
                    if (not isinstance(opponent,dict) or opponent.get('end')!=1-end or opponent.get('kind')!=1
                            or not integer(opponent.get('dispatch'),human['dispatch'],row['last_sampled_dispatch'])
                            or not integer(row.get('opponent_contact_order'),row['human_launch_order']+1)):return None
                elif row.get('opponent_contact_order') is not None:return None
                if prefix is not None and row['outgoing_samples_present'] is not (row['samples']>prefix+human['dispatch']+1):return None
                expected=('interception' if opponent is not None else 'net' if row['contact']&1 else
                          'out' if row['contact']&0x88 else 'landing' if row['contact']&2 else 'unqualified')
            else:
                if any(row.get(key) is not None for key in ('human_launch','human_launch_order','opponent_contact','opponent_contact_order')) or row['outgoing_samples_present']:return None
                expected='no-contact' if row['contact']&0x8d else 'unqualified'
            if row.get('classification')!=expected:return None
            first=row.get('first_terminal_dispatch')
            if expected!='unqualified':
                if not integer(first) or first!=row['last_sampled_dispatch']:return None
                if row.get('preview_outcome')!={'landing':1,'net':2,'out':3,'interception':4,'no-contact':5}[expected]:return None
            elif first is not None:return None
            if expected in ('net','out','interception'):coverage.add(expected)
        coincident=facts['geometry_coincident'] and all(row['outgoing_samples_present'] for row in variants)
        if facts.get('launched_outgoing_coincidence') is not coincident:return None
        if coincident:coverage.add('coincidence')
        return coverage if facts.get('coverage')==sorted(coverage) else None
    seeds_expected=[0xace1,0x0001,0x1234,0xbeef];required={'net','out','interception','coincidence'}
    policy=dict(select_mode=0,entropy_policy=0,
        cycle=['game_round_poll','game_core_sample_pads','game_core_sample_result','game_tick_dispatch'],
        release_modulus=64,release_prefix=8,direction_modulus=96,first_direction_ticks=48,
        direction_first=8,direction_second=4,opponent_packet=0,result_words=[0]*6)
    if (not isinstance(stage,dict) or stage.get('passed') is not True
            or stage.get('planned_seeds')!=seeds_expected or stage.get('input_policy')!=policy
            or any(stage.get(key)!=value for key,value in dict(dispatch_cap=512,ordinary_operation_cap=2049,
                returns_per_seed_cap=2,positions_per_return_cap=9,job_cap=72,worker_call_cap=8192,
                maximum_worker_operations=4,total_samples_per_path=256).items())
            or stage.get('frozen_history_write_guard') is not True
            or stage.get('position_policy')!='recorded-contact-plus-minus8-clamped-to-actual-phase-limits'
            or stage.get('required_coverage')!=['net','out','interception','coincidence']
            or stage.get('actual_coverage')!=sorted(required) or stage.get('absent_classes')!=[]):return False
    seeds=stage.get('seeds');jobs=stage.get('job_results');chosen=stage.get('chosen_cases')
    if (not isinstance(seeds,list) or len(seeds)!=4 or [row.get('seed') for row in seeds if isinstance(row,dict)]!=seeds_expected
            or not isinstance(jobs,list) or not integer(stage.get('jobs'),1,72) or stage['jobs']!=len(jobs)
            or not isinstance(chosen,list) or not 1<=len(chosen)<=4):return False
    identities={};skipped=False
    for row in seeds:
        if not integer(row.get('seed'),1,65535) or type(row.get('recorded')) is not bool or not isinstance(row.get('candidates'),list):return False
        if not row['recorded']:
            if row.get('skipped')!='coverage complete' or row.get('dispatches')!=0 or row.get('operations')!=0 or row['candidates']:return False
            skipped=True;continue
        if (skipped or row.get('dispatches')!=512 or row.get('operations')!=2049 or row.get('oldest')!=0
                or row.get('latest')!=2049 or not sha(row.get('input_stream_sha256'))
                or not integer(row.get('recorded_completed_returns'))
                or len(row['candidates'])!=min(2,row['recorded_completed_returns'])):return False
        stream=[('game_core_select',[0,row['seed'],0])]
        for tick in range(512):
            stream.extend([('game_round_poll',[]),('game_core_sample_pads',[
                (16 if tick%64>=8 else 0)|(8 if tick%96<48 else 4),0]),
                ('game_core_sample_result',[0]*6),('game_tick_dispatch',[])])
        if row['input_stream_sha256']!=hashlib.sha256(json.dumps(stream,separators=(',',':')).encode()).hexdigest():return False
        previous=-1
        for candidate in row['candidates']:
            if (not isinstance(candidate,dict) or candidate.get('completed_kind')!=1 or not integer(candidate.get('end'),0,1)
                    or not integer(candidate.get('ordinal')) or candidate.get('incoming_kind') not in (1,3)
                    or candidate.get('incoming_end')!=1-candidate['end']
                    or any(not integer(candidate.get(key),0,2048) for key in ('incoming_origin','probe_origin','action_boundary'))
                    or not candidate['incoming_origin']<candidate['probe_origin']<=candidate['action_boundary']
                    or candidate['action_boundary']<=previous or candidate.get('full_incoming_retained') is not True
                    or candidate.get('selected_lifecycle')!=1
                    or any(not integer(candidate.get(key),0,255) for key in ('recorded_x','recorded_y'))):return False
            key=(row['seed'],candidate['ordinal'])
            if key in identities:return False
            identities[key]=candidate;previous=candidate['action_boundary']
    names={};positions={};covered=set()
    for row in jobs:
        if not isinstance(row,dict):return False
        if not integer(row.get('seed'),1,65535) or not integer(row.get('ordinal')):return False
        key=(row.get('seed'),row.get('ordinal'));candidate=identities.get(key);bounds=row.get('bounds')
        if (candidate is None or row.get('candidate')!=candidate or row.get('selection')!=candidate['action_boundary']
                or not isinstance(row.get('name'),str) or row['name'] in names or not costs(row.get('costs'))
                or any(row.get(k)!=v for k,v in dict(worker_call_cap=8192,maximum_worker_operations=4,total_samples_per_path=256).items())
                or row.get('frozen_history_write_guard') is not True
                or not isinstance(bounds,dict) or any(not integer(bounds.get(k),0,255) for k in ('left','right','top','bottom'))
                or not bounds['left']<bounds['right'] or not bounds['top']<bounds['bottom']
                or not integer(bounds.get('phase_offset')) or bounds['phase_offset'] not in (0,4,8,12)
                or not integer(row.get('x'),bounds['left'],bounds['right']-1)
                or not integer(row.get('y'),bounds['top'],bounds['bottom']-1)):return False
        xs={max(bounds['left'],min(bounds['right']-1,candidate['recorded_x']+d)) for d in (-8,0,8)}
        ys={max(bounds['top'],min(bounds['bottom']-1,candidate['recorded_y']+d)) for d in (-8,0,8)}
        grid=positions.setdefault(key,set());point=(row['x'],row['y'])
        if point in grid or point[0] not in xs or point[1] not in ys:return False
        grid.add(point)
        if len(grid)>9:return False
        facts=qualification(row.get('qualification'),candidate['end'])
        if facts is None:return False
        covered.update(facts);names[row['name']]=row
    chosen_coverage=set();chosen_names=set()
    for row in chosen:
        job=names.get(row.get('name')) if isinstance(row,dict) else None
        if job is None or row['name'] in chosen_names:return False
        if (any(row.get(k) is not True for k in ('passed','continuous_state_path_output_equal',
                'independent_continuation_policy_equal','live_history_output_preserved','edited_only_position_changed'))
                or any(row.get(k)!=job[k] for k in ('seed','ordinal','selection','x','y','bounds','costs','qualification'))
                or row.get('end')!=job['candidate']['end'] or not integer(row.get('prefix_samples'),0,255)):return False
        facts=qualification(row['qualification'],row['end'],row['prefix_samples'])
        contribution=row.get('coverage_contributed')
        if (facts is None or not isinstance(contribution,list) or not contribution
                or contribution!=sorted(facts-chosen_coverage)):return False
        states=row.get('final_states');paths=row.get('paths')
        if not isinstance(states,list) or len(states)!=2 or not isinstance(paths,list) or len(paths)!=2:return False
        for variant in (0,1):
            try:state=bytes.fromhex(states[variant]);path=bytes.fromhex(paths[variant])
            except (TypeError,ValueError):return False
            fact=row['qualification']['variants'][variant]
            if len(state)!=318 or hashlib.sha256(state).hexdigest()!=fact['final_state_sha256'] or len(path)!=8*fact['samples']:return False
        geometry=[]
        for path_hex in paths:
            path=bytes.fromhex(path_hex)
            geometry.append([(path[n:n+4],bool(path[n+6]&15),bool(path[n+6]&240),path[n+7]) for n in range(0,len(path),8)])
        if row['qualification']['geometry_coincident'] is not (geometry[0]==geometry[1]):return False
        if row.get('path_counts')!=[fact['samples'] for fact in row['qualification']['variants']]:return False
        chosen_coverage.update(contribution);chosen_names.add(row['name'])
    return covered==required and chosen_coverage==required


def required_extent(case,report):
    if report.get('passed') is not True:return False
    if case.extent and not acceptance(case.extent,report):return False
    if case.id=='preview-cpu':
        validation=report.get('preview_validation') or {}
        evidence=report.get('evidence') or {}
        rows=validation.get('cases')
        fallback=validation.get('ai_serve_setup_fixture') or {}
        if (report.get('execution')!='actual-68000-cpu-only'
                or evidence.get('target_role')!='legacy-validator-reference'
                or evidence.get('actual_execution')!='actual-68000-cpu-only'
                or validation.get('passed') is not True
                or validation.get('preview_storage_bytes')!=5550 or validation.get('metadata_bytes')!=110
                or type(validation.get('fixture_operations')) is not int or validation['fixture_operations']<2049
                or not isinstance(rows,list) or len(rows)!=3
                or {r.get('name') for r in rows if isinstance(r,dict)}!={
                    'completed-serve','return-after-pads','return-before-dispatch'}):return False
        if (not isinstance(fallback,dict)
                or any(fallback.get(key) is not True for key in
                       ('passed','ai','frozen','legal_position_verified'))
                or type(fallback.get('operations')) is not int or fallback['operations']<=0
                or type(fallback.get('end')) is not int or fallback['end'] not in (0,1)
                or type(fallback.get('phase')) is not int or not 0<fallback['phase']<=255
                or fallback['phase']&0xe0==0
                or fallback.get('rejection_scope')!='ai-serving-context'
                or fallback.get('ai_guard_isolated') is not False
                or type(fallback.get('human_phase')) is not int or not 0<=fallback['human_phase']<=255
                or fallback['human_phase']&0xe0!=0
                or any(type(fallback.get(key)) is not int or not 0<=fallback[key]<=255
                       for key in ('legal_x','legal_y'))):return False
        required={'stale-step','stale-cancel','stale-request','zero-budget','excess-budget',
                  'unpublished-result','changed-selection-result','ai-serve-fallback'}
        for row in rows:
            calls=row.get('worker_calls');paths=row.get('path_counts')
            if (row.get('passed') is not True or row.get('continuous_state_path_output_equal') is not True
                    or row.get('independent_continuation_policy_equal') is not True
                    or row.get('live_history_output_preserved') is not True
                    or type(calls) is not int or calls<=0
                    or type(row.get('maximum_worker_operations')) is not int
                    or not 0<row['maximum_worker_operations']<=4
                    or type(row.get('preservation_checks')) is not int or row['preservation_checks']<calls
                    or row.get('worker_restorations')!=calls
                    or not isinstance(paths,list) or len(paths)!=2
                    or any(type(count) is not int or not 1<=count<=256 for count in paths)
                    or not required.issubset(set(row.get('negative_controls') or []))):return False
            if row['name'].startswith('return'):
                controls=row.get('first_dispatch_controls')
                if (not isinstance(controls,dict) or set(controls)!={'0','1'}
                        or any(type(value) is not int for value in controls.values())
                        or controls['0']&0x3f!=16 or controls['1']&0x3f!=0):return False
            for field in ('request_cpu_cycles','total_worker_cpu_cycles','maximum_worker_cpu_cycles',
                          'repeat_request_cpu_cycles'):
                if type(row.get(field)) is not int or row[field]<=0:return False
            for field in ('resolver_operations','resolver_worker_calls','resolver_inclusive_cpu_cycles',
                          'repeat_resolver_operations','repeat_resolver_worker_calls','repeat_resolver_cpu_cycles'):
                if type(row.get(field)) is not int or row[field]<0:return False
        cache=validation.get('cache_validation') or {}
        paired=cache.get('cold_warm') or {}
        failures=cache.get('failed_seek_controls')
        invalidation=cache.get('invalidation') or {}
        if (cache.get('passed') is not True
                or any(paired.get(key) is not True for key in
                       ('passed','state_path_output_equal','prefix_equal','live_history_output_preserved'))
                or type(cache.get('maximum_stack_bytes')) is not int or cache['maximum_stack_bytes']<=0):return False
        for name in ('original','cold','warm'):
            job=paired.get(name) or {}
            if (job.get('cache_hit') is not (name=='warm')
                    or type(job.get('resolver_operations')) is not int
                    or (job['resolver_operations']!=0 if name=='warm' else job['resolver_operations']<=0)
                    or type(job.get('maximum_worker_operations')) is not int
                    or not 0<job['maximum_worker_operations']<=4):return False
            for field in ('generation','request_cpu_cycles','total_worker_cpu_cycles','maximum_worker_cpu_cycles',
                          'worker_calls','stack_bytes'):
                if type(job.get(field)) is not int or job[field]<=0:return False
            if job['stack_bytes']>cache['maximum_stack_bytes']:return False
        if (not isinstance(failures,list) or len(failures)!=5
                or {row.get('name') for row in failures if isinstance(row,dict)}!={
                    'corrupt-checkpoint-schema','corrupt-checkpoint-simulation','corrupt-checkpoint-state',
                    'corrupt-operation-id','out-of-range-high'}):return False
        for row in failures:
            if (any(row.get(key) is not True for key in ('passed','all_72_metadata_preserved',
                    'canonical_preserved','history_bytes_preserved','cache_generation_status_preserved',
                    'ready_result_preserved'))
                    or type(row.get('failed_seek_cpu_cycles')) is not int or row['failed_seek_cpu_cycles']<=0):return False
        if (invalidation.get('passed') is not True or invalidation.get('generation_exhausted') is not True
                or not {'seek-back-ready','failed-seek-preserves','different-attempt','cancel','eviction',
                        'exhaustion','stale-generation'}.issubset(set(invalidation.get('negative_controls') or []))):return False
        for field in ('after_cancel_resolver_operations','different_attempt_resolver_operations'):
            if type(invalidation.get(field)) is not int or invalidation[field]<=0:return False
        for field in ('oldest_after_eviction','evicted_incoming_origin'):
            if type(invalidation.get(field)) is not int or invalidation[field]<0:return False
        if invalidation['oldest_after_eviction']<=invalidation['evicted_incoming_origin']:return False
        return (preview_a1_extent(validation.get('stage_a1_validation'))
                and preview_a2_extent(validation.get('stage_a2_validation')))
    if case.id=='history-cpu':
        validation=report.get('history_validation') or {}
        proofs=validation.get('proofs') or {}
        evidence=report.get('evidence') or {}
        if (report.get('execution')!='actual-68000-cpu-only' or validation.get('passed') is not True
                or evidence.get('target_role')!='legacy-validator-reference'
                or evidence.get('actual_execution')!='actual-68000-cpu-only'
                or set(proofs)!={'empty','long','cursor-wrap','relocated','native-sinks','logical-api','pending-eviction'}
                or any(p.get('passed') is not True for p in proofs.values())):return False
        if proofs['empty'].get('operations')!=0 or proofs['empty'].get('boundaries_checked')!=1:return False
        for name in ('long','cursor-wrap','relocated','native-sinks','logical-api','pending-eviction'):
            proof=proofs[name]
            if not history_boundary_extent(proof) or 'invalid-operation-id' not in proof['negative_controls']:return False
        long=proofs['long'];kinds=long.get('completed_episode_kinds') or {};wrap=proofs['cursor-wrap']
        api=proofs['logical-api'];eviction=proofs['pending-eviction']
        operations={'game_core_init','game_core_select','game_core_sample_pads','game_core_sample_result',
                    'game_core_clear_inputs','game_core_return_title','game_round_poll','game_tick_dispatch','game_core_latch_actions'}
        argument_hashes=[proofs[name].get('record_arguments_sha256') for name in ('cursor-wrap','relocated','native-sinks')]
        return (long.get('operations',0)>3*4096 and long.get('tick_wraps',0)>0
                and long.get('buffer_bytes')==80318 and type(long.get('retained_operations')) is int
                and 4032<=long['retained_operations']<4096
                and type(long.get('terminal_outcome_operations')) is int and long['terminal_outcome_operations']>0
                and all(kinds.get(str(kind),kinds.get(kind,0))>0 for kind in (1,2))
                and wrap.get('low_longword_wrap') is True and wrap.get('latest',0)>>32==1
                and all((api.get('operation_counts') or {}).get(name,0)>0 for name in operations)
                and eviction.get('pending_canceled') is True
                and eviction.get('eviction_oldest',0)>eviction.get('evicted_pending_origin',0)
                and eviction.get('completed_new_origin',-1)>=eviction.get('eviction_oldest',0)
                and eviction.get('completed_new_episode_kind') in (1,2)
                and isinstance(argument_hashes[0],str) and len(argument_hashes[0])==64
                and len(set(argument_hashes))==1
                and 'native-presentation-and-hardware-sinks-suppressed' in proofs['native-sinks']['negative_controls'])
    if case.id in ('history-pal','history-ntsc'):
        rows=report.get('rows',[])
        validation=report.get('history_validation') or {}
        seek=validation.get('seek') or {}
        retained=validation.get('retained_operations')
        boundaries=seek.get('boundaries_checked')
        seeks=seek.get('seeks')
        seconds=report.get('seconds')
        evidence=report.get('evidence') or {}
        return (report.get('history') is True and isinstance(seconds,(int,float)) and seconds>=24
                and evidence.get('target_role')=='legacy-validator-reference'
                and evidence.get('actual_target')==report.get('target')
                and report.get('native_video')==dict(
                    presentation_last_line=261 if case.id=='history-ntsc' else 311,
                    simulation_interval_whole=11947 if case.id=='history-ntsc' else 11838,
                    simulation_interval_fraction=13180 if case.id=='history-ntsc' else 14906)
                and report.get('target')==dict(video='NTSC' if case.id=='history-ntsc' else 'PAL',
                                              cpu='68000',chipset='OCS',chip_kib=512,slow_kib=0,fast_kib=0)
                and isinstance(rows,list) and bool(rows)
                and (report.get('summary') or {}).get('operations')==len(rows)
                and validation.get('passed') is True and validation.get('native_buffer_equal') is True
                and type(seek.get('terminal_outcome_operations')) is int and seek['terminal_outcome_operations']>0
                and type(seek.get('operations')) is int and seek['operations']>4096
                and type(seek.get('oldest')) is int and seek['oldest']>0
                and seek.get('buffer_bytes')==80318 and type(retained) is int and 4032<=retained<4096
                and any(isinstance(row,list) and len(row)==3 and row[1]==2
                        for row in validation.get('native_attempts',[]))
                and type(retained) is int and retained>0 and seek.get('retained_operations')==retained
                and type(boundaries) is int and boundaries==retained+1
                and type(seeks) is int and seeks>=2*boundaries and history_boundary_extent(seek))
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
    meta=report.get('evidence')
    standard=bool(meta)
    if standard:
        # ReportRun's historical environment records RUST_LOG only. A fresh
        # controller execution may add its own binding, never rewrite that
        # original receipt or infer an old missing environment.
        if status(path)['status']!='passed':return None
        command=meta.get('command',[])
        if (not command or Path(command[0]).name!=Path(case.args[0]).name
                or command[1:]!=list(case.args[1:])):return None
        environment=meta.get('environment',{})
        if 'PYTHONPATH' in environment and environment['PYTHONPATH']!=os.environ.get('PYTHONPATH'):return None
    elif case.id not in ('startup','video-standard'):return None
    # These two observers lack ReportRun metadata. Only execution by this
    # controller can supply their missing identities; historical reports stay
    # ineligible. Capture emitted fixture/release bytes and all local artifacts.
    artifacts=dict(meta['files']) if standard else snapshot(p for p in path.parent.rglob('*') if p.is_file())
    if not standard and case.id=='startup':
        product=Path(root)/'build/amiga/interfaces/enhanced'
        artifacts.update(snapshot([product/'delivery/baseline-rally',product/'delivery/baseline-rally.adf',product/'native.lst']))
        if (report.get('release_sha256')!=digest(product/'delivery/baseline-rally')
                or report.get('adf_sha256')!=digest(product/'delivery/baseline-rally.adf')):return None
    elif not standard:
        if report.get('executable_sha256')!=digest(path.parent/'fixture'):return None
    return {'path':str(path),'sha256':digest(path),'original_evidence':meta,'artifacts':artifacts,
            'classification':'fresh-controller-bound','dependency_key':dependency_key,
            'environment':{'RUST_LOG':'info','PYTHONPATH':os.environ.get('PYTHONPATH')}}

def receipt_token(case,root):
    if not case.report:return None
    try:
        stat=(Path(root)/'build'/case.report).stat()
        return (stat.st_ino,stat.st_mtime_ns,stat.st_size)
    except OSError:return None

def produced_receipt(case,root,started,before):
    report=read(Path(root)/'build'/case.report) or {}
    meta=report.get('evidence') or {}
    if meta:
        return (receipt_token(case,root)!=before and isinstance(meta.get('started_utc'),str)
                and meta['started_utc']>=started)
    return receipt_token(case,root)!=before and receipt_token(case,root) is not None

def attempt_valid(attempt, case, deps, root=ROOT):
    if not attempt or attempt.get('state')!='complete' or attempt.get('exit_code')!=0:
        return False
    if attempt.get('dependency_key')!=canonical(deps) or changed(attempt.get('artifacts',{})):
        return False
    if attempt.get('orchestration')!=orchestration_identity():return False
    if execution_blocker(case,deps,root):return False
    if case.report:
        saved=attempt.get('receipt',{})
        if saved.get('classification')=='fresh-controller-bound':
            path=Path(saved['path']);report=read(path)
            return bool(digest(path)==saved['sha256'] and not changed(saved['artifacts'])
                        and saved.get('environment')==deps.get('environment')
                        and saved.get('environment')=={'RUST_LOG':'info','PYTHONPATH':os.environ.get('PYTHONPATH')}
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
        blocker=execution_blocker(case,deps,root,directory)
        if blocker:
            receipt=None;reason=blocker
        elif attempts and not attempt_valid(latest,case,deps,root):
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
        reusable=not blocker and (receipt or attempt_valid(latest,case,deps,root))
        result.append({'id':case.id,'action':'reuse' if reusable else 'run',
                       'reason':reason,'dependencies':deps,'dependency_key':canonical(deps),'receipt':receipt,
                       'prior_artifacts':dict(latest.get('artifacts',{}),**{str(attempts[-1]/'completion.json'):digest(attempts[-1]/'completion.json')}) if latest and attempt_valid(latest,case,deps,root) else {}})
    return result

def caller_ancestors():
    """Read the reconnect caller's own identity chain, without environment data."""
    result=set();pid=os.getpid()
    while pid and pid not in {p for p,_ in result}:
        identity=process_identity(pid)
        if not identity:break
        result.add((pid,identity['start']))
        try:
            fields=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()
            pid=int(fields[1])
        except (OSError,ValueError,IndexError):
            break
    return result

def tagged_processes(campaign_id, owner=None):
    """Missing /proc access is ambiguous and blocks reclaim; never PID-only."""
    found=[]
    if not owner:return found
    current=process_identity()
    if owner.get('boot')!=current['boot']:return found
    marker=('CTENNIS_CAMPAIGN_ID='+campaign_id).encode()
    # Exclude the external reconnect launcher, which is an ancestor of this
    # scan, after checking owned group membership. A caller already tagged as
    # campaign work gets no exclusion. All other live permission denials block.
    ancestors=caller_ancestors() if os.environ.get('CTENNIS_CAMPAIGN_ID')!=campaign_id else set()
    for item in Path('/proc').iterdir():
        if not item.name.isdigit() or int(item.name)==os.getpid():continue
        try:
            identity=process_identity(int(item.name))
            if not identity or int(identity['start'])<int(owner['start']):continue
            if identity['group']==owner['group']:
                found.append(identity);continue
            if (identity['pid'],identity['start']) in ancestors:continue
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
            begin=dict(decision,started_utc=started,controller=process_identity(),provenance=provenance,
                       orchestration=orchestration,resolved_build=str((Path(root)/'build').resolve()),attempt=str(attempt))
            history=(Path(root)/'build').resolve()/'.acceptance-case-history'/case.id/decision['dependency_key']/uuid.uuid4().hex
            atomic_json(history/'started.json',begin)
            atomic_json(attempt/'started.json',begin)
            if decision['action']=='reuse':
                code=0;receipt=decision['receipt']
                artifact.update(decision['prior_artifacts'])
            else:
                receipt=None
                before_receipt=receipt_token(case,root)
                with (attempt/'child.log').open('wb') as output:
                    child=subprocess.Popen([sys.executable,*case.args],cwd=root,
                        env=dict(os.environ,RUST_LOG='info'),stdout=output,stderr=subprocess.STDOUT,
                        pass_fds=(fd,))
                    atomic_json(attempt/'child.json',{'identity':process_identity(child.pid),'command':[sys.executable,*case.args]})
                    code=child.wait()
                artifact=snapshot([attempt/'child.log'])
                if code==0 and case.report:
                    reason='Child did not produce a receipt for this actual invocation'
                    if produced_receipt(case,root,started,before_receipt):
                        receipt,reason=compatible_receipt(case,root,check_history=False)
                        if not receipt:receipt=fresh_receipt(case,root,decision['dependency_key'])
                    if not receipt:code=1;decision['validation_error']=reason
                if code==0 and changed(decision['dependencies']['files']):
                    code=1;decision['validation_error']='Dependencies changed during execution'
                if code==0 and any((not Path(name).exists())!=absent for name,absent in decision['dependencies'].get('optional_absence',{}).items()):
                    code=1;decision['validation_error']='Optional input presence changed during execution'
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
            atomic_json(history/'completion.json',complete)
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
