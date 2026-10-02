"""Collect one complete observed 68000 long store, independent of bus order."""


class LongwordObserver:
    def __init__(self):
        self.data = bytearray(4)
        self.seen = set()
        self.pc = None

    def write(self, offset, value, size, pc):
        if not 0 <= offset < offset+size <= 4:
            raise ValueError('Long store outside observed field')
        parts = set(range(offset, offset+size))
        if self.seen and (pc != self.pc or self.seen & parts):
            raise ValueError('Incomplete long store before next mutation')
        self.pc = pc
        self.data[offset:offset+size] = value.to_bytes(size, 'big')
        self.seen.update(parts)
        if len(self.seen) != 4:
            return None
        self.seen.clear()
        return int.from_bytes(self.data, 'big')
