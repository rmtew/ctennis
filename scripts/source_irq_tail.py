"""IRQ counters, audio scheduling and pending VDP-register bytes at 06B1."""

from collections.abc import Callable

from ball_math import u8
from source_audio import audio_tick_17c5


def irq_tail_06b1(
    ram: bytearray,
    *,
    rom: bytes | None = None,
    audio_tick: Callable[[bytearray], tuple[int, ...]] | None = None,
) -> tuple[bool, tuple[int, ...], tuple[int, ...]]:
    """Run 06B1-06EA; return (audio_due, VDP bytes, PSG bytes).

    Audio record processing at 17C5 runs against `rom` when due. A custom
    callback may replace it for differential checks; without either, a due
    tick raises rather than silently treating the update as complete.
    """
    ram[0x6B] = u8(ram[0x6B] + 1)
    for offset in range(0x6C, 0x72):
        if ram[offset] != 0xFF:
            ram[offset] += 1
    ram[0x83] = u8(ram[0x83] - 1)
    due = ram[0x83] == 0
    psg: tuple[int, ...] = ()
    if due:
        if audio_tick is not None:
            psg = audio_tick(ram)
        elif rom is not None:
            psg = audio_tick_17c5(ram, rom)
        else:
            raise ValueError("17C5 audio tick is due; supply the identified ROM bytes")
    if not ram[0x02] & 0x80:
        return due, (), psg
    ram[0x02] &= ~0x80
    register_1 = 0xE2 if ram[0x02] & 1 else 0xA2
    register_2 = 0x0F if ram[0x02] & 2 else 0x0E
    return due, (register_1, 0x81, register_2, 0x82), psg
