"""Explicitly capture original-game WAVs and timed PSG writes twice from reset."""
import argparse
import configparser
import csv
import hashlib
import json
import os
import subprocess
import wave
import zipfile
from pathlib import Path

from capture_test_reference import ROOT, ROM_SHA256
from round_reference import validate_fixture


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def capture(case_name):
    config = configparser.ConfigParser(interpolation=None)
    config.read(ROOT / 'config.local.ini', encoding='utf-8')
    cartridge = Path(config['inputs']['cartridge']).read_bytes()
    if hashlib.sha256(cartridge).hexdigest() != ROM_SHA256:
        raise ValueError('Unexpected source cartridge')
    with zipfile.ZipFile(ROOT / 'build/mame/roms/sg1000/champtns.zip') as archive:
        if len(archive.namelist()) != 1 or archive.read(archive.namelist()[0]) != cartridge:
            raise ValueError('MAME archive differs from configured cartridge')
    parent_path = ROOT / f'tests/reference/{case_name}.json'
    parent = json.loads(parent_path.read_text())
    validate_fixture(parent)
    case_path = ROOT / f'tests/cases/{case_name}.json'
    case = json.loads(case_path.read_text())
    directory = ROOT / f'build/tests/{case_name}-audio'
    directory.mkdir(parents=True, exist_ok=True)
    manifest_path = directory / 'manifest.json'
    manifest_path.unlink(missing_ok=True)
    mame = ROOT / '.tools/mame-0.289/mame.exe'
    runs = []
    for label in ('a', 'b'):
        out = directory / label
        out.mkdir(exist_ok=True)
        raw, events, wav = out / 'callbacks.tsv', out / 'psg-times.tsv', out / 'source.wav'
        env = os.environ.copy()
        env.update(CT_TEST_CAPTURE=str(raw), CT_TEST_LAST_FRAME=str(case['last_begin_frame']),
                   CT_TEST_SELECT='two' if case_name == 'two-player-match' else 'one',
                   CT_TEST_FIRE='0' if case_name == 'two-player-match' else '1',
                   CT_TEST_CONTACT_MARKERS='1' if case_name == 'two-player-match' else '0',
                   CT_TEST_POLICY='scripts/capture_audio_policy.lua',
                   CT_AUDIO_BASE_POLICY=case['capture_policy'], CT_AUDIO_EVENTS=str(events),
                   CT_AUDIO_FRAMES=str(out / 'frame-times.tsv'))
        command = [str(mame), 'sc3000', '-noreadconfig', '-hashpath', '.tools/mame-0.289/hash',
                   '-rompath', 'build/mame/roms', '-cart', 'champtns', '-video', 'none',
                   '-sound', 'none', '-samplerate', '48000', '-volume', '0', '-wavwrite', str(wav),
                   '-debug', '-debugger', 'none', '-skip_gameinfo', '-nothrottle',
                   '-seconds_to_run', str(case['last_begin_frame'] // 60 + 2),
                   '-autoboot_script', 'scripts/capture_round_reference.lua']
        print(f'{case_name}: recording audio {label}', flush=True)
        # No arbitrary timeout terminates a capture; the emulator has a finite
        # emulated stop guard and the caller can observe the same live process.
        result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True)
        (out / 'capture.log').write_text(result.stdout + result.stderr, encoding='utf-8')
        if result.returncode or 'ROUND_REFERENCE_COMPLETE' not in result.stdout or 'LUA ERROR' in result.stdout + result.stderr:
            raise RuntimeError(result.stdout + result.stderr)
        if digest(raw) != parent['capture_sha256']:
            raise ValueError('Audio observation changed accepted source callback recording')
        with events.open(newline='', encoding='utf-8') as stream:
            writes = list(csv.DictReader(stream, delimiter='\t'))
        if not writes:
            raise ValueError('No timed PSG writes')
        with wave.open(str(wav), 'rb') as audio:
            fmt = {'channels': audio.getnchannels(), 'sample_width': audio.getsampwidth(),
                   'sample_rate': audio.getframerate(), 'sample_frames': audio.getnframes()}
            pcm = audio.readframes(audio.getnframes())
        if fmt['sample_rate'] != 48000 or fmt['sample_width'] != 2 or not any(pcm):
            raise ValueError(f'Invalid or silent source audio: {fmt}')
        runs.append({'callbacks_sha256': digest(raw), 'events_sha256': digest(events),
                     'frame_times_sha256': digest(out / 'frame-times.tsv'),
                     'wav_sha256': digest(wav), 'pcm_sha256': hashlib.sha256(pcm).hexdigest(),
                     'wav_format': fmt, 'timed_writes': len(writes), 'command': command})
    equality = ('callbacks_sha256', 'events_sha256', 'frame_times_sha256', 'wav_sha256', 'pcm_sha256', 'wav_format', 'timed_writes')
    if any(runs[0][key] != runs[1][key] for key in equality):
        raise ValueError('Repeated source audio captures differ')
    manifest = {'schema_version': 1, 'source_case': case_name, 'repeat_identical': True,
                'preserved_callbacks': True, 'accepted_complete_P2': False,
                'pending': ['PSG/callback association and event intervals', 'source WAV timing/level measurements', 'native audio adapter/comparison'],
                'rom_sha256': ROM_SHA256, 'parent_sha256': digest(parent_path), 'case_sha256': digest(case_path),
                'emulator_sha256': digest(mame), 'observer_sha256': digest(ROOT / 'scripts/capture_audio_policy.lua'),
                'recorder_sha256': digest(ROOT / 'scripts/capture_round_reference.lua'),
                'policy_sha256': digest(ROOT / case['capture_policy']), 'generator_sha256': digest(Path(__file__)),
                'runs': runs, 'time_origin': 'MAME elapsed emulated time from reset; recorded seconds plus attoseconds at actual IO write'}
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'case': case_name, 'repeat_identical': True, 'wav': runs[0]['wav_format'],
                      'timed_writes': runs[0]['timed_writes'], 'manifest': str(manifest_path)}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=('one-player-match', 'two-player-match'), default='one-player-match')
    capture(parser.parse_args().case)
