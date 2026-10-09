"""Validate completed PAL measurement after controller archival ENOSPC.

No emulator executes. The original incomplete campaign is never changed.
"""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from tutorial_latency import required_latency_extent

ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = '0144dc18e4d440a6b4a5573e1d73b5e2'
REPORT_SHA = '5085ecc066237d0349fe955497c3ce97d6785f1e3165a8379e58a5627542ea72'


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def validate():
    directory = ROOT/'build/acceptance/campaigns'/CAMPAIGN
    attempt = directory/'attempts/tutorial-latency-pal/000001'
    source = ROOT/'build/tests/tutorial-latency-pal/report.json'
    assert digest(source) == REPORT_SHA == digest(attempt/'receipt.json')
    report = json.loads(source.read_text())
    meta = report['evidence']
    assert meta['state'] == 'complete' and not meta['changed_during_run']
    original = json.loads((directory/'report.json').read_text())
    assert original == dict(campaign=CAMPAIGN, state='incomplete', passed=False, cases=[])
    assert not (attempt/'completion.json').exists()
    logs = list(directory.glob('controller-*.log'))
    assert len(logs) == 1
    log = logs[0].read_text()
    assert 'preserve_artifacts' in log and 'objects.mkdir' in log
    assert 'OSError: [Errno 28] No space left on device:' in log
    for name, expected in meta['files'].items():
        assert digest(ROOT/name) == expected, ('Consumed file drift', name)
    for name, tool in meta['tools'].items():
        path = ROOT/tool['path']
        if path.is_dir():
            prefix = tool['path'].rstrip('/')+'/'
            assert any(p.startswith(prefix) for p in meta['files']), ('Unbound tool package', name)
        else:
            assert tool['path'] in meta['files'], ('Unbound tool', name)
    for name, expected in meta['compiled_executables'].items():
        assert digest(ROOT/name) == expected, ('Product drift', name)
    assert required_latency_extent(report, 'PAL'), 'Required measurement extent failed'
    protected = [source, attempt/'receipt.json', attempt/'started.json',
                 attempt/'child.json', directory/'report.json', logs[0]]
    bindings = {str(p.relative_to(ROOT)): dict(sha256=digest(p), bytes=p.stat().st_size)
                for p in protected}
    for path in (source.parent).iterdir():
        if path.is_file():
            bindings[str(path.relative_to(ROOT))] = dict(sha256=digest(path), bytes=path.stat().st_size)
    return dict(schema=1, passed=True, acceptance_passed=False,
        execution='Validation-only reuse of completed original PAL measurement; no emulator execution',
        scope='Finite latency measurement extent; independent literal-evidence review; no full native gate',
        runtime_commit=meta['commit'], native_product_commit=meta['native_product_commit'],
        validation_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        original_campaign_state='incomplete/passedfalse; unchanged',
        original_child_exit_status='Not independently recorded in child.json; no exit-zero claim',
        controller_failure='ENOSPC during preserve_artifacts objects.mkdir after completed child report',
        target=report['target'], required_extent=True, bindings=bindings,
        consumed_inputs=meta['files'], tools=meta['tools'],
        compiled_executables=meta['compiled_executables'],
        validation_writer=dict(path=str(Path(__file__).relative_to(ROOT)), sha256=digest(Path(__file__))),
        validator=dict(path='scripts/tutorial_latency.py', sha256=digest(ROOT/'scripts/tutorial_latency.py')))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    assert output.is_relative_to((ROOT/'build/tests/tutorial-latency-pal-validation').resolve())
    assert not output.exists(), 'Preserve existing validation receipts'
    result = validate()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(dict(passed=True, acceptance_passed=False, output=str(output), sha256=digest(output))))


if __name__ == '__main__':
    main()
