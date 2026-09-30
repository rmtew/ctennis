"""Capture lossless source rasters and hardware state alongside a frozen replay."""
import argparse
import configparser
import hashlib
import json
import os
import subprocess
import zipfile
from pathlib import Path

from PIL import Image
from capture_test_reference import ROOT, ROM_SHA256
from round_reference import validate_fixture


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=('one-player-match', 'two-player-match'), default='one-player-match')
    args = parser.parse_args()
    config = configparser.ConfigParser(interpolation=None)
    config.read(ROOT / 'config.local.ini', encoding='utf-8')
    cartridge = Path(config['inputs']['cartridge']).read_bytes()
    if sha(cartridge) != ROM_SHA256:
        raise ValueError('Unexpected cartridge')
    with zipfile.ZipFile(ROOT / 'build/mame/roms/sg1000/champtns.zip') as archive:
        if len(archive.namelist()) != 1 or archive.read(archive.namelist()[0]) != cartridge:
            raise ValueError('MAME archive differs from configured cartridge')
    parent_path = ROOT / f'tests/reference/{args.case}.json'
    parent_bytes = parent_path.read_bytes()
    parent = json.loads(parent_bytes)
    validate_fixture(parent)
    case = json.loads((ROOT / f'tests/cases/{args.case}.json').read_text())
    out = ROOT / f'build/tests/{args.case}-presentation'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'manifest.json').unlink(missing_ok=True)
    # Keep surrounding rasters: callback completion and visible scanout need not coincide.
    named = {'startup': 100, 'title-candidate': 300, 'selection-input': 120, 'serve-wait': 1299,
             'serve-input': 1300, **{name: item['frame'] for name, item in parent['milestones'].items()}}
    seen_scores = set()
    for row in parent['updates']:
        ram = bytes.fromhex(row['post_tail_ram'])
        pair = tuple(ram[0x3E:0x40])
        if pair not in seen_scores:
            seen_scores.add(pair)
            named[f'point-codes-{pair[0]}-{pair[1]}'] = row['end_frame']
    for event in parent['timeline']:
        if event['kind'] == 'M' and event.get('pc') in (0x0C9F, 0x0FD3):
            name = 'lower-contact' if event['pc'] == 0x0C9F else 'upper-contact'
            named.setdefault(name, event['frame'])
    frames = sorted({frame + delta for frame in named.values() for delta in (-1, 0, 1, 2)
                     if 0 < frame + delta <= parent['updates'][-1]['end_frame'] + 1})
    targets = out / 'targets.lua'
    targets.write_text('return {' + ','.join(f'[{frame}]=true' for frame in frames) + '}\n')
    runs = []
    for run in ('a', 'b'):
        directory = out / run
        directory.mkdir(exist_ok=True)
        raw = directory / 'callbacks.tsv'
        env = os.environ.copy()
        env.update(CT_TEST_CAPTURE=str(raw), CT_TEST_LAST_FRAME=str(case['last_begin_frame']),
                   CT_TEST_SELECT='two' if args.case == 'two-player-match' else 'one',
                   CT_TEST_FIRE='0' if args.case == 'two-player-match' else '1',
                   CT_TEST_CONTACT_MARKERS='1' if args.case == 'two-player-match' else '0',
                   CT_TEST_POLICY='scripts/capture_presentation_policy.lua',
                   CT_MEDIA_BASE_POLICY=case['capture_policy'], CT_MEDIA_TARGETS=str(targets),
                   CT_MEDIA_DIRECTORY=str(directory))
        command = [str(ROOT / '.tools/mame-0.289/mame.exe'), 'sc3000', '-noreadconfig',
                   '-hashpath', '.tools/mame-0.289/hash', '-rompath', 'build/mame/roms',
                   '-cart', 'champtns', '-video', 'none', '-sound', 'none', '-debug',
                   '-debugger', 'none', '-skip_gameinfo', '-nothrottle', '-seconds_to_run',
                   str(case['last_begin_frame'] // 60 + 2), '-snapshot_directory', str(directory),
                   '-autoboot_script', 'scripts/capture_round_reference.lua']
        result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, timeout=180)
        (directory / 'capture.log').write_text(result.stdout + result.stderr, encoding='utf-8')
        if result.returncode or 'ROUND_REFERENCE_COMPLETE' not in result.stdout or 'LUA ERROR' in result.stdout + result.stderr:
            raise RuntimeError(result.stdout + result.stderr)
        if sha(raw.read_bytes()) != parent['capture_sha256']:
            raise ValueError('Media observer changed the frozen callback recording')
        samples = []
        for frame in frames:
            stem = f'f{frame:05d}'
            with Image.open(directory / (stem + '.png')) as picture:
                rgb = picture.convert('RGB')
                size = list(rgb.size)
                pixels = sha(rgb.tobytes())
            files = {suffix: sha((directory / (stem + '.' + suffix)).read_bytes())
                     for suffix in ('ram', 'vram', 'regs', 'pc')}
            for suffix, expected_length in (('ram', 1024), ('vram', 16384), ('regs', 8)):
                if (directory / (stem + '.' + suffix)).stat().st_size != expected_length:
                    raise ValueError(f'Incomplete {stem}.{suffix}')
            completed = [row for row in parent['updates'] if row['end_frame'] < frame]
            active = [row['ordinal'] for row in parent['updates']
                      if row['begin_frame'] < frame <= row['end_frame']]
            samples.append(dict(frame=frame, size=size, rgb_sha256=pixels, hardware_sha256=files,
                                last_completed_update=completed[-1]['ordinal'] if completed else None,
                                active_updates=active))
        runs.append(samples)
    if runs[0] != runs[1]:
        raise ValueError('Repeated media captures differ')
    manifest = dict(schema_version=1, rom_sha256=ROM_SHA256,
                    accepted_graphics_oracle=False,
                    pending_validation=['alternating incomplete title raster', 'active-area crop',
                                        'first visible update and source presentation lag', 'remaining P1 windows'],
                    parent_reference_sha256=sha(parent_bytes), source_case=args.case,
                    repeat_identical=True, observer_preserved_callback_capture=True,
                    raster='raw MAME raster including border; active crop not yet verified',
                    capture_boundary='frame_done after frozen input policy; RAM is contemporaneous, not asserted post-tail',
                    named_frames=named, samples=runs[0],
                    observer_sha256=sha((ROOT / 'scripts/capture_presentation_policy.lua').read_bytes()),
                    recorder_sha256=sha((ROOT / 'scripts/capture_round_reference.lua').read_bytes()),
                    policy_sha256=sha((ROOT / case['capture_policy']).read_bytes()),
                    emulator_sha256=sha((ROOT / '.tools/mame-0.289/mame.exe').read_bytes()),
                    case_sha256=sha((ROOT / f'tests/cases/{args.case}.json').read_bytes()))
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(case=args.case, samples=len(frames), repeat_identical=True,
                          preserved_callbacks=True, manifest=str(out / 'manifest.json')), indent=2))


if __name__ == '__main__':
    main()
