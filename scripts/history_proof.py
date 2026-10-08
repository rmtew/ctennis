"""Bounded-store proofs over the actual 68000 logical API, never tennis rules."""
from collections import Counter, defaultdict
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


def cycle_distribution(values):
    ordered = sorted(values)
    return dict(samples=len(values), minimum_cpu_cycles=ordered[0],
                median_cpu_cycles=(ordered[(len(values)-1)//2]+ordered[len(values)//2])/2,
                p95_cpu_cycles=ordered[(95*len(values)+99)//100-1],
                maximum_cpu_cycles=ordered[-1])


def exercise(executable, rows=None, ticks=1536, poison=0xa5, base=0x10000, wrap=False, native_guards=False, stream_override=None):
    image,symbols = load_image(executable,base)
    offset = (1<<32)-512 if wrap else 0
    if stream_override is not None:
        stream = stream_override
    elif rows is None:
        stream = [('game_core_select',[0,0xace1,0])]
        for tick in range(ticks):
            # Controls are fixed inputs only. Outcomes come from 68000.
            stream.extend([('game_round_poll',[]),
                ('game_core_sample_pads',[(0x10 if tick%64>=8 else 0) | (8 if tick%96<48 else 4),0]),
                ('game_core_sample_result',[0,0,0,0,0,0]),('game_tick_dispatch',[])])
    else:
        assert rows[0]['operation']=='game_core_init'
        stream = [(row['operation'],row['arguments']) for row in rows[1:]]
    expected, baseline = {}, {}
    # machine68k has one active CPU context; independent executions are
    # sequential, freshly initialized, with no intermediate state injection.
    with Core(image,symbols,poison=poison,readonly=READONLY) as uninterrupted:
        uninterrupted.call_logical('game_core_init',[])
        expected[offset] = (uninterrupted.state(),[])
        for ordinal,(name,args) in enumerate(stream,1):
            uninterrupted.clear_events()
            cycles = uninterrupted.call_logical(name,args)
            expected[offset+ordinal] = (uninterrupted.state(),list(uninterrupted.events))
            baseline[ordinal] = (cycles,[uninterrupted.cpu.r_reg(r) for r in range(15)],uninterrupted.cpu.r_sr())
        uninterrupted.audit_reads()
    with Core(image,symbols,poison=poison,readonly=READONLY) as cpu:
        cpu.call_logical('game_core_init',[])
        canonical = cpu.state()
        expected_size = symbols['game_history_buffer_end']-symbols['game_history_buffer']
        for pointer,length in ((0,expected_size),(symbols['game_history_buffer']+1,expected_size),
                               (symbols['game_history_buffer'],expected_size-2),
                               (symbols['game_history_buffer'],expected_size+2),(0xfffffffe,expected_size)):
            cpu.call('game_history_attach',{8:pointer,0:length})
            assert cpu.cpu.r_reg(0)==0 and cpu.state()==canonical and field(cpu,'game_history_mode',1)==0
        size = attach(cpu)
        # Measure the actual copy independently into the owned interruption
        # scratch area. Canonical/live recording state is never injected.
        copy_cycles = cpu.call('game_history_copy_state',
            {8:symbols['game_history_buffer']+size-318,9:symbols['game_core_state']})
        assert cpu.state()==canonical and cursor(cpu)==0
        if wrap:
            # One-time history-only fixture origin, before the first operation.
            # Canonical state is untouched and no later expected state injected.
            cpu.mem.w_block(symbols['game_history_cursor'],offset.to_bytes(8,'big'))
            cpu.mem.w_block(symbols['game_history_oldest'],offset.to_bytes(8,'big'))
            cpu.mem.w_block(symbols['game_history_buffer']+14336,offset.to_bytes(8,'big'))
        outputs, record_cycles, checkpoint_cycles = {}, [], []
        regular_overhead, checkpoint_overhead = [], []
        overhead_groups = defaultdict(list)
        prior_pads = None
        counts = Counter()
        outcomes = set()
        tick_wraps = 0
        last_tick = field(cpu,'game_tick',1)
        for ordinal,(name,args) in enumerate(stream,1):
            previous_oldest = cursor(cpu,'game_history_oldest')
            cpu.clear_events()
            cycles = cpu.call_logical(name,args)
            baseline_cycles, registers, sr = baseline[ordinal]
            assert (cpu.state(),cpu.events)==expected[offset+ordinal], ('recording alters core',name)
            assert [cpu.cpu.r_reg(r) for r in range(15)]==registers and cpu.cpu.r_sr()==sr, ('recording alters CPU ABI',name)
            boundary = cursor(cpu)
            overhead = cycles-baseline_cycles
            checkpoint = boundary%64==0
            (checkpoint_overhead if checkpoint else regular_overhead).append(overhead)
            overhead_groups['all/'+name].append(overhead)
            overhead_groups['checkpoint' if checkpoint else 'regular'].append(overhead)
            if checkpoint:
                overhead_groups['checkpoint/'+name].append(overhead)
                overhead_groups['checkpoint-eviction' if cursor(cpu,'game_history_oldest')!=previous_oldest
                                else 'checkpoint-before-eviction'].append(overhead)
            if name=='game_core_sample_pads':
                if args!=prior_pads:
                    overhead_groups['changed-pad-input'].append(overhead)
                prior_pads = list(args)
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
        frozen_calls = [('game_core_init',[]),('game_core_select',[1,65535,0]),
            ('game_core_sample_pads',[0xffff,0xffff]),('game_core_sample_result',[65535]*6),
            ('game_core_clear_inputs',[]),('game_core_return_title',[]),
            ('game_round_poll',[]),('game_tick_dispatch',[]),('game_core_latch_actions',[])]
        for name,args in frozen_calls:
            count = cpu.logical_calls
            registers = [((count*65537+r*0x1010101)^0x965aa569^cpu.context_seed)&0xffffffff for r in range(15)]
            for r,value in enumerate(args):
                registers[r] = (registers[r]&0xffff0000)|value
            sr = 0x2700|((count^cpu.context_seed)&31)
            cpu.clear_events()
            cpu.call_logical(name,args)
            assert cpu.state()==live and cpu.events==[] and cursor(cpu)==end
            assert [cpu.cpu.r_reg(r) for r in range(15)]==registers and cpu.cpu.r_sr()==sr
            assert bytes(cpu.mem.r_block(symbols['game_history_buffer'],size-318))==before
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
        seek(cpu,end)
        selected_checkpoint = field(cpu,'game_history_selected',4)
        seek(cpu,oldest)
        working = cpu.state()
        working_cursor = cursor(cpu,'game_history_position')
        assert working_cursor==oldest
        def rejected(target):
            cpu.clear_events()
            cpu.call('game_history_seek',{0:(target>>32)&0xffffffff,1:target&0xffffffff})
            assert cpu.cpu.r_reg(0)==0 and cpu.state()==working and cpu.events==[]
            assert cursor(cpu,'game_history_position')==working_cursor
            assert cursor(cpu)==end and cursor(cpu,'game_history_oldest')==oldest
            assert bytes(cpu.mem.r_block(symbols['game_history_buffer'],size-318))==before
        for target in (oldest-1,end+1):
            rejected(target)
            negatives.append('out-of-range-'+str(target))
        # Corrupt a requested origin while the selected working state is older
        # than the live backup. Failure cannot silently restore the live state.
        address = selected_checkpoint
        for delta,value in ((8,255),(10,255),(12+314,255),(12+88+4,254)):
            original = cpu.mem.r8(address+delta)
            cpu.mem.w8(address+delta,value)
            saved_before = before
            before = bytes(cpu.mem.r_block(symbols['game_history_buffer'],size-318))
            rejected(end)
            cpu.mem.w8(address+delta,original)
            before = saved_before
            negatives.append('checkpoint-byte-'+str(delta))
        invalid_target = end if end%64 else end-1
        if invalid_target>oldest:
            address = symbols['game_history_buffer']+((invalid_target-1)&1023)*14
            original = cpu.mem.r16(address)
            cpu.mem.w16(address,0xffff)
            saved_before = before
            before = bytes(cpu.mem.r_block(symbols['game_history_buffer'],size-318))
            rejected(invalid_target)
            cpu.mem.w16(address,original)
            before = saved_before
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
        import hashlib
        ordered_records = b''.join(bytes(cpu.mem.r_block(symbols['game_history_buffer']+(n&1023)*14,14)) for n in range(oldest,end))
        return {'record_arguments_sha256':hashlib.sha256(ordered_records).hexdigest(),'operations':len(stream),'buffer_bytes':size,'metadata_bytes':symbols['game_history_state_end']-symbols['game_history_state'],
                'canonical_copy_cpu_cycles':copy_cycles,
                'record_overhead_distributions':{name:cycle_distribution(values) for name,values in overhead_groups.items()},
                'oldest':oldest,'latest':end,'retained_operations':end-oldest,
                'boundaries_checked':len(boundaries),'seeks':len(seek_cycles),
                'max_seek_cpu_cycles':max(seek_cycles),'max_regular_cpu_cycles':max(record_cycles),
                'max_checkpoint_cpu_cycles':max(checkpoint_cycles,default=0),
                'max_record_overhead_cpu_cycles':max(regular_overhead),
                'max_checkpoint_overhead_cpu_cycles':max(checkpoint_overhead,default=0),'stack_bytes':cpu.stack_bytes,
                'attempts':dict(Counter(kind for _,kind,_ in index)),
                'negative_controls':negatives,'frozen_operations_checked':len(frozen_calls),'register_sr_equivalence_operations':len(stream),'failure_preserves_older_position':working_cursor==oldest,'low_longword_wrap':wrap,'tick_wraps':tick_wraps,'completed_episode_kinds':dict(Counter(kind for _,kind in outcomes)),
                'actual_contact_probes':cpu.visits.get(symbols['game_player_contact'],0),
                'operation_counts':dict(counts)}


def logical_api(executable):
    stream = [('game_core_select',[0,0x3037,0]),
        ('game_core_sample_pads',[0x10,0x20]),('game_core_latch_actions',[]),
        ('game_core_clear_inputs',[]),('game_core_sample_result',[0,0,0,0,0,0]),
        ('game_round_poll',[]),('game_tick_dispatch',[]),
        ('game_core_return_title',[]),('game_core_init',[]),
        ('game_core_select',[1,0xffff,0]),('game_core_sample_pads',[0x30,0x30]),
        ('game_core_sample_result',[1,1,0,0,0,0]),('game_tick_dispatch',[]),
        ('game_core_sample_pads',[0,0]),('game_core_latch_actions',[]),
        ('game_core_clear_inputs',[]),('game_round_poll',[]),('game_tick_dispatch',[])]
    return exercise(executable,stream_override=stream)


def pending_eviction(executable, verify_seek=True):
    image,symbols = load_image(executable)
    stream = []
    with Core(image,symbols,readonly=READONLY) as cpu:
        cpu.call_logical('game_core_init',[])
        attach(cpu)
        def call(name,args):
            stream.append((name,args))
            cpu.clear_events()
            cpu.call_logical(name,args)
            attempts(cpu)
        call('game_core_select',[0,0xace1,0])
        def update(tick):
            call('game_round_poll',[])
            call('game_core_sample_pads',[(0x10 if tick%64>=8 else 0)|(8 if tick%96<48 else 4),0])
            call('game_core_sample_result',[0,0,0,0,0,0])
            call('game_tick_dispatch',[])
        for tick in range(1024):
            update(tick)
            if field(cpu,'game_history_probe_active',1):
                break
        else:
            raise AssertionError('Actual incoming human episode absent')
        origin = next(n for n,kind,_ in attempts(cpu) if kind==0)
        pending_state = cpu.state()
        for _ in range(1100):
            call('game_round_poll',[])
            assert cpu.state()==pending_state, 'Playing poll advances incoming state'
        assert cursor(cpu,'game_history_oldest')>origin
        assert field(cpu,'game_history_probe_active',1)==0
        assert all(n!=origin for n,_,_ in attempts(cpu))
        eviction_oldest = cursor(cpu,'game_history_oldest')
        for later in range(tick+1,tick+513):
            update(later)
            completed = [(n,kind) for n,kind,_ in attempts(cpu) if kind in (1,2)]
            assert all(n>=eviction_oldest for n,_ in completed)
            if completed:
                new_origin, outcome = completed[-1]
                break
        else:
            raise AssertionError('Post-eviction actual contact/miss outcome absent')
        cpu.audit_reads()
    extent = exercise(executable,stream_override=stream) if verify_seek else {'operations':len(stream),'development_phase_check_only':True}
    return dict(extent,
                evicted_pending_origin=origin,eviction_oldest=eviction_oldest,
                pending_canceled=True,completed_new_origin=new_origin,
                completed_new_episode_kind=outcome)
