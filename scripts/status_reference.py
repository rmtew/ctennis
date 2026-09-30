"""Bounded source-observed status lifecycles, separate from physical scanout."""
import json
from presentation_reference import ROOT
from run_presentation_tests import digest
from phase_reference import build_phase, validate_phase

CASES = tuple(f'p1-status-{value}-lifecycle' for value in (2, 3, 4, 5, 6))


def reference(case):
    inputs = {'one-player-match': [{'port': 2, 'red': True}],
              'two-player-match': [{'port': 1, 'red': True}, {'port': 2, 'red': True}]}
    if (case['source_case'] not in inputs
            or case['inputs'] != inputs[case['source_case']]
            or case['fields'] != ['status']):
        raise ValueError('Status adapter requires the declared held-fire physical inputs')
    root = ROOT / 'tests/reference/presentation'
    frozen = json.loads((root / 'manifest.json').read_text())
    if not frozen['source_media_checks_passed'] or frozen['recipe_sha256'] != digest(ROOT / 'tests/cases/presentation.json'):
        raise ValueError('Unverified source media recipe')
    entry = frozen['references'][case['source_case']]
    manifest_path = root / entry['manifest']
    if digest(manifest_path) != entry['manifest_sha256'] or digest(root / entry['validation']) != entry['validation_sha256']:
        raise ValueError('Frozen status source media changed')
    manifest = json.loads(manifest_path.read_text())
    parent_path = ROOT / f'tests/reference/{case["source_case"]}.json'
    if digest(parent_path) != manifest['parent_reference_sha256']:
        raise ValueError('Status source parent changed')
    parent = json.loads(parent_path.read_text())
    value = case['status_variant']
    appear, expire = case['appearance_callback'], case['expiry_callback']
    if (manifest['trigger_updates'][f'status-{value}-appears'] != appear
            or manifest['trigger_updates'][f'status-{value}-disappears'] != expire):
        raise ValueError('Status source trigger changed')
    phase_path = ROOT / case['initial_phase_reference']
    phase_case = json.loads((ROOT / 'tests/cases' / phase_path.name).read_text())
    phase = build_phase(phase_case)
    # Rebuild reproducible private data from the pinned original, never the port.
    phase_path.write_text(json.dumps(phase, indent=2) + '\n')
    validate_phase(phase, phase_case)
    start, end = case['initial_source_update'], case['completed_callbacks'][-1]
    if (phase['initial_source_update'] != start
            or phase['parent_reference'] != f'tests/reference/{case["source_case"]}.json'):
        raise ValueError('Status phase start or parent differs from the recipe')
    lead = case.get('initial_lead_callbacks', 2)
    if lead not in (2, 4) or start != appear - lead or end > start + len(phase['updates']):
        raise ValueError('Status lifecycle must begin before its point event')
    if bytes.fromhex(phase['initial_post_tail'])[0x42] & 0xc0:
        raise ValueError('Status phase begins with a pending/visible earlier message')
    expected = {}
    for row in parent['updates'][start:end]:
        pre, post = bytes.fromhex(row['entry_ram']), bytes.fromhex(row['ram'])
        update = row['ordinal']
        # Bit 6 is the original's observed "message has been drawn" latch.
        # These isolated windows contain exactly one pending message and clear.
        selector = post[0x42] & 7 if post[0x42] & 64 else 0
        wanted = value if appear <= update < expire else 0
        if row['callback_kind'] != 'gameplay' or selector != wanted:
            raise ValueError('Original status latch does not match the bounded lifecycle')
        if case['source_case'] == 'two-player-match' and [(event['group'], event['value']) for event in row['inputs']] != [(1, 16), (0, 16)]:
            raise ValueError('Two-player source interval does not have both held button observations')
        expected[update] = {'selector': selector, 'score_flags_before': pre[0x42],
                            'status_timer_before': pre[0x71]}
        if case.get('observe_state'):
            expected[update]['post_tail_ram'] = row['post_tail_ram']
    drawing = expected[appear]
    clearing = expected[expire]
    if (drawing['score_flags_before'] & 0xc0 != 0x80
            or clearing['score_flags_before'] & 0xc0 != 0xc0
            or clearing['status_timer_before'] != 255):
        raise ValueError('Original appearance/expiry boundaries are missing')
    return expected, {'parent_sha256': digest(parent_path), 'phase_sha256': digest(phase_path),
        'source_manifest_sha256': digest(manifest_path), 'appearance_callback': appear,
        'expiry_callback': expire, 'source_visible_updates': expire - appear,
        'scope': 'Original drawn-message latch per callback; physical pixels checked separately at stable captured generations.'}
