"""Isolated execution of the product's actual 68000 match core.

Adapters are synchronous observation sinks, never a gameplay model. Cycle counts
include trap dispatch and exclude native presentation/physical audio work; they
are CPU measurements, not Amiga elapsed-time bounds.
"""
from importlib.metadata import version

ADAPTERS = ('game_render_sprites', 'game_scene_present_fields',
            'game_core_title_requested', 'game_audio_write_period',
            'game_audio_write_level')
OPTIONAL_ADAPTERS = ('game_core_status_present',)
RAM_SIZE = 0x200000
STACK_BASE, STACK_TOP = 0x1f0000, 0x1ffff0
RETURN_TRAP = 0x100000


class Core:
    """Load shared code/tables, poison working memory, and guard every CPU access.

    ``image`` contains (address, bytes) pairs. ``initial`` optionally supplies one
    complete contiguous state image. Omit it to test the real initializer against
    poisoned state. ``readonly`` maps symbol names (or addresses) to byte lengths;
    audit_reads permits only those tables, owned state, and executed code bytes.
    """
    def __init__(self, image, symbols, initial=None, poison=0xa5, readonly=None):
        import machine68k as m
        if version('machine68k') != '0.4.1':
            raise ValueError('Use pinned machine68k 0.4.1')
        if not 0 <= poison <= 255:
            raise ValueError('Poison must be one byte')
        self.symbols = symbols
        self.start, self.stop = symbols['game_core_state'], symbols['game_core_state_end']
        if not 0 <= self.start < self.stop <= RAM_SIZE:
            raise ValueError('Invalid core state bounds')
        if (self.start < STACK_TOP + 4 and self.stop > STACK_BASE
                or self.start <= RETURN_TRAP < self.stop):
            raise ValueError('Core state overlaps harness stack or return trap')
        self.machine = m.Machine(m.CPUType.M68000, RAM_SIZE // 1024)
        self.mem, self.cpu = self.machine.mem, self.machine.cpu
        self.traps = []
        self.regions = []
        self.readonly = dict(readonly or {})
        self.events, self.writes, self.reads = [], set(), set()
        self.instructions, self.pcs, self.visits = set(), set(), {}
        self.stack_low = STACK_TOP
        self.total_cycles = self.last_cycles = 0
        self.mem.w_block(0, bytes([poison]) * RAM_SIZE)
        for address, data in image:
            end = address + len(data)
            if not 0 <= address < end <= RAM_SIZE:
                raise ValueError('Invalid loaded image region')
            if address < STACK_TOP + 4 and end > STACK_BASE or address <= RETURN_TRAP < end:
                raise ValueError('Image overlaps harness stack or return trap')
            if any(address < high and end > low for low, high in self.regions):
                raise ValueError('Overlapping image regions')
            self.mem.w_block(address, bytes(data))
            self.regions.append((address, end))
        if not any(low <= self.start and self.stop <= high for low, high in self.regions):
            raise ValueError('Core state must be inside one loaded image region')
        # Loaded BSS/data must not accidentally initialize owned mutable state.
        self.mem.w_block(self.start, bytes([poison]) * (self.stop-self.start))
        if initial is not None:
            if len(initial) != self.stop-self.start:
                raise ValueError('Initial image must contain the complete core state')
            self.mem.w_block(self.start, bytes(initial))
        self.end = self.machine.create_execute_end('return')
        self._trap(RETURN_TRAP, lambda opcode, pc: self.end)
        for name in (*ADAPTERS, *(name for name in OPTIONAL_ADAPTERS if name in symbols)):
            address = symbols[name]
            if not any(low <= address and address+2 <= high for low, high in self.regions):
                raise ValueError('Adapter outside loaded image: ' + name)
            self._trap(address, self._adapter(name))
        self.cpu.set_instr_hook_callback(self.instruction)
        self.mem.set_invalid_func(self.invalid)
        self.mem.set_trace_func(self.trace)
        self.mem.set_trace_mode(True)
        self.cpu.w_sr(0x2700)
        for register in range(15):
            self.cpu.w_reg(register, poison * 0x01010101)

    def _trap(self, address, callback):
        trap = self.machine.traps.alloc(callback)
        self.traps.append(trap)
        self.mem.w16(address, 0xa000 | trap)

    def _adapter(self, name):
        def invoke(opcode, pc):
            def read(symbol, size):
                address = self.symbols[symbol]
                if not self.start <= address <= self.stop-size:
                    raise AssertionError('Adapter observes out-of-state data: ' + symbol)
                return bytes(self.mem.r_block(address, size))
            if name == 'game_render_sprites':
                self.events.append(['render', read('game_scene_objects', 65).hex(),
                                    read('field_values', 6).hex()])
            elif name == 'game_scene_present_fields':
                self.events.append(['fields', read('score_dirty', 1)[0],
                                    read('field_values', 6).hex()])
            elif name == 'game_core_status_present':
                self.events.append(['status', read('field_values', 6).hex()])
            elif name == 'game_core_title_requested':
                self.events.append(['title'])
            else:
                kind = 'period' if name == 'game_audio_write_period' else 'level'
                self.events.append([kind, self.cpu.r_reg(7) & 0xffff,
                                    self.cpu.r_reg(0) & 0xffff])
            # Emulate only the adapter's RTS. No gameplay registers are changed.
            sp = self.cpu.r_sp()
            if not STACK_BASE <= sp <= STACK_TOP:
                raise AssertionError('Adapter return outside stack')
            target = self.mem.cpu_r32(sp)
            self.cpu.w_sp(sp + 4)
            self.cpu.w_pc(target)
        return invoke

    def instruction(self, pc):
        if pc not in self.pcs:
            if pc != RETURN_TRAP and not any(low <= pc and pc+2 <= high for low, high in self.regions):
                raise AssertionError(f'Execution outside loaded code: {pc:#x}')
            self.pcs.add(pc)
            size, _ = self.cpu.disassemble(pc)
            self.instructions.update(range(pc, pc + size))
        self.visits[pc] = self.visits.get(pc, 0) + 1

    def invalid(self, mode, width, address):
        raise AssertionError(f'Forbidden bus access {mode}{1 << width} at {address:#x}')

    def trace(self, mode, width, address, value):
        size = 1 << width
        if STACK_BASE <= address and address + size <= STACK_TOP + 4:
            self.stack_low = min(self.stack_low, address)
            return
        if address == RETURN_TRAP:
            if mode == 'R' and size == 2:
                return
            raise AssertionError(f'Forbidden return-trap access {mode}{size} at {address:#x}')
        if mode == 'W':
            if not self.start <= address <= self.stop-size:
                raise AssertionError(f'Out-of-state write {address:#x}')
            self.writes.update(range(address, address+size))
        else:
            if not any(low <= address and address+size <= high for low, high in self.regions):
                raise AssertionError(f'Out-of-image read {address:#x}')
            self.reads.update(range(address, address+size))

    def call(self, name, registers=None, max_cycles=2000000):
        """Call an actual entry; preserve accumulated events until clear_events()."""
        for register, value in (registers or {}).items():
            if not 0 <= register < 15:
                raise ValueError('Only D0-D7/A0-A6 arguments are supported')
            self.cpu.w_reg(register, value)
        self.cpu.w_sp(STACK_TOP)
        self.mem.w32(STACK_TOP, RETURN_TRAP)
        self.cpu.w_pc(self.symbols[name])
        result = self.machine.execute(max_cycles)
        if result.result is not self.end:
            raise AssertionError('Unbounded call: ' + name)
        if self.cpu.r_sp() != STACK_TOP + 4:
            raise AssertionError('Unbalanced stack: ' + name)
        self.last_cycles = result.cycles
        self.total_cycles += result.cycles
        return result.cycles

    def state(self):
        # AV_NEXT is a product-owned table offset, so no address normalization.
        return bytes(self.mem.r_block(self.start, self.stop-self.start))

    def clear_events(self):
        self.events.clear()

    @property
    def stack_bytes(self):
        return STACK_TOP + 4 - self.stack_low

    def audit_reads(self):
        allowed = set(range(self.start, self.stop)) | self.instructions
        for symbol, size in self.readonly.items():
            address = self.symbols[symbol] if isinstance(symbol, str) else symbol
            allowed.update(range(address, address+size))
        unknown = self.reads - allowed
        if unknown:
            raise AssertionError(f'Undeclared data read: {sorted(unknown)[:10]}')

    def close(self):
        for trap in self.traps:
            self.machine.traps.free(trap)
        self.traps.clear()
        self.machine.cleanup()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
