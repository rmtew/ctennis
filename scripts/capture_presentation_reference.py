"""Capture lossless source rasters and hardware state alongside a frozen replay."""
import argparse
import configparser
import hashlib
import json
import os
import re
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
    parser.add_argument('--case', choices=('one-player-match', 'two-player-match', 'one-player-restart-complete', 'two-player-restart-complete'), default='one-player-match')
    parser.add_argument('--recipe', help='Additional bounded source checkpoints; retain separately from the primary media')
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
    if args.case.endswith('-restart-complete'):
        from regime_reference import validate_extension, load_reference
        base_name = args.case.replace('-restart-complete', '-match')
        validate_extension(parent, {'continuous_parent': base_name})
        parent = {**parent, 'milestones': load_reference(base_name)[0]['milestones']}
    case = json.loads((ROOT / f'tests/cases/{args.case}.json').read_text())
    out = ROOT / f'build/tests/{args.case}-presentation'
    extra = json.loads((ROOT / args.recipe).read_text()) if args.recipe else None
    if extra:
        if extra['source_case'] != args.case or not re.fullmatch('[a-z0-9-]+', extra['capture_label']):
            raise ValueError('Invalid supplemental source recipe')
        out = out.with_name(out.name + '-' + extra['capture_label'])
    out.mkdir(parents=True, exist_ok=True)
    (out / 'manifest.json').unlink(missing_ok=True)
    # Keep surrounding rasters: callback completion and visible scanout need not coincide.
    named = {'startup': 100, 'title': 300, 'selection-input': 120,
             'accepted-mode': 1299, **{name: item['frame'] for name, item in parent['milestones'].items()}}
    trigger_updates = {}
    def checkpoint(name, row):
        if name not in named:
            named[name] = row['end_frame']
            trigger_updates[name] = row['ordinal']
    initial = bytes.fromhex(parent['initial_post_tail'])
    for side, offset in (('lower', 0x3A), ('upper', 0x3B)):
        if initial[offset] & 0x40:
            named[f'serve-{side}-wait'] = parent['initial_callback']['end_frame']
            trigger_updates[f'serve-{side}-wait'] = 0
    seen_scores = set()
    for row in parent['updates']:
        ram = bytes.fromhex(row['post_tail_ram'])
        entry = bytes.fromhex(row['entry_ram'])
        body = bytes.fromhex(row['ram'])
        for side, offset in (('lower', 0x3A), ('upper', 0x3B)):
            if body[offset] & 0x40:
                checkpoint(f'serve-{side}-wait', row)
            if entry[offset] & 0x40 and body[offset] & 0x20:
                checkpoint(f'serve-{side}-action', row)
            if entry[offset] & 0x20 and entry[0x6C] == 0x10:
                checkpoint(f'serve-{side}-launch', row)
            if entry[offset] & 0x20 and entry[0x6C] == 0x11 and body[0x66] > 0:
                checkpoint(f'serve-{side}-first-flight', row)
        if not entry[0x39] & 2 and body[0x39] & 2:
            checkpoint('first-court-bounce', row)
        if not entry[0x39] & 1 and body[0x39] & 1:
            checkpoint('first-net-reflection', row)
        if not entry[0x39] & 8 and body[0x39] & 8:
            checkpoint('first-outside-court-contact', row)
        if body[0x42] & 0xC0 == 0xC0 and entry[0x42] & 0xC0 != 0xC0:
            checkpoint(f'status-{body[0x42] & 7}-appears', row)
        if entry[0x42] & 0xC0 == 0xC0 and not body[0x42] & 0x80:
            checkpoint(f'status-{entry[0x42] & 7}-disappears', row)
        pair = tuple(ram[0x3E:0x40])
        if pair not in seen_scores:
            seen_scores.add(pair)
            checkpoint(f'point-codes-{pair[0]}-{pair[1]}', row)
    for event in parent['timeline']:
        if event['kind'] == 'M' and event.get('pc') in (0x0C9F, 0x0FD3):
            name = 'lower-contact' if event['pc'] == 0x0C9F else 'upper-contact'
            named.setdefault(name, event['frame'])
        if event['kind'] == 'M' and parent['milestones']['match_award']['update'] <= event['after_callback'] <= parent['milestones']['restart_selection']['update']:
            if event.get('pc') == 0x0580:
                named.setdefault('match-result-sound-start', event['frame'])
            elif event.get('pc') == 0x0109:
                named.setdefault('return-to-title', event['frame'])
    field_requests = {}
    if extra:
        named, trigger_updates = {}, {}
        for name, checkpoint in extra['checkpoints'].items():
            row = parent['updates'][checkpoint['update'] - 1]
            ram = bytes.fromhex(row['post_tail_ram'])
            if list(ram[0x3e:0x42]) != checkpoint['scores']:
                raise ValueError('Supplemental scoring checkpoint differs from the original')
            named[name], trigger_updates[name] = row['end_frame'], row['ordinal']
            field_requests[name] = dict(point_a=ram[0x3e], point_b=ram[0x3f],
                games_a=ram[0x40], games_b=ram[0x41],
                mode=0 if ram[0x3d] & 4 else 2 if ram[0x3d] & 128 else 1)
            if checkpoint.get('fields') == []:
                field_requests[name] = {}
    window = extra['raster_window'] if extra else [-2, 4]
    frames = sorted({frame + delta for frame in named.values() for delta in range(window[0], window[1] + 1)
                     if 0 < frame + delta <= parent['updates'][-1]['end_frame'] + 1})
    targets = out / 'targets.lua'
    targets.write_text('return {' + ','.join(f'[{frame}]=true' for frame in frames) + '}\n')
    runs, commands = [], []
    for run in ('a', 'b'):
        directory = out / run
        directory.mkdir(exist_ok=True)
        raw = directory / 'callbacks.tsv'
        env = os.environ.copy()
        env.update(CT_TEST_CAPTURE=str(raw), CT_TEST_LAST_FRAME=str(case['last_begin_frame']),
                   CT_TEST_SELECT='two' if args.case.startswith('two-player-') else 'one',
                   CT_TEST_FIRE='0' if args.case.startswith('two-player-') else '1',
                   CT_TEST_CONTACT_MARKERS='1' if args.case.startswith('two-player-') else '0',
                   CT_TEST_POLICY='scripts/capture_presentation_policy.lua',
                   CT_MEDIA_BASE_POLICY=case['capture_policy'], CT_MEDIA_TARGETS=str(targets),
                   CT_MEDIA_DIRECTORY=str(directory))
        command = [str(ROOT / '.tools/mame-0.289/mame.exe'), 'sc3000', '-noreadconfig',
                   '-hashpath', '.tools/mame-0.289/hash', '-rompath', 'build/mame/roms',
                   '-cart', 'champtns', '-video', 'none', '-sound', 'none', '-debug',
                   '-debugger', 'none', '-skip_gameinfo', '-nothrottle', '-seconds_to_run',
                   str(case['last_begin_frame'] // 60 + 2), '-snapshot_directory', str(directory),
                   '-autoboot_script', 'scripts/capture_round_reference.lua']
        commands.append(command)
        result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, timeout=180)
        (directory / 'capture.log').write_text(result.stdout + result.stderr, encoding='utf-8')
        if result.returncode or 'ROUND_REFERENCE_COMPLETE' not in result.stdout or 'LUA ERROR' in result.stdout + result.stderr:
            raise RuntimeError(result.stdout + result.stderr)
        if sha(raw.read_bytes()) != parent['capture_sha256']:
            raise ValueError('Media observer changed the frozen callback recording')
        samples = []
        for frame in frames:
            stem = f'f{frame:05d}'
            size = list(map(int, (directory / (stem + '.raster')).read_text().split()))
            raw_pixels = (directory / (stem + '.pixels')).read_bytes()
            if len(raw_pixels) != size[0] * size[1] * 4:
                raise ValueError(f'Incomplete raster {stem}')
            # screen:pixels is the already-rendered RGB bitmap, packed as host-endian u32.
            # The pinned Windows MAME is little endian. Preserve native bitmap pixels
            # without a layout, scaling or interpolation pass through snapshot rendering.
            rgb = Image.frombytes('RGBA', tuple(size), raw_pixels, 'raw', 'BGRA').convert('RGB')
            rgb.save(directory / (stem + '.png'))
            if size != [280, 216]:
                raise ValueError(f'Unexpected MAME raster geometry: {size}')
            rgb.crop((12, 12, 268, 204)).save(directory / (stem + '.active.png'))
            pixels = sha(rgb.tobytes())
            files = {suffix: sha((directory / (stem + '.' + suffix)).read_bytes())
                     for suffix in ('ram', 'vram', 'regs', 'pc', 'pixels', 'raster')}
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
    title = [row['rgb_sha256'] for row in runs[0] if 299 <= row['frame'] <= 302]
    if not extra and (len(title) != 4 or len(set(title)) != 1):
        raise ValueError('Stable title adjacent rasters differ')
    manifest = dict(schema_version=1, rom_sha256=ROM_SHA256,
                    accepted_graphics_oracle=False,
                    pending_validation=['first visible update and source presentation lag', 'remaining P1 windows'],
                    parent_reference_sha256=sha(parent_bytes), source_case=args.case,
                    repeat_identical=True, observer_preserved_callback_capture=True,
                    raster='screen:pixels Windows little-endian RGB words; no snapshot rendering',
                    active_area=[12, 12, 268, 204],
                    geometry_source='MAME mame0289 src/devices/video/tms9928a.cpp device_config_complete',
                    capture_boundary='frame_done after frozen input policy; RAM is contemporaneous, not asserted post-tail',
                    named_frames=named, trigger_updates=trigger_updates, samples=runs[0],
                    field_requests=field_requests, supplemental_recipe=args.recipe,
                    supplemental_recipe_sha256=sha((ROOT / args.recipe).read_bytes()) if extra else None,
                    observer_sha256=sha((ROOT / 'scripts/capture_presentation_policy.lua').read_bytes()),
                    recorder_sha256=sha((ROOT / 'scripts/capture_round_reference.lua').read_bytes()),
                    policy_sha256=sha((ROOT / case['capture_policy']).read_bytes()),
                    generator_sha256=sha(Path(__file__).read_bytes()), source_commands=commands,
                    emulator_sha256=sha((ROOT / '.tools/mame-0.289/mame.exe').read_bytes()),
                    case_sha256=sha((ROOT / f'tests/cases/{args.case}.json').read_bytes()))
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(case=args.case, samples=len(frames), repeat_identical=True,
                          preserved_callbacks=True, manifest=str(out / 'manifest.json')), indent=2))


if __name__ == '__main__':
    main()
