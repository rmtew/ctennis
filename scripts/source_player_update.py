"""Lower/upper Champion Tennis player phase dispatchers from Z80 source.

RAM is C000-C0FF. AI's Z80 R-register bit is explicit input where needed.
This module does not run an emulator or the complete interrupt callback.
"""

from ball_math import advance_ball_12ce, derive_launch_vector_1554, divide_152b, multiply_151e, u8
from source_ball_update import player_contact_0bf3_0f21


SERVE_LOWER = bytes((0, 0, 0x40, 0xA0, 0x14, 0xB4, 0))
SERVE_UPPER = bytes((0, 0, 0x40, 0x18, 0xFC, 0x28, 0))
TABLE_E39 = bytes((0x40, 0x80, 0xC0, 0xFF, 0x20, 0x24, 0x24, 0x24, 0x24))
TABLE_E42 = bytes((0x40, 0x80, 0xC0, 0xFF, 0x40, 0x40, 0x40, 0x40, 0x40))
TABLE_E4B = bytes((0x40, 0x80, 0xF0, 0xFF, 0x6D, 0x68, 0x58, 0x6D, 0x68))
TABLE_10D7 = bytes((0x40, 0x80, 0xC0, 0xFF, 0x90, 0x90, 0x90, 0x90, 0x90))
TABLE_10E0 = bytes((0x40, 0x80, 0xF0, 0xFF, 0x88, 0x98, 0xA0, 0xA0, 0xA0))


def _prng(ram: bytearray) -> int:
    ram[0x72] = u8(ram[0x72] * 5 + 1)
    return ram[0x72]


def _action_1498(ram: bytearray, *, upper: bool) -> int:
    action = ram[0x56]
    if (ram[0x3D] ^ (0x10 if upper else 0)) & 0x10:
        action = ((action << 4) | (action >> 4)) & 0xFF
    return action & 3


def _serve_vector_1760(ram: bytearray, *, upper: bool) -> None:
    ram[0x60:0x67] = SERVE_UPPER if upper else SERVE_LOWER
    player_x = ram[0x46 if upper else 0x4A]
    ram[0x64] = u8(ram[0x64] + player_x)


def _table_sample_0e2b(ram: bytearray, table: bytes) -> int:
    first = _prng(ram)
    index = 0
    while index < 4 and first >= table[index]:
        index += 1
    second = _prng(ram)
    return u8(table[4 + index] + (second & 0x0C))


def _random_launch(ram: bytearray, *, upper: bool) -> None:
    ram[0x5B] = ram[0x4E]
    ram[0x5A], ram[0x5C] = (0x0C, 0x28) if upper else (0x98, 0xA8)
    ram[0x5F] = _table_sample_0e2b(ram, TABLE_E39)
    ram[0x5D] = _table_sample_0e2b(ram, TABLE_10D7 if upper else TABLE_E42)
    ram[0x5E] = _table_sample_0e2b(ram, TABLE_10E0 if upper else TABLE_E4B)
    ram[0x38] = 0x80
    if _prng(ram) >= 0xE0:
        ram[0x5F] = 0x0C
        ram[0x5D] = 0x78 if upper else 0x68
        ram[0x38] |= 0x08
    if ram[0x3D] & 0x08:
        ram[0x5E] = u8(-ram[0x5E])
    derive_launch_vector_1554(ram)


def _adjust_intercept_16fa(player_x: int, y: int, x: int) -> tuple[int, int]:
    x = u8(x - 0x10) if player_x < x else x
    return u8(y - 0x20), x


def _intercept_candidates_167c(ram: bytearray) -> tuple[tuple[int, int], tuple[int, int]]:
    """Return two (Y,X) candidates, preserving C067-C06A scratch writes."""
    ram[0x67] = ram[0x68] = 0
    start_x, start_y = ram[0x5B], ram[0x5C]
    end_y, end_x = ram[0x5D], ram[0x5E]
    y_negative = end_y < start_y
    x_negative = end_x < start_x
    if y_negative:
        ram[0x67] = 1
    if x_negative:
        ram[0x68] = 1
    ram[0x69] = abs(end_y - start_y)
    ram[0x6A] = abs(end_x - start_x)
    q = divide_152b(multiply_151e(ram[0x6A], 0x10), ram[0x69])[0]
    ram[0x69] = q
    first_y = u8(end_y + (-0x10 if y_negative else 0x10))
    first_x = u8(end_x + (-q if x_negative else q))
    first = (first_y, first_x)
    if 0x50 <= end_y < 0x90:
        return first, first
    second_y = u8(first_y + (0x20 if y_negative else -0x20))
    second_x = u8(first_x + 2 * q)
    return first, (second_y, second_x)


def _setup_ai_target(ram: bytearray, *, upper: bool, refresh_bit: int | None) -> str:
    phase = 0x3B if upper else 0x3A
    # Lower sets up on C039 bit 6; upper sets up when it is clear.
    target_side = bool(ram[0x39] & 0x40)
    if target_side != (not upper):
        return _track_ai_target(ram, upper=upper, refresh_bit=refresh_bit)
    first, second = _intercept_candidates_167c(ram)
    selected = second if _prng(ram) >= 0xF0 else first
    player_x = ram[0x46 if upper else 0x4A]
    y, x = _adjust_intercept_16fa(player_x, *selected)
    random_value = _prng(ram)
    random_shift = random_value & 7
    if random_value & 0x10:
        random_shift = -random_shift
    offset = 0x75 if upper else 0x73
    ram[offset], ram[offset + 1] = y, u8(x + random_shift)
    ram[phase] = 0x02
    return "ai_target_setup"


def _direction_ai_162d(ram: bytearray, *, upper: bool) -> int:
    mode = ram[0x3D]
    use_high_nibble = True
    if mode & 0x04:
        effective = mode ^ (0x10 if upper else 0)
        use_high_nibble = bool(effective & 0x10)
    target = 0x75 if upper else 0x73
    player = 0x45 if upper else 0x49
    direction = 0
    if ram[player] < ram[target]:
        direction |= 0x08
    elif ram[player] > ram[target]:
        direction |= 0x02
    if ram[player + 1] < ram[target + 1]:
        direction |= 0x01
    elif ram[player + 1] > ram[target + 1]:
        direction |= 0x04
    if use_high_nibble:
        ram[0x53] = (direction << 4) | (ram[0x53] & 0x0F)
    else:
        ram[0x53] = (ram[0x53] & 0xF0) | direction
    return direction


def _track_ai_target(ram: bytearray, *, upper: bool, refresh_bit: int | None) -> str:
    if not ram[0x3C] & 0x40:
        return "ai_tracking_disabled"
    direction = _direction_ai_162d(ram, upper=upper)
    if direction:
        return "ai_move"
    phase = 0x3B if upper else 0x3A
    if ram[phase] & 0x02:
        return "ai_at_target"
    if refresh_bit not in (0, 1):
        raise ValueError("Z80 refresh-register bit 0 is required for AI retargeting")
    offset = 0x75 if upper else 0x73
    player = 0x45 if upper else 0x49
    opponent_x = ram[0x4A if upper else 0x46]
    ram[offset] = ram[player]
    jitter = (_prng(ram) & 0x0F) | 0x10
    ram[offset + 1] = u8(opponent_x + (-jitter if refresh_bit else jitter))
    return "ai_retarget"


def _ai_wait_target(ram: bytearray, *, upper: bool) -> None:
    player_x = ram[0x46 if upper else 0x4A]
    y, x = _adjust_intercept_16fa(player_x, 0x40 if upper else 0xA0, 0x80)
    offset = 0x75 if upper else 0x73
    ram[offset], ram[offset + 1] = y, x
    ram[0x3B if upper else 0x3A] = 0x04


def player_state_0b29_0e54(
    ram: bytearray, *, upper: bool, refresh_bit: int | None = None
) -> str:
    """Run the highest-priority lower/upper player phase once."""
    phase = 0x3B if upper else 0x3A
    state = ram[phase]
    ai = bool(ram[0x3C] & (1 if upper else 2))
    animation = 0x44 if upper else 0x43
    if state & 0x80:
        _serve_vector_1760(ram, upper=upper)
        ram[0x39] = 0x40 if upper else 0
        ram[0x6C] = 0
        ram[phase] = 0x40
        return "serve_setup"
    if state & 0x40:
        advance_ball_12ce(ram)
        if ram[0x4D] >= (0x18 if upper else 0xA0):
            ram[0x66] = 0
        ball_x = u8(ram[0x46 if upper else 0x4A] + (-4 if upper else 0x14))
        ram[0x4E] = ram[0x35] = ball_x
        if ai:
            ready = ram[0x6C] >= 0x50
        else:
            ready = bool(_action_1498(ram, upper=upper))
        if ready:
            ram[0x6C] = 0
            ram[animation] = 0xF3 if upper else 0xF0
            ram[phase] = 0x20
            return "serve_triggered"
        return "serve_wait"
    if state & 0x20:
        counter = ram[0x6C]
        if counter == 0x10:
            ram[animation] |= 0x80
            _random_launch(ram, upper=upper)
            return "serve_launch"
        if counter == 0x20:
            other_animation = 0x43 if upper else 0x44
            other_phase = 0x3A if upper else 0x3B
            ram[other_animation] = (ram[other_animation] & 0x1F) | 0x40
            ram[other_phase] |= 1
            return "serve_handoff"
        if counter >= 0x31:
            ram[animation] &= ~0x80
            ram[phase] = 0x11
            return "serve_complete"
        return "serve_animation"
    if state & 0x10:
        if ai:
            if state & 1:
                _ai_wait_target(ram, upper=upper)
                return "ai_wait_target"
            return "ai_wait"
        return "contact" if player_contact_0bf3_0f21(ram, upper=upper) else "no_contact"
    if state & 0x08:
        if ram[0x6F] < 8:
            return "animation_wait"
        ram[animation] &= ~0x80
        if ai:
            _ai_wait_target(ram, upper=upper)
            return "ai_wait_target"
        ram[phase] = 0x10
        return "animation_complete"
    if state & 0x04:
        return _setup_ai_target(ram, upper=upper, refresh_bit=refresh_bit)
    if state & 0x02:
        if player_contact_0bf3_0f21(ram, upper=upper):
            return "contact"
        return _track_ai_target(ram, upper=upper, refresh_bit=refresh_bit) if ai else "no_contact"
    return "idle"
