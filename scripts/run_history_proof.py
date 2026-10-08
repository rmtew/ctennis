"""Fresh actual 68000 history proof; execute only through native_acceptance.py."""
import json
import os

from build_match_core import build as build_core, load_image
from build_native_game import build
from history_proof import exercise, attach, seek, logical_api, pending_eviction
from match_core_cpu import Core, cpu_tool_inputs
from run_shared_match_core import READONLY
from native_evidence import ReportRun, compile_manifest, digest, inputs_for, snapshot, status, atomic_json
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
        paths,tools = inputs_for('build', 'scripts/run_history_proof.py')
        cpu_paths,tools['machine68k'] = cpu_tool_inputs()
        transaction.meta.update(files=snapshot(paths|cpu_paths),tools=tools)
        transaction.meta.update(target_role='legacy-validator-reference',actual_execution='actual-68000-cpu-only',
            target_scope='evidence.target is a legacy validation reference; this proof executes an isolated 68000 CPU with no actual display or emulator target.')
        transaction.meta['environment']['PYTHONPATH'] = os.environ.get('PYTHONPATH')
        _,native = build()
        standalone,_ = build_core()
        _,symbols = load_image(standalone)
        capacity = (symbols['game_history_checkpoints']-symbols['game_history_buffer'])//14
        proofs = {'empty':empty(standalone)}
        for name,executable,options in (
                ('long',standalone,dict(ticks=3*capacity//4)),
                ('cursor-wrap',standalone,dict(ticks=capacity//4+16,wrap=True,poison=0x5a)),
                ('relocated',standalone,dict(ticks=capacity//4+16,base=0x30000,poison=0x96)),
                ('native-sinks',native,dict(ticks=capacity//4+16,native_guards=True))):
            print('Running history proof',name,flush=True)
            proofs[name] = dict(passed=True,**exercise(executable,**options))
        print('Running history proof logical-api',flush=True)
        proofs['logical-api'] = dict(passed=True,**logical_api(standalone))
        print('Running history proof pending-eviction',flush=True)
        proofs['pending-eviction'] = dict(passed=True,**pending_eviction(standalone))
        assert len({proofs[name]['record_arguments_sha256'] for name in ('cursor-wrap','relocated','native-sinks')})==1, 'Omitted words depend on register poison/relocation'
        assert proofs['long']['tick_wraps'] > 0
        assert proofs['long']['terminal_outcome_operations'] > 0
        assert proofs['long']['operations'] > 3*capacity
        assert all(proofs['long']['completed_episode_kinds'].get(kind,0)>0 for kind in (1,2)), 'Actual hit/miss episodes absent'
        assert proofs['cursor-wrap']['latest']>>32 == 1
        report = {'passed':True,'execution':'actual-68000-cpu-only',
                  'executable_sha256':digest(standalone),
                  'history_validation':{'passed':True,'proofs':proofs},
                  'scope':'Fresh actual CPU state/output/store proofs and emitted native replay sinks; no contended seek deadline claim. evidence.target is a legacy validator reference, not an execution target.'}
        # Keep completed computation if receipt validation fails afterward.
        # This diagnostic is never a passing acceptance receipt by itself.
        atomic_json(path.parent/('proof-results-'+transaction.meta['run_id']+'-unvalidated.json'),dict(report,
            receipt_validated=False,receipt_run_id=transaction.meta['run_id']))
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
