"""Associate repeated original WAVs with exact callback PSG writes and intervals.

Test-only PSG register decoding follows pinned MAME mame0289 sn76496.cpp.
Expected sound is the captured original output, never a synthesized waveform.
"""
import argparse
import array
import csv
import json
import math
import wave

from capture_source_audio_reference import ROOT, digest

ATTO = 10 ** 18
PSG_CLOCK = 3579545


def read_times(path):
    with path.open(newline='', encoding='utf-8') as stream:
        rows = list(csv.DictReader(stream, delimiter='\t'))
    for row in rows:
        row['time_attoseconds'] = int(row['seconds']) * ATTO + int(row['attoseconds'])
        row['frame'] = int(row['frame'])
        if 'value' in row:
            row['value'], row['pc'] = int(row['value'], 16), int(row['pc'], 16)
    if any(b['time_attoseconds'] < a['time_attoseconds'] for a, b in zip(rows, rows[1:])):
        raise ValueError('Nonmonotonic source audio timestamps')
    return rows


def decode_registers(events):
    registers, latched = [0] * 8, 0  # pinned non-Sega SN76489A reset state
    for event in events:
        value = event['value']
        if value & 128:
            latched = (value >> 4) & 7
            registers[latched] = (registers[latched] & 0x3f0) | (value & 15)
        elif latched in (0, 2, 4):
            registers[latched] = (registers[latched] & 15) | ((value & 63) << 4)
        else:
            registers[latched] = (registers[latched] & 0x3f0) | (value & 15)
        event['registers_after'] = registers.copy()
        event['selected_register'] = latched
        event['tones_after'] = [{'divisor': registers[2 * channel] or 1024,
                                'attenuation': registers[2 * channel + 1] & 15,
                                'frequency_hz': PSG_CLOCK / (32 * (registers[2 * channel] or 1024))}
                               for channel in range(3)]
        event['noise_audible_after'] = (registers[7] & 15) != 15


def verify(case):
    directory = ROOT / f'build/tests/{case}-audio'
    manifest_path = directory / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    parent_path = ROOT / f'tests/reference/{case}.json'
    if not manifest['repeat_identical'] or not manifest['preserved_callbacks'] or digest(parent_path) != manifest['parent_sha256']:
        raise ValueError('Source audio parent/repetition not verified')
    parent = json.loads(parent_path.read_text())
    for label, run in zip(('a', 'b'), manifest['runs']):
        for name, field in [('callbacks.tsv', 'callbacks_sha256'), ('psg-times.tsv', 'events_sha256'),
                            ('frame-times.tsv', 'frame_times_sha256'), ('source.wav', 'wav_sha256')]:
            if digest(directory / label / name) != run[field]:
                raise ValueError(f'Changed source audio evidence: {label}/{name}')
    events = read_times(directory / 'a/psg-times.tsv')
    frames = {row['frame']: row['time_attoseconds'] for row in read_times(directory / 'a/frame-times.tsv')}
    raw_psg = []
    for line in (directory / 'a/callbacks.tsv').read_text(encoding='ascii').splitlines():
        sequence, text = line.split('\t', 1)
        tokens = text.split()
        if tokens[1] == 'P':
            raw_psg.append({'sequence': int(sequence), 'callback': int(tokens[2]), 'frame': int(tokens[3]),
                            'pc': int(tokens[4], 16), 'value': int(tokens[5], 16)})
    timed = [event for event in events if event['frame'] >= 1298]
    if len(timed) < len(raw_psg):
        raise ValueError('Missing timed source PSG writes')
    for index, (observed, original) in enumerate(zip(timed, raw_psg)):
        if any(observed[key] != original[key] for key in ('frame', 'pc', 'value')):
            raise ValueError(f'Timed PSG/source callback sequence differs at write {index}')
        observed.update(raw_sequence=original['sequence'], callback=original['callback'])
    by_sequence = {event['raw_sequence']: event for event in timed if 'raw_sequence' in event}
    timeline = [event for event in parent['timeline'] if event['kind'] == 'P']
    for event in timeline:
        observed = by_sequence[event['sequence']]
        observed.update(context=event['context'], retained_parent_event=True)
    decode_registers(events)
    presentation = json.loads((ROOT / f'tests/reference/presentation/{case}/manifest.json').read_text())
    triggers = {name: (ordinal, parent['updates'][ordinal - 1]['begin_frame'])
                for name, ordinal in presentation['trigger_updates'].items()
                if name in ('serve-lower-launch', 'serve-upper-launch') and ordinal > 0}
    for side, pc in [('lower', 0x0c9f), ('upper', 0x0fd3)]:
        contact = next((event for event in parent['timeline'] if event['kind'] == 'M' and event['pc'] == pc), None)
        if contact:
            triggers[f'{side}-return'] = (contact['after_callback'], contact['frame'])
    first_point = next(row for row in parent['updates'] if bytes.fromhex(row['ram'])[0x3e:0x40] != bytes.fromhex(row['entry_ram'])[0x3e:0x40])
    triggers['first-point'] = (first_point['ordinal'], first_point['begin_frame'])
    for name in ('tail_only_start', 'gameplay_resumed', 'match_award', 'restart_gameplay'):
        trigger = parent['milestones'][name]
        triggers[name] = (trigger['update'], trigger['frame'])
    marker = next(event for event in parent['timeline'] if event['kind'] == 'M' and event['pc'] == 0x0580
                  and event['after_callback'] >= parent['milestones']['match_award']['update'])
    triggers['match-result-sound'] = (marker['after_callback'], marker['frame'])
    with wave.open(str(directory / 'a/source.wav'), 'rb') as audio:
        pcm = audio.readframes(audio.getnframes())
        rate, channels, width = audio.getframerate(), audio.getnchannels(), audio.getsampwidth()
    if (rate, channels, width) != (48000, 1, 2):
        raise ValueError('Unsupported source WAV format')
    names = sorted(triggers, key=lambda name: frames[triggers[name][1]])
    intervals = {}
    for index, name in enumerate(names):
        ordinal, frame = triggers[name]
        start = frames[frame]  # observed start of this recorder frame label
        limit = frames[triggers[names[index + 1]][1]] if index + 1 < len(names) else frames[parent['updates'][-1]['end_frame'] + 1]
        before = [event for event in events if event['time_attoseconds'] < start]
        selected = [event for event in events if start <= event['time_attoseconds'] < limit]
        initial = before[-1]['registers_after'] if before else [0] * 8
        audible = any(initial[index] & 15 != 15 for index in (1, 3, 5, 7))
        onset, silence = (start if audible else None), None
        for event in selected:
            active = any(tone['attenuation'] != 15 for tone in event['tones_after']) or event['noise_audible_after']
            if active and onset is None:
                onset = event['time_attoseconds']
            if not active and onset is not None and silence is None:
                silence = event['time_attoseconds']
        # Retain the whole named interval as well as the first silence. Silence
        # between phrases must not truncate a later part of a result sequence.
        first_sample, last_sample = start * rate // ATTO, (limit * rate + ATTO - 1) // ATTO
        excerpt = pcm[first_sample * 2:last_sample * 2]
        samples = array.array('h', excerpt)
        path = directory / f'{name}.wav'
        with wave.open(str(path), 'wb') as audio:
            audio.setnchannels(1); audio.setsampwidth(2); audio.setframerate(rate); audio.writeframes(excerpt)
        intervals[name] = {'trigger_callback': ordinal, 'trigger_frame': frame,
                           'start_attoseconds': start, 'end_attoseconds': limit,
                           'first_audible_command_attoseconds': onset,
                           'first_all_muted_attoseconds': silence, 'first_sample': first_sample, 'last_sample': last_sample,
                           'initial_registers': initial,
                           'timed_writes': selected, 'noise_writes_audible': any(event['noise_audible_after'] for event in selected),
                           'rms': math.sqrt(sum(value * value for value in samples) / len(samples)) if samples else 0,
                           'wav': path.name, 'wav_sha256': digest(path)}
    report = {'source_case': case, 'capture_manifest_sha256': digest(manifest_path),
              'parent_sha256': digest(parent_path), 'exact_associated_psg_writes': len(raw_psg),
              'retained_parent_psg_writes': len(timeline), 'timed_events': events, 'intervals': intervals,
              'clock_hz': PSG_CLOCK, 'noise_gameplay_audible': any(event['noise_audible_after'] for event in timed),
              'scope': 'Original WAVs and exact timed PSG associations. Trigger frames bound intervals; audio onset/response measurements and native comparisons remain required.'}
    (directory / 'audio-associations.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'case': case, 'associated': len(raw_psg), 'retained': len(timeline),
                      'intervals': list(intervals), 'noise_gameplay_audible': report['noise_gameplay_audible']}, indent=2))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=('one-player-match', 'two-player-match'), default='one-player-match')
    verify(parser.parse_args().case)
