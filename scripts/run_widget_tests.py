"""Renderer-unit comparisons: original captured glyphs through the live Copper backend."""
import argparse
import configparser
import hashlib
import json
import re
from pathlib import Path
from PIL import Image
from copperline_test_session import CopperlineSession
from capture_native_presentation import code_symbols
from run_presentation_tests import ROOT, build_native, digest, native_picture, map_source_palette, compare
from run_translated_prng_probe import ASSEMBLER, run
from run_amiga_score_copper_probe import FIELDS
from presentation_reference import ACTIVE_AREA
from widget_reference import catalog, CASES


def capture(mutation=None):
    directory = ROOT / ('build/tests/native-widgets' + ('-' + mutation if mutation else ''))
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / 'capture.json'
    path.unlink(missing_ok=True)
    build_native({'native_source': 'amiga/gameplay_integration_probe.s'}, directory)
    original = (ROOT / 'amiga/gameplay_integration_probe.s').read_text(encoding='utf-8')
    start, end = original.index('main_loop:'), original.index('; CIA-B timer B')
    harness = '''main_loop:
        bsr     poll_presentation
        tst.b   display_ready
        bne.s   main_loop
widget_wait:
        tst.b   widget_request
        beq.s   main_loop
        bsr     upload_sprite_attributes
        bsr     patch_score_pointers
        clr.b   widget_request
        move.b  #1,display_ready
widget_prepared:
        bra.s   main_loop
widget_request: dc.b 0
        even

'''
    adapted = original[:start] + harness + original[end:]
    if mutation:
        patch = (ROOT / 'amiga/score_copper_patch.i').read_text(encoding='utf-8')
        marker = '        move.b  0(a4,d1.w),d2'
        if patch.count(marker) != 1:
            raise ValueError('Native widget selector instruction changed')
        private = directory / 'wrong-selector.i'
        replacement = '        moveq   #0,d2' if mutation == 'zero' else '        move.b  1(a4,d1.w),d2'
        private.write_text(patch.replace(marker, replacement), encoding='utf-8')
        adapted = adapted.replace('include "amiga/score_copper_patch.i"', f'include "{private.as_posix()}"')
    wrapper = directory / 'native-widgets.s'
    wrapper.write_text(adapted, encoding='utf-8')
    executable, listing = directory / 'native-application', directory / 'native.lst'
    run([str(ASSEMBLER), '-Fhunkexe', '-kick1hunks', '-m68000', '-L', str(listing), '-o', str(executable), str(wrapper)])
    listing_text = listing.read_text()
    symbols = code_symbols(listing_text)
    all_symbols = {n: (s, int(o, 16)) for n, s, o in re.findall(r'^([A-Za-z_][\w]*)\s+([0-9A-Fa-f]{2}):([0-9A-Fa-f]{8})\s*$', listing_text, re.M)}
    section, begin = all_symbols['copperlist']
    if all_symbols['copperlist_end'][0] != section:
        raise ValueError('Copper list sections changed')
    copper_length = all_symbols['copperlist_end'][1] - begin
    config = configparser.ConfigParser(interpolation=None)
    config.read(ROOT / 'config.local.ini', encoding='utf-8')
    ctl = Path(config['tools']['copperline']).with_name('copperline-ctl.exe')
    observations = []
    contract = json.loads((ROOT / 'tests/cases/presentation.json').read_text())
    with CopperlineSession(ctl, ROOT) as session:
        launch = session.inspect('session_launch', {'factory': True, 'model': 'A500',
            'binary': config['tools']['copperline'], 'run': str(executable),
            'args': ['--chipset', 'OCS', '--video', 'PAL', '--cpu', '68000', '--chip', '512K',
                     '--slow', '0', '--fast', '0', '--noaudio', config['inputs']['amiga_rom']]})
        stop = session.inspect('run_until', {'seconds': 30, 'wait_ms': 50000})
        if stop['reason'] != 'loadseg':
            raise RuntimeError('Widget unit executable not loaded')
        base = int(re.search(r'first hunk \$([0-9A-Fa-f]+)', stop['detail']).group(1), 16)
        def read(name, length):
            return session.inspect('mem_read', {'addr': base + symbols[name], 'len': length})['data']
        def target(name):
            event = session.inspect('run_until', {'pc': base + symbols[name], 'wait_ms': 50000})
            if event['reason'] != 'target' or event.get('bridge'):
                raise RuntimeError(f'Widget stop not reached: {name}: {event}')
            return event
        baseline = None
        for value in range(7):
            target('widget_wait')
            selections = [(value + field.index) % field.count for field in FIELDS]
            front = int(read('front_copper', 4), 16)
            before = session.inspect('mem_read', {'addr': front, 'len': copper_length})['data']
            for name, data in (('field_values', bytes(selections).hex()), ('widget_request', '01')):
                reply = session.inspect('mem_write', {'addr': base + symbols[name], 'data': data})
                if reply['written'] != len(bytes.fromhex(data)):
                    raise RuntimeError('Native widget input not written')
            prepared = target('widget_prepared')
            if int(read('front_copper', 4), 16) != front or session.inspect('mem_read', {'addr': front, 'len': copper_length})['data'] != before:
                raise AssertionError('Renderer preparation changed the displayed Copper list')
            committed = target('presentation_commit_in_blank')
            if not (committed['vpos'] < 44 or committed['vpos'] >= 236):
                raise AssertionError('Widget committed on visible scanlines')
            if int(read('front_copper', 4), 16) == front:
                raise AssertionError('Widget did not switch the displayed Copper buffer')
            visible_frame = committed['frame'] + (1 if committed['vpos'] >= 236 else 0)
            while True:
                wrapped = session.inspect('run_until', {'vpos': 0, 'hpos': 0, 'wait_ms': 50000})
                if wrapped['reason'] != 'target' or wrapped.get('bridge'):
                    raise RuntimeError('Widget completed raster not reached')
                if wrapped['frame'] - 1 >= visible_frame:
                    break
            png = directory / f'selection-{value}.png'
            session.inspect('capture_screenshot', {'path': str(png)})
            with Image.open(png) as picture:
                logical = native_picture(picture, contract)
            outside = logical.copy()
            for field in FIELDS:
                outside.paste((0, 0, 0), (field.x, field.y, field.x + field.width, field.y + field.height))
            signature = hashlib.sha256(outside.tobytes()).hexdigest()
            if baseline is not None and signature != baseline:
                raise AssertionError('Widget update changed pixels outside its six rectangles')
            baseline = signature
            if int(read('simulation_updates', 2), 16) != 0:
                raise AssertionError('Widget unit test unexpectedly executed gameplay')
            observations.append({'selection': value, 'field_values': selections, 'prepared': prepared,
                'commit': committed, 'completed_raster': wrapped, 'front_copper_before': front,
                'front_copper_after': int(read('front_copper', 4), 16), 'front_unchanged_during_prepare': True,
                'image': str(png), 'image_sha256': digest(png), 'outside_fields_sha256': signature})
        log = Path(launch['log']).read_text(encoding='utf-8', errors='replace')
        for marker in ('cpu=M68000', 'cpu_clock=7.09MHz', 'chip_ram=512K', 'fast_ram=0K',
                       'slow_ram=0K', 'chipset=Ocs', 'video=Pal', 'Kickstart 1.3'):
            if marker not in log:
                raise ValueError('Widget hardware profile changed')
        (directory / 'copperline.log').write_text(log, encoding='utf-8')
    report = {'mutation': mutation, 'observations': observations, 'executable_sha256': digest(executable),
        'adapter_sha256': digest(wrapper), 'native_source_sha256': digest(ROOT / 'amiga/gameplay_integration_probe.s'),
        'native_backend_sha256': digest(ROOT / 'amiga/score_copper_patch.i'),
        'emulator_sha256': digest(Path(config['tools']['copperline'])), 'bridge_sha256': digest(ctl),
        'kickstart_sha256': digest(Path(config['inputs']['amiga_rom'])), 'gameplay_callbacks': 0}
    path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return path, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--all', action='store_true')
    parser.add_argument('--case', choices=CASES)
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.all == bool(args.case):
        parser.error('Choose --all or --case')
    names = CASES if args.all else (args.case,)
    for name in names:
        (ROOT / f'build/tests/{name}-report.json').unlink(missing_ok=True)
    policy, source = catalog()
    normal_path, normal = capture()
    changes = [(kind, *capture(kind)) for kind in ('zero', 'adjacent')] if args.self_test else []
    contract = json.loads((ROOT / 'tests/cases/presentation.json').read_text())
    passed = True
    for name in names:
        case = json.loads((ROOT / f'tests/cases/{name}.json').read_text())
        field = next(f for f in FIELDS if f.name == case['field'])
        if case['variants'] != policy['required_variants'][field.name]:
            raise ValueError('Widget required selections changed')
        checks, detects, first = [], {kind: [] for kind, _, _ in changes}, None
        for value in case['variants']:
            ref = source[field.name][value]
            with Image.open(ref['image']) as picture:
                wanted = map_source_palette(picture.convert('RGB').crop(ACTIVE_AREA).crop(ref['rectangle']), contract)
            observation = next(row for row in normal['observations'] if row['field_values'][field.index] == value)
            with Image.open(observation['image']) as picture:
                actual = native_picture(picture, contract).crop((field.x, field.y, field.x + field.width, field.y + field.height))
            diff = compare(wanted, actual, 'native-widget-' + field.name)
            if diff:
                diff.update(update=value, x=diff['x'] + field.x, y=diff['y'] + field.y)
            first = first or diff
            checks.append({'value': value, 'source': ref, 'native': observation, 'first_difference': diff})
            for kind, _, changed in changes:
                changed_observation = next(row for row in changed['observations'] if row['field_values'][field.index] == value)
                with Image.open(changed_observation['image']) as picture:
                    altered = native_picture(picture, contract).crop((field.x, field.y, field.x + field.width, field.y + field.height))
                changed_diff = compare(wanted, altered, 'native-widget-' + field.name)
                if changed_diff != compare(wanted, actual, 'native-widget-' + field.name):
                    detects[kind].append(value)
        if changes and not all(detects.values()):
            raise AssertionError('Actual widget selector mutation was not detected: ' + name)
        result = {'case': name, 'passed': first is None, 'first_difference': first, 'checks': checks,
            'self_test': args.self_test, 'mutation_detected_values': detects, 'scope': case['contract'],
            'case_sha256': digest(ROOT / f'tests/cases/{name}.json'),
            'reference_sha256': digest(ROOT / 'tests/reference/presentation/manifest.json'),
            'capture': str(normal_path), 'capture_sha256': digest(normal_path),
            'mutation_captures': {kind: {'path': str(path), 'sha256': digest(path)} for kind, path, _ in changes}}
        (ROOT / f'build/tests/{name}-report.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        passed &= result['passed']
        print(json.dumps({'case': name, 'passed': result['passed'], 'first_difference': first, 'checks': len(checks)}), flush=True)
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
