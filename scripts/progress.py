"""Report evidence freshness, compiled runtime dependencies and delivery gates.

Read-only; writes only an ignored summary. It never runs tests or promotes old
reports. --fresh-since identifies actual executions in a caller's session.
"""
import argparse
import datetime as dt
import json
from pathlib import Path
from evidence import ROOT, TARGET, atomic_json, status, now, snapshot, python_inputs, digest
from run_regression_tests import native_replay_cases
from physical_input_reference import CASES as INPUT_CASES
from maintained_state_contract import MAINTAINED_STATE_CONTRACT, MAINTAINED_SCRATCH_OFFSETS


REPLAY = native_replay_cases()
CT05_REPLAY = ('round-transition', 'deuce-sequence-phase',
               'one-player-round-lower-complete-phase', 'one-player-round-upper-complete-phase',
               'two-player-round-lower-complete-phase', 'two-player-round-upper-complete-phase',
               'two-player-resumed-serve-complete-phase', 'two-player-upper-resumed-serve-complete-phase')
CT05_SCENES = ('p1-first-round-scenes', 'p1-one-player-upper-round-scenes',
               'p1-two-player-lower-round-scenes', 'p1-two-player-upper-round-scenes')
CT06_PHASES = ('one-player-match-complete-phase', 'two-player-match-complete-phase')
CT06_SCENES = ('p1-one-player-result-restart-scenes', 'p1-two-player-result-restart-scenes')
GATES = {
    'CT-01': ['serve'],
    'CT-02': ['p1-accept-one-player', 'p1-accept-two-player'],
    'CT-03': list(INPUT_CASES) + ['control-ownership', 'p1-accept-one-player', 'p1-accept-two-player'],
    'CT-04': list(REPLAY) + ['p1-accept-one-player', 'p1-accept-two-player'],
    'CT-05': list(CT05_REPLAY) + list(CT05_SCENES) + ['ct05-r2-first-round', 'ct05-ordinary-one-round', 'ct05-ordinary-two-round'],
    'CT-06': list(CT06_PHASES) + list(CT06_SCENES) + ['ct06-ordinary-one-restart', 'ct06-ordinary-two-restart', 'ct06-ordinary-one-early-release'],
    'CT-07': ['p1-upper-player-placement', 'p1-moving-prefix', 'p1-score-status-prefix', *CT05_SCENES, *CT06_SCENES, 'p1-accept-one-player', 'p1-accept-two-player'],
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


def presentation_proof(report, recipe):
    """Finite CT07 recipes: exact pixels and only the established raw scratch debt."""
    if (report.get('subject') != 'maintained-native'
            or report.get('state_contract') != MAINTAINED_STATE_CONTRACT
            or report.get('omitted_legacy_scratch_offsets') != list(MAINTAINED_SCRATCH_OFFSETS)
            or report.get('self_test') is not True or report.get('passed') is not True
            or report.get('first_difference') is not None):
        return False
    if recipe['name'] == 'p1-upper-player-placement':
        raw = report.get('raw_state_differences', [])
        raster = report.get('completed_raster', {})
        return (report.get('region') == recipe['region']
                and report.get('native_observation', {}).get('completed_callbacks') == recipe['completed_callbacks']
                and bool(raster.get('generation'))
                and all(r.get('offset') in MAINTAINED_SCRATCH_OFFSETS for r in raw))
    checks = report.get('checks', [])
    expected = [(c,f) for c in recipe['completed_callbacks'] for f in recipe['fields']]
    return ([(r.get('requested_callback'), r.get('field')) for r in checks] == expected
            and all(r.get('first_difference') is None and r.get('raster', {}).get('generation') for r in checks)
            and [r.get('update') for r in report.get('raw_state_differences', [])] == recipe['completed_callbacks']
            and all(d.get('offset') in MAINTAINED_SCRATCH_OFFSETS
                    for r in report['raw_state_differences'] for d in r['differences']))


def report_path(name):
    if name == 'ct05-r2-first-round':
        name = 'two-player-match'
    if name == 'serve':
        return ROOT / 'build/tests/report.json'
    if name == 'control-ownership':
        return ROOT / 'build/tests/native-control-ownership/capture.json'
    return ROOT / f'build/tests/{name}-report.json'


def bounded_round_status(path, fresh_since=None):
    """R2 first round through source-observed next serve; never full-match proof."""
    result = status(path, 'maintained', full=False, fresh_since=fresh_since)
    if result['status'] != 'passed':
        return result
    try:
        report = json.loads(Path(path).read_text())
        reference = ROOT / 'tests/reference/two-player-match.json'
        fixture = json.loads(reference.read_text())
        milestones = fixture['milestones']
        checkpoints = [milestones[n]['update'] for n in
                       ('first_game_award', 'tail_only_start', 'gameplay_resumed', 'resumed_serve_flight')]
        required = checkpoints[-1]
        count = len(fixture['updates'])
        executed = report['updates']
        if (report.get('case') != 'two-player-match'
                or fixture.get('reference_kind') == 'source-derived-phase'
                or fixture['initial_callback'].get('ordinal') != 0
                or report.get('reference_sha256') != digest(reference)
                or report['evidence']['files'].get(str(reference.relative_to(ROOT))) != digest(reference)
                or any(type(n) is not int or n <= 0 for n in checkpoints)
                or checkpoints != sorted(set(checkpoints))
                or type(executed) is not int or not required <= executed <= count
                or report.get('updates_matched') != executed
                or report.get('reference_updates') != count):
            raise ValueError('Continuous R2 first-round/next-serve proof missing or extent insufficient')
    except (OSError, ValueError, KeyError, TypeError) as error:
        return dict(result, status='failed', reason=str(error))
    return dict(result, scope='Continuous R2 first round through advancing resumed serve',
                required_updates=required, full_match_executed=report.get('full_replay_executed') is True,
                full_match_reference=count)


def ordinary_round_proof(report, mode, executable_sha256):
    """Require the ordinary runner's actual ordered lifecycle observations."""
    checkpoints = [report.get(k) for k in
                   ('award_callback', 'pause_callback', 'resume_callback', 'next_serve_callback')]
    return (report.get('case') == f'ct05-ordinary-{mode}-round'
            and report.get('executable_sha256') == executable_sha256
            and all(type(n) is int and n > 0 for n in checkpoints)
            and checkpoints == sorted(set(checkpoints))
            and type(report.get('observed_callbacks')) is int
            and report['observed_callbacks'] >= checkpoints[-1] - checkpoints[0] + 1)


def result_scene_proof(report, recipe, fault_kinds=('entropy', 'field', 'sprite')):
    """A local source phase proves only its declared complete scene window."""
    start=recipe['initial_source_update'];targets=recipe['completed_callbacks']
    states=report.get('checks',{}).get('states',[])
    pixels=report.get('checks',{}).get('pixels',[])
    regions=('viewport','point_a','point_b','games_a','games_b','status','mode')
    return (report.get('case')==recipe['name'] and report.get('subject')=='maintained-native'
        and report.get('state_contract')==MAINTAINED_STATE_CONTRACT
        and report.get('omitted_legacy_scratch_offsets')==list(MAINTAINED_SCRATCH_OFFSETS)
        and report.get('state_bytes_compared_per_callback')==250
        and report.get('raw_state_subject')=='maintained-native'
        and report.get('raw_state_contract')=='original-byte-page-diagnostic-v1'
        and report.get('raw_state_bytes_compared_per_callback')==254
        and isinstance(report.get('raw_state_passed'),bool)
        and [row.get('update') for row in states]==list(range(start+1,targets[-1]+1))
        and all(row.get('differences')==[] for row in states)
        and [(row.get('checkpoint'),row.get('region')) for row in pixels]
            ==[(target,region) for target in targets for region in regions]
        and all(row.get('expected_sha256')==row.get('actual_sha256')
                and row.get('expected_sha256') and row.get('first_difference') is None for row in pixels)
        and report.get('checks',{}).get('source_events')==[]
        and sorted((m.get('kind'),m.get('detected')) for m in report.get('hardware_mutations',[]))
            ==sorted((kind,True) for kind in fault_kinds))

def ordinary_restart_proof(report,mode,executable_sha256):
    """Ordinary physical path is distinct from captured result initialization."""
    checkpoints=report.get('checkpoints',{})
    names=('match_award','returned_title_display','title_ready','restart_selected',
           'restart_playing','old_action_blocked','restart_action','restarted_flight')
    values=[checkpoints.get(name) for name in names]
    return (report.get('case')==f'ct06-ordinary-{mode}-restart'
        and report.get('subject')=='maintained-native'
        and report.get('executable_sha256')==executable_sha256
        and report.get('start_mode')==mode
        and report.get('restart_mode')==('two' if mode=='one' else 'one')
        and report.get('consecutive_callbacks') is True
        and report.get('held_old_actions_verified') is True
        and all(type(n) is int and n>0 for n in values)
        and values==sorted(set(values))
        and type(report.get('observed_callbacks')) is int
        and report['observed_callbacks']>=values[-1]-values[0]+1)


def early_release_proof(report, executable_sha256):
    names=('match_award','returned_title_display','title_ready','restart_selected',
           'early_release','sampled_release','early_repress','sampled_repress',
           'restart_playing','fresh_action_eligible','restarted_flight')
    points=report.get('checkpoints',{});values=[points.get(n) for n in names]
    samples=report.get('action_samples',{})
    expected={'before_release':(9,[16,16],[16,16]),'sampled_release':(9,[0,16],[0,16]),
              'sampled_repress':(9,[16,16],[0,16]),'playable':(1,[16,16],[0,16])}
    return (report.get('case')=='ct06-ordinary-one-early-release'
        and report.get('subject')=='maintained-native'
        and report.get('executable_sha256')==executable_sha256
        and report.get('start_mode')=='one' and report.get('restart_mode')=='two'
        and report.get('consecutive_callbacks') is True and report.get('early_release_verified') is True
        and all(type(n) is int and n>0 for n in values) and values==sorted(set(values))
        and type(report.get('observed_callbacks')) is int
        and report['observed_callbacks']>=values[-1]-values[0]+1
        and all(samples.get(name,{}).get('lifecycle')==state
                and samples[name].get('raw')==raw and samples[name].get('latches')==latches
                for name,(state,raw,latches) in expected.items())
        and samples['sampled_release'].get('released')==[16,0]
        and samples['sampled_repress'].get('pressed')==[16,0]
        and samples['playable'].get('controls')==[16,0]
        and samples['sampled_release'].get('callback')==points['sampled_release']
        and samples['sampled_repress'].get('callback')==points['sampled_repress']
        and samples['playable'].get('callback')==points['fresh_action_eligible'])


def progress(fresh_since=None):
    evidence = {}
    for name in sorted(set(n for names in GATES.values() for n in names)):
        if name == 'ct05-r2-first-round':
            evidence[name] = bounded_round_status(report_path(name), fresh_since)
            continue
        subject = 'maintained' if name in REPLAY or name in CT05_REPLAY or name.startswith(('round-', 'deuce-')) or name in CT06_PHASES or name.endswith('-match') else 'maintained-native'
        full = name in CT06_PHASES or name in REPLAY or name in CT05_REPLAY or name in ('round-transition', 'one-player-match', 'two-player-match', 'deuce-sequence-phase')
        evidence[name] = status(report_path(name), subject, full, fresh_since)
        if name in CT05_SCENES + CT06_SCENES and evidence[name]['status'] in ('passed', 'failed'):
            report = json.loads(report_path(name).read_text())
            evidence[name]['state_contract'] = report.get('state_contract')
            evidence[name]['raw_diagnostic'] = {k: report.get('raw_state_' + k) for k in
                ('subject', 'contract', 'passed', 'bytes_compared_per_callback', 'first_difference')}
    build_path = ROOT / 'build/amiga/gameplay-integration/build-report.json'
    build = status(build_path, 'maintained-native', fresh_since=fresh_since)
    ordinary = build.get('status') == 'passed' and build.get('startup') == 'ordinary title'
    symbols = set(json.loads(build_path.read_text()).get('compiled_symbols', [])) if ordinary else set()
    native = {'serve/contact': ['game_player_tick', 'game_player_contact'],
              'ball/launch': ['game_ball_tick', 'game_derive_launch', 'game_launch_root'],
              'movement': ['game_move_player'], 'AI': ['game_ai_track', 'game_ai_setup'],
              'presentation': ['game_scene_finish_tick', 'game_render_sprites', 'game_scene_update_fields']}
    old = {'serve/contact': ['lower_player_state', 'upper_player_state'],
           'ball/launch': ['ball_flight_update', 'derive_launch_vector', 'triangular_root_step'],
           'movement': ['lower_player_motion_update', 'upper_player_movement'], 'AI': ['predict_ball_intercept', 'direction_ai'],
           'presentation': ['build_player_sprites', 'scoreboard_update', 'irq_vdp_tail', 'shadow_vram', 'copy_cpu_bytes_to_vram_b_count']}
    remaining = {'score/lifecycle': ['score_gate', 'scoreboard_update'],
                 'shared scalar ABI (CT10)': ['virtual_memory'],
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
        if gate in ('CT-01', 'CT-02', 'CT-03', 'CT-04', 'CT-05', 'CT-06') and not ordinary:
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
        if gate == 'CT-05':
            for scene in CT05_SCENES:
                if evidence[scene]['status'] != 'passed':
                    continue
                report = json.loads(report_path(scene).read_text())
                if (report.get('subject') != 'maintained-native'
                        or report.get('state_contract') != MAINTAINED_STATE_CONTRACT
                        or report.get('omitted_legacy_scratch_offsets') != list(MAINTAINED_SCRATCH_OFFSETS)
                        or report.get('state_bytes_compared_per_callback') != 250
                        or report.get('raw_state_subject') != 'maintained-native'
                        or report.get('raw_state_contract') != 'original-byte-page-diagnostic-v1'
                        or report.get('raw_state_bytes_compared_per_callback') != 254
                        or not isinstance(report.get('raw_state_passed'), bool)
                        or sorted((m.get('kind'), m.get('detected')) for m in report.get('hardware_mutations', []))
                           != [('entropy', True), ('field', True), ('sprite', True), ('state', True)]):
                    verified = False
                    reasons.append(f'{scene} maintained semantic/raw contract missing')
            for mode in ('one', 'two'):
                name = f'ct05-ordinary-{mode}-round'
                if (not ordinary or evidence[name]['status'] != 'passed'
                        or evidence[name].get('startup') != 'ordinary title'
                        or evidence[name].get('kind') != 'ordinary-round'
                        or not ordinary_round_proof(json.loads(report_path(name).read_text()), mode,
                            json.loads(build_path.read_text()).get('executable_sha256'))):
                    verified = False
                    reasons.append(f'Ordinary {mode}-player first-game/next-serve acceptance missing')
            if not all(n in symbols for n in ('game_score_resolve', 'game_round_poll')) or 'score_gate' in symbols:
                verified = False
                reasons.append('Ordinary native scoring/round routing unverified')
            if any(evidence[n]['status'] != 'passed' for n in names):
                reasons.append('Required bounded round/serve/deuce/scene evidence missing or failing')
        if gate == 'CT-06':
            for scene in CT06_SCENES:
                if evidence[scene]['status'] != 'passed':continue
                recipe=json.loads((ROOT/f'tests/cases/{scene}.json').read_text())
                if not result_scene_proof(json.loads(report_path(scene).read_text()),recipe):
                    verified=False;reasons.append(f'{scene} complete semantic/pixel/event/fault acceptance missing')
            for mode in ('one','two'):
                name=f'ct06-ordinary-{mode}-restart'
                if (not ordinary or evidence[name]['status']!='passed'
                        or evidence[name].get('startup')!='ordinary title'
                        or evidence[name].get('kind')!='ordinary-round'
                        or not ordinary_restart_proof(json.loads(report_path(name).read_text()),mode,
                            json.loads(build_path.read_text()).get('executable_sha256'))):
                    verified=False;reasons.append(f'Ordinary {mode}-player match/title/restarted serve missing')
            name='ct06-ordinary-one-early-release'
            if (not ordinary or evidence[name]['status']!='passed'
                    or evidence[name].get('startup')!='ordinary title'
                    or evidence[name].get('kind')!='ordinary-round'
                    or not early_release_proof(json.loads(report_path(name).read_text()),
                        json.loads(build_path.read_text()).get('executable_sha256'))):
                verified=False;reasons.append('Restart-sound release/repress with continuously held P2 acceptance missing')
            if not all(n in symbols for n in ('game_result_poll','game_restart_begin','game_menu_tick','game_source_tick')):
                verified=False;reasons.append('Ordinary native result/restart routing unverified')
        if gate == 'CT-07':
            if not ordinary or not all(n in symbols for n in native['presentation']) or any(n in symbols for n in old['presentation']):
                verified = False
                reasons.append('Ordinary native display routing/bridge retirement unverified')
            for name in names[:3]:
                if evidence[name]['status'] == 'passed' and not presentation_proof(json.loads(report_path(name).read_text()), json.loads((ROOT/f'tests/cases/{name}.json').read_text())):
                    verified = False
                    reasons.append(f'{name} complete exact pixel/semantic coverage missing')
            for name in CT05_SCENES:
                if evidence[name]['status'] == 'passed':
                    r = json.loads(report_path(name).read_text())
                    recipe = json.loads((ROOT/f'tests/cases/{name}.json').read_text())
                    if not result_scene_proof(r, recipe, ('entropy','field','sprite','state')):
                        verified = False
                        reasons.append(f'{name} complete round pixel/event/fault protection missing')
            for name in CT06_SCENES:
                if evidence[name]['status'] == 'passed' and not result_scene_proof(json.loads(report_path(name).read_text()), json.loads((ROOT/f'tests/cases/{name}.json').read_text())):
                    verified = False
                    reasons.append(f'{name} complete result pixel/event/fault protection missing')
        if gate in ('CT-08', 'CT-09', 'CT-10'):
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
