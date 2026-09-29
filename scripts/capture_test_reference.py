"""Explicitly record and freeze an independent MAME serve oracle."""
import configparser
import hashlib
import json
import os
import subprocess
from pathlib import Path
from run_translated_prng_probe import ROOT
from run_translated_player_frame_probe import ROM_SHA256


def main():
    config = configparser.ConfigParser(interpolation=None)
    config.read(ROOT / "config.local.ini", encoding="utf-8")
    cartridge = Path(config['inputs']['cartridge']).read_bytes()
    if hashlib.sha256(cartridge).hexdigest() != ROM_SHA256:
        raise ValueError('Unexpected cartridge')
    out = ROOT / 'build/tests/reference-capture'
    out.mkdir(parents=True, exist_ok=True)
    captures = []
    for name in ('a', 'b'):
        path = out / (name + '.tsv')
        env = os.environ.copy()
        env['CT_TEST_CAPTURE'] = str(path)
        command = [str(ROOT / '.tools/mame-0.289/mame.exe'), 'sc3000', '-noreadconfig',
                   '-hashpath', '.tools/mame-0.289/hash', '-rompath', 'build/mame/roms',
                   '-cart', 'champtns', '-video', 'none', '-sound', 'none', '-skip_gameinfo',
                   '-nothrottle', '-seconds_to_run', '26', '-autoboot_script', 'scripts/capture_test_reference.lua']
        result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, timeout=120)
        (out / (name + '.log')).write_text(result.stdout + result.stderr, encoding='utf-8')
        if result.returncode or 'TEST_REFERENCE_COMPLETE' not in result.stdout:
            raise RuntimeError(result.stdout + result.stderr)
        captures.append(path.read_bytes())
    if captures[0] != captures[1]:
        raise AssertionError('Source captures differ')
    states, tails, events = {}, {}, {}
    for line in captures[0].decode().splitlines():
        kind, frame, value = line.split('\t')
        frame = int(frame)
        if kind == 'S':
            if frame in states:
                raise AssertionError('Duplicate source callback')
            states[frame] = value
        elif kind == 'T':
            tails[frame] = value
        else:
            events.setdefault(frame, []).append(int(value, 16))
    if sorted(states) != list(range(1299, 1500)) or sorted(tails) != sorted(states) or not events:
        raise AssertionError('Incomplete RAM or PSG capture')
    fixture = {'rom_sha256': ROM_SHA256, 'emulator': 'MAME 0.289 sc3000',
               'capture_sha256': hashlib.sha256(captures[0]).hexdigest(), 'repeat_identical': True,
               'initial_pre_tail': states[1299], 'initial_psg': events.get(1299, []),
               'initial_post_tail': tails[1299],
               'updates': [{'frame': frame, 'ram': states[frame], 'post_tail_ram': tails[frame], 'psg': events.get(frame, [])}
                           for frame in range(1300, 1500)]}
    target = ROOT / 'tests/reference/serve.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(fixture, indent=2) + '\n', encoding='utf-8')
    print(f'Frozen 200 source callbacks in {target}; two captures identical')


if __name__ == '__main__':
    main()
