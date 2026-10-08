"""Read native receipts. Keep missing, stale and incomplete results open."""
import argparse
import json
from pathlib import Path
from native_tools import ROOT
from native_evidence import status, atomic_json
from native_clock import clock_contract

RECEIPTS = {
    'package': 'amiga/interfaces/enhanced/delivery/package-report.json',
    'menu-cold': 'tests/enhanced-menu-cold/report.json',
    'inputs': 'tests/native-inputs/report.json',
    'video-clock': 'tests/native-video-clock/report.json',
    'sprite-dma-pal': 'tests/native-sprite-dma-pal-report.json',
    'sprite-dma-ntsc': 'tests/native-sprite-dma-ntsc-report.json',
    'scoreboard': 'tests/native-scoreboard/report.json',
    'setup-proposal': 'tests/native-setup/report.json',
    'demo': 'tests/demo-full-repeat/report.json',
    'takeover': 'tests/demo-mid-takeover/report.json',
    'attract-cycles': 'tests/attract-two-cycles/report.json',
    'feedback-one': 'tests/enhanced-feedback-one/report.json',
    'feedback-two': 'tests/enhanced-feedback-two/report.json',
    'ordinary-one-cold': 'tests/ct10-adf-one-cadence-enhanced-report.json',
    'ordinary-two': 'tests/ct09-ordinary-two-cadence-enhanced-report.json',
    'bank-control': 'tests/ct09-published-bank-control-enhanced-report.json',
    'restart-audio-early': 'tests/ct06-ordinary-one-early-release-enhanced-report.json',
    **{name: f'tests/native-contracts/{name}/report.json' for name in (
        'deuce','advantage','return-deuce','advantage-game','match-award',
        'status-2','status-3','status-4','status-5','audio-hit')},
}


def acceptance(name, report):
    if name == 'video-clock':
        return ([c.get('standard') for c in report.get('cases',[])]==['PAL','NTSC']
                and all(c.get('completed_updates',0)>=150 for c in report['cases']))
    if name.startswith('sprite-dma-'):
        cases=report.get('cases',[])
        return (len(cases)==(15 if name.endswith('pal') else 6)
                and all(c.get('passed') and c.get('full_fields',0)>=23 for c in cases)
                and len(report.get('compiled_controls',[]))==(4 if name.endswith('pal') else 1))
    if name == 'scoreboard':
        return (len(report.get('cases', [])) == 28
                and bool(report.get('compiled_fault_controls'))
                and all(len({p['bank'] for p in row.get('plane_pointers', [])}) == 3
                        and len(row.get('raster', [])) == 2
                        for row in report.get('cases', [])))
    if name == 'package':
        return report.get('embedded_executable_verified') is True and report.get('reproducibility', {}).get('two_clean_builds') is True
    if name == 'demo':
        return report.get('verified_input_ticks') == 10958 and report.get('missed_publications') == 0
    if name == 'attract-cycles':
        windows=report.get('windows',[])
        captures=[Path(p).name for p in report.get('captures',[])]
        expected={f'cycle-{cycle}-title-{suffix}.png' for cycle in (1,2)
                  for suffix in ('4','first-complete','600','1200','1790')}
        return (len(windows)==2 and len(report.get('entries',[]))==3
                and len(captures)==len(expected) and set(captures)==expected
                and all(w.get('stable') is True and w.get('unexpected_title_writes')==0
                        and w.get('publications',0)>0 and w.get('next_entry')
                        and w.get('first_complete_title_capture',{}).get('reply')
                        and len(w.get('title_frame_digests',[]))>=1400 for w in windows))
    if name == 'takeover':
        return report.get('verified_input_ticks') == 5480 and report.get('takeover') is True and report.get('missed_publications') == 0
    if name == 'menu-cold':
        return len(report.get('checks', [])) >= 69 and all(r.get('matched') is True for r in report.get('loaded_hunks', [])) and bool(report.get('loaded_hunks'))
    if name.startswith('feedback-'):
        return len(report.get('awards', [])) == 2 and report.get('observed_missed_publication_deadlines') == 0 and any('raster matches' in row['label'] for row in report.get('checks', []))
    if name.startswith('ordinary-'):
        required = ('initial_title','first_selection','first_play','first_flight','point','game','pause','resume','result','returned_title','restart_title_ready','restart_selection','restart_play','held_blocked','fresh_action','restarted_flight','finished')
        return (all(k in report.get('checkpoints', {}) for k in required)
            and report.get('uninterrupted') is True and report.get('callback_breakpoints') == 0
            and report.get('entropy') == 'ordinary native timer' and report.get('observed_callbacks',0) > 0
            and report.get('loaded_executable_verified') is True
            and report.get('presentation', {}).get('actual_pointer_checked') is True
            and report.get('presentation', {}).get('latest_prepared_completed_epoch') is True
            and report.get('cadence', {}).get('clock_contract') == clock_contract())
    if name == 'bank-control':
        return report.get('detected_failure', {}).get('field') == 'published Copper bank'
    if name == 'restart-audio-early':
        return report.get('early_release_verified') is True and report.get('audio_observed') is True and len(report.get('emitted_audio', [])) == 3 and bool(report.get('compiled_fault_controls'))
    if name == 'setup-proposal':
        return (report.get('raw_all_callback_deadline_passed') is True
                and bool(report.get('elapsed_accounting_samples'))
                and [c.get('name') for c in report.get('compiled_fault_controls', [])] == ['lost-wrap','ui-overrun'])
    if name == 'inputs':
        return len(report.get('checks', [])) >= 11
    if name in ('deuce','status-2','audio-hit') and not report.get('compiled_fault_controls'):
        return False
    if name.startswith('status-') and (len(report.get('status_raster', [])) != 2 or not all(row.get('matched') is True and row.get('published_scene', {}).get('completed') is True for row in report.get('status_raster', []))):
        return False
    return report.get('case') == name and bool(report.get('observations'))


def summary(fresh_since=None):
    rows = {}
    for name, relative in RECEIPTS.items():
        path = ROOT / 'build' / relative
        row = status(path, subject='maintained-native-mutant' if name=='bank-control' else 'maintained-native',
                     interface_flavor='enhanced', fresh_since=fresh_since)
        if row['status'] == 'passed' and not acceptance(name, json.loads(path.read_text())):
            row = dict(row, status='failed', reason='Required native extent/contract is absent')
        rows[name] = row
    return {'passed': all(row['status']=='passed' for row in rows.values()), 'receipts': rows,
            'scope': 'Finite native gate only; current risks and local fixtures remain separately labeled'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fresh-since')
    result = summary(parser.parse_args().fresh_since)
    atomic_json(ROOT / 'build/progress-report.json', result)
    print(json.dumps(result, indent=2))
