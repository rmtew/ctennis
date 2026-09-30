"""Validate and retain private original audio evidence; native parity is separate."""
import json
import shutil

from source_audio_reference import ROOT, verify, digest


def main():
    target = ROOT / 'tests/reference/audio'
    target.mkdir(parents=True, exist_ok=True)
    (target / 'manifest.json').unlink(missing_ok=True)
    references, names = {}, set()
    for case in ('one-player-match', 'two-player-match'):
        report = verify(case)
        names.update(report['intervals'])
        source, destination = ROOT / f'build/tests/{case}-audio', target / case
        destination.mkdir(exist_ok=True)
        files = ['manifest.json', 'audio-associations.json', 'a/source.wav',
                 'a/psg-times.tsv', 'a/frame-times.tsv', 'a/callbacks.tsv']
        files += [interval['wav'] for interval in report['intervals'].values()]
        retained = {}
        for name in files:
            path = destination / name
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source / name, path)
            retained[name] = digest(path)
        references[case] = {'directory': case, 'files': retained,
                            'parent_sha256': report['parent_sha256'], 'intervals': list(report['intervals'])}
    required = {'serve-lower-launch', 'serve-upper-launch', 'lower-return', 'upper-return',
                'first-point', 'tail_only_start', 'gameplay_resumed', 'match_award',
                'match-result-sound', 'restart_gameplay'}
    if not required <= names:
        raise ValueError(f'Missing source audio classes: {required - names}')
    manifest = {'schema_version': 1, 'kind': 'independent-original-game-P2-audio',
                'source_capture_checks_passed': True, 'complete_P2_comparison': False,
                'references': references, 'required_interval_classes': sorted(required),
                'remaining': ['source/native waveform response measurements', 'native comparisons for all named intervals'],
                'noise': 'No audible noise channel or noise-control write observed during either retained gameplay recording; reset output is separate.'}
    (target / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'source_capture_checks_passed': True, 'intervals': sum(len(x['intervals']) for x in references.values())}))


if __name__ == '__main__':
    main()
