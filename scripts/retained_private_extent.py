"""Bounded retained-private native evidence, separate from later UI integration."""
import math
from native_evidence import TARGET

CPU_RECEIPTS={
 'build/tests/preview-cpu/report.json':'82655fe568c668b97cae26d9219b5ef2104de9dbd24c7ecc3d4a867680446e5e',
 'build/tests/seek-sliced-cpu/report.json':'a0da6b594010e82e3ffc6f996fee17ff07c0286e5f12f1c2221e46e4dcf4f23b',
 'build/tests/private-state-cpu/report.json':'10f7166a21ad631c4c0153491aa16a4207de8d1e4e1058b4ccc49314a854d3cc'}


def required_retained_extent(report,standard):
    v=report.get('retained_private_validation') or {};costs=v.get('costs') or {}
    jobs=v.get('completed_jobs') or [];frames=v.get('body_frames') or []
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
    if core!=dict(bytes=17524,relocations=7,sinks=14,
            sha256='951935ce4ec1538f5ff2fa83898c36af7a75de60f4c0fe025e74181543f1544c'):return False
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
