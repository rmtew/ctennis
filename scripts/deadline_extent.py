"""Experimental G2 finite timing detector; this never grants normative safety."""
from bisect import bisect_right
from native_tools import ROOT
import gzip
import json

B_CHUNK_CCK=5000
B_CALLBACK_CCK=56500
B_ENTRY_CCK=1250
B_TRANSPORT_CCK=50000
OPERATIONS={'game_core_sample_pads_body':3,'game_core_sample_result_body':4,
            'game_core_clear_inputs_body':5,'game_round_poll_body':7,'game_core_latch_actions_body':9}


def validate_capture(captured):
    calls=captured['stack_timing']['calls'];callbacks=captured['timing']['callbacks']
    workers=[r for r in calls if r['callee']=='game_preview_step' and r.get('caller')=='tutorial_background']
    owners=[r for r in calls if r['callee']=='tutorial_background']
    assert workers,'No between-callback worker executed'
    root_calls=sorted((r for r in calls if r['depth']==0 and r.get('caller') is None),key=lambda r:r['entry']['cck'])
    services=[]
    for i in range(len(root_calls)-3):
        seq=root_calls[i:i+4]
        if [r['callee'] for r in seq]==['account_sim_timer','game_poll_keyboard','poll_presentation','account_sim_timer']:
            services.append(seq[-1]['exit']['cck']-seq[0]['entry']['cck'])
    assert services,'Missing complete root service sequence'
    entries=[r['entry']['cck'] for r in callbacks];rows=[];accepted=set()
    owners.sort(key=lambda r:r['entry']['cck']);owner_entries=[r['entry']['cck'] for r in owners]
    ordered=sorted(calls,key=lambda r:r['entry']['cck']);call_entries=[r['entry']['cck'] for r in ordered]
    operations=captured['deadline_operations'];op_entries=[r['position']['cck'] for r in operations]
    for worker in workers:
        index=bisect_right(owner_entries,worker['entry']['cck'])-1
        assert index>=0
        owner=owners[index]
        assert owner['entry']['cck']<=worker['entry']['cck']<=worker['exit']['cck']<=owner['exit']['cck']
        accepted.add(owner['entry']['cck'])
        assert owner['depth']==0 and owner.get('caller') is None
        assert owner['elapsed_bus_cck']<=B_CHUNK_CCK,'Complete background owner exceeds declared hypothesis'
        at=bisect_right(entries,owner['entry']['cck'])-1
        assert 0<=at<len(callbacks)-1
        assert callbacks[at]['completion']['cck']<=owner['entry']['cck']<=owner['exit']['cck']<=callbacks[at+1]['entry']['cck'],'Private owner crosses logical sample/callback'
        sub=ordered[bisect_right(call_entries,worker['entry']['cck']):bisect_right(call_entries,worker['exit']['cck'])]
        bodies=[r['callee'] for r in sub if r['exit']['cck']<=worker['exit']['cck'] and (r['callee'] in OPERATIONS or r['callee']=='(a1)')]
        writes=operations[bisect_right(op_entries,worker['entry']['cck']):bisect_right(op_entries,worker['exit']['cck'])]
        assert len(bodies)==len(writes)==1 and writes[0]['operation'] in OPERATIONS.values(),(worker,bodies,writes)
        if bodies[0] in OPERATIONS:assert OPERATIONS[bodies[0]]==writes[0]['operation']
        forbidden={'game_preview_dispatch','game_preview_resolve_one','game_preview_prime_one','game_preview_finish_variant','game_preview_compare_geometry','game_preview_endpoint_try','tutorial_animate','tutorial_progress_slice'}
        assert not any(r['callee'] in forbidden and worker['entry']['cck']<=r['entry']['cck']<=worker['exit']['cck'] for r in sub)
        rows.append(dict(operation=writes[0]['operation'],whole_owner_cck=owner['elapsed_bus_cck'],worker_cck=worker['elapsed_bus_cck'],entry=owner['entry'],exit=owner['exit'],callback_after=callbacks[at+1]['callback']))
    assert max(r['work_cck'] for r in callbacks)<=B_CALLBACK_CCK,'Full callback exceeds declared hypothesis'
    assert max(r['entry_phase_cck'] for r in callbacks)<=B_ENTRY_CCK,'Nominal callback entry lateness exceeds declared hypothesis'
    return dict(passed=True,prototype_only=True,normative_s05_s18_g2_safety=False,
        chunks=rows,background_worker_calls=len(workers),classes=sorted({r['operation'] for r in rows}),
        maximum_whole_owner_cck=max(r['whole_owner_cck'] for r in rows),chunk_hypothesis_cck=B_CHUNK_CCK,
        root_service_sequences=len(services),maximum_root_service_cck=max(services),root_service_hypothesis_cck=2500,
        root_service_hypothesis_observed=max(services)<=2500,admission_arithmetic_independently_reconstructed=False,
        declined_owner_calls=sum(r['entry']['cck'] not in accepted for r in owners),
        maximum_declined_owner_cck=max((r['elapsed_bus_cck'] for r in owners if r['entry']['cck'] not in accepted),default=0),
        maximum_callback_cck=max(r['work_cck'] for r in callbacks),callback_hypothesis_cck=B_CALLBACK_CCK,
        maximum_entry_lateness_cck=max(r['entry_phase_cck'] for r in callbacks),entry_hypothesis_cck=B_ENTRY_CCK,
        private_owner_released_before_every_sample=True,
        unsupported_operation_exclusion_scope='Read-only classifier CPU partitions and source guards; call-stack detector cannot observe every BRA tail.',
        scope='Finite emitted owner stack spans include classify/admission/worker/release/progress; CPU pre-store/post-return and full IRQ entry/RTE effects remain unresolved uncertainty, never a WCET.')


def negative_controls(captured):
    # Detector challenges use altered measurement records, never simulation
    # oracle state or a runtime product. Full S25 native fault injection is open.
    bad=dict(captured);bad['stack_timing']=dict(captured['stack_timing'])
    bad['stack_timing']['calls']=[dict(r) for r in captured['stack_timing']['calls']]
    worker=next(r for r in bad['stack_timing']['calls'] if r['callee']=='game_preview_step' and r.get('caller')=='tutorial_background')
    owner=next(r for r in bad['stack_timing']['calls'] if r['callee']=='tutorial_background' and r['entry']['cck']<=worker['entry']['cck']<=worker['exit']['cck']<=r['exit']['cck'])
    owner['elapsed_bus_cck']=B_CHUNK_CCK+1
    try:validate_capture(bad)
    except AssertionError:return ['oversized-complete-owner-record-rejected']
    raise AssertionError('Oversized owner detector accepted negative control')


def native_extent(report,standard):
    from predictor_extent import native_extent as predictor_extent
    relative='build/tests/deadline-native-'+standard.lower()+'/latency.json.gz'
    try:
        with gzip.open(ROOT/relative,'rt') as handle:captured=json.load(handle)
        expected=validate_capture(captured)
    except (OSError,ValueError,KeyError,AssertionError):return False
    probe=report.get('input_probe') or {}
    return (predictor_extent(report,standard,'deadline-native-') and report.get('deadline')==expected
        and expected.get('prototype_only') is True and expected.get('normative_s05_s18_g2_safety') is False
        and probe.get('maximum_keyboard_poll_gap_cck',B_TRANSPORT_CCK+1)<=B_TRANSPORT_CCK
        and captured.get('deadline_negative_controls')==['oversized-complete-owner-record-rejected'])
