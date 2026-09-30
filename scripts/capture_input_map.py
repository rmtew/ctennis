"""Capture and retain two-player physical input calibration independently in MAME."""
import hashlib
import json
import os
import subprocess
import configparser
import zipfile
from pathlib import Path
from round_reference import parse_capture
from run_translated_player_frame_probe import ROM_SHA256

ROOT = Path(__file__).resolve().parent.parent


def main():
    config = configparser.ConfigParser(interpolation=None)
    config.read(ROOT / 'config.local.ini', encoding='utf-8')
    cartridge = Path(config['inputs']['cartridge']).read_bytes()
    if hashlib.sha256(cartridge).hexdigest() != ROM_SHA256:
        raise ValueError('Unexpected cartridge')
    with zipfile.ZipFile(ROOT / 'build/mame/roms/sg1000/champtns.zip') as archive:
        if len(archive.namelist()) != 1 or archive.read(archive.namelist()[0]) != cartridge:
            raise ValueError('MAME archive differs from supplied cartridge')
    out = ROOT / 'build/tests/input-map-capture'
    out.mkdir(parents=True, exist_ok=True)
    payloads = []
    command = ['.tools/mame-0.289/mame.exe', 'sc3000', '-noreadconfig', '-hashpath',
               '.tools/mame-0.289/hash', '-rompath', 'build/mame/roms', '-cart', 'champtns',
               '-video', 'none', '-sound', 'none', '-debug', '-debugger', 'none',
               '-skip_gameinfo', '-nothrottle', '-seconds_to_run', '32',
               '-autoboot_script', 'scripts/capture_round_reference.lua']
    for name in ('a', 'b'):
        path = out / f'{name}.tsv'
        env = os.environ.copy()
        env.update(CT_TEST_SELECT='two', CT_TEST_FIRE='0', CT_TEST_CAPTURE=str(path),
                   CT_TEST_POLICY='scripts/calibrate_two_player_inputs.lua', CT_TEST_LAST_FRAME='1860',
                   CT_TEST_CONTACT_MARKERS='0')
        result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, timeout=120)
        (out / f'{name}.log').write_text(result.stdout + result.stderr)
        if result.returncode or 'ROUND_REFERENCE_COMPLETE' not in result.stdout or 'LUA ERROR' in result.stdout + result.stderr:
            raise RuntimeError(result.stdout + result.stderr)
        payloads.append(path.read_bytes())
    if payloads[0] != payloads[1]:
        raise ValueError('Input calibration captures differ')
    callbacks, timeline = parse_capture(payloads[0])
    if bytes.fromhex(callbacks[0]['ram'])[0x3D] != 0x80:
        raise ValueError('Two-player mode was not established')
    controls = [event for event in timeline if event['kind'] == 'control']
    observations = []
    for event in controls:
        if event['value'] != 1:
            continue
        release = next(item for item in controls if item['control'] == event['control']
                       and item['frame'] > event['frame'] and item['value'] == 0)
        rows = [row for row in callbacks if event['frame'] < row['frame'] < release['frame']]
        states = [bytes.fromhex(row['ram']) for row in rows]
        reads = sorted({(read['group'], read['value']) for row in rows for read in row['inputs']})
        player, action = event['control'].split('-', 1)
        value = {'up': 2, 'down': 8, 'left': 4, 'right': 1, 'button1': 16, 'button2': 32}[action]
        expected_reads = [(0, 1), (1, 4)] if event['frame'] == 1820 else [(0, value if player == 'p1' else 0), (1, value if player == 'p2' else 0)]
        if reads != expected_reads:
            raise ValueError(f'Physical input mapping changed: {event["control"]}: {reads}')
        observations.append({'control': event['control'], 'press_frame': event['frame'],
                             'physical_port': f':ctrl{player[1]}:mspad:JOYPAD',
                             'physical_mask': {'up': 1, 'down': 2, 'left': 4, 'right': 8,
                                               'button1': 16, 'button2': 32}[action],
                             'press_value': 1, 'release_value': 0,
                             'release_frame': release['frame'], 'input_reader_returns': reads,
                             'source_updates': [row['ordinal'] for row in rows],
                             'normalized_controls': sorted({(state[0x53], state[0x56]) for state in states}),
                             'position_first_last': {name: [states[0][offset], states[-1][offset]]
                                for name, offset in [('upper_y', 0x45), ('upper_x', 0x46),
                                                     ('lower_y', 0x49), ('lower_x', 0x4A)]}})
    record = {'schema_version': 1, 'repeat_identical': True,
              'rom_sha256': ROM_SHA256,
              'emulator_sha256': hashlib.sha256((ROOT / command[0]).read_bytes()).hexdigest(),
              'script_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                                for name in ('scripts/capture_round_reference.lua',
                                             'scripts/calibrate_two_player_inputs.lua')},
              'capture_sha256': hashlib.sha256(payloads[0]).hexdigest(),
              'mode_selection': {'port': ':sgexp:sk1100:PB5', 'mask': 8,
                                 'press_frame': 120, 'release_frame': 420, 'mode_flags': 128},
              'source_command': command, 'observations': observations,
              'callbacks': callbacks, 'timeline': timeline}
    simultaneous = [item for item in observations if item['press_frame'] == 1820]
    positions = simultaneous[0]['position_first_last']
    if positions['lower_x'][1] <= positions['lower_x'][0] or positions['upper_x'][1] >= positions['upper_x'][0]:
        raise ValueError('Simultaneous independent movement was not observed')
    target = ROOT / 'tests/reference/input-map.json'
    target.write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps({'capture_sha256': record['capture_sha256'],
                      'callbacks': len(callbacks), 'control_observations': len(observations),
                      'repeat_identical': True}, indent=2))


if __name__ == '__main__':
    main()
