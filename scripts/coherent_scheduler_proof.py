"""Actual 68000 grouping/interleaving proof, without a host simulation model.

Each schedule starts a fresh real recorder fixture. The legacy held-first worker
is the grouping reference; predictor.execute supplies an independently advanced
shared-body reference for exact/observational contracts. Raw boundary records
retain full states and ordered outputs, including on a failed comparison.
"""
import gzip
import json
import random
from pathlib import Path

from build_match_core import load_image
from history_proof import field, seek
from match_core_cpu import Core
from predictor_proof import discover, execute, causal, compare, MAX_WORKER_CALLS
from preview_proof import (OPERATIONS, ARITY, fixture, protected, call_checked,
                           block, point)
from run_shared_match_core import READONLY


def raw_json(path, value):
    """Lossless full byte/event records, compressed to bound disk consumption."""
    path = Path(str(path) + '.gz')
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_bytes(gzip.compress(json.dumps(value, sort_keys=True,
        separators=(',', ':')).encode(), mtime=0))
    temporary.replace(path)


def cursors(cpu, variant):
    s = cpu.symbols
    return dict(stream=int.from_bytes(cpu.mem.r_block(
        s['game_preview_stream_cursors'] + variant * 8, 8), 'big'),
        synthetic=cpu.mem.r16(s['game_preview_synthetic_phases'] + variant * 2),
        dispatches=cpu.mem.r16(s['game_preview_dispatches'] + variant * 2),
        flight=cpu.mem.r16(s['game_preview_flight_phases'] + variant * 2))


def outcome(cpu, variant):
    return cpu.mem.r16(cpu.symbols['game_preview_outcomes'] + variant * 2)


def session(image, symbols, case, x, y, projected, schedule, poison, raw):
    """Fresh independent execution; hooks observe body returns, never feed state."""
    rows = dict(resolve=[], branches=[[], []], calls=[], negatives=[])
    raw_json(raw, dict(passed=False, stage='started', records=rows))
    with Core(image, symbols, poison=poison, readonly=READONLY) as cpu:
        fixture(cpu, seed=case['seed'], dispatches=case['ticks'])
        live = cpu.state()
        cpu.call('game_history_freeze')
        seek(cpu, case['selected'])
        saved = protected(cpu)
        original_trace = cpu.trace

        def guard(mode, width, address, value):
            size = 1 << width
            active = cpu.mem.r8(symbols['game_preview_active'])
            if active and address < cpu.stop and address + size > cpu.start:
                raise AssertionError('Private worker accesses paused canonical state')
            if (mode == 'W' and address < symbols['game_history_buffer_end']
                    and address + size > symbols['game_history_buffer']):
                raise AssertionError('Worker writes frozen history/live backup')
            original_trace(mode, width, address, value)

        generation = field(cpu, 'game_preview_generation', 4)
        request = 'game_preview_request_projected' if projected else 'game_preview_request'
        call_checked(cpu, request, {0:generation, 1:0xfffe, 2:x, 3:y}, saved)
        assert cpu.cpu.r_reg(0) == 1
        generation += 1
        # Request legitimately reads the frozen selected origin while preparing
        # new private owners. Worker isolation starts after that transaction.
        cpu.mem.set_trace_func(guard)
        cpu.preview_events.clear()
        cpu.preview_event_groups.clear()
        bodies = {symbols[n + '_body']:(n, a) for n, a in zip(OPERATIONS, ARITY)}
        # The dispatch wrapper is the single logical operation on either route.
        bodies.pop(symbols['game_tick_dispatch_body'])
        bodies[symbols['game_preview_dispatch']] = ('game_tick_dispatch', 0)
        bodies[symbols['game_ball_tick']] = ('game_ball_tick', 0)
        pending = None

        def observe(pc):
            nonlocal pending
            cpu.instruction(pc)
            if pending and pc == pending['return_pc'] and cpu.cpu.r_sp() == pending['sp'] + 4:
                active, variant = pending['active'], pending['variant']
                record = dict(operation=pending['operation'], arguments=pending['arguments'],
                    full=cpu.working_state().hex(),
                    events=list(cpu.preview_events[pending['event_start']:]))
                if active == 2:
                    record['cursors'] = cursors(cpu, variant)
                    rows['branches'][variant].append(record)
                else:
                    record['cursor'] = int.from_bytes(cpu.mem.r_block(symbols['game_preview_cursor'], 8), 'big')
                    rows['resolve'].append(record)
                pending = None
            if pending or pc not in bodies:
                return
            active = cpu.mem.r8(symbols['game_preview_active'])
            if active not in (1, 2):
                return
            operation, arity = bodies[pc]
            sp = cpu.cpu.r_sp()
            pending = dict(operation=operation, active=active,
                variant=cpu.mem.r8(symbols['game_preview_variant']), sp=sp,
                return_pc=cpu.mem.r32(sp), event_start=len(cpu.preview_events),
                arguments=[cpu.cpu.r_reg(r) & 65535 for r in range(arity)])

        cpu.cpu.set_instr_hook_callback(observe)

        def neutral(name, args, label, frozen=True):
            before = block(cpu, 'game_preview_storage', 'game_preview_storage_end')
            if frozen:
                call_checked(cpu, name, args, saved)
            else:
                cpu.call(name,args)
                assert protected(cpu)==saved and field(cpu,'game_preview_active',1)==0
            assert cpu.cpu.r_reg(0) == 0, label
            assert block(cpu, 'game_preview_storage', 'game_preview_storage_end') == before, label
            rows['negatives'].append(label)

        neutral('game_preview_step_variant', {0:generation-1, 1:4, 2:0}, 'stale')
        neutral('game_preview_step_variant', {0:generation, 1:0, 2:0}, 'zero-budget')
        neutral('game_preview_step_variant', {0:generation, 1:5, 2:0}, 'excess-budget')
        neutral('game_preview_step_variant', {0:generation, 1:1, 2:2}, 'invalid-variant')
        neutral('game_preview_complete', {0:generation-1}, 'stale-complete')
        rng = random.Random(schedule['seed'])
        terminal_repeats = set()
        try:
            for step in range(MAX_WORKER_CALLS):
                budget = schedule.get('budget') or rng.randrange(1, 5)
                legacy = schedule['kind'] == 'legacy' or (
                    schedule['kind'] == 'mixed-prime' and field(cpu,'game_preview_primed_mask') & 2) or (
                    schedule['kind'] == 'mixed-terminal' and outcome(cpu,1))
                if legacy:
                    name, args = 'game_preview_step', {0:generation, 1:budget}
                else:
                    order = schedule['order']
                    variant = order[step % 2] if schedule['kind'] == 'interleave' else (
                        order[0] if not outcome(cpu, order[0]) else order[1])
                    if outcome(cpu, variant):
                        variant ^= 1
                    name, args = 'game_preview_step_variant', {0:generation, 1:budget, 2:variant}
                before = sum(len(r) for r in rows['branches']) + len(rows['resolve'])
                geometry_before = sum(cpu.visits.get(symbols[n],0) for n in
                    ('game_preview_complete','game_preview_compare_geometry'))
                cycles = call_checked(cpu, name, args, saved)
                assert cpu.cpu.r_reg(0) == 1
                assert pending is None, 'Logical body did not complete'
                executed = sum(len(r) for r in rows['branches']) + len(rows['resolve']) - before
                assert 0 <= executed <= budget, ('Operation budget exceeded', executed, budget)
                if name == 'game_preview_step_variant':
                    assert sum(cpu.visits.get(symbols[n],0) for n in
                        ('game_preview_complete','game_preview_compare_geometry')) == geometry_before, 'Variant worker hides geometry completion'
                rows['calls'].append(dict(api=name, args=args, cycles=cycles, operations=executed))
                for variant in (0, 1):
                    if outcome(cpu, variant) and variant not in terminal_repeats:
                        counts = [len(r) for r in rows['branches']]
                        call_checked(cpu, 'game_preview_step_variant', {0:generation, 1:4, 2:variant}, saved)
                        assert [len(r) for r in rows['branches']] == counts, 'Terminal branch advances again'
                        terminal_repeats.add(variant)
                if outcome(cpu, 0) and outcome(cpu, 1):
                    break
            else:
                raise AssertionError('Bounded worker-call cap reached')
            complete_cycles = 0
            for _ in range(66):
                complete_cycles += call_checked(cpu, 'game_preview_complete', {0:generation}, saved)
                if field(cpu, 'game_preview_status') == 5:
                    break
            assert field(cpu, 'game_preview_status') == 5
            final = dict(states=[block(cpu, n, n + '_end').hex() if n + '_end' in symbols
                else bytes(cpu.mem.r_block(symbols[n],318)).hex()
                for n in ('game_preview_held_state', 'game_preview_released_state')],
                paths=[bytes(cpu.mem.r_block(symbols['game_preview_paths'] + v*513*8,
                    cpu.mem.r16(symbols['game_preview_counts'] + v*2)*8)).hex() for v in (0,1)],
                outcomes=[outcome(cpu,v) for v in (0,1)],
                cursors=[cursors(cpu,v) for v in (0,1)],
                coincident=field(cpu,'game_preview_coincident'))
            before = block(cpu, 'game_preview_storage', 'game_preview_storage_end')
            call_checked(cpu, 'game_preview_complete', {0:generation}, saved)
            assert block(cpu, 'game_preview_storage', 'game_preview_storage_end') == before
            call_checked(cpu, 'game_preview_cancel', {0:generation}, saved)
            neutral('game_preview_step_variant', {0:generation,1:4,2:0}, 'cancelled-step')
            neutral('game_preview_complete', {0:generation}, 'cancelled-complete')
            neutral('game_preview_complete', {0:field(cpu,'game_preview_generation',4)}, 'cancelled-current-generation-complete')
            # Exercise real history ownership transitions after preserving the
            # completed branch ledger. Each new request reads an actual sought
            # state; no reference snapshot is fed back into the candidate.
            cpu.cpu.set_instr_hook_callback(cpu.instruction)
            cpu.mem.set_trace_func(original_trace)
            seek(cpu, case['selected'])
            saved = protected(cpu)
            old_generation = generation
            generation = field(cpu, 'game_preview_generation', 4)
            neutral('game_preview_step_variant', {0:old_generation,1:4,2:1}, 'seek-invalidates')
            call_checked(cpu, request, {0:generation,1:0xfffe,2:x,3:y}, saved)
            assert cpu.cpu.r_reg(0) == 1
            generation += 1
            cpu.mem.set_trace_func(guard)
            call_checked(cpu, 'game_preview_step_variant', {0:generation,1:1,2:1}, saved)
            assert cpu.cpu.r_reg(0) == 1
            cpu.mem.set_trace_func(original_trace)
            call_checked(cpu, request, {0:generation,1:0xfffe,2:x+1,3:y}, saved)
            assert cpu.cpu.r_reg(0) == 1, 'Changed position request rejected'
            old_generation = generation
            generation += 1
            neutral('game_preview_step_variant', {0:old_generation,1:4,2:0}, 'replacement-invalidates')
            seek_generation=field(cpu,'game_history_seek_generation',4)
            target=case['selected']-1
            cpu.call('game_history_seek_begin',{0:seek_generation,1:target>>32,2:target&0xffffffff})
            assert cpu.cpu.r_reg(0)==1 and field(cpu,'game_history_seek_status') in (1,2)
            saved=protected(cpu)
            neutral('game_preview_complete',{0:field(cpu,'game_preview_generation',4)},'pending-or-ready-seek-complete')
            neutral('game_preview_step_variant',{0:field(cpu,'game_preview_generation',4),1:4,2:0},'pending-or-ready-seek-step')
            cpu.call('game_history_resume_latest')
            assert cpu.cpu.r_reg(0) == 1 and cpu.state() == live
            assert field(cpu, 'game_history_mode', 1) == 1
            saved = protected(cpu)
            neutral('game_preview_step_variant', {0:generation,1:4,2:0}, 'resume-invalidates', frozen=False)
            cpu.audit_reads()
            result = dict(execution_passed=True, comparison_validated=False,
                records=rows, final=final, stack=cpu.stack_bytes,
                complete_cycles=complete_cycles, canonical_history_live_outputs_preserved=True)
            raw_json(raw, result)
            return result
        except BaseException:
            raw_json(raw, dict(passed=False, stage='execution-failed', records=rows))
            raise


def run(executable, raw):
    image, symbols = load_image(executable)
    raw = Path(raw)
    raw.mkdir(parents=True, exist_ok=True)
    cases = discover(image, symbols, 0xace1) + discover(image, symbols, 0xace1, upper=True)
    summaries = []
    for case in cases:
        end = case['end']
        positions = [(case['human']['x'], case['human']['y'])] if case['human'] else [(111,153)]
        if not end:
            positions += [(100,153),(114,153),(111,128),(40,153)]
        for x,y in dict.fromkeys(positions):
            references = {False:[],True:[]}
            for held in (True,False):
                origin = bytearray(case['source'])
                origin[end*10+3], origin[end*10+2] = x,y
                exact=execute(image,symbols,bytes(origin),case['stream'],end,held,False,0xa5)
                projected_reference=execute(image,symbols,bytes(origin),case['stream'],end,held,True,0x96)
                compare(exact,projected_reference)
                references[False].append(exact)
                references[True].append(projected_reference)
            raw_json(raw/f'reference-{end}-{x}-{y}.json', references)
            for projected in (False,True):
                schedules = [dict(kind='legacy',budget=1,order=[0,1],seed=0),
                    dict(kind='serial',budget=4,order=[1,0],seed=1),
                    dict(kind='interleave',order=[0,1],seed=0xace1),
                    dict(kind='interleave',order=[1,0],seed=0xbeef)]
                if (x,y)==positions[0]:
                    schedules += [dict(kind='mixed-prime',order=[1,0],seed=19),
                        dict(kind='mixed-terminal',order=[1,0],seed=23)]
                baseline = None
                for index,schedule in enumerate(schedules):
                    identity=f'{end}-{x}-{y}-{int(projected)}-{index}'
                    result=session(image,symbols,case,x,y,projected,schedule,
                        0xa5 if index%2==0 else 0x96,raw/(identity+'.json'))
                    semantic=(result['records']['resolve'],result['records']['branches'],result['final'])
                    if baseline is None:
                        baseline=semantic
                    else:
                        assert semantic==baseline, ('Grouping/interleaving changes logical boundaries',identity)
                    for variant,reference in enumerate(references[projected]):
                        assert result['final']['paths'][variant]==''.join(reference['path']), identity
                        actual_boundaries=result['records']['branches'][variant]
                        incoming_dispatches=reference['boundaries'][-1]['dispatches']
                        outgoing_count=len(reference['path'])-1-incoming_dispatches
                        assert len(actual_boundaries)==len(reference['boundaries'])+outgoing_count, ('Exact logical boundary count',identity)
                        for actual, expected in zip(actual_boundaries,reference['boundaries']):
                            expected_operation='game_core_sample_pads' if expected['operation']=='prime' else expected['operation']
                            assert actual['operation']==expected_operation, (identity,actual['operation'],expected_operation)
                            if projected:
                                assert causal(bytes.fromhex(actual['full']),symbols)==expected['causal'], ('Intermediate observations',identity)
                            else:
                                assert actual['full']==expected['full'] and actual['events']==expected['events'], ('Intermediate full state/events',identity)
                            assert actual['events']==expected['events'], ('Declared route ordered events',identity)
                        for phase,actual in enumerate(actual_boundaries[len(reference['boundaries']):],1):
                            assert actual['operation']=='game_ball_tick', ('Accounted outgoing operation',identity)
                            assert point(bytes.fromhex(actual['full']),symbols).hex()==reference['path'][incoming_dispatches+phase], ('Outgoing phase observation',identity)
                        if projected:
                            assert causal(bytes.fromhex(result['final']['states'][variant]),symbols)==causal(bytes.fromhex(reference['final']),symbols),identity
                        else:
                            assert result['final']['states'][variant]==reference['final'],identity
                        events=[e for r in result['records']['branches'][variant] for e in r['events']]
                        assert events==reference['events'],('Final ordered route events',identity)
                    summaries.append(dict(identity=identity,passed=True,schedule=schedule,
                        calls=len(result['records']['calls']),stack=result['stack'],
                        max_cpu_cycles=max(c['cycles'] for c in result['records']['calls']),
                        complete_cpu_cycles=result['complete_cycles'],
                        operations=sum(c['operations'] for c in result['records']['calls'])))
                    result.update(passed=True, comparison_validated=True)
                    raw_json(raw/(identity+'.json'),result)
                    print(f'coherent CPU case {identity} passed',flush=True)
    return dict(passed=True,cases=summaries,full_private_bytes=318,
        intermediate_states_events_cursors_equal=True,both_orders=True,random_grouping=True,
        mixed_legacy_after_released_prime_terminal=True,ordered_projected_route_events_equal=True,
        scope='Finite actual 68000 API grouping/branch isolation, exact/observational equivalence, cancel/replacement/seek/resume generation isolation; not native IRQ/timing/display or universal cost bounds. Native producer/publication require separate proofs.')
