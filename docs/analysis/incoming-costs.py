"""Read retained native bus-span evidence; never build or execute the game.

Usage: python docs/analysis/incoming-costs.py --output /tmp/incoming-costs.json
Intervals are half-open; nested calls are unioned before subtraction. Raw
captured state, instructions and events remain in private build storage.
"""
import argparse
from bisect import bisect_left, bisect_right
from collections import Counter
import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = {'game_preview_request', 'game_preview_step', 'game_preview_result',
          'game_preview_cancel', 'game_preview_endpoint_try'}
LOGICAL = {'game_core_init_body', 'game_core_select_body',
           'game_core_sample_pads_body', 'game_core_sample_result_body',
           'game_core_clear_inputs_body', 'game_core_return_title_body',
           'game_round_poll_body', 'game_tick_dispatch_body',
           'game_core_latch_actions_body'}
ADMISSION = {'tutorial_work_remaining', 'tutorial_work_admitted',
             'tutorial_presentation_admitted', 'tutorial_render_admitted'}
PRESENT = {'tutorial_progress_fast_publish', 'tutorial_animate',
           'tutorial_footer', 'tutorial_render'}
NATIVE_INPUT = {'sample_amiga_joystick', 'ui_sample', 'game_native_commands',
                'tutorial_controls'}
METADATA = {'tutorial_progress_returned', 'tutorial_animation_due',
            'tutorial_progress_status'}
POLLING = {'account_sim_timer', 'game_poll_keyboard', 'poll_presentation'}


def merge(spans):
    result = []
    for a, b in sorted(spans):
        assert a <= b
        if a == b:
            continue
        if result and a <= result[-1][1]:
            result[-1][1] = max(b, result[-1][1])
        else:
            result.append([a, b])
    return result


def clip(spans, lo, hi):
    return merge((max(a, lo), min(b, hi)) for a, b in spans
                 if a < hi and lo < b)


def minus(spans, removed):
    result = []
    for a, b in merge(spans):
        for x, y in merge(removed):
            if y <= a or x >= b:
                continue
            if a < x:
                result.append([a, x])
            a = max(a, y)
            if a >= b:
                break
        if a < b:
            result.append([a, b])
    return result


def length(spans):
    return sum(b-a for a, b in merge(spans))


def span(row):
    return row['entry']['cck'], row['exit']['cck']


def inside(row, owners):
    a, b = span(row)
    index = bisect_right(owners, a, key=lambda pair: pair[0])-1
    return index >= 0 and b <= owners[index][1]


def digest(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def distribution(values):
    values=sorted(values)
    return dict(samples=len(values),min=values[0],median=statistics.median(values),
                p95=values[(95*len(values)+99)//100-1],max=values[-1])


def cia_decisions(capture,rows,lo,hi,callbacks,steps):
    """Decode the last successful coherent read of the actual CIA counter."""
    reads=capture['timer_reads']
    times=[r['position']['cck'] for r in reads]
    assert times==sorted(times)
    parents={tuple(child):r for r in rows if r['callee']=='tutorial_work_remaining'
             for child in r['child_spans']}
    ordered_steps=sorted(steps,key=lambda r:span(r)[0])
    step_times=[span(r)[0] for r in ordered_steps]
    result=[]
    for timer in rows:
        if timer['callee']!='read_sim_timer' or timer['caller']!='tutorial_work_remaining':
            continue
        a,b=span(timer)
        if not lo<=a<hi:
            continue
        parent=parents[span(timer)]
        if parent['caller']!='tutorial_tick':
            continue # Direct caller is specifically the source's dense-slice check.
        packet=reads[bisect_left(times,a):bisect_right(times,b)][-7:]
        assert [r['addr'] for r in packet]==[0xbfd700,0xbfd600,0xbfd500,0xbfd400,0xbfd500,0xbfd700,0xbfd600]
        v=[r['value'] for r in packet]
        assert v[2]==v[4] and v[:2]==v[5:7]
        params=packet[-1]['timer_parameters']
        assert all(r['timer_parameters']==params for r in packet)
        current=(v[0]<<24)|(v[1]<<16)|(v[2]<<8)|v[3]
        remaining=max(0,params['simulation_interval']-params['simulation_phase']-
                      ((params['last_timer_count']-current)&0xffffffff))
        index=bisect_left(step_times,span(parent)[1])
        owner=next((c for c in callbacks if c[0]<=a and b<=c[1]),None)
        assert owner is not None
        next_step=ordered_steps[index] if index<len(ordered_steps) else None
        admitted=bool(next_step and span(next_step)[0]<owner[1])
        assert admitted==(remaining>=7000), ('Dense source/observed branch mismatch',a,remaining)
        result.append(dict(cck=a,remaining_e_ticks=remaining,admitted=admitted,
                           four_operation_reserve_met=remaining>=10000))
    assert sum(r['admitted'] for r in result)==len(steps)
    return dict(samples=len(result),admitted_two_operation=sum(r['admitted'] for r in result),
                met_four_operation_reserve=sum(r['four_operation_reserve_met'] for r in result),
                refused_two_operation=sum(not r['admitted'] for r in result),
                admitted_remaining_e_ticks=distribution([r['remaining_e_ticks'] for r in result if r['admitted']]),
                refused_remaining_e_ticks=distribution([r['remaining_e_ticks'] for r in result if not r['admitted']]),
                scope='Matched literal coherent CIA reads and direct dense-slice remaining-time calls; current incoming kind0 thresholds10000/7000 E-ticks. No reserve changes.')


def analyse(standard):
    directory = ROOT / ('build/tests/incoming-flight-native-'+standard.lower())
    report_path, capture_path = directory/'report.json', directory/'latency.json'
    report = json.loads(report_path.read_text())
    capture = json.loads(capture_path.read_text())
    assert report['passed'] and report['evidence']['state']=='complete'
    assert report['evidence']['changed_during_run']==[]
    for name, expected in report['evidence']['files'].items():
        assert digest(Path(name))==expected, ('Retained receipt dependency drift',name)
    assert report['evidence']['commit'] == 'a936ebac16c977cfc6c39a4426de1cbfdf62170e'
    assert report['executable_sha256'] == digest(ROOT/'build/amiga/interfaces/enhanced/baseline-rally')
    rows = capture['stack_timing']['calls']
    endpoint = capture['endpoints'][-1]
    assert endpoint['label'] == 'fresh-D-edit'
    lo, pub = endpoint['request']['cck'], endpoint['first_actual_publication']['position']['cck']
    hooks = [r for r in rows if r['callee']=='game_preview_launch' and lo < span(r)[0] < pub]
    assert len(hooks) == 1
    hook = span(hooks[0])[0]
    workers = merge(span(r) for r in rows if r['callee'] in PUBLIC)
    logical = [r for r in rows if inside(r, workers) and
               (r['callee'] in LOGICAL or
                r['callee']=='(a1)' and r['caller']=='game_preview_execute_record')]
    logical_spans=merge(span(r) for r in logical)
    ball=[r for r in rows if r['callee']=='game_ball_tick' and inside(r,workers) and not inside(r,logical_spans)]
    fast=[r for r in rows if r['callee']=='landing_try_fast' and inside(r,workers)]
    active = [span(r) for r in rows if r['callee']=='game_active_tick']
    dispatch = [r for r in logical if r['callee']=='game_tick_dispatch_body' or
                r['callee']=='(a1)' and any(span(r)[0] <= a and b <= span(r)[1] for a,b in active)]
    contact_dispatch = [r for r in dispatch if span(r)[0] <= hook < span(r)[1]]
    assert len(contact_dispatch)==1
    dispatcher_return = span(contact_dispatch[0])[1]
    callbacks = [span(r) for r in rows if r['callee']=='simulation_update']

    def account(a, b):
        cb = clip(callbacks, a, b)
        work = clip(workers, a, b)
        core = clip([span(r) for r in logical], a, b)
        tick = clip([span(r) for r in dispatch], a, b)
        sequential=clip([span(r) for r in ball],a,b)
        bounded=clip([span(r) for r in fast],a,b)
        original=merge(core+sequential+bounded)
        admissions = minus(clip([span(r) for r in rows if r['callee'] in ADMISSION], a,b), work)
        presentation = minus(clip([span(r) for r in rows if r['callee'] in PRESENT], a,b), work)
        used=merge(work+admissions+presentation)
        inputs=minus(clip([span(r) for r in rows if r['callee'] in NATIVE_INPUT],a,b),used)
        used=merge(used+inputs)
        metadata=minus(clip([span(r) for r in rows if r['callee'] in METADATA],a,b),used)
        used=merge(used+metadata)
        polling=minus(clip([span(r) for r in rows if r['callee'] in POLLING],a,b),cb)
        for child,parent in ((work,cb),(core,work),(tick,core),(sequential,work),(bounded,work),
                             (admissions,cb),(presentation,cb),(inputs,cb),(metadata,cb)):
            assert not minus(child,parent), 'Category outside its disclosed owner'
        groups=dict(original_dispatch=tick,other_original_envelopes=minus(core,tick),
                    original_sequential_ball=sequential,bounded_landing_helper=bounded,
                    public_worker_residual=minus(work,original),callback_admission=admissions,
                    callback_presentation=presentation,callback_native_input_controls=inputs,
                    callback_progress_metadata=metadata,callback_other_unassigned=minus(cb,used),
                    outside_callback_observed_polling=polling,
                    outside_callback_other_unassigned=minus([[a,b]],merge(cb+polling)))
        sets=list(groups.values())
        for i,left in enumerate(sets):
            for right in sets[i+1:]:
                assert length(left+right)==length(left)+length(right), 'Overlapping finalized categories'
        parts={name:length(value) for name,value in groups.items()}
        assert sum(parts.values())==b-a
        return dict(start_cck=a,end_cck=b,elapsed_cck=b-a,disjoint_cck=parts)

    entered_steps=[r for r in rows if r['callee']=='game_preview_step' and lo<=span(r)[0]<hook]
    original_spans=merge(span(r) for r in logical)
    step_counts=[]
    for step in entered_steps:
        a,b=span(step)
        body=[r for r in logical if a<=span(r)[0] and span(r)[1]<=b]
        # Direct outgoing calls are operations too; nested dispatcher ball calls
        # remain within their single original dispatcher envelope.
        body += [r for r in rows if r['callee']=='game_ball_tick' and
                 not inside(r,original_spans) and a<=span(r)[0] and span(r)[1]<=b]
        step_counts.append(len(body))
    callback_steps=[]
    for a,b in callbacks:
        if a < hook and lo < b:
            callback_steps.append(sum(a<=span(r)[0]<b for r in entered_steps))
    requests=[r for r in rows if r['callee']=='game_preview_request' and lo<=span(r)[0]<hook]
    core_counts=Counter(r['callee'] for r in logical if lo<=span(r)[0]<hook)
    api_costs=[r['elapsed_bus_cck'] for r in entered_steps]
    nested = {}
    for name in ('game_play_tick','game_ball_tick','game_advance_ball','game_ratio32',
                 'game_scene_finish_tick','game_scene_build_players','game_scene_update_fields',
                 'game_audio_tick','game_advance_clocks','game_player_tick','game_move_player'):
        matches=[span(r) for r in rows if r['callee']==name and inside(r,workers)]
        nested[name]=length(clip(matches,lo,hook)) if matches else None
    prime=[span(r) for r in rows if r['callee']=='game_preview_prime_one']
    stable_steps=[r for r in entered_steps if span(requests[-1])[1]<=span(r)[0] and span(r)[1]<=hook
                  and not any(span(r)[0]<=a and b<=span(r)[1] for a,b in prime)]
    stable_steps.sort(key=lambda r:span(r)[0])
    pair_sums=[stable_steps[i]['elapsed_bus_cck']+stable_steps[i+1]['elapsed_bus_cck']
               for i in range(0,len(stable_steps)-1,2)]
    return dict(standard=standard,receipt_sha256=digest(report_path),capture_sha256=digest(capture_path),
                source_commit=report['evidence']['commit'],executable_sha256=report['executable_sha256'],
                generation=endpoint['generation'],intervals=dict(request_to_hook=account(lo,hook),
                hook_to_dispatcher_return=account(hook,dispatcher_return),
                dispatcher_return_to_publication=account(dispatcher_return,pub)),
                entered_step_count=len(entered_steps),actual_operations_per_step=dict(sorted(Counter(step_counts).items())),
                steps_per_callback=dict(sorted(Counter(callback_steps).items())),
                request_calls=[dict(start=span(r)[0],end=span(r)[1],elapsed=r['elapsed_bus_cck']) for r in requests],
                original_envelope_counts=dict(core_counts),
                worker_api_cost_cck=dict(min=min(api_costs),max=max(api_costs),sum=sum(api_costs)),
                dense_admission=cia_decisions(capture,rows,lo,hook,callbacks,entered_steps),
                adjacent_two_step_pair_model=dict(distribution_cck=distribution(pair_sums),
                    scope='Counterfactual sum of adjacent complete budget2 APIs after final request, excluding PRIME and contact-crossing step. Not a measured budget4 bound; ownership, IRQ and contention would differ.'),
                nested_original_cck_not_additive=nested,
                scope='Actual bus spans, including IRQ/contention. Final worker/dispatcher clipped at contact hook; counts use entered calls. No instruction CPU-only or unexplained-time scheduler attribution.')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result=dict(schema=1,analysed_reviewed_head='1e25a197fdf329f17d0d302a2c240e0d058bac91',
                rows=[analyse(v) for v in ('PAL','NTSC')])
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(output=str(args.output),standards=[r['standard'] for r in result['rows']])))
