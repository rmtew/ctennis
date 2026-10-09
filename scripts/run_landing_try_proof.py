"""Manifest-bound finite proof of the actual bounded endpoint helper."""
import hashlib
import json
import os

from build_match_core import build, load_image
from build_native_game import build as build_native
from check_shared_core_bytes import normalized, run as shared_bytes
from landing_try_proof import proof
from match_core_cpu import cpu_tool_inputs
from native_evidence import ReportRun, compile_manifest, digest, inputs_for, snapshot, status
from native_tools import ROOT


def main():
    output = ROOT/'build/tests/landing-try-cpu/report.json'
    transaction = ReportRun([output], 'cpu-proof', 'maintained-native',
                           'actual shared bounded endpoint helper; no native admission claim')
    try:
        paths, tools = inputs_for('build', 'scripts/run_landing_try_proof.py')
        cpu_paths, tools['machine68k'] = cpu_tool_inputs()
        transaction.meta.update(files=snapshot(paths|cpu_paths), tools=tools,
                                runner='scripts/run_landing_try_proof.py')
        transaction.meta['environment']['PYTHONPATH'] = os.environ.get('PYTHONPATH')
        standalone, standalone_listing = build()
        build_native()
        native = ROOT/'build/amiga/interfaces/enhanced/baseline-rally'
        native_listing = native.parent/'native.lst'
        core = shared_bytes()
        assert (core['matched_bytes'], core['normalized_sha256']) == (17606,
            '99c543c170c036137be81d07ebd30b522ef3abdff04bd7b1af38f00047bb99d5')
        kwargs = dict(begin_name='landing_try_begin', end_name='landing_try_end',
                      external_names=('game_advance_ball', 'game_bounce'))
        helper = normalized(standalone, standalone_listing, **kwargs)
        assert helper == normalized(native, native_listing, **kwargs)
        _, symbols = load_image(standalone)
        assert len(helper[0]) == symbols['landing_try_end']-symbols['landing_try_begin']
        result = proof(standalone, native)
        report = dict(passed=True, execution='actual-68000-cpu-only', validation=result,
                      shared_core=core, helper_code_bytes=len(helper[0]),
                      helper_static_state_bytes=0, helper_frame_bytes=48,
                      helper_normalized_sha256=hashlib.sha256(helper[0]).hexdigest(),
                      helper_relocations_each=helper[1], helper_external_branches_each=helper[2],
                      executable_sha256=digest(native),
                      executable_hashes={'standalone':digest(standalone), 'native':digest(native)})
        transaction.finalize(output, report, compiled=[compile_manifest(standalone, standalone_listing),
                                                       compile_manifest(native, native_listing)])
        assert status(output)['status'] == 'passed', status(output)
        print(json.dumps({'passed':True, 'report':str(output), 'sha256':digest(output)}), flush=True)
    except BaseException as error:
        transaction.abort(error)
        raise


if __name__ == '__main__':
    main()
