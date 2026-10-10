"""Finite coherent-scheduler observations; no inferred admission safety or WCET.

The immutable capture owns call spans once. Summary rows reference their indices
rather than duplicating nested trees. Record envelopes are independent of worker
quantum: a worker may execute a prefix containing several operation writes.
"""
import gzip
import json
from bisect import bisect_right
from native_evidence import digest, TARGET
from native_tools import ROOT

JOBS={'game_preview_step_variant':'prefix','game_preview_complete':'geometry',
      'game_preview_endpoint_try':'endpoint','complete_scene':'producer',
      'tutorial_animate':'animation','tutorial_render':'render',
      'tutorial_progress_slice':'producer-prefix','tutorial_footer':'footer',
      'game_preview_result':'result','tutorial_footer_commit':'footer-commit',
      'tutorial_copy_court':'render','ui_footer_draw':'render'}
OPTIONAL={'game_preview_step_variant','game_preview_complete','game_preview_endpoint_try'}


def enclosed(outer, inner):
    return outer['entry']['cck']<=inner['entry']['cck']<=inner['exit']['cck']<=outer['exit']['cck']


def validate_capture(c):
    calls=c['stack_timing']['calls'];callbacks=c['timing']['callbacks']
    policy=c['coherent_policy']['policy']
    assert policy['schema']==1 and policy['status']=='experimental-hypotheses-only' and policy['normative_s05_s18_g2_safety'] is False
    hypotheses=policy['hypotheses'];job_policy=policy['job_hypotheses_e']
    reserve_cck=hypotheses['root_service']+hypotheses['residual_margin']
    assert reserve_cck%5==0
    reserve_e=reserve_cck//5
    assert c['input_probe']['maximum_keyboard_poll_gap_cck']<=hypotheses['keyboard_poll_gap_finite_detector'],'Keyboard poll gap exceeds finite policy threshold'
    assert not c['stack_timing']['open_enclosing_calls']
    owners=[(i,r) for i,r in enumerate(calls) if r['callee']=='tutorial_background']
    assert owners,'No coherent admission owner observed'
    entries=[r['entry']['cck'] for r in callbacks]
    ordered=sorted(enumerate(calls),key=lambda v:v[1]['entry']['cck'])
    starts=[r['entry']['cck'] for _,r in ordered]
    operations=c['deadline_operations'];opstarts=[r['position']['cck'] for r in operations]
    chunks=[];accepted=set();classes={};job_budgets={}
    telemetry={name:sorted((r for r in c['scheduler_job_writes'] if r['field']==name),key=lambda r:r['position']['cck']) for name in ('tutorial_job_kind','tutorial_job_variant','tutorial_job_budget','tutorial_job_cost')}
    telemetry_times={name:[r['position']['cck'] for r in rows] for name,rows in telemetry.items()}
    admission_rows={name:[r for r in c['admission_writes'] if r['field']==name] for name in ('simulation_phase','simulation_interval')}
    admission_times={name:[r['position']['cck'] for r in rows] for name,rows in admission_rows.items()}
    def job_at(at):
        result={}
        for name,rows in telemetry.items():
            i=bisect_right(telemetry_times[name],at)-1
            result[name]=rows[i]['value'] if i>=0 else None
        return result
    for oi,o in owners:
        assert o['depth']==0 and o.get('caller') is None
        sub=[(i,r) for i,r in ordered[bisect_right(starts,o['entry']['cck']):bisect_right(starts,o['exit']['cck'])] if enclosed(o,r)]
        jobs=[dict(call_index=i,kind=JOBS[r['callee']]) for i,r in sub if r['callee'] in JOBS]
        if not jobs:continue
        at=bisect_right(entries,o['entry']['cck'])-1
        assert 0<=at<len(callbacks)-1
        assert callbacks[at]['completion']['cck']<=o['entry']['cck']<=o['exit']['cck']<=callbacks[at+1]['entry']['cck'],'Owner crosses mandatory callback'
        accepted.add(oi)
        telemetry_job=job_at(min(calls[r['call_index']]['entry']['cck'] for r in jobs))
        assert telemetry_job['tutorial_job_kind'] in range(1,8) and telemetry_job['tutorial_job_cost'] is not None
        exact_costs={2:{job_policy['endpoint_query']},3:{job_policy['geometry_eight_points']},
                     4:{job_policy['placement_animation_producer'],job_policy['menu_render_single_unit']},
                     5:{job_policy['footer_stage_private']},6:{job_policy['result_metadata']},7:{job_policy['footer_commit_512']}}
        if telemetry_job['tutorial_job_kind']!=1:
            assert telemetry_job['tutorial_job_cost'] in exact_costs[telemetry_job['tutorial_job_kind']],'Job allowance differs from bound policy'
        assert o['elapsed_bus_cck']<=telemetry_job['tutorial_job_cost']*5,'Complete owner exceeds observed job cost hypothesis'
        admission=dict(c['initial_admission_state'])
        job_start=min(calls[r['call_index']]['entry']['cck'] for r in jobs)
        for name,rows in admission_rows.items():
            i=bisect_right(admission_times[name],job_start)-1
            if i>=0:admission[name]=rows[i]['value']
        remaining=admission['simulation_interval']-admission['simulation_phase']
        assert remaining>=telemetry_job['tutorial_job_cost']+reserve_e,'Admitted job lacks cost plus service/margin reservation'
        key=str(telemetry_job['tutorial_job_kind'])+':'+str(telemetry_job['tutorial_job_budget'])
        bucket=job_budgets.setdefault(key,dict(count=0,maximum_owner_cck=0,sum_owner_cck=0))
        bucket['count']+=1;bucket['sum_owner_cck']+=o['elapsed_bus_cck'];bucket['maximum_owner_cck']=max(bucket['maximum_owner_cck'],o['elapsed_bus_cck'])
        ops=[r['operation'] for r in operations[bisect_right(opstarts,o['entry']['cck']):bisect_right(opstarts,o['exit']['cck'])]]
        assert all(op in range(1,10) for op in ops)
        for job in jobs:
            bucket=classes.setdefault(job['kind'],dict(count=0,maximum_cck=0,sum_cck=0))
            cost=calls[job['call_index']]['elapsed_bus_cck'];bucket['count']+=1;bucket['sum_cck']+=cost;bucket['maximum_cck']=max(bucket['maximum_cck'],cost)
        chunks.append(dict(owner_call_index=oi,entry=o['entry'],exit=o['exit'],whole_owner_cck=o['elapsed_bus_cck'],
                           jobs=jobs,telemetry=telemetry_job,admission_state=admission,reserved_e=telemetry_job['tutorial_job_cost']+reserve_e,operations=ops,callback_after=callbacks[at+1]['callback']))
    assert any(j['kind']=='prefix' for row in chunks for j in row['jobs']),'No coherent prefix observed'
    for i,r in enumerate(calls):
        if r['callee'] in OPTIONAL:
            assert any(enclosed(o,r) for _,o in owners),'Optional preview work outside sole background owner'
    assert max(r['work_cck'] for r in callbacks)<=hypotheses['callback'],'Callback exceeds legacy finite hypothesis'
    assert max(r['entry_phase_cck'] for r in callbacks)<=hypotheses['entry_lateness'],'Callback entry exceeds legacy finite hypothesis'
    footer=validate_footer(c,owners)
    boundaries=c['branch_boundaries'];assert boundaries
    for r in boundaries:
        assert r['active']==0 and len(bytes.fromhex(r['held_state']))==len(bytes.fromhex(r['released_state']))==318
        assert len(bytes.fromhex(r['cursors']))==16 and len(bytes.fromhex(r['history']))==72
    return dict(passed=True,prototype_only=True,normative_deadline_safety=False,chunks=chunks,
                footer_commits=footer,callback_hypothesis_cck=hypotheses['callback'],entry_hypothesis_cck=hypotheses['entry_lateness'],cost_cck_per_e=5,service_margin_reserve_e=reserve_e,
                background_worker_calls=classes['prefix']['count'],observed_job_classes=classes,observed_owner_by_class_budget=job_budgets,
                maximum_whole_owner_cck=max(r['whole_owner_cck'] for r in chunks),
                declined_owner_calls=len(owners)-len(accepted),
                maximum_declined_owner_cck=max((r['elapsed_bus_cck'] for i,r in owners if i not in accepted),default=0),
                maximum_callback_cck=max(r['work_cck'] for r in callbacks),
                maximum_entry_lateness_cck=max(r['entry_phase_cck'] for r in callbacks),
                private_owner_released_before_every_sample=True,prefix_cost_classification_independently_recomputed=False,
                accounted_reservation_reconstructed=True,full_admission_predicate_independently_recomputed=False,
                scope='Observed emitted BSR-stack-store to RTS-stack-read spans. Includes wall elapsed during nested IRQs; CPU pre-store/post-read and full IRQ tails unresolved. Reconstructs accounted cost+service/margin reservation only; beam/IRQ/coherent-read predicates and universal bounds remain unresolved.')


def negative_controls(c):
    bad=dict(c);bad['branch_boundaries']=[dict(r) for r in c['branch_boundaries']]
    bad['branch_boundaries'][0]['active']=1
    try:validate_capture(bad)
    except AssertionError:return ['retained-private-ownership-record-rejected']
    raise AssertionError('Private ownership detector accepted negative control')


def required_extent(report,standard):
    if not (report.get('passed') is True and report.get('target')==dict(TARGET,video=standard)
            and report.get('execution')=='coherent-physical-input-contact-phase-probe'
            and report.get('no_simulation_state_injection') is True
            and report.get('frozen_complete_state_history_records_equal') is True):return False
    relative=report['capture'];path=ROOT/relative
    if report.get('evidence',{}).get('files',{}).get(relative)!=digest(path):return False
    with gzip.open(path,'rt') as h:c=json.load(h)
    if validate_capture(c)!=report['deadline']:return False
    if c['coherent_policy']!=report['coherent_policy']:return False
    if report['evidence']['files'].get('docs/tutorial-coherent-cost-policy.json')!=c['coherent_policy']['policy_sha256']:return False
    if not any(r['bytes_written']==512 for r in report['deadline']['footer_commits']):return False
    if c['deadline_negative_controls']!=['retained-private-ownership-record-rejected']:return False
    rows=c['endpoints']
    if len(rows)!=9 or sum(bool(r['human_launches'][0]) for r in rows)!=8:return False
    if not all(r.get('original_incoming_reference',{}).get('passed') is True for r in rows):return False
    if not all(r.get('original_outgoing_reference',{}).get('passed') is True for r in rows if r['human_launches'][0]):return False
    witnesses=[]
    for chunk in c['deadline']['chunks']:
        roots=[r for r in c['stack_timing']['calls'] if r['callee']=='game_launch_root' and enclosed(chunk,r)]
        launches=[r for r in c['launch_rows'] if chunk['entry']['cck']<=r['position']['cck']<=chunk['exit']['cck']]
        if roots and launches:witnesses.append(dict(owner=chunk,roots=roots,launches=launches))
    validate_witnesses(c,witnesses)
    return bool(witnesses) and witnesses==report['contact_owner_witnesses']==c['contact_owner_witnesses']


def validate_witnesses(c,witnesses):
    # Causal contact/root enclosure including indirect helper calls, never just
    # a coincident launch counter and root somewhere in the same long owner.
    calls=c['stack_timing']['calls']
    for witness in witnesses:
        owner=witness['owner']
        valid=False
        for root in witness['roots']:
            for launch in witness['launches']:
                marker=launch['position']['cck']
                dispatches=[r for r in calls if r['callee']=='game_preview_dispatch' and enclosed(owner,r) and enclosed(r,root) and root['exit']['cck']<=marker<=r['exit']['cck']]
                hooks=[r for r in calls if r['callee']=='game_history_contact' and enclosed(owner,r) and r['entry']['cck']<=marker<=r['exit']['cck']]
                for dispatch in dispatches:
                    samples=[r for r in c['dispatch_samples'] if dispatch['entry']['cck']<=r['position']['cck']<=root['entry']['cck']]
                    if len(samples)==1 and hooks:
                        assert len(bytes.fromhex(samples[0]['private_state']))==318
                        valid=True
        assert valid,'Background root lacks causal accepted contact/full private dispatch witness'


def validate_footer(c,owners):
    calls=c['stack_timing']['calls'];commits=[r for r in calls if r['callee']=='tutorial_footer_commit']
    writes=[r for r in c['overlay_writes'] if r['tutorial_active']]
    for row in writes:
        assert row['position']['vpos']<236 or row['position']['vpos']>251,'Live overlay write during footer DMA fetch'
        enclosing=[r for r in commits if r['entry']['cck']<=row['position']['cck']<=r['exit']['cck']]
        assert len(enclosing)==1 and any(enclosed(owner,enclosing[0]) for _,owner in owners),'Live overlay write lacks root footer commit owner'
    results=[]
    for commit in commits:
        assert any(enclosed(owner,commit) for _,owner in owners)
        samples=[r for r in c['footer_commit_samples'] if commit['entry']['cck']<=r['position']['cck']<=commit['exit']['cck']]
        assert len(samples)==1,'Footer commit lacks unique staged byte sample'
        sample=samples[0];payload={};bus_writes=0;bus_widths={}
        for row in writes:
            if not commit['entry']['cck']<=row['position']['cck']<=commit['exit']['cck']:continue
            bus_writes+=1;bus_widths[str(row['size'])]=bus_widths.get(str(row['size']),0)+1
            assert row['size'] in (2,4),'Footer transaction has unsupported bus write width'
            offset=row['addr']-c['overlay_base'];assert 0<=offset<=512-row['size'] and offset%2==0
            for i,b in enumerate(row['value'].to_bytes(row['size'],'big')):
                assert offset+i not in payload,'Footer byte written repeatedly'
                payload[offset+i]=b
        if sample['generation']==sample['footer_generation']:
            assert len(payload)==512 and bytes(payload[i] for i in range(512)).hex()==sample['staged'],'Footer commit differs from staged512 bytes'
        else:assert not payload,'Stale footer generation wrote live overlay'
        results.append(dict(entry=commit['entry'],exit=commit['exit'],bytes_written=len(payload),observed_bus_writes=bus_writes,observed_bus_width_counts=bus_widths,generation=sample['generation'],footer_generation=sample['footer_generation']))
    return results
