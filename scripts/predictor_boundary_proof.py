"""Supplemental integrated witnesses, with explicit once-only boundary setup.

Declared geometry is not a naturally reached opponent launch. Public cache
fixtures declare the complete immutable origin and protocol metadata before
the first tested request; they do not exercise cold resolver discovery.
"""
from pathlib import Path

from build_match_core import load_image
from history_proof import attach, field
from match_core_cpu import Core
from native_evidence import atomic_json
from predictor_proof import (SEEDS, MAX_WORKER_CALLS, api_case, causal, compare,
                             discover, execute, guard_cases, offset)
from preview_proof import block, call_checked, protected
from run_shared_match_core import READONLY


def declared_cases(symbols, source):
    common = dict(game_lower_phase=2, game_upper_phase=0, game_lower_y=153,
        game_lower_x=40, game_flight=64, game_contact=64, game_step=2,
        game_velocity_x=0, game_velocity_y=5, game_velocity_z=0,
        game_base_x=128, game_base_y=193, game_base_screen_y=191,
        game_ball_x=128, game_ball_y=191, game_court_x=128, game_court_y=193,
        game_tick=255)
    settings = [
        ('scene-clamp-tick-wrap', {}, 'no-contact', 0x8d),
        ('incoming-outside', dict(game_step=0, game_base_x=31,
            game_base_y=150, game_base_screen_y=100, game_ball_x=31,
            game_court_x=31, game_court_y=150, game_ball_y=100), 'no-contact', 0x80),
        ('incoming-net', dict(game_step=0, game_flight=72, game_base_y=110,
            game_base_screen_y=110, game_court_y=110, game_ball_y=110), 'no-contact', 1),
        ('incoming-court-out-bounce', dict(game_step=0, game_base_x=32,
            game_base_y=100, game_base_screen_y=101, game_ball_x=32,
            game_court_x=32, game_court_y=100, game_ball_y=101), 'no-contact', 0x0a),
        ('outgoing-out-after-contact', dict(game_step=0, game_base_x=32,
            game_base_y=180, game_base_screen_y=160, game_ball_x=32,
            game_court_x=32, game_court_y=180, game_ball_y=160), 'out', 0x0a),
    ]
    for name, changes, termination, mask in settings:
        state = bytearray(source)
        fields = common | changes
        for key, value in fields.items():
            state[offset(symbols, key)] = value
        yield dict(name=name, origin=bytes(state), changes=fields,
                   termination=termination, terminal_mask=mask)


def witnesses(symbols, case, result):
    state = bytes.fromhex(result['final'])
    flags = state[offset(symbols, 'game_contact')]
    paths = [bytes.fromhex(p) for p in result['path']]
    assert result['termination'] == case['termination'], case['name']
    assert flags & case['terminal_mask'], (case['name'], flags)
    if case['name'] != 'scene-clamp-tick-wrap':
        assert flags & case['terminal_mask'] == case['terminal_mask'], (case['name'], flags)
    incoming = [bytes.fromhex(b['full']) for b in result['boundaries']
                if b['operation'] == 'game_tick_dispatch']
    assert incoming and case['origin'][offset(symbols, 'game_tick')] == 255
    assert incoming[0][offset(symbols, 'game_tick')] == 0
    # Every dispatcher increments the actual byte clock; cursor/counts remain
    # independent of that wrap. Outgoing ball-only samples do not advance it.
    assert all(s[offset(symbols, 'game_tick')] == i & 255
               for i, s in enumerate(incoming))
    clamp = case['name'] == 'scene-clamp-tick-wrap'
    if clamp:
        assert result['ledger']['clamps'][0] == dict(phase=1, ball_y=192, court_y=193)
        assert paths[1][1] == 194 and paths[1][3] == 192
    launch = case['name'] == 'outgoing-out-after-contact'
    assert bool(result['ledger']['launches']) == launch
    if launch:
        assert result['ledger']['launches'][0]['phase'] == 1
        assert result['ledger']['launches'][0]['kind'] == 1
    return dict(passed=True, tick_wrap=True, scene_clamp=clamp,
        human_launch=launch, terminal_flags=flags,
        incoming_dispatches=len(incoming), samples=len(paths),
        termination=result['termination'])


def cached_api(image, symbols, case, budget, poison, references):
    """Public requests over a declared complete cache at a frozen boundary.

    All fixture writes precede the first tested request. No subsequent oracle
    state feed, force-contact, outgoing patch or worker selection is allowed.
    """
    origin = case['origin']
    with Core(image, symbols, initial=origin, poison=poison, readonly=READONLY) as cpu:
        attach(cpu)
        cpu.call_logical('game_round_poll', [])
        assert cpu.state() == origin
        cpu.call('game_history_freeze')
        # Declare an already resolved cache: opponent pre-op cursor0, complete
        # post-op origin1. The retained op0 here is only a fixture placeholder;
        # no natural cache-discovery or historical-launch assertion is made.
        for name in ('game_preview_incoming_state', 'game_preview_selected_state'):
            cpu.mem.w_block(symbols[name], origin)
        cpu.mem.w_block(symbols['game_preview_history_saved'],
                        block(cpu, 'game_history_state', 'game_history_state_end'))
        for name, value in [('game_preview_status', 2), ('game_preview_cache_valid', 1),
                ('game_preview_ordinal', 0xfffe), ('game_preview_kind', 0),
                ('game_preview_end', 0)]:
            cpu.mem.w16(symbols[name], value)
        cpu.mem.w8(symbols['game_preview_incoming_valid'], 1)
        cpu.mem.w_block(symbols['game_preview_selected'], (1).to_bytes(8, 'big'))
        cpu.mem.w_block(symbols['game_preview_incoming'], bytes(8))
        saved = protected(cpu)
        old_trace = cpu.trace
        def trace(mode, width, address, value):
            if (mode == 'R' and field(cpu, 'game_preview_active', 1) == 2
                    and address < cpu.stop and address + (1 << width) > cpu.start):
                raise AssertionError('Public private worker read paused canonical state')
            old_trace(mode, width, address, value)
        cpu.mem.set_trace_func(trace)
        generation = field(cpu, 'game_preview_generation', 4)
        results = []
        for name, projected in [('game_preview_request_projected', True),
                                ('game_preview_request', False)]:
            cpu.preview_event_groups.clear()
            call_checked(cpu, name, {0:generation, 1:0xfffe, 2:40, 3:153}, saved)
            assert cpu.cpu.r_reg(0) == 1
            generation += 1
            assert field(cpu, 'game_preview_status') == 2
            assert bytes(cpu.mem.r_block(symbols['game_preview_predictor_routes'], 2)) == bytes([int(projected)] * 2)
            cycles = []
            for _ in range(MAX_WORKER_CALLS):
                cycles.append(call_checked(cpu, 'game_preview_step', {0:generation, 1:budget}, saved))
                if field(cpu, 'game_preview_status') >= 5:
                    break
            assert field(cpu, 'game_preview_status') == 5
            observations = []
            for variant, expected in enumerate(references):
                count = cpu.mem.r16(symbols['game_preview_counts'] + variant * 2)
                paths = bytes(cpu.mem.r_block(symbols['game_preview_paths'] + variant * 513 * 8, count * 8))
                assert paths == bytes.fromhex(''.join(expected['path']))
                last = expected['boundaries'][-1]
                cursor = int.from_bytes(cpu.mem.r_block(symbols['game_preview_stream_cursors'] + variant * 8, 8), 'big')
                assert cursor == 1 + last['record_cursor'] and cursor >= 1
                assert cpu.mem.r16(symbols['game_preview_synthetic_phases'] + variant * 2) == last['synthetic_phase']
                assert cpu.mem.r16(symbols['game_preview_dispatches'] + variant * 2) == last['dispatches']
                assert cpu.mem.r16(symbols['game_preview_flight_phases'] + variant * 2) == count - 1 - last['dispatches']
                assert cpu.mem.r16(symbols['game_preview_outcomes'] + variant * 2) == (3 if case['termination'] == 'out' else 5)
                context = 'game_preview_held_state' if variant == 0 else 'game_preview_released_state'
                final = bytes(cpu.mem.r_block(symbols[context], 318))
                assert causal(final, symbols) == causal(bytes.fromhex(expected['final']), symbols)
                assert bool(cpu.mem.r8(symbols['game_preview_launches'] + variant)) == bool(expected['ledger']['launches'])
                if expected['ledger']['launches']:
                    launch = bytes(cpu.mem.r_block(symbols['game_preview_launch_states'] + variant * 318, 318))
                    assert causal(launch, symbols) == causal(bytes.fromhex(expected['incoming_final']), symbols)
                if not projected:
                    assert final.hex() == expected['final']
                    assert cpu.preview_event_groups.get((2, variant), []) == expected['events']
                observations.append(dict(variant=variant, cursor=cursor, dispatches=last['dispatches'],
                    synthetic_phase=last['synthetic_phase'], samples=count, final=final.hex(), path=paths.hex()))
            results.append(dict(api=name, route=int(projected), maximum_step_cpu_cycles=max(cycles),
                observations=observations, exact_full_state_events_equal=not projected))
        call_checked(cpu, 'game_preview_cancel', {0:generation}, saved)
        before = block(cpu, 'game_preview_storage', 'game_preview_storage_end')
        for name in ('game_preview_request', 'game_preview_request_projected'):
            call_checked(cpu, name, {0:generation, 1:0xfffe, 2:40, 3:153}, saved)
            assert cpu.cpu.r_reg(0) == 0
            assert block(cpu, 'game_preview_storage', 'game_preview_storage_end') == before
        cpu.audit_reads()
        return dict(passed=True, budget=budget, poison=poison, results=results,
            frozen_full_image_history_isolated=True, canonical_read_guard=True,
            stale_cancel_neutral=True, initial_setup='declared-full-cache-api-boundary',
            cold_resolver_tested=False, natural_reachability_claimed=False)


def run(executable, raw):
    image, symbols = load_image(executable)
    raw = Path(raw); raw.mkdir(parents=True, exist_ok=True)
    base = discover(image, symbols, 0xace1)[0]
    boundaries = []; terminal_origins = []; faults = []
    for case in declared_cases(symbols, base['source']):
        references = []; pairs = []; checks = []
        for held in (True, False):
            reference = execute(image, symbols, case['origin'], [], 0, held, False, 0xa5)
            references.append(reference)
            for poison in (0xa5, 0x96):
                candidate = execute(image, symbols, case['origin'], [], 0, held, True, poison, omitted_poison=True)
                compare(reference, candidate)
                assert candidate['route'] == 1 and candidate['reason'] == 0 and candidate['predictor_ticks'] > 0
                check = witnesses(symbols, case, candidate); checks.append(check)
                pairs.append(dict(held=held, poison=poison, reference=reference, candidate=candidate, witnesses=check))
        apis = [cached_api(image, symbols, case, budget, 0xa5 if budget & 1 else 0x96, references)
                for budget in (1,2,3,4)]
        # Start a separate pair at the complete terminal produced by actual
        # execution. Never feed it back into the running trial. Admission must
        # reject terminal origins and full fallback must match state/events.
        terminal = bytes.fromhex(references[0]['final'])
        left = execute(image, symbols, terminal, [], 0, True, False, 0xa5)
        right = execute(image, symbols, terminal, [], 0, True, True, 0x96)
        compare(left, right)
        assert right['route'] == 0 and right['reason'] == 7 and right['predictor_ticks'] == 0
        terminal_origins.append(dict(name=case['name'], passed=True, reason=7,
            full_state_events_equal=True, predictor_ticks=0))
        if case['name'] == 'incoming-outside':
            fault_terminal = terminal
        atomic_json(raw/(case['name']+'.json'), dict(name=case['name'], initial_origin=case['origin'].hex(),
            changes=case['changes'], setup='Once-declared complete boundary and cache; no natural reachability claim',
            pairs=pairs, api_cases=apis, terminal_fallback=dict(reference=left, candidate=right)))
        boundaries.append(dict(name=case['name'], passed=True, pairs=len(pairs), witnesses=checks,
            api_budgets=[a['budget'] for a in apis], exact_replacement=True,
            initial_setup='declared-full-cache-api-boundary', natural_reachability_claimed=False))
        print('boundary passed:', case['name'], flush=True)
    for name, display, status in [('first-serve-fault', 16, 5), ('second-serve-fault', 24, 6)]:
        origin = bytearray(fault_terminal)
        # Once-declared serve/fault retry latch at an actual terminal boundary;
        # scoring announcement is outside the admitted preview horizon.
        origin[offset(symbols, 'game_display')] = display
        reference = execute(image, symbols, bytes(origin), [], 0, True, False, 0xa5)
        candidate = execute(image, symbols, bytes(origin), [], 0, True, True, 0x96)
        compare(reference, candidate)
        assert candidate['route'] == 0 and candidate['reason'] == 7 and candidate['predictor_ticks'] == 0
        final = bytes.fromhex(candidate['final'])
        assert final[offset(symbols, 'game_display')] & 7 == status
        assert final[offset(symbols, 'game_score_state')] == 2
        assert bool(final[offset(symbols, 'game_display')] & 8) == (status == 5)
        start_points = bytes(origin)[offset(symbols, 'game_point_a'):offset(symbols, 'game_point_a')+2]
        end_points = final[offset(symbols, 'game_point_a'):offset(symbols, 'game_point_a')+2]
        assert (start_points == end_points) == (status == 5)
        atomic_json(raw/(name+'.json'),dict(initial_origin=bytes(origin).hex(), reference=reference,
            candidate=candidate, initial_setup='declared-serve-retry-latch-at-actual-terminal',
            natural_reachability_claimed=False))
        faults.append(dict(name=name, passed=True, reason=7, queued_status=status,
            stage=2, full_state_events_equal=True, predictor_ticks=0,
            point_award=status == 6, visible_announcement_tested=False))
        print('exact fault fallback passed:', name, flush=True)
    upper = []
    for seed in (1, 0xbeef):
        case = discover(image, symbols, seed, upper=True)[0]
        end = case['end']; human = case['human']; x, y = human['x'], human['y']
        origin = bytearray(case['source']); origin[end*10+3] = x; origin[end*10+2] = y
        references = []; pairs = []
        for held in (True, False):
            reference = execute(image, symbols, bytes(origin), case['stream'], end, held, False, 0xa5)
            references.append(reference)
            for poison in (0xa5,0x96):
                candidate = execute(image, symbols, bytes(origin), case['stream'], end, held, True, poison, omitted_poison=True)
                compare(reference, candidate)
                assert candidate['route'] == 1 and candidate['predictor_ticks'] > 0
                pairs.append(dict(held=held, poison=poison, reference=reference, candidate=candidate))
        apis = [api_case(image, symbols, case, x, y, budget, 0xa5 if budget & 1 else 0x96, references)
                for budget in (1,2,3,4)]
        atomic_json(raw/f'upper-{seed:04x}.json',dict(initial_origin=bytes(origin).hex(),
            source=case['source'].hex(), seed=seed, incoming=case['incoming'], selected=case['selected'],
            actual_discovery_ticks=case['ticks'], human=human, pairs=pairs, api_cases=apis))
        upper.append(dict(passed=True, seed=seed, end=1, discovery_ticks=case['ticks'],
            pairs=len(pairs), api_budgets=[a['budget'] for a in apis], natural_exchange=True,
            human_contact_witness=any(r['reference']['ledger']['launches'] for r in pairs)))
        print('natural upper passed:', hex(seed), case['ticks'], flush=True)
    guards = guard_cases(image, symbols, base)
    atomic_json(raw/'guard-cases.json', guards)
    return dict(passed=True, boundary_cases=boundaries, natural_upper_cases=upper,
        guard_cases=guards, terminal_fallbacks=terminal_origins, fault_fallbacks=faults,
        full_private_bytes=318, no_intermediate_state_injection=True,
        unchanged_runtime=True, scope='Integrated actual CPU requests/workers with declared boundary fixtures; natural upper seeds separately. No new native timing or release coverage.')


def required_extent(report):
    v = report.get('validation') or {}
    rows = v.get('boundary_cases') or []; upper = v.get('natural_upper_cases') or []
    guards = v.get('guard_cases') or []
    terminals = v.get('terminal_fallbacks') or []; faults = v.get('fault_fallbacks') or []
    return (report.get('passed') is True and report.get('execution') == 'actual-68000-cpu-only'
        and v.get('passed') is True and v.get('full_private_bytes') == 318
        and v.get('no_intermediate_state_injection') is True and v.get('unchanged_runtime') is True
        and len(rows) == 5 and {r.get('name') for r in rows} == {
            'scene-clamp-tick-wrap', 'incoming-outside', 'incoming-net',
            'incoming-court-out-bounce', 'outgoing-out-after-contact'}
        and all(r.get('passed') is True and r.get('pairs') == 4 and r.get('api_budgets') == [1,2,3,4]
            and r.get('exact_replacement') is True and r.get('natural_reachability_claimed') is False
            and len(r.get('witnesses') or []) == 4 and all(w.get('passed') is True and w.get('tick_wrap') is True
                for w in r['witnesses']) for r in rows)
        and all(all(w.get('scene_clamp') is True for w in r['witnesses'])
                for r in rows if r['name'] == 'scene-clamp-tick-wrap')
        and all(all(w.get('human_launch') is True and w.get('termination') == 'out' for w in r['witnesses'])
                for r in rows if r['name'] == 'outgoing-out-after-contact')
        and len(upper) == 2 and {r.get('seed') for r in upper} == {1,0xbeef}
        and all(r.get('passed') is True and r.get('end') == 1 and r.get('natural_exchange') is True
            and r.get('human_contact_witness') is True and r.get('pairs') == 4
            and r.get('api_budgets') == [1,2,3,4] for r in upper)
        and len(terminals) == 5 and {r.get('name') for r in terminals} == {r['name'] for r in rows}
        and all(r.get('passed') is True and r.get('reason') == 7 and r.get('predictor_ticks') == 0
            and r.get('full_state_events_equal') is True for r in terminals)
        and len(faults) == 2 and {(r.get('name'), r.get('queued_status')) for r in faults} == {
            ('first-serve-fault',5), ('second-serve-fault',6)}
        and all(r.get('passed') is True and r.get('reason') == 7 and r.get('stage') == 2
            and r.get('predictor_ticks') == 0 and r.get('full_state_events_equal') is True
            and r.get('visible_announcement_tested') is False for r in faults)
        and len(guards) == 26 and {r.get('name') for r in guards} == {
            'exact-policy','serve-kind','invalid-kind','missing-incoming','lifecycle','uninitialized',
            'idle-stage','invalid-stage','pending-command','restart','suppressed-input','round-mode',
            'result-mode','two-human-mode','invalid-end','scorer-ai','score-flags','end-mode',
            'human-ai','opponent-human','owner','upper-owner','wrong-side','terminal','launch-pending','no-flight'}
        and all(r.get('passed') is True and r.get('admission_read_only') is True
            and r.get('registers_preserved') is True
            and (r.get('scope') != 'full-fallback' or r.get('full_state_events_equal') is True) for r in guards)
        and (v.get('original_core_bytes') or {}).get('passed') is True
        and (v.get('original_core_bytes') or {}).get('normalized_sha256') ==
            '99c543c170c036137be81d07ebd30b522ef3abdff04bd7b1af38f00047bb99d5'
        and (v.get('predictor_bytes') or {}).get('passed') is True
        and (v.get('predictor_bytes') or {}).get('sha256') ==
            '684cf9ca6f5db1d7b2863e59fade1fbb58175ba551e956017011daaa4d7831ef')
