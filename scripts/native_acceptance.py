"""Finite CT11 native gate; sequential commands, exact-head receipt and no originals."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from native_tools import ROOT
from native_evidence import atomic_json
from progress import summary


def main():
    directory = ROOT / 'build/acceptance'
    directory.mkdir(parents=True, exist_ok=True)
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    head = subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip()
    if subprocess.run(['git','diff','--quiet','HEAD'], cwd=ROOT).returncode:
        raise ValueError('Run the final gate at a committed clean head')
    forbidden = ['tests/reference','build/reference','build/translation','analysis','tooling','roms']
    if any((ROOT / name).exists() for name in forbidden):
        raise ValueError('Original inputs/obsolete directories present in gate checkout')
    commands = [
        ['-m','unittest','discover','-s','tests/unit','-q'],
        ['scripts/native_assets.py'],
        ['scripts/build_native_adf.py','--self-test'],
        ['scripts/run_enhanced_menu_tests.py','--adf'],
        ['scripts/run_native_inputs.py'],
        ['scripts/run_native_scoreboard_tests.py','--self-test'],
        *[['scripts/run_native_contracts.py','--case='+case,*(['--self-test'] if case in ('deuce','status-2','status-6','audio-hit') else [])]
          for case in ('deuce','advantage','return-deuce','advantage-game','match-award','status-2','status-3','status-4','status-5','status-6','audio-hit')],
        ['scripts/run_celebration_tests.py','--winner=blue','--self-test'],
        ['scripts/run_celebration_tests.py','--winner=red'],
        ['scripts/run_celebration_tests.py','--winner=blue','--exchanged'],
        ['scripts/run_celebration_tests.py','--winner=red','--exchanged'],
        ['scripts/run_demo_match_tests.py'],
        ['scripts/run_demo_match_tests.py','--takeover'],
        ['scripts/run_attract_cycle_tests.py'],
        ['scripts/run_enhanced_feedback_tests.py','--mode=one'],
        ['scripts/run_enhanced_feedback_tests.py','--mode=two'],
        ['scripts/run_ordinary_round_tests.py','--mode=one','--match','--cadence','--adf'],
        ['scripts/run_ordinary_round_tests.py','--mode=two','--match','--cadence'],
        ['scripts/run_ordinary_round_tests.py','--mode=one','--bank-control'],
        ['scripts/run_ordinary_round_tests.py','--mode=one','--match','--early-release','--audio','--self-test'],
        ['scripts/run_native_setup_tests.py','--self-test'],
        ['scripts/build_native_adf.py','--self-test'],
    ]
    report = {'commit': head, 'started_utc': started, 'state': 'incomplete', 'passed': False,
              'commands': [], 'original_inputs_absent_in_checkout': True}
    path = directory / 'report.json'
    atomic_json(path, report)
    for i, args in enumerate(commands):
        command = [sys.executable, *args]
        name = f'{i:02d}-{Path(args[0]).stem}'
        print('RUN', ' '.join(command), flush=True)
        begin = dt.datetime.now(dt.timezone.utc).isoformat()
        with (directory / (name+'.log')).open('w') as log:
            result = subprocess.run(command, cwd=ROOT, env=dict(os.environ,RUST_LOG='info'), stdout=log, stderr=subprocess.STDOUT)
        report['commands'].append({'command': command,'started_utc':begin,'completed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
                                   'exit_code':result.returncode,'log':str((directory/(name+'.log')).relative_to(ROOT))})
        atomic_json(path, report)
        if result.returncode:
            report.update(state='failed', first_failure=report['commands'][-1])
            atomic_json(path, report)
            print('FAILED; see',report['commands'][-1]['log'],flush=True)
            return result.returncode
        print('PASS', name, flush=True)
    status = summary(fresh_since=started)
    unchanged = subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip() == head and subprocess.run(['git','diff','--quiet','HEAD'], cwd=ROOT).returncode == 0
    report.update(state='complete',completed_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                  passed=status['passed'] and unchanged, native_status=status, head_unchanged=unchanged,
                  artifacts={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                             for p in (ROOT/'build/amiga/interfaces/enhanced/baseline-rally',
                                       ROOT/'build/amiga/interfaces/enhanced/delivery/baseline-rally.adf')})
    atomic_json(path, report)
    print(json.dumps({'passed':report['passed'],'commit':head,'artifacts':report['artifacts'],'report':str(path)}),flush=True)
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
