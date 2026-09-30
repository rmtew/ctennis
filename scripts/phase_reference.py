"""Retain exact reachable phases from an independently captured continuous oracle."""
import copy
import hashlib
import json
from pathlib import Path
from round_reference import validate_fixture

ROOT = Path(__file__).resolve().parent.parent
CASES = ('round-tail-phase', 'resumed-play-phase', 'match-tail-phase', 'restart-play-phase')


def build_phase(case):
    path = ROOT / case['parent_reference']
    payload = path.read_bytes()
    parent = json.loads(payload)
    validate_fixture(parent)
    start, count = case['initial_source_update'], case['updates']
    if start < 1 or count < 1 or start + count > len(parent['updates']):
        raise ValueError('Phase exceeds retained continuous source evidence')
    initial = parent['updates'][start - 1]
    updates = copy.deepcopy(parent['updates'][start:start + count])
    for ordinal, row in enumerate(updates, 1):
        row['source_ordinal'] = row['ordinal']
        row['ordinal'] = ordinal
    return {'schema_version': 2, 'reference_kind': 'source-derived-phase',
            'parent_reference': case['parent_reference'],
            'parent_sha256': hashlib.sha256(payload).hexdigest(),
            'rom_sha256': parent['rom_sha256'], 'repeat_identical': parent['repeat_identical'],
            'initial_source_update': start, 'initial_pre_tail': initial['ram'],
            'initial_post_tail': initial['post_tail_ram'], 'initial_psg': initial['psg'],
            'updates': updates}


def validate_phase(fixture, case):
    # Reconstruct from the validated, twice-captured parent rather than trusting
    # editable phase metadata or snapshots. No expected data comes from the port.
    if fixture != build_phase(case):
        raise ValueError('Phase differs from its retained source parent or recipe')
    return {'updates': len(fixture['updates']), 'reference_kind': fixture['reference_kind'],
            'parent_sha256': fixture['parent_sha256'],
            'initial_source_update': fixture['initial_source_update'],
            'final_source_update': fixture['updates'][-1]['source_ordinal']}


if __name__ == '__main__':
    for name in CASES:
        case = json.loads((ROOT / f'tests/cases/{name}.json').read_text())
        fixture = build_phase(case)
        target = ROOT / case['reference']
        target.write_text(json.dumps(fixture, indent=2) + '\n')
        print(name, validate_phase(fixture, case))
