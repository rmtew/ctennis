"""Preserve a prior coherent observer directory before any latest-file writes.

Archival establishes byte custody only. It never upgrades a failed/incomplete
receipt or changes campaign acceptance/freshness. The campaign workspace lock
must exclude a live writer before this helper is called.
"""
import json
import re
from pathlib import Path
from native_evidence import atomic_json,digest


def archive_previous(directory):
    directory=Path(directory)
    if directory.is_symlink():raise ValueError('Prior coherent observer directory is a symlink')
    if not directory.exists():return None
    if not any(directory.iterdir()):return None
    report=json.loads((directory/'report.json').read_text())
    run_id=report.get('evidence',{}).get('run_id')
    if not isinstance(run_id,str) or not re.fullmatch(r'[0-9a-f]{32}',run_id):
        raise ValueError('Prior coherent observer receipt lacks a valid run identity; preservation required')
    if (directory/'archive-manifest.json').exists():
        raise ValueError('Prior coherent observer already contains the reserved archive manifest name')
    files={}
    for path in sorted(directory.rglob('*')):
        if path.is_symlink():raise ValueError('Prior coherent observer archive contains a symlink')
        if path.is_file():files[str(path.relative_to(directory))]=digest(path)
    parent=directory.parent/(directory.name+'-attempts')
    target=parent/run_id
    parent.mkdir(parents=True,exist_ok=True)
    # Reserve our destination without replacing an existing archive. Rename
    # replaces only this empty reservation, atomically on the same filesystem.
    target.mkdir()
    try:
        directory.rename(target)
    except BaseException:
        target.rmdir()
        raise
    actual={str(p.relative_to(target)):digest(p) for p in sorted(target.rglob('*')) if p.is_file()}
    if actual!=files:
        raise ValueError('Prior coherent observer bytes changed during archive; new run blocked')
    atomic_json(target/'archive-manifest.json',dict(schema=1,run_id=run_id,
        source_directory=str(directory.absolute()),files=files,
        receipt_state=report['evidence'].get('state'),receipt_passed=report.get('passed'),
        acceptance_upgraded=False))
    return target
