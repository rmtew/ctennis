"""Fresh actual 68000 history proof; execute only through native_acceptance.py."""
import json
import os
from pathlib import Path
import sys
from importlib.metadata import distribution, version

from build_match_core import build as build_core, load_image
from build_native_game import build
from history_proof import exercise, attach, seek, logical_api, pending_eviction
from match_core_cpu import Core
from run_shared_match_core import READONLY
from native_evidence import ReportRun, compile_manifest, digest, python_inputs, snapshot, status
from native_tools import ROOT


def empty(executable):
    image,symbols = load_image(executable)
    with Core(image,symbols,readonly=READONLY) as cpu:
        cpu.call_logical('game_core_init',[])
        initial = cpu.state()
        attach(cpu)
        cpu.call('game_history_freeze')
        seek(cpu,0)
        assert cpu.state()==initial and cpu.events==[]
        cpu.call('game_history_resume_latest')
        assert cpu.state()==initial
        cpu.audit_reads()
    return {'passed':True,'operations':0,'boundaries_checked':1}


def run():
    path = ROOT/'build/tests/history-cpu/report.json'
    transaction = ReportRun([path],'history-cpu','maintained-native','actual CPU, no emulator')
    try:
        import machine68k
        if version('machine68k') != '0.4.1':
            raise ValueError('Use pinned machine68k 0.4.1')
        _,native = build()
        standalone,_ = build_core()
        paths = python_inputs(Path(__file__)) | {Path(sys.executable),Path(machine68k.__file__)}
        paths.update(Path(distribution('machine68k').locate_file(p))
                     for p in distribution('machine68k').files or []
                     if str(p).endswith(('.so','.py','/METADATA')))
        transaction.meta['files'] = snapshot(paths)
        transaction.meta['environment']['PYTHONPATH'] = os.environ.get('PYTHONPATH')
        proofs = {'empty':empty(standalone)}
        for name,executable,options in (
                ('long',standalone,dict(ticks=1536)),
                ('cursor-wrap',standalone,dict(ticks=272,wrap=True,poison=0x5a)),
                ('relocated',standalone,dict(ticks=272,base=0x30000,poison=0x96)),
                ('native-sinks',native,dict(ticks=272,native_guards=True))):
            print('Running history proof',name,flush=True)
            proofs[name] = dict(passed=True,**exercise(executable,**options))
        print('Running history proof logical-api',flush=True)
        proofs['logical-api'] = dict(passed=True,**logical_api(standalone))
        print('Running history proof pending-eviction',flush=True)
        proofs['pending-eviction'] = dict(passed=True,**pending_eviction(standalone))
        assert len({proofs[name]['record_arguments_sha256'] for name in ('cursor-wrap','relocated','native-sinks')})==1, 'Omitted words depend on register poison/relocation'
        assert proofs['long']['tick_wraps'] > 0
        assert proofs['long']['operations'] > 6*1024
        assert all(proofs['long']['completed_episode_kinds'].get(kind,0)>0 for kind in (1,2)), 'Actual hit/miss episodes absent'
        assert proofs['cursor-wrap']['latest']>>32 == 1
        report = {'passed':True,'execution':'actual-68000-cpu-only',
                  'executable_sha256':digest(standalone),
                  'history_validation':{'passed':True,'proofs':proofs},
                  'scope':'Fresh actual CPU state/output/store proofs and emitted native replay sinks; no contended seek deadline claim'}
        transaction.finalize(path,report,compiled=[
            compile_manifest(native,native.parent/'native.lst'),
            compile_manifest(standalone,standalone.parent/'match-core.lst')])
        assert status(path)['status']=='passed',status(path)
        print(json.dumps({'passed':True,'report':str(path),'proofs':proofs}),flush=True)
    except BaseException as error:
        transaction.abort(error)
        raise


if __name__=='__main__':
    run()
