"""Confirm the resumed-launch carry defect using a temporary native-code correction."""
import configparser
import json
from phase_reference import ROOT, validate_phase
from run_regression_tests import compare, execute, prepare_inputs
from run_translated_player_frame_probe import prepare_gameplay


def main():
    case = json.loads((ROOT / 'tests/cases/resumed-play-phase.json').read_text())
    fixture = json.loads((ROOT / case['reference']).read_text())
    validate_phase(fixture, case)
    fields = json.loads((ROOT / 'tests/state-fields.json').read_text())['bytes']
    config = configparser.ConfigParser(interpolation=None)
    config.read(ROOT / 'config.local.ini', encoding='utf-8')
    prepare_inputs(fixture, case)
    prepare_gameplay()
    path = ROOT / 'build/translation/player-frame-routines.s'
    original = path.read_text()
    records, _ = execute(config, 'root-carry-baseline')
    baseline = compare(records, fixture, case, fields)
    if not baseline or any(baseline.get(key) != value for key, value in
                           {'update': 96, 'ram_offset': 87, 'expected': 199, 'actual': 200}.items()):
        raise AssertionError('The diagnosed baseline signature has changed')
    start = original.index('triangular_root_step:')
    end = original.index('derive_launch_vector:', start)
    helper = original[start:end]
    anchor = ('\tMAKE_BC_NO_AR\t\t; [sbc hl,bc]\n'
              '\tMAKE_HL_NO_AR\t\t; [sbc hl,bc]\n\tsubx.w\td2,d6')
    if helper.count(anchor) != 2:
        raise ValueError('Triangular-root translation has changed')
    # Z80 register-pair assembly must preserve carry before the SUBX input.
    helper = helper.replace(anchor, '\tPUSH_SR\n\tMAKE_BC_NO_AR\n'
                            '\tMAKE_HL_NO_AR\n\tPOP_SR\n\tsubx.w\td2,d6')
    try:
        path.write_text(original[:start] + helper + original[end:])
        records, digest = execute(config, 'root-carry-diagnostic')
        corrected = compare(records, fixture, case, fields)
        if corrected is not None:
            raise AssertionError(f'Temporary correction did not resolve the phase: {corrected}')
    finally:
        path.write_text(original)
    report = {'case': case['name'], 'updates': len(fixture['updates']),
              'baseline_first_difference': baseline, 'corrected_first_difference': corrected,
              'temporary_correction_only': True, 'generated_source_restored': path.read_text() == original,
              'corrected_executable_sha256': digest}
    (ROOT / 'build/tests/root-carry-diagnostic-report.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Baseline signature reproduced; temporary carry preservation matches all 200 updates; source restored.')


if __name__ == '__main__':
    main()
