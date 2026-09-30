"""Compare actual native Paula output against independently recorded original sound."""
import argparse
import json
from fractions import Fraction
from pathlib import Path

from audio_wave import read_wave, crossing_frequency
from capture_native_presentation import capture
from run_presentation_tests import ROOT, digest


def source_record(case):
    path = ROOT / case['reference']
    manifest = json.loads(path.read_text())
    if not manifest['source_capture_checks_passed']:
        raise ValueError('Source audio not verified')
    entry = manifest['references'][case['source_case']]
    directory = path.parent / entry['directory']
    for name, expected in entry['files'].items():
        if digest(directory / name) != expected:
            raise ValueError(f'Source audio changed: {name}')
    report = json.loads((directory / 'audio-associations.json').read_text())
    if digest(ROOT / f'tests/reference/{case["source_case"]}.json') != report['parent_sha256']:
        raise ValueError('Source audio parent changed')
    return report, directory, digest(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=('p2-first-serve-pitch',), default='p2-first-serve-pitch')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    case = json.loads((ROOT / f'tests/cases/{args.case}.json').read_text())
    report_path = ROOT / f'build/tests/{args.case}-report.json'
    report_path.unlink(missing_ok=True)
    source, source_directory, reference_sha = source_record(case)
    mutation = None
    if args.self_test:
        def mutate_pitch(executable):
            original = executable.read_bytes()
            old, new = bytes.fromhex('c6fc01fb'), bytes.fromhex('c6fc01fc')
            # Private assembled MULU.W #507,D3 -> #508,D3. No product source changes.
            if original.count(old) != 1:
                raise ValueError('Native pitch instruction not uniquely identified')
            executable.write_bytes(original.replace(old, new))
        altered = capture(tuple(case['completed_callbacks']), recorded_entropy=True,
                          observe_audio=True, executable_mutator=mutate_pitch)
        mutation = {'executable_sha256': altered['executable_sha256'],
                    'first_period': altered['audio_events'][0]['registers'][f'AUD{case["paula_channel"]}PER']}
    # Rebuild and recapture the normal executable last; no mutation remains in
    # the authoritative report, audio file or executable used by the case.
    captured = capture(tuple(case['completed_callbacks']), recorded_entropy=True, observe_audio=True)
    if any(row['state_differences'] for row in captured['observations']):
        raise ValueError('Native audio replay state differs from source')
    observations, first = [], None
    channel, tone = case['paula_channel'], case['source_tone']
    for native in captured['audio_events']:
        original = [event for event in source['timed_events'] if event.get('retained_parent_event') and event.get('callback') == native['update']]
        if not original or [event['value'] for event in original] != list(bytes.fromhex(native['psg'])):
            raise ValueError('Original/native audio event association differs')
        state = original[-1]['tones_after'][tone]
        if state['attenuation'] == 15:
            continue
        exact = Fraction(case['paula_clock_hz'] * 32 * state['divisor'], source['clock_hz'] * case['samples_per_cycle'])
        expected = round(exact)
        if expected < 123 or expected > 65535:
            raise ValueError('Pitch case outside supported legal period range')
        actual = native['registers'][f'AUD{channel}PER']
        difference = {'update': native['update'], 'boundary': 'paula-events-applied',
                      'field': f'Paula period for source tone {tone}', 'expected': expected, 'actual': actual} if expected != actual else None
        first = first or difference
        observations.append({'update': native['update'], 'source_state': state, 'paula_period': actual,
                             'nearest_paula_period': expected, 'source_events': original,
                             'paula_frequency_hz': case['paula_clock_hz'] / (case['samples_per_cycle'] * actual),
                             'paula_volume': native['registers'][f'AUD{channel}VOL'], 'first_difference': difference})
    if not observations:
        raise ValueError('No audible native tone observations')
    if args.self_test:
        if mutation['first_period'] == observations[0]['paula_period'] or mutation['executable_sha256'] == captured['executable_sha256']:
            raise AssertionError('Actual assembled pitch mutation was not detected')
    fmt, pcm = read_wave(Path(captured['native_wav']))
    start, end = captured['audio_events'][0]['stop']['seconds'] + .005, captured['audio_events'][-1]['stop']['seconds'] - .003
    measured = crossing_frequency(pcm, fmt['sample_rate'], fmt['channels'], start, end)
    result = {'case': args.case, 'passed': first is None, 'first_difference': first,
              'criterion': case['criterion'], 'scope': case['contract'], 'observations': observations,
              'reference_sha256': reference_sha, 'native_executable_sha256': captured['executable_sha256'],
              'native_wav_sha256': digest(Path(captured['native_wav'])),
              'native_wav_format': fmt, 'measured_native_wave': measured,
              'wave_measurement_scope': 'Diagnostic rising-crossing estimate; no waveform acceptance tolerance inferred.',
              'source_wav_sha256': digest(source_directory / 'a/source.wav'), 'self_test': args.self_test,
              'mutation': mutation,
              'native_provenance': {key: captured[key] for key in ('native_source', 'native_source_sha256',
                  'emulator_sha256', 'bridge_sha256', 'kickstart_sha256', 'reference_sha256')},
              'case_sha256': digest(ROOT / f'tests/cases/{args.case}.json')}
    report_path.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'case': args.case, 'passed': result['passed'], 'first_difference': first,
                      'wave_frequency_hz': measured['frequency_hz']}, indent=2))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
