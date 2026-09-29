"""Static checks for translated ROM arithmetic and ball/point paths.

Run with: python scripts/check_source_ball_update.py
This does not launch or use an emulator.
"""

import configparser
import hashlib
from pathlib import Path

from ball_math import (
    advance_ball_12ce,
    bounce_121c,
    divide_152b,
    multiply_151e,
    triangular_root_1542,
)
from source_ball_update import (
    ball_dispatch_11a0,
    player_contact_0bf3_0f21,
    player_contact_candidate,
    resolve_pending_point_0989,
)
from source_player_update import (
    SERVE_LOWER,
    SERVE_UPPER,
    TABLE_10D7,
    TABLE_10E0,
    TABLE_E39,
    TABLE_E42,
    TABLE_E4B,
    player_state_0b29_0e54,
)
from source_gameplay_slice import run_gameplay_slice
from source_gameplay_slice import run_translated_frame_body
from source_irq_tail import irq_tail_06b1
from source_audio import AUDIO_TEMPLATE, audio_initialize_1787, audio_tick_17c5
from source_score_display import (
    GAME_TILES,
    MODE_TILES,
    POINT_TILES,
    STATUS_TILES,
    score_gate_094e,
    scoreboard_update_06eb,
)
from source_input_movement import (
    ANIMATION_RECORDS,
    LOWER_BOUNDS,
    SPRITE_DESCRIPTORS,
    UPPER_BOUNDS,
    input_update_0832,
    movement_and_sprites_13b9,
)


def check_integer_routines() -> None:
    for a in range(256):
        for b in range(256):
            assert multiply_151e(a, b) == a * b
    for divisor in range(1, 256):
        for quotient in (0, 1, 2, 7, 31, 127, 255):
            for remainder in (0, divisor // 2, divisor - 1):
                dividend = quotient * divisor + remainder
                if dividend <= 65535:
                    assert divide_152b(dividend, divisor) == (quotient, remainder)
    for n in range(65536):
        k = triangular_root_1542(n)
        assert n <= k * (k + 1)
        assert k == 0 or n > (k - 1) * k


def check_rom_tables() -> None:
    root = Path(__file__).resolve().parent.parent
    config = configparser.ConfigParser(interpolation=None)
    if not config.read(root / "config.local.ini", encoding="utf-8"):
        raise FileNotFoundError("config.local.ini")
    cartridge = Path(config["inputs"]["cartridge"]).read_bytes()
    assert hashlib.sha256(cartridge).hexdigest() == (
        "19bb6647f14ef50f976e8d0a06d389f06b2e700d54a54fb1734d3140f9745ad1"
    )
    for address, table in (
        (0x0B73, SERVE_LOWER),
        (0x0EA0, SERVE_UPPER),
        (0x0E39, TABLE_E39),
        (0x0E42, TABLE_E42),
        (0x0E4B, TABLE_E4B),
        (0x10D7, TABLE_10D7),
        (0x10E0, TABLE_10E0),
        (0x144D, LOWER_BOUNDS),
        (0x147C, UPPER_BOUNDS),
        (0x14FA, ANIMATION_RECORDS),
        (0x115A, SPRITE_DESCRIPTORS),
        (0x0725, STATUS_TILES),
        (0x07A2, MODE_TILES),
        (0x07B1, GAME_TILES),
        (0x0816, POINT_TILES),
        (0x17B9, AUDIO_TEMPLATE),
    ):
        assert cartridge[address : address + len(table)] == table


def check_ball_paths() -> None:
    ram = bytearray(256)
    ram[0x38] = 0x80
    ram[0x57:0x5D] = bytes((1, 2, 3, 4, 5, 6))
    assert ball_dispatch_11a0(ram) == "launch"
    assert ram[0x60:0x66] == bytes((1, 2, 3, 4, 5, 6))
    assert (ram[0x38], ram[0xA1], ram[0xA2], ram[0xA3]) == (0x40, 0xF2, 0x1F, 9)

    for base_y, height_base, flags, result in (
        (0x40, 0x40, 0x40, "flight"),
        (0x40, 0x50, 0x40, "court_bounce"),
        (0x6E, 0x60, 0x48, "net_reflect"),
    ):
        ram = bytearray(256)
        ram[0x38], ram[0x61] = flags, 4
        ram[0x63], ram[0x64], ram[0x65] = height_base, 0x80, base_y
        assert ball_dispatch_11a0(ram) == result
    ram = bytearray(256)
    ram[0x38], ram[0x61] = 0x40, 3
    assert ball_dispatch_11a0(ram) == "outside"
    assert ram[0x39] & 0x80

    ram = bytearray(256)
    ram[0x63], ram[0x64], ram[0x65] = 0x70, 0x80, 0x40
    advance_ball_12ce(ram)
    assert (ram[0x66], ram[0x4E], ram[0x35], ram[0x34], ram[0x4D]) == (
        1, 0x80, 0x80, 0x40, 0x70
    )
    ram = bytearray(256)
    ram[0x34], ram[0x35], ram[0x66], ram[0x62] = 0x70, 0x80, 8, 4
    ram[0x60], ram[0x61], ram[0x43] = 0x20, 0xA0, 0x80
    bounce_121c(ram)
    assert (ram[0x39], ram[0x62], ram[0x60], ram[0x61], ram[0x66], ram[0x43]) == (
        2, 21, 31, 0x9F, 0, 0xE0
    )


def check_contact_and_score() -> None:
    for upper in (False, True):
        ram = bytearray(256)
        if upper:
            ram[0x45], ram[0x46] = 0x40, 0x80
            ram[0x34], ram[0x35], ram[0x39] = 0x63, 0x88, 0
        else:
            ram[0x49], ram[0x4A] = 0x50, 0x80
            ram[0x34], ram[0x35], ram[0x39] = 0x6B, 0x88, 0x40
        ram[0x4D], ram[0x4E], ram[0x72] = ram[0x34] - 3, 0x88, 1
        assert player_contact_candidate(ram, upper=upper)
        assert player_contact_0bf3_0f21(ram, upper=upper)
        assert ram[0x38] & 0x80
        assert ram[0x3B if upper else 0x3A] == 8
        assert ram[0x44 if upper else 0x43] in (0xF1, 0xF2)

    for a, b, expected, points in (
        (0, 0, "point", (1, 0)),
        (2, 3, "deuce", (5, 5)),
        (3, 0, "game", (0, 0)),
        (5, 5, "advantage", (4, 6)),
    ):
        ram = bytearray(256)
        ram[0x3C], ram[0x39], ram[0x3E], ram[0x3F] = 0x40, 0x82, a, b
        assert resolve_pending_point_0989(ram) == expected
        assert (ram[0x3E], ram[0x3F]) == points


def check_player_phases() -> None:
    for upper, source_x, expected_attached_x in ((False, 0x80, 0x94), (True, 0x80, 0x7C)):
        ram = bytearray(256)
        phase = 0x3B if upper else 0x3A
        animation = 0x44 if upper else 0x43
        other_phase = 0x3A if upper else 0x3B
        ram[phase] = 0x80
        ram[0x46 if upper else 0x4A] = source_x
        assert player_state_0b29_0e54(ram, upper=upper) == "serve_setup"
        assert ram[phase] == 0x40 and ram[0x64] == expected_attached_x
        ram[0x3C] = 1 if upper else 2
        ram[0x6C] = 0x50
        assert player_state_0b29_0e54(ram, upper=upper) == "serve_triggered"
        assert ram[phase] == 0x20 and ram[animation] == (0xF3 if upper else 0xF0)
        ram[0x6C] = 0x10
        assert player_state_0b29_0e54(ram, upper=upper) == "serve_launch"
        assert ram[0x38] & 0x80
        ram[0x6C] = 0x20
        assert player_state_0b29_0e54(ram, upper=upper) == "serve_handoff"
        assert ram[other_phase] & 1
        ram[0x6C] = 0x31
        assert player_state_0b29_0e54(ram, upper=upper) == "serve_complete"
        assert ram[phase] == 0x11

    # C039 bit 6 selects which side prepares an AI intercept.
    for upper in (False, True):
        ram = bytearray(256)
        phase = 0x3B if upper else 0x3A
        ram[phase] = 0x04
        ram[0x39] = 0 if upper else 0x40
        ram[0x5B:0x5F] = bytes((0x70, 0x50, 0x80, 0x90))
        ram[0x46 if upper else 0x4A] = 0x80
        assert player_state_0b29_0e54(ram, upper=upper) == "ai_target_setup"
        assert ram[phase] == 0x02

    ram = bytearray(256)
    ram[0x3A] = 0x02
    ram[0x3C] = 0x42
    ram[0x39] = 0x40
    ram[0x73:0x75] = bytes((0x70, 0x90))
    ram[0x49:0x4B] = bytes((0x60, 0x80))
    assert player_state_0b29_0e54(ram, upper=False) == "ai_move"
    assert ram[0x53] & 0xF0


def check_source_order_slice() -> None:
    ram = bytearray(256)
    ram[0x3C], ram[0x39] = 0x40, 0x82
    result = run_gameplay_slice(ram)
    assert (result[0].name, *result[1:]) == ("point", "idle", "idle", "idle")
    assert (ram[0x3E], ram[0x3C]) == (1, 0x20)
    ram = bytearray(256)
    ram[0x3A], ram[0x4A] = 0x80, 0x80
    result = run_gameplay_slice(ram)
    assert (result[0].name, *result[1:]) == ("idle", "serve_setup", "idle", "idle")
    assert ram[0x3A] == 0x40 and ram[0x64] == 0x94


def check_input_movement_sprites() -> None:
    ram = bytearray(256)
    ram[0x3D] = 4
    input_update_0832(ram)
    assert (ram[0x53], ram[0x56]) == (0, 0)
    ram[0x3D] = 0
    input_update_0832(ram, game_bits=0x35)
    assert (ram[0x53], ram[0x56]) == (5, 3)
    ram[0x3D] = 0x80
    input_update_0832(ram, game_bits=0x35, keyboard_bits=0x2A)
    assert (ram[0x53], ram[0x56]) == (0xA5, 0x23)

    ram = bytearray(256)
    ram[0x49], ram[0x4A] = 0x98, 0x90
    result = run_translated_frame_body(ram, bytearray(0x4000), game_bits=1)
    assert result.prior_sprite_upload == bytes(40)
    assert (result.score.name, result.lower_path, result.upper_path, result.ball_path) == (
        "idle", "idle", "idle", "idle"
    )
    assert ram[0x4A] == 0x91 and result.ball_slot == 0x30
    assert ram[0x14 + 2] == 0x30  # lower descriptor zero, first pattern

    ram = bytearray(256)
    ram[0x43] = 0x10
    ram[0x49], ram[0x4A] = 0x98, 0x90
    movement_and_sprites_13b9(ram)
    assert ram[0x43] & 0x08
    assert ram[0x6D] == 0
    assert ram[0x4B] == 8  # lower animation writes lower descriptor selector
    assert ram[0x14 + 2] == SPRITE_DESCRIPTORS[8 * 5]


def check_scoreboard_and_tail() -> None:
    ram, vram = bytearray(256), bytearray(0x4000)
    ram[0x42] = 0xA1  # pending status record 1 and full redraw
    ram[0x3E], ram[0x3F], ram[0x40], ram[0x41] = 1, 2, 1, 2
    writes = scoreboard_update_06eb(ram, vram)
    assert len(writes) == 3 + 5 + 4 + 4 + 12 + 12
    assert vram[0x398E:0x3991] == STATUS_TILES[3:6]
    assert vram[0x3A5A:0x3A5F] == MODE_TILES[5:10]
    assert (vram[0x38A2], vram[0x38A3], vram[0x38C2], vram[0x38C3]) == tuple(
        POINT_TILES[4:8]
    )
    assert ram[0x42] & 0x40 and not ram[0x42] & 0x20

    ram = bytearray(256)
    ram[0x3C], ram[0x6C] = 0x20, 0x40
    event = score_gate_094e(ram)
    assert event.name == "positions_reset" and len(event.extra_sprite_upload or b"") == 40
    assert (ram[0x49], ram[0x4A], ram[0x45], ram[0x46]) == (0x98, 0xB8, 8, 0x50)
    ram[0x6C] = 0xC0
    assert score_gate_094e(ram).name == "point_sound"
    assert (ram[0x3C], ram[0xA1], ram[0xA2], ram[0xA3]) == (0x80, 0xDC, 0x1F, 0x17)
    ram[0xA4] = ram[0xA5]
    assert score_gate_094e(ram).name == "round_reset"
    assert ram[0x3C] == 0x40 and ram[0x3A] == 0x80

    ram = bytearray(256)
    ram[0x02] = 0x83
    ram[0x6B], ram[0x6C], ram[0x83] = 0xFF, 0xFE, 2
    due, control, psg = irq_tail_06b1(ram)
    assert not due and control == (0xE2, 0x81, 0x0F, 0x82) and not psg
    assert (ram[0x6B], ram[0x6C], ram[0x83], ram[0x02]) == (0, 0xFF, 1, 3)


def check_first_audio_stream() -> None:
    root = Path(__file__).resolve().parent.parent
    config = configparser.ConfigParser(interpolation=None)
    config.read(root / "config.local.ini", encoding="utf-8")
    rom = Path(config["inputs"]["cartridge"]).read_bytes()
    ram = bytearray(256)
    assert audio_initialize_1787(ram) == (0xFF, 0xDF, 0xBF)
    ram[0x3C], ram[0x6C] = 0x20, 0xC0
    assert score_gate_094e(ram).name == "point_sound"
    first_seven = []
    for _ in range(7):
        emitted = audio_tick_17c5(ram, rom)
        assert emitted[-3:-1] == (0xC4, 0x05)
        first_seven.append(emitted[-1])
    assert first_seven == [0xD0, 0xD1, 0xD0, 0xD1, 0xD0, 0xD1, 0xD0]
    assert ram[0x83] == ram[0x82] == 1

    # Two source streams start together: channel 1 period 0D5, channel 0 07F.
    ram = bytearray(256)
    audio_initialize_1787(ram)
    for base, start, length in ((0x85, 0x1F05, 0x4E), (0x93, 0x1F53, 0x44)):
        pointer = start - 1
        ram[base], ram[base + 1] = pointer & 0xFF, pointer >> 8
        ram[base + 2 : base + 5] = bytes((length + 1, 0, 1))
        ram[base + 13] = 0
    emitted = audio_tick_17c5(ram, rom)
    assert emitted[:2] == (0xA5, 0x0D)
    assert (0x8F, 0x07) == emitted[4:6]

    ram = bytearray(256)
    audio_initialize_1787(ram)
    ram[0x83] = 1
    frame = run_translated_frame_body(ram, bytearray(0x4000), game_bits=0, rom=rom)
    assert frame.audio_due and ram[0x83] == ram[0x82] == 2


if __name__ == "__main__":
    check_rom_tables()
    check_integer_routines()
    check_ball_paths()
    check_contact_and_score()
    check_player_phases()
    check_source_order_slice()
    check_input_movement_sprites()
    check_scoreboard_and_tail()
    check_first_audio_stream()
    print("Static source ball-update checks passed")
