"""Read-only emitted call/RTS stack bus timing; never a gameplay oracle."""
import re


def instruction_map(listing, segments, read):
    calls, returns = {}, set()
    for hunk, offset, encoded, mnemonic, operand in re.findall(
            r'^(\d\d):([\da-fA-F]{8})\s+([\dA-F]+)\s+[^\n]*?:\s*(bsr|jsr|rts)\s*([^\n]*)$',
            listing, re.M | re.I):
        address = segments[int(hunk)]['start'] + int(offset, 16)
        code = bytes.fromhex(encoded)
        opcode = int.from_bytes(code[:2], 'big')
        assert read(address, 2) == code[:2], 'Loaded call/return opcode differs from listing'
        if mnemonic.lower() == 'rts':
            assert opcode == 0x4e75 and len(code) == 2
            returns.add(address)
        else:
            assert opcode & 0xff00 == 0x6100 or opcode & 0xffc0 == 0x4e80
            assert len(code) in (2, 4, 6), 'Non-68000 call encoding'
            calls[address] = dict(return_pc=address+len(code), opcode=code.hex(),
                                  callee=operand.split(';')[0].strip())
    assert calls and returns
    return calls, returns


def category(callee):
    if callee.startswith('game_preview_') and not callee.endswith('_body'):
        return 'public-preview'
    if callee.endswith('_body'):
        return 'core-body'
    if any(word in callee for word in ('copy', 'restore', 'release_selected', 'save_working')):
        return 'copy-restore'
    if any(word in callee for word in ('guard', 'unchanged', 'validate', 'admitted', 'remaining', 'read_sim_timer')):
        return 'guard-admission'
    return 'other'


class StackTiming:
    def __init__(self, calls, returns, bottom, top):
        self.calls, self.returns = calls, returns
        self.bottom, self.top = bottom, top
        self.pending = None
        self.stack, self.rows = [], []
        self.notifications = self.reads = self.writes = 0

    def observe(self, row):
        a, size, value, pc = (row[k] for k in ('addr', 'size', 'value', 'pc'))
        assert row['access'] in ('read', 'write')
        if not (a < self.top and a+size > self.bottom):
            return
        assert self.bottom <= a < a+size <= self.top
        self.notifications += 1
        position = dict(row['position'])
        if row['access'] == 'write':
            self.writes += 1
            if pc not in self.calls:
                return  # Saves/exception frames are not invented call entries.
            call = self.calls[pc]
            expected = call['return_pc'].to_bytes(4, 'big')
            if self.pending is None:
                candidates = [a-i for i in range(5-size)
                              if expected[i:i+size] == value.to_bytes(size, 'big')
                              and (a-i) % 2 == 0]
                assert len(candidates) == 1, 'Ambiguous/mismatched emitted call return slot'
                self.pending = dict(pc=pc, slot=candidates[0], data=bytearray(4),
                                    seen=set(), entry=position)
            pending = self.pending
            assert pending['pc'] == pc, 'Incomplete call entry interrupted by another call'
            offset = a-pending['slot']
            assert 0 <= offset < offset+size <= 4
            assert not pending['seen'].intersection(range(offset, offset+size))
            pending['data'][offset:offset+size] = value.to_bytes(size, 'big')
            pending['seen'].update(range(offset, offset+size))
            if len(pending['seen']) == 4:
                assert bytes(pending['data']) == expected
                if self.stack:
                    assert pending['slot'] < self.stack[-1]['slot'], 'Non-LIFO call stack'
                self.stack.append(dict(call, entry_pc=pc, slot=pending['slot'],
                    entry= pending['entry'], entry_store_complete=position, reads={},
                    depth=len(self.stack), children=[],
                    caller=self.stack[-1]['callee'] if self.stack else None))
                self.pending = None
        else:
            self.reads += 1
            if pc not in self.returns:
                return  # MOVEM dummy reads / restores never count as RTS.
            assert self.stack, 'RTS without an observed emitted call'
            frame = self.stack[-1]
            offset = a-frame['slot']
            assert 0 <= offset < offset+size <= 4, 'RTS reads a different return slot'
            data = value.to_bytes(size, 'big')
            expected = frame['return_pc'].to_bytes(4, 'big')
            assert data == expected[offset:offset+size], 'RTS return value mismatch'
            for i, byte in enumerate(data, offset):
                assert i not in frame['reads'], 'Duplicate RTS return-slot read'
                frame['reads'][i] = byte
            if len(frame['reads']) == 4:
                self.stack.pop()
                frame.pop('reads')
                frame.update(exit_pc=pc, exit=position,
                             elapsed_bus_cck=position['cck']-frame['entry']['cck'])
                children = frame.pop('children')
                assert all(frame['entry']['cck'] <= child[0] <= child[1] <= position['cck']
                           for child in children)
                for left, right in zip(children, children[1:]):
                    assert left[1] <= right[0], 'Overlapping direct-child spans'
                frame['exclusive_bus_cck'] = frame['elapsed_bus_cck']-sum(b-a for a,b in children)
                frame['child_spans'] = children
                frame['category'] = category(frame['callee'])
                assert frame['exclusive_bus_cck'] >= 0
                self.rows.append(frame)
                if self.stack:
                    self.stack[-1]['children'].append([frame['entry']['cck'], position['cck']])

    def result(self):
        assert self.pending is None, 'Partial emitted call entry at completed boundary'
        assert self.rows and self.reads and self.writes
        # An enclosing main-loop call can remain open at simulation_update entry.
        # It is disclosed and omitted; completed descendants remain exact bus spans.
        return dict(protocol='emitted-call-stack-stores-and-matched-emitted-rts-stack-reads',
            calls=self.rows, open_enclosing_calls=[{k:v for k,v in f.items() if k != 'reads'}
                                                  for f in self.stack],
            stack_reads=self.reads, stack_writes=self.writes,
            stack_notifications=self.notifications,
            uncertainty='First return-address store through final RTS return-address read only; '
                        'instruction pre-store/post-read CPU tails and IRQ work are not isolated. '
                        'Exclusive spans subtract completed direct children, not overlapping inclusive totals.')


class LatencyObserver:
    """Keep read probes entirely out of the write-only callback/surface observer."""
    def __init__(self, callbacks, timing):
        self.callbacks, self.timing = callbacks, timing
        self.dropped = 0
        self.timer_reads = []

    def observe(self, message):
        row = message.get('params', {})
        if message.get('method', '').startswith('event.'):
            assert type(row.get('dropped_notifications')) is int
            assert row['dropped_notifications'] == 0
            for name in ('dropped_events', 'dropped_accesses', 'queue_overflow',
                         'access_overflow', 'notification_overflow', 'overflow'):
                assert row.get(name, 0) == 0, ('Latency probe lost accesses', name)
        if message.get('method') == 'event.mmio':
            assert row['access'] in ('read', 'write')
            if row['access']=='read' and row['addr'] in (0xbfd400,0xbfd500,0xbfd600,0xbfd700):
                assert row['size']==1
                self.timer_reads.append(dict(row, timer_parameters={n:self.callbacks.state[n]
                    for n in ('last_timer_count','simulation_phase','simulation_interval')}))
            self.timing.observe(row)
            if row['access'] == 'read':
                return
        self.callbacks.observe(message)
