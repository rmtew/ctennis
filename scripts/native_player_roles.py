"""Inspect a completed native scene; never write runtime state or derive physics."""
import struct
from native_tools import ROOT


def assert_player_roles(mem, num):
    """Call at game_scene_prepared, after actual role/geometry preparation."""
    human = list(struct.iter_unpack('>HHHbb', (ROOT/'assets/native/scene/poses.bin').read_bytes()))
    robot = list(struct.iter_unpack('>HHHbb', (ROOT/'assets/native/scene/robot-poses.bin').read_bytes()))
    world = mem('game_play_state', 60)
    scene = mem('game_scene_objects', 64)
    demo, mode = bool(num('ui_demo')), num('game_mode')
    exchanged = bool(mode & 16)
    result = []
    for end, actor, slot, flag, owner in (
            ('lower', 0, 0, 2, 1 if exchanged else 0),
            ('upper', 10, 24, 1, 0 if exchanged else 1)):
        pose = world[actor+4]
        assert 0 <= pose < 14, ('uncovered native pose', end, pose)
        is_robot = demo or (not (mode & 128) and owner == 1)
        r, top, bottom, dy, dx = (robot if is_robot else human)[pose]
        expected = ((r, (world[actor+2]+dy)&255, (world[actor+3]+dx)&255, 1),
                    (top, world[actor+2], world[actor+3], 2+owner),
                    (bottom, (world[actor+2]+16)&255, world[actor+3], 2+owner))
        for part, (frame, y, x, colour) in enumerate(expected):
            off = slot+8*part
            actual = (int.from_bytes(scene[off+2:off+4], 'big'), scene[off], scene[off+1], scene[off+4])
            assert actual == (frame, y, x, colour), ('completed native role/pose', end, part, actual, expected)
        result.append({'end': end, 'owner': 'P'+str(owner+1), 'role': 'robot' if is_robot else 'human', 'pose': pose})
    return result
