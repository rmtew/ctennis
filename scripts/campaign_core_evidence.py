"""CPU-only receipts for retained native captures and actual shared-core proofs.

This never launches an emulator or rebuilds a product. Native capture provenance
must still be compatible; a stale capture is a blocker, not a silently upgraded
pass. Fresh CPU replay is reported separately from the reused native observation.
"""
import argparse
from importlib.metadata import distribution, version
import json
import os
from pathlib import Path
import sys

from native_evidence import (ReportRun, changed, compile_manifest, digest,
                             python_inputs, snapshot, status)
from native_tools import ROOT

PROOFS = ('pal-demo', 'ntsc-two-restart', 'fixture-deuce', 'fixture-advantage',
          'fixture-return-deuce', 'fixture-advantage-game', 'fixture-match-award',
          'entropy', 'shared-bytes')


def core_cases():
    from acceptance_cases import Case
    return [Case('core-'+name, ('scripts/campaign_core_evidence.py', '--proof='+name),
                 'tests/campaign-core-'+name+'/report.json', category='core-proof')
            for name in PROOFS]


def validate(case, root=ROOT):
    path = Path(root)/'build'/case.report
    try:
        report = json.loads(path.read_text())
    except (OSError, ValueError):
        proof = case.id.removeprefix('core-')
        if proof not in ('entropy', 'shared-bytes'):
            try:
                capture_inputs(proof)
            except (OSError, ValueError, KeyError, TypeError) as error:
                return None, 'CPU-only proof blocked by retained native capture: '+str(error)
        return None, 'Missing CPU-proof receipt; CPU-only execution required'
    row = status(path)
    if row['status'] != 'passed':
        return None, 'Latest CPU-proof receipt '+row['status']+': '+str(row)
    meta = report['evidence']
    command = meta.get('command') or ['']
    if (report.get('proof') != case.id.removeprefix('core-') or
            meta.get('environment', {}).get('PYTHONPATH') != os.environ.get('PYTHONPATH') or
            command[1:] != list(case.args[1:]) or
            Path(command[0]).name != Path(case.args[0]).name or
            report.get('execution') != 'actual-68000-cpu-only' or
            not report.get('result')):
        return None, 'CPU-proof identity or extent absent'
    return {'path': str(path), 'sha256': digest(path), 'original_evidence': meta,
            'artifacts': meta['files'], 'classification': 'reused'}, 'Compatible CPU-proof receipt'


def capture_inputs(proof):
    path = ROOT/'build/tests'/('shared-match-core-'+proof)/'report.json'
    report = json.loads(path.read_text())
    if report.get('passed') is not True or not report.get('files') or not report.get('sha256'):
        raise ValueError('Native capture incomplete: '+str(path))
    differences = changed(report['files']) + changed(report['sha256'])
    if differences:
        raise ValueError('Native capture inputs changed; review/recapture required: '+str(sorted(set(differences))))
    rows = report.get('rows', [])
    if not rows or report['summary']['operations'] != len(rows):
        raise ValueError('Incomplete captured operation stream')
    if any(row['index'] != index or len(bytes.fromhex(row['state'])) != 318
           for index, row in enumerate(rows)):
        raise ValueError('Noncontiguous or incompatible canonical state stream')
    expected_video = 'NTSC' if proof == 'ntsc-two-restart' else 'PAL'
    if report['target'] != dict(video=expected_video, cpu='68000', chipset='OCS',
                               chip_kib=512, slow_kib=0, fast_kib=0):
        raise ValueError('Native capture target differs')
    if proof == 'pal-demo':
        if (report.get('demo') is not True or report.get('seconds', 0) < 300 or
                report['summary'].get('written_bytes') != 318):
            raise ValueError('Complete PAL attract/state-write extent absent')
    elif proof == 'ntsc-two-restart':
        if (report.get('two') is not True or report.get('restart') is not True or
                report.get('seconds', 0) < 8 or report['summary'].get('written_bytes') != 318):
            raise ValueError('NTSC two-player restart extent absent')
    elif report.get('case') != proof.removeprefix('fixture-') or report.get('seconds', 0) < 8:
        raise ValueError('Scoring fixture identity/extent absent')
    paths = {ROOT/p for p in report['files']} | {ROOT/p for p in report['sha256']} | {path}
    return path, report, paths


def replay_capture(proof, report, executable):
    from build_match_core import load_image
    from match_core_cpu import Core
    from run_shared_match_core import READONLY, replay_and_negatives
    rows = report['rows']
    image, symbols = load_image(executable)
    if proof.startswith('fixture-'):
        from run_native_contracts import SCORING
        _, _, _, points, games = SCORING[proof.removeprefix('fixture-')]
        first = next(row for row in rows if row['operation'] == 'game_tick_dispatch')
        state = bytes.fromhex(first['state'])
        if list(state[66:68]) != points or list(state[68:70]) != games:
            raise ValueError('Retained independent scoring contract differs')
        for poison, base in ((0xa5, 0x10000), (0x5a, 0x10000), (0x96, 0x30000)):
            image, symbols = load_image(executable, base=base)
            with Core(image, symbols, initial=bytes.fromhex(report['initial']),
                      poison=poison, readonly=READONLY) as cpu:
                for row in rows:
                    cpu.clear_events()
                    cpu.call_logical(row['operation'], row['arguments'])
                    assert cpu.state().hex() == row['state'], ('fixture state', row['index'])
                    assert cpu.events == row['events'], ('fixture events', row['index'])
                cpu.audit_reads()
        return {'operations': len(rows), 'complete_state_bytes': 318, 'poisons': [165, 90, 150],
                'relocation_operations': len(rows), 'retained_points': points, 'retained_games': games}
    negatives = replay_and_negatives(image, symbols, rows, executable)
    polls = 0
    if proof == 'pal-demo':
        with Core(image, symbols, poison=0x69, readonly=READONLY) as cpu:
            for row in rows:
                cpu.clear_events()
                cpu.call_logical(row['operation'], row['arguments'])
                assert cpu.state().hex() == row['state'], ('poll replay state', row['index'])
                assert cpu.events == row['events'], ('poll replay events', row['index'])
                if row['operation'] == 'game_round_poll':
                    first = cpu.state()
                    for _ in range(2):
                        cpu.clear_events()
                        cpu.call_logical('game_round_poll', [])
                        assert cpu.state() == first and cpu.events == [], ('extra poll', row['index'])
                    polls += 1
            cpu.audit_reads()
    return {'operations': len(rows), 'complete_state_bytes': 318, 'poisons': [165, 90, 150],
            'relocation_operations': len(rows), 'negative_controls': negatives,
            'extra_poll_boundaries': polls, 'extra_polls_per_boundary': 2 if polls else 0}


def run(proof):
    output = ROOT/'build/tests'/('campaign-core-'+proof)/'report.json'
    transaction = ReportRun([output], 'shared-core-cpu', proof, 'isolated CPU; reused native capture')
    try:
        import machine68k
        if version('machine68k') != '0.4.1':
            raise ValueError('Use pinned machine68k 0.4.1')
        native = ROOT/'build/amiga/interfaces/enhanced/baseline-rally'
        standalone = ROOT/'build/standalone/match-core'
        paths = python_inputs(Path(__file__)) | {Path(sys.executable), Path(machine68k.__file__)}
        paths.update(Path(distribution('machine68k').locate_file(p))
                     for p in distribution('machine68k').files or []
                     if str(p).endswith(('.so', '.py', '/METADATA')))
        compiled = [compile_manifest(native, native.parent/'native.lst'),
                    compile_manifest(standalone, standalone.parent/'match-core.lst')]
        for item in compiled:
            paths.update(ROOT/p for p in item['files'])
            paths.add(ROOT/item['executable'])
        capture = None
        if proof not in ('entropy', 'shared-bytes'):
            capture_path, capture, capture_paths = capture_inputs(proof)
            paths.update(capture_paths)
        transaction.meta['files'] = snapshot(paths)
        transaction.meta['environment']['PYTHONPATH'] = os.environ.get('PYTHONPATH')
        transaction.meta['tools'] = {'python': {'version': sys.version, 'path': str(Path(sys.executable))},
                                     'machine68k': {'version': version('machine68k'), 'path': machine68k.__file__}}
        if proof == 'entropy':
            from check_core_entropy import check
            result = {'algorithm': 'galois16-b400-v2', 'images': {
                str(path.relative_to(ROOT)): check(path) for path in (native, standalone)}}
        elif proof == 'shared-bytes':
            from check_shared_core_bytes import run as compare
            result = compare()
        else:
            result = replay_capture(proof, capture, standalone)
        report = {'passed': True, 'proof': proof, 'execution': 'actual-68000-cpu-only',
                  'executable_sha256': digest(standalone), 'result': result,
                  'native_observation': None if capture is None else {
                      'classification': 'reused', 'report': str(capture_path),
                      'sha256': digest(capture_path), 'original_commit': capture.get('commit'),
                      'target': capture['target'], 'seconds': capture['seconds']},
                  'scope': 'Fresh isolated actual CPU proofs; retained native capture, no new emulator run or contended deadline claim'}
        transaction.finalize(output, report, compiled=compiled)
        assert status(output)['status'] == 'passed', status(output)
        print(json.dumps({'passed': True, 'proof': proof, 'report': str(output)}), flush=True)
        return 0
    except BaseException as error:
        transaction.abort(error)
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--proof', choices=PROOFS, required=True)
    raise SystemExit(run(parser.parse_args().proof))
