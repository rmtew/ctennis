"""Actual CPU differential for fixed incoming and geometric outgoing trials.

The oracle calls original logical bodies through changed contact timing, then
original ball phases. It contains no contact, trajectory or AI model. State is
initialized once per execution; expected intermediate state is never injected.
"""
import json
from pathlib import Path

from build_match_core import build, load_image
from history_proof import attempts, cursor, field, seek
from match_core_cpu import Core
from preview_proof import call_checked, fixture, point, protected
from run_shared_match_core import READONLY

CAPACITY = 513


def pads(state, symbols, end, held):
    offset = symbols['game_lower_owner'] - symbols['game_core_state'] + end
    owner = state[offset]
    offset = symbols['game_input_bits'] - symbols['game_core_state']
    values = list(state[offset:offset+2])
    values[owner] = (values[owner] & 0xc0) | (0x10 if held else 0)
    return values


def oracle(image, symbols, initial, stream, end, held, poison):
    path, states, outputs = [point(initial, symbols)], [], []
    launched, contact_phase, phases = False, None, 0
    with Core(image, symbols, initial=initial, poison=poison, readonly=READONLY) as cpu:
        def observe(pc):
            nonlocal launched, contact_phase
            cpu.instruction(pc)
            if pc in (symbols['game_history_contact'], symbols['game_history_serve']):
                if cpu.cpu.r_reg(7) & 0xffff == end:
                    launched = True
                    contact_phase = phases + 1
        cpu.cpu.set_instr_hook_callback(observe)
        cpu.call_logical('game_core_sample_pads', pads(initial, symbols, end, held))
        for name, arguments in stream:
            arguments = list(arguments)
            if name == 'game_core_sample_pads':
                owner = cpu.state()[symbols['game_lower_owner']-cpu.start+end]
                arguments[owner] = (arguments[owner] & 0xffc0) | (16 if held else 0)
            cpu.clear_events()
            cpu.call_logical(name, arguments)
            outputs.extend(cpu.events)
            if name != 'game_tick_dispatch':
                continue
            phases += 1
            state = cpu.state()
            path.append(point(state, symbols))
            states.append(state)
            if launched or state[symbols['game_contact']-cpu.start] & 0x8d:
                break
            if phases == 256:
                break
        if launched:
            for _ in range(256):
                cpu.call('game_ball_tick', {12: symbols['game_play_state'], 13: cpu.start})
                state = cpu.state()
                path.append(point(state, symbols))
                states.append(state)
                if state[symbols['game_contact']-cpu.start] & 0x8b:
                    break
        cpu.audit_reads()
        return path, cpu.state(), contact_phase, states, outputs


def run(executable):
    image, symbols = load_image(executable)
    with Core(image, symbols, readonly=READONLY) as cpu:
        stream, states, _, launches = fixture(cpu)
        contact = next(row for row in launches if row['human'] and row['kind'] == 1)
        incoming = max(row['origin'] for row in launches
                       if row['end'] != contact['end'] and row['origin'] < contact['origin'])
        source = states[incoming+1]
        ordinal = next(i for i, (_, kind, end) in enumerate(attempts(cpu))
                       if kind == 1 and end == contact['end'])
    results = []
    player_offset = symbols['game_play_state']-symbols['game_core_state']+contact['end']*10
    for x, y in ((111,153), (111,140), (111,128), (111,112), (111,98), (100,153), (119,153), (40,153), (180,153)):
        for poison in (0xa5, 0x96):
            edited = bytearray(source)
            edited[player_offset+3], edited[player_offset+2] = x, y
            expected = [oracle(image, symbols, edited, stream[incoming+1:],
                               contact['end'], held, poison) for held in (True, False)]
            with Core(image, symbols, poison=poison, readonly=READONLY) as cpu:
                fixture(cpu)
                cpu.call('game_history_freeze')
                seek(cpu, contact['origin'])
                saved = protected(cpu)
                generation = field(cpu, 'game_preview_generation', 4)
                selection = ordinal if poison == 0xa5 else 0xfffe
                call_checked(cpu, 'game_preview_request',
                             {0:generation, 1:selection, 2:x, 3:y}, saved)
                assert cpu.cpu.r_reg(0) == 1, (x, y, selection)
                generation += 1
                cycles = []
                cpu.preview_event_groups.clear()
                # One operation per public yield exposes each complete phase.
                previous_counts = [0,0]
                for job in range(4096):
                    cycles.append(call_checked(cpu, 'game_preview_step',
                                               {0:generation, 1:1}, saved))
                    for variant in (0,1):
                        count = cpu.mem.r16(symbols['game_preview_counts']+2*variant)
                        if count > 1:
                            target = expected[variant][3][count-2]
                            name = 'game_preview_held_state' if variant == 0 else 'game_preview_released_state'
                            # Sampling/poll phases can alter state between ball samples;
                            # compare only a newly completed projection.
                            previous = previous_counts[variant]
                            if count != previous:
                                assert bytes(cpu.mem.r_block(symbols[name],318)) == target, (x,y,variant,count,'phase-state')
                        previous_counts[variant] = count
                    if field(cpu, 'game_preview_status') >= 5:
                        break
                assert field(cpu, 'game_preview_status') == 5, (x, y, selection, field(cpu, 'game_preview_status'))
                assert cursor(cpu, 'game_preview_incoming') == incoming
                cache = bytes(cpu.mem.r_block(symbols['game_preview_incoming_state'], 318))
                assert cache == source, 'Incoming cache excludes dispatcher service/scene tail'
                for variant, (path, final, phase, _, _) in enumerate(expected):
                    count = cpu.mem.r16(symbols['game_preview_counts']+2*variant)
                    actual = bytes(cpu.mem.r_block(symbols['game_preview_paths']+variant*CAPACITY*8, count*8))
                    assert actual == b''.join(path), (x, y, variant, count, len(path))
                    state_symbol = 'game_preview_held_state' if variant == 0 else 'game_preview_released_state'
                    assert bytes(cpu.mem.r_block(symbols[state_symbol], 318)) == final, (x, y, variant, 'full-state')
                    assert cpu.preview_event_groups.get((2,variant),[]) == expected[variant][4], (x,y,variant,'events')
                    assert final[player_offset+3] == x and final[player_offset+2] == y, 'Trial/visible edited player diverged'
                cpu.audit_reads()
                row = dict(x=x, y=y, poison=poison, selection=selection,
                           counts=[len(item[0]) for item in expected],
                           contact_phases=[item[2] for item in expected],
                           outcomes=[cpu.mem.r16(symbols['game_preview_outcomes']+2*v) for v in (0,1)],
                           maximum_step_cpu_cycles=max(cycles), passed=True)
                results.append(row)
                print(json.dumps(row), flush=True)
    phases = {row['contact_phases'][0] for row in results}
    assert None in phases and len(phases - {None}) >= 2, 'Missing changed timing or visible miss coverage'
    boundaries = []
    with Core(image, symbols, readonly=READONLY) as cpu:
        _, original_states, _, _ = fixture(cpu)
        miss_ordinal, miss_origin = next((i, n) for i,(n,k,e) in enumerate(attempts(cpu)) if k==2)
    terminal = next(n for n in sorted(original_states) if n > miss_origin and
                    original_states[n][symbols['game_contact']-symbols['game_core_state']] & 0x8d)
    for label, boundary, selection, expected_status in (
            ('current-expires-after-return', contact['origin']+1, 0xfffe, 6),
            ('completed-return-after-action', contact['origin']+1, ordinal, 5),
            ('current-expires-after-miss', terminal, 0xfffe, 6),
            ('completed-miss-after-terminal', terminal, miss_ordinal, 5)):
        with Core(image, symbols, readonly=READONLY) as cpu:
            fixture(cpu)
            cpu.call('game_history_freeze')
            seek(cpu, boundary)
            saved = protected(cpu)
            generation = field(cpu,'game_preview_generation',4)
            call_checked(cpu,'game_preview_request',{0:generation,1:selection,2:111,3:153},saved)
            assert cpu.cpu.r_reg(0)==1
            for _ in range(4096):
                call_checked(cpu,'game_preview_step',{0:generation+1,1:4},saved)
                if field(cpu,'game_preview_status')>=5:
                    break
            assert field(cpu,'game_preview_status')==expected_status, (label,field(cpu,'game_preview_status'))
            cpu.audit_reads()
            boundaries.append(dict(label=label, boundary=boundary, selection=selection,
                                   expected_status=expected_status,passed=True))
    return dict(passed=True, rows=results, boundaries=boundaries, incoming_cursor=incoming,
                original_contact_cursor=contact['origin'], full_private_bytes=318,
                protected='complete image outside preview, canonical/history/live events',
                scope='Actual CPU; native timing, sprite publication and resource gate pending.')


if __name__ == '__main__':
    executable, _ = build()
    result = run(executable)
    output = Path('build/tests/incoming-flight-cpu/results-unvalidated.json')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2)+'\n')
