"""Read-only regression reduction and complete endpoint/contact validation.

Consumes retained literal captures. Never launches Copperline or edits product.
"""
import argparse,bisect,gzip,json
from pathlib import Path
from native_tools import ROOT
from native_evidence import ReportRun,digest,inputs_for,snapshot
from physics_comparison import union_span


def load(path):
    with gzip.open(path,'rt') as h:return json.load(h)


def enclosed(calls,outer):
    return [r for r in calls if outer['entry']['cck']<=r['entry']['cck']<=r['exit']['cck']<=outer['exit']['cck']]


def regression(c):
    calls=sorted(c['stack_timing']['calls'],key=lambda r:r['entry']['cck'])
    starts=[r['entry']['cck'] for r in calls];callbacks=c['timing']['callbacks']
    callback_starts=[r['entry']['cck'] for r in callbacks]
    endpoint=next(r for r in c['endpoints'] if r['label']=='aligned-held')
    gesture=endpoint['request']['cck'];marker=endpoint['first_actual_publication']['position']['cck']
    requests=[r for r in calls if r['callee']=='game_preview_request_projected' and gesture<=r['entry']['cck']<=marker]
    indices=[bisect.bisect_right(callback_starts,r['entry']['cck'])-1 for r in requests]
    gaps=[b-a for a,b in zip(indices,indices[1:])]
    final=requests[-1]['entry']['cck'];api=union_span([r for r in calls if r['callee'] in ('game_preview_step','game_preview_endpoint_try')],final,marker)
    classes={};declines=[]
    for owner in (r for r in calls if r['callee']=='tutorial_background'):
        sub=enclosed(calls[bisect.bisect_right(starts,owner['entry']['cck']):bisect.bisect_right(starts,owner['exit']['cck'])],owner)
        names={r['callee'] for r in sub}
        if 'game_preview_step' in names:kind='accepted'
        elif 'tutorial_background_class' not in names:kind='early-reserve-refusal'
        elif 'read_presentation_line' not in names:kind='classifier-refusal'
        elif 'account_sim_timer' not in names:kind='after-beam-refusal'
        else:kind='after-fresh-account-refusal'
        bucket=classes.setdefault(kind,dict(count=0,sum_cck=0,max_cck=0));bucket['count']+=1;bucket['sum_cck']+=owner['elapsed_bus_cck'];bucket['max_cck']=max(bucket['max_cck'],owner['elapsed_bus_cck'])
        if kind!='accepted':declines.append(owner['elapsed_bus_cck'])
    return dict(placement_requests=len(requests),callback_gap_counts={str(v):gaps.count(v) for v in sorted(set(gaps))},gesture_to_final_request_cck=final-gesture,
        final_request_to_copjmp_cck=marker-final,preview_api_cck=api,outside_preview_api_cck=marker-final-api,
        owners=classes,declined_sum_cck=sum(declines),declined_count=len(declines),
        refusal_scope='Observed completed call partition only; no inferred classifier return or branch arithmetic. Different complete run lengths prevent treating total sums as isolated overhead.')


def contact(c,exe):
    from build_match_core import load_image
    from predictor_native_proof import original_reference
    from landing_try_proof import reference
    from deadline_extent import validate_capture
    from deadline_service_reduction import reduce_capture
    image,symbols=load_image(exe);results=[]
    records=bytes.fromhex(c['retained_records']);count=len(records)//14
    for row in c['endpoints']:
        incoming=original_reference(image,symbols,row,records,count,c['history_end'])
        outgoing=None
        if row['human_launches'][0]:
            final,sample,phases,outcome,_=reference(image,symbols,bytes.fromhex(row['held_launch_state']))
            scene=row['first_actual_publication']
            if scene['tutorial_fields']['tutorial_ball_mode']==1:
                assert scene['native_sprite_check']['actual_sample']==sample.hex()
                assert bytes.fromhex(scene['endpoint_points'])[:8]==sample
                assert scene['endpoint_phases']>>16==phases and scene['endpoint_outcomes']>>16==outcome
                assert scene['endpoint_ready']>>8 and scene['endpoint_generation']==row['generation']
            assert row['held_endpoint_point']==sample.hex()
            assert row['held_endpoint_phase']==phases and row['outcomes'][0]==outcome
            assert row['held_terminal_state']==final.hex()
            outgoing=dict(full318_equal=True,point_phase_outcome_equal=True,phases=phases,outcome=outcome,expected_full_state=final.hex(),actual_full_state=row['held_terminal_state'],expected_point=sample.hex(),actual_point=row['held_endpoint_point'])
        results.append(dict(label=row['label'],x=row['x'],y=row['y'],incoming=incoming,outgoing=outgoing))
    deadline=validate_capture(c);assert deadline==c['deadline'];services=reduce_capture(c);assert services['passed']
    calls=c['stack_timing']['calls'];w=[]
    for chunk in deadline['chunks']:
        if chunk['operation']!=8:continue
        sub=enclosed(calls,chunk);roots=[r for r in sub if r['callee']=='game_launch_root']
        launches=[r for r in c['launch_rows'] if chunk['entry']['cck']<=r['position']['cck']<=chunk['exit']['cck']]
        if not roots or not launches:continue
        assert len(roots)==1
        marker=launches[0]['position']['cck'];root=roots[0]
        dispatches=[r for r in sub if r['callee']=='game_preview_dispatch' and r['entry']['cck']<=root['entry']['cck']<=root['exit']['cck']<=marker<=r['exit']['cck']]
        assert len(dispatches)==1;dispatch=dispatches[0]
        hooks=[r for r in sub if r['callee']=='game_history_contact' and r['entry']['cck']<=marker<=r['exit']['cck']]
        assert len(hooks)==1
        samples=[r for r in c['dispatch_samples'] if dispatch['entry']['cck']<=r['position']['cck']<=root['entry']['cck']]
        assert len(samples)==1;sample=samples[0];assert sample['registers']['d'][7]==0,'Only held markers are captured'
        state=bytes.fromhex(sample['private_state']);assert len(state)==318
        def byte(name):return state[symbols[name]-symbols['game_core_state']]
        fields={name:byte(name) for name in ('game_contact','game_flight','game_mode','game_score_initialized','game_score_flags','game_lower_owner','game_upper_owner')}
        fields.update(lower_y=state[2],lower_phase=state[0],upper_y=state[12],upper_phase=state[10])
        assert 98<=fields['lower_y']<=153 and 7<=fields['upper_y']<=62
        assert fields['game_contact']&0x8d==0 and fields['game_flight']&0xc0==0x40
        assert (fields['lower_phase']|fields['upper_phase'])&0xc0==0
        w.append(dict(owner=chunk,root=root,accepted_hook=hooks[0],dispatch=dispatch,launch_marker=launches[0],dispatch_sample=sample,guard_fields=fields,
            irq_scope='Wall elapsed encloses nested IRQ work; pre-BSR store and post-RTS read/IRQ entry-RTE tails remain unresolved.',held_only=True))
    diagnostics=[]
    callbacks=c['timing']['callbacks']
    for marker in c['launch_rows']:
        at=marker['position']['cck']
        cbindex=next((i for i,r in enumerate(callbacks) if r['entry']['cck']<=at<=r['completion']['cck']),None)
        if cbindex is None:continue
        assert cbindex>0
        before,cb=callbacks[cbindex-1],callbacks[cbindex]
        owners=[r for r in calls if r['callee']=='tutorial_background' and before['completion']['cck']<=r['entry']['cck']<=r['exit']['cck']<=cb['entry']['cck']]
        diagnostics.append(dict(launch_cck=at,nominal_callback=cb['callback'],preceding_callback_work_cck=before['work_cck'],
            preceding_absolute_headroom_cck=before['absolute_headroom_cck'],observed_gap_to_contact_callback_cck=cb['entry']['cck']-before['completion']['cck'],
            whole_owner_plus_service_reserve_cck=25000,preceding_owner_count=len(owners),
            preceding_callback_completion_vpos=before['completion']['vpos'],contact_callback_entry_vpos=cb['entry']['vpos'],
            owners=[dict(entry=o['entry'],exit=o['exit'],elapsed_bus_cck=o['elapsed_bus_cck'],
                operation=next((r['operation'] for r in deadline['chunks'] if r['entry']['cck']==o['entry']['cck']),None),
                completed_child_calls=[r['callee'] for r in enclosed(calls,o) if r['callee'] in ('tutorial_background_class','read_presentation_line','account_sim_timer','game_preview_step')]) for o in owners],
            last_owners=[{k:r[k] for k in ('entry','exit','elapsed_bus_cck')} for r in owners[-4:]]))
    return dict(endpoint_rows=results,contact_owner_witnesses=w,contact_coverage=bool(w),nominal_contact_diagnostics=diagnostics,
        maximum_contact_owner_cck=max((r['owner']['whole_owner_cck'] for r in w),default=None),deadline=deadline,
        services={k:v for k,v in services.items() if k!='spans'},normative_deadline_safety=False)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--contact-region',choices=('pal','ntsc'));args=parser.parse_args()
    directory=ROOT/'build/tests'/('physics-contact-validation-'+args.contact_region if args.contact_region else 'physics-regression-analysis')
    directory.mkdir(parents=True,exist_ok=True);output=directory/'report.json'
    paths,tools=inputs_for('build','scripts/physics_followup_analysis.py');consumed=set()
    if args.contact_region:
        from match_core_cpu import cpu_tool_inputs
        cpu_paths,tools['machine68k']=cpu_tool_inputs();paths|=set(cpu_paths)
    if args.contact_region:
        source=ROOT/('build/tests/physics-contact-native-'+args.contact_region);consumed|={source/'report.json',source/'latency.json.gz'}
        exe=ROOT/'build/amiga/interfaces/enhanced/baseline-rally';manifest=Path(str(exe)+'.compile.json');consumed|={exe,manifest}
    else:
        consumed|={ROOT/('build/tests/'+prefix+region+'/'+name) for prefix in ('physics-native-','physics-control-native-') for region in ('pal','ntsc') for name in ('report.json','latency.json.gz')}
    t=ReportRun([output],'offline-native-reduction','maintained-native','Captured endpoints and owner/control interval reduction')
    t.meta.update(files=snapshot(paths|consumed),tools=tools,runner='scripts/physics_followup_analysis.py')
    try:
        if args.contact_region:
            receipt=json.loads((source/'report.json').read_text());assert receipt['evidence']['state']=='complete'
            assert receipt['executable_sha256']==digest(exe)==json.loads(manifest.read_text())['executable_sha256']
            result=contact(load(source/'latency.json.gz'),exe)
            result.update(physical_receipt_passed=receipt['passed'],physical_run_id=receipt['evidence']['run_id'],executable_sha256=digest(exe))
        else:
            result={region:{kind:regression(load(ROOT/('build/tests/'+prefix+region+'/latency.json.gz'))) for kind,prefix in (('control','physics-control-native-'),('candidate','physics-native-'))} for region in ('pal','ntsc')}
        t.finalize(output,dict(passed=True,execution='offline-retained-capture-validation',results=result,normative_deadline_safety=False))
        print(json.dumps(dict(report=str(output),sha256=digest(output))),flush=True)
    except BaseException as e:t.abort(e);raise


if __name__=='__main__':main()
