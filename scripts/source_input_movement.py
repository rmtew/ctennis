"""Input selection, player movement, animation and sprite RAM from G-1009.

Hardware scan results are explicit inputs. RAM is the C000-C0FF byte page.
This is source translation, not an SG/SC port or VDP emulator.
"""

from ball_math import u8


LOWER_BOUNDS = bytes.fromhex("9a 98 c8 80 9a 98 70 28 9a 80 c8 28 9a 62 c8 28")
UPPER_BOUNDS = bytes.fromhex("0a 07 70 50 0a 07 a0 80 20 07 b0 40 3f 07 b0 40")
ANIMATION_RECORDS = bytes.fromhex(
    "10 20 30 40 08 09 0a ff ff "
    "08 10 18 20 0c 0d 0b ff ff "
    "08 10 18 20 05 06 04 ff ff "
    "10 20 30 40 01 02 03 ff ff"
)
SPRITE_DESCRIPTORS = bytes.fromhex(
    "30 28 2c 08 00 0c 04 08 00 10 "
    "18 10 14 f8 f8 24 1c 20 10 08 "
    "0c 44 48 fe 10 3c 34 38 08 f8 "
    "40 34 38 0a 10 4c a8 ac 00 00 "
    "8c 84 88 00 f0 98 90 94 f8 08 "
    "a4 9c a0 10 f8 8c c4 c8 fe f0 "
    "bc b4 b8 08 08 c0 b4 b8 0a f0"
)


def input_update_0832(
    ram: bytearray, *, game_bits: int | None = None, keyboard_bits: int | None = None
) -> None:
    """0832-087D: map decoded 087E/0887 results to C053/C056.

    `game_bits` is the byte returned by 087E, not raw active-low I/O ports.
    `keyboard_bits` is the byte returned by 0887 in C03D-bit-7 mode.
    A separate hardware adapter must implement those readers.
    """
    mode = ram[0x3D]
    if mode & 0x04:
        ram[0x53] = ram[0x56] = 0
        return
    if game_bits is None or not 0 <= game_bits <= 255:
        raise ValueError("087E game-input result is required")
    if mode & 0x80:
        if keyboard_bits is None or not 0 <= keyboard_bits <= 255:
            raise ValueError("0887 keyboard-input result is required in bit-7 mode")
        ram[0x53] = (game_bits & 0x0F) | ((keyboard_bits & 0x0F) << 4)
        ram[0x56] = ((game_bits & 0x30) >> 4) | (keyboard_bits & 0x30)
    else:
        ram[0x53] = game_bits & 0x0F
        ram[0x56] = (game_bits & 0x30) >> 4


def _selected_direction(ram: bytearray, *, upper: bool) -> int:
    direction = ram[0x53]
    if (ram[0x3D] ^ (0x10 if upper else 0)) & 0x10:
        direction = ((direction << 4) | (direction >> 4)) & 0xFF
    return direction & 0x0F


def move_player_1404_145d(ram: bytearray, *, upper: bool) -> None:
    """1404-148B: bounded Y/X movement using prior IRQ counter parity."""
    if ram[0x39] & 0x04:
        return
    animation = 0x44 if upper else 0x43
    if ram[animation] & 0x80:
        return
    bounds = UPPER_BOUNDS if upper else LOWER_BOUNDS
    # Three RRCA instructions followed by AND 0C select one 4-byte row.
    row = ((ram[animation] >> 5) & 3) * 4
    step = 1 + (ram[0x6B] & 1)
    direction = _selected_direction(ram, upper=upper)
    y = 0x45 if upper else 0x49
    x = y + 1
    if direction & 0x08:
        value = u8(ram[y] + step)
        if value < bounds[row]:
            ram[y] = value
    if direction & 0x02:
        value = u8(ram[y] - step)
        if value >= bounds[row + 1]:
            ram[y] = value
    if direction & 0x01:
        value = u8(ram[x] + step)
        if value < bounds[row + 2]:
            ram[x] = value
    if direction & 0x04:
        value = u8(ram[x] - step)
        if value >= bounds[row + 3]:
            ram[x] = value


def _animation_lookup(record: bytes, timer: int) -> int:
    index = 0
    while index < 4 and timer >= record[index]:
        index += 1
    return record[4 + index]


def animate_player_14a7_14b3(ram: bytearray, *, upper: bool) -> None:
    animation = 0x44 if upper else 0x43
    counter = 0x6E if upper else 0x6D
    descriptor = 0x47 if upper else 0x4B
    flags = ram[animation]
    if not flags & 0x08:
        if not flags & 0x10:
            return
        ram[animation] |= 0x08
        ram[counter] = 0
    index = ram[animation] & 7
    if index >= 4:
        raise ValueError(f"Animation index {index} would address beyond ROM table 14FA")
    record = ANIMATION_RECORDS[index * 9 : index * 9 + 9]
    selected = _animation_lookup(record, ram[counter])
    if selected == 0xFF:
        ram[animation] &= ~0x18
        selected = 0 if upper else 7
    ram[descriptor] = selected


def build_player_sprites_10e9(ram: bytearray) -> None:
    """10E9-114D: three 4-byte hardware sprite records per player."""
    for upper in (True, False):
        player = 0x45 if upper else 0x49
        sprite = 0x24 if upper else 0x14
        y, x = ram[player], ram[player + 1]
        index = ram[player + 2]
        if index >= 14:
            raise ValueError(f"Sprite descriptor index {index} exceeds 14 records")
        base = index * 5
        p0, p1, p2, dy, dx = SPRITE_DESCRIPTORS[base : base + 5]
        ram[sprite + 4] = y
        ram[sprite + 5] = ram[sprite + 9] = x
        ram[sprite + 8] = u8(y + 0x10)
        ram[sprite + 2], ram[sprite + 6], ram[sprite + 10] = p0, p1, p2
        ram[sprite], ram[sprite + 1] = u8(y + dy), u8(x + dx)
        colors = ram[player + 3]
        ram[sprite + 3] = (colors >> 4) & 0x0F
        ram[sprite + 7] = ram[sprite + 11] = colors & 0x0F


def movement_and_sprites_13b9(ram: bytearray) -> int:
    """13B9-1401: move, animate and build sprite RAM; return ball slot."""
    move_player_1404_145d(ram, upper=False)
    move_player_1404_145d(ram, upper=True)
    animate_player_14a7_14b3(ram, upper=False)
    animate_player_14a7_14b3(ram, upper=True)
    build_player_sprites_10e9(ram)
    for slot in (0x10, 0x20, 0x30):
        ram[slot] = 0xC2
    ball_y = ram[0x34]
    if u8(ram[0x45] + 0x20) >= ball_y:
        slot = 0x30
    elif u8(ram[0x49] + 0x24) >= ball_y:
        slot = 0x20
    else:
        slot = 0x10
    ram[slot : slot + 4] = ram[0x4D:0x51]
    if ram[0x4D] >= 0xC0:
        ram[0x34] = 0xC2
        for ball_slot in (0x10, 0x20, 0x30):
            ram[ball_slot] = 0xC2
    return slot
