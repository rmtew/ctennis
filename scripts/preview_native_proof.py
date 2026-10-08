"""Emitted native sinks: setup traps end before the frozen proof begins."""
from history_proof import field
from match_core_cpu import ADAPTERS, OPTIONAL_ADAPTERS


def native_entries(cpu,image):
    entries={}
    for name in (*ADAPTERS,*(n for n in OPTIONAL_ADAPTERS if n in cpu.symbols)):
        address=cpu.symbols[name]
        raw=next(data[address-low:address-low+2] for low,data in image if low<=address and address+2<=low+len(data))
        cpu.mem.w_block(address,raw)
        entries[name]=raw
    original=cpu.instruction
    cpu.native_semantic_events=[]
    def observe(pc):
        original(pc)
        for name in entries:
            if pc==cpu.symbols[name]:
                registers=[cpu.cpu.r_reg(r) for r in range(15)]
                sr=cpu.cpu.r_sr();sp=cpu.cpu.r_sp();before_pc=cpu.cpu.r_pc()
                # Frozen external seek/reference intents belong to an isolated
                # observation ledger, never the interrupted live output queue.
                if field(cpu,'game_preview_active',1):cpu.observe_adapter(name)
                else:
                    live=cpu.events
                    try:
                        cpu.events=cpu.native_semantic_events
                        cpu.observe_adapter(name)
                    finally:cpu.events=live
                assert registers==[cpu.cpu.r_reg(r) for r in range(15)]
                assert (sr,sp,before_pc)==(cpu.cpu.r_sr(),cpu.cpu.r_sp(),cpu.cpu.r_pc())
    # execute() installs its own instruction observer, so extend the instance's
    # underlying observer rather than only the machine callback.
    cpu.instruction=observe
    cpu.cpu.set_instr_hook_callback(observe)
    original_trace=cpu.trace
    def guard(mode,width,address,value):
        if (mode=='W' and field(cpu,'game_history_mode',1)==2
                and address<cpu.symbols['game_history_buffer_end']
                and address+(1<<width)>cpu.symbols['game_history_buffer']):
            raise AssertionError('Emitted frozen sink/reference writes history or live backup')
        original_trace(mode,width,address,value)
    cpu.mem.set_trace_func(guard)
    cpu.native_entries=entries
    return entries


def assert_native_entries(cpu):
    for name,raw in getattr(cpu,'native_entries',{}).items():
        assert bytes(cpu.mem.r_block(cpu.symbols[name],2))==raw, 'Native sink adapter trap restored after proof began'


def outside_canonical(cpu):
    pieces=[]
    for low,high in cpu.regions:
        if low<cpu.start:pieces.append(bytes(cpu.mem.r_block(low,min(high,cpu.start)-low)))
        if high>cpu.stop:pieces.append(bytes(cpu.mem.r_block(max(low,cpu.stop),high-max(low,cpu.stop))))
    return pieces
