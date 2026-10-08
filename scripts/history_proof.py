"""Bounded-store proofs over the actual 68000 logical API, never tennis rules."""
from collections import Counter
from build_match_core import load_image
from match_core_cpu import Core
from run_shared_match_core import READONLY


def field(cpu, name, size=2):
    return int.from_bytes(cpu.mem.r_block(cpu.symbols[name], size), 'big')


def cursor(cpu, name='game_history_cursor'):
    return field(cpu, name, 8)


def attach(cpu):
    s = cpu.symbols
    size = s['game_history_buffer_end']-s['game_history_buffer']
    cpu.call('game_history_attach', {8:s['game_history_buffer'], 0:size})
    assert cpu.cpu.r_reg(0) == 1
    return size


def attempts(cpu):
    first, count = field(cpu,'game_history_attempt_first'), field(cpu,'game_history_attempt_count')
    store = field(cpu,'game_history_store',4)
    result = []
    for index in range(count):
        address = store+14336+5280+((first+index)&127)*12
        raw = bytes(cpu.mem.r_block(address,12))
        origin = int.from_bytes(raw[:8],'big')
        kind, end = int.from_bytes(raw[8:10],'big'), int.from_bytes(raw[10:],'big')
        assert cursor(cpu,'game_history_oldest') <= origin < cursor(cpu), (origin,cursor(cpu))
        assert kind in (0,1,2,3) and end in (0,1)
        result.append((origin,kind,end))
    return result


def seek(cpu, target):
    cpu.clear_events()
    cycles = cpu.call('game_history_seek',{0:target>>32,1:target&0xffffffff})
    assert cpu.cpu.r_reg(0) == 1, ('seek rejected',target)
    return cycles


def exercise(executable, rows=None, ticks=1536, poison=0xa5, base=0x10000, wrap=False, native_guards=False):
    image,symbols = load_image(executable,base)
    with Core(image,symbols,poison=poison,readonly=READONLY) as cpu, Core(image,symbols,poison=poison,readonly=READONLY) as uninterrupted:
        cpu.call_logical('game_core_init',[])
        uninterrupted.call_logical('game_core_init',[])
        canonical = cpu.state()
        expected_size = symbols['game_history_buffer_end']-symbols['game_history_buffer']
        for pointer,length in ((0,expected_size),(symbols['game_history_buffer']+1,expected_size),
                               (symbols['game_history_buffer'],expected_size-2),
                               (symbols['game_history_buffer'],expected_size+2),(0xfffffffe,expected_size)):
            cpu.call('game_history_attach',{8:pointer,0:length})
            assert cpu.cpu.r_reg(0)==0 and cpu.state()==canonical and field(cpu,'game_history_mode',1)==0
        size = attach(cpu)
        offset = (1<<32)-512 if wrap else 0
        if wrap:
            # One-time history-only fixture origin, before the first operation.
            # Canonical state is untouched and no later expected state injected.
            cpu.mem.w_block(symbols['game_history_cursor'],offset.to_bytes(8,'big'))
            cpu.mem.w_block(symbols['game_history_oldest'],offset.to_bytes(8,'big'))
            cpu.mem.w_block(symbols['game_history_buffer']+14336,offset.to_bytes(8,'big'))
        expected = {offset:(cpu.state(),[])}
        outputs, record_cycles, checkpoint_cycles = {}, [], []
        regular_overhead, checkpoint_overhead = [], []
        counts = Counter()
        outcomes = set()
        tick_wraps = 0
        last_tick = field(cpu,'game_tick',1)
        if rows is None:
            stream = [('game_core_select',[0,0xace1,0])]
            for tick in range(ticks):
                # Fixed controls are inputs only. Outcomes come from 68000.
                stream.extend([('game_round_poll',[]),
                    ('game_core_sample_pads',[(0x10 if tick%64>=8 else 0) | (8 if tick%96<48 else 4),0]),
                    ('game_core_sample_result',[0,0,0,0,0,0]),
                    ('game_tick_dispatch',[])])
        else:
            stream = [(row['operation'],row['arguments']) for row in rows if row['operation']!='game_core_init']
        for name,args in stream:
            cpu.clear_events()
            cycles = cpu.call_logical(name,args)
            uninterrupted.clear_events()
            baseline_cycles = uninterrupted.call_logical(name,args)
            assert cpu.state()==uninterrupted.state() and cpu.events==uninterrupted.events, ('recording alters core',name)
            boundary = cursor(cpu)
            (checkpoint_overhead if boundary%64==0 else regular_overhead).append(cycles-baseline_cycles)
            expected[boundary] = (cpu.state(),list(cpu.events))
            outputs[boundary] = list(cpu.events)
            counts[name] += 1
            tick = field(cpu,'game_tick',1)
            tick_wraps += int(last_tick==255 and tick==0)
            last_tick = tick
            outcomes.update((origin,kind) for origin,kind,_ in attempts(cpu) if kind)
            (checkpoint_cycles if boundary%64==0 else record_cycles).append(cycles)
            if rows is not None:
                row = rows[boundary-offset] # initial init is row0
                assert cpu.state().hex() == row['state'] and cpu.events == row['events']
        end, oldest = cursor(cpu), cursor(cpu,'game_history_oldest')
        index = attempts(cpu)
        before = bytes(cpu.mem.r_block(symbols['game_history_buffer'],size-318))
        live = cpu.state()
        cpu.call('game_history_freeze')
        assert cpu.cpu.r_reg(0) == 1
        # External logical controls while frozen cannot advance/edit live core.
        cpu.call_logical('game_core_sample_pads',[0xffff,0xffff])
        assert cpu.state() == live
        seek_cycles = []
        boundaries = list(range(oldest,end+1))
        for target in boundaries[::-1] + boundaries + [oldest,end,oldest,end]:
            seek_cycles.append(seek(cpu,target))
            if len(seek_cycles)%500==0:
                print('Validated seeks',len(seek_cycles),'of',2*len(boundaries)+4,flush=True)
            assert cpu.state() == expected[target][0], ('seek state',target)
            origin = cursor(cpu,'game_history_origin')
            events = [event for n in range(origin+1,target+1) for event in outputs[n]]
            assert cpu.events == events, ('seek events',target)
            assert cursor(cpu) == end and cursor(cpu,'game_history_oldest') == oldest
            assert bytes(cpu.mem.r_block(symbols['game_history_buffer'],size-318)) == before
        negatives = []
        for target in (oldest-1,end+1):
            state = cpu.state()
            cpu.clear_events()
            cpu.call('game_history_seek',{0:(target>>32)&0xffffffff,1:target&0xffffffff})
            assert cpu.cpu.r_reg(0)==0 and cpu.state()==state and cpu.events==[]
            negatives.append('out-of-range-'+str(target))
        # Selected checkpoint envelope/entropy corruption must reject before
        # canonical writes. Restore only the corrupted store byte afterwards.
        address = field(cpu,'game_history_selected',4)
        for delta,value in ((8,255),(10,255),(12+314,255),(12+88+4,254)):
            original = cpu.mem.r8(address+delta)
            cpu.mem.w8(address+delta,value)
            state = cpu.state()
            cpu.call('game_history_seek',{0:end>>32,1:end&0xffffffff})
            assert cpu.cpu.r_reg(0)==0 and cpu.state()==state
            cpu.mem.w8(address+delta,original)
            negatives.append('checkpoint-byte-'+str(delta))
        if end%64:
            address = symbols['game_history_buffer']+((end-1)&1023)*14
            original = cpu.mem.r16(address)
            cpu.mem.w16(address,0xffff)
            state = cpu.state()
            cpu.call('game_history_seek',{0:end>>32,1:end&0xffffffff})
            assert cpu.cpu.r_reg(0)==0 and cpu.state()==state
            cpu.mem.w16(address,original)
            negatives.append('invalid-operation-id')
        if native_guards:
            from match_core_cpu import ADAPTERS, OPTIONAL_ADAPTERS
            # Run the emitted product adapters themselves while replaying.
            # The CPU bus guard rejects every presentation/input/Paula write.
            for name in (*ADAPTERS,*OPTIONAL_ADAPTERS):
                address = symbols[name]
                raw = next(data[address-low:address-low+2] for low,data in image if low<=address<low+len(data))
                cpu.mem.w_block(address,raw)
            seek(cpu,end)
            assert cpu.state()==live and cpu.events==[], 'Native replay escaped output suppression'
            negatives.append('native-presentation-and-hardware-sinks-suppressed')
        cpu.call('game_history_resume_latest')
        assert cpu.state()==live and cursor(cpu)==end and attempts(cpu)==index
        cpu.audit_reads()
        uninterrupted.audit_reads()
        return {'operations':len(stream),'buffer_bytes':size,'metadata_bytes':symbols['game_history_state_end']-symbols['game_history_state'],
                'oldest':oldest,'latest':end,'retained_operations':end-oldest,
                'boundaries_checked':len(boundaries),'seeks':len(seek_cycles),
                'max_seek_cpu_cycles':max(seek_cycles),'max_regular_cpu_cycles':max(record_cycles),
                'max_checkpoint_cpu_cycles':max(checkpoint_cycles,default=0),
                'max_record_overhead_cpu_cycles':max(regular_overhead),
                'max_checkpoint_overhead_cpu_cycles':max(checkpoint_overhead,default=0),'stack_bytes':cpu.stack_bytes,
                'attempts':dict(Counter(kind for _,kind,_ in index)),
                'negative_controls':negatives,'low_longword_wrap':wrap,'tick_wraps':tick_wraps,'completed_episode_kinds':dict(Counter(kind for _,kind in outcomes)),
                'actual_contact_probes':cpu.visits.get(symbols['game_player_contact'],0),
                'operation_counts':dict(counts)}
