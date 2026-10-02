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
from fractions import Fraction
from bisect import bisect_right


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
    'CT-08': ['p2-first-serve-pitch', 'p2-first-serve-envelope', 'p2-first-serve-mute', 'ct08-effect-classes', 'status-timer-saturation-phase', 'ct06-ordinary-one-restart'],
    'CT-09': ['one-player-match', 'two-player-match', 'ct09-ordinary-one-cadence',
              'ct09-ordinary-two-cadence', 'ct09-input-timing-edges','ct09-published-bank-control'],
    'CT-10': ['ct10-adf-one-cadence','one-player-match','two-player-match',
              'ct09-ordinary-one-cadence','ct09-ordinary-two-cadence',
              'ct09-input-timing-edges','ct09-published-bank-control','ct06-ordinary-one-restart',
              # Newly demonstrated delivery regressions remain required guards;
              # ordinary match counts cannot override a broken pixel/raster check.
              'p1-moving-prefix','p1-upper-serve',
              *[f'p1-status-{n}-lifecycle' for n in range(2,6)]],
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
    if recipe['name']=='p1-upper-serve' and report.get('interface_flavor')=='enhanced':
        rows=checks + report.get('hardware_mutation',{}).get('checks',[])
        if any(r.get('raster',{}).get('requested_generation')!=r.get('requested_callback')
               or type(r.get('raster',{}).get('wait_horizon_callback')) is not int
               or r['raster']['wait_horizon_callback'] < r.get('requested_callback',0)
               or r.get('raster',{}).get('generation',{}).get('prepared_after_callback')!=r.get('requested_callback')
               or r.get('source',{}).get('generation')!=r.get('requested_callback')
               or r.get('requested_callback')==4131 and (r.get('source',{}).get('hardware_frames')!=[5430]
                                                         or r.get('source',{}).get('pixel_frames')!=[5432])
               for r in rows):
            return False
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


def status_lifecycle_proof(report, recipe):
    """The existing finite status contract: every callback, raster and fault."""
    checks = report.get('checks', {})
    timing, pixels = checks.get('timing', []), checks.get('pixels', [])
    mutations = report.get('hardware_mutations', [])
    return (report.get('subject') == 'maintained-native' and report.get('passed') is True
            and report.get('first_difference') is None and checks.get('first_difference') is None
            and report.get('self_test') is True
            and [r.get('update') for r in timing] == list(range(recipe['initial_source_update'] + 1, recipe['completed_callbacks'][-1] + 1))
            and all(r.get('first_difference') is None for r in timing)
            and [r.get('requested_callback') for r in pixels] == recipe['completed_callbacks']
            and all(r.get('first_difference') is None and r.get('raster', {}).get('generation') for r in pixels)
            and [m.get('kind') for m in mutations] == ['retain', 'early']
            and all(m.get('detected') is True
                    and m.get('mutation_first_difference', {}).get('boundary') == 'native-status-selection'
                    and m['mutation_first_difference'].get('update') == recipe['expiry_callback'] - (m['kind'] == 'early')
                    and m.get('executable_sha256') != report.get('executable_sha256') for m in mutations))


def cadence_proof(report, mode, executable_sha, cold_adf=False, interface_flavor=None, keyboard=False):
    """Validate the finite ordinary receipt, never promote replay counts to CT09."""
    from ordinary_cadence import clock_contract
    expected_case=f'ct10-adf-{mode}-cadence' if cold_adf else f'ct09-ordinary-{mode}-cadence'
    if interface_flavor:
        expected_case+='-'+interface_flavor+('-keyboard' if keyboard else '')
        if report.get('interface_flavor')!=interface_flavor:return False
    if (report.get('passed') is not True or report.get('first_difference') is not None
            or report.get('case') != expected_case
            or report.get('subject') != 'maintained-native' or report.get('start_mode') != mode
            or report.get('restart_mode') != ('two' if mode == 'one' else 'one')
            or report.get('startup') != ('cold ADF' if cold_adf else 'ordinary title') or report.get('entropy') != 'ordinary native timer'
            or report.get('uninterrupted') is not True or report.get('callback_breakpoints') != 0
            or not executable_sha or report.get('executable_sha256') != executable_sha):
        return False
    try:
        captured = ROOT/report['capture']
        if report['evidence']['files'].get(str(captured.relative_to(ROOT))) != digest(captured):
            return False
        application = captured.parent/'native-application'
        if report['evidence']['compiled_executables'].get(str(application.relative_to(ROOT))) != executable_sha:
            return False
        measurement = json.loads((ROOT/report['capture']).read_text())
        log = (ROOT/report['capture']).parent.joinpath('emulator.log').read_text()
        if any(marker not in log for marker in ('cpu=M68000','chip_ram=512K','fast_ram=0K',
                'slow_ram=0K','z3_ram=0K','chipset=Ocs','video=Pal','Kickstart 1.3 (34.5)')):
            return False
        if cold_adf:
            adf=ROOT/report['adf']
            loaded=measurement['loaded_executable_checks']
            allocations=measurement['boot_allocations']
            regions=measurement['boot_calibration']['regions']
            headers={str(r['header']):r for r in regions}
            positions=[r['position']['cck'] for r in allocations]
            if positions!=sorted(positions):return False
            for row in allocations:
                free=row['free_counts']
                if (set(free)!=set(headers) or row['used_chip_bytes']!=524288-sum(free.values())
                        or any(not 0<=n<=headers[h]['upper']-headers[h]['lower'] for h,n in free.items())):
                    return False
            if (report.get('loaded_executable_verified') is not True
                    or report['adf_sha256']!=digest(adf)
                    or report['evidence']['files'].get(str(adf.relative_to(ROOT)))!=digest(adf)
                    or 'run' in measurement['launch'] or not loaded
                    or any(c.get('matched') is not True or c.get('expected_sha256')!=c.get('actual_sha256') for c in loaded)
                    or not allocations or allocations[0]['position']['cck']>=measurement['timer_start_cck']
                    or allocations[-1]['used_chip_bytes']!=measurement['memory_final']['used_chip_bytes']
                    or report['memory']['cold_boot_peak']!=max(r['used_chip_bytes'] for r in allocations)):
                return False
        contract = clock_contract()
        if measurement['clock_contract'] != contract or report['cadence']['clock_contract'] != contract:
            return False
        rows = measurement['callbacks']
        if not rows or len(rows) != report['observed_callbacks']:
            return False
        pending = measurement.get('pending_final_callback')
        if pending and (pending != report.get('pending_final_callback') or pending.get('callback') != len(rows)+1
                        or 'completion' in pending or measurement['stop'].get('reason') != 'pause'):
            return False
        if report.get('started_callbacks') != len(rows)+bool(pending):
            return False
        origin = measurement['timer_start_cck']+(65535-measurement['timer_origin_count'])*5
        if origin != measurement['clock_origin_cck']:
            return False
        interval = Fraction(contract['source_period_attoseconds']*contract['cck_hz'],10**18)
        for n, row in enumerate(rows,1):
            if row['callback'] != n or row['entry']['cck'] >= row['completion']['cck']:
                return False
            ideal = origin+(n-1)*interval
            allowance = 10+Fraction((n-1)*5,131072)
            if row['entry']['cck'] < ideal-allowance or row['completion']['cck'] >= ideal+interval+allowance:
                return False
        required = ('initial_title','first_selection','first_release','first_play','first_flight',
                    'point','game','pause','resume','result','returned_title','restart_title_ready',
                    'restart_selection','restart_release','restart_play','held_blocked','fresh_action','restarted_flight','finished')
        checkpoints = measurement['checkpoints']
        if checkpoints != report['checkpoints'] or any(k not in checkpoints for k in required):
            return False
        sequence = [checkpoints[k]['callback'] for k in required]
        if sequence != sorted(sequence) or sequence[-1] != len(rows):
            return False
        result_ram = bytes.fromhex(checkpoints['result']['ram'])
        if max(result_ram[0x40:0x42]) != 6 or any(result_ram[0x3e:0x40]):
            return False
        for label, selected in (('first_selection',mode),('restart_selection',report['restart_mode'])):
            selected_ram = bytes.fromhex(checkpoints[label]['ram'])
            if bool(selected_ram[0x3d]&128) != (selected=='two') or any(selected_ram[0x3e:0x42]):
                return False
        held_start, held_end = checkpoints['restart_play']['callback'], checkpoints['held_blocked']['callback']
        if held_end-held_start < 80:
            return False
        for row in rows[held_start-1:held_end]:
            if row['flight'] or any(v&0x30 for v in bytes.fromhex(row['controls'])[6:8]):
                return False
        memory = measurement['memory_final']
        if (report['memory']['continuous_allocation_watch'] is not True
                or any(w['position']['cck'] >= measurement['timer_start_cck'] for w in measurement['memory_writes'])
                or memory['used_chip_bytes'] != 524288-sum(h['free'] for h in memory['regions'])
                or report['memory']['peak_chip_bytes'] != memory['used_chip_bytes']
                or not 0 < memory['used_chip_bytes'] < 524288):
            return False
        watched = {(w['addr'],w['len'],w['access']) for w in measurement['watch_ranges']}
        if any((h['header'],32,'write') not in watched or not h['attributes']&2
               or sum(c['bytes'] for c in h['chunks']) != h['free'] for h in memory['regions']):
            return False
        commits = measurement['commits']
        generations = [c['generation'] for c in commits]
        if not commits or generations != sorted(set(generations)):
            return False
        if any(c['generation'] > len(rows) or 44 <= c['position']['vpos'] < 236 for c in commits):
            return False
        banks = measurement['bank_addresses']
        preparations = measurement['prepared_scenes']
        prepared_by_key={(p['generation'],p['bank'],p['position']['cck']):p for p in preparations}
        prepare_times=[p['position']['cck'] for p in preparations]
        if prepare_times!=sorted(set(prepare_times)):
            return False
        for commit in commits:
            prepared = commit['prepared']
            selections=[v for v in measurement['view_selections'] if v['position']['cck']<=commit['position']['cck']]
            title=selections[-1]['title'] if selections else measurement['title_initial']
            if not title and 25 <= commit['position']['vpos'] < 236:
                return False
            expected=banks['title_copper'] if title else prepared['bank']
            index=bisect_right(prepare_times,commit['position']['cck'])-1
            if (prepared_by_key.get((prepared['generation'],prepared['bank'],prepared['position']['cck']))!=prepared or prepared['generation']!=commit['generation']
                    or index<0 or preparations[index]!=prepared
                    or rows[prepared['generation']-1]['completion']['cck']>commit['position']['cck']
                    or prepared['bank'] not in (banks['copperlist'],banks['copperlist_back'])
                    or prepared['position']['cck']>=commit['position']['cck']
                    or commit['title_selected']!=title or commit['pointer']!=expected
                    or commit['expected_pointer']!=expected):
                return False
        if report['presentation'].get('actual_pointer_checked') is not True:
            return False
        if any(str(c['id']) not in measurement['replies'] or 'error' in measurement['replies'][str(c['id'])]
               for c in measurement['inputs']):
            return False
        return True
    except (KeyError,TypeError,ValueError,OSError):
        return False


def timing_edge_proof(report, executable_sha):
    if (report.get('passed') is not True or report.get('first_difference') is not None
            or report.get('subject')!='maintained-native' or not executable_sha
            or report.get('case')!='ct09-input-timing-edges'
            or report.get('executable_sha256') != executable_sha):
        return False
    checks = report.get('checks',[])
    if [(c.get('kind'),c.get('boundary')) for c in checks] != [(k,b) for k in ('direction','action') for b in ('before','after')]:
        return False
    for c in checks:
        try:
            a,b = c['actual'],c['before']
            if c['passed'] is not True or a['started'] != b['started']+(c['boundary']=='after') or a['completed'] != a['started']-1:
                return False
            if c['kind']=='direction' and not a['lower_x'] < b['lower_x']:
                return False
            if c['kind']=='action' and not (b['lower_phase']&0x40 and a['lower_phase']==0x20):
                return False
            if c['boundary']=='after' and (c['neutral_same_callback']['lower_x']!=b['lower_x'] or c['neutral_same_callback']['lower_phase']!=b['lower_phase']):
                return False
        except (KeyError,TypeError):
            return False
    return True


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


def audio_expected_checks():
    # Independent frozen event epochs, not the native report's declared counts.
    path=ROOT/'tests/reference/audio/one-player-match/audio-associations.json'
    source=json.loads(path.read_text())
    updates=sorted({e['callback'] for e in source['timed_events'] if e.get('retained_parent_event')
                    and e.get('context')=='callback' and 11959<e.get('callback',0)<=13378})
    return [(ordinal,tone) for ordinal in updates for tone in range(3)]


def audio_expected_rows(name):
    recipe=json.loads((ROOT/f'tests/cases/{name}.json').read_text())
    source=json.loads((ROOT/f"tests/reference/audio/{recipe['source_case']}/audio-associations.json").read_text())
    events={}
    for event in source['timed_events']:
        ordinal=event.get('callback',0)
        if (event.get('retained_parent_event') and event.get('context')=='callback'
                and 0<ordinal<=max(recipe['completed_callbacks'])):
            events[ordinal]=event
    if recipe.get('comparison')=='mute':return [recipe['mute_update']]
    return sorted(n for n,e in events.items() if e['tones_after'][recipe['source_tone']]['attenuation']!=15)


def audio_proof(report,name):
    if (report.get('case')!=name or report.get('subject')!='maintained-native' or report.get('passed') is not True
            or report.get('first_difference') is not None
            or report.get('state_contract')!=MAINTAINED_STATE_CONTRACT
            or report.get('omitted_legacy_scratch_offsets')!=list(MAINTAINED_SCRATCH_OFFSETS)
            or any(d.get('offset') not in MAINTAINED_SCRATCH_OFFSETS for d in report.get('raw_state_differences',[]))):
        return False
    if name=='ct08-effect-classes':
        classes=['intro-a','intro-b','result-a','result-b','ready-cue','strike']
        emitted=report.get('emitted_classes',[]);checks=report.get('checks',[])
        return (report.get('initial_source_update')==11959 and report.get('final_source_update')==13381
            and report.get('observed_callbacks')==1422 and report.get('due_callbacks')==890
            and report.get('two_tick_countdowns')==530 and report.get('classes')==classes
            and len(report.get('interval_inventory',[]))==18
            and sorted(r.get('class') for r in emitted)==sorted(classes+['silence'])
            and all(r.get('expected_signal')==r.get('actual_signal') for r in emitted)
            and [(r.get('update'),r.get('tone')) for r in checks]==audio_expected_checks()
            and all(r.get('expected_volume')==r.get('actual_volume') and
                    (r.get('expected_period') is None or r['expected_period']==r.get('actual_period')) for r in checks))
    mutation=report.get('mutation',{});rows=report.get('observations',[])
    if (report.get('self_test') is not True or not mutation.get('detected_difference')
            or mutation.get('executable_sha256')==report.get('native_executable_sha256') or not rows
            or any(r.get('criterion_expected')!=r.get('criterion_actual') or r.get('first_difference') for r in rows)
            or [r.get('update') for r in rows]!=audio_expected_rows(name)):
        return False
    if name=='p2-first-serve-mute':
        return (report.get('emitted_waveform',{}).get('first_difference') is None
            and bool(report.get('emitted_waveform',{}).get('checks'))
            and bool(report.get('disconnected_waveform_mutation',{}).get('emitted_waveform',{}).get('first_difference')))
    return name in ('p2-first-serve-pitch','p2-first-serve-envelope')


def ordinary_audio_proof(report,executable_sha256):
    emitted=report.get('emitted_audio',[])
    quiet=next((r for r in report.get('audio_checkpoints',[]) if r.get('lifecycle')==7),{})
    return (ordinary_restart_proof(report,'one',executable_sha256) and report.get('audio_observed') is True
        and [(r.get('event'),r.get('expected_signal'),r.get('actual_signal')) for r in emitted]
            ==[('returned-title',False,False),('restart-intro',True,True)]
        and all(quiet.get('registers',{}).get(f'AUD{channel}VOL')==0 for channel in (0,1,3)))


def progress(fresh_since=None):
    evidence = {}
    for name in sorted(set(n for names in GATES.values() for n in names)):
        if name == 'ct05-r2-first-round':
            evidence[name] = bounded_round_status(report_path(name), fresh_since)
            continue
        subject = 'maintained-native-mutant' if name=='ct09-published-bank-control' else 'maintained' if name in REPLAY or name in CT05_REPLAY or name.startswith(('round-', 'deuce-')) or name in CT06_PHASES or name.endswith('-match') or name == 'status-timer-saturation-phase' else 'maintained-native'
        full = name == 'status-timer-saturation-phase' or name in CT06_PHASES or name in REPLAY or name in CT05_REPLAY or name in ('round-transition', 'one-player-match', 'two-player-match', 'deuce-sequence-phase')
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
    native['audio'] = ['game_audio_tick','game_audio_queue','game_audio_write_period','game_audio_write_level','game_audio_cue_complete']
    old = {'serve/contact': ['lower_player_state', 'upper_player_state'],
           'ball/launch': ['ball_flight_update', 'derive_launch_vector', 'triangular_root_step'],
           'movement': ['lower_player_motion_update', 'upper_player_movement'], 'AI': ['predict_ball_intercept', 'direction_ai'],
           'presentation': ['build_player_sprites', 'scoreboard_update', 'irq_vdp_tail', 'shadow_vram', 'copy_cpu_bytes_to_vram_b_count']}
    old['audio'] = ['audio_tick_adapter','paula_apply_psg_events','assign_sound_stream_4','psg_log','game_audio_import_capture']
    native['score/lifecycle']=['game_score_tick','game_round_poll','game_result_poll']
    old['score/lifecycle']=['score_gate','scoreboard_update']
    native['shared native state/order']=['game_active_tick','game_service_tail']
    old['shared native state/order']=['virtual_memory','legacy_active_tick','legacy_tail_tick']
    remaining = {}
    architecture = {'ordinary_build': build, 'subsystems': {}}
    for group in native:
        architecture['subsystems'][group] = {'integration': ('native entry points compiled; replaced translated entry points absent'
            if ordinary and all(n in symbols for n in native[group]) and not any(n in symbols for n in old[group])
            else 'unverified'), 'native_entry_points': [n for n in native[group] if n in symbols],
            'translated_entry_points': [n for n in old[group] if n in symbols]}
    for group, labels in remaining.items():
        architecture['subsystems'][group] = {'integration': 'temporary runtime dependencies remain' if ordinary and any(n in symbols for n in labels) else 'unverified',
                                             'compiled_dependencies': [n for n in labels if n in symbols]}
    package_path=ROOT/'build/amiga/ctennis-delivery/package-report.json'
    package_status=status(package_path,'maintained-native',fresh_since=fresh_since)
    package_report=json.loads(package_path.read_text()) if package_status['status']=='passed' else {}
    package_verified=(package_report.get('embedded_executable_verified') is True
        and package_report.get('reproducibility',{}).get('two_clean_builds') is True
        and package_report.get('reproducibility',{}).get('first_adf_sha256')==package_report.get('adf_sha256')
        and package_report.get('reproducibility',{}).get('second_adf_sha256')==package_report.get('adf_sha256')
        and ordinary and package_report.get('executable_sha256')==json.loads(build_path.read_text()).get('executable_sha256'))
    cold_report=json.loads(report_path('ct10-adf-one-cadence').read_text()) if evidence['ct10-adf-one-cadence']['status']=='passed' else {}
    cold_verified=(ordinary and bool(cold_report) and cadence_proof(cold_report,'one',json.loads(build_path.read_text()).get('executable_sha256'),True))
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
        if gate == 'CT-08':
            if not ordinary or not all(n in symbols for n in native['audio']) or any(n in symbols for n in old['audio']):
                verified=False;reasons.append('Ordinary native voices/direct Paula or runtime bridge retirement unverified')
            for name in names[:4]:
                if evidence[name]['status']=='passed' and not audio_proof(json.loads(report_path(name).read_text()),name):
                    verified=False;reasons.append(f'{name} complete finite audio acceptance missing')
            name='ct06-ordinary-one-restart'
            if not ordinary or evidence[name]['status']!='passed' or not ordinary_audio_proof(json.loads(report_path(name).read_text()),json.loads(build_path.read_text()).get('executable_sha256')):
                verified=False;reasons.append('Ordinary physical result/title/restart audio proof missing')
        if gate == 'CT-09':
            sha = json.loads(build_path.read_text()).get('executable_sha256') if ordinary else None
            for mode in ('one','two'):
                name=f'ct09-ordinary-{mode}-cadence'
                if (not ordinary or evidence[name]['status']!='passed'
                        or evidence[name].get('kind')!='ordinary-cadence'
                        or not cadence_proof(json.loads(report_path(name).read_text()),mode,sha)):
                    verified=False
                    reasons.append(f'Uninterrupted ordinary {mode} cadence/complete-play/memory receipt missing or incompatible')
            name='ct09-input-timing-edges'
            if (evidence[name]['status']!='passed' or evidence[name].get('kind')!='physical'
                    or evidence[name].get('startup')!='ordinary title'
                    or not timing_edge_proof(json.loads(report_path(name).read_text()),sha)):
                verified=False
                reasons.append('Four ordinary direction/action boundary edges missing or incompatible')
            name='ct09-published-bank-control'
            control=json.loads(report_path(name).read_text()) if evidence[name]['status']=='passed' else {}
            fault=control.get('detected_failure',{})
            if (not control.get('passed') or fault.get('field')!='published Copper bank'
                    or fault.get('generation',0)<200 or fault.get('expected_pointer')==fault.get('actual_pointer')
                    or control.get('normal_executable_sha256')!=sha):
                verified=False
                reasons.append('Actual delayed wrong-bank publication control missing or incompatible')
        if gate == 'CT-10':
            # User approved Copperline as the sufficient target on 2026-10-01.
            # Preserve exact-profile/full-play/loaded-byte/audio evidence; never
            # upgrade an older receipt when a build dependency changed.
            verified = bool(verified and ordinary and package_verified and cold_verified)
            reasons += [f'{name} required delivery guard is {evidence[name]["status"]}'
                        for name in names if evidence[name]['status'] != 'passed']
            for name in ['p1-moving-prefix', 'p1-upper-serve'] + [f'p1-status-{n}-lifecycle' for n in range(2,6)]:
                if evidence[name]['status'] != 'passed':
                    continue
                receipt = json.loads(report_path(name).read_text())
                recipe = json.loads((ROOT/f'tests/cases/{name}.json').read_text())
                proof = status_lifecycle_proof if name.startswith('p1-status-') else presentation_proof
                if not proof(receipt, recipe):
                    verified=False;reasons.append(f'{name} full declared pixel/status/fault extent missing')
            if not package_verified:reasons.append('Two clean identical native executable/ADF package receipts missing or incompatible')
            if not cold_verified:reasons.append('Cold disk native lifecycle/cadence/loaded-byte/allocation receipt missing or incompatible')
            if capabilities['CT-09']['acceptance']!='evidenced within stated scope':
                verified=False;reasons.append('Current both-mode ordinary cadence/replay/control acceptance missing')
            audio_name='ct06-ordinary-one-restart'
            if (evidence[audio_name]['status']!='passed' or not ordinary or not ordinary_audio_proof(
                    json.loads(report_path(audio_name).read_text()),json.loads(build_path.read_text()).get('executable_sha256'))):
                verified=False;reasons.append('Current ordinary Paula/emitted result/title/restart audio receipt missing')
        capabilities[gate] = {'capability': NAMES[gate], 'acceptance': 'evidenced within stated scope' if verified else 'unverified',
                              'evidence': names, 'limitations': reasons}
    runtime_target = all(evidence[n]['status'] == 'passed' and evidence[n].get('startup') == 'ordinary title'
                         for n in GATES['CT-02'])
    supporting = {'captured_live_serve': status(
        ROOT/'build/amiga/gameplay-integration/serve-report.json', 'maintained-native',
        fresh_since=fresh_since)}
    ordinary_complete = capabilities['CT-09']['acceptance']=='evidenced within stated scope'
    peak = 'unverified'
    if ordinary_complete:
        peak = {'bytes': max(json.loads(report_path(f'ct09-ordinary-{m}-cadence').read_text())['memory']['peak_chip_bytes'] for m in ('one','two')),
                'scope': 'CIA timer start through restarted flight in both modes; resident OS/allocated stack included; pre-timer and cold ADF boot peak unverified'}
    return {'behavior': {'capabilities': capabilities, 'evidence': evidence, 'supporting_evidence': supporting},
            'runtime_dependencies': architecture,
            'delivery': {'target': TARGET, 'ordinary_target_execution': 'evidenced in uninterrupted ordinary runs' if ordinary_complete else 'evidenced local cold-disk lifecycle' if cold_verified else 'evidenced in mode/control checks' if runtime_target else 'unverified',
                         'peak_chip_ram': peak, 'cadence_and_full_ordinary_play': 'evidenced in two native-entropy runs' if ordinary_complete else 'unverified',
                         'native_ADF_package': {'status':'evidenced' if package_verified else 'unverified','evidence':package_status},
                         'cold_ADF_boot': 'evidenced local Copperline full lifecycle' if cold_verified else 'unverified',
                         'cold_boot_chip_ram': {'bytes':cold_report['memory']['cold_boot_peak'],'scope':cold_report['memory']['cold_boot_peak_scope']} if cold_verified else 'unverified',
                         'accepted_validation_target':'Copperline (user approved 2026-10-01 20:00 UTC)',
                         'independent_emulator_or_hardware': 'not performed; not required by user-approved scope',
                         'independent_code_runtime_review':'pending external exact-head review',
                         'pre_Exec_pool_peak':'unmeasured; scoped initialized-pool allocation reported separately'},
            'scope': 'Retained reports checked against current dependencies; integration symbols are not runtime acceptance. No percentages or file-size RAM estimate.'}


def interface_positions_proof(report, exchanged=False):
    try:
        values={name:bytes.fromhex(report['observations'][name])
                for name in ('before','after','reverse','waiting','flight')}
        if any(len(v)!=256 for v in values.values()):return False
        before,after,reverse=(values[n] for n in ('before','after','reverse'))
        p1,p2=(0x46,0x4a) if exchanged else (0x4a,0x46)
        if not after[p1]<before[p1] or not reverse[p1]>after[p1]:return False
        two=exchanged or report.get('mode')=='two'
        if two and (not after[p2]>before[p2] or not reverse[p2]<after[p2]):return False
        if bool(before[0x3d]&0x80)!=two:return False
        return not bool(values['waiting'][0x38] and values['waiting'][0x66]) and bool(values['flight'][0x38] and values['flight'][0x66])
    except (KeyError,TypeError,ValueError):return False


def interface_progress(flavor, fresh_since=None):
    """Finite follow-on view. Never cross-credit another interface's receipts."""
    root=ROOT/'build/amiga/interfaces'/flavor
    names=['interface-one-enhanced','interface-two-enhanced','interface-exchanged-enhanced'] if flavor=='enhanced' else []
    names += [f'{case}-{flavor}' for case in ('p1-moving-prefix','p1-upper-serve','p1-score-status-prefix')]
    if flavor=='enhanced':
        names += [f'p1-status-{n}-lifecycle-enhanced' for n in range(2,6)]
        names += ['ct10-adf-one-cadence-enhanced-keyboard','ct09-ordinary-two-cadence-enhanced-keyboard',
                  'ct09-published-bank-control-enhanced']
    else:names += ['ct09-ordinary-one-cadence-original']
    reports={name:status(ROOT/f'build/tests/{name}-report.json',
                         'maintained-native-mutant' if 'bank-control' in name else 'maintained-native',
                         fresh_since=fresh_since,interface_flavor=flavor) for name in names}
    build_status=status(root/'build-report.json','maintained-native',fresh_since=fresh_since,interface_flavor=flavor)
    package_status=status(root/'delivery/package-report.json','maintained-native',fresh_since=fresh_since,interface_flavor=flavor)
    executable=json.loads((root/'build-report.json').read_text()).get('executable_sha256') if build_status['status']=='passed' else None
    for name,value in reports.items():
        if value['status']!='passed':continue
        report=json.loads((ROOT/f'build/tests/{name}-report.json').read_text())
        valid=True
        if name.startswith('p1-'):
            case=name.removesuffix('-'+flavor)
            recipe=json.loads((ROOT/f'tests/cases/{case}.json').read_text())
            valid=status_lifecycle_proof(report,recipe) if '-lifecycle' in case else presentation_proof(report,recipe)
            if case=='p1-upper-serve':
                mutant=report.get('hardware_mutation') or {}
                valid=valid and (mutant.get('detected_at_all_checkpoints') is True
                    and mutant.get('executable_sha256')!=report.get('executable_sha256')
                    and [r.get('requested_callback') for r in mutant.get('checks',[])]==recipe['completed_callbacks']
                    and all(r.get('first_difference') for r in mutant.get('checks',[])))
        elif 'cadence' in name:
            mode='two' if '-two-' in name else 'one'
            valid=cadence_proof(report,mode,executable,name.startswith('ct10-'),flavor,name.endswith('-keyboard'))
        elif 'bank-control' in name:
            fault=report.get('detected_failure',{})
            valid=(fault.get('field')=='published Copper bank' and fault.get('generation',0)>=200
                   and fault.get('expected_pointer')!=fault.get('actual_pointer')
                   and report.get('normal_executable_sha256')==executable)
            valid=valid and (report.get('subject')=='maintained-native-mutant' and report.get('passed') is True
                   and report.get('executable_sha256')!=executable
                   and report.get('presentation',{}).get('actual_pointer_checked') is True
                   and report.get('presentation',{}).get('latest_prepared_completed_epoch') is False)
        elif name.startswith('interface-'):
            checks=report.get('checks',[])
            labels={r.get('label') for r in checks}
            if name=='interface-exchanged-enhanced':
                valid=(interface_positions_proof(report,True) and report.get('startup')=='captured exchanged-end phase'
                       and report.get('initial_source_callback')==2672
                       and {'exchanged logical owners','P1 upper reverses','P2 lower reverses',
                            'P2 keypad blue launches its own serve'}<=labels
                       and all(r.get('actual')==r.get('expected') for r in checks))
                if not valid:reports[name]=dict(value,status='failed',reason='Local exchanged keyboard ownership missing')
                continue
            valid=(interface_positions_proof(report) and report.get('mode')==name.split('-')[1]
                   and report.get('startup')=='ordinary title' and report.get('executable_sha256')==executable
                   and {'intended title raster','accepted original mode label','held selection accepted once','P1 reverses',
                        'all six keypad aliases','P1 keyboard blue launches serve',
                        'legacy alias keeps selection held','keyboard release retains joystick action',
                        'opposing horizontal packet','opposing vertical packet'}<=labels
                   and all(r.get('actual')==r.get('expected') for r in checks))
        if not valid:reports[name]=dict(value,status='failed',reason='Declared interface acceptance extent not established')
    package=json.loads((root/'delivery/package-report.json').read_text()) if package_status['status']=='passed' else {}
    reproducible=(package.get('executable_sha256')==executable and package.get('embedded_executable_verified') is True
                  and package.get('reproducibility',{}).get('two_clean_builds') is True
                  and package.get('reproducibility',{}).get('first_adf_sha256')==package.get('adf_sha256')
                  and package.get('reproducibility',{}).get('second_adf_sha256')==package.get('adf_sha256'))
    ready=build_status['status']=='passed' and reproducible and all(r['status']=='passed' for r in reports.values())
    return {'interface_flavor':flavor,'acceptance':'evidenced within stated scope' if ready else 'unverified',
            'build':build_status,'package':package_status,'package_reproducibility_verified':reproducible,
            'reports':reports,'scope':'Interface follow-on only; immutable original oracle, shared gameplay and independent review remain separately scoped',
            'limitations':[] if ready else ['Required interface-specific receipts/extent/reproducibility missing, stale or failed']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--interface',choices=('original','enhanced'),default='enhanced')
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
        result['interface_follow_on']=interface_progress(args.interface,args.fresh_since)
        report_paths = {report_path(n) for names in GATES.values() for n in names}
        report_paths.update(ROOT/'build/amiga/gameplay-integration'/n
                            for n in ('build-report.json', 'serve-report.json'))
        result['view_provenance'] = {
            'generated_utc': now(), 'fresh_since': args.fresh_since,
            'sources': snapshot(python_inputs(Path(__file__).resolve())),
            'reports': snapshot(report_paths),
            'interface_reports':snapshot([ROOT/f'build/tests/{n}-report.json' for n in result['interface_follow_on']['reports']]
                +[ROOT/f'build/amiga/interfaces/{args.interface}/build-report.json',
                  ROOT/f'build/amiga/interfaces/{args.interface}/delivery/package-report.json']),
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
