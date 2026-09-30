"""Measure retained mute tails; diagnostic evidence, not a waveform acceptance gate."""
import json
import math
from pathlib import Path

from audio_wave import read_wave
from run_audio_tests import source_record
from run_presentation_tests import ROOT, digest


def measure(path, start, duration):
    fmt, samples = read_wave(path)
    first = math.ceil(start * fmt['sample_rate'])
    last = math.floor((start + duration) * fmt['sample_rate'])
    if first < 0 or last > fmt['sample_frames'] or last <= first:
        raise ValueError('Requested mute window is not fully retained')
    values = samples[first * fmt['channels']:last * fmt['channels']]
    if not all(math.isfinite(value) for value in values):
        raise ValueError('Nonfinite audio samples')
    scale = 32768 if fmt['encoding'] == 'pcm16' else 1
    return {'format': fmt, 'first_sample': first, 'last_sample_exclusive': last,
            'peak_normalized': max(abs(value) for value in values) / scale,
            'rms_normalized': math.sqrt(sum((value / scale) ** 2 for value in values) / len(values)),
            'exact_zero_samples': sum(value == 0 for value in values),
            'sample_values': len(values), 'wav_sha256': digest(path)}


def main():
    case = json.loads((ROOT / 'tests/cases/p2-first-serve-mute.json').read_text())
    report = json.loads((ROOT / 'build/tests/p2-first-serve-mute-report.json').read_text())
    capture_path = Path(report['capture_report_path'])
    if digest(capture_path) != report['capture_report_sha256']:
        raise ValueError('Native capture report changed')
    capture = json.loads(capture_path.read_text())
    native = Path(capture['native_wav'])
    if digest(native) != report['native_wav_sha256']:
        raise ValueError('Native waveform changed')
    source, directory, _ = source_record(case)
    original = [event for event in source['timed_events']
                if event.get('retained_parent_event') and event.get('callback') == case['mute_update']]
    if not original or any(tone['attenuation'] != 15 for tone in original[-1]['tones_after']) or original[-1]['noise_audible_after']:
        raise ValueError('Original boundary is not all muted')
    original_time = original[-1]['time_attoseconds'] / 1e18
    native_time = next(row['stop']['seconds'] for row in capture['audio_events'] if row['update'] == case['mute_update'])
    rows = []
    for delay in (.005, .010, .020):
        rows.append({'delay_seconds': delay, 'duration_seconds': .020,
                     'source': measure(directory / 'a/source.wav', original_time + delay, .020),
                     'native': measure(native, native_time + delay, .020)})
    result = {'requirement': 'Emitted first-serve sound decays to silence after the original mute event',
              'acceptance_established': False,
              'limitation': 'Measured tails only; no waveform tolerance or onset/deadline acceptance inferred. Native timestamp is the debugger stop, not an exact audio-sample marker.',
              'source_mute_seconds': original_time, 'native_mute_stop_seconds': native_time,
              'measurements': rows}
    path = ROOT / 'build/tests/mute-waveform-inspection.json'
    path.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
