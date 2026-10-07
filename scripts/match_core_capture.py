"""Non-stopping native core observation through a fixture-only trace mailbox.

The mailbox records logical API arguments and call boundaries, never expected
state. CPU write notifications reconstruct complete state from one initial read.
No emulator control, CPU rules, physical input schedule or gameplay oracle lives
here. Callers own the native session and drive ordinary physical inputs.
"""

OPERATIONS = {
    1: ('game_core_init', 0),
    2: ('game_core_select', 2),
    3: ('game_core_sample_pads', 2),
    4: ('game_core_sample_result', 6),
    5: ('game_core_clear_inputs', 0),
    6: ('game_core_return_title', 0),
    7: ('game_round_poll', 0),
    8: ('game_tick_dispatch', 0),
}
SINKS = {0x101: 'render', 0x102: 'fields', 0x103: 'status',
         0x104: 'title', 0x105: 'period', 0x106: 'level'}


class TraceCollector:
    """Collect exact calls/state/events without stopping at every native tick.

    Protocol: write arguments (six big-endian words) then a marker word. Markers
    1..8 begin an operation; zero ends it; 0x101..0x106 identify synchronous
    output sinks. Audio sinks put logical voice and value in argument words 0/1.
    Instrumentation must preserve CPU registers/SR. All trace storage is outside
    core state and compiled only in the native observation fixture.

    The marker and argument addresses are parameters so fixture storage need not
    become a production API. ``operations`` may override the default ID mapping.
    """
    def __init__(self, symbols, initial, marker, arguments, operations=None,
                 on_row=None, initial_callback=None):
        self.symbols = symbols
        self.start, self.stop = symbols['game_core_state'], symbols['game_core_state_end']
        if len(initial) != self.stop-self.start:
            raise ValueError('Initial state size differs from declared core')
        self.initial = bytes(initial)
        self.shadow = bytearray(initial)
        self.marker, self.arguments = marker, arguments
        for low, high in ((marker, marker+2), (arguments, arguments+12)):
            if low < self.stop and high > self.start:
                raise ValueError('Trace mailbox overlaps core state')
        if marker < arguments+12 and marker+2 > arguments:
            raise ValueError('Trace marker overlaps arguments')
        self.argbytes = bytearray(12)
        self.argwritten = set()
        self.operations = dict(OPERATIONS if operations is None else operations)
        self.on_row = on_row
        self.rows, self.outside_events = [], []
        self.active = None
        self.written = set()
        self.write_count = 0
        self.callbacks = 0
        self.last_callback = initial_callback
        self.last_position = None

    def watches(self):
        ranges = [(self.start, self.stop-self.start), (self.marker, 2),
                  (self.arguments, 12)]
        if 'simulation_updates' in self.symbols:
            ranges.append((self.symbols['simulation_updates'], 2))
        return [{'addr':address, 'len':size, 'access':'write'} for address, size in ranges]

    def state(self):
        return bytes(self.shadow)

    def field(self, name, size):
        start = self.symbols[name]-self.start
        if not 0 <= start <= len(self.shadow)-size:
            raise AssertionError('Observed field outside core state: ' + name)
        return bytes(self.shadow[start:start+size])

    def _arguments(self, count):
        needed = set(range(count*2))
        if not needed <= self.argwritten:
            raise AssertionError('Trace marker lacks freshly captured logical arguments')
        return [int.from_bytes(self.argbytes[i:i+2], 'big') for i in range(0, count*2, 2)]

    def _marker(self, value, position):
        if value == 0:
            if self.active is None:
                raise AssertionError('Core operation end without start')
            row = self.active
            row.update(state=self.state().hex(), end=position,
                       elapsed_cck=position['cck']-row['start']['cck'])
            self.active = None
            self.rows.append(row)
            if self.on_row is not None:
                self.on_row(row)
        elif value in self.operations:
            if self.active is not None:
                raise AssertionError('Nested traced core operation')
            name, count = self.operations[value]
            self.active = {'operation':name, 'arguments':self._arguments(count),
                           'events':[], 'start':position, 'index':len(self.rows)}
        elif value in SINKS:
            kind = SINKS[value]
            if kind == 'render':
                event = [kind, self.field('game_scene_objects', 65).hex(),
                         self.field('field_values', 6).hex()]
            elif kind == 'fields':
                event = [kind, self.field('score_dirty', 1)[0],
                         self.field('field_values', 6).hex()]
            elif kind == 'status':
                event = [kind, self.field('field_values', 6).hex()]
            elif kind == 'title':
                event = [kind]
            else:
                event = [kind, *self._arguments(2)]
            if self.active is None:
                self.outside_events.append({'event':event, 'position':position})
            else:
                self.active['events'].append(event)
        else:
            raise AssertionError(f'Unknown core trace marker {value:#x}')
        self.argwritten.clear()

    def observe(self, message):
        params = message.get('params', {})
        if params.get('dropped_events', 0) or params.get('dropped_notifications', 0):
            raise AssertionError('Native core trace dropped observations')
        if message.get('method') != 'event.mmio':
            return
        address, size, value = params['addr'], params['size'], params['value']
        if params.get('access', 'write') != 'write':
            raise AssertionError('Unexpected read in write-only core subscription')
        data = value.to_bytes(size, 'big')
        position = dict(params['position'])
        self.last_position = position
        if self.start <= address < self.stop:
            if address+size > self.stop:
                raise AssertionError('CPU write crosses core state boundary')
            if self.active is None:
                raise AssertionError(f'Core state write outside logical API at {address:#x}')
            if 'game_core_code_begin' in self.symbols:
                pc = params['pc']
                if not self.symbols['game_core_code_begin'] <= pc < self.symbols['game_core_code_end']:
                    raise AssertionError(f'Non-core instruction writes core state at {pc:#x}')
            offset = address-self.start
            self.shadow[offset:offset+size] = data
            self.written.update(range(offset, offset+size))
            self.write_count += 1
        elif self.arguments <= address < self.arguments+12:
            offset = address-self.arguments
            if offset+size > 12:
                raise AssertionError('CPU write crosses trace argument boundary')
            self.argbytes[offset:offset+size] = data
            self.argwritten.update(range(offset, offset+size))
        elif address == self.marker:
            if size != 2:
                raise AssertionError('Trace marker must be one word')
            self._marker(value, position)
        elif address == self.symbols.get('simulation_updates'):
            if size != 2:
                raise AssertionError('Callback counter must be one word')
            if self.last_callback is not None and value != (self.last_callback+1) & 0xffff:
                raise AssertionError('Native callback discontinuity')
            self.last_callback = value
            self.callbacks += 1
        else:
            raise AssertionError(f'Unexpected subscribed core trace write {address:#x}')

    def finish(self, actual=None):
        """Verify a paused boundary; optionally cross-check one native memory read."""
        if self.active is not None:
            raise AssertionError('Capture ended inside a logical core operation')
        if actual is not None and bytes(actual) != self.state():
            raise AssertionError('Reconstructed state differs from direct native read')
        return {'operations':len(self.rows), 'callbacks':self.callbacks,
                'written_bytes':len(self.written), 'writes':self.write_count,
                'outside_sink_events':len(self.outside_events)}
