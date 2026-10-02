"""Observe emitted digital silence/signal per channel without source media."""
import math
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
        # Compare digital recordings at retained PCM16 precision, not exact float zero.
        # Inspect channels separately: opposite-phase stereo must not cancel.
        quantized = values if fmt['encoding'] == 'pcm16' else [round(value * 32768) for value in values]
        result.append({'channel': channel, 'nonzero_pcm16_samples': sum(value != 0 for value in quantized),
                       'peak_pcm16': max(abs(value) for value in quantized)})
    return {'first_sample': first, 'last_sample_exclusive': last, 'format': fmt, 'channels': result}


