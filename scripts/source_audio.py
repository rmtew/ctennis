"""Three-record PSG command interpreter from G-1009 ROM 17C5-19BB.

This runs on RAM C000-C0FF and the identified 8 KB ROM image. It returns the
bytes the source writes to PSG port 7F; it does not synthesize audio samples.
"""

from ball_math import u8


AUDIO_TEMPLATE = bytes.fromhex("20 00 00 07 00 02 10 00 00 10 00 00")


def _word(ram: bytearray, low: int) -> int:
    return ram[low] | (ram[low + 1] << 8)


def _read_rom(rom: bytes, address: int) -> int:
    if not 0 <= address < len(rom):
        raise ValueError(f"Audio ROM read outside image: {address:04X}")
    return rom[address]


def _fetch_199c(ram: bytearray, rom: bytes, base: int) -> tuple[int, bool]:
    """Return (byte, stopped/carry). Current index advances before the read."""
    stop, index = ram[base + 3], ram[base + 4]
    if stop == index:
        return stop, True
    new_index = u8(index + 1)
    if new_index >= ram[base + 2]:
        new_index = 0
    ram[base + 4] = new_index
    address = _word(ram, base) + index
    return _read_rom(rom, address), False


def _psg_latch(channel: int, value: int, *, volume: bool) -> int:
    return (0x90 if volume else 0x80) | ((channel & 3) << 5) | (value & 0x0F)


def _pitch_1944(ram: bytearray, rom: bytes, channel: int, note: int, shift: int) -> list[int]:
    index = u8(ram[0x84] + note)
    if index >= 0x0C:
        shift = u8(shift + 1)
        index = u8(index - 0x0C)
    location = 0x18DA + 2 * index
    word = (_read_rom(rom, location) << 8) | _read_rom(rom, location + 1)
    word >>= shift & 7
    return [_psg_latch(channel, (word & 0xFF) >> 4, volume=False), word >> 8]


def _volume_and_duration(
    ram: bytearray, rom: bytes, base: int, channel: int, command: int, *, rest: bool
) -> list[int]:
    volume = 0x0F if rest or ram[base + 10] else ram[base + 6]
    emitted = [_psg_latch(channel, volume, volume=True)]
    duration = ram[base + 8]
    if command & 0x80:
        duration, _ = _fetch_199c(ram, rom, base)
    ram[base + 12] = duration
    scaled = (duration * ram[base + 5]) & 0xFFFF
    ram[base + 13] = u8((scaled >> 3) + 1)
    ram[base + 11] = 0x10 if rest else 0
    return emitted


def _command_183a(
    ram: bytearray, rom: bytes, base: int, channel: int, command: int
) -> tuple[bool, list[int]]:
    """Return (note_or_rest_completed, PSG bytes); otherwise fetch again."""
    handler = (command >> 4) & 7
    low = command & 0x0F
    if handler == 0:
        if low == 0:
            return True, _volume_and_duration(ram, rom, base, channel, command, rest=True)
        pitch = _pitch_1944(ram, rom, channel, low - 1, ram[base + 7])
        return True, pitch + _volume_and_duration(ram, rom, base, channel, command, rest=False)
    if handler == 1:
        argument, _ = _fetch_199c(ram, rom, base)
        note = u8((argument & 0x7F) - 1)
        shift, pitch_index = divmod(note, 12)
        pitch = _pitch_1944(ram, rom, channel, pitch_index, shift)
        return True, pitch + _volume_and_duration(ram, rom, base, channel, argument, rest=False)
    if handler == 2:
        if command & 0x80:
            ram[0x84] = low
        else:
            ram[base + 7] = command & 7
    elif handler == 3:
        ram[base + 6] = 0x0F - low
    elif handler == 4:
        selector = command & 7
        address = _word(ram, 0x80) + 8 * (selector - 1) if selector else 0
        ram[base + 9], ram[base + 10] = address & 0xFF, (address >> 8) & 0xFF
    elif handler == 5:
        ram[base + 5] = low
    elif handler == 6:
        ram[base + 8], _ = _fetch_199c(ram, rom, base)
    elif handler == 7:
        ram[0x82], _ = _fetch_199c(ram, rom, base)
    return False, []


def _envelope_1807(ram: bytearray, rom: bytes, base: int, channel: int) -> list[int]:
    old_step = ram[base + 11]
    if old_step == 0x10:
        return []
    ram[base + 13] = u8(ram[base + 13] - 1)
    if ram[base + 13] == 0:
        ram[base + 11] = 8
    elif old_step == 8:
        return []
    step = ram[base + 11]
    address = _word(ram, base + 9) + (step >> 1)
    envelope_byte = _read_rom(rom, address)
    volume = (envelope_byte & 0x0F) if step & 1 else (envelope_byte >> 4)
    ram[base + 11] = u8(step + 1)
    return [_psg_latch(channel, volume, volume=True)]


def audio_tick_17c5(ram: bytearray, rom: bytes) -> tuple[int, ...]:
    """Run one due audio tick and return ordered PSG-port bytes."""
    if len(rom) != 8192:
        raise ValueError("Expected the identified 8 KB ROM bytes")
    psg: list[int] = []
    for channel in (2, 1, 0):
        base = 0x85 + 14 * channel
        if ram[base + 12]:
            ram[base + 12] = u8(ram[base + 12] - 1)
            if ram[base + 12] == 0:
                psg.append(_psg_latch(channel, 0x0F, volume=True))
        if ram[base + 12] == 0:
            for _ in range(256):
                command, stopped = _fetch_199c(ram, rom, base)
                if stopped:
                    break
                complete, emitted = _command_183a(ram, rom, base, channel, command)
                psg.extend(emitted)
                if complete:
                    break
            else:
                raise RuntimeError("Audio setup commands did not reach note/rest or stop")
        if ram[base + 10]:
            psg.extend(_envelope_1807(ram, rom, base, channel))
        elif ram[base + 12]:
            ram[base + 13] = u8(ram[base + 13] - 1)
            if ram[base + 13] == 0:
                psg.append(_psg_latch(channel, 0x0F, volume=True))
    ram[0x83] = ram[0x82]
    return tuple(psg)


def audio_initialize_1787(ram: bytearray) -> tuple[int, ...]:
    """Initialize three records and return the initial PSG mute bytes."""
    ram[0x80], ram[0x81] = 0xBC, 0x19
    ram[0x82], ram[0x83], ram[0x84] = 2, 2, 0
    for channel in range(3):
        base = 0x85 + 14 * channel
        pointer = 0xC0AF + 0x20 * channel
        ram[base], ram[base + 1] = pointer & 0xFF, pointer >> 8
        ram[base + 2 : base + 14] = AUDIO_TEMPLATE
    return tuple(_psg_latch(channel, 0x0F, volume=True) for channel in (3, 2, 1))
