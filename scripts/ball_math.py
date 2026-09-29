"""Literal 8/16-bit arithmetic extracted from Champion Tennis G-1009.

RAM is the cartridge's C000-C0FF page, indexed by its low address byte.
These functions do not model an emulator or generate display output. They retain
Z80 wraparound and the order of writes so the Amiga translation can be reviewed.
"""

from math import isqrt


def u8(value: int) -> int:
    return value & 0xFF


def word(ram: bytearray, low: int) -> int:
    return ram[low] | (ram[low + 1] << 8)


def multiply_151e(high: int, low: int) -> int:
    """151E-152A: HL <- H * L, full 16-bit unsigned product."""
    hl = ((high & 0xFF) << 8)
    de = low & 0xFF
    for _ in range(8):
        carry = bool(hl & 0x8000)
        hl = (hl << 1) & 0xFFFF
        if carry:
            hl = (hl + de) & 0xFFFF
    return hl


def divide_152b(dividend: int, divisor: int) -> tuple[int, int]:
    """152B-1541: return output H,L (8-bit quotient,remainder).

    The loop is retained rather than using // and %, including its defined
    behavior for zero divisors and quotients that do not fit in eight bits.
    """
    hl = dividend & 0xFFFF
    e = divisor & 0xFF
    carry = 0  # XOR A at 152D
    for _ in range(8):
        shifted = 2 * hl + carry  # ADC HL,HL
        shifted_carry = shifted > 0xFFFF
        hl = shifted & 0xFFFF
        h, l = hl >> 8, hl & 0xFF
        if shifted_carry or h >= e:
            h = (h - e) & 0xFF
            carry = 1  # SUB; XOR A; CCF
        else:
            carry = 0  # CP sets carry; CCF clears it
        hl = (h << 8) | l
    remainder = hl >> 8
    quotient = ((hl & 0xFF) << 1 | carry) & 0xFF  # RL L at 153C
    return quotient, remainder


def triangular_root_1542(value: int) -> int:
    """1542-1553: least k with value <= k*(k+1), for 16-bit value."""
    # SCF causes an initial subtraction of one. The ROM then subtracts each
    # successive BC twice. This is a triangular-root-like integer operation,
    # not floor(sqrt(value)); for example 3->2 and 7->3.
    n = value & 0xFFFF
    k = (isqrt(4 * n + 1) - 1) // 2
    if k * (k + 1) < n:
        k += 1
    return k


def _quotient(high: int, low: int, divisor: int) -> int:
    return divide_152b(multiply_151e(high, low), divisor)[0]


def derive_launch_vector_1554(ram: bytearray) -> None:
    """1554-1613: derive C057-C059 from setup fields C05A-C05F.

    It also writes scratch C067-C06A. All subtraction/NEG operations wrap to
    eight bits; divide_152b preserves the original behavior for divisor zero.
    """
    ram[0x69] = abs(ram[0x5D] - ram[0x5C])
    ram[0x67] = abs(0x6F - ram[0x5C])
    ram[0x68] = abs(ram[0x5D] - 0x6F)
    ram[0x6A] = u8(ram[0x5C] - ram[0x5A])

    first = _quotient(ram[0x5F], ram[0x69], ram[0x68])
    divisor = u8(first - ram[0x6A])  # A=C06A; SUB H; NEG at 1592-1596
    second = _quotient(ram[0x69], ram[0x67], divisor)
    root = triangular_root_1542(multiply_151e(second, 0x40))
    ram[0x58] = root & 0x7F

    c = _quotient(0x40, ram[0x69], ram[0x58])
    h = _quotient(ram[0x58], ram[0x6A], ram[0x69])
    ram[0x59] = u8(c - h)

    negative = ram[0x5E] < ram[0x5B]
    delta = abs(ram[0x5E] - ram[0x5B])
    horizontal = _quotient(delta, ram[0x58], ram[0x69])
    ram[0x57] = horizontal | (0x80 if negative else 0)
    if ram[0x5D] < ram[0x5C]:
        ram[0x58] |= 0x80


def _signed_step_136b(field: int, step: int) -> int:
    magnitude = _quotient(field & 0x7F, step, 0x20)
    return u8(-magnitude) if field & 0x80 else magnitude


def advance_ball_12ce(ram: bytearray) -> None:
    """12CE-136A: one active-flight coordinate and height update.

    This routine is called inside the larger 11A0 dispatcher. It does not
    implement boundary, bounce, net, scoring, or sprite-record routing.
    """
    ram[0x66] = u8(ram[0x66] + 1)
    ram[0x50] = 0x0F
    ram[0x37] = 1
    step = ram[0x66]

    ram[0x4E] = u8(ram[0x64] + _signed_step_136b(ram[0x60], step))
    ram[0x35] = ram[0x4E]
    ram[0x34] = u8(ram[0x65] + _signed_step_136b(ram[0x61], step))

    y_velocity = ram[0x61] & 0x7F
    if ram[0x61] & 0x80:
        # NEG low byte then DEC H at 1306-1309. Negative zero is FF00,
        # not 0000, so keep the literal 16-bit construction.
        y_velocity = 0xFF00 | u8(-y_velocity)
    # SBC HL,DE uses carry cleared by AND A at 1310.
    vertical = (2 * step + y_velocity - ram[0x62]) & 0xFFFF
    negative = bool(vertical & 0x8000)
    magnitude_low = u8(-u8(vertical)) if negative else u8(vertical)
    height = _quotient(magnitude_low, step, 0x20)

    if negative and height:
        result = ram[0x63] - height
        if result < 0:
            ram[0x4D] = 0
            ram[0x50] = 0
            return
        ram[0x4D] = result
    else:
        ram[0x4D] = u8(ram[0x63] + height)

    if 0x5E <= ram[0x34] < 0x6E:
        ram[0x37] = 0
    if 0x5E <= ram[0x4D] < 0x6E:
        ram[0x50] = 0


def court_contact_1298(ram: bytearray) -> None:
    """1298-12CD: update C039 contact/outside flags from court X/Y."""
    flags = ram[0x39]
    if not flags & 0x02:
        y, x = ram[0x34], ram[0x35]
        outside = not 0x27 <= y < 0xB8
        if not outside:
            half_width = (y - 0x27) >> 2
            outside = x <= 0x4F - half_width or x > 0xAF + half_width
        if outside:
            flags |= 0x08
    if flags & 0x04:
        ram[0x39] = flags
        return
    if flags & 0x02:
        flags |= 0x04
    ram[0x39] = flags | 0x02


def bounce_121c(ram: bytearray) -> None:
    """121C-1243: contact flags and new flight base, then reflect_1244."""
    court_contact_1298(ram)
    # The bit-3/bit-1 decision is on C038 (IX), not contact flags C039.
    if ram[0x38] & (0x08 | 0x02):
        ram[0x67], ram[0x68] = 0xF0, 0x80
    else:
        ram[0x67], ram[0x68] = 0xFF, 0xC0
    ram[0x4D], ram[0x4E] = ram[0x34], ram[0x35]
    ram[0x63], ram[0x64] = ram[0x34], ram[0x35]
    ram[0x65] = ram[0x34]
    reflect_1244(ram)


def reflect_1244(ram: bytearray) -> None:
    """1244-1286: trajectory rewrite shared by court bounce and net hit."""

    # 1244-1261: signed 16-bit subtraction, clamp negative to zero,
    # then take only the low byte as multiplier.
    difference = 4 * ram[0x66] - ram[0x62]
    multiplier = u8(max(difference, 0))
    ram[0x62] = multiply_151e(ram[0x68], multiplier) >> 8

    # 1287-1297: scale each signed-magnitude field by C067/256.
    for field in (0x60, 0x61):
        original = ram[field]
        scaled = multiply_151e(original & 0x7F, ram[0x67]) >> 8
        ram[field] = scaled | (original & 0x80)
    ram[0x66] = 0
    for field in (0x43, 0x44):
        ram[field] = (ram[field] & 0x9F) | 0x60
