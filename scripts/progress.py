"""Report evidence freshness, compiled runtime dependencies and delivery gates.

Read-only; writes only an ignored summary. It never runs tests or promotes old
reports. --fresh-since identifies actual executions in a caller's session.
"""
import argparse
import datetime as dt
import json
from pathlib import Path
from evidence import ROOT, TARGET, atomic_json, status, now, snapshot, python_inputs
from run_regression_tests import native_replay_cases
from physical_input_reference import CASES as INPUT_CASES


REPLAY = native_replay_cases()
GATES = {
    'CT-01': ['serve'],
    'CT-02': ['p1-accept-one-player', 'p1-accept-two-player'],
    'CT-03': list(INPUT_CASES) + ['control-ownership', 'p1-accept-one-player', 'p1-accept-two-player'],
    'CT-04': list(REPLAY) + ['p1-accept-one-player', 'p1-accept-two-player'],
    'CT-05': ['round-transition', 'two-player-match', 'deuce-sequence-phase'],
    'CT-06': ['one-player-restart-complete', 'two-player-restart-complete'],
    'CT-07': ['p1-upper-player-placement', 'p1-moving-prefix', 'p1-score-status-prefix'],
    'CT-08': ['p2-first-serve-pitch', 'p2-first-serve-envelope', 'p2-first-serve-mute', 'status-timer-saturation-phase'],
    'CT-09': ['one-player-match', 'two-player-match'],
    'CT-10': [],
}
NAMES = {
    'CT-01': 'Shared maintained dispatcher / regeneration / mutation',
    'CT-02': 'Ordinary title, held selection and accepted mode',
    'CT-03': 'Physical controls and player ownership (exchange is local)',
    'CT-04': 'Serve, rally, point ownership, movement and AI (captured starts)',
    'CT-05': 'Continuous round boundary and score lifecycle',
    'CT-06': 'Complete result / restart lifecycle',
    'CT-07': 'Direct native presentation',
    'CT-08': 'Native audio effects / cadence',
    'CT-09': 'Uninterrupted ordinary play / cadence',
    'CT-10': 'Adapter-free executable / cold bootable ADF',
}


def report_path(name):
    if name == 'serve':
        return ROOT / 'build/tests/report.json'
    if name == 'control-ownership':
        return ROOT / 'build/tests/native-control-ownership/capture.json'
    return ROOT / f'build/tests/{name}-report.json'


def progress(fresh_since=None):
    evidence = {}
    for name in sorted(set(n for names in GATES.values() for n in names)):
        subject = 'maintained' if name in REPLAY or name.startswith(('round-', 'deuce-')) or name.endswith('-match') else 'maintained-native'
        full = name in REPLAY or name in ('round-transition', 'one-player-match', 'two-player-match', 'deuce-sequence-phase')
        evidence[name] = status(report_path(name), subject, full, fresh_since)
    build_path = ROOT / 'build/amiga/gameplay-integration/build-report.json'
    build = status(build_path, 'maintained-native', fresh_since=fresh_since)
    ordinary = build.get('status') == 'passed' and build.get('startup') == 'ordinary title'
    symbols = set(json.loads(build_path.read_text()).get('compiled_symbols', [])) if ordinary else set()
    native = {'serve/contact': ['game_player_tick', 'game_player_contact'],
              'ball/launch': ['game_ball_tick', 'game_derive_launch', 'game_launch_root'],
              'movement': ['game_move_player'], 'AI': ['game_ai_track', 'game_ai_setup']}
    old = {'serve/contact': ['lower_player_state', 'upper_player_state'],
           'ball/launch': ['ball_flight_update', 'derive_launch_vector', 'triangular_root_step'],
           'movement': ['lower_player_motion_update', 'upper_player_movement'], 'AI': ['predict_ball_intercept', 'direction_ai']}
    remaining = {'score/lifecycle': ['score_gate', 'scoreboard_update'],
                 'presentation': ['build_player_sprites', 'virtual_memory', 'shadow_vram'],
                 'audio': ['audio_tick_adapter']}
    architecture = {'ordinary_build': build, 'subsystems': {}}
    for group in native:
        architecture['subsystems'][group] = {'integration': ('native entry points compiled; replaced translated entry points absent'
            if ordinary and all(n in symbols for n in native[group]) and not any(n in symbols for n in old[group])
            else 'unverified'), 'native_entry_points': [n for n in native[group] if n in symbols],
            'translated_entry_points': [n for n in old[group] if n in symbols]}
    for group, labels in remaining.items():
        architecture['subsystems'][group] = {'integration': 'temporary runtime dependencies remain' if ordinary and any(n in symbols for n in labels) else 'unverified',
                                             'compiled_dependencies': [n for n in labels if n in symbols]}
    capabilities = {}
    for gate, names in GATES.items():
        verified = bool(names) and all(evidence[n]['status'] == 'passed' for n in names)
        reasons = []
        if gate in ('CT-01', 'CT-02', 'CT-03', 'CT-04') and not ordinary:
            verified = False
            reasons.append('Current ordinary executable build dependencies unverified')
        if gate in ('CT-02', 'CT-03', 'CT-04') and not all(
                evidence[n].get('startup') == 'ordinary title'
                for n in ('p1-accept-one-player', 'p1-accept-two-player')):
            verified = False
            reasons.append('Ordinary mode starts unverified')
        if gate == 'CT-04' and not all(
                architecture['subsystems'][n]['integration'] != 'unverified' for n in native):
            verified = False
            reasons.append('Ordinary compiled gameplay routing unverified')
        if gate == 'CT-01' and verified:
            r = json.loads(report_path('serve').read_text())
            verified = bool(r.get('regeneration_preserved_native_modules') and r.get('mutation_first_difference') and r.get('restored_replay_passed'))
            if not verified:
                reasons.append('Dispatcher mutation/restoration evidence missing')
        if gate in ('CT-05', 'CT-06', 'CT-07', 'CT-08', 'CT-09', 'CT-10'):
            verified = False  # Existing narrow diagnostics are not complete delivery acceptance.
            reasons.append('Direct subsystem/full ordinary delivery acceptance not recorded by this integration')
        capabilities[gate] = {'capability': NAMES[gate], 'acceptance': 'evidenced within stated scope' if verified else 'unverified',
                              'evidence': names, 'limitations': reasons}
    runtime_target = all(evidence[n]['status'] == 'passed' and evidence[n].get('startup') == 'ordinary title'
                         for n in GATES['CT-02'])
    supporting = {'captured_live_serve': status(
        ROOT/'build/amiga/gameplay-integration/serve-report.json', 'maintained-native',
        fresh_since=fresh_since)}
    return {'behavior': {'capabilities': capabilities, 'evidence': evidence, 'supporting_evidence': supporting},
            'runtime_dependencies': architecture,
            'delivery': {'target': TARGET, 'ordinary_target_execution': 'evidenced in mode/control checks' if runtime_target else 'unverified',
                         'peak_chip_ram': 'unverified', 'cadence_and_full_ordinary_play': 'unverified',
                         'cold_ADF_boot': 'not run', 'independent_emulator_or_hardware': 'unverified'},
            'scope': 'Retained reports checked against current dependencies; integration symbols are not runtime acceptance. No percentages or file-size RAM estimate.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fresh-since', help='ISO UTC/session timestamp; older compatible executions are labelled reused')
    args = parser.parse_args()
    if args.fresh_since:
        try:
            stamp = dt.datetime.fromisoformat(args.fresh_since)
            if stamp.tzinfo is None:
                raise ValueError('Timezone required')
            args.fresh_since = stamp.astimezone(dt.timezone.utc).isoformat()
        except ValueError:
            parser.error('Use an ISO timestamp with timezone')
    output = ROOT/'build/progress-report.json'
    atomic_json(output, {'state': 'incomplete', 'started_utc': now()})
    try:
        result = progress(args.fresh_since)
        report_paths = {report_path(n) for names in GATES.values() for n in names}
        report_paths.update(ROOT/'build/amiga/gameplay-integration'/n
                            for n in ('build-report.json', 'serve-report.json'))
        result['view_provenance'] = {
            'generated_utc': now(), 'fresh_since': args.fresh_since,
            'sources': snapshot(python_inputs(Path(__file__).resolve())),
            'reports': snapshot(report_paths),
            'scope': 'Snapshot view; rerun this command before trusting current gates.'}
        result['state'] = 'complete'
        atomic_json(output, result)
        print(json.dumps(result, indent=2))
    except BaseException as error:
        atomic_json(output, {'state': 'interrupted' if isinstance(error, KeyboardInterrupt) else 'failed',
                             'completed_utc': now(), 'error': str(error)})
        raise


if __name__ == '__main__':
    main()
