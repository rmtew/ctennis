"""Score-phase gate and scoreboard VRAM writes from Champion Tennis G-1009."""

from dataclasses import dataclass

from ball_math import u8
from source_ball_update import resolve_pending_point_0989
from source_input_movement import build_player_sprites_10e9


STATUS_TILES = bytes.fromhex("20 20 20 00 55 59 5a 5f 5e 59 51 5e 4d 4f 51 52 57 5e 50 4e 52")
MODE_TILES = bytes.fromhex("00 50 51 58 5a 45 5b 57 4d 61 46 5b 57 4d 61")
GAME_TILES = bytes.fromhex(
    "00 00 00 00 00 00 00 00 00 00 00 00 "
    "24 25 00 00 00 00 00 00 00 00 00 00 "
    "24 25 24 25 00 00 00 00 00 00 00 00 "
    "24 25 24 25 24 25 00 00 00 00 00 00 "
    "24 25 24 25 24 25 24 25 00 00 00 00 "
    "24 25 24 25 24 25 24 25 24 25 00 00 "
    "24 25 24 25 24 25 24 25 24 25 24 25"
)
POINT_TILES = bytes.fromhex(
    "00 26 00 27 28 2e 29 2f 2a 26 2b 27 2c 26 2d 27 "
    "30 32 31 33 2c 26 2d 27 00 00 00 00"
)


@dataclass(frozen=True)
class ScoreGateResult:
    name: str
    extra_sprite_upload: bytes | None = None


def _start_sound_058f(ram: bytearray) -> None:
    """058F->059B->05AB: channel-two record for 1FDD, length 16h."""
    ram[0xA1], ram[0xA2] = 0xDC, 0x1F
    ram[0xA3], ram[0xA4] = 0x17, 0
    ram[0xA5], ram[0xAE] = 1, 0


def _round_reset_0aa2(ram: bytearray) -> None:
    ram[0x38] = 0
    mode = ram[0x3D]
    if not mode & 0x80:
        ram[0x77] = ram[0x78] = ram[0x40]
        if mode & 0x04:
            ram[0x78 if mode & 0x10 else 0x77] = ram[0x41]
    ram[0x43] = ram[0x44] = 0x20 if mode & 0x08 else 0
    if mode & 0x02:
        ram[0x3A], ram[0x3B], ram[0x39] = 0x10, 0x80, 0x40
    else:
        ram[0x3A], ram[0x3B], ram[0x39] = 0x80, 0x10, 0


def _reset_positions_0af4(ram: bytearray) -> bytes:
    if ram[0x3D] & 0x08:
        ram[0x49], ram[0x4A], ram[0x45], ram[0x46] = 0x98, 0x38, 0x08, 0xA0
    else:
        ram[0x49], ram[0x4A], ram[0x45], ram[0x46] = 0x98, 0xB8, 0x08, 0x50
    ram[0x38] = 0
    ram[0x43] |= 0x80
    ram[0x44] |= 0x80
    ram[0x47], ram[0x4B] = 0, 7
    build_player_sprites_10e9(ram)
    return bytes(ram[0x10:0x38])  # direct 046F upload during score phase


def score_gate_094e(ram: bytearray) -> ScoreGateResult:
    """094E-0AA1 including its priority-ordered timed transitions."""
    flags = ram[0x3C]
    if flags & 0x80:
        if ram[0x42] & 0x40:
            return ScoreGateResult("audio_wait")
        ram[0x42] |= 0x10
        if ram[0xA4] != ram[0xA5]:
            return ScoreGateResult("audio_wait")
        _round_reset_0aa2(ram)
        ram[0x3C] = (ram[0x3C] & 7) | 0x40
        return ScoreGateResult("round_reset")
    if flags & 0x40:
        return ScoreGateResult(resolve_pending_point_0989(ram))
    if flags & 0x20:
        timer = ram[0x6C]
        if timer == 0x40:
            upload = _reset_positions_0af4(ram)
            return ScoreGateResult("positions_reset", upload)
        if timer >= 0xC0:
            _start_sound_058f(ram)
            ram[0x3C] = (ram[0x3C] & 7) | 0x80
            return ScoreGateResult("point_sound")
        return ScoreGateResult("point_pause")
    if flags & 0x10:
        if ram[0x6C] >= 0x80:
            ram[0x3D] |= 0x20
            ram[0x3C] = 0
            return ScoreGateResult("match_transition")
        return ScoreGateResult("match_pause")
    return ScoreGateResult("idle")


def scoreboard_update_06eb(ram: bytearray, vram: bytearray) -> list[tuple[int, int]]:
    """06EB-0815: write selected ROM tile bytes to a 16 KB VRAM image."""
    if len(vram) < 0x4000:
        raise ValueError("Expected at least 16 KB of VRAM")
    writes: list[tuple[int, int]] = []

    def put(address: int, value: int) -> None:
        vram[address] = value
        writes.append((address, value))

    status = ram[0x42]
    if status & 0x80:
        if status & 0x40:
            if u8(ram[0x71] + 1) == 0:
                ram[0x42] &= ~0xC0
                index = 0
            else:
                index = None
        else:
            ram[0x42] |= 0x40
            index = ram[0x42] & 7
        if index is not None:
            if index >= 7:
                raise ValueError("Status tile index exceeds seven ROM records")
            for i, value in enumerate(STATUS_TILES[index * 3 : index * 3 + 3]):
                put(0x398E + i, value)
            ram[0x71] = 0xE0

    if ram[0x42] & 0x20:
        ram[0x42] &= ~0x20
        mode = ram[0x3D]
        mode_index = 0 if mode & 0x04 else (2 if mode & 0x80 else 1)
        for i, value in enumerate(MODE_TILES[mode_index * 5 : mode_index * 5 + 5]):
            put(0x3A5A + i, value)
        for point, destination in ((ram[0x3E], 0x38A2), (ram[0x3F], 0x38BC)):
            if point >= 7:
                raise ValueError("Point tile index exceeds seven ROM records")
            record = POINT_TILES[point * 4 : point * 4 + 4]
            for row in range(2):
                for column in range(2):
                    put(destination + row * 0x20 + column, record[row * 2 + column])
        for games, destination in ((ram[0x40], 0x3922), (ram[0x41], 0x393C)):
            if games >= 7:
                raise ValueError("Game tile index exceeds seven ROM records")
            record = GAME_TILES[games * 12 : games * 12 + 12]
            for row in range(6):
                for column in range(2):
                    put(destination + row * 0x20 + column, record[row * 2 + column])
    return writes
