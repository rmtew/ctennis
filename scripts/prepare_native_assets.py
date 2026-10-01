"""Explicit offline preparation of private original assets, separate from build.

Requires already verified private captures and legitimate local cartridge.
Never distribute the outputs or ROMs through the public repository.
"""
from native_tools import ROOT, run
import sys

def prepare():
    from generate_amiga_sprite_probe import main as background
    from generate_native_scene_assets import generate as scene
    from generate_native_audio_assets import generate as audio
    from generate_native_title import generate as title
    from run_amiga_score_copper_probe import make_banks, make_copper_and_patch_tables
    background(); scene(); audio(); title()
    make_banks((ROOT/'build/reference/source-timing/sprite-f1310.vram').read_bytes())
    make_copper_and_patch_tables()

if __name__=='__main__':
    prepare()
