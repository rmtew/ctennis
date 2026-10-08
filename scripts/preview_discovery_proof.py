"""A2 finite inputs discover endpoints from actual 68000 outputs, never rules."""
import hashlib
import json
from build_match_core import load_image
from history_proof import attempts, cursor, seek
from match_core_cpu import Core
from preview_extended_proof import candidates, continuous, execute, table, value
from preview_proof import fixture, geometry
from run_shared_match_core import READONLY

SEEDS=(0xace1,0x0001,0x1234,0xbeef)
REQUIRED=('net','out','interception','coincidence')
INPUT_POLICY=dict(select_mode=0,entropy_policy=0,
    cycle=['game_round_poll','game_core_sample_pads','game_core_sample_result','game_tick_dispatch'],
    release_modulus=64,release_prefix=8,direction_modulus=96,first_direction_ticks=48,
    direction_first=8,direction_second=4,opponent_packet=0,result_words=[0]*6)


def stream_hash(stream):
    return hashlib.sha256(json.dumps(stream,separators=(',',':')).encode()).hexdigest()


def qualification(observation,symbols):
    """Derive coverage from actual full state/hook order and drawn geometry.

    Preview status/outcome enums are diagnostics. The independent order is
    interception, net, out, then landing. Incoming coincidence cannot qualify.
    """
    result=observation['result'];end=observation['end'];rows=[];coverage=set()
    for variant in (0,1):
        accepted=observation['launches'][variant]
        human=next((i for i,event in enumerate(accepted) if event['end']==end),None)
        opponent=next((i for i,event in enumerate(accepted)
            if human is not None and i>human and event['end']!=end and event['kind']==1),None)
        state=result['contexts'][variant]
        contact=value(state,symbols,'game_contact');flight=value(state,symbols,'game_flight')
        lifecycle=value(state,symbols,'game_lifecycle',2)
        classification='unqualified'
        if human is not None:
            if opponent is not None:classification='interception'
            elif contact&1:classification='net'
            elif contact&0x88:classification='out'
            elif contact&2:classification='landing'
        elif contact&0x8d:classification='no-contact'
        if classification in REQUIRED:coverage.add(classification)
        count=len(result['paths'][variant])//8
        # Require a complete sample strictly later than the launch boundary.
        outgoing=(human is not None and count>result['prefix']+accepted[human]['dispatch']+1)
        rows.append(dict(variant=variant,has_human_launch=human is not None,
            human_launch_order=human,human_launch=accepted[human] if human is not None else None,
            opponent_contact_order=opponent,opponent_contact=accepted[opponent] if opponent is not None else None,
            contact=contact,flight=flight,lifecycle=lifecycle,classification=classification,
            preview_outcome=result['outcomes'][variant],samples=count,outgoing_samples_present=outgoing,
            final_state_sha256=hashlib.sha256(state).hexdigest(),
            last_sampled_boundary=observation['boundaries'][variant][-1]))
    paths=[[path[n:n+8] for n in range(0,len(path),8)] for path in result['paths']]
    coincident=bool(paths[0] and paths[1] and geometry(paths[0])==geometry(paths[1]))
    launched_coincidence=coincident and all(row['outgoing_samples_present'] for row in rows)
    if launched_coincidence:coverage.add('coincidence')
    return dict(variants=rows,geometry_coincident=coincident,
        launched_outgoing_coincidence=launched_coincidence,coverage=sorted(coverage),
        classifier_priority=['interception','net','out','landing'],
        source='actual-full-canonical-and-accepted-hooks',geometry_source='actual-sampled-drawn-geometry-visibility-ticks')


def discovery(executable,progress):
    image,symbols=load_image(executable)
    observations=[];seeds=[];jobs=[];qualified=set()
    for seed in SEEDS:
        if set(REQUIRED)<=qualified:
            seeds.append(dict(seed=seed,recorded=False,dispatches=0,operations=0,
                candidates=[],skipped='coverage complete'));continue
        with Core(image,symbols,readonly=READONLY) as cpu:
            stream,states,_,launches=fixture(cpu,seed=seed,dispatches=512)
            assert len(stream)==2049 and cursor(cpu,'game_history_oldest')==0
            index=attempts(cpu);eligible=candidates(index,launches)
            completed_returns=[event for event in launches if event['human'] and event['kind']==1]
            assert all((event['episode_origin'],1,event['end']) in index for event in completed_returns), 'Ordinary bounded recording loses a completed return identity'
            assert [event['origin'] for event in eligible]==[event['origin'] for event in completed_returns[:2]], 'Discovery substitutes a later return for the first completed candidate'
            # All first available completed returns are retained: ordinary
            # recording is below capacity, with no later replacement search.
            identities=[]
            for candidate in eligible:
                incoming=next(event for event in launches if event['origin']==candidate['incoming_origin'])
                probe=candidate['probe_origin'];action=candidate['origin']
                assert (probe,1,candidate['end'])==index[candidate['ordinal']]
                assert incoming['end']!=candidate['end'] and 0<=incoming['origin']<probe<=action<len(stream)
                identities.append(dict(ordinal=candidate['ordinal'],completed_kind=1,end=candidate['end'],
                    incoming_origin=incoming['origin'],incoming_kind=incoming['kind'],incoming_end=incoming['end'],
                    probe_origin=probe,action_boundary=action,recorded_x=candidate['x'],recorded_y=candidate['y'],
                    full_incoming_retained=True,selected_lifecycle=value(states[action],symbols,'game_lifecycle',2)))
            seeds.append(dict(seed=seed,recorded=True,dispatches=512,operations=len(stream),
                oldest=0,latest=cursor(cpu),input_stream_sha256=stream_hash(stream),candidates=identities,
                recorded_completed_returns=len(completed_returns),
                unavailable=None if len(eligible)==2 else f'Only {len(eligible)} completed returns with retained incoming context within512dispatches; no later search'))
            progress(dict(stage='stage-a2-recorded-seed',seed=seeds[-1]))
            cpu.call('game_history_freeze')
            for candidate,identity in zip(eligible,identities):
                selection=candidate['origin'];seek(cpu,selection);bounds=table(cpu,candidate['end'])
                xs=sorted({max(bounds['left'],min(bounds['right']-1,candidate['x']+delta)) for delta in (-8,0,8)})
                ys=sorted({max(bounds['top'],min(bounds['bottom']-1,candidate['y']+delta)) for delta in (-8,0,8)})
                assert len(xs)<=3 and len(ys)<=3
                for x in xs:
                    for y in ys:
                        assert len(jobs)<72, 'A2 reaches72jobs; no automatic cap expansion'
                        observation=execute(cpu,candidate['ordinal'],selection,x,y,stream,seed,f'discovery-{seed:04x}-{len(jobs)}')
                        facts=qualification(observation,symbols)
                        assert bounds['left']<=x<bounds['right'] and bounds['top']<=y<bounds['bottom']
                        row=dict(name=observation['name'],seed=seed,ordinal=candidate['ordinal'],
                            candidate=identity,x=x,y=y,bounds=bounds,selection=selection,
                            qualification=facts,costs=observation['costs'])
                        jobs.append(row)
                        new=set(facts['coverage'])-qualified
                        if new:
                            observations.append((observation,facts,sorted(new)))
                            qualified.update(new)
                        progress(dict(stage='stage-a2-job',job=row,total_jobs=len(jobs),
                            actual_coverage=sorted(qualified),absent_classes=sorted(set(REQUIRED)-qualified)))
                        if set(REQUIRED)<=qualified:break
                    if set(REQUIRED)<=qualified:break
                if set(REQUIRED)<=qualified:break
            cpu.audit_reads()
    chosen=[]
    for observation,facts,new in observations:
        report=continuous(image,symbols,observation)
        report.update(qualification=facts,coverage_contributed=new)
        chosen.append(report)
        progress(dict(stage='stage-a2-chosen-continuous',case=report))
    report=dict(passed=set(REQUIRED)<=qualified,planned_seeds=list(SEEDS),input_policy=INPUT_POLICY,
        dispatch_cap=512,ordinary_operation_cap=2049,returns_per_seed_cap=2,positions_per_return_cap=9,
        position_policy='recorded-contact-plus-minus8-clamped-to-actual-phase-limits',job_cap=72,
        jobs=len(jobs),seeds=seeds,job_results=jobs,required_coverage=list(REQUIRED),
        actual_coverage=sorted(qualified),absent_classes=sorted(set(REQUIRED)-qualified),chosen_cases=chosen,
        scope='A2 bounded actual CPU discovery and chosen uninterrupted continuations; A3/native/resources/UI pending.')
    progress(dict(stage='stage-a2-complete',result=report))
    assert report['passed'], 'Bounded A2 discovery lacks actual '+', '.join(report['absent_classes'])+'; no automatic seed/dispatch/job expansion'
    assert jobs and chosen
    return report
