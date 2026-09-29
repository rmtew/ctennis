"""Source-order ball dispatch and point resolution for G-1009.

Only the routines named here are translated. This is not a complete interrupt
callback: player serve/return and score-transition setup remain separate.
RAM is a 256-byte C000-C0FF window. No emulator is used.
"""

from ball_math import (
    advance_ball_12ce,
    bounce_121c,
    derive_launch_vector_1554,
    divide_152b,
    multiply_151e,
    reflect_1244,
    u8,
)


def net_vicinity_1383(ram: bytearray) -> bool:
    """Return the source carry flag; mutate fields on first net crossing."""
    if not ram[0x38] & 0x08 or ram[0x39] & 0x01:
        return False
    if abs(ram[0x34] - 0x6E) >= 3:
        return False
    ram[0x39] |= 0x01
    ram[0x67], ram[0x68] = 0x40, 0xC0  # LD HL,C040; LD (C067),HL
    ram[0x61] ^= 0x80
    ram[0x63], ram[0x64] = ram[0x4D], ram[0x4E]
    ram[0x65] = ram[0x34]
    return True


def _stop_outside_120e(ram: bytearray) -> None:
    ram[0x39] |= 0x80
    ram[0x38] = (ram[0x38] & ~0x40) | 0x20


def _start_ball_sound_0596(ram: bytearray) -> None:
    """Record assignment made by 0596 -> 059B -> 05AB for stream 1FF3."""
    # The stored pointer is one byte before the stream; the fetch increments.
    ram[0xA1], ram[0xA2] = 0xF2, 0x1F
    ram[0xA3], ram[0xA4] = 9, 0
    ram[0xA5], ram[0xAE] = 1, 0


def ball_dispatch_11a0(ram: bytearray) -> str:
    """11A0-121B: perform one ball phase; return the path taken."""
    flags = ram[0x38]
    if flags & 0x80:
        ram[0x60:0x66] = ram[0x57:0x5D]
        ram[0x66] = 0
        _start_ball_sound_0596(ram)
        ram[0x38] = (ram[0x38] & ~0x80) | 0x40
        return "launch"
    if not flags & 0x40:
        if flags & 0x20:
            for offset in (0x34, 0x10, 0x20, 0x30):
                ram[offset] = 0xC2
            return "hidden"
        return "idle"

    advance_ball_12ce(ram)
    if (ram[0x61] & 0x7F) < 4:
        _stop_outside_120e(ram)
        return "outside"
    if ram[0x34] < ram[0x4D]:
        bounce_121c(ram)
        return "court_bounce"
    if net_vicinity_1383(ram):
        reflect_1244(ram)
        return "net_reflect"
    if 0x20 <= ram[0x35] < 0xE8 and 0x04 <= ram[0x34] < 0xCC:
        return "flight"
    _stop_outside_120e(ram)
    return "outside"


def player_contact_candidate(ram: bytearray, *, upper: bool) -> bool:
    """Source gates and geometry for lower 0BF3 / upper 0F21 paths.

    A true result only reaches the contact-construction body. It does not
    select action, trajectory, animation, AI return, or play a sound.
    """
    if upper:
        if ram[0x39] & 0x40:
            return False
        y, x = ram[0x45], ram[0x46]
        y_offset = 0x23
    else:
        if not ram[0x39] & 0x40:
            return False
        y, x = ram[0x49], ram[0x4A]
        y_offset = 0x1B
    if ram[0x39] & 0x0D:
        return False
    # ADD HL,DE at 0C06/0F34 is 16-bit: a low-byte Y carry also increments X.
    contact = ((x << 8) | y) + ((8 << 8) | y_offset)
    contact_y, contact_x = contact & 0xFF, (contact >> 8) & 0xFF
    ram[0x67], ram[0x68] = contact_y, contact_x
    height = ram[0x34] - ram[0x4D]
    return (
        abs(ram[0x34] - contact_y) < 4
        and abs(ram[0x35] - contact_x) < 17
        and 0 <= height < 0x1D
    )


def _prng_1754(ram: bytearray) -> int:
    ram[0x72] = u8(5 * ram[0x72] + 1)
    return ram[0x72]


def _contact_target_170a(ram: bytearray) -> int:
    """Return H from 170A, with C067-C06A scratch writes preserved."""
    y, x = ram[0x67], ram[0x68]
    ram[0x67] = u8(0xE0 - y)
    ram[0x69] = u8((ram[0x67] >> 2) + 0x24)
    ram[0x6A] = u8((y >> 2) + 0x24)
    left_of_center = x < 0x80
    ram[0x68] = 0x80 if left_of_center else 0
    distance = abs(x - 0x80)
    product = multiply_151e(distance, ram[0x69])
    scaled = divide_152b(product, ram[0x6A])[0]
    if left_of_center:
        scaled = u8(-scaled)
    return u8(scaled + 0x80)


def _return_vector_0cda(ram: bytearray, *, phase: int) -> int:
    """0CDA-0D46: build trajectory and return animation byte F1/F2."""
    ram[phase] &= ~1
    difference = ram[0x4E] - ram[0x68]
    ball_left_of_contact = difference < 0
    if ball_left_of_contact:
        ram[phase] |= 1
    distance = abs(difference)
    if distance >= 0x0D:
        distance = u8(distance + (_prng_1754(ram) & 7))
    ram[0x5E] = u8(2 * distance)
    target_x = _contact_target_170a(ram)
    delta = ram[0x5E]
    if ball_left_of_contact:
        addition = target_x + u8(-delta)
        ram[0x5E] = u8(addition) if addition > 0xFF else 0
    else:
        ram[0x5E] = u8(target_x + delta)

    if not ram[0x38] & 0x08 and not ram[0x39] & 0x02:
        ram[0x38] |= 0x02
    ram[0x5A], ram[0x5B] = ram[0x4D], ram[0x4E]
    ram[0x5C] = ram[0x34]
    derive_launch_vector_1554(ram)
    ram[0x42] &= ~0x10
    ram[0x38] |= 0x80
    return 0xF2 if ball_left_of_contact else 0xF1


def player_contact_0bf3_0f21(ram: bytearray, *, upper: bool) -> bool:
    """Successful contact construction: 0BF3-0CB0 / 0F21-0FE6.

    False means this geometric path did not accept a hit. It handles the
    control-flag-dependent random/action branches after contact, while the
    player state dispatchers determine when this routine is entered.
    """
    if not player_contact_candidate(ram, upper=upper):
        return False
    height = ram[0x34] - ram[0x4D]  # candidate establishes 0..28
    ram[0x38] = 0
    ai = bool(ram[0x3C] & (0x01 if upper else 0x02))
    special = height < 8
    if special and ai:
        special = _prng_1754(ram) >= 0xE0
    if special:
        ram[0x38] |= 0x08
        ram[0x5F] = 0x0C
        ram[0x5D] = 0x78 if upper else 0x68
    else:
        ram[0x5F] = u8(height + 0x18)
        target_y = u8(0xE0 - ram[0x67])
        ram[0x5D] = min(target_y, 0xA0) if upper else max(target_y, 0x40)
        if ai:
            action_taken = (_prng_1754(ram) & 0x0F) == 0
        else:
            # 1498 rotates nibbles when mode bit 4 differs from the side.
            action = ram[0x56]
            rotate = bool((ram[0x3D] ^ (0x10 if upper else 0)) & 0x10)
            if rotate:
                action = ((action << 4) | (action >> 4)) & 0xFF
            action_taken = bool(action & 3)
        if action_taken:
            if upper:
                ram[0x5F] = u8(0x80 - ram[0x67])
                ram[0x5D] = u8(0xD0 - ram[0x5F])
            else:
                ram[0x5F] = u8(ram[0x67] - 0x60)
                ram[0x5D] = u8(ram[0x5F] + 0x10)
            ram[0x38] |= 0x02

    phase = 0x3B if upper else 0x3A
    ram[0x44 if upper else 0x43] = _return_vector_0cda(ram, phase=phase)
    ram[0x6F] = 0
    ram[0x39] = 0x40 if upper else 0
    ram[phase] = 0x08
    return True


def resolve_pending_point_0989(ram: bytearray) -> str:
    """0989-0A78: resolve a C039 bit-7 outcome with C03C bit 6 active."""
    if not ram[0x3C] & 0x40 or not ram[0x39] & 0x80:
        return "not_pending"

    outcome = 1 if ram[0x39] & 0x02 and not ram[0x39] & 0x08 else 2
    if ram[0x39] & 0x01:
        outcome = 3
    pending_bit4 = bool(ram[0x42] & 0x10)
    if pending_bit4:
        outcome = 4 if outcome == 1 else 5
    ram[0x42] = (ram[0x42] & 0x18) | 0x80 | outcome
    if pending_bit4 and outcome != 4:
        if not ram[0x42] & 0x08:
            ram[0x42] |= 0x08
            ram[0x42] |= 0x20
            ram[0x38] = ram[0x6C] = 0
            ram[0x3C] = (ram[0x3C] & 7) | 0x20
            return "deferred"
        ram[0x42] = u8(ram[0x42] + 1)
    ram[0x42] &= ~0x08

    selected, other, side = 0x3E, 0x3F, 0
    if (ram[0x42] & 7) not in (1, 4):
        selected, other = other, selected
        side += 1
    if ram[0x39] & 0x40:
        selected, other = other, selected
        side += 1
    if ram[0x3D] & 0x10:
        selected, other = other, selected
        side += 1

    point = ram[selected] & 7
    if point <= 1:
        ram[selected] = u8(ram[selected] + 1)
        result = "point"
    elif point == 2:
        if ram[other] == 3:
            ram[selected] = ram[other] = 5
            result = "deuce"
        else:
            ram[selected] = u8(ram[selected] + 1)
            result = "point"
    elif point in (3, 4):
        game_cell = 0x40 + (side & 1)
        ram[game_cell] = u8(ram[game_cell] + 1)
        if ram[game_cell] >= 6:
            ram[0x3D] |= 0x40
        ram[0x3E] = ram[0x3F] = 0
        ram[0x42] |= 0x20
        ram[0x38] = ram[0x6C] = 0
        ram[0x43] |= 0x80
        ram[0x44] |= 0x80
        ram[0x3C] = (ram[0x3C] & 7) | 0x10
        return "game"
    elif point == 5:
        ram[selected] = u8(ram[selected] - 1)
        ram[other] = u8(ram[other] + 1)
        result = "advantage"
    else:
        ram[selected] = ram[other] = 5
        result = "deuce"

    ram[0x3D] ^= 0x08
    ram[0x42] |= 0x20
    ram[0x38] = ram[0x6C] = 0
    ram[0x3C] = (ram[0x3C] & 7) | 0x20
    return result
