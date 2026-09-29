"""Translated G-1009 gameplay interrupt body, in ROM call order.

The caller supplies decoded input bytes, RAM/VRAM state and the source ROM.
Physical I/O remains external. No emulator is launched.
"""

from collections.abc import Callable
from dataclasses import dataclass

from source_ball_update import ball_dispatch_11a0
from source_player_update import player_state_0b29_0e54
from source_input_movement import input_update_0832, movement_and_sprites_13b9
from source_score_display import ScoreGateResult, score_gate_094e, scoreboard_update_06eb
from source_irq_tail import irq_tail_06b1


@dataclass(frozen=True)
class FrameBodyResult:
    prior_sprite_upload: bytes
    scoreboard_writes: tuple[tuple[int, int], ...]
    score: ScoreGateResult
    lower_path: str
    upper_path: str
    ball_path: str
    ball_slot: int
    audio_due: bool
    vdp_control_bytes: tuple[int, ...]
    psg_bytes: tuple[int, ...]


def run_gameplay_slice(
    ram: bytearray, *, lower_refresh_bit: int | None = None, upper_refresh_bit: int | None = None
) -> tuple[ScoreGateResult, str, str, str]:
    """Call 094E, 0B29, 0E54, 11A0 in that order; return path names."""
    if len(ram) < 256:
        raise ValueError("Expected at least the C000-C0FF RAM page")
    score = score_gate_094e(ram)
    lower = player_state_0b29_0e54(ram, upper=False, refresh_bit=lower_refresh_bit)
    upper = player_state_0b29_0e54(ram, upper=True, refresh_bit=upper_refresh_bit)
    ball = ball_dispatch_11a0(ram)
    return score, lower, upper, ball


def run_translated_frame_body(
    ram: bytearray,
    vram: bytearray,
    *,
    game_bits: int | None = None,
    keyboard_bits: int | None = None,
    lower_refresh_bit: int | None = None,
    upper_refresh_bit: int | None = None,
    rom: bytes | None = None,
    audio_tick: Callable[[bytearray], tuple[int, ...]] | None = None,
) -> FrameBodyResult:
    """Model 046F, 06EB, 0832, 094E, 0B29, 0E54, 11A0, 13B9, 06B1.

    The prior 40-byte sprite buffer is returned for the 046F upload; the
    scoreboard writes mutate VRAM and are returned in order. The 17C5 audio
    tick uses `rom` when due. Hardware ports are not modeled.
    """
    if len(ram) < 256:
        raise ValueError("Expected at least the C000-C0FF RAM page")
    prior_sprite_buffer = bytes(ram[0x10:0x38])
    scoreboard_writes = scoreboard_update_06eb(ram, vram)
    input_update_0832(ram, game_bits=game_bits, keyboard_bits=keyboard_bits)
    score, lower, upper, ball = run_gameplay_slice(
        ram, lower_refresh_bit=lower_refresh_bit, upper_refresh_bit=upper_refresh_bit
    )
    ball_slot = movement_and_sprites_13b9(ram)
    audio_due, vdp_bytes, psg_bytes = irq_tail_06b1(ram, rom=rom, audio_tick=audio_tick)
    return FrameBodyResult(
        prior_sprite_buffer,
        tuple(scoreboard_writes),
        score,
        lower,
        upper,
        ball,
        ball_slot,
        audio_due,
        vdp_bytes,
        psg_bytes,
    )
