"""Check emitted signal/mute at the independently retained PCM16 precision."""
import math
from pathlib import Path

from audio_wave import read_wave


def pcm16_window(path, start, duration):
    if not math.isfinite(start) or not math.isfinite(duration) or duration <= 0:
        raise ValueError('Invalid audio criterion window')
    fmt, samples = read_wave(path)
    first = math.ceil(start * fmt['sample_rate'])
    last = math.floor((start + duration) * fmt['sample_rate'])
    if first < 0 or last > fmt['sample_frames'] or last <= first:
        raise ValueError('Audio criterion window is not fully retained')
    result = []
    for channel in range(fmt['channels']):
        values = samples[first * fmt['channels'] + channel:last * fmt['channels']:fmt['channels']]
        if not all(math.isfinite(value) for value in values):
            raise ValueError('Nonfinite audio output')
        # Compare digital recordings at source precision, not exact float zero.
        # Inspect channels separately: opposite-phase stereo must not cancel.
        quantized = values if fmt['encoding'] == 'pcm16' else [round(value * 32768) for value in values]
        result.append({'channel': channel, 'nonzero_pcm16_samples': sum(value != 0 for value in quantized),
                       'peak_pcm16': max(abs(value) for value in quantized)})
    return {'first_sample': first, 'last_sample_exclusive': last, 'format': fmt, 'channels': result}


def check_emitted_mute(case, source, source_directory, captured):
    if any(row['state_differences'] for row in captured['observations']):
        raise ValueError('Mute waveform capture differs from original game state')
    for event in captured['audio_events']:
        original = [row for row in source['timed_events'] if row.get('retained_parent_event') and row.get('callback') == event['update']]
        if [row['value'] for row in original] != list(bytes.fromhex(event['psg'])):
            raise ValueError('Mute waveform capture has different PSG events')
    original = [row for row in source['timed_events'] if row.get('retained_parent_event') and row.get('callback') == case['mute_update']]
    if not original:
        raise ValueError('Missing original mute event')
    event = original[-1]
    if any(tone['attenuation'] != 15 for tone in event['tones_after']) or event['noise_audible_after']:
        raise ValueError('Original event does not mute all channels')
    source_time = event['time_attoseconds'] / 1e18
    native_time = next(row['stop']['seconds'] for row in captured['audio_events'] if row['update'] == case['mute_update'])
    checks = []
    for recipe in case['waveform_windows']:
        if recipe['kind'] not in ('audible', 'silent'):
            raise ValueError('Unknown emitted audio criterion')
        offset, duration = recipe['offset_seconds'], recipe['duration_seconds']
        first, last = source_time + offset, source_time + offset + duration
        # Quiet output cannot be expected across a subsequent audible command.
        if recipe['kind'] == 'silent' and any(first <= row['time_attoseconds'] / 1e18 < last
                and (any(tone['attenuation'] != 15 for tone in row['tones_after']) or row['noise_audible_after'])
                for row in source['timed_events']):
            raise ValueError('Source quiet window contains an audible command')
        expected = pcm16_window(source_directory / 'a/source.wav', first, duration)
        if expected['format']['encoding'] != 'pcm16':
            raise ValueError('Independent expectation requires original PCM16 precision')
        actual = pcm16_window(Path(captured['native_wav']), native_time + offset, duration)
        original_signal = any(row['nonzero_pcm16_samples'] for row in expected['channels'])
        native_signal = any(row['nonzero_pcm16_samples'] for row in actual['channels'])
        wanted = recipe['kind'] == 'audible'
        if original_signal != wanted:
            raise ValueError('Independent source waveform does not establish the declared expectation')
        difference = None if native_signal == wanted else {
            'update': case['mute_update'], 'boundary': 'emitted-audio-pcm16',
            'field': recipe['kind'] + ' waveform window', 'expected': wanted, 'actual': native_signal}
        checks.append({'kind': recipe['kind'], 'offset_seconds': offset, 'duration_seconds': duration,
                       'source': expected, 'native': actual, 'first_difference': difference})
    return {'checks': checks, 'first_difference': next((row['first_difference'] for row in checks if row['first_difference']), None),
            'criterion': 'Audible before mute and silent after mute, in every output channel at source PCM16 recording precision.',
            'scope': 'Bounded signal presence/silence. Debugger timestamps locate windows; exact onset/decay deadlines and analogue inaudibility are not established.'}
