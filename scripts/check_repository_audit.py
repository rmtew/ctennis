"""Check that the audit accounts for every baseline and current tracked file."""
import csv
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASELINE = 'dd97c573df8044ba090facaedf31d549b83e12cf'
INDEX = ROOT / 'docs/repository-audit.tsv'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def check():
    baseline = {}
    for entry in git('ls-tree', '-rlz', BASELINE).split(b'\0'):
        if entry:
            metadata, path = entry.split(b'\t', 1)
            baseline[path.decode()] = int(metadata.split()[3])
    current = set(git('ls-files', '-z').decode().split('\0')) - {''}
    with INDEX.open(newline='') as stream:
        rows = list(csv.DictReader(stream, delimiter='\t'))
    indexed = {row['path']: row for row in rows}
    errors = []
    if len(indexed) != len(rows):
        errors.append('Duplicate paths in audit index')
    for path in sorted(set(baseline) | current | set(indexed)):
        row = indexed.get(path)
        if row is None:
            errors.append(f'Missing audit row: {path}')
            continue
        if not all(row.get(key) for key in ('type', 'purpose', 'consumer', 'evidence')):
            errors.append(f'Incomplete audit row: {path}')
        expected_size = str(baseline[path]) if path in baseline else ''
        if row['baseline_bytes'] != expected_size:
            errors.append(f'Wrong baseline size: {path}')
        if path not in baseline:
            expected = 'add' if path in current else None
        elif path not in current:
            expected = 'remove'
        else:
            original = git('show', f'{BASELINE}:{path}')
            expected = 'keep' if (ROOT / path).read_bytes() == original else 'update'
        if row['decision'] != expected:
            errors.append(f'Wrong decision for {path}: expected {expected}')
    if errors:
        raise SystemExit('\n'.join(errors))
    print(f'Audit covers {len(baseline)} baseline files and {len(current)} current files.')
    print(f'Baseline bytes: {sum(baseline.values())}; decisions: ' + ', '.join(
        f'{decision}={sum(r["decision"] == decision for r in rows)}'
        for decision in ('keep', 'update', 'remove', 'add')))


if __name__ == '__main__':
    check()
