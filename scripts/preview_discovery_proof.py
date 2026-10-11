"""A2 finite inputs discover endpoints from actual 68000 outputs, never rules."""
import hashlib
import json
from build_match_core import load_image
from history_proof import attempts, cursor, field, seek
from match_core_cpu import Core
from preview_extended_proof import candidates, continuous, execute, table, value, continuation_fingerprint, validate_edited_source
from preview_proof import fixture, geometry, CAPACITY
from run_shared_match_core import READONLY
from native_tools import ROOT

SEEDS=(0xace1,0x0001,0x1234,0xbeef)
REQUIRED=('net','out','coincidence')
INPUT_POLICY=dict(select_mode=0,entropy_policy=0,
    cycle=['game_round_poll','game_core_sample_pads','game_core_sample_result','game_tick_dispatch'],
    release_modulus=64,release_prefix=8,direction_modulus=96,first_direction_ticks=48,
    direction_first=8,direction_second=4,opponent_packet=0,result_words=[0]*6)
TIME_POLICY='first-regular-height8-28-first-low-height0-7-last-legal-incoming-pre-dispatch'
POSITION_POLICY='actual-recorded-court-contact-center-plus-minus16-lateral-selected-phase-limits'
GEOMETRY_FIELDS=('game_court_x','game_court_y','game_ball_x','game_ball_y','game_contact')


def contact_contract():
    """Bind fixture offsets to the actual contact instructions, not ball rules."""
    source=(ROOT/'amiga/game/gameplay_contact.s').read_text()
    for instruction in ('addi.w  #$081b,d5','addq.w  #8,d5','cmpi.w  #4,d0',
                        'cmpi.w  #17,d0','cmpi.w  #29,d2','cmpi.w  #8,d2'):
        assert instruction in source, 'Actual contact fixture contract changed: '+instruction
    tick=(ROOT/'amiga/game/gameplay.s').read_text()
    assert tick.index('bsr     game_player_tick')<tick.index('bsr     game_ball_tick')
    return dict(source='amiga/game/gameplay_contact.s',source_sha256=hashlib.sha256(source.encode()).hexdigest(),
        tick_source='amiga/game/gameplay.s',tick_source_sha256=hashlib.sha256(tick.encode()).hexdigest(),
        x_offset=8,lower_y_offset=27,upper_y_offset=35,
        players_before_ball=True,lateral_offsets=[-16,0,16])


def sampling_rows(cpu,candidate,stream,states):
    """Select bounded input times from complete, already recorded core states."""
    end=candidate['end'];possible=[];previous=None
    for selection,(operation,_) in enumerate(stream):
        if operation!='game_tick_dispatch':continue
        if previous is not None and candidate['incoming_origin']<previous<=selection<=candidate['origin']:
            source=states[previous];selected=states[selection]
            geometry={name:value(source,cpu.symbols,name) for name in GEOMETRY_FIELDS}
            assert all(value(selected,cpu.symbols,name)==number for name,number in geometry.items()), 'Poll/pads/result changes recorded contact geometry'
            player=cpu.symbols['game_play_state']-cpu.symbols['game_core_state']+end*10
            phase=(selected[player+1]>>3)&12
            address=cpu.symbols['game_lower_limits' if end==0 else 'game_upper_limits']+phase
            bottom,top,right,left=bytes(cpu.mem.r_block(address,4))
            bounds=dict(left=left,right=right,top=top,bottom=bottom,phase_offset=phase)
            x=geometry['game_court_x']-8;y=geometry['game_court_y']-(27 if end==0 else 35)
            height=geometry['game_court_y']-geometry['game_ball_y']
            if (left<=x<right and top<=y<bottom and 0<=height<29
                    and not geometry['game_contact']&0x0d
                    and bool(geometry['game_contact']&0x40)==(end==0)
                    and selected[player]&0xec==0 and selected[player]&0x12):
                possible.append(dict(source_complete_boundary=previous,selection=selection,
                    court_x=geometry['game_court_x'],court_y=geometry['game_court_y'],
                    ball_x=geometry['game_ball_x'],ball_y=geometry['game_ball_y'],
                    contact=geometry['game_contact'],height=height,player_phase=selected[player],
                    player_animation=selected[player+1],center_x=x,center_y=y,bounds=bounds,
                    source_geometry_equal_at_selection=True))
        previous=selection+1
    choices=(('regular',next((row for row in possible if 8<=row['height']<=28),None)),
             ('low',next((row for row in possible if 0<=row['height']<=7),None)),
             ('late',possible[-1] if possible else None))
    rows=[];seen=set()
    for band,row in choices:
        if row is None:
            rows.append(dict(band=band,available=False,reason='No legal recorded incoming contact center in band before original action'));continue
        if row['selection'] in seen:
            rows.append(dict(band=band,available=False,reason='Duplicate selected time',duplicate_selection=row['selection']));continue
        seen.add(row['selection'])
        xs=sorted({max(row['bounds']['left'],min(row['bounds']['right']-1,row['center_x']+delta)) for delta in (-16,0,16)})
        rows.append(dict(row,band=band,available=True,x_positions=xs,
            clamped_lateral_offsets=[delta for delta in (-16,0,16)
                if not row['bounds']['left']<=row['center_x']+delta<row['bounds']['right']]))
    return rows


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
        human=next((i for i,event in enumerate(accepted) if event['end']==end and event['kind']==1),None)
        opponent=next((i for i,event in enumerate(accepted)
            if human is not None and i>human and event['end']!=end and event['kind']==1),None)
        assert opponent is None, 'Geometric outgoing flight executes a future opponent contact'
        state=result['contexts'][variant]
        contact=value(state,symbols,'game_contact');flight=value(state,symbols,'game_flight')
        lifecycle=value(state,symbols,'game_lifecycle',2)
        first_terminal=None
        first_classification=None
        for dispatch,boundary in enumerate(observation['boundaries'][variant]):
            launched=human is not None and accepted[human]['dispatch']<=dispatch
            intercepted=(opponent is not None and accepted[opponent]['dispatch']<=dispatch)
            flags=boundary['contact'];terminal=None
            if launched:
                if intercepted:terminal='interception'
                elif flags&1:terminal='net'
                elif flags&0x88:terminal='out'
                elif flags&2:terminal='landing'
            elif flags&0x8d:terminal='no-contact'
            if terminal is not None:
                first_terminal=dispatch;first_classification=terminal;break
        last_dispatch=len(observation['boundaries'][variant])-1
        assert last_dispatch>=0, 'Discovery lacks a full actual dispatch boundary'
        if first_terminal is not None:
            assert first_terminal==last_dispatch, 'Preview continues after its first actual terminal boundary'
        classification='unqualified'
        if human is not None:
            if opponent is not None:classification='interception'
            elif contact&1:classification='net'
            elif contact&0x88:classification='out'
            elif contact&2:classification='landing'
        elif contact&0x8d:classification='no-contact'
        assert (first_classification or 'unqualified')==classification, 'Final endpoint is not the first actual terminal'
        if classification!='unqualified':
            assert result['outcomes'][variant]=={'landing':1,'net':2,'out':3,'interception':4,'no-contact':5}[classification]
        if classification in REQUIRED:coverage.add(classification)
        count=len(result['paths'][variant])//8
        # Require a complete sample strictly later than the launch boundary.
        outgoing=(human is not None and count>result['prefix']+accepted[human]['dispatch']+2)
        rows.append(dict(variant=variant,has_human_launch=human is not None,
            human_launch_order=human,human_launch=accepted[human] if human is not None else None,
            opponent_contact_order=opponent,opponent_contact=accepted[opponent] if opponent is not None else None,
            contact=contact,flight=flight,lifecycle=lifecycle,classification=classification,
            preview_outcome=result['outcomes'][variant],samples=count,outgoing_samples_present=outgoing,
            final_state_sha256=hashlib.sha256(state).hexdigest(),
            last_sampled_boundary=observation['boundaries'][variant][-1],
            first_terminal_boundary_checked=True,first_terminal_dispatch=first_terminal,
            last_sampled_dispatch=last_dispatch))
    paths=[[path[n:n+8] for n in range(0,len(path),8)] for path in result['paths']]
    coincident=bool(paths[0] and paths[1] and geometry(paths[0])==geometry(paths[1]))
    launched_coincidence=coincident and all(row['outgoing_samples_present'] for row in rows)
    if launched_coincidence:coverage.add('coincidence')
    return dict(variants=rows,prefix_samples=result['prefix'],geometry_coincident=coincident,
        launched_outgoing_coincidence=launched_coincidence,coverage=sorted(coverage),
        classifier_priority=['interception','net','out','landing'],
        source='actual-full-canonical-and-accepted-hooks',geometry_source='actual-sampled-drawn-geometry-visibility-ticks')


def discovery(executable,progress):
    image,symbols=load_image(executable)
    contract=contact_contract()
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
                    full_incoming_retained=True,selected_lifecycle=value(states[action],symbols,'game_lifecycle',2),
                    sampling_rows=sampling_rows(cpu,candidate,stream,states)))
            seeds.append(dict(seed=seed,recorded=True,dispatches=512,operations=len(stream),
                oldest=0,latest=cursor(cpu),input_stream_sha256=stream_hash(stream),candidates=identities,
                recorded_completed_returns=len(completed_returns),
                unavailable=None if len(eligible)==2 else f'Only {len(eligible)} completed returns with retained incoming context within512dispatches; no later search'))
            progress(dict(stage='stage-a2-recorded-seed',seed=seeds[-1]))
            original_trace=cpu.trace
            def guard(mode,width,address,value):
                if (mode=='W' and address<symbols['game_history_buffer_end']
                        and address+(1<<width)>symbols['game_history_buffer']
                        and field(cpu,'game_history_mode',1)==2):
                    raise AssertionError('Frozen discovery writes history/live backup, including crossing writes')
                original_trace(mode,width,address,value)
            cpu.mem.set_trace_func(guard)
            cpu.call('game_history_freeze')
            for candidate,identity in zip(eligible,identities):
                seen_jobs=set()
                for sample in identity['sampling_rows']:
                    if not sample['available']:continue
                    selection=sample['selection'];seek(cpu,selection);bounds=table(cpu,candidate['end'])
                    assert bounds==sample['bounds'], 'Sampling legal table differs at selected actual animation'
                    y=sample['center_y']
                    for x in sample['x_positions']:
                        key=(selection,x,y)
                        if key in seen_jobs:continue
                        seen_jobs.add(key)
                        assert len(jobs)<72, 'A2 reaches72jobs; no automatic cap expansion'
                        observation=execute(cpu,candidate['ordinal'],selection,x,y,stream,seed,f'discovery-{seed:04x}-{len(jobs)}')
                        source=states[candidate['incoming_origin']+1]
                        observation['recorded_incoming_origin']=candidate['incoming_origin']
                        observation['recorded_incoming_state']=source
                        assert observation['result']['incoming']==candidate['incoming_origin']
                        validate_edited_source(observation,symbols,source)
                        for variant in (0,1):
                            first_dispatch=next((state for name,args,state in observation['traces'][variant] if name=='game_tick_dispatch'),None)
                            assert first_dispatch is not None
                            assert all(value(first_dispatch,symbols,name)==value(states[candidate['incoming_origin']+1],symbols,name)
                                for name in GEOMETRY_FIELDS), 'Primer changes actual selected pre-dispatch contact geometry'
                        facts=qualification(observation,symbols)
                        assert bounds['left']<=x<bounds['right'] and bounds['top']<=y<bounds['bottom']
                        row=dict(name=observation['name'],seed=seed,ordinal=candidate['ordinal'],
                            candidate=identity,x=x,y=y,bounds=bounds,selection=selection,sampling_row=sample,
                            pre_dispatch_geometry_verified=True,incoming_full_state_verified=True,fingerprint=continuation_fingerprint(observation),
                            qualification=facts,costs=observation['costs'],
                            worker_call_cap=8192,maximum_worker_operations=4,total_samples_per_path=CAPACITY,
                            frozen_history_write_guard=True)
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
        position_policy=POSITION_POLICY,time_policy=TIME_POLICY,contact_geometry_contract=contract,job_cap=72,
        worker_call_cap=8192,maximum_worker_operations=4,total_samples_per_path=CAPACITY,
        frozen_history_write_guard=True,
        jobs=len(jobs),seeds=seeds,job_results=jobs,required_coverage=list(REQUIRED),
        actual_coverage=sorted(qualified),absent_classes=sorted(set(REQUIRED)-qualified),chosen_cases=chosen,
        scope='A2 bounded actual CPU discovery and chosen uninterrupted continuations; A3/native/resources/UI pending.')
    progress(dict(stage='stage-a2-complete',result=report))
    assert report['passed'], 'Bounded A2 discovery lacks actual '+', '.join(report['absent_classes'])+'; no automatic seed/dispatch/job expansion'
    assert jobs and chosen
    return report
