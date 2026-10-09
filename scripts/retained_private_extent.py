"""Bounded retained-private native evidence, separate from later UI integration."""
import math
from native_evidence import TARGET
from preview_native_extent import irq_resumptions_valid

CPU_RECEIPTS={
 'build/tests/preview-cpu/report.json':'82655fe568c668b97cae26d9219b5ef2104de9dbd24c7ecc3d4a867680446e5e',
 'build/tests/seek-sliced-cpu/report.json':'a0da6b594010e82e3ffc6f996fee17ff07c0286e5f12f1c2221e46e4dcf4f23b',
 'build/tests/private-state-cpu/report.json':'10f7166a21ad631c4c0153491aa16a4207de8d1e4e1058b4ccc49314a854d3cc'}


def irq_coverage_valid(v):
    try:
        ledger=v['irq_coverage_validation'];frames=v['body_frames'];apis=v['api_rows']
        proofs=ledger['final_proofs'];writes=v['irq_writes'];rules=v['irq_rules']
        if (ledger.get('passed') is not True or type(ledger.get('needed')) is not bool
                or ledger.get('budget')!=3 or ledger.get('maximum_worker_calls')!=512
                or ledger.get('initial_roles') not in ([1],[2],[],[1,2])
                or ledger['needed']!=(ledger['initial_roles']!=[1,2])
                or [p['role'] for p in proofs]!=[1,2]):return False
        mapping={f['entry_index']:f for f in frames}
        for proof in proofs:
            frame=mapping[proof['entry_index']];a,b=proof['acknowledgements']
            if (frame['ownership']['active']!=proof['role'] or proof['api_row_index']!=frame['api_row_index'] or a not in writes or b not in writes
                    or a['pc']>=b['pc']
                    or not frame['start']['cck']<=a['position']['cck']<b['position']['cck']<=frame['end']['cck']):return False
            for ack in (a,b):
                rule=rules[str(ack['pc'])]
                if (rule['destination'].lower()!='$dff09c' or rule['source']!='#$0010'
                        or ack['address']!=0xdff09c or ack['size']!=2 or ack['value']!=16):return False
        steps=ledger['worker_api_row_indices'];counts=ledger['worker_body_counts']
        if not isinstance(steps,list) or not isinstance(counts,list) or len(steps)!=len(counts):return False
        if not ledger['needed']:return not steps and not counts
        first=ledger['invalidating_cancel_api_row_index'];request=ledger['request_api_row_index'];last=ledger['cancel_api_row_index']
        if (ledger.get('cancelled_incomplete_job') is not True or not 1<=len(steps)<=512
                or not 0<ledger['generation']<0xffffffff
                or ledger.get('generation_before_cancel')!=ledger['generation']
                or type(ledger.get('status_before_cancel')) is not int or not 1<=ledger['status_before_cancel']<5
                or any(p['api_row_index'] not in steps for p in proofs if p['role'] not in ledger['initial_roles'])
                or not isinstance(ledger.get('request_arguments'),list) or len(ledger['request_arguments'])!=4
                or ledger['request_arguments'][0]!=ledger['generation']-1
                or not first<request<steps[0]<=steps[-1]<last
                or not all(a<b for a,b in zip(steps,steps[1:]))
                or apis[first]['name']!='game_preview_cancel' or apis[request]['name']!='game_preview_request'
                or apis[last]['name']!='game_preview_cancel'):return False
        return all(apis[i]['name']=='game_preview_step' and type(n) is int and 0<=n<=3
            and apis[i]['bodies']==n and sum(f['api_row_index']==i for f in frames)==n for i,n in zip(steps,counts))
    except (KeyError,TypeError,ValueError,IndexError):return False


def required_retained_extent(report,standard):
    v=report.get('retained_private_validation') or {};costs=v.get('costs') or {}
    jobs=v.get('completed_jobs') or [];frames=v.get('body_frames') or []
    if not irq_coverage_valid(v):return False
    expected_video=dict(zip(('presentation_last_line','simulation_interval_whole','simulation_interval_fraction'),
        (311,11838,14906) if standard=='PAL' else (261,11947,13180)))
    if not (report.get('passed') is True and report.get('execution')=='actual-native-paused-retained'
            and report.get('target')==dict(TARGET,video=standard) and v.get('passed') is True
            and v.get('video')==expected_video and v.get('irq_owner_roles')==[1,2]
            and v.get('dropped_notifications')==0 and v.get('irq_inside',0)>0
            and v.get('actual_body_entries')==len(frames)>0 and len(jobs)==2
            and all(v.get(k) is True for k in ('complete318_history72_backup_preserved',
                'private_a5_state_and_outputs_observed','full_bus_write_guard',
                'canonical_and_other_owner_guard','actual_a5_preserved','normal_resume'))
            and math.isfinite(costs.get('minimum_callback_headroom_cck',-1))
            and costs.get('minimum_callback_headroom_cck',-1)>=0):return False
    evidence=report.get('evidence') or {};files=evidence.get('files') or {}
    compiled=evidence.get('compiled_executables') or {};hunks=v.get('loaded_hunks')
    if (v.get('cpu_receipts')!=CPU_RECEIPTS
            or any(files.get(path)!=sha for path,sha in CPU_RECEIPTS.items())
            or v.get('product_sha256') not in compiled.values()
            or v.get('fixture_sha256') not in compiled.values()
            or report.get('executable_sha256')!=v.get('fixture_sha256')
            or not isinstance(hunks,list) or not hunks):return False
    spans=[]
    for h in hunks:
        if (h.get('matched') is not True or not isinstance(h.get('start'),int)
                or not isinstance(h.get('bytes'),int) or h['bytes']<=0
                or not 0<=h['start']<h['start']+h['bytes']<=524288
                or not isinstance(h.get('expected_sha256'),str) or len(h['expected_sha256'])!=64
                or h.get('actual_sha256')!=h['expected_sha256']):return False
        spans.append((h['start'],h['start']+h['bytes']))
    spans.sort()
    if any(a[1]>b[0] for a,b in zip(spans,spans[1:])):return False
    for frame in frames:
        if not irq_resumptions_valid(frame):return False
        try:
            if (frame['exit_pc']!=frame['return_pc'] or frame['exit_sp']!=frame['entry_sp']+4
                    or frame['entry_registers']['pc']!=frame['entry_pc']
                    or frame['entry_registers']['a'][7]!=frame['entry_sp']
                    or frame['end']['cck']<frame['start']['cck']
                    or frame['elapsed_cck']!=frame['end']['cck']-frame['start']['cck']
                    or any(len(bytes.fromhex(frame[k]))!=318 for k in ('before','after'))
                    or frame['state']!=frame['after']):return False
        except (KeyError,TypeError,ValueError):return False
    core=v.get('normalized_core') or {}
    if core!=dict(bytes=17606,relocations=7,sinks=14,
            sha256='99c543c170c036137be81d07ebd30b522ef3abdff04bd7b1af38f00047bb99d5'):return False
    for job,name,budget in zip(jobs,('retained-cold-budget4','retained-cached-budget2'),(4,2)):
        c=job.get('costs') or {}
        if not (job.get('name')==name and job.get('passed') is True
                and job.get('continuous_state_path_output_equal') is True
                and job.get('independent_continuation_policy_equal') is True
                and 0<c.get('maximum_worker_operations',0)<=budget
                and c.get('worker_calls',0)>0
                and len(c.get('worker_body_counts',[]))==c['worker_calls']
                and all(type(n) is int and 0<=n<=budget for n in c['worker_body_counts'])
                and len(bytes.fromhex(job.get('selected_state','')))==318
                and len(job.get('final_states',[]))==2
                and all(len(bytes.fromhex(s))==318 for s in job['final_states'])):return False
    return (jobs[0]['costs']['resolver_operations']>0 and not jobs[0]['costs']['cache_hit']
            and jobs[1]['costs']['resolver_operations']==0 and jobs[1]['costs']['cache_hit'])
