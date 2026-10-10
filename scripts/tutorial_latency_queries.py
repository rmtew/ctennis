"""Six read-only fresh-D queries against custody-bound PR47 captures.

No guest execution. Sequential region loads; no writes to original evidence.
"""
import gzip,json,hashlib,pathlib,sys
root=pathlib.Path(__file__).resolve().parents[1]
def scrub(v):
 if isinstance(v,dict):return {k:scrub(x) for k,x in v.items() if k not in ('child_spans','reads','loaded_hunks','retained_records','workspace')}
 if isinstance(v,list):return [scrub(x) for x in v]
 if isinstance(v,str) and len(v)>128:return dict(omitted_bytes=len(v)//2,sha256=hashlib.sha256(bytes.fromhex(v)).hexdigest())
 return v
def at(v):
 if not isinstance(v,dict):return None
 for k in ('position','entry','request'):
  if isinstance(v.get(k),dict) and 'cck' in v[k]:return v[k]['cck']
 return v.get('cck')

from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
import argparse
import tutorial_latency_accounting as prior

INSTRUCTION_COMMIT='866999df0037879dce4a935020cb5f61c5acde87'
SUPPORT={'preview_envelopes_state_support','scheduler_owner_other',
         'scheduler_classification','remaining_mandatory_callback'}

def project(region):
    verified=[];missing=[];mismatched=[]
    for name,expected in region['original_351_file_bindings'].items():
        p=pathlib.Path(name) if name.startswith('/') else root/name
        if not p.exists():missing.append(name)
        elif prior.digest(p)==expected:verified.append(name)
        else:mismatched.append(name)
    for f in region['files']:
        assert prior.digest(root/f['relative_path'])==f['sha256'], f['relative_path']
    p=root/next(f['relative_path'] for f in region['files'] if f['relative_path'].endswith('latency.json.gz'))
    with gzip.open(p,'rt') as f:c=json.load(f)
    e=next(e for e in c['endpoints'] if e['label']=='fresh-D-edit')
    lo=e['request']['cck'];hi=e['first_actual_publication']['position']['cck']
    result=dict(provenance=region,endpoint=scrub(e),window=[lo,hi],
        custody_check=dict(available_match_count=len(verified),missing=missing,mismatched=mismatched,
                          retained_five_files_hash_verified=True),
        initial_admission_state=c['initial_admission_state'],lists={},call_map=c['call_map'])
    for k,v in c.items():
        if isinstance(v,list):
            rows=[x for x in v if at(x) is not None and lo-150000<=at(x)<=hi+150000]
            if rows:result['lists'][k]=scrub(rows)
    result['calls']=[dict(index=i,**scrub(x)) for i,x in enumerate(c['stack_timing']['calls'])
                     if x['entry']['cck']<hi+150000 and x['exit']['cck']>lo-150000]
    result['callbacks']=scrub([x for x in c['timing']['callbacks']
        if x['entry']['cck']<hi+150000 and x['completion']['cck']>lo-150000])
    result['chunks']=scrub([x for x in c['deadline']['chunks']
        if x['entry']['cck']<hi+150000 and x['exit']['cck']>lo-150000])
    return result


def primary_segments(calls,lo,hi):
    """Sweep all emitted calls; exclusive primary category and deepest identity."""
    rows={r['index']:r for r in calls};events=defaultdict(list)
    events[lo];events[hi]
    for r in calls:
        a,b=max(lo,r['entry']['cck']),min(hi,r['exit']['cck'])
        if a<b:events[a].append((r['index'],True));events[b].append((r['index'],False))
    active=set();previous=lo;out=[]
    for pos in sorted(events):
        if pos>previous:
            candidates=[]
            for i in active:
                r=rows[i]
                for j,cat in enumerate(prior.CATEGORIES[:-1]):
                    if r['callee'] in prior.NAMES[cat]:
                        if cat=='actual_outgoing_ball' and r.get('caller') not in ('game_preview_continue_one','game_preview_flight_one'):continue
                        candidates.append(j);break
            category=prior.CATEGORIES[min(candidates)] if candidates else 'unclassified'
            deepest=max(active,key=lambda i:(rows[i]['depth'],rows[i]['entry']['cck'])) if active else None
            owner=next((i for i in active if rows[i]['callee']=='tutorial_background'),None)
            account=next((i for i in active if rows[i]['callee']=='account_sim_timer'),None)
            # Preserve existing service-mask priority across IRQ nesting.
            service=next((name for name in ('poll_presentation','game_poll_keyboard','account_sim_timer')
                          if any(rows[i]['callee']==name for i in active)),None)
            out.append((previous,pos,category,deepest,owner,account,service))
        for i,enter in events[pos]:
            if enter:active.add(i)
            else:active.remove(i)
        previous=pos
    assert sum(b-a for a,b,*_ in out)==hi-lo
    return out


def next_snapshot(lists,pos):
    return next((r for r in lists.get('boundaries',[]) if r['position']['cck']>=pos),None)


def fields_subset(fields):
    wanted={'simulation_phase','simulation_interval','last_timer_count','display_ready','ready_completed',
      'ready_copper','ready_generation','tutorial_generation','game_preview_generation','tutorial_active_variant'}
    return {k:v for k,v in fields.items() if k in wanted or k.startswith('tutorial_placement')
            or k.startswith('tutorial_presentation') or k.startswith('tutorial_animation') or k.startswith('tutorial_footer')}


def observed_signature_repeats(epoch_rows):
    """Repeated plan telemetry is not complete unchanged admission state."""
    counts=Counter();seen=set()
    for epoch in epoch_rows:
        seen.clear()
        for row in epoch['owners']:
            if row['accepted']:
                seen.clear();continue
            fields=row['final_job_fields']
            signature=(row['next_entry_generation'],row['next_entry_preview_generation'],
              row['route_witness'],tuple(fields.get(k) for k in
                ('tutorial_job_kind','tutorial_job_variant','tutorial_job_budget','tutorial_job_cost')))
            if signature in seen:counts[row['classification']]+=1
            seen.add(signature)
    return dict(counts)


def reduce(s):
    lo,hi=s['window'];calls=s['calls'];byid={r['index']:r for r in calls};lists=s['lists']
    chunks={r['owner_call_index']:r for r in s['chunks']};generation=s['endpoint']['generation']
    owners=[r for r in calls if r['callee']=='tutorial_background' and r['entry']['cck']<hi and r['exit']['cck']>lo]
    contact=[]
    for o in owners:
        chunk=chunks.get(o['index'])
        if chunk and chunk['telemetry']['tutorial_job_variant']==0 and any(
          o['entry']['cck']<=x['position']['cck']<=o['exit']['cck'] for x in lists.get('launch_rows',[])):
            contact.append(o)
    contact_owner=min(contact,key=lambda r:r['entry']['cck']) if contact else None
    contact_cck=contact_owner['entry']['cck'] if contact_owner else None
    profiles=[r for r in lists.get('endpoint_profiles',[]) if r['generation']==generation and
              r['variant']==0 and r['after']['ready'] and lo<=r['exit']['cck']<=hi]
    known=min(r['exit']['cck'] for r in profiles)
    segs=primary_segments(calls,lo,hi)
    phases=[('input_to_contact_owner',lo,contact_cck),('contact_owner_to_known',contact_cck,known),
            ('known_to_copjmp',known,hi)] if contact_cck else [('contact_unknown',lo,known),('known_to_copjmp',known,hi)]
    phase_rows=[]
    request_calls=[r for r in calls if r['callee']=='game_preview_request_projected' and lo<=r['entry']['cck']<=hi]
    accepted_api_return=request_calls[0]['exit']['cck'] if len(request_calls)==1 else None
    for label,a,b in phases:
        counts=defaultdict(Counter);generation_counts=defaultdict(Counter)
        for x,y,cat,deep,o,*_ in segs:
            cost=max(0,min(b,y)-max(a,x))
            if cost:
                role='accepted_owner' if o in chunks else 'declined_owner' if o is not None else 'outside_owner'
                counts[role][cat]+=cost
                snap=next_snapshot(lists,byid[o]['exit']['cck']) if o is not None else None
                gen=snap['fields'].get('game_preview_generation') if snap else None
                fence='accepted_generation_source_fenced' if o is not None and accepted_api_return is not None and byid[o]['entry']['cck']>=accepted_api_return and gen==generation else 'previous_generation_next_entry_witness' if gen is not None and gen!=generation else 'generation_unknown_or_outside_owner'
                generation_counts[fence+':'+role][cat]+=cost
        phase_rows.append(dict(label=label,start_cck=a,end_cck=b,total_cck=b-a,
                               category_by_ownership_cck={k:dict(v) for k,v in counts.items()},category_by_generation_and_ownership_cck={k:dict(v) for k,v in generation_counts.items()}))
        assert sum(sum(v.values()) for v in counts.values())==b-a
    decomposition={}
    for cat in SUPPORT:
        durations=Counter();ids=defaultdict(set)
        for a,b,c,deep,*_ in segs:
            if c!=cat:continue
            routine=byid[deep]['callee'] if deep is not None else 'unclassified_gap'
            durations[routine]+=b-a;ids[routine].add(deep)
        decomposition[cat]=[dict(routine=n,disjoint_cck=v,observed_calls_with_assigned_span=len(ids[n]))
                            for n,v in durations.most_common()]
    callbacks=sorted(s['callbacks'],key=lambda r:r['entry']['cck'])
    epochs=defaultdict(list)
    nojob=Counter();eligibility=[]
    for o in sorted(owners,key=lambda r:r['entry']['cck']):
        a,b=o['entry']['cck'],o['exit']['cck'];chunk=chunks.get(o['index'])
        nested=[r for r in calls if r['index']!=o['index'] and a<=r['entry']['cck']<=r['exit']['cck']<=b]
        writes=[r for r in lists.get('scheduler_job_writes',[]) if a<=r['position']['cck']<=b]
        last={r['field']:r['value'] for r in writes}
        variants=[r['value'] for r in writes if r['field']=='tutorial_job_variant']
        snapshot=next_snapshot(lists,b);observed=snapshot['fields'] if snapshot else {}
        cb=next((r for r in reversed(callbacks) if r['completion']['cck']<=a),None)
        cls=[r for r in nested if r['callee']=='tutorial_background_class'];adm=[r for r in nested if r['callee']=='tutorial_job_admitted']
        route='selected_primary_witness' if variants==[observed.get('tutorial_active_variant')] else 'other_branch_toggle_witness' if len(variants)==2 else 'multiple_variant_writes_fallback_possible' if len(variants)>2 else 'unknown'
        reason='executed_job' if chunk else 'zero_budget_without_admission' if cls and not adm and last.get('tutorial_job_budget')==0 else 'admission_return_without_job' if adm else 'early_guard_or_route_unknown'
        if not chunk:nojob[reason]+=1
        progress=[{k:v for k,v in r.items() if k not in ('held_state','released_state','history','active')}
                  for r in lists.get('branch_boundaries',[]) if a<=r['position']['cck']<=b]
        queries=[dict(api=r['api'],generation=r['generation'],variant=r['variant'],entry_cck=r['entry']['cck'],exit_cck=r['exit']['cck'],
            before={k:r['before'].get(k) for k in ('stage','cursor','ready','attempted')},
            after={k:r['after'].get(k) for k in ('stage','cursor','ready','attempted')})
            for r in lists.get('endpoint_profiles',[]) if a<=r['entry']['cck']<=r['exit']['cck']<=b]
        row=dict(start_cck=a,end_cck=b,owner_wall_cck=b-a,accepted=bool(chunk),route_witness=route,
            next_entry_generation=observed.get('tutorial_generation'),next_entry_preview_generation=observed.get('game_preview_generation'),
            next_entry_snapshot_cck=snapshot['position']['cck'] if snapshot else None,
            class_calls=len(cls),class_union_cck=prior.union_duration(a,b,[(r['entry']['cck'],r['exit']['cck']) for r in cls]),
            admission_calls=len(adm),admission_union_cck=prior.union_duration(a,b,[(r['entry']['cck'],r['exit']['cck']) for r in adm]),
            classification=reason,exact_refusal_predicate=None,final_job_fields=last,variant_store_sequence=variants,
            chunk=chunk,branch_progress=progress,endpoint_progress=queries,spent_count=None,flight_phase=None,
            observed_admission_timer_reads=[dict(cck=r['position']['cck'],timer_parameters=r['timer_parameters'])
                for r in lists.get('timer_reads',[]) if any(x['entry']['cck']<=r['position']['cck']<=x['exit']['cck'] for x in adm)][:1],
            beam_entry=o['entry'],blank_latch_at_guard=None,launch_saved_at_guard=None)
        epochs[cb['callback'] if cb else 'unknown'].append(row)
        for call in nested:
            if call['callee']=='game_preview_endpoint_pending' and (contact_cck is None or call['entry']['cck']<contact_cck):
                eligibility.append(dict(entry_cck=call['entry']['cck'],exit_cck=call['exit']['cck'],
                    caller=call.get('caller'),next_entry_generation=observed.get('tutorial_generation'),
                    next_entry_preview_generation=observed.get('game_preview_generation'),
                    snapshot_cck=row['next_entry_snapshot_cck'],launch_saved=None,exact_generation_at_entry=None,
                    nested_selection_calls=sum(r['callee']=='game_preview_selection_valid' and
                     call['entry']['cck']<=r['entry']['cck']<=r['exit']['cck']<=call['exit']['cck'] for r in nested)))
    epoch_rows=[]
    for cbid,rows in epochs.items():
        cb=next((x for x in callbacks if x['callback']==cbid),None)
        first_phase=next((r for r in lists.get('admission_writes',[]) if cb and r['field']=='simulation_phase' and
                          cb['completion']['cck']<=r['position']['cck']<=rows[0]['start_cck']),None)
        epoch_rows.append(dict(callback=cbid,entry_snapshot=fields_subset(cb['state']) if cb else None,
              completion_cck=cb['completion']['cck'] if cb else None,
              first_observed_post_callback_phase_write=first_phase,
              exact_completion_slack_e=None,owners=rows))
    timer_ids=sorted({r['entry_pc'] for r in calls if r['callee']=='account_sim_timer' and r['entry']['cck']<hi and r['exit']['cck']>lo})
    main_ids=sorted({r['entry_pc'] for r in calls if r['callee']=='account_sim_timer' and r.get('depth')==0})
    timers=[]
    for pc in timer_ids:
        group=[r for r in calls if r['callee']=='account_sim_timer' and r['entry_pc']==pc and r['entry']['cck']<hi and r['exit']['cck']>lo]
        masks={r['index'] for r in group};cost=sum(b-a for a,b,cat,_,_,acc,service in segs if cat=='hardware_service' and acc in masks and service=='account_sim_timer')
        label='first_main_loop' if pc==main_ids[0] else 'second_main_loop' if len(main_ids)>1 and pc==main_ids[1] else 'admission' if all(r.get('caller')=='tutorial_job_admitted' for r in group) else 'other'
        retry=0;reads=0
        for r in group:
            rr=[x for x in lists.get('timer_reads',[]) if r['entry']['cck']<=x['position']['cck']<=r['exit']['cck']]
            reads+=len(rr)
            if rr:
                first=rr[0];retry+=max(0,sum(x['pc']==first['pc'] and x['addr']==first['addr'] for x in rr)-1)
        timers.append(dict(entry_pc=pc,role=label,calls=len(group),primary_mask_disjoint_cck=cost,
                           observed_timer_byte_reads=reads,repeated_first_read_retry_witnesses=retry))
    suffix_calls=[dict(callee=r['callee'],entry_cck=r['entry']['cck'],exit_cck=r['exit']['cck'],entry_beam=r['entry'],exit_beam=r['exit'])
                  for r in calls if r['entry']['cck']<hi and r['exit']['cck']>known and r['callee'] in
                  ('tutorial_progress_slice','tutorial_render','tutorial_animate','complete_scene','poll_presentation')]
    return dict(standard=s['provenance']['standard'],custody=s['custody_check'],
        provenance={k:s['provenance'][k] for k in ('run_id','source_commit','native_sha256','files')},
        accepted_generation=generation,generation_fence=dict(
          request_api_calls=[dict(entry_cck=r['entry']['cck'],exit_cck=r['exit']['cck']) for r in calls if r['callee']=='game_preview_request_projected' and lo<=r['entry']['cck']<=hi],
          boundary_samples=[dict(cck=r['position']['cck'],tutorial_generation=r['fields']['tutorial_generation'],preview_generation=r['fields']['game_preview_generation'])
              for r in lists.get('boundaries',[]) if lo<=r['position']['cck']<=hi],
          actual_generation_store_positions=None,exact_acceptance_tick=None,accepted_request_return_upper_bound_cck=accepted_api_return,source_fence_basis='Sole request API returns before owner, next callback-entry preview generation agrees, and root optional jobs do not change generations. Inferred stability, not a sampled generation store.'),
        milestones=dict(input_cck=lo,contact_owner_entry_cck=contact_cck,contact_owner_exit_cck=contact_owner['exit']['cck'] if contact_owner else None,
          endpoint_ready_return_upper_bound_cck=known,qualified_copjmp_cck=hi),
        q1=phase_rows,q2=decomposition,q3_callback_epochs=epoch_rows,
        q4=dict(declined_counts=dict(nojob),repeated_observed_plan_signature_no_optional_job=observed_signature_repeats(epoch_rows),repeat_scope='Same callback and observed next-entry generations/route/final telemetry; any optional job clears repeats. Does not establish unchanged guard/private/presentation state.',pre_contact_eligibility=eligibility,
            unchanged_complete_guard_state_proven=None,refusal_reasons=None,
            missing=['launch_saved stores/snapshots','complete classifier inputs','guard-time blank latch','guard branch PC outcomes','exact generation stores']),
        q5_timer_callsites=timers,q6=dict(ready_profiles=profiles,producer_and_presenter_calls=suffix_calls,
            publications=[r for r in lists.get('publications',[]) if known<=r['position']['cck']<=hi],
            callback_snapshot_transitions=[dict(cck=r['entry']['cck'],fields=fields_subset(r['state'])) for r in callbacks if known<=r['entry']['cck']<=hi],
            exact_dirty_transition=None,exact_latch_rearm=None,first_scanout=None))


def main():
    p=argparse.ArgumentParser(__doc__)
    p.add_argument('--output',type=pathlib.Path,default=root/'docs/evidence/tutorial-latency/fresh-d-queries.json')
    args=p.parse_args();m=json.loads((root/'docs/evidence/tutorial-latency/custody-manifest.json').read_text())
    out=dict(schema=1,instruction_commit=INSTRUCTION_COMMIT,reducer_sha256=prior.digest(__file__),
        custody_manifest_sha256=prior.digest(root/'docs/evidence/tutorial-latency/custody-manifest.json'),
        scope='Read-only retained traces, PAL then NTSC fresh-D only. IRQ-inclusive wall ownership, not CPU savings. Null values are unknown. No new native execution.',regions=[])
    for region in m['regions']:
        s=project(region)
        reduced=reduce(s)
        frozen=json.loads((root/'docs/evidence/tutorial-latency/accounting.json').read_text())
        expected=next(t for r in frozen['regions'] if r['standard']==region['standard'] for t in r['trials'] if t['label']=='fresh-D-edit')
        actual=Counter()
        for phase in reduced['q1']:
            for amounts in phase['category_by_ownership_cck'].values():actual.update(amounts)
        assert all(actual[k]==v for k,v in expected['partition_cck'].items())
        assert all(sum(x['disjoint_cck'] for x in reduced['q2'][k])==actual[k] for k in SUPPORT)
        out['regions'].append(reduced);del s
        print(region['standard']+' fresh-D reduction complete',flush=True)
    args.output.write_text(json.dumps(out,separators=(',',':'),sort_keys=True)+'\n')
    print(str(args.output)+': '+prior.digest(args.output),flush=True)

if __name__=='__main__':main()
