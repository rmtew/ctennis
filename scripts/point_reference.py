"""Original draw-boundary contracts for three distinct point transitions."""
import json
from presentation_reference import ROOT
from phase_reference import build_phase, validate_phase
from run_presentation_tests import digest

CASES = tuple('p1-' + name + '-fields' for name in ('deuce', 'advantage', 'return-deuce'))
FIELDS = ('point_a', 'point_b', 'games_a', 'games_b', 'mode')
SLOTS = (0, 1, 2, 3, 5)


def reference(case):
    recipe_path = ROOT / 'tests/cases/point-fields.json'
    recipe = json.loads(recipe_path.read_text())
    frozen = json.loads((ROOT / recipe['reference_directory'] / 'manifest.json').read_text())
    if frozen['supplemental_recipe_sha256'] != digest(recipe_path):
        raise ValueError('Point source recipe changed')
    checkpoint = recipe['checkpoints'][case['transition']]
    award = checkpoint['update']
    start, end = case['initial_source_update'], case['completed_callbacks'][-1]
    if (case['source_case'] != recipe['source_case'] or start != award - 4
            or case['completed_callbacks'] != [award + 2, award + 5]
            or case['fields'] != list(FIELDS)
            or case['inputs'] != [{'port': 1, 'red': True}, {'port': 2, 'red': True}]):
        raise ValueError('Point case differs from its bounded source contract')
    phase_path = ROOT / case['initial_phase_reference']
    phase_case = json.loads((ROOT / 'tests/cases' / phase_path.name).read_text())
    phase = build_phase(phase_case)
    validate_phase(phase, phase_case)
    if phase['initial_source_update'] != start or phase['parent_reference'] != f'tests/reference/{case["source_case"]}.json':
        raise ValueError('Point phase has the wrong source start')
    phase_path.write_text(json.dumps(phase, indent=2) + '\n')
    parent_path = ROOT / phase['parent_reference']
    entry = frozen['references'][case['source_case']]
    media_path = ROOT / recipe['reference_directory'] / entry['manifest']
    media = json.loads(media_path.read_text())
    if digest(parent_path) != media['parent_reference_sha256']:
        raise ValueError('Point source parent changed')
    parent = json.loads(parent_path.read_text())
    expected, selection, draws = {}, None, []
    for row in parent['updates'][start:end]:
        pre, post = bytes.fromhex(row['entry_ram']), bytes.fromhex(row['ram'])
        update = row['ordinal']
        if row['callback_kind'] != 'gameplay' or [(e['group'], e['value']) for e in row['inputs']] != [(1, 16), (0, 16)]:
            raise ValueError('Point window lacks the declared gameplay/physical inputs')
        if pre[0x42] & 32:
            selection = list(pre[0x3e:0x42]) + [0 if pre[0x3d] & 4 else 2 if pre[0x3d] & 128 else 1]
            draws.append(update)
            if post[0x42] & 32:
                raise ValueError('Original redraw flag was not consumed')
        expected[update] = {'selection': selection, 'score_flags_before': pre[0x42],
                            'post_tail_ram': row['post_tail_ram']}
    if draws != [award + 1] or selection[:4] != checkpoint['scores']:
        raise ValueError('Original point draw boundary changed')
    return expected, {'parent_sha256': digest(parent_path), 'phase_sha256': digest(phase_path),
        'source_manifest_sha256': digest(media_path), 'award_callback': award,
        'draw_callback': draws[0], 'reference_directory': recipe['reference_directory'],
        'scope': 'Before first draw preserve actual native bootstrap fields; thereafter compare original selections and independently captured pixels.'}
