"""Compare actual native Paula output against independently recorded original sound."""
import argparse
import json
from fractions import Fraction
from pathlib import Path

from audio_wave import read_wave, crossing_frequency
from audio_mute import check_emitted_mute
from capture_native_presentation import capture
from run_presentation_tests import ROOT, digest
from maintained_state_contract import MAINTAINED_STATE_CONTRACT, MAINTAINED_SCRATCH_OFFSETS
from evidence import tracked_call


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


def measured_envelope(source, directory, tone, first_update, last_update):
    fmt, values = read_wave(directory / 'a/source.wav')
    if fmt['channels'] != 1 or fmt['encoding'] != 'pcm16':
        raise ValueError('Envelope calibration requires the captured mono source WAV')
    rows = {}
    events = source['timed_events']
    for index, event in enumerate(events[:-1]):
        update = event.get('callback', -1)
        state = event['tones_after'][tone]
        if not first_update <= update <= last_update or event['selected_register'] != 2 * tone + 1 or state['attenuation'] == 15:
            continue
        if any(other['attenuation'] != 15 for channel, other in enumerate(event['tones_after']) if channel != tone) or event['noise_audible_after']:
            raise ValueError('Source envelope calibration contains other audible channels')
        start, end = event['time_attoseconds'] / 1e18, events[index + 1]['time_attoseconds'] / 1e18
        levels = []
        windows = []
        for margin in (.002, .003, .004):
            first, last = int((start + margin) * fmt['sample_rate']), int((end - margin) * fmt['sample_rate'])
            samples = sorted(values[first:last])
            if len(samples) < 100:
                raise ValueError('Source plateau interval too short')
            # The two square-wave plateaus are the lower/upper quartiles.
            # This excludes edge ringing without assuming generated samples.
            levels.append(samples[3 * len(samples) // 4] - samples[len(samples) // 4])
            windows.append({'trim_seconds': margin, 'first_sample': first, 'last_sample': last})
        if len(set(levels)) != 1:
            raise ValueError('Source plateau level depends on extraction margin')
        rows[update] = {'attenuation': state['attenuation'], 'measured_plateau_difference': levels[0], 'windows': windows}
    base = next(row['measured_plateau_difference'] for row in rows.values() if row['attenuation'] == 0)
    if base <= 0:
        raise ValueError('No nonzero source envelope reference')
    for row in rows.values():
        row['nearest_paula_volume'] = round(Fraction(64 * row['measured_plateau_difference'], base))
    return rows


def compare_audio_value(update, field, expected, actual):
    return {'update': update, 'boundary': 'paula-events-applied', 'field': field,
            'expected': expected, 'actual': actual} if expected != actual else None


def run_case(args):
    if args.case == 'ct08-effect-classes':
        return run_effect_classes(args)
    case = json.loads((ROOT / f'tests/cases/{args.case}.json').read_text())
    report_path = ROOT / f'build/tests/{args.case}-report.json'
    source, source_directory, reference_sha = source_record(case)
    comparison = case.get('comparison', 'pitch')
    envelope = measured_envelope(source, source_directory, case['source_tone'], 17, 39) if comparison == 'volume' else None
    mutation = None
    disconnected = None
    if args.self_test:
        def mutate_output(executable):
            original = executable.read_bytes()
            if comparison == 'pitch':
                old = (ROOT / 'build/amiga/native-audio/periods.bin').read_bytes()
                new = b''.join((int.from_bytes(old[n:n+2], 'big') + 1).to_bytes(2, 'big') for n in range(0,len(old),2))
            else:
                old = bytes.fromhex('403328201914100d0a08060504030300')
                changed = bytearray(old)
                changed[0 if comparison == 'volume' else 15] = 63 if comparison == 'volume' else 1
                new = bytes(changed)
            # Mutate only the unique private instruction/table; product source is untouched.
            if original.count(old) != 1:
                raise ValueError('Native pitch instruction not uniquely identified')
            executable.write_bytes(original.replace(old, new))
        altered = capture(tuple(case['completed_callbacks']), recorded_entropy=True,
                          observe_audio=True, executable_mutator=mutate_output, capture_label=case['name'] + '-mutation')
        mutation = {'capture_report_path': altered['capture_report_path'],
                    'capture_report_sha256': digest(Path(altered['capture_report_path'])),
                    'native_wav': altered['native_wav'],
                    'executable_sha256': altered['executable_sha256'],
                    'first_period': altered['audio_events'][0]['registers'][f'AUD{case["paula_channel"]}PER'],
                    'volumes': {event['update']: event['registers'][f'AUD{case["paula_channel"]}VOL'] for event in altered['audio_events']}}
        if comparison == 'mute':
            mutation['capture_report_path'] = altered['capture_report_path']
            mutation['capture_report_sha256'] = digest(Path(altered['capture_report_path']))
            mutation['native_wav_sha256'] = digest(Path(altered['native_wav']))
            event = next(event for event in altered['audio_events'] if event['update'] == case['mute_update'])
            mutation['criterion_value'] = [event['registers'][f'AUD{c}VOL'] for c in (0, 1, 3)]
            mutation['emitted_waveform'] = check_emitted_mute(case, source, source_directory, altered)
            if mutation['emitted_waveform']['first_difference'] is None:
                raise AssertionError('Emitted audio comparator missed the actual unmuted-channel fault')
            def disconnect_waveform(executable):
                original = executable.read_bytes()
                waveform = bytes.fromhex('7f7f8181')
                if original.count(waveform) != 1:
                    raise ValueError('Private waveform is not uniquely identified')
                executable.write_bytes(original.replace(waveform, bytes(4)))
            silent = capture(tuple(case['completed_callbacks']), recorded_entropy=True,
                             observe_audio=True, executable_mutator=disconnect_waveform,
                             capture_label=case['name'] + '-disconnected')
            disconnected = {'executable_sha256': silent['executable_sha256'],
                            'capture_report_path': silent['capture_report_path'], 'native_wav': silent['native_wav'],
                            'capture_report_sha256': digest(Path(silent['capture_report_path'])),
                            'native_wav_sha256': digest(Path(silent['native_wav'])),
                            'emitted_waveform': check_emitted_mute(case, source, source_directory, silent),
                            'audio_controls': [{key: event['registers'][key]
                                for key in (f'AUD{channel}{suffix}' for channel in (0, 1, 3) for suffix in ('PER', 'VOL', 'LEN'))}
                                for event in silent['audio_events']]}
            if disconnected['emitted_waveform']['first_difference'] is None:
                raise AssertionError('Emitted audio comparator missed a disconnected waveform')
        else:
            mutation['criterion_value'] = mutation['first_period'] if comparison == 'pitch' else mutation['volumes'][altered['audio_events'][0]['update']]
    # Rebuild and recapture the normal executable last; no mutation remains in
    # the authoritative report, audio file or executable used by the case.
    captured = capture(tuple(case['completed_callbacks']), recorded_entropy=True, observe_audio=True, capture_label=case['name'])
    raw_differences = [difference for row in captured['observations'] for difference in row['state_differences']]
    semantic_differences = [d for d in raw_differences if d['offset'] not in MAINTAINED_SCRATCH_OFFSETS]
    if semantic_differences:
        raise ValueError(f'Native audio replay semantic state differs from source: {semantic_differences[0]}')
    observations, first = [], None
    channel, tone = case['paula_channel'], case['source_tone']
    for native in captured['audio_events']:
        original = [event for event in source['timed_events'] if event.get('retained_parent_event') and event.get('callback') == native['update']]
        if not original or [event['value'] for event in original] != list(bytes.fromhex(native['psg'])):
            raise ValueError('Original/native audio event association differs')
        state = original[-1]['tones_after'][tone]
        if comparison == 'mute' and native['update'] != case['mute_update']:
            continue
        if comparison != 'mute' and state['attenuation'] == 15:
            continue
        exact = Fraction(case['paula_clock_hz'] * 32 * state['divisor'], source['clock_hz'] * case['samples_per_cycle'])
        expected = round(exact)
        if expected < 123 or expected > 65535:
            raise ValueError('Pitch case outside supported legal period range')
        actual = native['registers'][f'AUD{channel}PER']
        if comparison == 'volume':
            expected_value = envelope[native['update']]['nearest_paula_volume']
            actual_value, field = native['registers'][f'AUD{channel}VOL'], f'Paula volume for source tone {tone}'
        elif comparison == 'mute':
            if any(t['attenuation'] != 15 for t in original[-1]['tones_after']) or original[-1]['noise_audible_after']:
                raise ValueError('Expected mute boundary is not silent in the source')
            expected_value, actual_value, field = [0, 0, 0], [native['registers'][f'AUD{c}VOL'] for c in (0, 1, 3)], 'Paula tone mute volumes'
        else:
            expected_value, actual_value, field = expected, actual, f'Paula period for source tone {tone}'
        difference = compare_audio_value(native['update'], field, expected_value, actual_value)
        first = first or difference
        observations.append({'update': native['update'], 'source_state': state, 'paula_period': actual,
                             'criterion_expected': expected_value, 'criterion_actual': actual_value, 'criterion_field': field,
                             'nearest_paula_period': expected, 'source_events': original,
                             'paula_frequency_hz': case['paula_clock_hz'] / (case['samples_per_cycle'] * actual),
                             'paula_volume': native['registers'][f'AUD{channel}VOL'], 'first_difference': difference})
    if not observations:
        raise ValueError('No audible native tone observations')
    waveform = check_emitted_mute(case, source, source_directory, captured) if comparison == 'mute' else None
    if waveform:
        first = first or waveform['first_difference']
    if disconnected:
        controls = [{key: event['registers'][key]
                     for key in (f'AUD{channel}{suffix}' for channel in (0, 1, 3) for suffix in ('PER', 'VOL', 'LEN'))}
                    for event in captured['audio_events']]
        if disconnected['audio_controls'] != controls:
            raise AssertionError('Disconnected waveform control changed period/volume/length expectations')
        if disconnected['executable_sha256'] == captured['executable_sha256']:
            raise AssertionError('Disconnected waveform control did not change the executable')
    if args.self_test:
        changed = mutation['first_period'] != observations[0]['paula_period'] if comparison == 'pitch' else mutation['volumes'][observations[0]['update']] != observations[0]['paula_volume']
        if not changed or mutation['executable_sha256'] == captured['executable_sha256']:
            raise AssertionError('Actual assembled pitch mutation was not detected')
        initial = observations[0]
        detected = compare_audio_value(initial['update'], initial['criterion_field'], initial['criterion_expected'], mutation['criterion_value'])
        if detected is None or detected == initial['first_difference']:
            raise AssertionError('Audio comparator did not reject the actual executable mutation')
        mutation['detected_difference'] = detected
    fmt, pcm = read_wave(Path(captured['native_wav']))
    start, end = captured['audio_events'][0]['stop']['seconds'] + .005, captured['audio_events'][-1]['stop']['seconds'] - .003
    measured = crossing_frequency(pcm, fmt['sample_rate'], fmt['channels'], start, end)
    result = {'case': args.case, 'subject': 'maintained-native', 'startup': 'captured phase',
              'state_contract': MAINTAINED_STATE_CONTRACT, 'raw_state_differences': raw_differences,
              'omitted_legacy_scratch_offsets': list(MAINTAINED_SCRATCH_OFFSETS), 'passed': first is None, 'first_difference': first,
              'criterion': case['criterion'], 'scope': case['contract'], 'observations': observations,
              'capture_report_path': captured['capture_report_path'],
              'capture_report_sha256': digest(Path(captured['capture_report_path'])),
              'reference_sha256': reference_sha, 'native_executable_sha256': captured['executable_sha256'],
              'native_wav': captured['native_wav'],
              'native_wav_sha256': digest(Path(captured['native_wav'])),
              'native_wav_format': fmt, 'measured_native_wave': measured,
              'wave_measurement_scope': 'Diagnostic rising-crossing estimate; no waveform acceptance tolerance inferred.',
              'source_wav_sha256': digest(source_directory / 'a/source.wav'), 'self_test': args.self_test,
              'mutation': mutation,
              'emitted_waveform': waveform, 'disconnected_waveform_mutation': disconnected,
              'waveform_comparator_sha256': digest(ROOT / 'scripts/audio_mute.py') if waveform else None,
              'comparison': comparison, 'source_envelope_measurements': envelope,
              'native_provenance': {key: captured[key] for key in ('native_source', 'native_source_sha256',
                  'emulator_sha256', 'bridge_sha256', 'kickstart_sha256', 'reference_sha256')},
              'case_sha256': digest(ROOT / f'tests/cases/{args.case}.json')}
    report_path.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'case': args.case, 'passed': result['passed'], 'first_difference': first,
                      'wave_frequency_hz': measured['frequency_hz']}, indent=2))
    return 0 if result['passed'] else 1


def run_effect_classes(args):
    from audio_effect_classes import inventory, compare_window
    from evidence import atomic_json
    case = json.loads((ROOT / 'tests/cases/ct08-effect-classes.json').read_text())
    recipe = json.loads((ROOT / f"tests/cases/{case['presentation_case']}.json").read_text())
    source, directory, reference_sha = source_record(case)
    first, last = recipe['initial_source_update'], recipe['completed_callbacks'][-1]
    captured = capture((last,), recorded_entropy=True, observe_audio=True, observe_state=True,
        initial_source_update=first, initial_phase_reference=recipe['initial_phase_reference'],
        source_case=recipe['source_case'], native_inputs=recipe['inputs'],
        native_input_schedule=recipe['native_input_schedule'],
        presentation_reference_directory=recipe['presentation_reference_directory'],
        capture_label=case['name'])
    parent = json.loads((ROOT / f"tests/reference/{recipe['source_case']}.json").read_text())
    measured = measured_envelope(source,directory,2,17,39)
    levels = {15:0}
    for row in measured.values():
        attenuation, level = row['attenuation'],row['nearest_paula_volume']
        if attenuation in levels and levels[attenuation]!=level:
            raise ValueError('Original calibrated amplitude is inconsistent')
        levels[attenuation]=level
    if set(levels)!=set(range(16)):
        raise ValueError('Original calibration does not cover all amplitude steps')
    result = compare_window(captured,parent,source,directory,first,last,levels)
    result['source_envelope_measurements'] = measured
    result.update(case=args.case, subject='maintained-native', startup='captured phase',
        passed=result['first_difference'] is None, state_contract=MAINTAINED_STATE_CONTRACT,
        omitted_legacy_scratch_offsets=list(MAINTAINED_SCRATCH_OFFSETS),
        reference_sha256=reference_sha, criterion=case['criterion'], scope=case['contract'],
        initial_source_update=first, final_source_update=last,
        interval_inventory=inventory(ROOT,source_record),
        capture_report_path=captured['capture_report_path'], native_wav=captured['native_wav'],
        capture_report_sha256=digest(Path(captured['capture_report_path'])),
        native_executable_sha256=captured['executable_sha256'],
        native_wav_sha256=digest(Path(captured['native_wav'])),
        source_wav_sha256=digest(directory/'a/source.wav'), self_test=False)
    atomic_json(ROOT / f'build/tests/{args.case}-report.json',result)
    print(json.dumps({k:result[k] for k in ('passed','first_difference','observed_callbacks','due_callbacks','two_tick_countdowns','classes')},indent=2))
    return 0 if result['passed'] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=('p2-first-serve-pitch', 'p2-first-serve-envelope', 'p2-first-serve-mute', 'ct08-effect-classes'), default='p2-first-serve-pitch')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    return tracked_call([ROOT / f'build/tests/{args.case}-report.json'], 'audio', 'maintained-native',
                        'captured phase', 'scripts/run_audio_tests.py', args.case,
                        lambda: run_case(args),
                        lambda path, report: [Path(report['capture_report_path']).parent / 'native-application'])

if __name__ == '__main__':
    raise SystemExit(main())
