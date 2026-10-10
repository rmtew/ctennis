"""Partition retained coherent captures. This does not run or model the game.

Intervals are measured emitted-call stack-store -> final RTS-read spans. Nested
wall time (including IRQs) is assigned once by an explicit priority; it is not
CPU-exclusive time. Unknown instruction tails and gaps remain unclassified.
"""
import argparse
from bisect import bisect_left, bisect_right
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
CATEGORIES = (
    'landing_algorithm', 'shared_preview_dispatch', 'hardware_service', 'actual_outgoing_ball',
    'preview_envelopes_state_support', 'display_producer_footer',
    'controls_and_requests', 'endpoint_eligibility', 'scheduler_classification',
    'scheduler_admission', 'scheduler_owner_other',
    'remaining_mandatory_callback', 'unclassified',
)
NAMES = {
    'landing_algorithm': {'landing_try_prepare', 'landing_try_step'},
    'shared_preview_dispatch': {'game_preview_dispatch'},
    'hardware_service': {'game_poll_keyboard', 'poll_presentation',
                         'account_sim_timer', 'read_sim_timer'},
    'actual_outgoing_ball': {'game_ball_tick'},
    'preview_envelopes_state_support': {'game_preview_step_variant',
        'game_preview_endpoint_step', 'game_preview_complete', 'game_preview_result'},
    'display_producer_footer': {'tutorial_progress_slice', 'tutorial_footer_step',
        'tutorial_footer_commit', 'tutorial_render', 'tutorial_animate'},
    'controls_and_requests': {'tutorial_tick', 'tutorial_sample',
        'game_preview_request_projected', 'game_preview_request_body'},
    'endpoint_eligibility': {'game_preview_endpoint_pending'},
    'scheduler_classification': {'tutorial_background_class'},
    'scheduler_admission': {'tutorial_job_admitted'},
    'scheduler_owner_other': {'tutorial_background'},
    'remaining_mandatory_callback': {'simulation_update'},
}


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for data in iter(lambda: f.read(1 << 20), b''):
            h.update(data)
    return h.hexdigest()


def partition(start, end, intervals, segments=None):
    """Exhaustive half-open partition; smaller category index wins overlaps."""
    assert start <= end
    events = {start: [], end: []}
    for category, lo, hi in intervals:
        lo, hi = max(start, lo), min(end, hi)
        if lo < hi:
            events.setdefault(lo, []).append((category, 1))
            events.setdefault(hi, []).append((category, -1))
    counts = Counter()
    totals = [0] * len(CATEGORIES)
    previous = start
    for at in sorted(events):
        active = [i for i, n in counts.items() if n]
        chosen = min(active) if active else len(CATEGORIES)-1
        totals[chosen] += at-previous
        if segments is not None and at > previous:
            segments.append((chosen, previous, at))
        for category, delta in events[at]:
            counts[category] += delta
            assert counts[category] >= 0
        previous = at
    assert not any(counts.values()) and sum(totals) == end-start
    return dict(zip(CATEGORIES, totals))


def union_duration(start, end, rows):
    return partition(start, end, [(0, a, b) for a, b in rows])[CATEGORIES[0]]


def merge_spans(rows):
    result = []
    for start, end in sorted(rows):
        if start >= end:
            continue
        if result and start <= result[-1][1]:
            result[-1] = (result[-1][0], max(end, result[-1][1]))
        else:
            result.append((start, end))
    return result


def intersection_duration(start, end, left, right):
    left, right = merge_spans(left), merge_spans(right)
    i = j = total = 0
    while i < len(left) and j < len(right):
        lo = max(start, left[i][0], right[j][0])
        hi = min(end, left[i][1], right[j][1])
        total += max(0, hi-lo)
        if left[i][1] <= right[j][1]:
            i += 1
        else:
            j += 1
    return total


def owner_rows(c):
    chunks = {r['owner_call_index']: r for r in c['deadline']['chunks']}
    result = []
    for index, call in enumerate(c['stack_timing']['calls']):
        if call['callee'] == 'tutorial_background':
            row = dict(index=index, start=call['entry']['cck'],
                       end=call['exit']['cck'], accepted=index in chunks)
            if index in chunks:
                row['telemetry'] = chunks[index]['telemetry']
            result.append(row)
    return result


def selected_classifier_zero_cohort(c, owners):
    """Identify a narrow observed path, without inventing its refusal reason."""
    calls = sorted(c['stack_timing']['calls'],key=lambda r:r['entry']['cck'])
    call_times = [r['entry']['cck'] for r in calls]
    writes = sorted(c['scheduler_job_writes'],key=lambda r:r['position']['cck'])
    write_times = [r['position']['cck'] for r in writes]
    boundaries = sorted(c['boundaries'],key=lambda r:r['position']['cck'])
    boundary_times = [r['position']['cck'] for r in boundaries]
    callbacks = c['timing']['callbacks']
    completed_times = [r['completion']['cck'] for r in callbacks]
    rows = []
    epoch = 0
    seen = set()
    for owner in sorted(owners,key=lambda r:r['start']):
        if owner['accepted']:
            epoch += 1  # Any optional job invalidates the proposed frontier cache.
            continue
        lo,hi = owner['start'],owner['end']
        nested = [r for r in calls[bisect_left(call_times,lo):bisect_right(call_times,hi)]
                  if r['callee'] != 'tutorial_background' and r['exit']['cck'] <= hi]
        classifiers = [r for r in nested if r['callee']=='tutorial_background_class']
        if len(classifiers) != 1 or any(r['callee']=='tutorial_job_admitted' for r in nested):
            continue
        local = writes[bisect_left(write_times,lo):bisect_right(write_times,hi)]
        variants = [r['value'] for r in local if r['field']=='tutorial_job_variant']
        budgets = [r['value'] for r in local if r['field']=='tutorial_job_budget']
        if variants != [0] or not budgets or budgets[-1] != 0:
            continue
        callback_index = bisect_right(completed_times,lo)-1
        # Entry snapshots precede that callback's control handling. The next
        # entry observes the controller fields after the current callback and
        # intervening root owners; optional root work does not change them.
        boundary_index = bisect_left(boundary_times,hi)
        assert callback_index >= 0 and boundary_index < len(boundaries)
        boundary = boundaries[boundary_index]
        fields = boundary['fields']
        assert fields['tutorial_active_variant'] == 0
        generation = fields['tutorial_generation']
        callback = callbacks[callback_index]['callback']
        assert callbacks[callback_index]['completion']['cck'] <= lo <= hi
        classifier = classifiers[0]
        key = (callback,generation,0,epoch)
        rows.append(dict(start_cck=lo,end_cck=hi,class_start_cck=classifier['entry']['cck'],
            class_end_cck=classifier['exit']['cck'],callback=callback,generation=generation,
            intervening_optional_job_epoch=epoch,repeat_since_same_epoch_first=key in seen))
        seen.add(key)
    return rows


def collapsed_breakdown(totals, post_known, hz):
    """A second exhaustive partition, not a milestone added to full totals."""
    pre = {k:v-(post_known[k] if post_known is not None else 0)
           for k,v in totals.items()}
    assert all(v >= 0 for v in pre.values())
    bins = dict(
        actual_math_before_known=sum(pre[k] for k in
            ('landing_algorithm','shared_preview_dispatch','actual_outgoing_ball')),
        scheduling_and_preview_support_before_known=sum(pre[k] for k in
            ('preview_envelopes_state_support','endpoint_eligibility',
             'scheduler_classification','scheduler_admission','scheduler_owner_other')),
        measured_hardware_service_and_display_production_before_known=sum(pre[k] for k in
            ('hardware_service','display_producer_footer')),
        mandatory_callback_controls_requests_before_known=sum(pre[k] for k in
            ('controls_and_requests','remaining_mandatory_callback')),
        unclassified_before_known=pre['unclassified'],
        known_upper_bound_to_qualifying_copjmp=sum(post_known.values())
            if post_known is not None else 0)
    assert sum(bins.values()) == sum(totals.values())
    return dict(partition_cck=bins,partition_ms={k:v*1000/hz for k,v in bins.items()},
                pre_known_partition_cck=pre,sum_verified=True,
                known_cutoff_observed=post_known is not None,
                waiting_cause_attributed=False)


def trial(c, endpoint, intervals, owners, hz, classifier_zero):
    start = endpoint['request']['cck']
    scene = endpoint['first_actual_publication']
    end = scene['position']['cck']
    assert end-start == endpoint['latency_cck']
    generation = endpoint['generation']
    segments = []
    totals = partition(start, end, intervals, segments)
    calls = c['stack_timing']['calls']
    intersects = lambda r: r['entry']['cck'] < end and r['exit']['cck'] > start
    requests = [r for r in calls if r['callee'] == 'game_preview_request_projected'
                and intersects(r)]
    profiles = [r for r in c['endpoint_profiles'] if r['generation'] == generation
                and r['variant'] == 0 and r.get('after', {}).get('ready')
                and start <= r['exit']['cck'] <= end]
    known = min((r['exit']['cck'] for r in profiles), default=None)
    known_basis = 'matching selected endpoint API ready-return upper bound'
    if known is None:
        dense = [r for r in c['branch_boundaries'] if r['generation'] == generation
                 and int(r['outcomes'][:4], 16)
                 and start <= r['position']['cck'] <= end]
        known = min((r['position']['cck'] for r in dense), default=None)
        known_basis = 'matching selected dense-outcome released-boundary sample upper bound'
    owner_subset = [r for r in owners if r['start'] < end and r['end'] > start]
    refused = [r for r in owner_subset if not r['accepted']]
    # A repeated request is observed work, not evidence of equal causal inputs.
    root_work = [r for r in c['contact_owner_witnesses']
                 if r['owner']['entry']['cck'] < end
                 and r['owner']['exit']['cck'] > start]
    selected_contact = min((r['owner']['entry']['cck'] for r in root_work
        if r['owner']['telemetry']['tutorial_job_variant'] == 0), default=None)
    selected_contact_end = min((r['owner']['exit']['cck'] for r in root_work
        if r['owner']['telemetry']['tutorial_job_variant'] == 0), default=None)
    pending = [r for r in calls if r['callee'] == 'game_preview_endpoint_pending'
               and intersects(r)]
    def eligibility_slice(lo, hi):
        wrappers = [(r['entry']['cck'], r['exit']['cck']) for r in pending
                    if r['entry']['cck'] < hi and r['exit']['cck'] > lo]
        selection = [(r['entry']['cck'],r['exit']['cck']) for r in calls
                     if r['callee'] == 'game_preview_selection_valid'
                     and any(a <= r['entry']['cck'] <= r['exit']['cck'] <= b
                             for a,b in wrappers)]
        inclusive = union_duration(lo,hi,wrappers)
        nested = union_duration(lo,hi,selection)
        assert nested <= inclusive
        return dict(pending_calls=len(wrappers), pending_union_cck=inclusive,
                    nested_selection_valid_union_cck=nested,
                    pending_excluding_selection_cck=inclusive-nested)
    eligibility = dict(total=eligibility_slice(start,end),
        pre_selected_contact=eligibility_slice(start,selected_contact)
            if selected_contact is not None else None,
        after_known=eligibility_slice(known,end) if known is not None else None,
        pre_contact_cutoff_cck=selected_contact,
        scope='Conservative cutoff at containing selected-contact owner entry, before launch. '
              'Does not assert every pending call belongs to the accepted generation; request '
              'fencing and exact launch_saved stores need stronger evidence. After-known uses '
              'the matching-generation sampled upper bound.')
    callback_union = union_duration(start, end,
        [(r['entry']['cck'], r['completion']['cck']) for r in c['timing']['callbacks']])
    ready_partition = partition(known, end, intervals) if known is not None else None
    narrow = [r for r in classifier_zero if r['start_cck'] >= start and r['end_cck'] <= end]
    repeats = [r for r in narrow if r['repeat_since_same_epoch_first']]
    groups = Counter((r['callback'],r['generation'],r['intervening_optional_job_epoch'])
                     for r in narrow)
    def cohort_duration(rows):
        return union_duration(start,end,[(r['class_start_cck'],r['class_end_cck']) for r in rows])
    narrow_metrics = dict(owners=len(narrow),classifier_union_cck=cohort_duration(narrow),
        repeated_after_first_same_callback_generation_no_optional_job=len(repeats),
        repeated_classifier_union_cck=cohort_duration(repeats),
        maximum_attempts_same_callback_generation_no_optional_job=max(groups.values(),default=0),
        criteria='Declined enclosing root; exactly one emitted background_class; no job_admitted; '
            'exactly one root-local variant store0; final root-local budget store0; '
            'next-callback-entry observed activevariant0. Callback/generation/variant and any optional '
            'job fence repeats. Identifies selected classifier-zero path, not its refusal reason.',
        scope='Measured classifier wall span only, including IRQ elapsed. Cache/flag overhead and '
            'wall-latency improvement are not measured; source guards/clock reason not reconstructed.')
    branch_work = {}
    for role, variant in [('selected', 0), ('competing', 1)]:
        windows = [(r['start'], r['end']) for r in owner_subset if r.get('telemetry', {})
                   .get('tutorial_job_kind') in (1, 2)
                   and r['telemetry']['tutorial_job_variant'] == variant]
        branch_work[role] = {}
        for category in ('shared_preview_dispatch', 'landing_algorithm', 'actual_outgoing_ball',
                         'preview_envelopes_state_support'):
            index = CATEGORIES.index(category)
            spans = [(a,b) for kind,a,b in segments if kind == index]
            branch_work[role][category] = intersection_duration(start,end,spans,windows)
        branch_work[role]['scope'] = ('Exclusive primary category segments within emitted owner '
            'telemetry variant; secondary subset diagnostics are not added to the primary partition.')
    dispatch_segments = [(a,b) for kind,a,b in segments
                         if kind == CATEGORIES.index('shared_preview_dispatch')]
    dispatch_phase = None
    if selected_contact is not None:
        dispatch_phase = dict(before_first_selected_contact_owner_cck=
            union_duration(start,selected_contact,dispatch_segments),
            first_selected_contact_owner_dispatch_cck=
            union_duration(selected_contact,selected_contact_end,dispatch_segments),
            after_first_selected_contact_owner_cck=
            union_duration(selected_contact_end,end,dispatch_segments),
            scope='Primary dispatch partition subdivided by actual selected-contact owner. '
                  'Does not identify superseded-generation work in held alignment.')
    services = {}
    hardware_segments = [(a,b) for kind,a,b in segments
                         if kind == CATEGORIES.index('hardware_service')]
    service_names = ('poll_presentation','game_poll_keyboard','account_sim_timer')
    service_masks = []
    for index,name in enumerate(service_names):
        matched = [r for r in calls if r['callee']==name and intersects(r)]
        mask = [(r['entry']['cck'],r['exit']['cck']) for r in matched]
        service_masks.extend((index,a,b) for a,b in mask)
        services[name] = dict(calls=len(matched))
    service_segments = []
    partition(start,end,service_masks,service_segments)
    for index,name in enumerate(service_names):
        mask = [(a,b) for kind,a,b in service_segments if kind==index]
        services[name]['primary_exclusive_union_cck'] = intersection_duration(
            start,end,hardware_segments,mask)
    measured_service_sum = sum(v['primary_exclusive_union_cck'] for v in services.values())
    assert measured_service_sum <= totals['hardware_service']
    services['other_service'] = dict(primary_exclusive_union_cck=
                                    totals['hardware_service']-measured_service_sum)
    return dict(label=endpoint['label'], generation=generation,
        interval=dict(request_cck=start, first_qualifying_copjmp_cck=end,
                      total_cck=end-start, milliseconds=(end-start)*1000/hz),
        partition_cck=totals, partition_ms={k: v*1000/hz for k, v in totals.items()},
        partition_sum_verified=True, callback_union_cck=callback_union,
        request_api_calls=len(requests),
        request_api_union_cck=union_duration(start, end,
            [(r['entry']['cck'], r['exit']['cck']) for r in requests]),
        latest_request_api_entry_cck=max((r['entry']['cck'] for r in requests),default=None),
        latest_request_generation_verified=False,
        accepted_owners=sum(r['accepted'] for r in owner_subset),
        declined_owners=len(refused), declined_owner_union_cck=union_duration(start,end,
            [(r['start'],r['end']) for r in refused]),
        background_contact_owner_witnesses=len(root_work),
        endpoint_ready_before_dense=endpoint['endpoint_ready_before_dense'],
        endpoint_known_return_upper_bound_cck=known,
        endpoint_known_basis=known_basis if known is not None else 'not observed before qualifying publication',
        endpoint_known_upper_bound_to_publication_cck=end-known if known is not None else None,
        endpoint_known_to_publication_partition_cck=ready_partition,
        branch_work_exclusive_cck=branch_work,
        dispatch_phase_diagnostics=dispatch_phase,
        hardware_service_diagnostics=services,
        hardware_service_priority='Nested presenter first, keyboard second, timer accounting third; '
            'hardware-service primary-mask intersection. Secondary service amounts are disjoint '
            'and sum to the primary hardware-service category including explicit other_service.',
        collapsed_nonoverlapping_breakdown=collapsed_breakdown(totals,ready_partition,hz),
        endpoint_eligibility_diagnostics=eligibility,
        selected_classifier_zero_diagnostics=narrow_metrics,
        queued_bank_sha256=scene['bank_sha256'],
        native_sprite_matched=scene['native_sprite_check']['matched'],
        waiting_attribution=dict(input_wait_per_trial=None, display_wait_per_trial=None,
            deadline_reservation_wait_per_trial=None,
            reason='No complete per-trial consumed-input/failed-branch/ready-publication deadline ledger. '
                   'Declined owner spans measure work; their adjacent gaps are not attributed to waiting.'),
        scope='Physical action boundary to first qualifying actual COPJMP. Live-clean qualification '
              'can exclude an earlier valid completed bank. Aligned-held includes ongoing placement '
              'edits and superseded requests. Endpoint-known uses matching ready API return, an upper '
              'bound on its write; no first-scanout or physical-resume inference.')


def reduce_report(path):
    report = json.loads(path.read_text())
    assert report['passed'] and report['normative_deadline_safety'] is False
    bound = report['evidence']['files']
    # Existing source/tool/raw bindings are verified, not regenerated.
    for name, expected in bound.items():
        p = Path(name) if Path(name).is_absolute() else ROOT/name
        assert p.is_file() and digest(p) == expected, f'Changed/missing evidence binding: {name}'
    capture = ROOT/report['capture']
    with gzip.open(capture, 'rt') as f:
        c = json.load(f)
    assert c['timing']['dropped_notifications'] == 0
    assert not c['stack_timing']['open_enclosing_calls']
    assert c['coherent_policy'] == report['coherent_policy']
    hz = report['final_caption']['physical_clock_hz']
    intervals = []
    for call in c['stack_timing']['calls']:
        for i, category in enumerate(CATEGORIES[:-1]):
            if call['callee'] in NAMES[category]:
                if category == 'actual_outgoing_ball' and call.get('caller') not in {
                        'game_preview_continue_one', 'game_preview_flight_one'}:
                    continue
                intervals.append((i, call['entry']['cck'], call['exit']['cck']))
                break
    owners = owner_rows(c)
    classifier_zero = selected_classifier_zero_cohort(c,owners)
    trials = [trial(c, e, intervals, owners, hz,classifier_zero) for e in c['endpoints']]
    return dict(standard=report['target']['video'], physical_clock_hz=hz,
        original_run_id=report['evidence']['run_id'], report_sha256=digest(path),
        capture_sha256=digest(capture), verified_original_binding_count=len(bound),
        original_source_commit=report['evidence']['commit'],
        native_product_commit=report['evidence']['native_product_commit'],
        native_sha256=report['executable_sha256'], coherent_policy=report['coherent_policy'],
        raw_bindings={k:v for k,v in bound.items() if 'literal-rpc' in k},
        trials=trials, final_caption=report['final_caption_validation'],
        input_extrema=report['input_probe'],
        retained_holds=dict(full_admission_predicate_independently_recomputed=False,
            prefix_cost_classification_independently_recomputed=False,
            normative_deadline_safety=False, causal_paired_improvement_claim=False))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--report', action='append', type=Path,
                   help='Existing native report; repeat for sequential PAL/NTSC reduction')
    p.add_argument('--output', type=Path,
                   default=ROOT/'build/tests/tutorial-latency-accounting/report.json')
    args = p.parse_args()
    paths = args.report or [ROOT/f'build/tests/coherent-contact-native-{s}/report.json'
                            for s in ('pal','ntsc')]
    output = dict(schema=1, execution='offline-existing-capture-latency-accounting',
        accounting_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        reducer_sha256=digest(__file__), interval_categories=list(CATEGORIES),
        category_call_names={k:sorted(v) for k,v in NAMES.items()},
        attribution_priority='Earlier category wins; nested parents lose that interval. '
            'All totals form one exhaustive partition; secondary milestones overlap it and are not added.',
        actual_outgoing_ball_scope='Only emitted game_ball_tick calls whose captured caller is '
            'game_preview_continue_one (tail branch to flight_one) or game_preview_flight_one. '
            'Incoming dispatch and landing-stage ball calls remain in their measured parents.',
        measurement_scope='Emitted call stack-store through final RTS-read bus spans; IRQ elapsed '
            'included once, not isolated CPU time. Instruction tails/gaps remain unclassified. '
            'Callbacks contain work and are never treated as idle. No new native execution.',
        comparison_requirements='Improvement needs paired identical accepted-generation causal state, '
            'physical input trace/phasing, native source/policy/target, incoming/outgoing original-core '
            'outputs, same publication qualification and retained complete timing extent. '
            'Same seed or endpoint label alone does not establish pairing.',
        regions=[reduce_report(path.resolve()) for path in paths])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(output,indent=2)+'\n')
    print(f'{args.output}: {digest(args.output)}')


if __name__ == '__main__':
    main()
