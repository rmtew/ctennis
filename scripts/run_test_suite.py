"""Run registered native regressions and keep incomplete required coverage visible."""
import argparse
import json
import subprocess
import sys
from pathlib import Path
from phase_reference import CASES as PHASE_CASES

ROOT = Path(__file__).resolve().parent.parent
PRESENTATION_CASES = ('p1-title', 'p1-upper-player-placement')
CASES = ('serve', 'round-transition', 'one-player-match', 'two-player-match') + PHASE_CASES + PRESENTATION_CASES
# These requirements await evidence-backed cases or a justified coverage inventory.
MISSING = ['R2 same-rally return by both players (full match captured; rally gap remains)', 'F1-F5 meaningful-gap inventory and cases',
           'phase-specific comparisons after the first continuous failure',
           'remaining P1 native graphics cases (source checkpoints retained; native title registered)',
           'P2 audio references and native comparisons',
           'P3 timing/input references and native comparisons']


def classify(report, expected):
    difference = report['first_difference']
    if report['passed']:
        return 'unexpected-green' if expected else 'green'
    if not expected:
        return 'unexpected-red'
    signature = expected['signature']
    if difference and all(difference.get(key) == value for key, value in signature.items()):
        return 'known-red'
    return 'unexpected-red'


def verify_failure_policy(known):
    for case, expected in known.items():
        report = {'passed': False, 'first_difference': expected['signature']}
        original = expected['signature']['actual']
        changed = original ^ 1 if isinstance(original, int) else original + '00'
        altered = {'passed': False, 'first_difference': {**expected['signature'], 'actual': changed}}
        if classify(report, expected) != 'known-red' or classify(altered, expected) != 'unexpected-red':
            raise AssertionError(f'Known-failure signature policy failed: {case}')
        if classify({'passed': True, 'first_difference': None}, expected) != 'unexpected-green':
            raise AssertionError(f'Unexpected pass was silently accepted: {case}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline-check', action='store_true',
                        help='Accept verified known-red signatures; missing coverage still fails')
    parser.add_argument('--self-test', action='store_true',
                        help='Verify mutation detection and changed-signature rejection')
    args = parser.parse_args()
    known = json.loads((ROOT / 'tests/known-failures.json').read_text())['cases']
    if args.self_test:
        verify_failure_policy(known)
    results = []
    out = ROOT / 'build/tests'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'suite-report.json').unlink(missing_ok=True)
    for case in CASES:
        report_path = out / ('report.json' if case == 'serve' else f'{case}-report.json')
        # Never classify stale output from a failed invocation as a known failure.
        report_path.unlink(missing_ok=True)
        runner = 'scripts/run_presentation_tests.py' if case in PRESENTATION_CASES else 'scripts/run_regression_tests.py'
        command = [sys.executable, runner, '--case', case]
        if args.baseline_check and case in known and case not in PRESENTATION_CASES:
            command += ['--through-update', str(max(1, known[case]['signature']['update']))]
        if args.self_test and case in ('serve',) + PRESENTATION_CASES:
            command.append('--self-test')
        process = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        (out / f'{case}-runner.log').write_text(process.stdout + process.stderr)
        if process.returncode not in (0, 1) or not report_path.exists():
            results.append({'case': case, 'status': 'tool-error', 'exit_code': process.returncode})
            continue
        report = json.loads(report_path.read_text())
        if report['passed'] != (process.returncode == 0):
            raise ValueError('Runner exit status and report disagree')
        status = classify(report, known.get(case))
        results.append({'case': case, 'status': status, 'report': str(report_path),
                        'first_difference': report['first_difference']})
        print(f'{case}: {status}', flush=True)
    allowed = {'green', 'known-red'} if args.baseline_check else {'green'}
    passed = not MISSING and all(row['status'] in allowed for row in results)
    summary = {'baseline_check': args.baseline_check, 'passed': passed,
               'cases': results, 'missing_requirements': MISSING,
               'self_test': args.self_test}
    (out / 'suite-report.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({'passed': passed, 'missing_requirements': MISSING}, indent=2))
    return 0 if passed else 2 if MISSING or any(row['status'] == 'tool-error' for row in results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
