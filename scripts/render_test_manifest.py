"""Render the reviewed test manifest using current registered cases and retained reports.

This inspects evidence; it does not run tests, change acceptance or collect media.
"""
import collections
import json
from pathlib import Path

from run_test_suite import CASES, classify

ROOT = Path(__file__).resolve().parent.parent


def link(path):
    return f'[{path}](../{path})'


def main():
    path = ROOT / 'tests/test-manifest.json'
    manifest = json.loads(path.read_text())
    members = [case for family in manifest['implemented_families'] for case in family['cases']]
    if len(members) != len(set(members)) or set(members) != set(CASES):
        raise ValueError('Manifest must assign every registered test exactly once')
    candidates = manifest['candidates']
    if len({row['id'] for row in candidates}) != len(candidates):
        raise ValueError('Duplicate candidate ID')
    for row in candidates:
        for key in ('missing_behaviour', 'plausible_regression', 'independent_expectation',
                    'stopping_condition', 'existing_overlap', 'implementation_work', 'evidence_readiness'):
            if not row.get(key):
                raise ValueError(f'Unreviewable candidate {row["id"]}: {key}')
    known = json.loads((ROOT / 'tests/known-failures.json').read_text())['cases']
    inventory = []
    for family in manifest['implemented_families']:
        for name in family['cases']:
            recipe_path = ROOT / f'tests/cases/{name}.json'
            recipe = json.loads(recipe_path.read_text())
            report_path = ROOT / 'build/tests' / ('report.json' if name == 'serve' else f'{name}-report.json')
            if report_path.exists():
                report = json.loads(report_path.read_text())
                status = classify(report, known.get(name), report_path)
                failure = report.get('first_difference')
            else:
                status, failure = 'missing-report', None
            policy = known.get(name, {})
            acceptance = ('complete observation digest' if policy.get('complete_checks_sha256') else
                          'explicit complete interval' if policy.get('complete_state_failure_interval') else
                          'first failure signature only' if status == 'known-red' else 'declared assertions pass')
            extent = 'See recipe and family limits'
            if report_path.exists() and 'updates_matched' in report:
                extent = (f'{report["updates_matched"]} matched / {report["updates"]} executed / '
                          f'{report["reference_updates"]} reference callbacks; '
                          f'{report["bytes_compared_per_boundary"]} RAM bytes/boundary')
            inventory.append({'case': name, 'family': family['id'], 'status': status,
                              'known_failure_acceptance': acceptance, 'retained_comparison_extent': extent,
                              'recipe': str(recipe_path.relative_to(ROOT)).replace('\\', '/'),
                              'reference': recipe.get('reference', recipe.get('parent_reference')),
                              'scope': recipe.get('contract', recipe.get('stop_condition', recipe.get('checkpoint'))),
                              'last_failure': failure,
                              'report': str(report_path.relative_to(ROOT)).replace('\\', '/')})
    counts = collections.Counter(row['status'] for row in inventory)
    lines = ['# Test manifest', '',
             'Review source: [test-manifest.json](test-manifest.json). Rebuild this document with '
             '`python scripts/render_test_manifest.py`. Every registered test belongs to exactly one family; '
             'recipes define individual scope. Candidates have stable IDs for discussion.', '',
             f'**Evidence snapshot ({manifest["snapshot_date"]}):** classifications below come from retained reports, not a fresh suite run. '
             + ', '.join(f'{value} {key}' for key, value in sorted(counts.items())) + '. '
             'Green applies only to the stated scope. Known red means a test exists and exposes a reviewed implementation defect. '
             'Neither status closes other requirements.', '',
             '## Review findings', '',
             'The manifest was checked against runner assertions, build subjects and retained report extents. '
             'Review corrected overstated coverage; it did not run new emulator tests or fix the suite.', '']
    for finding in manifest['review_findings']:
        lines += [f'- **{finding["id"]} ({finding["severity"]}):** {finding["finding"]}. '
                  f'Action: {finding["action"]}.']
    lines += ['',
             '## Candidate review', '',
             'Priority is a recommendation for review, not an instruction to implement. Audit-first candidates '
             'must establish additional regression protection before capture. Prefer extending existing cases '
             'and reusing original evidence. Effort estimates are relative, not elapsed-time promises.', '',
             '| ID | Candidate | Decision | Priority | Effort |',
             '| --- | --- | --- | --- | --- |']
    for row in candidates:
        lines.append(f'| {row["id"]} | [{row["title"]}](#{row["id"].lower()}) | {row["decision"]} | {row["priority"]} | {row["effort"]} |')
    for row in candidates:
        lines += ['', f'### {row["id"]}', '', f'**{row["title"]} — {row["decision"]}.**', '',
                  f'- Missing behaviour: {row["missing_behaviour"]}.',
                  f'- Plausible regression: {row["plausible_regression"]}.',
                  f'- Independent expectation: {row["independent_expectation"]}.',
                  f'- Stop when: {row["stopping_condition"]}.',
                  f'- Existing protection/overlap: {row["existing_overlap"]}.',
                  f'- Work: {row["implementation_work"]}.',
                  f'- Evidence readiness: {row["evidence_readiness"]}.',
                  f'- Dependencies: {row["dependencies"]}.']
    lines += ['', '## Implemented tests', '',
              'The four criteria below describe each family. Individual cases inherit them and further narrow '
              'their contract in the linked recipe. Existing tests are retained; this inventory proposes no removals.', '']
    for family in manifest['implemented_families']:
        lines += [f'### {family["id"]}: {family["title"]}', '',
                  f'**Value:** {family["worth"]}.', '',
                  f'- Behaviour protected: {family["behaviour"]}.',
                  f'- Plausible regression: {family["regression"]}.',
                  f'- Independent expectation: {family["independent_expectation"]}.',
                  f'- Stopping condition: {family["stopping_condition"]}.',
                  f'- Limits/overlap: {family["limits"]}.', '',
                  f'**Subject:** {family["test_subject"]}.', '',
                  '| Case and exact recipe | Retained classification | Acceptance gate | Actual retained extent |', '| --- | --- | --- | --- |']
        for row in inventory:
            if row['family'] == family['id']:
                lines.append(f'| [{row["case"]}](../{row["recipe"]}) | {row["status"]} | {row["known_failure_acceptance"]} | {row["retained_comparison_extent"]} |')
        lines.append('')
    lines += ['## Supporting checks', '', 'These are not additional gameplay acceptance cases.', '']
    for row in manifest['support_checks']:
        entrypoints = row.get('entrypoints', [row.get('entrypoint')])
        lines += [f'### {row["id"]}: {row["name"]}', '',
                  f'Entrypoints: {", ".join(link(entry) for entry in entrypoints)}.', '',
                  f'Protects: {row["protects"]}. Limit: {row["limit"]}.', '']
    lines += ['## Remaining-requirement mapping', '',
              '| Backlog requirement | Review rows |', '| --- | --- |',
              '| F2 contact/action | C01–C03; existing I09/I10 |',
              '| F3 scoring | Existing I03; stop equivalent variants |',
              '| F4 court outcomes | C04; C16 only for distinct rendering protection |',
              '| F5 timer/random effects | Existing I04; C05 for choice-to-effect audit |',
              '| P1 graphics and accepted mode | C15/C16; existing I12/I15–I20 |',
              '| P2 audible sound | C11–C14; existing I13 |',
              '| P3 physical input/cadence/continuity | C06–C10; existing I14/I19 |',
              '| Test subject follows maintained code | C19 |',
              '| Rewrite-independent observable contract | C20 |',
              '| Later changes behind known errors affect acceptance | C21 |', '',
              'Suggested review order: ' + ', '.join(manifest['review_order']) + '. '
              'First make existing tests follow the intended implementation and reject concealed later changes; '
              'then audit duplicated core coverage before expanding integration checks. C08/C12 need time mapping; '
              'C14 is conditional on an explicit presentation policy. C16 needs an escaping render fault. '
              'This is a discussion order, not authorization to start the candidates.', '',
              'No test-count target. Completion requires every required behaviour to have adequate original-backed '
              'protection or a reviewed reason why existing tests already protect it. Candidate discovery is not '
              'completion, and implementation defects may remain known red after useful tests are built.', '']
    # Keep the machine-readable status snapshot private; it names local reports.
    out = ROOT / 'build/tests/test-manifest-inventory.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({'fresh_test_execution': False, 'classifications': dict(counts),
                               'implemented': inventory}, indent=2) + '\n', encoding='utf-8')
    (ROOT / 'tests/TEST-MANIFEST.md').write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps({'implemented_cases': len(inventory), 'families': len(manifest['implemented_families']),
                      'candidate_decisions': dict(collections.Counter(row['decision'] for row in candidates)),
                      'retained_classifications': dict(counts)}, indent=2))


if __name__ == '__main__':
    main()
